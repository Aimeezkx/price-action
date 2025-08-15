"""
Access control and user data protection utilities
"""

import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from uuid import UUID

from fastapi import HTTPException, Request
from sqlalchemy.orm import Session

from app.core.config import settings
from app.utils.logging import SecurityLogger

security_logger = SecurityLogger(__name__)


class AccessController:
    """Access control for user data and operations"""
    
    # Rate limiting: requests per minute per IP
    RATE_LIMITS = {
        'upload': 5,      # 5 uploads per minute
        'search': 30,     # 30 searches per minute
        'review': 100,    # 100 reviews per minute
        'export': 2,      # 2 exports per minute
    }
    
    # Session tracking for rate limiting
    _request_tracking: Dict[str, Dict[str, list]] = {}
    
    @classmethod
    def check_rate_limit(cls, request: Request, operation: str) -> bool:
        """Check if request is within rate limits"""
        client_ip = cls._get_client_ip(request)
        current_time = datetime.now()
        
        # Initialize tracking for this IP if not exists
        if client_ip not in cls._request_tracking:
            cls._request_tracking[client_ip] = {}
        
        if operation not in cls._request_tracking[client_ip]:
            cls._request_tracking[client_ip][operation] = []
        
        # Clean old requests (older than 1 minute)
        cutoff_time = current_time - timedelta(minutes=1)
        cls._request_tracking[client_ip][operation] = [
            req_time for req_time in cls._request_tracking[client_ip][operation]
            if req_time > cutoff_time
        ]
        
        # Check rate limit
        request_count = len(cls._request_tracking[client_ip][operation])
        limit = cls.RATE_LIMITS.get(operation, 10)
        
        if request_count >= limit:
            security_logger.log_security_event(
                "rate_limit_exceeded",
                {
                    "ip_address": client_ip,
                    "operation": operation,
                    "request_count": request_count,
                    "limit": limit
                },
                "WARNING"
            )
            return False
        
        # Add current request
        cls._request_tracking[client_ip][operation].append(current_time)
        return True
    
    @classmethod
    def _get_client_ip(cls, request: Request) -> str:
        """Get client IP address from request"""
        # Check for forwarded headers first
        forwarded_for = request.headers.get('X-Forwarded-For')
        if forwarded_for:
            return forwarded_for.split(',')[0].strip()
        
        real_ip = request.headers.get('X-Real-IP')
        if real_ip:
            return real_ip
        
        # Fallback to direct client IP
        return request.client.host if request.client else "unknown"
    
    @classmethod
    def validate_document_access(cls, document_id: UUID, user_id: Optional[str] = None) -> bool:
        """Validate user access to document"""
        # For now, allow access to all documents
        # In a multi-user system, this would check ownership/permissions
        return True
    
    @classmethod
    def sanitize_user_input(cls, input_data: str, max_length: int = 1000) -> str:
        """Sanitize user input to prevent injection attacks"""
        if not input_data:
            return ""
        
        # Limit length
        if len(input_data) > max_length:
            input_data = input_data[:max_length]
        
        # Remove potentially dangerous characters
        dangerous_chars = ['<', '>', '"', "'", '&', '\x00', '\r']
        for char in dangerous_chars:
            input_data = input_data.replace(char, '')
        
        return input_data.strip()
    
    @classmethod
    def generate_secure_token(cls, length: int = 32) -> str:
        """Generate a secure random token"""
        return secrets.token_urlsafe(length)
    
    @classmethod
    def hash_user_identifier(cls, identifier: str) -> str:
        """Hash user identifier for privacy"""
        if not identifier:
            return "anonymous"
        
        # Use SHA-256 with salt for consistent hashing
        salt = "document_learning_app_salt"  # In production, use environment variable
        return hashlib.sha256(f"{salt}{identifier}".encode()).hexdigest()[:16]


class DataProtection:
    """Data protection utilities"""
    
    @classmethod
    def anonymize_document_metadata(cls, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Anonymize sensitive metadata"""
        if not settings.anonymize_logs:
            return metadata
        
        anonymized = metadata.copy()
        
        # Anonymize sensitive fields
        sensitive_fields = ['author', 'creator', 'producer', 'title', 'subject']
        for field in sensitive_fields:
            if field in anonymized:
                anonymized[field] = f"[{field}:anonymized]"
        
        # Remove creation/modification dates if present
        date_fields = ['creation_date', 'modification_date', 'created', 'modified']
        for field in date_fields:
            if field in anonymized:
                anonymized[field] = "[date:anonymized]"
        
        return anonymized
    
    @classmethod
    def clean_text_content(cls, text: str) -> str:
        """Clean text content of potentially sensitive information"""
        if not text or not settings.anonymize_logs:
            return text
        
        # Remove email addresses
        import re
        text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[email]', text)
        
        # Remove phone numbers (basic patterns)
        text = re.sub(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', '[phone]', text)
        text = re.sub(r'\b\(\d{3}\)\s?\d{3}[-.]?\d{4}\b', '[phone]', text)
        
        # Remove potential SSNs
        text = re.sub(r'\b\d{3}-\d{2}-\d{4}\b', '[ssn]', text)
        
        return text
    
    @classmethod
    def secure_delete_file(cls, file_path: str) -> bool:
        """Securely delete a file by overwriting it"""
        try:
            import os
            
            if not os.path.exists(file_path):
                return True
            
            # Get file size
            file_size = os.path.getsize(file_path)
            
            # Overwrite with random data multiple times
            with open(file_path, 'r+b') as file:
                for _ in range(3):  # 3 passes
                    file.seek(0)
                    file.write(secrets.token_bytes(file_size))
                    file.flush()
                    os.fsync(file.fileno())
            
            # Finally delete the file
            os.remove(file_path)
            return True
            
        except Exception as e:
            security_logger.log_error(e, {"file_path": file_path, "operation": "secure_delete"})
            return False


def require_rate_limit(operation: str):
    """Decorator to enforce rate limiting on endpoints"""
    def decorator(func):
        async def wrapper(request: Request, *args, **kwargs):
            if not AccessController.check_rate_limit(request, operation):
                raise HTTPException(
                    status_code=429,
                    detail=f"Rate limit exceeded for {operation}. Please try again later."
                )
            return await func(request, *args, **kwargs)
        return wrapper
    return decorator