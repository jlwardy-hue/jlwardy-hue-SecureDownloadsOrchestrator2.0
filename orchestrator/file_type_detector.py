import os
import logging
import magic
from datetime import datetime

class FileTypeDetector:
    def __init__(self):
        self.magic = magic.Magic(mime=True)

    def detect_type_and_metadata(self, file_path):
        if not os.path.isfile(file_path):
            logging.warning(f"Tried to detect file type of non-existent file: {file_path}")
            return None

        try:
            mime_type = self.magic.from_file(file_path)
            stat = os.stat(file_path)
            metadata = {
                "file_name": os.path.basename(file_path),
                "file_path": file_path,
                "extension": os.path.splitext(file_path)[1].lower(),
                "mime_type": mime_type,
                "size_bytes": stat.st_size,
                "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
            }
            logging.info(f"File type detected: {mime_type} | Metadata: {metadata}")
            return metadata
        except Exception as e:
            logging.error(f"Error detecting file type for {file_path}: {e}")
            return None
