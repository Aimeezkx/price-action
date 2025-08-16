"""Access control and authentication utilities."""

import jwt
import os
import re
from pathlib import Path
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


class AccessController:
    """Simple access control utilities."""

    @staticmethod
    def _get_client_ip(request: Request) -> str:
        return get_client_ip(request)

    @staticmethod
    def check_rate_limit(request: Request, action: str) -> bool:
        identifier = AccessController._get_client_ip(request)
        return not check_rate_limit(identifier, action)


def require_rate_limit(action: str):
    """Decorator enforcing rate limits based on client IP."""
    def decorator(func):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            if not AccessController.check_rate_limit(request, action):
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Rate limit exceeded",
                )
            return await func(request, *args, **kwargs)

        return wrapper

    return decorator


class DataProtection:
    """Basic data protection helpers."""

    @staticmethod
    def anonymize_document_metadata(metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Anonymize sensitive metadata fields."""
        if not getattr(settings, "anonymize_logs", False):
            return metadata

        anonymized = metadata.copy()
        if "author" in anonymized:
            anonymized["author"] = "[author:anonymized]"
        if "title" in anonymized:
            anonymized["title"] = "[title:anonymized]"
        if "creation_date" in anonymized:
            anonymized["creation_date"] = "[date:anonymized]"
        return anonymized

    @staticmethod
    def clean_text_content(text: str) -> str:
        """Remove sensitive data like emails and phone numbers from text."""
        if not getattr(settings, "anonymize_logs", False):
            return text
        text = re.sub(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}", "[email]", text)
        text = re.sub(r"\b\d{3}-\d{3}-\d{4}\b", "[phone]", text)
        return text

    @staticmethod
    def secure_delete_file(path: str | Path) -> bool:
        """Securely delete file by overwriting before removal."""
        try:
            p = Path(path)
            if not p.exists():
                return True
            size = p.stat().st_size
            with open(p, "ba", buffering=0) as f:
                f.seek(0)
                f.write(b"\x00" * size)
            p.unlink()
            return True
        except Exception:
            return False

