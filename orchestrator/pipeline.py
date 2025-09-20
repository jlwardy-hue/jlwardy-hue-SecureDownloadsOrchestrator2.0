"""
Unified File Processing Pipeline for SecureDownloadsOrchestrator 2.0

This module provides a comprehensive file processing pipeline that performs:
1. Real-time directory monitoring
2. Antivirus scanning (using ClamAV)
3. Archive extraction and recursive processing
4. File classification (extension and magic number based)
5. OCR-based metadata extraction (date, sender, business context)
6. Intelligent file organization

The pipeline integrates cleanly with the existing orchestrator configuration and
provides robust error handling and comprehensive logging.
"""

import logging
import os
import re
import shutil
import subprocess
import tarfile
import tempfile
import time
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

try:
    import pytesseract
    from PIL import Image

    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False

try:
    from pdf2image import convert_from_path

    PDF2IMAGE_AVAILABLE = True
except ImportError:
    PDF2IMAGE_AVAILABLE = False

from orchestrator.classifier import FileClassifier
from orchestrator.file_type_detector import FileTypeDetector


class SecurityScanResult:
    """Result of a security scan operation."""

    def __init__(
        self, is_clean: bool, threat_name: str = None, scan_output: str = None
    ):
        self.is_clean = is_clean
        self.threat_name = threat_name
        self.scan_output = scan_output
        self.scanned_at = datetime.now()


class PathValidationError(Exception):
    """Exception raised when path validation fails."""

    pass


class ArchiveBombError(Exception):
    """Exception raised when archive bomb protection is triggered."""

    pass


class OCRMetadata:
    """Metadata extracted from OCR processing."""

    def __init__(self):
        self.text: str = ""
        self.date_detected: Optional[datetime] = None
        self.sender: Optional[str] = None
        self.business_context: Optional[str] = None
        self.confidence: float = 0.0


class ProcessingResult:
    """Result of file processing operation."""

    def __init__(self, success: bool, final_path: str = None, error: str = None):
        self.success = success
        self.final_path = final_path
        self.error = error
        self.metadata: Dict[str, Any] = {}
        self.processed_at = datetime.now()


class UnifiedFileProcessor:
    """
    Unified file processing pipeline that handles the complete workflow
    from file detection to final organization.
    """

    def __init__(self, config: Dict[str, Any], logger: Optional[logging.Logger] = None):
        """
        Initialize the unified file processor.

        Args:
            config: Configuration dictionary containing directories, categories, etc.
            logger: Logger instance for recording operations
        """
        self.config = config
        self.logger = logger or logging.getLogger(__name__)

        # Initialize components
        self.classifier = FileClassifier(config, logger)
        self.file_detector = FileTypeDetector()

        # Configuration paths
        self.source_dir = Path(config.get("directories", {}).get("source", ""))
        self.destination_dir = Path(
            config.get("directories", {}).get("destination", "")
        )
        # Check if quarantine directory is explicitly configured
        quarantine_path = config.get("directories", {}).get("quarantine")
        if quarantine_path:
            self.quarantine_dir = Path(quarantine_path)
        else:
            self.quarantine_dir = self.destination_dir / "quarantine"

        # Processing settings
        self.processing_config = config.get("processing", {})
        self.enable_security_scan = self.processing_config.get(
            "enable_security_scan", False
        )
        self.enable_ocr = self.processing_config.get("enable_ocr", True)
        self.enable_archive_extraction = self.processing_config.get(
            "enable_archive_extraction", True
        )

        # Security settings
        self.security_config = config.get("security", {})
        self.fail_closed = self.security_config.get(
            "fail_closed", True
        )  # Default to fail-closed
        self.archive_limits = self.security_config.get(
            "archive_limits",
            {
                "max_files": 1000,  # Maximum number of files in archive
                "max_total_size": 100 * 1024 * 1024,  # 100MB max total extracted size
                "max_depth": 10,  # Maximum nesting depth
                "max_file_size": 50 * 1024 * 1024,  # 50MB max individual file size
            },
        )

        # Atomic move settings
        self.atomic_move_config = config.get("atomic_move", {})
        self.check_file_stability = self.atomic_move_config.get("enabled", True)
        self.stability_check_duration = self.atomic_move_config.get(
            "duration_seconds", 2
        )
        self.stability_check_interval = self.atomic_move_config.get(
            "check_interval", 0.5
        )

        # Create necessary directories
        self._ensure_directories()

        # Check system dependencies
        self._check_dependencies()

    def _ensure_directories(self):
        """Create necessary directories if they don't exist."""
        try:
            self.quarantine_dir.mkdir(parents=True, exist_ok=True)

            # Create category directories
            categories = self.config.get("categories", {})
            for category, category_config in categories.items():
                dest_path = self.destination_dir / category_config.get(
                    "destination", category
                )
                dest_path.mkdir(parents=True, exist_ok=True)

        except Exception as e:
            self.logger.error(f"Failed to create directories: {e}")

    def _check_dependencies(self):
        """Check availability of system dependencies."""
        # Check ClamAV
        try:
            result = subprocess.run(
                ["which", "clamscan"], capture_output=True, text=True, timeout=5
            )
            self.clamav_available = result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            self.clamav_available = False

        if not self.clamav_available and self.enable_security_scan:
            self.logger.warning("ClamAV not available - security scanning disabled")

        # Check Tesseract
        if not TESSERACT_AVAILABLE and self.enable_ocr:
            self.logger.warning("Tesseract/PIL not available - OCR disabled")

    def _validate_file_path(self, filepath: str) -> None:
        """
        Validate file path for security concerns.

        Protects against path traversal attacks and ensures files are within
        allowed directories.

        Args:
            filepath: Path to validate

        Raises:
            PathValidationError: If path validation fails
        """
        try:
            # Convert to Path object for normalization
            path = Path(filepath)

            # Check for path traversal attempts in the original string
            if ".." in filepath or "~" in filepath:
                raise PathValidationError(f"Path traversal detected in: {filepath}")

            # Resolve the path
            resolved_path = path.resolve()

            # Ensure path exists and is a regular file
            if not resolved_path.exists():
                raise PathValidationError(f"File does not exist: {filepath}")

            if not resolved_path.is_file():
                raise PathValidationError(f"Path is not a regular file: {filepath}")

            # Check if path is within allowed directories (source or temp)
            allowed_parents = [
                self.source_dir.resolve(),
                Path(tempfile.gettempdir()).resolve(),
            ]

            path_is_allowed = False
            for allowed_parent in allowed_parents:
                try:
                    resolved_path.relative_to(allowed_parent)
                    path_is_allowed = True
                    break
                except ValueError:
                    continue

            if not path_is_allowed:
                raise PathValidationError(
                    f"File path outside allowed directories: {filepath}"
                )

            self.logger.debug(f"Path validation passed for: {filepath}")

        except PathValidationError:
            # Re-raise PathValidationError as-is
            raise
        except Exception as e:
            self.logger.error(f"Path validation failed for {filepath}: {e}")
            raise PathValidationError(f"Path validation failed: {e}")

    def _check_file_stability(self, filepath: str) -> bool:
        """
        Check if file is stable (not being written to) before processing.

        This implements atomic move detection by monitoring file size and
        modification time to ensure the file is completely written.

        Args:
            filepath: Path to the file to check

        Returns:
            bool: True if file is stable, False otherwise
        """
        if not self.check_file_stability:
            return True

        try:
            path = Path(filepath)
            if not path.exists():
                return False

            initial_stat = path.stat()
            initial_size = initial_stat.st_size
            initial_mtime = initial_stat.st_mtime

            self.logger.debug(f"Checking file stability for: {filepath}")

            # Wait and check multiple times
            start_time = time.time()
            while time.time() - start_time < self.stability_check_duration:
                time.sleep(self.stability_check_interval)

                if not path.exists():
                    self.logger.warning(
                        f"File disappeared during stability check: {filepath}"
                    )
                    return False

                current_stat = path.stat()
                current_size = current_stat.st_size
                current_mtime = current_stat.st_mtime

                if current_size != initial_size or current_mtime != initial_mtime:
                    self.logger.debug(f"File still being modified: {filepath}")
                    initial_size = current_size
                    initial_mtime = current_mtime
                    start_time = time.time()  # Reset timer

            self.logger.debug(f"File is stable: {filepath}")
            return True

        except Exception as e:
            self.logger.error(f"Error checking file stability for {filepath}: {e}")
            return False

    def process_file(self, filepath: str) -> ProcessingResult:
        """
        Process a single file through the complete pipeline.

        Args:
            filepath: Path to the file to process

        Returns:
            ProcessingResult: Result of the processing operation
        """
        try:
            self.logger.info(f"Starting pipeline processing for: {filepath}")

            # Step 1: Path validation and security checks
            try:
                self._validate_file_path(filepath)
            except PathValidationError as e:
                self.logger.warning(f"Path validation failed, quarantining file: {e}")
                # Create a fake scan result for quarantine
                scan_result = SecurityScanResult(False, "PathValidationError", str(e))
                return self._quarantine_file(filepath, scan_result)

            # Step 2: File stability check (atomic move detection)
            if not self._check_file_stability(filepath):
                self.logger.info(f"File not stable, skipping processing: {filepath}")
                return ProcessingResult(False, error="File not stable for processing")

            # Step 3: Security scanning with fail-closed behavior
            if (
                self.enable_security_scan
                or not self.clamav_available
                and self.fail_closed
            ):
                scan_result = self._scan_file_security(filepath)
                if not scan_result.is_clean:
                    return self._quarantine_file(filepath, scan_result)

            # Step 4: File classification
            file_category = self.classifier.classify_file(filepath)
            self.logger.info(f"File classified as: {file_category}")

            # Step 5: Archive extraction (if applicable) with bomb protection
            if file_category == "archive" and self.enable_archive_extraction:
                return self._process_archive(filepath)

            # Step 6: OCR metadata extraction (for images and PDFs)
            ocr_metadata = None
            if self.enable_ocr and file_category in ["image", "pdf"]:
                ocr_metadata = self._extract_ocr_metadata(filepath)

            # Step 7: Intelligent file organization
            final_path = self._organize_file(filepath, file_category, ocr_metadata)

            return ProcessingResult(True, final_path)

        except Exception as e:
            self.logger.error(f"Error processing file {filepath}: {e}")
            return ProcessingResult(False, error=str(e))

    def _scan_file_security(self, filepath: str) -> SecurityScanResult:
        """
        Scan file for security threats using ClamAV with fail-closed behavior.

        Args:
            filepath: Path to file to scan

        Returns:
            SecurityScanResult: Result of the security scan
        """
        if not self.clamav_available:
            if self.fail_closed:
                self.logger.warning(
                    f"ClamAV not available, failing closed for: {filepath}"
                )
                return SecurityScanResult(
                    False, "AVUnavailable", "Antivirus scanner not available"
                )
            else:
                self.logger.debug(
                    "ClamAV not available, assuming clean (fail-open mode)"
                )
                return SecurityScanResult(True)

        try:
            self.logger.info(f"Security scanning file: {filepath}")

            # Run ClamAV scan
            result = subprocess.run(
                ["clamscan", "--no-summary", filepath],
                capture_output=True,
                text=True,
                timeout=60,
            )

            output = result.stdout + result.stderr

            # ClamAV returns 0 for clean files, 1 for infected files
            if result.returncode == 0:
                self.logger.info(f"Security scan clean: {filepath}")
                return SecurityScanResult(True, scan_output=output)
            elif result.returncode == 1:
                # Extract threat name from output
                threat_match = re.search(r": (.+) FOUND", output)
                threat_name = (
                    threat_match.group(1) if threat_match else "Unknown threat"
                )

                self.logger.warning(
                    f"Security threat detected in {filepath}: {threat_name}"
                )
                return SecurityScanResult(False, threat_name, output)
            else:
                self.logger.error(f"ClamAV scan error for {filepath}: {output}")
                if self.fail_closed:
                    self.logger.warning(f"Scan error, failing closed for: {filepath}")
                    return SecurityScanResult(
                        False, "ScanError", f"Scan error: {output}"
                    )
                else:
                    return SecurityScanResult(
                        True
                    )  # Assume clean on scan error (fail-open)

        except subprocess.TimeoutExpired:
            self.logger.error(f"Security scan timeout for file: {filepath}")
            if self.fail_closed:
                self.logger.warning(f"Scan timeout, failing closed for: {filepath}")
                return SecurityScanResult(
                    False, "ScanTimeout", "Security scan timed out"
                )
            else:
                return SecurityScanResult(True)  # Assume clean on timeout (fail-open)
        except Exception as e:
            self.logger.error(f"Security scan error for {filepath}: {e}")
            if self.fail_closed:
                self.logger.warning(f"Scan exception, failing closed for: {filepath}")
                return SecurityScanResult(
                    False, "ScanException", f"Scan exception: {e}"
                )
            else:
                return SecurityScanResult(True)  # Assume clean on error (fail-open)

    def _quarantine_file(
        self, filepath: str, scan_result: SecurityScanResult
    ) -> ProcessingResult:
        """
        Quarantine a file that failed security scanning.

        Args:
            filepath: Path to the infected file
            scan_result: Security scan result

        Returns:
            ProcessingResult: Result of quarantine operation
        """
        try:
            filename = Path(filepath).name
            quarantine_path = (
                self.quarantine_dir
                / f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}"
            )

            # Move file to quarantine
            shutil.move(filepath, quarantine_path)

            # Log quarantine action
            self.logger.warning(f"File quarantined: {filepath} -> {quarantine_path}")
            self.logger.warning(f"Threat detected: {scan_result.threat_name}")

            # Create quarantine log file
            log_path = quarantine_path.with_suffix(quarantine_path.suffix + ".log")
            with open(log_path, "w") as f:
                f.write(f"Quarantine Date: {datetime.now().isoformat()}\n")
                f.write(f"Original Path: {filepath}\n")
                f.write(f"Threat Name: {scan_result.threat_name}\n")
                f.write(f"Scan Output:\n{scan_result.scan_output}\n")

            return ProcessingResult(True, str(quarantine_path))

        except Exception as e:
            self.logger.error(f"Failed to quarantine file {filepath}: {e}")
            return ProcessingResult(False, error=f"Quarantine failed: {e}")

    def _process_archive(self, filepath: str) -> ProcessingResult:
        """
        Extract and recursively process archive contents with bomb protection.

        Implements protection against archive bombs (zip bombs, tar bombs) by
        monitoring file count, total extracted size, and nesting depth.

        Args:
            filepath: Path to the archive file

        Returns:
            ProcessingResult: Result of archive processing
        """
        try:
            self.logger.info(f"Processing archive with bomb protection: {filepath}")

            # Create temporary extraction directory
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)

                # Extract archive with protection
                try:
                    if filepath.lower().endswith((".zip", ".jar")):
                        self._extract_zip_with_protection(filepath, temp_path)
                    elif filepath.lower().endswith(
                        (".tar", ".tar.gz", ".tgz", ".tar.bz2")
                    ):
                        self._extract_tar_with_protection(filepath, temp_path)
                    else:
                        return ProcessingResult(
                            False, error="Unsupported archive format"
                        )
                except ArchiveBombError as e:
                    self.logger.warning(f"Archive bomb detected: {filepath} - {e}")
                    # Quarantine the archive
                    scan_result = SecurityScanResult(False, "ArchiveBomb", str(e))
                    return self._quarantine_file(filepath, scan_result)

                # Count extracted files and validate limits
                total_extracted_size = 0
                file_count = 0

                # Walk through extracted files and check limits
                for root, dirs, files in os.walk(temp_path):
                    depth = len(Path(root).relative_to(temp_path).parts)
                    if depth > self.archive_limits["max_depth"]:
                        raise ArchiveBombError(
                            f"Archive depth {depth} exceeds limit {self.archive_limits['max_depth']}"
                        )

                    for file in files:
                        file_count += 1
                        if file_count > self.archive_limits["max_files"]:
                            raise ArchiveBombError(
                                f"Archive file count {file_count} exceeds limit {self.archive_limits['max_files']}"
                            )

                        file_path = Path(root) / file
                        if file_path.exists():
                            file_size = file_path.stat().st_size
                            total_extracted_size += file_size

                            if file_size > self.archive_limits["max_file_size"]:
                                raise ArchiveBombError(
                                    f"File size {file_size} exceeds limit {self.archive_limits['max_file_size']}"
                                )

                            if (
                                total_extracted_size
                                > self.archive_limits["max_total_size"]
                            ):
                                raise ArchiveBombError(
                                    f"Total extracted size {total_extracted_size} exceeds limit {self.archive_limits['max_total_size']}"
                                )

                self.logger.info(
                    f"Archive extraction completed safely: {file_count} files, {total_extracted_size} bytes"
                )

                # Recursively process extracted files
                extracted_files = []
                for root, dirs, files in os.walk(temp_path):
                    for file in files:
                        extracted_file = os.path.join(root, file)
                        try:
                            # Validate each extracted file path
                            self._validate_extracted_file_path(
                                extracted_file, temp_path
                            )

                            # Process each extracted file
                            result = self.process_file(extracted_file)
                            if result.success:
                                extracted_files.append(result.final_path)
                        except (PathValidationError, Exception) as e:
                            self.logger.error(
                                f"Error processing extracted file {extracted_file}: {e}"
                            )

                # Move the original archive to archives category
                archive_final_path = self._organize_file(filepath, "archive", None)

                self.logger.info(
                    f"Archive processing complete: {len(extracted_files)} files extracted"
                )

                result = ProcessingResult(True, archive_final_path)
                result.metadata["extracted_files"] = extracted_files
                result.metadata["total_extracted_size"] = total_extracted_size
                result.metadata["file_count"] = file_count
                return result

        except ArchiveBombError as e:
            self.logger.warning(f"Archive bomb detected: {filepath} - {e}")
            scan_result = SecurityScanResult(False, "ArchiveBomb", str(e))
            return self._quarantine_file(filepath, scan_result)
        except Exception as e:
            self.logger.error(f"Failed to process archive {filepath}: {e}")
            return ProcessingResult(False, error=f"Archive processing failed: {e}")

    def _extract_zip_with_protection(self, filepath: str, extract_path: Path) -> None:
        """Extract ZIP file with bomb protection."""
        with zipfile.ZipFile(filepath, "r") as zip_ref:
            total_size = 0
            file_count = 0

            # Check archive contents before extraction
            for info in zip_ref.infolist():
                file_count += 1
                if file_count > self.archive_limits["max_files"]:
                    raise ArchiveBombError(f"ZIP file count {file_count} exceeds limit")

                # Check for path traversal in archive member names
                if ".." in info.filename or info.filename.startswith("/"):
                    raise ArchiveBombError(
                        f"Path traversal detected in ZIP member: {info.filename}"
                    )

                total_size += info.file_size
                if total_size > self.archive_limits["max_total_size"]:
                    raise ArchiveBombError(f"ZIP total size {total_size} exceeds limit")

                if info.file_size > self.archive_limits["max_file_size"]:
                    raise ArchiveBombError(
                        f"ZIP member size {info.file_size} exceeds limit"
                    )

            # Safe extraction
            zip_ref.extractall(extract_path)

    def _extract_tar_with_protection(self, filepath: str, extract_path: Path) -> None:
        """Extract TAR file with bomb protection."""
        with tarfile.open(filepath, "r:*") as tar_ref:
            total_size = 0
            file_count = 0

            # Check archive contents before extraction
            for member in tar_ref.getmembers():
                file_count += 1
                if file_count > self.archive_limits["max_files"]:
                    raise ArchiveBombError(f"TAR file count {file_count} exceeds limit")

                # Check for path traversal
                if ".." in member.name or member.name.startswith("/"):
                    raise ArchiveBombError(
                        f"Path traversal detected in TAR member: {member.name}"
                    )

                if member.isfile():
                    total_size += member.size
                    if total_size > self.archive_limits["max_total_size"]:
                        raise ArchiveBombError(
                            f"TAR total size {total_size} exceeds limit"
                        )

                    if member.size > self.archive_limits["max_file_size"]:
                        raise ArchiveBombError(
                            f"TAR member size {member.size} exceeds limit"
                        )

            # Safe extraction
            tar_ref.extractall(extract_path)

    def _validate_extracted_file_path(
        self, filepath: str, extraction_root: Path
    ) -> None:
        """Validate that extracted file path is safe and within extraction directory."""
        try:
            file_path = Path(filepath).resolve()
            extract_root = extraction_root.resolve()

            # Ensure file is within extraction directory
            file_path.relative_to(extract_root)

            # Additional checks for symlinks and special files
            if file_path.is_symlink():
                # Resolve symlink and ensure target is also within extraction directory
                target = file_path.resolve()
                target.relative_to(extract_root)

        except ValueError:
            raise PathValidationError(
                f"Extracted file path outside extraction directory: {filepath}"
            )
        except Exception as e:
            raise PathValidationError(f"Path validation failed for extracted file: {e}")

    def _extract_ocr_metadata(self, filepath: str) -> Optional[OCRMetadata]:
        """
        Extract metadata from images or PDFs using OCR.

        Args:
            filepath: Path to the image or PDF file

        Returns:
            OCRMetadata: Extracted metadata or None if OCR fails
        """
        if not TESSERACT_AVAILABLE:
            return None

        try:
            self.logger.info(f"Extracting OCR metadata from: {filepath}")

            metadata = OCRMetadata()
            images = []

            # Handle different file types
            file_ext = Path(filepath).suffix.lower()

            if file_ext in [".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif"]:
                # Direct image processing
                images.append(Image.open(filepath))
            elif file_ext == ".pdf" and PDF2IMAGE_AVAILABLE:
                # Convert PDF pages to images
                try:
                    pdf_images = convert_from_path(filepath)
                    images.extend(pdf_images[:3])  # Limit to first 3 pages
                except Exception as e:
                    self.logger.warning(f"Failed to convert PDF to images: {e}")
                    return None
            else:
                return None

            # Perform OCR on all images
            all_text = []
            for i, image in enumerate(images):
                try:
                    text = pytesseract.image_to_string(image)
                    if text.strip():
                        all_text.append(text)
                        self.logger.debug(
                            f"OCR text extracted from page {i + 1}: {len(text)} characters"
                        )
                except Exception as e:
                    self.logger.warning(f"OCR failed for image {i + 1}: {e}")

            if not all_text:
                return None

            # Combine all extracted text
            metadata.text = "\n".join(all_text)

            # Extract structured metadata from text
            self._extract_structured_metadata(metadata)

            self.logger.info(f"OCR metadata extraction complete for: {filepath}")
            return metadata

        except Exception as e:
            self.logger.error(f"OCR metadata extraction failed for {filepath}: {e}")
            return None

    def _extract_structured_metadata(self, metadata: OCRMetadata):
        """
        Extract structured information from OCR text.

        Args:
            metadata: OCRMetadata object to populate
        """
        text = metadata.text.lower()

        # Date extraction patterns
        date_patterns = [
            r"\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b",  # MM/DD/YYYY or DD/MM/YYYY
            r"\b(\d{4}[/-]\d{1,2}[/-]\d{1,2})\b",  # YYYY/MM/DD
            r"\b(january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{1,2},?\s+\d{4}\b",
            r"\b(\d{1,2}\s+(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\s+\d{4})\b",
        ]

        for pattern in date_patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    # Attempt to parse the date from the matched string
                    date_str = match.group(1) if match.lastindex else match.group(0)
                    date_formats = [
                        "%m/%d/%Y",
                        "%d/%m/%Y",
                        "%Y/%m/%d",
                        "%Y-%m-%d",
                        "%m-%d-%Y",
                        "%d-%m-%Y",
                        "%B %d, %Y",
                        "%d %b %Y",
                    ]
                    parsed = None
                    for fmt in date_formats:
                        try:
                            parsed = datetime.strptime(date_str, fmt)
                            break
                        except Exception:
                            continue
                    metadata.date_detected = parsed
                    break
                except Exception:
                    continue

        # Sender extraction (email addresses, names)
        sender_patterns = [
            r"\b([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\b",  # Email
            r"\bfrom[:\s]+([a-zA-Z\s]+)\b",  # "From: Name"
            r"\bsender[:\s]+([a-zA-Z\s]+)\b",  # "Sender: Name"
        ]

        for pattern in sender_patterns:
            match = re.search(pattern, text)
            if match:
                metadata.sender = match.group(1).strip()
                break

        # Business context extraction
        business_keywords = [
            "invoice",
            "receipt",
            "contract",
            "agreement",
            "proposal",
            "statement",
            "bill",
            "purchase",
            "order",
            "delivery",
            "payment",
            "quote",
            "estimate",
        ]

        for keyword in business_keywords:
            if keyword in text:
                metadata.business_context = keyword
                break

        # Calculate confidence based on extracted information
        confidence = 0.0
        if metadata.date_detected:
            confidence += 0.3
        if metadata.sender:
            confidence += 0.4
        if metadata.business_context:
            confidence += 0.3

        metadata.confidence = confidence

    def _organize_file(
        self, filepath: str, category: str, ocr_metadata: Optional[OCRMetadata] = None
    ) -> str:
        """
        Organize file into the appropriate destination directory.

        Args:
            filepath: Source file path
            category: File category from classification
            ocr_metadata: OCR metadata if available

        Returns:
            str: Final path where file was moved
        """
        try:
            source_path = Path(filepath)
            filename = source_path.name

            # Determine base destination directory
            categories = self.config.get("categories", {})

            # Handle classifier-to-config category mapping
            category_mapping = {
                "document": "documents",
                "image": "images",
                "audio": "audio",
                "video": "video",
                "archive": "archives",
                "code": "code",
                "executable": "executables",
            }

            # Map classifier category to config category
            config_category = category_mapping.get(category, category)
            category_config = categories.get(config_category, {})
            base_dest = category_config.get("destination", category)

            # Build intelligent directory structure
            dest_parts = [base_dest]

            # Add date-based organization if available
            if ocr_metadata and ocr_metadata.date_detected:
                date_str = ocr_metadata.date_detected.strftime("%Y/%m")
                dest_parts.append(date_str)

            # Add business context if available
            if ocr_metadata and ocr_metadata.business_context:
                dest_parts.append(ocr_metadata.business_context)

            # Add sender information if available
            if ocr_metadata and ocr_metadata.sender:
                # Clean sender name for filesystem
                clean_sender = re.sub(r'[<>:"/\\|?*]', "_", ocr_metadata.sender[:50])
                dest_parts.append(clean_sender)

            # Construct final destination path
            final_dest_dir = self.destination_dir / Path(*dest_parts)
            final_dest_dir.mkdir(parents=True, exist_ok=True)

            # Handle filename conflicts
            final_path = final_dest_dir / filename
            counter = 1
            while final_path.exists():
                name_parts = filename.rsplit(".", 1)
                if len(name_parts) == 2:
                    new_filename = f"{name_parts[0]}_{counter}.{name_parts[1]}"
                else:
                    new_filename = f"{filename}_{counter}"
                final_path = final_dest_dir / new_filename
                counter += 1

            # Move the file
            shutil.move(filepath, final_path)

            self.logger.info(f"File organized: {filepath} -> {final_path}")

            return str(final_path)

        except Exception as e:
            self.logger.error(f"Failed to organize file {filepath}: {e}")
            # Fallback: move to category directory with original name
            try:
                # Recompute destination directory as in main logic
                category_config = self.config.get("categories", {}).get(category, {})
                fallback_base_dest = category_config.get("destination", category)
                fallback_dest = self.destination_dir / fallback_base_dest / filename
                fallback_dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(filepath, fallback_dest)
                return str(fallback_dest)
            except Exception as e2:
                self.logger.error(f"Fallback organization also failed: {e2}")
                raise

    def _handle_special_folders(self, filepath: str) -> bool:
        """
        Handle special cases like pure-image folders and scripts.

        Args:
            filepath: Path to check for special handling

        Returns:
            bool: True if special handling was applied
        """
        # This is a placeholder for future special folder handling
        # Could include logic for:
        # - Detecting folders with only images
        # - Special script processing
        # - Custom business rules
        return False


# Convenience function for integration with existing system
def create_unified_processor(
    config: Dict[str, Any], logger: Optional[logging.Logger] = None
) -> UnifiedFileProcessor:
    """
    Factory function to create a unified file processor.

    Args:
        config: Configuration dictionary
        logger: Logger instance

    Returns:
        UnifiedFileProcessor: Configured processor instance
    """
    return UnifiedFileProcessor(config, logger)
