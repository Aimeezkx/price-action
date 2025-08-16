"""File validation utilities for security."""

import os
import hashlib
from pathlib import Path
from typing import List, Optional
from dataclasses import dataclass

from fastapi import UploadFile

try:
    import magic
    MAGIC_AVAILABLE = True
except ImportError:
    MAGIC_AVAILABLE = False
    magic = None

try:
    from app.core.config import settings
except ImportError:
    # Fallback for testing
    class MockSettings:
        privacy_mode = False
    settings = MockSettings()


class FileValidationError(Exception):
    """Exception raised when file validation fails."""
    pass


@dataclass
class FileValidationResult:
    """Result of file validation."""
    is_valid: bool
    error_message: Optional[str] = None
    warnings: List[str] = None
    sanitized_filename: Optional[str] = None


class FileValidator:
    """File validation and security checking."""
    
    # Allowed file extensions
    ALLOWED_EXTENSIONS = {'.pdf', '.docx', '.doc', '.txt', '.md', '.rtf'}
    
    # Allowed MIME types
    ALLOWED_MIME_TYPES = {
        'application/pdf',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'application/msword',
        'text/plain',
        'text/markdown',
        'application/rtf'
    }
    
    # Dangerous file signatures (magic bytes)
    DANGEROUS_SIGNATURES = {
        b'MZ': 'Executable file (PE)',
        b'\x7fELF': 'Executable file (ELF)',
        b'\xca\xfe\xba\xbe': 'Java class file',
        b'PK\x03\x04': 'ZIP archive (potential)',  # Could contain executables
        b'\x50\x4b\x03\x04': 'ZIP archive',
    }
    
    # Maximum file size (100MB)
    MAX_FILE_SIZE = 100 * 1024 * 1024
    
    # Dangerous filename patterns
    DANGEROUS_FILENAME_PATTERNS = [
        '../', '..\\', './', '.\\',  # Path traversal
        '\x00',  # Null bytes
        '<', '>', '"', '|', '?', '*',  # Special characters
        'CON', 'PRN', 'AUX', 'NUL',  # Windows reserved names
        'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
        'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
    ]
    
    def __init__(self):
        """Initialize file validator."""
        if MAGIC_AVAILABLE:
            self.magic_mime = magic.Magic(mime=True)
        else:
            self.magic_mime = None
    
    def validate_file_upload(self, file_path: Path) -> FileValidationResult:
        """Validate uploaded file for security and format compliance."""
        try:
            # Check file exists
            if not file_path.exists():
                return FileValidationResult(False, "File does not exist")
            
            # Check file size
            file_size = file_path.stat().st_size
            if file_size > self.MAX_FILE_SIZE:
                return FileValidationResult(False, f"File too large: {file_size} bytes (max: {self.MAX_FILE_SIZE})")
            
            if file_size == 0:
                return FileValidationResult(False, "File is empty")
            
            # Validate filename
            filename_result = self._validate_filename(file_path.name)
            if not filename_result.is_valid:
                return filename_result
            
            # Check file extension
            extension = file_path.suffix.lower()
            if extension not in self.ALLOWED_EXTENSIONS:
                return FileValidationResult(False, f"File extension '{extension}' not allowed")
            
            # Check MIME type
            if self.magic_mime:
                mime_type = self.magic_mime.from_file(str(file_path))
                if mime_type not in self.ALLOWED_MIME_TYPES:
                    return FileValidationResult(False, f"MIME type '{mime_type}' not allowed")
            else:
                # Fallback to extension-based validation when magic is not available
                pass
            
            # Check file signature
            signature_result = self._check_file_signature(file_path)
            if not signature_result.is_valid:
                return signature_result
            
            # Check for malicious content
            content_result = self._check_file_content(file_path)
            if not content_result.is_valid:
                return content_result
            
            # Sanitize filename
            sanitized_filename = self._sanitize_filename(file_path.name)
            
            return FileValidationResult(
                True,
                sanitized_filename=sanitized_filename,
                warnings=filename_result.warnings
            )
            
        except Exception as e:
            return FileValidationResult(False, f"Validation error: {str(e)}")
    
    def _validate_filename(self, filename: str) -> FileValidationResult:
        """Validate filename for security issues."""
        warnings = []
        
        # Check for dangerous patterns
        for pattern in self.DANGEROUS_FILENAME_PATTERNS:
            if pattern in filename:
                if pattern in ['../', '..\\', './', '.\\']:
                    return FileValidationResult(False, "Path traversal attempt detected in filename")
                elif pattern == '\x00':
                    return FileValidationResult(False, "Null byte detected in filename")
                elif pattern in ['<', '>', '"', '|', '?', '*']:
                    warnings.append(f"Special character '{pattern}' in filename will be removed")
                elif pattern in filename.upper():
                    return FileValidationResult(False, f"Reserved filename '{pattern}' not allowed")
        
        # Check for double extensions
        parts = filename.split('.')
        if len(parts) > 2:
            extensions = [f".{part}" for part in parts[1:]]
            dangerous_extensions = {'.exe', '.bat', '.cmd', '.com', '.scr', '.pif', '.js', '.vbs', '.php'}
            if any(ext in dangerous_extensions for ext in extensions):
                return FileValidationResult(False, "Suspicious double extension detected")
        
        # Check filename length
        if len(filename) > 255:
            return FileValidationResult(False, "Filename too long")
        
        return FileValidationResult(True, warnings=warnings)
    
    def _check_file_signature(self, file_path: Path) -> FileValidationResult:
        """Check file signature for dangerous file types."""
        try:
            with open(file_path, 'rb') as f:
                header = f.read(16)  # Read first 16 bytes
            
            for signature, description in self.DANGEROUS_SIGNATURES.items():
                if header.startswith(signature):
                    # Special case for ZIP files - they might be valid DOCX
                    if signature in [b'PK\x03\x04', b'\x50\x4b\x03\x04']:
                        if file_path.suffix.lower() in ['.docx', '.xlsx', '.pptx']:
                            continue  # These are valid Office formats
                    
                    return FileValidationResult(False, f"Dangerous file type detected: {description}")
            
            return FileValidationResult(True)
            
        except Exception as e:
            return FileValidationResult(False, f"Error checking file signature: {str(e)}")
    
    def _check_file_content(self, file_path: Path) -> FileValidationResult:
        """Check file content for malicious patterns."""
        try:
            # For text files, check content
            if file_path.suffix.lower() in ['.txt', '.md']:
                with open(file_path, 'rb') as f:
                    content = f.read(1024 * 1024)  # Read first 1MB
                
                # Check for null bytes in text files
                if b'\x00' in content:
                    return FileValidationResult(False, "Null bytes detected in text file")
                
                # Check for script content in text files
                try:
                    text_content = content.decode('utf-8', errors='ignore').lower()
                    dangerous_patterns = [
                        '<script>', 'javascript:', 'vbscript:', 'data:text/html',
                        '<?php', '<%', '<jsp:', 'eval(', 'exec('
                    ]
                    
                    for pattern in dangerous_patterns:
                        if pattern in text_content:
                            return FileValidationResult(False, f"Potentially malicious content detected: {pattern}")
                
                except UnicodeDecodeError:
                    pass  # Binary content in text file - suspicious but not necessarily malicious
            
            return FileValidationResult(True)
            
        except Exception as e:
            return FileValidationResult(False, f"Error checking file content: {str(e)}")
    
    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename by removing dangerous characters."""
        if not filename:
            return filename
            
        # Remove dangerous characters
        dangerous_chars = '<>:"|?*\x00'
        for char in dangerous_chars:
            filename = filename.replace(char, '_')
        
        # Remove path traversal attempts
        filename = filename.replace('../', '').replace('..\\', '')
        filename = filename.replace('./', '').replace('.\\', '')
        
        # Remove any remaining path separators
        filename = filename.replace('/', '_').replace('\\', '_')
        
        # Limit length
        if len(filename) > 255:
            name, ext = os.path.splitext(filename)
            max_name_length = 255 - len(ext)
            filename = name[:max_name_length] + ext
        
        # Ensure it's not a reserved name
        name_without_ext = os.path.splitext(filename)[0].upper()
        reserved_names = ['CON', 'PRN', 'AUX', 'NUL', 'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9', 'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9']
        if name_without_ext in reserved_names:
            filename = f"file_{filename}"
        
        return filename
    
    def calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA-256 hash of file."""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()


# Global validator instance
file_validator = FileValidator()


def validate_file_upload(file_path: Path) -> FileValidationResult:
    """Validate uploaded file."""
    return file_validator.validate_file_upload(file_path)


def sanitize_filename(filename: str) -> str:
    """Sanitize filename."""
    validator = FileValidator()
    return validator._sanitize_filename(filename)


def get_file_type(filename: str) -> str:
    """Return file type based on extension."""
    extension = Path(filename).suffix.lower()[1:]
    return extension if extension in {ext.lstrip('.') for ext in FileValidator.ALLOWED_EXTENSIONS} else "unknown"


def is_supported_file_type(filename: str) -> bool:
    """Check if the file has an allowed extension."""
    return Path(filename).suffix.lower() in FileValidator.ALLOWED_EXTENSIONS


async def validate_file(upload_file: UploadFile) -> FileValidationResult:
    """Validate an uploaded file object."""
    file_type = get_file_type(upload_file.filename)
    if not is_supported_file_type(upload_file.filename):
        return FileValidationResult(False, error_message="Unsupported file type")

    contents = await upload_file.read()
    await upload_file.seek(0)

    if not contents:
        return FileValidationResult(False, error_message="File is empty")

    if len(contents) > FileValidator.MAX_FILE_SIZE:
        return FileValidationResult(
            False,
            error_message=f"File too large: {len(contents)} bytes (max: {FileValidator.MAX_FILE_SIZE})",
        )

    sanitized = sanitize_filename(upload_file.filename)
    return FileValidationResult(True, error_message="", sanitized_filename=sanitized, warnings=[])

