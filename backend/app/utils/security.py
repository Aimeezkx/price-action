"""
Security utilities for file validation and data protection
"""

import hashlib
import logging
import mimetypes
import os
import re
from pathlib import Path
from typing import Optional, Tuple

from fastapi import HTTPException, UploadFile

from app.core.config import settings

logger = logging.getLogger(__name__)


class SecurityValidator:
    """Security validation utilities"""
    
    # Allowed MIME types for each file extension
    ALLOWED_MIME_TYPES = {
        'pdf': ['application/pdf'],
        'docx': [
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'application/msword'
        ],
        'md': ['text/markdown', 'text/plain']
    }
    
    # Maximum file sizes by type (in bytes)
    MAX_FILE_SIZES = {
        'pdf': 100 * 1024 * 1024,  # 100MB
        'docx': 50 * 1024 * 1024,  # 50MB
        'md': 10 * 1024 * 1024     # 10MB
    }
    
    # Dangerous file patterns to reject
    DANGEROUS_PATTERNS = [
        rb'<script',
        rb'javascript:',
        rb'vbscript:',
        rb'onload=',
        rb'onerror=',
        rb'eval\(',
        rb'exec\(',
        rb'system\(',
        rb'shell_exec',
        rb'passthru',
        rb'<?php',
        rb'<%',
        rb'<jsp:',
    ]
    
    @classmethod
    async def validate_upload_file(cls, file: UploadFile) -> Tuple[str, str]:
        """
        Validate uploaded file for security and format compliance
        
        Returns:
            Tuple of (file_type, safe_filename)
            
        Raises:
            HTTPException: If file validation fails
        """
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")
            
        # Get file extension
        file_ext = cls._get_file_extension(file.filename)
        if file_ext not in settings.allowed_file_types:
            raise HTTPException(
                status_code=400, 
                detail=f"File type '{file_ext}' not allowed. Allowed types: {settings.allowed_file_types}"
            )
        
        # Validate filename
        safe_filename = cls._sanitize_filename(file.filename)
        
        # Check file size
        file_size = 0
        content_chunks = []
        
        while chunk := await file.read(8192):
            content_chunks.append(chunk)
            file_size += len(chunk)
            
            if file_size > cls.MAX_FILE_SIZES.get(file_ext, settings.max_file_size):
                raise HTTPException(
                    status_code=413,
                    detail=f"File too large. Maximum size for {file_ext}: {cls.MAX_FILE_SIZES.get(file_ext, settings.max_file_size)} bytes"
                )
        
        # Reconstruct file content
        file_content = b''.join(content_chunks)
        
        # Reset file pointer for further processing
        await file.seek(0)
        
        # Validate MIME type
        cls._validate_mime_type(file_content, file_ext, file.content_type)
        
        # Scan for malicious content
        if settings.enable_file_scanning:
            cls._scan_for_malicious_content(file_content, file_ext)
        
        return file_ext, safe_filename
    
    @classmethod
    def _get_file_extension(cls, filename: str) -> str:
        """Extract and validate file extension"""
        ext = Path(filename).suffix.lower().lstrip('.')
        if not ext:
            raise HTTPException(status_code=400, detail="File must have an extension")
        return ext
    
    @classmethod
    def _sanitize_filename(cls, filename: str) -> str:
        """Sanitize filename to prevent path traversal and other attacks"""
        # Remove path components
        filename = os.path.basename(filename)
        
        # Remove dangerous characters
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        
        # Remove control characters
        filename = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', filename)
        
        # Limit length
        if len(filename) > 255:
            name, ext = os.path.splitext(filename)
            filename = name[:250] + ext
        
        # Ensure filename is not empty
        if not filename or filename.startswith('.'):
            filename = f"document_{hashlib.md5(filename.encode()).hexdigest()[:8]}.txt"
        
        return filename
    
    @classmethod
    def _validate_mime_type(cls, content: bytes, file_ext: str, declared_type: Optional[str]):
        """Validate file MIME type matches extension"""
        # Check magic bytes for common formats
        if file_ext == 'pdf' and not content.startswith(b'%PDF-'):
            raise HTTPException(status_code=400, detail="Invalid PDF file format")
        
        if file_ext == 'docx':
            # DOCX files are ZIP archives with specific structure
            if not content.startswith(b'PK'):
                raise HTTPException(status_code=400, detail="Invalid DOCX file format")
        
        # Validate declared MIME type if provided
        if declared_type:
            allowed_types = cls.ALLOWED_MIME_TYPES.get(file_ext, [])
            if declared_type not in allowed_types:
                logger.warning(f"MIME type mismatch: declared={declared_type}, expected={allowed_types}")
    
    @classmethod
    def _scan_for_malicious_content(cls, content: bytes, file_ext: str):
        """Scan file content for malicious patterns"""
        # Convert to lowercase for case-insensitive matching
        content_lower = content.lower()
        
        for pattern in cls.DANGEROUS_PATTERNS:
            if pattern in content_lower:
                logger.warning(f"Dangerous pattern detected in {file_ext} file: {pattern}")
                raise HTTPException(
                    status_code=400,
                    detail="File contains potentially malicious content"
                )
        
        # Additional checks for specific file types
        if file_ext == 'pdf':
            cls._scan_pdf_content(content)
        elif file_ext == 'md':
            cls._scan_markdown_content(content)
    
    @classmethod
    def _scan_pdf_content(cls, content: bytes):
        """Additional PDF-specific security checks"""
        # Check for embedded JavaScript
        if b'/JS' in content or b'/JavaScript' in content:
            raise HTTPException(
                status_code=400,
                detail="PDF contains JavaScript which is not allowed"
            )
        
        # Check for forms and actions
        if b'/Action' in content or b'/OpenAction' in content:
            logger.warning("PDF contains actions - potential security risk")
    
    @classmethod
    def _scan_markdown_content(cls, content: bytes):
        """Additional Markdown-specific security checks"""
        try:
            text = content.decode('utf-8', errors='ignore')
            
            # Check for HTML script tags
            if '<script' in text.lower():
                raise HTTPException(
                    status_code=400,
                    detail="Markdown contains script tags which are not allowed"
                )
            
            # Check for data URLs that could contain malicious content
            if 'data:' in text.lower():
                logger.warning("Markdown contains data URLs - potential security risk")
                
        except Exception as e:
            logger.error(f"Error scanning markdown content: {e}")


def generate_secure_filename(original_filename: str, document_id: str) -> str:
    """Generate a secure filename for storage"""
    ext = Path(original_filename).suffix.lower()
    # Use document ID + hash of original filename for uniqueness
    filename_hash = hashlib.sha256(original_filename.encode()).hexdigest()[:16]
    return f"{document_id}_{filename_hash}{ext}"


def hash_sensitive_data(data: str) -> str:
    """Hash sensitive data for logging"""
    if not data:
        return "[empty]"
    
    # Hash the data and return first 8 characters for identification
    hashed = hashlib.sha256(data.encode()).hexdigest()
    return f"[hash:{hashed[:8]}]"