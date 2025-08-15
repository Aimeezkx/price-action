"""
Privacy-aware logging utilities
"""

import hashlib
import logging
import re
from pathlib import Path
from typing import Any, Dict, Optional

from app.core.config import settings


class PrivacyFilter(logging.Filter):
    """Filter to anonymize sensitive data in log messages"""
    
    # Patterns to anonymize
    SENSITIVE_PATTERNS = [
        # File paths (absolute paths only)
        (r'/(?:home|Users|Documents|Desktop)/[^\s]+', lambda m: f"[path:{_hash_data(m.group())}]"),
        # Email addresses
        (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', lambda m: f"[email:{_hash_data(m.group())}]"),
        # IP addresses
        (r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b', lambda m: f"[ip:{_hash_data(m.group())}]"),
        # File names with extensions (but not common words)
        (r'\b[\w\-]+\.(pdf|docx|md|txt|doc)\b', lambda m: f"[file:{_hash_data(m.group())}]"),
    ]
    
    def filter(self, record: logging.LogRecord) -> bool:
        """Filter and anonymize log record"""
        if not settings.anonymize_logs:
            return True
            
        # Anonymize the message
        if hasattr(record, 'msg') and record.msg:
            record.msg = self._anonymize_message(str(record.msg))
        
        # Anonymize arguments
        if hasattr(record, 'args') and record.args:
            record.args = tuple(
                self._anonymize_message(str(arg)) if isinstance(arg, str) else arg
                for arg in record.args
            )
        
        return True
    
    def _anonymize_message(self, message: str) -> str:
        """Anonymize sensitive data in a message"""
        for pattern, replacement in self.SENSITIVE_PATTERNS:
            message = re.sub(pattern, replacement, message, flags=re.IGNORECASE)
        return message


def _hash_data(data: str) -> str:
    """Hash data for anonymization"""
    return hashlib.sha256(data.encode()).hexdigest()[:8]


class SecurityLogger:
    """Security-focused logger with privacy features"""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        
        # Add privacy filter if anonymization is enabled
        if settings.anonymize_logs:
            privacy_filter = PrivacyFilter()
            self.logger.addFilter(privacy_filter)
    
    def log_file_upload(self, filename: str, file_size: int, user_id: Optional[str] = None):
        """Log file upload with privacy protection"""
        if settings.anonymize_logs:
            filename_hash = _hash_data(filename)
            user_hash = _hash_data(user_id) if user_id else "anonymous"
            self.logger.info(f"File upload: [file:{filename_hash}] size={file_size} user=[user:{user_hash}]")
        else:
            self.logger.info(f"File upload: {filename} size={file_size} user={user_id}")
    
    def log_processing_start(self, document_id: str, filename: str):
        """Log document processing start"""
        if settings.anonymize_logs:
            filename_hash = _hash_data(filename)
            self.logger.info(f"Processing started: doc_id={document_id} file=[file:{filename_hash}]")
        else:
            self.logger.info(f"Processing started: doc_id={document_id} file={filename}")
    
    def log_processing_complete(self, document_id: str, chapters: int, cards: int, duration: float):
        """Log processing completion"""
        self.logger.info(
            f"Processing complete: doc_id={document_id} chapters={chapters} "
            f"cards={cards} duration={duration:.2f}s"
        )
    
    def log_security_event(self, event_type: str, details: Dict[str, Any], severity: str = "WARNING"):
        """Log security events"""
        # Always log security events but anonymize sensitive details
        anonymized_details = {}
        for key, value in details.items():
            if key in ['filename', 'filepath', 'user_id', 'ip_address']:
                anonymized_details[key] = f"[{key}:{_hash_data(str(value))}]"
            else:
                anonymized_details[key] = value
        
        log_method = getattr(self.logger, severity.lower(), self.logger.warning)
        log_method(f"Security event: {event_type} - {anonymized_details}")
    
    def log_api_access(self, endpoint: str, method: str, user_id: Optional[str] = None, 
                      ip_address: Optional[str] = None):
        """Log API access"""
        if settings.anonymize_logs:
            user_hash = _hash_data(user_id) if user_id else "anonymous"
            ip_hash = _hash_data(ip_address) if ip_address else "unknown"
            self.logger.info(f"API access: {method} {endpoint} user=[user:{user_hash}] ip=[ip:{ip_hash}]")
        else:
            self.logger.info(f"API access: {method} {endpoint} user={user_id} ip={ip_address}")
    
    def log_error(self, error: Exception, context: Dict[str, Any]):
        """Log errors with context"""
        # Anonymize context data
        anonymized_context = {}
        for key, value in context.items():
            if key in ['filename', 'filepath', 'user_id']:
                anonymized_context[key] = f"[{key}:{_hash_data(str(value))}]"
            else:
                anonymized_context[key] = value
        
        self.logger.error(f"Error: {type(error).__name__}: {error} - Context: {anonymized_context}")


def setup_privacy_logging():
    """Setup privacy-aware logging configuration"""
    # Configure root logger
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Add privacy filter to all loggers if anonymization is enabled
    if settings.anonymize_logs:
        privacy_filter = PrivacyFilter()
        
        # Add to root logger
        root_logger = logging.getLogger()
        root_logger.addFilter(privacy_filter)
        
        # Add to specific loggers
        for logger_name in ['uvicorn', 'fastapi', 'sqlalchemy']:
            logger = logging.getLogger(logger_name)
            logger.addFilter(privacy_filter)


# Initialize privacy logging
setup_privacy_logging()