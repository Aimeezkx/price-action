"""Access control and authentication utilities."""

import jwt
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any
from functools import wraps
from fastapi import HTTPException, status, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

try:
    from app.core.config import settings
except ImportError:
    # Fallback for testing
    class MockSettings:
        secret_key = "test_secret_key_for_testing_only"
        api_keys = []
    settings = MockSettings()

try:
    from app.utils.security import log_security_event, get_client_ip
except ImportError:
    # Fallback for testing
    def log_security_event(*args, **kwargs):
        pass
    def get_client_ip(request):
        return "127.0.0.1"


# JWT Configuration
SECRET_KEY = getattr(settings, 'secret_key', 'test_secret_key_for_testing_only')
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7


class UserRole(Enum):
    """User roles."""
    ADMIN = "admin"
    USER = "user"
    GUEST = "guest"


class RolePermissions:
    """Role-based permissions."""
    
    PERMISSIONS = {
        UserRole.ADMIN: {
            "read_all_documents",
            "read_own_documents",
            "upload_documents",
            "delete_any_document",
            "delete_own_document",
            "manage_users",
            "view_analytics",
            "export_data",
            "manage_system",
            "access_admin_panel"
        },
        UserRole.USER: {
            "read_own_documents",
            "upload_documents",
            "delete_own_document",
            "export_own_data",
            "create_cards",
            "review_cards",
            "search_content"
        },
        UserRole.GUEST: {
            "read_public_documents",
            "search_public_content"
        }
    }
    
    @classmethod
    def get_permissions(cls, role: UserRole) -> set:
        """Get permissions for a role."""
        return cls.PERMISSIONS.get(role, set())
    
    @classmethod
    def has_permission(cls, role: UserRole, permission: str) -> bool:
        """Check if role has specific permission."""
        return permission in cls.get_permissions(role)


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token."""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "type": "access"})
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: Dict[str, Any]) -> str:
    """Create JWT refresh token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Dict[str, Any]:
    """Verify and decode JWT token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )


def check_permissions(role: UserRole, required_permission: str) -> bool:
    """Check if user role has required permission."""
    return RolePermissions.has_permission(role, required_permission)


# Security scheme
security = HTTPBearer()


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """Get current authenticated user."""
    token = credentials.credentials
    payload = verify_token(token)
    
    # Validate token type
    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type"
        )
    
    return payload


async def get_current_active_user(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """Get current active user."""
    # Add additional checks here (e.g., user is active, not banned, etc.)
    return current_user


def require_permission(permission: str):
    """Decorator to require specific permission."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get current user from kwargs or dependency injection
            current_user = kwargs.get('current_user')
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            user_role = UserRole(current_user.get('role', 'guest'))
            
            if not check_permissions(user_role, permission):
                log_security_event(
                    "permission_denied",
                    {
                        "user_id": current_user.get('user_id'),
                        "role": user_role.value,
                        "required_permission": permission,
                        "endpoint": func.__name__
                    },
                    "MEDIUM"
                )
                
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def require_role(required_role: UserRole):
    """Decorator to require specific role."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get('current_user')
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            user_role = UserRole(current_user.get('role', 'guest'))
            
            if user_role != required_role:
                log_security_event(
                    "role_access_denied",
                    {
                        "user_id": current_user.get('user_id'),
                        "user_role": user_role.value,
                        "required_role": required_role.value,
                        "endpoint": func.__name__
                    },
                    "MEDIUM"
                )
                
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Role {required_role.value} required"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


class APIKeyValidator:
    """API key validation for service accounts."""
    
    def __init__(self):
        self.valid_keys = set(settings.api_keys) if hasattr(settings, 'api_keys') else set()
    
    def validate_api_key(self, api_key: str) -> bool:
        """Validate API key."""
        return api_key in self.valid_keys
    
    def get_api_key_info(self, api_key: str) -> Optional[Dict[str, Any]]:
        """Get API key information."""
        if not self.validate_api_key(api_key):
            return None
        
        # In a real implementation, this would fetch from database
        return {
            "key": api_key,
            "permissions": ["read_documents", "upload_documents"],
            "rate_limit": 1000,
            "expires": None
        }


api_key_validator = APIKeyValidator()


def validate_api_key(api_key: str) -> bool:
    """Validate API key."""
    return api_key_validator.validate_api_key(api_key)


async def get_api_key_user(request: Request) -> Optional[Dict[str, Any]]:
    """Get user info from API key."""
    api_key = request.headers.get("X-API-Key")
    if not api_key:
        return None
    
    if not validate_api_key(api_key):
        log_security_event(
            "invalid_api_key",
            {
                "api_key": api_key[:8] + "...",  # Log only first 8 chars
                "ip": get_client_ip(request),
                "user_agent": request.headers.get("User-Agent", "")
            },
            "HIGH"
        )
        return None
    
    return {
        "user_id": f"api_key_{api_key[:8]}",
        "username": "api_user",
        "role": "user",
        "auth_type": "api_key"
    }


class SessionManager:
    """Manage user sessions."""
    
    def __init__(self):
        # In production, use Redis or database
        self.active_sessions = {}
        self.max_sessions_per_user = 5
    
    def create_session(self, user_id: str, token: str, ip: str, user_agent: str) -> str:
        """Create new session."""
        session_id = f"{user_id}_{datetime.utcnow().timestamp()}"
        
        if user_id not in self.active_sessions:
            self.active_sessions[user_id] = []
        
        # Remove old sessions if limit exceeded
        if len(self.active_sessions[user_id]) >= self.max_sessions_per_user:
            self.active_sessions[user_id].pop(0)
        
        session_info = {
            "session_id": session_id,
            "token": token,
            "ip": ip,
            "user_agent": user_agent,
            "created_at": datetime.utcnow(),
            "last_activity": datetime.utcnow()
        }
        
        self.active_sessions[user_id].append(session_info)
        return session_id
    
    def validate_session(self, user_id: str, token: str) -> bool:
        """Validate session."""
        if user_id not in self.active_sessions:
            return False
        
        for session in self.active_sessions[user_id]:
            if session["token"] == token:
                session["last_activity"] = datetime.utcnow()
                return True
        
        return False
    
    def invalidate_session(self, user_id: str, token: str) -> bool:
        """Invalidate specific session."""
        if user_id not in self.active_sessions:
            return False
        
        self.active_sessions[user_id] = [
            session for session in self.active_sessions[user_id]
            if session["token"] != token
        ]
        return True
    
    def invalidate_all_sessions(self, user_id: str) -> bool:
        """Invalidate all sessions for user."""
        if user_id in self.active_sessions:
            del self.active_sessions[user_id]
            return True
        return False


session_manager = SessionManager()


class RateLimiter:
    """Rate limiting for API endpoints."""
    
    def __init__(self):
        # In production, use Redis
        self.requests = {}
        self.limits = {
            "login": {"count": 5, "window": 300},  # 5 attempts per 5 minutes
            "upload": {"count": 10, "window": 3600},  # 10 uploads per hour
            "search": {"count": 100, "window": 3600},  # 100 searches per hour
            "api": {"count": 1000, "window": 3600}  # 1000 API calls per hour
        }
    
    def is_rate_limited(self, identifier: str, action: str) -> bool:
        """Check if request is rate limited."""
        if action not in self.limits:
            return False
        
        limit_config = self.limits[action]
        key = f"{action}:{identifier}"
        now = datetime.utcnow()
        
        if key not in self.requests:
            self.requests[key] = []
        
        # Remove old requests outside the window
        window_start = now - timedelta(seconds=limit_config["window"])
        self.requests[key] = [
            req_time for req_time in self.requests[key]
            if req_time > window_start
        ]
        
        # Check if limit exceeded
        if len(self.requests[key]) >= limit_config["count"]:
            return True
        
        # Add current request
        self.requests[key].append(now)
        return False


rate_limiter = RateLimiter()


def check_rate_limit(identifier: str, action: str) -> bool:
    """Check rate limit for action."""
    return rate_limiter.is_rate_limited(identifier, action)


class DataProtection:
    """Data protection and privacy utilities."""
    
    def __init__(self):
        self.privacy_mode = getattr(settings, 'privacy_mode', False)
    
    def anonymize_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Anonymize sensitive data."""
        if not self.privacy_mode:
            return data
        
        anonymized = data.copy()
        
        # Remove or mask sensitive fields
        sensitive_fields = ['email', 'phone', 'ssn', 'credit_card', 'ip_address']
        
        for field in sensitive_fields:
            if field in anonymized:
                if field == 'email':
                    anonymized[field] = self._mask_email(anonymized[field])
                elif field == 'phone':
                    anonymized[field] = self._mask_phone(anonymized[field])
                else:
                    anonymized[field] = '***REDACTED***'
        
        return anonymized
    
    def _mask_email(self, email: str) -> str:
        """Mask email address."""
        if '@' not in email:
            return '***REDACTED***'
        
        local, domain = email.split('@', 1)
        if len(local) <= 2:
            masked_local = '*' * len(local)
        else:
            masked_local = local[0] + '*' * (len(local) - 2) + local[-1]
        
        return f"{masked_local}@{domain}"
    
    def _mask_phone(self, phone: str) -> str:
        """Mask phone number."""
        if len(phone) < 4:
            return '*' * len(phone)
        
        return '*' * (len(phone) - 4) + phone[-4:]
    
    def check_data_retention(self, created_at: datetime, retention_days: int = 365) -> bool:
        """Check if data should be retained."""
        if not self.privacy_mode:
            return True
        
        retention_limit = datetime.utcnow() - timedelta(days=retention_days)
        return created_at > retention_limit
    
    def get_user_data(self, user_id: str) -> Dict[str, Any]:
        """Get user data for privacy requests."""
        # This would typically fetch from database
        # Placeholder implementation
        return {
            "user_id": user_id,
            "data_collected": [],
            "processing_purposes": [],
            "retention_period": "365 days",
            "third_party_sharing": False
        }
    
    def delete_user_data(self, user_id: str) -> bool:
        """Delete user data for privacy requests."""
        # This would typically delete from database
        # Placeholder implementation
        log_security_event(
            "user_data_deletion",
            {"user_id": user_id},
            "INFO"
        )
        return True


class AccessController:
    """Access control utilities."""
    
    def __init__(self):
        self.rate_limiter = rate_limiter
        self.session_manager = session_manager
    
    def check_document_access(self, user_id: str, document_id: str, action: str) -> bool:
        """Check if user has access to document."""
        # This would typically check database permissions
        # Placeholder implementation
        return True
    
    def check_resource_access(self, user_id: str, resource_type: str, resource_id: str) -> bool:
        """Check if user has access to resource."""
        # This would typically check database permissions
        # Placeholder implementation
        return True
    
    def log_access_attempt(self, user_id: str, resource: str, action: str, success: bool):
        """Log access attempt."""
        log_security_event(
            "access_attempt",
            {
                "user_id": user_id,
                "resource": resource,
                "action": action,
                "success": success
            },
            "INFO" if success else "MEDIUM"
        )


def require_rate_limit(action: str, limit: int = None):
    """Decorator to enforce rate limiting."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get request from args/kwargs
            request = None
            for arg in args:
                if hasattr(arg, 'client'):  # FastAPI Request object
                    request = arg
                    break
            
            if not request:
                # If no request found, skip rate limiting
                return await func(*args, **kwargs)
            
            # Get client identifier
            client_ip = get_client_ip(request)
            
            # Check rate limit
            if check_rate_limit(client_ip, action):
                log_security_event(
                    "rate_limit_exceeded",
                    {
                        "ip": client_ip,
                        "action": action,
                        "endpoint": func.__name__
                    },
                    "MEDIUM"
                )
                
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Rate limit exceeded"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator