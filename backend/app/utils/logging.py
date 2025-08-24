"""Enhanced logging utilities with sanitization."""

import logging
import re
import json
from datetime import datetime
from typing import Any, Dict, Optional
from pathlib import Path

try:
    from app.core.config import settings
except ImportError:
    # Fallback for testing
    class MockSettings:
        privacy_mode = False
    settings = MockSettings()

try:
    from app.utils.security import mask_sensitive_data
except ImportError:
    # Fallback implementation
    import re
    def mask_sensitive_data(data: str, mask_char: str = '*') -> str:
        if not data:
            return data
        # Basic email masking
        data = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', 
                      '***@***.***', data)
        # Basic SSN masking
        data = re.sub(r'\b\d{3}-\d{2}-\d{4}\b', '***-**-****', data)
        return data


class SanitizedFormatter(logging.Formatter):
    """Custom formatter that sanitizes sensitive data."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sensitive_patterns = {
            # Email addresses
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b': '***@***.***',
            # Phone numbers
            r'\b\+?1?[-.\s]?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}\b': '***-***-****',
            # SSN
            r'\b\d{3}-\d{2}-\d{4}\b': '***-**-****',
            # Credit card numbers
            r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b': '****-****-****-****',
            # IP addresses
            r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b': '***.***.***.***',
            # Names (basic pattern)
            r'\b[A-Z][a-z]+\s+[A-Z][a-z]+\b': '*** ***',
            # Dates (YYYY-MM-DD)
            r'\b\d{4}-\d{2}-\d{2}\b': '****-**-**',
            # File paths with sensitive info
            r'[/\\]([^/\\]*(?:medical|personal|private|confidential|secret)[^/\\]*)[/\\]': '/[REDACTED]/',
        }
    
    def format(self, record):
        # Format the record normally first
        formatted = super().format(record)
        
        # Apply sanitization based on log level
        if record.levelno >= logging.ERROR:
            # Less aggressive sanitization for errors (for debugging)
            formatted = self._sanitize_light(formatted)
        else:
            # More aggressive sanitization for info/debug
            formatted = self._sanitize_full(formatted)
        
        return formatted
    
    def _sanitize_light(self, message: str) -> str:
        """Light sanitization - only critical PII."""
        critical_patterns = {
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b': '***@***.***',
            r'\b\d{3}-\d{2}-\d{4}\b': '***-**-****',
            r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b': '****-****-****-****',
        }
        
        for pattern, replacement in critical_patterns.items():
            message = re.sub(pattern, replacement, message)
        
        return message
    
    def _sanitize_full(self, message: str) -> str:
        """Full sanitization - all sensitive patterns."""
        for pattern, replacement in self.sensitive_patterns.items():
            message = re.sub(pattern, replacement, message, flags=re.IGNORECASE)
        
        return message


class SanitizedLogger:
    """Logger with built-in sanitization."""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self._setup_logger()
    
    def _setup_logger(self):
        """Setup logger with sanitized formatter."""
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = SanitizedFormatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def debug(self, message: str, extra: Optional[Dict[str, Any]] = None):
        """Log debug message with sanitization."""
        self.logger.debug(self._sanitize_message(message), extra=extra)
    
    def info(self, message: str, extra: Optional[Dict[str, Any]] = None):
        """Log info message with sanitization."""
        self.logger.info(self._sanitize_message(message), extra=extra)
    
    def warning(self, message: str, extra: Optional[Dict[str, Any]] = None):
        """Log warning message with sanitization."""
        self.logger.warning(self._sanitize_message(message), extra=extra)
    
    def error(self, message: str, extra: Optional[Dict[str, Any]] = None):
        """Log error message with sanitization."""
        self.logger.error(self._sanitize_message(message), extra=extra)
    
    def critical(self, message: str, extra: Optional[Dict[str, Any]] = None):
        """Log critical message with sanitization."""
        self.logger.critical(self._sanitize_message(message), extra=extra)
    
    def _sanitize_message(self, message: str) -> str:
        """Sanitize log message."""
        return mask_sensitive_data(message)


def sanitize_log_data(data: Any) -> Any:
    """Sanitize data for logging."""
    if isinstance(data, str):
        return mask_sensitive_data(data)
    elif isinstance(data, dict):
        return {key: sanitize_log_data(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [sanitize_log_data(item) for item in data]
    else:
        return data


class SecurityLogger:
    """Specialized logger for security events."""
    
    def __init__(self, name: str = 'security'):
        self.logger = logging.getLogger(name)
        self._setup_security_logger()
    
    def _setup_security_logger(self):
        """Setup security logger with file handler."""
        if not self.logger.handlers:
            # Create logs directory if it doesn't exist
            log_dir = Path('logs')
            log_dir.mkdir(exist_ok=True)
            
            # File handler for security logs
            file_handler = logging.FileHandler(log_dir / 'security.log')
            file_formatter = SanitizedFormatter(
                '%(asctime)s - SECURITY - %(levelname)s - %(message)s'
            )
            file_handler.setFormatter(file_formatter)
            
            # Console handler
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(file_formatter)
            
            self.logger.addHandler(file_handler)
            self.logger.addHandler(console_handler)
            self.logger.setLevel(logging.INFO)
    
    def log_event(self, event_type: str, details: Dict[str, Any], severity: str = 'INFO'):
        """Log security event."""
        sanitized_details = sanitize_log_data(details)
        
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'event_type': event_type,
            'severity': severity,
            'details': sanitized_details
        }
        
        message = f"Security Event: {json.dumps(log_entry)}"
        
        if severity == 'CRITICAL':
            self.logger.critical(message)
        elif severity == 'HIGH':
            self.logger.error(message)
        elif severity == 'MEDIUM':
            self.logger.warning(message)
        else:
            self.logger.info(message)
    
    def log_authentication_attempt(self, username: str, success: bool, ip: str, user_agent: str):
        """Log authentication attempt."""
        self.log_event(
            'authentication_attempt',
            {
                'username': username,
                'success': success,
                'ip': ip,
                'user_agent': user_agent
            },
            'HIGH' if not success else 'INFO'
        )
    
    def log_file_upload(self, filename: str, user_id: str, success: bool, reason: str = None):
        """Log file upload attempt."""
        self.log_event(
            'file_upload',
            {
                'filename': filename,
                'user_id': user_id,
                'success': success,
                'reason': reason
            },
            'MEDIUM' if not success else 'INFO'
        )
    
    def log_permission_denied(self, user_id: str, resource: str, action: str):
        """Log permission denied event."""
        self.log_event(
            'permission_denied',
            {
                'user_id': user_id,
                'resource': resource,
                'action': action
            },
            'MEDIUM'
        )
    
    def log_suspicious_activity(self, activity_type: str, details: Dict[str, Any]):
        """Log suspicious activity."""
        self.log_event(
            'suspicious_activity',
            {
                'activity_type': activity_type,
                **details
            },
            'HIGH'
        )
    
    def log_security_event(self, event_type: str, details: Dict[str, Any], severity: str = 'INFO'):
        """Log security event - alias for log_event."""
        self.log_event(event_type, details, severity)
    
    def log_error(self, error: Exception, details: Dict[str, Any] = None):
        """Log error with details."""
        error_details = {
            'error_type': type(error).__name__,
            'error_message': str(error),
            **(details or {})
        }
        self.log_event('error', error_details, 'HIGH')


class AuditLogger:
    """Logger for audit trail."""
    
    def __init__(self):
        self.logger = logging.getLogger('audit')
        self._setup_audit_logger()
    
    def _setup_audit_logger(self):
        """Setup audit logger."""
        if not self.logger.handlers:
            log_dir = Path('logs')
            log_dir.mkdir(exist_ok=True)
            
            file_handler = logging.FileHandler(log_dir / 'audit.log')
            formatter = SanitizedFormatter(
                '%(asctime)s - AUDIT - %(message)s'
            )
            file_handler.setFormatter(formatter)
            
            self.logger.addHandler(file_handler)
            self.logger.setLevel(logging.INFO)
    
    def log_action(self, user_id: str, action: str, resource: str, details: Dict[str, Any] = None):
        """Log user action for audit trail."""
        audit_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'user_id': user_id,
            'action': action,
            'resource': resource,
            'details': sanitize_log_data(details or {})
        }
        
        self.logger.info(json.dumps(audit_entry))


# Global logger instances
security_logger = SecurityLogger()
audit_logger = AuditLogger()


def get_sanitized_logger(name: str) -> SanitizedLogger:
    """Get sanitized logger instance."""
    return SanitizedLogger(name)


def setup_logging():
    """Setup application logging."""
    # Create logs directory
    log_dir = Path('logs')
    log_dir.mkdir(exist_ok=True)
    
    # Setup root logger
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / 'app.log'),
            logging.StreamHandler()
        ]
    )
    
    # Set up sanitized formatter for all handlers
    for handler in logging.root.handlers:
        if not isinstance(handler.formatter, SanitizedFormatter):
            handler.setFormatter(SanitizedFormatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            ))


def setup_privacy_logging():
    """Setup privacy-aware logging configuration."""
    # Create logs directory
    log_dir = Path('logs')
    log_dir.mkdir(exist_ok=True)
    
    # Setup privacy-aware formatters
    privacy_formatter = SanitizedFormatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Configure root logger with privacy formatter
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # Remove existing handlers to avoid duplicates
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Add file handler with privacy formatter
    file_handler = logging.FileHandler(log_dir / 'app.log')
    file_handler.setFormatter(privacy_formatter)
    root_logger.addHandler(file_handler)
    
    # Add console handler with privacy formatter
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(privacy_formatter)
    root_logger.addHandler(console_handler)
    
    # Setup security and audit loggers
    security_logger._setup_security_logger()
    audit_logger._setup_audit_logger()


# Initialize logging on import
setup_logging()