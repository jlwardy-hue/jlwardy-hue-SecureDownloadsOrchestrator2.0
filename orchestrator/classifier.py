"""
File classification module for SecureDownloadsOrchestrator 2.0

Provides file classification functionality using file extensions, magic numbers,
and advanced AI-powered operations via OpenAI GPT including classification, 
summarization, sensitive information detection, and metadata extraction.
"""

import json
import logging
import os
import time
from pathlib import Path
from typing import Any, Dict, Optional, List, Union

from orchestrator.file_type_detector import FileTypeDetector


class FileClassifier:
    """
    Advanced file classifier with multi-skill AI capabilities.
    
    Supports traditional file classification via extensions and magic numbers,
    plus advanced AI-powered operations including:
    - File classification with confidence scoring
    - Content summarization  
    - Sensitive information detection
    - Metadata extraction
    
    All AI operations support configurable prompt templates and JSON output parsing.
    """

    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        logger: Optional[logging.Logger] = None,
    ):
        """Initialize the file classifier.

        Args:
            config: Configuration dictionary containing AI settings
            logger: Optional logger instance
        """
        self.logger = logger or logging.getLogger(__name__)
        self.file_detector = FileTypeDetector()
        self.config = config or {}

        # Initialize OpenAI client if AI classification is enabled
        self._openai_client: Optional[Any] = None
        self._ai_enabled = self._should_enable_ai_classification()

        if self._ai_enabled:
            self._initialize_openai_client()

        # Define classification mappings based on file extensions
        self.extension_map = {
            # Documents
            ".pdf": "pdf",
            ".doc": "document",
            ".docx": "document",
            ".txt": "document",
            ".rtf": "document",
            ".odt": "document",
            ".pages": "document",
            # Spreadsheets
            ".xls": "spreadsheet",
            ".xlsx": "spreadsheet",
            ".csv": "spreadsheet",
            ".ods": "spreadsheet",
            ".numbers": "spreadsheet",
            # Presentations
            ".ppt": "presentation",
            ".pptx": "presentation",
            ".odp": "presentation",
            ".key": "presentation",
            # Images
            ".jpg": "image",
            ".jpeg": "image",
            ".png": "image",
            ".gif": "image",
            ".bmp": "image",
            ".tiff": "image",
            ".tif": "image",
            ".svg": "image",
            ".webp": "image",
            ".ico": "image",
            ".heic": "image",
            ".raw": "image",
            # Audio
            ".mp3": "audio",
            ".wav": "audio",
            ".flac": "audio",
            ".aac": "audio",
            ".ogg": "audio",
            ".wma": "audio",
            ".m4a": "audio",
            # Video
            ".mp4": "video",
            ".avi": "video",
            ".mkv": "video",
            ".mov": "video",
            ".wmv": "video",
            ".flv": "video",
            ".webm": "video",
            ".m4v": "video",
            ".3gp": "video",
            # Archives
            ".zip": "archive",
            ".rar": "archive",
            ".7z": "archive",
            ".tar": "archive",
            ".gz": "archive",
            ".bz2": "archive",
            ".xz": "archive",
            ".tar.gz": "archive",
            ".tar.bz2": "archive",
            ".tar.xz": "archive",
            # Executables
            ".exe": "executable",
            ".msi": "executable",
            ".dmg": "executable",
            ".pkg": "executable",
            ".deb": "executable",
            ".rpm": "executable",
            ".appimage": "executable",
            # Code/Development
            ".py": "code",
            ".js": "code",
            ".html": "code",
            ".css": "code",
            ".java": "code",
            ".cpp": "code",
            ".c": "code",
            ".h": "code",
            ".php": "code",
            ".rb": "code",
            ".go": "code",
            ".rs": "code",
            ".swift": "code",
            ".kt": "code",
            ".json": "code",
            ".xml": "code",
            ".yaml": "code",
            ".yml": "code",
        }

        # MIME type mappings for magic number detection
        self.mime_type_map = {
            # Documents
            "application/pdf": "pdf",
            "application/msword": "document",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "document",
            "text/plain": "document",
            "application/rtf": "document",
            # Spreadsheets
            "application/vnd.ms-excel": "spreadsheet",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": "spreadsheet",
            "text/csv": "spreadsheet",
            # Presentations
            "application/vnd.ms-powerpoint": "presentation",
            "application/vnd.openxmlformats-officedocument.presentationml.presentation": "presentation",
            # Images
            "image/jpeg": "image",
            "image/png": "image",
            "image/gif": "image",
            "image/bmp": "image",
            "image/tiff": "image",
            "image/svg+xml": "image",
            "image/webp": "image",
            "image/x-icon": "image",
            # Audio
            "audio/mpeg": "audio",
            "audio/wav": "audio",
            "audio/flac": "audio",
            "audio/aac": "audio",
            "audio/ogg": "audio",
            # Video
            "video/mp4": "video",
            "video/x-msvideo": "video",
            "video/x-matroska": "video",
            "video/quicktime": "video",
            "video/webm": "video",
            # Archives
            "application/zip": "archive",
            "application/x-rar-compressed": "archive",
            "application/x-7z-compressed": "archive",
            "application/x-tar": "archive",
            "application/gzip": "archive",
            "application/x-bzip2": "archive",
            # Executables
            "application/x-msdownload": "executable",
            "application/x-msi": "executable",
            "application/x-apple-diskimage": "executable",
            "application/vnd.debian.binary-package": "executable",
            # Code
            "text/x-python": "code",
            "application/javascript": "code",
            "text/html": "code",
            "text/css": "code",
            "application/json": "code",
            "application/xml": "code",
            "text/xml": "code",
        }

    def _should_enable_ai_classification(self) -> bool:
        """Check if AI classification should be enabled based on configuration."""
        try:
            processing_config = self.config.get("processing", {})
            return processing_config.get("enable_ai_classification", False)
        except Exception as e:
            self.logger.warning(f"Error checking AI classification config: {e}")
            return False

    def _initialize_openai_client(self) -> None:
        """Initialize OpenAI client if configuration is valid."""
        try:

            import openai

            # Check for API key in environment
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                self.logger.warning(
                    "AI classification enabled but OPENAI_API_KEY environment variable not set. "
                    "AI classification will be disabled."
                )
                self._ai_enabled = False
                return

            # Get AI configuration
            ai_config = self.config.get("ai_classification", {})
            endpoint = ai_config.get("endpoint", "https://api.openai.com/v1")

            # Initialize OpenAI client
            self._openai_client = openai.OpenAI(api_key=api_key, base_url=endpoint)

            # Log successful initialization without exposing API key
            self.logger.info(
                f"OpenAI client initialized successfully for AI classification "
                f"(endpoint: {endpoint})"
            )

        except ImportError:
            self.logger.error(
                "OpenAI package not installed. Install with: pip install openai. "
                "AI classification will be disabled."
            )
            self._ai_enabled = False
        except Exception as e:
            self.logger.error(
                f"Failed to initialize OpenAI client: {e}. AI classification disabled."
            )
            self._ai_enabled = False

    def _is_text_file(self, filepath: str, mime_type: Optional[str] = None) -> bool:
        """Check if a file is likely to contain readable text."""
        try:
            # Check MIME type first if available
            if mime_type:
                if mime_type.startswith("text/"):
                    return True
                # Some code files might have application MIME types
                if mime_type in [
                    "application/json",
                    "application/xml",
                    "application/javascript",
                    "application/x-python",
                    "application/x-sh",
                ]:
                    return True

            # Check file extension
            file_path = Path(filepath)
            text_extensions = {
                ".txt",
                ".md",
                ".py",
                ".js",
                ".html",
                ".css",
                ".json",
                ".xml",
                ".yaml",
                ".yml",
                ".ini",
                ".cfg",
                ".conf",
                ".log",
                ".csv",
                ".sql",
                ".sh",
                ".bat",
                ".ps1",
                ".c",
                ".cpp",
                ".h",
                ".java",
                ".php",
                ".rb",
                ".go",
                ".rs",
                ".swift",
                ".kt",
            }

            if file_path.suffix.lower() in text_extensions:
                return True

            return False

        except Exception as e:
            self.logger.warning(f"Error checking if file is text: {filepath}: {e}")
            return False

    def _read_file_content(self, filepath: str) -> Optional[str]:
        """Read the first part of a file for AI classification."""
        try:
            ai_config = self.config.get("ai_classification", {})
            max_length = ai_config.get("max_content_length", 2048)

            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read(max_length)

            self.logger.debug(
                f"Read {len(content)} characters from {filepath} for AI classification"
            )
            return content

        except UnicodeDecodeError:
            self.logger.debug(
                f"File {filepath} contains non-UTF8 content, skipping AI classification"
            )
            return None
        except Exception as e:
            self.logger.warning(
                f"Error reading file content for AI classification: {filepath}: {e}"
            )
            return None

    def _classify_with_ai(self, filepath: str, content: str) -> Optional[str]:
        """
        Classify file content using OpenAI GPT with enhanced JSON response parsing.
        
        This method maintains backward compatibility while leveraging the new
        multi-skill AI framework for improved classification accuracy.
        """
        if not self._ai_enabled or not self._openai_client:
            return None

        try:
            # Try the new JSON-based classification first
            classification_result = self._call_ai_skill("classification", filepath, content)
            
            if classification_result and "category" in classification_result:
                category = classification_result["category"].lower()
                confidence = classification_result.get("confidence", "unknown")
                reasoning = classification_result.get("reasoning", "No reasoning provided")
                
                # Validate the category
                valid_categories = {
                    "document", "image", "audio", "video", "archive", "code", 
                    "executable", "pdf", "spreadsheet", "presentation", "unknown"
                }
                
                if category in valid_categories:
                    self.logger.info(
                        f"AI classified {os.path.basename(filepath)} as '{category}' "
                        f"(confidence: {confidence}, reasoning: {reasoning})"
                    )
                    return category
                else:
                    self.logger.warning(
                        f"AI returned invalid category '{category}' for {filepath}. "
                        f"Full response: {classification_result}"
                    )
            
            # Fallback to legacy classification method if JSON classification fails
            self.logger.debug(f"Falling back to legacy AI classification for {filepath}")
            return self._legacy_classify_with_ai(filepath, content)
            
        except Exception as e:
            self.logger.error(f"Error in enhanced AI classification for {filepath}: {e}")
            # Try legacy method as final fallback
            return self._legacy_classify_with_ai(filepath, content)

    def _legacy_classify_with_ai(self, filepath: str, content: str) -> Optional[str]:
        """
        Legacy AI classification method for backward compatibility.
        
        This method uses the original simple prompt-response approach.
        """
        try:
            ai_config = self.config.get("ai_classification", {})
            model = ai_config.get("model", "gpt-3.5-turbo")
            timeout = ai_config.get("timeout", 30)

            # Prepare the legacy prompt
            prompt = (
                "Analyze the following file content and classify it into one of these categories: "
                "document, image, audio, video, archive, code, executable, pdf, spreadsheet, "
                "presentation, or unknown. Return only the category name.\n\n"
                f"File: {os.path.basename(filepath)}\n"
                f"Content preview:\n{content[:1000]}..."
            )

            self.logger.debug(f"Sending legacy AI classification request for {filepath}")

            response = self._openai_client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a file classifier. Return only the category name.",
                    },
                    {"role": "user", "content": prompt},
                ],
                max_tokens=50,
                temperature=0.1,
                timeout=timeout,
            )

            ai_category = response.choices[0].message.content.strip().lower()

            # Validate the response
            valid_categories = {
                "document", "image", "audio", "video", "archive", "code",
                "executable", "pdf", "spreadsheet", "presentation", "unknown"
            }

            if ai_category not in valid_categories:
                self.logger.warning(
                    f"Legacy AI returned invalid category '{ai_category}' for {filepath}"
                )
                return None

            self.logger.info(f"Legacy AI classified {filepath} as '{ai_category}'")
            return ai_category

        except Exception as e:
            self.logger.error(f"Error in legacy AI classification for {filepath}: {e}")
            return None

    def _prepare_ai_prompt(self, skill: str, filepath: str, content: str) -> Optional[str]:
        """
        Prepare AI prompt using configurable templates.
        
        Args:
            skill: The AI skill to use (classification, summarization, etc.)
            filepath: Path to the file being analyzed
            content: File content to analyze
            
        Returns:
            Formatted prompt string or None if skill not configured
        """
        try:
            ai_config = self.config.get("ai_classification", {})
            skills_config = ai_config.get("skills", {})
            skill_config = skills_config.get(skill, {})
            
            if not skill_config.get("enabled", False):
                self.logger.debug(f"AI skill '{skill}' is not enabled")
                return None
                
            prompt_template = skill_config.get("prompt_template", "")
            if not prompt_template:
                self.logger.warning(f"No prompt template configured for AI skill '{skill}'")
                return None
                
            # Format the prompt with file information
            filename = os.path.basename(filepath)
            formatted_prompt = prompt_template.format(
                filename=filename,
                content=content[:ai_config.get("max_content_length", 2048)]
            )
            
            return formatted_prompt
            
        except Exception as e:
            self.logger.error(f"Error preparing AI prompt for skill '{skill}': {e}")
            return None

    def _call_ai_skill(self, skill: str, filepath: str, content: str) -> Optional[Dict[str, Any]]:
        """
        Call a specific AI skill with the given content.
        
        Args:
            skill: The AI skill to execute
            filepath: Path to the file being analyzed
            content: File content to analyze
            
        Returns:
            Parsed JSON response from AI or None if failed
        """
        if not self._ai_enabled or not self._openai_client:
            return None
            
        try:
            # Prepare the prompt
            prompt = self._prepare_ai_prompt(skill, filepath, content)
            if not prompt:
                return None
                
            ai_config = self.config.get("ai_classification", {})
            skills_config = ai_config.get("skills", {})
            skill_config = skills_config.get(skill, {})
            
            model = ai_config.get("model", "gpt-3.5-turbo")
            timeout = ai_config.get("timeout", 30)
            max_tokens = skill_config.get("max_tokens", 200)
            temperature = skill_config.get("temperature", 0.1)
            
            # Log the request (without sensitive content)
            prompt_summary = f"skill={skill}, model={model}, max_tokens={max_tokens}, temp={temperature}"
            self.logger.debug(f"Sending AI {skill} request for {os.path.basename(filepath)} ({prompt_summary})")
            
            # Optionally log prompt structure for debugging (but not actual content)
            if self.logger.isEnabledFor(logging.DEBUG):
                prompt_lines = prompt.split('\n')
                prompt_structure = f"Prompt has {len(prompt_lines)} lines, {len(prompt)} chars"
                self.logger.debug(f"AI {skill} prompt structure: {prompt_structure}")
            
            # Record start time for performance logging
            start_time = time.time()
            
            # Make the API call
            response = self._openai_client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": f"You are an AI assistant specializing in {skill}. Always respond with valid JSON.",
                    },
                    {"role": "user", "content": prompt},
                ],
                max_tokens=max_tokens,
                temperature=temperature,
                timeout=timeout,
            )
            
            # Calculate response time
            response_time = time.time() - start_time
            
            # Extract and parse the response
            ai_response_text = response.choices[0].message.content.strip()
            
            # Log the successful response (sanitized)
            response_summary = f"response_time={response_time:.2f}s, response_length={len(ai_response_text)}chars"
            self.logger.debug(f"AI {skill} response received for {os.path.basename(filepath)} ({response_summary})")
            
            # Parse JSON response
            try:
                ai_response_json = json.loads(ai_response_text)
                
                # Log successful parsing with key structure (but not values)
                keys = list(ai_response_json.keys()) if isinstance(ai_response_json, dict) else []
                self.logger.info(
                    f"AI {skill} completed successfully for {os.path.basename(filepath)} "
                    f"(response keys: {keys})"
                )
                return ai_response_json
                
            except json.JSONDecodeError as e:
                # Log JSON parsing error with limited response preview
                response_preview = ai_response_text[:100].replace('\n', '\\n')
                self.logger.error(
                    f"Failed to parse AI {skill} JSON response for {os.path.basename(filepath)}: {e}. "
                    f"Response preview: {response_preview}..."
                )
                return None
                
        except Exception as e:
            self.logger.error(f"Error in AI {skill} for {filepath}: {e}")
            return None

    def _should_use_ocr_for_file(self, filepath: str, mime_type: Optional[str] = None) -> bool:
        """
        Determine if OCR should be used for non-text files.
        
        Args:
            filepath: Path to the file
            mime_type: MIME type of the file
            
        Returns:
            True if OCR should be attempted
        """
        try:
            processing_config = self.config.get("processing", {})
            ai_multi_skill_config = processing_config.get("ai_multi_skill", {})
            
            if not ai_multi_skill_config.get("ocr_for_non_text", True):
                return False
                
            # Check if file is an image or PDF that might benefit from OCR
            if mime_type:
                ocr_candidate_types = [
                    "image/jpeg", "image/png", "image/tiff", "image/bmp",
                    "application/pdf", "image/gif"
                ]
                return mime_type in ocr_candidate_types
                
            # Fallback to extension check
            file_path = Path(filepath)
            ocr_extensions = {".jpg", ".jpeg", ".png", ".tiff", ".tif", ".bmp", ".pdf", ".gif"}
            return file_path.suffix.lower() in ocr_extensions
            
        except Exception as e:
            self.logger.warning(f"Error checking OCR eligibility for {filepath}: {e}")
            return False

    def _extract_text_with_ocr(self, filepath: str) -> Optional[str]:
        """
        Extract text from non-text files using OCR.
        
        Args:
            filepath: Path to the file
            
        Returns:
            Extracted text or None if failed
        """
        try:
            # This is a placeholder for OCR integration
            # In a real implementation, this would use pytesseract or similar
            self.logger.info(f"OCR text extraction attempted for {filepath} (placeholder)")
            
            # For now, return None to indicate OCR is not available
            # When implementing, add actual OCR logic here
            return None
            
        except Exception as e:
            self.logger.warning(f"OCR extraction failed for {filepath}: {e}")
            return None

    def analyze_file_with_ai(self, filepath: str, skills: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Perform comprehensive AI analysis of a file using multiple skills.
        
        Args:
            filepath: Path to the file to analyze
            skills: List of skills to apply, or None for all enabled skills
            
        Returns:
            Dictionary containing results from all applied skills
        """
        if not os.path.isfile(filepath):
            self.logger.warning(f"Cannot analyze non-existent file: {filepath}")
            return {}
            
        if not self._ai_enabled:
            self.logger.debug("AI analysis requested but AI is not enabled")
            return {}
            
        results = {}
        
        try:
            # Determine which skills to apply
            ai_config = self.config.get("ai_classification", {})
            skills_config = ai_config.get("skills", {})
            
            if skills is None:
                # Use all enabled skills
                skills = [skill for skill, config in skills_config.items() 
                         if config.get("enabled", False)]
            
            if not skills:
                self.logger.debug(f"No AI skills enabled for file analysis: {filepath}")
                return {}
                
            # Get file content
            content = None
            
            # First try to read as text
            if self._is_text_file(filepath):
                content = self._read_file_content(filepath)
            
            # If text reading failed, try OCR if enabled
            if not content and self._should_use_ocr_for_file(filepath):
                self.logger.info(f"Attempting OCR text extraction for {filepath}")
                content = self._extract_text_with_ocr(filepath)
                
            if not content:
                self.logger.warning(
                    f"No readable content found for AI analysis: {filepath}. "
                    "File may be binary or OCR unavailable."
                )
                return {}
                
            # Apply each requested skill
            for skill in skills:
                try:
                    skill_result = self._call_ai_skill(skill, filepath, content)
                    if skill_result:
                        results[skill] = skill_result
                    else:
                        results[skill] = {"error": f"AI {skill} failed or returned invalid response"}
                        
                except Exception as e:
                    self.logger.error(f"Error applying AI skill '{skill}' to {filepath}: {e}")
                    results[skill] = {"error": str(e)}
                    
            self.logger.info(
                f"AI analysis completed for {filepath}. "
                f"Applied {len(skills)} skills, {len([r for r in results.values() if 'error' not in r])} successful."
            )
            
        except Exception as e:
            self.logger.error(f"Error in comprehensive AI analysis for {filepath}: {e}")
            results["error"] = str(e)
            
        return results

    def _get_file_extension(self, filepath: str) -> str:
        """Get the file extension, handling compound extensions."""
        file_path = Path(filepath)
        extension = file_path.suffix.lower()

        # Handle compound extensions like .tar.gz
        if extension in [".gz", ".bz2", ".xz"] and len(file_path.suffixes) > 1:
            compound_ext = "".join(file_path.suffixes[-2:]).lower()
            if compound_ext in self.extension_map:
                extension = compound_ext

        return extension

    def _get_traditional_classification(self, filepath: str, extension: str) -> tuple:
        """Get traditional classification based on extension and MIME type."""
        # First try classification by extension
        extension_category = self.extension_map.get(extension)

        # Get MIME type using magic numbers
        metadata = self.file_detector.detect_type_and_metadata(filepath)
        mime_category = None

        if metadata and metadata.get("mime_type"):
            mime_type = metadata["mime_type"]
            mime_category = self.mime_type_map.get(mime_type)

        return extension_category, mime_category, metadata

    def _determine_final_category(
        self, extension_category: str, mime_category: str, metadata: dict
    ) -> str:
        """Determine the final category using traditional classification logic."""
        # Special case: if extension is unknown and MIME type is generic, classify as unknown
        if not extension_category and metadata.get("mime_type") in [
            "text/plain",
            "application/octet-stream",
        ]:
            return "unknown"
        # For specific MIME types that are clearly identifiable, prefer MIME type
        elif mime_category and metadata.get("mime_type") not in [
            "text/plain",
            "application/octet-stream",
        ]:
            return mime_category
        # For generic MIME types or when MIME detection fails, prefer extension
        elif extension_category:
            return extension_category
        # Fallback to MIME category if extension didn't match
        elif mime_category:
            return mime_category
        else:
            return "unknown"

    def classify_file(self, filepath: str) -> str:
        """
        Classify a file based on its extension and magic numbers.

        Args:
            filepath: Path to the file to classify

        Returns:
            str: File category such as 'pdf', 'image', 'archive', 'unknown', etc.
        """
        if not os.path.isfile(filepath):
            self.logger.warning(f"Cannot classify non-existent file: {filepath}")
            return "unknown"

        try:
            # Get file extension
            extension = self._get_file_extension(filepath)

            # Get traditional classification
            extension_category, mime_category, metadata = self._get_traditional_classification(
                filepath, extension
            )

            # Determine final category with traditional logic
            final_category = self._determine_final_category(
                extension_category, mime_category, metadata
            )

            # Try AI classification if enabled and file is suitable
            ai_category = None
            if self._ai_enabled:
                mime_type = metadata.get("mime_type") if metadata else None
                if self._is_text_file(filepath, mime_type):
                    content = self._read_file_content(filepath)
                    if content:
                        ai_category = self._classify_with_ai(filepath, content)

            # Use AI classification if available and different from traditional classification
            if ai_category:
                if final_category == "unknown" or ai_category != final_category:
                    self.logger.info(
                        f"AI classification override: {filepath} "
                        f"traditional: {final_category} -> AI: {ai_category}"
                    )
                    final_category = ai_category

            # Log the classification result
            log_msg = f"File classified: {filepath} -> {final_category} "
            log_msg += f"(ext: {extension}, mime: {metadata.get('mime_type', 'unknown') if metadata else 'unknown'}"
            if ai_category:
                log_msg += f", AI: {ai_category}"
            log_msg += ")"
            self.logger.info(log_msg)

            return final_category

        except Exception as e:
            self.logger.error(f"Error classifying file {filepath}: {e}")
            return "unknown"


def classify_file(
    filepath: str,
    config: Optional[Dict[str, Any]] = None,
    logger: Optional[logging.Logger] = None,
) -> str:
    """
    Convenience function to classify a file without creating a classifier instance.

    Args:
        filepath: Path to the file to classify
        config: Optional configuration dictionary containing AI settings
        logger: Optional logger instance

    Returns:
        str: File category such as 'pdf', 'image', 'archive', 'unknown', etc.
    """
    classifier = FileClassifier(config, logger)
    return classifier.classify_file(filepath)


def analyze_file_with_ai(
    filepath: str,
    skills: Optional[List[str]] = None,
    config: Optional[Dict[str, Any]] = None,
    logger: Optional[logging.Logger] = None,
) -> Dict[str, Any]:
    """
    Convenience function to perform comprehensive AI analysis without creating a classifier instance.
    
    Args:
        filepath: Path to the file to analyze
        skills: List of AI skills to apply (None for all enabled skills)
        config: Optional configuration dictionary containing AI settings
        logger: Optional logger instance
        
    Returns:
        Dictionary containing results from all applied AI skills
    """
    classifier = FileClassifier(config, logger)
    return classifier.analyze_file_with_ai(filepath, skills)
