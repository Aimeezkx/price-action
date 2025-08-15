"""
File validation utilities
"""

import os
from typing import Set, NamedTuple
from fastapi import UploadFile

from app.core.config import settings

# Try to import magic, use fallback if not available
try:
    import magic
    MAGIC_AVAILABLE = True
except ImportError:
    MAGIC_AVAILABLE = False


class ValidationResult(NamedTuple):
    """File validation result"""
    is_valid: bool
    error_message: str = ""


# Supported file types and their MIME types
SUPPORTED_TYPES = {
    'pdf': {'application/pdf'},
    'docx': {
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'application/msword'
    },
    'md': {'text/markdown', 'text/plain'},
    'txt': {'text/plain'}
}

# File extensions mapping
EXTENSION_TO_TYPE = {
    '.pdf': 'pdf',
    '.docx': 'docx',
    '.doc': 'docx',
    '.md': 'md',
    '.markdown': 'md',
    '.txt': 'txt'
}

# Maximum file size (from settings)
MAX_FILE_SIZE = settings.max_file_size


async def validate_file(file: UploadFile) -> ValidationResult:
    """
    Validate uploaded file for type, size, and content
    
    Requirements: 1.1, 1.5 - File type checking and validation
    """
    
    # Check if file is provided
    if not file or not file.filename:
        return ValidationResult(False, "No file provided")
    
    # Get file extension
    file_ext = os.path.splitext(file.filename.lower())[1]
    if file_ext not in EXTENSION_TO_TYPE:
        supported_exts = ', '.join(EXTENSION_TO_TYPE.keys())
        return ValidationResult(
            False, 
            f"Unsupported file type. Supported types: {supported_exts}"
        )
    
    # Check file size
    if hasattr(file, 'size') and file.size:
        if file.size > MAX_FILE_SIZE:
            max_mb = MAX_FILE_SIZE / (1024 * 1024)
            return ValidationResult(
                False, 
                f"File too large. Maximum size: {max_mb:.1f}MB"
            )
    
    # Read a small portion to validate content
    try:
        # Read first 2KB to check file signature
        content_sample = await file.read(2048)
        await file.seek(0)  # Reset file pointer
        
        # Validate file signature using python-magic if available
        if MAGIC_AVAILABLE:
            try:
                mime_type = magic.from_buffer(content_sample, mime=True)
                file_type = EXTENSION_TO_TYPE[file_ext]
                
                if mime_type not in SUPPORTED_TYPES[file_type]:
                    return ValidationResult(
                        False,
                        f"File content doesn't match extension. Expected {file_type}, got {mime_type}"
                    )
                    
            except Exception:
                # If magic fails, just check extension (fallback)
                pass
        else:
            # Basic file signature validation without magic
            if file_ext == '.pdf' and not content_sample.startswith(b'%PDF'):
                return ValidationResult(False, "Invalid PDF file signature")
            elif file_ext in ['.docx'] and not (b'PK' in content_sample[:10]):
                return ValidationResult(False, "Invalid DOCX file signature")
            
    except Exception as e:
        return ValidationResult(False, f"Error reading file: {str(e)}")
    
    return ValidationResult(True)


def get_file_type(filename: str) -> str:
    """Get file type from filename"""
    file_ext = os.path.splitext(filename.lower())[1]
    return EXTENSION_TO_TYPE.get(file_ext, 'unknown')


def is_supported_file_type(filename: str) -> bool:
    """Check if file type is supported"""
    return get_file_type(filename) != 'unknown'