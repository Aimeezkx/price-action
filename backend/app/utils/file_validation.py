"""File validation utilities for security."""

import os
import hashlib
from pathlib import Path
from typing import List, Optional
from dataclasses import dataclass

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
    
    # Allowed MIME types with more comprehensive mapping
    ALLOWED_MIME_TYPES = {
        'application/pdf',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'application/msword',
        'text/plain',
        'text/markdown',
        'text/x-markdown',
        'application/rtf',
        'text/rtf',
        'application/x-rtf',
        'text/richtext'
    }
    
    # Extension to MIME type mapping for validation
    EXTENSION_MIME_MAP = {
        '.pdf': {'application/pdf'},
        '.docx': {'application/vnd.openxmlformats-officedocument.wordprocessingml.document'},
        '.doc': {'application/msword'},
        '.txt': {'text/plain'},
        '.md': {'text/markdown', 'text/x-markdown', 'text/plain'},
        '.rtf': {'application/rtf', 'text/rtf', 'application/x-rtf', 'text/richtext'}
    }
    
    # Dangerous file signatures (magic bytes) - expanded list
    DANGEROUS_SIGNATURES = {
        b'MZ': 'Executable file (PE)',
        b'\x7fELF': 'Executable file (ELF)',
        b'\xca\xfe\xba\xbe': 'Java class file',
        b'\xfe\xed\xfa\xce': 'Mach-O executable (32-bit)',
        b'\xfe\xed\xfa\xcf': 'Mach-O executable (64-bit)',
        b'\xcf\xfa\xed\xfe': 'Mach-O executable (reverse byte order)',
        b'\x4d\x5a': 'Windows executable (alternative)',
        b'\x50\x4b\x05\x06': 'ZIP archive (empty)',
        b'\x50\x4b\x07\x08': 'ZIP archive (spanned)',
        b'#!/bin/sh': 'Shell script',
        b'#!/bin/bash': 'Bash script',
        b'#!/usr/bin/env': 'Environment script',
        b'<?php': 'PHP script',
        b'<%': 'ASP/JSP script',
        b'<script': 'JavaScript in HTML',
        b'\x89PNG': 'PNG image (not allowed)',
        b'\xff\xd8\xff': 'JPEG image (not allowed)',
        b'GIF87a': 'GIF image (not allowed)',
        b'GIF89a': 'GIF image (not allowed)',
        b'RIFF': 'RIFF container (could be malicious)',
        b'\x00\x00\x01\x00': 'Windows icon (not allowed)',
        b'\x00\x00\x02\x00': 'Windows cursor (not allowed)'
    }
    
    # PDF-specific signatures for validation
    PDF_SIGNATURES = {
        b'%PDF-1.0', b'%PDF-1.1', b'%PDF-1.2', b'%PDF-1.3', 
        b'%PDF-1.4', b'%PDF-1.5', b'%PDF-1.6', b'%PDF-1.7', b'%PDF-2.0'
    }
    
    # Maximum file size (100MB) - configurable
    MAX_FILE_SIZE = 100 * 1024 * 1024
    
    # Minimum file size (to prevent empty files)
    MIN_FILE_SIZE = 10  # 10 bytes
    
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
                return FileValidationResult(False, f"File too large: {file_size:,} bytes (max: {self.MAX_FILE_SIZE:,} bytes)")
            
            if file_size < self.MIN_FILE_SIZE:
                return FileValidationResult(False, f"File too small: {file_size} bytes (min: {self.MIN_FILE_SIZE} bytes)")
            
            # Validate filename
            filename_result = self._validate_filename(file_path.name)
            if not filename_result.is_valid:
                return filename_result
            
            # Check file extension
            extension = file_path.suffix.lower()
            if extension not in self.ALLOWED_EXTENSIONS:
                return FileValidationResult(False, f"File extension '{extension}' not allowed. Allowed extensions: {', '.join(sorted(self.ALLOWED_EXTENSIONS))}")
            
            # Check MIME type and validate against extension
            mime_validation_result = self._validate_mime_type(file_path, extension)
            if not mime_validation_result.is_valid:
                return mime_validation_result
            
            # Check file signature (magic bytes)
            signature_result = self._check_file_signature(file_path, extension)
            if not signature_result.is_valid:
                return signature_result
            
            # Perform deep content validation
            content_result = self._check_file_content(file_path, extension)
            if not content_result.is_valid:
                return content_result
            
            # Check for embedded malicious content
            embedded_result = self._check_embedded_content(file_path, extension)
            if not embedded_result.is_valid:
                return embedded_result
            
            # Perform virus scanning if enabled
            if settings.enable_file_scanning:
                virus_result = self._scan_for_malware(file_path)
                if not virus_result.is_valid:
                    return virus_result
            
            # Sanitize filename
            sanitized_filename = self._sanitize_filename(file_path.name)
            
            # Collect all warnings
            all_warnings = []
            if filename_result.warnings:
                all_warnings.extend(filename_result.warnings)
            if mime_validation_result.warnings:
                all_warnings.extend(mime_validation_result.warnings)
            if content_result.warnings:
                all_warnings.extend(content_result.warnings)
            
            return FileValidationResult(
                True,
                sanitized_filename=sanitized_filename,
                warnings=all_warnings if all_warnings else None
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
    
    def _validate_mime_type(self, file_path: Path, extension: str) -> FileValidationResult:
        """Validate MIME type against file extension."""
        warnings = []
        
        try:
            if self.magic_mime:
                detected_mime = self.magic_mime.from_file(str(file_path))
                
                # Check if MIME type is allowed
                if detected_mime not in self.ALLOWED_MIME_TYPES:
                    return FileValidationResult(False, f"MIME type '{detected_mime}' not allowed")
                
                # Check if MIME type matches extension
                expected_mimes = self.EXTENSION_MIME_MAP.get(extension, set())
                if expected_mimes and detected_mime not in expected_mimes:
                    # Some flexibility for text files
                    if extension in ['.txt', '.md'] and detected_mime in ['text/plain', 'text/markdown', 'text/x-markdown']:
                        warnings.append(f"MIME type '{detected_mime}' acceptable for {extension} files")
                    else:
                        return FileValidationResult(False, f"MIME type '{detected_mime}' does not match extension '{extension}'. Expected: {', '.join(expected_mimes)}")
                
                return FileValidationResult(True, warnings=warnings if warnings else None)
            else:
                # Fallback when magic is not available
                warnings.append("MIME type validation skipped (python-magic not available)")
                return FileValidationResult(True, warnings=warnings)
                
        except Exception as e:
            return FileValidationResult(False, f"Error validating MIME type: {str(e)}")

    def _check_file_signature(self, file_path: Path, extension: str) -> FileValidationResult:
        """Check file signature for dangerous file types and format validation."""
        try:
            with open(file_path, 'rb') as f:
                header = f.read(32)  # Read first 32 bytes for better detection
            
            # Check for dangerous signatures first
            for signature, description in self.DANGEROUS_SIGNATURES.items():
                if header.startswith(signature):
                    # Special case for ZIP files - they might be valid DOCX
                    if signature in [b'PK\x03\x04', b'\x50\x4b\x03\x04']:
                        if extension in ['.docx']:
                            # Additional validation for DOCX files
                            if self._validate_docx_structure(file_path):
                                continue  # Valid DOCX file
                            else:
                                return FileValidationResult(False, "Invalid DOCX file structure")
                        else:
                            return FileValidationResult(False, f"ZIP archive not allowed for {extension} files")
                    
                    return FileValidationResult(False, f"Dangerous file type detected: {description}")
            
            # Validate specific file format signatures
            if extension == '.pdf':
                if not any(header.startswith(sig) for sig in self.PDF_SIGNATURES):
                    return FileValidationResult(False, "Invalid PDF file signature")
            
            elif extension == '.docx':
                # DOCX files should start with ZIP signature
                if not header.startswith(b'PK\x03\x04'):
                    return FileValidationResult(False, "Invalid DOCX file signature")
            
            elif extension in ['.txt', '.md']:
                # Check for binary content in text files
                if b'\x00' in header:
                    return FileValidationResult(False, "Binary content detected in text file")
            
            return FileValidationResult(True)
            
        except Exception as e:
            return FileValidationResult(False, f"Error checking file signature: {str(e)}")
    
    def _validate_docx_structure(self, file_path: Path) -> bool:
        """Validate DOCX file structure."""
        try:
            import zipfile
            with zipfile.ZipFile(file_path, 'r') as zip_file:
                # Check for required DOCX files
                required_files = ['[Content_Types].xml', '_rels/.rels']
                for required_file in required_files:
                    if required_file not in zip_file.namelist():
                        return False
                
                # Check for document.xml in word folder
                word_files = [f for f in zip_file.namelist() if f.startswith('word/')]
                if not any('document.xml' in f for f in word_files):
                    return False
                
                return True
        except Exception:
            return False
    
    def _check_file_content(self, file_path: Path, extension: str) -> FileValidationResult:
        """Check file content for malicious patterns and format compliance."""
        warnings = []
        
        try:
            # Read file content for analysis
            with open(file_path, 'rb') as f:
                content = f.read(2 * 1024 * 1024)  # Read first 2MB for analysis
            
            # Text file specific checks
            if extension in ['.txt', '.md']:
                # Check for null bytes in text files
                if b'\x00' in content:
                    return FileValidationResult(False, "Null bytes detected in text file")
                
                # Try to decode as text
                try:
                    text_content = content.decode('utf-8', errors='strict')
                    
                    # Check for malicious script patterns
                    dangerous_patterns = [
                        ('<script', 'HTML script tag'),
                        ('javascript:', 'JavaScript protocol'),
                        ('vbscript:', 'VBScript protocol'),
                        ('data:text/html', 'Data URI with HTML'),
                        ('<?php', 'PHP opening tag'),
                        ('<%', 'ASP/JSP opening tag'),
                        ('<jsp:', 'JSP tag'),
                        ('eval(', 'JavaScript eval function'),
                        ('exec(', 'Execution function'),
                        ('system(', 'System command function'),
                        ('shell_exec(', 'Shell execution function'),
                        ('passthru(', 'Passthrough function'),
                        ('file_get_contents(', 'File reading function'),
                        ('curl_exec(', 'CURL execution function'),
                        ('base64_decode(', 'Base64 decode function'),
                        ('document.write(', 'DOM manipulation'),
                        ('document.cookie', 'Cookie access'),
                        ('window.location', 'Location manipulation')
                    ]
                    
                    text_lower = text_content.lower()
                    for pattern, description in dangerous_patterns:
                        if pattern in text_lower:
                            return FileValidationResult(False, f"Potentially malicious content detected: {description}")
                    
                    # Check for suspicious URLs
                    import re
                    suspicious_url_patterns = [
                        r'https?://[^\s]*\.exe',
                        r'https?://[^\s]*\.bat',
                        r'https?://[^\s]*\.cmd',
                        r'https?://[^\s]*\.scr',
                        r'ftp://[^\s]*\.(exe|bat|cmd|scr)',
                    ]
                    
                    for pattern in suspicious_url_patterns:
                        if re.search(pattern, text_content, re.IGNORECASE):
                            return FileValidationResult(False, "Suspicious executable URL detected")
                    
                    # Check for excessive special characters (potential obfuscation)
                    special_char_ratio = sum(1 for c in text_content if not c.isalnum() and not c.isspace()) / len(text_content)
                    if special_char_ratio > 0.3:
                        warnings.append("High ratio of special characters detected (possible obfuscation)")
                
                except UnicodeDecodeError:
                    return FileValidationResult(False, "Text file contains invalid UTF-8 encoding")
            
            # PDF specific checks
            elif extension == '.pdf':
                # Check for embedded JavaScript in PDF
                if b'/JavaScript' in content or b'/JS' in content:
                    warnings.append("PDF contains JavaScript (potential security risk)")
                
                # Check for forms or actions
                if b'/Action' in content:
                    warnings.append("PDF contains actions (potential security risk)")
                
                # Check for external references
                if b'/URI' in content:
                    warnings.append("PDF contains external URI references")
            
            # DOCX specific checks (basic)
            elif extension == '.docx':
                # Check for macros (VBA)
                if b'vbaProject' in content or b'macros' in content.lower():
                    return FileValidationResult(False, "DOCX file contains macros (not allowed)")
                
                # Check for external references
                if b'http://' in content or b'https://' in content:
                    warnings.append("DOCX contains external references")
            
            # RTF specific checks
            elif extension == '.rtf':
                # Check for embedded objects
                if b'\\object' in content.lower():
                    warnings.append("RTF contains embedded objects")
                
                # Check for external references
                if b'\\field' in content.lower():
                    warnings.append("RTF contains field codes")
            
            # General checks for all files
            # Check for embedded executables
            executable_patterns = [
                b'This program cannot be run in DOS mode',
                b'MZ\x90\x00',  # PE header
                b'\x7fELF',     # ELF header
            ]
            
            for pattern in executable_patterns:
                if pattern in content:
                    return FileValidationResult(False, "Embedded executable content detected")
            
            return FileValidationResult(True, warnings=warnings if warnings else None)
            
        except Exception as e:
            return FileValidationResult(False, f"Error checking file content: {str(e)}")
    
    def _check_embedded_content(self, file_path: Path, extension: str) -> FileValidationResult:
        """Check for embedded malicious content in complex file formats."""
        try:
            if extension == '.pdf':
                return self._check_pdf_embedded_content(file_path)
            elif extension == '.docx':
                return self._check_docx_embedded_content(file_path)
            else:
                return FileValidationResult(True)
        except Exception as e:
            return FileValidationResult(False, f"Error checking embedded content: {str(e)}")
    
    def _check_pdf_embedded_content(self, file_path: Path) -> FileValidationResult:
        """Check PDF for embedded malicious content."""
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
            
            # Check for suspicious PDF features
            suspicious_features = [
                (b'/Launch', 'Launch action (can execute programs)'),
                (b'/EmbeddedFile', 'Embedded files'),
                (b'/XFA', 'XFA forms (potential security risk)'),
                (b'/RichMedia', 'Rich media content'),
                (b'/3D', '3D content'),
                (b'/Sound', 'Sound content'),
                (b'/Movie', 'Movie content'),
                (b'/GoToR', 'Remote go-to action'),
                (b'/ImportData', 'Data import action'),
                (b'/SubmitForm', 'Form submission action')
            ]
            
            warnings = []
            for pattern, description in suspicious_features:
                if pattern in content:
                    if pattern in [b'/Launch', b'/ImportData']:
                        return FileValidationResult(False, f"Dangerous PDF feature detected: {description}")
                    else:
                        warnings.append(f"PDF feature detected: {description}")
            
            return FileValidationResult(True, warnings=warnings if warnings else None)
            
        except Exception as e:
            return FileValidationResult(False, f"Error checking PDF embedded content: {str(e)}")
    
    def _check_docx_embedded_content(self, file_path: Path) -> FileValidationResult:
        """Check DOCX for embedded malicious content."""
        try:
            import zipfile
            warnings = []
            
            with zipfile.ZipFile(file_path, 'r') as zip_file:
                file_list = zip_file.namelist()
                
                # Check for suspicious files in DOCX
                suspicious_files = [
                    ('vbaProject.bin', 'VBA macros'),
                    ('activeX', 'ActiveX controls'),
                    ('embeddings/', 'Embedded objects'),
                    ('media/', 'Media files')
                ]
                
                for file_pattern, description in suspicious_files:
                    matching_files = [f for f in file_list if file_pattern in f]
                    if matching_files:
                        if file_pattern == 'vbaProject.bin':
                            return FileValidationResult(False, f"Dangerous DOCX content: {description}")
                        else:
                            warnings.append(f"DOCX contains: {description}")
                
                # Check for external references in relationships
                try:
                    rels_content = zip_file.read('_rels/.rels').decode('utf-8', errors='ignore')
                    if 'http://' in rels_content or 'https://' in rels_content:
                        warnings.append("DOCX contains external references")
                except:
                    pass
            
            return FileValidationResult(True, warnings=warnings if warnings else None)
            
        except Exception as e:
            return FileValidationResult(False, f"Error checking DOCX embedded content: {str(e)}")
    
    def _scan_for_malware(self, file_path: Path) -> FileValidationResult:
        """Scan file for malware using available scanners."""
        try:
            from app.utils.security import scan_file_for_malware
            
            is_infected = scan_file_for_malware(file_path)
            if is_infected:
                return FileValidationResult(False, "File failed malware scan - potential threat detected")
            
            return FileValidationResult(True)
            
        except Exception as e:
            # If scanning fails, log but don't block upload
            return FileValidationResult(True, warnings=[f"Malware scan failed: {str(e)}"])
    
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


def get_file_type(file_path) -> str:
    """Get file type based on extension and MIME type."""
    if isinstance(file_path, str):
        file_path = Path(file_path)
    extension = file_path.suffix.lower()
    
    # Map extensions to file types
    extension_map = {
        '.pdf': 'pdf',
        '.docx': 'docx',
        '.doc': 'doc',
        '.txt': 'text',
        '.md': 'markdown',
        '.rtf': 'rtf'
    }
    
    return extension_map.get(extension, 'unknown')


def validate_file(file_path: Path) -> FileValidationResult:
    """Validate file - alias for validate_file_upload."""
    return file_validator.validate_file_upload(file_path)