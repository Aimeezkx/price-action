"""Security utilities and functions."""

import re
import hashlib
import secrets
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any
import bcrypt
import html
from datetime import datetime, timedelta

try:
    from app.core.config import settings
except ImportError:
    # Fallback for testing
    class MockSettings:
        secret_key = "test_secret_key_for_testing_only"
    settings = MockSettings()


class SecurityError(Exception):
    """Exception raised for security-related errors."""
    pass


def hash_password(password: str) -> str:
    """Hash password using bcrypt."""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def verify_password(password: str, hashed: str) -> bool:
    """Verify password against hash."""
    try:
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    except Exception:
        return False


def generate_secure_token(length: int = 32) -> str:
    """Generate cryptographically secure random token."""
    return secrets.token_urlsafe(length)


def sanitize_input(input_string: str) -> str:
    """Sanitize user input to prevent injection attacks."""
    if not isinstance(input_string, str):
        return str(input_string)
    
    # Remove null bytes
    sanitized = input_string.replace('\x00', '')
    
    # Escape SQL injection characters
    sql_dangerous = ["'", '"', ';', '--', '/*', '*/', 'xp_', 'sp_']
    for dangerous in sql_dangerous:
        sanitized = sanitized.replace(dangerous, '')
    
    # Remove XSS patterns
    xss_patterns = [
        r'<script[^>]*>.*?</script>',
        r'javascript:',
        r'vbscript:',
        r'on\w+\s*=',
        r'<iframe[^>]*>.*?</iframe>',
        r'<object[^>]*>.*?</object>',
        r'<embed[^>]*>.*?</embed>',
    ]
    
    for pattern in xss_patterns:
        sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE | re.DOTALL)
    
    # Additional cleanup for remaining dangerous characters
    sanitized = sanitized.replace('<', '').replace('>', '')
    sanitized = sanitized.replace('DROP TABLE', '').replace('drop table', '')
    
    return sanitized.strip()


def escape_html(text: str) -> str:
    """Escape HTML characters to prevent XSS."""
    return html.escape(text, quote=True)


def validate_sql_query(query: str) -> bool:
    """Validate SQL query for dangerous patterns."""
    if not isinstance(query, str):
        return False
    
    query_lower = query.lower().strip()
    
    # Check for dangerous SQL patterns
    dangerous_patterns = [
        r';\s*drop\s+table',
        r';\s*delete\s+from',
        r';\s*insert\s+into',
        r';\s*update\s+.*\s+set',
        r'union\s+select',
        r'or\s+1\s*=\s*1',
        r'or\s+\'1\'\s*=\s*\'1\'',
        r'exec\s+xp_',
        r'exec\s+sp_',
        r'information_schema',
        r'sys\.',
        r'master\.',
        r'waitfor\s+delay',
        r'pg_sleep',
        r'sleep\s*\(',
        r'benchmark\s*\(',
    ]
    
    for pattern in dangerous_patterns:
        if re.search(pattern, query_lower):
            return False
    
    return True


def scan_file_for_malware(file_path: Path) -> bool:
    """Scan file for malware using available scanners."""
    try:
        # Check if ClamAV is available
        if virus_scanner_available():
            result = scan_with_clamav(file_path)
            return result.get('infected', False)
        
        # Fallback to basic signature detection
        return detect_malicious_content(file_path)
    
    except Exception:
        # If scanning fails, err on the side of caution
        return True


def virus_scanner_available() -> bool:
    """Check if virus scanner is available."""
    try:
        subprocess.run(['clamscan', '--version'], 
                      capture_output=True, 
                      check=True, 
                      timeout=5)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        return False


def scan_with_clamav(file_path: Path) -> Dict[str, Any]:
    """Scan file with ClamAV."""
    try:
        result = subprocess.run([
            'clamscan', 
            '--no-summary',
            '--infected',
            str(file_path)
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 1:  # Virus found
            return {
                'infected': True,
                'virus': result.stdout.strip(),
                'scanner': 'clamav'
            }
        elif result.returncode == 0:  # Clean
            return {
                'infected': False,
                'scanner': 'clamav'
            }
        else:  # Error
            return {
                'infected': True,  # Err on the side of caution
                'error': result.stderr.strip(),
                'scanner': 'clamav'
            }
    
    except subprocess.TimeoutExpired:
        return {'infected': True, 'error': 'Scan timeout', 'scanner': 'clamav'}
    except Exception as e:
        return {'infected': True, 'error': str(e), 'scanner': 'clamav'}


def detect_malicious_content(file_path: Path) -> bool:
    """Detect malicious content using signature-based detection."""
    try:
        with open(file_path, 'rb') as f:
            content = f.read(1024 * 1024)  # Read first 1MB
        
        # Check for executable signatures
        executable_signatures = [
            b'MZ',  # PE executable
            b'\x7fELF',  # ELF executable
            b'\xca\xfe\xba\xbe',  # Java class file
            b'\xfe\xed\xfa\xce',  # Mach-O executable (32-bit)
            b'\xfe\xed\xfa\xcf',  # Mach-O executable (64-bit)
        ]
        
        for signature in executable_signatures:
            if content.startswith(signature):
                return True
        
        # Check for script content
        try:
            text_content = content.decode('utf-8', errors='ignore').lower()
            malicious_patterns = [
                'eval(',
                'exec(',
                'system(',
                'shell_exec(',
                'passthru(',
                'file_get_contents(',
                'curl_exec(',
                'base64_decode(',
                'gzinflate(',
                'str_rot13(',
                'javascript:',
                'vbscript:',
                '<script',
                '<?php',
                '<%',
                'document.write(',
                'document.cookie',
                'window.location',
            ]
            
            for pattern in malicious_patterns:
                if pattern in text_content:
                    return True
        
        except UnicodeDecodeError:
            pass  # Binary file, already checked signatures
        
        return False
    
    except Exception:
        return True  # Err on the side of caution


def generate_csrf_token() -> str:
    """Generate CSRF token."""
    return generate_secure_token(32)


def validate_csrf_token(token: str, expected: str) -> bool:
    """Validate CSRF token."""
    if not token or not expected:
        return False
    return secrets.compare_digest(token, expected)


def rate_limit_key(identifier: str, action: str) -> str:
    """Generate rate limiting key."""
    return f"rate_limit:{action}:{identifier}"


def check_rate_limit(identifier: str, action: str, limit: int, window: int) -> bool:
    """Check if action is rate limited."""
    # This would typically use Redis or similar
    # For now, return False (not rate limited) as placeholder
    return False


def secure_filename(filename: str) -> str:
    """Generate secure filename."""
    # Remove path components
    filename = filename.split('/')[-1].split('\\')[-1]
    
    # Remove dangerous characters
    filename = re.sub(r'[^\w\-_\.]', '_', filename)
    
    # Limit length
    if len(filename) > 255:
        name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
        max_name_length = 255 - len(ext) - 1 if ext else 255
        filename = name[:max_name_length] + ('.' + ext if ext else '')
    
    return filename


def generate_secure_filename(original_filename: str) -> str:
    """Generate secure filename with timestamp and random component."""
    import time
    
    # Get secure base filename
    secure_base = secure_filename(original_filename)
    
    # Split name and extension
    if '.' in secure_base:
        name, ext = secure_base.rsplit('.', 1)
    else:
        name, ext = secure_base, ''
    
    # Add timestamp and random component
    timestamp = str(int(time.time()))
    random_part = generate_secure_token(8)
    
    # Construct new filename
    new_name = f"{name}_{timestamp}_{random_part}"
    if ext:
        new_name += f".{ext}"
    
    return new_name


def validate_email(email: str) -> bool:
    """Validate email address format."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_password_strength(password: str) -> Dict[str, Any]:
    """Validate password strength."""
    result = {
        'is_valid': True,
        'score': 0,
        'issues': []
    }
    
    if len(password) < 8:
        result['issues'].append('Password must be at least 8 characters long')
        result['is_valid'] = False
    else:
        result['score'] += 1
    
    if not re.search(r'[a-z]', password):
        result['issues'].append('Password must contain lowercase letters')
        result['is_valid'] = False
    else:
        result['score'] += 1
    
    if not re.search(r'[A-Z]', password):
        result['issues'].append('Password must contain uppercase letters')
        result['is_valid'] = False
    else:
        result['score'] += 1
    
    if not re.search(r'\d', password):
        result['issues'].append('Password must contain numbers')
        result['is_valid'] = False
    else:
        result['score'] += 1
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        result['issues'].append('Password must contain special characters')
        result['is_valid'] = False
    else:
        result['score'] += 1
    
    # Check for common passwords
    common_passwords = [
        'password', '123456', 'password123', 'admin', 'qwerty',
        'letmein', 'welcome', 'monkey', '1234567890'
    ]
    
    if password.lower() in common_passwords:
        result['issues'].append('Password is too common')
        result['is_valid'] = False
        result['score'] = max(0, result['score'] - 2)
    
    return result


def get_client_ip(request) -> str:
    """Get client IP address from request."""
    # Check for forwarded IP first
    forwarded_for = request.headers.get('X-Forwarded-For')
    if forwarded_for:
        return forwarded_for.split(',')[0].strip()
    
    # Check for real IP
    real_ip = request.headers.get('X-Real-IP')
    if real_ip:
        return real_ip
    
    # Fall back to remote address
    return getattr(request.client, 'host', '127.0.0.1')


def log_security_event(event_type: str, details: Dict[str, Any], severity: str = 'INFO'):
    """Log security event."""
    from app.utils.logging import security_logger
    
    log_entry = {
        'timestamp': datetime.utcnow().isoformat(),
        'event_type': event_type,
        'severity': severity,
        'details': details
    }
    
    if severity == 'CRITICAL':
        security_logger.critical(f"Security Event: {log_entry}")
    elif severity == 'HIGH':
        security_logger.error(f"Security Event: {log_entry}")
    elif severity == 'MEDIUM':
        security_logger.warning(f"Security Event: {log_entry}")
    else:
        security_logger.info(f"Security Event: {log_entry}")


def mask_sensitive_data(data: str, mask_char: str = '*') -> str:
    """Mask sensitive data for logging."""
    if not data:
        return data
    
    # Email addresses
    data = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', 
                  lambda m: m.group(0)[:2] + mask_char * 3 + '@' + mask_char * 3 + '.' + mask_char * 3, 
                  data)
    
    # Phone numbers
    data = re.sub(r'\b\d{3}-\d{3}-\d{4}\b', mask_char * 3 + '-' + mask_char * 3 + '-' + mask_char * 4, data)
    data = re.sub(r'\b\+\d{1,3}-\d{3}-\d{3}-\d{4}\b', '+' + mask_char * 3 + '-' + mask_char * 3 + '-' + mask_char * 3 + '-' + mask_char * 4, data)
    
    # SSN
    data = re.sub(r'\b\d{3}-\d{2}-\d{4}\b', mask_char * 3 + '-' + mask_char * 2 + '-' + mask_char * 4, data)
    
    # Credit card numbers
    data = re.sub(r'\b\d{4}-\d{4}-\d{4}-\d{4}\b', mask_char * 4 + '-' + mask_char * 4 + '-' + mask_char * 4 + '-' + mask_char * 4, data)
    
    return data


class SecurityValidator:
    """Security validation utilities."""
    
    def __init__(self):
        self.max_file_size = 100 * 1024 * 1024  # 100MB
        self.allowed_extensions = {'.pdf', '.docx', '.doc', '.txt', '.md', '.rtf'}
    
    def validate_file_security(self, file_path: Path) -> Dict[str, Any]:
        """Validate file for security issues."""
        result = {
            'is_secure': True,
            'issues': [],
            'warnings': []
        }
        
        try:
            # Check file size
            file_size = file_path.stat().st_size
            if file_size > self.max_file_size:
                result['is_secure'] = False
                result['issues'].append(f'File too large: {file_size} bytes')
            
            # Check extension
            extension = file_path.suffix.lower()
            if extension not in self.allowed_extensions:
                result['is_secure'] = False
                result['issues'].append(f'File extension not allowed: {extension}')
            
            # Check for malicious content
            if detect_malicious_content(file_path):
                result['is_secure'] = False
                result['issues'].append('Potentially malicious content detected')
            
        except Exception as e:
            result['is_secure'] = False
            result['issues'].append(f'Validation error: {str(e)}')
        
        return result
    
    def sanitize_user_input(self, user_input: str) -> str:
        """Sanitize user input."""
        return sanitize_input(user_input)
    
    def validate_request_headers(self, headers: Dict[str, str]) -> bool:
        """Validate request headers for security."""
        # Check for suspicious headers
        suspicious_patterns = [
            'eval(',
            'javascript:',
            '<script',
            'data:text/html'
        ]
        
        for header_name, header_value in headers.items():
            if isinstance(header_value, str):
                for pattern in suspicious_patterns:
                    if pattern.lower() in header_value.lower():
                        return False
        
        return True