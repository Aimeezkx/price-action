"""Test access control and authentication."""

import pytest
import jwt
from datetime import datetime, timedelta
from unittest.mock import patch, Mock

from app.utils.access_control import (
    create_access_token, verify_token, check_permissions,
    RolePermissions, UserRole
)
from app.utils.security import hash_password, verify_password


class TestAccessControl:
    """Test access control and authentication mechanisms."""
    
    def test_password_hashing(self):
        """Test password hashing and verification."""
        password = "test_password_123"
        
        # Hash password
        hashed = hash_password(password)
        
        # Should not be the same as original
        assert hashed != password
        
        # Should verify correctly
        assert verify_password(password, hashed) is True
        
        # Should not verify incorrect password
        assert verify_password("wrong_password", hashed) is False
    
    def test_jwt_token_creation_and_verification(self):
        """Test JWT token creation and verification."""
        user_data = {
            "user_id": "123",
            "username": "testuser",
            "role": "user"
        }
        
        # Create token
        token = create_access_token(user_data)
        assert token is not None
        
        # Verify token
        decoded = verify_token(token)
        assert decoded["user_id"] == "123"
        assert decoded["username"] == "testuser"
        assert decoded["role"] == "user"
    
    def test_expired_token_rejection(self):
        """Test that expired tokens are rejected."""
        user_data = {"user_id": "123", "username": "testuser"}
        
        # Create token with short expiration
        with patch('app.utils.access_control.ACCESS_TOKEN_EXPIRE_MINUTES', -1):
            token = create_access_token(user_data)
        
        # Should raise exception for expired token
        with pytest.raises(jwt.ExpiredSignatureError):
            verify_token(token)
    
    def test_invalid_token_rejection(self):
        """Test that invalid tokens are rejected."""
        invalid_tokens = [
            "invalid.token.here",
            "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.invalid",
            "",
            None
        ]
        
        for token in invalid_tokens:
            with pytest.raises((jwt.InvalidTokenError, AttributeError, TypeError)):
                verify_token(token)
    
    def test_role_based_permissions(self):
        """Test role-based permission system."""
        # Test admin permissions
        admin_permissions = RolePermissions.get_permissions(UserRole.ADMIN)
        assert "read_all_documents" in admin_permissions
        assert "delete_any_document" in admin_permissions
        assert "manage_users" in admin_permissions
        
        # Test user permissions
        user_permissions = RolePermissions.get_permissions(UserRole.USER)
        assert "read_own_documents" in user_permissions
        assert "upload_documents" in user_permissions
        assert "manage_users" not in user_permissions
        
        # Test guest permissions
        guest_permissions = RolePermissions.get_permissions(UserRole.GUEST)
        assert "read_public_documents" in guest_permissions
        assert "upload_documents" not in guest_permissions
    
    def test_permission_checking(self):
        """Test permission checking functionality."""
        # Test admin can access everything
        assert check_permissions(UserRole.ADMIN, "delete_any_document") is True
        assert check_permissions(UserRole.ADMIN, "manage_users") is True
        
        # Test user has limited permissions
        assert check_permissions(UserRole.USER, "read_own_documents") is True
        assert check_permissions(UserRole.USER, "delete_any_document") is False
        
        # Test guest has minimal permissions
        assert check_permissions(UserRole.GUEST, "read_public_documents") is True
        assert check_permissions(UserRole.GUEST, "upload_documents") is False
    
    def test_authentication_required_endpoints(self, security_test_client):
        """Test that protected endpoints require authentication."""
        protected_endpoints = [
            ("/api/documents/upload", "POST"),
            ("/api/documents/123", "DELETE"),
            ("/api/users/profile", "GET"),
            ("/api/admin/users", "GET"),
        ]
        
        for endpoint, method in protected_endpoints:
            if method == "GET":
                response = security_test_client.get(endpoint)
            elif method == "POST":
                response = security_test_client.post(endpoint)
            elif method == "DELETE":
                response = security_test_client.delete(endpoint)
            
            # Should require authentication
            assert response.status_code == 401
    
    def test_valid_token_access(self, security_test_client):
        """Test access with valid authentication token."""
        # Create valid token
        user_data = {"user_id": "123", "username": "testuser", "role": "user"}
        token = create_access_token(user_data)
        
        headers = {"Authorization": f"Bearer {token}"}
        
        # Should allow access to user endpoints
        response = security_test_client.get("/api/documents", headers=headers)
        assert response.status_code in [200, 404]  # 404 if no documents exist
    
    def test_role_based_endpoint_access(self, security_test_client):
        """Test role-based access to endpoints."""
        # Test admin access
        admin_data = {"user_id": "1", "username": "admin", "role": "admin"}
        admin_token = create_access_token(admin_data)
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Admin should access admin endpoints
        response = security_test_client.get("/api/admin/users", headers=admin_headers)
        assert response.status_code in [200, 404]
        
        # Test user access to admin endpoints
        user_data = {"user_id": "2", "username": "user", "role": "user"}
        user_token = create_access_token(user_data)
        user_headers = {"Authorization": f"Bearer {user_token}"}
        
        # User should not access admin endpoints
        response = security_test_client.get("/api/admin/users", headers=user_headers)
        assert response.status_code == 403
    
    def test_document_ownership_access_control(self, security_test_client):
        """Test document ownership-based access control."""
        # Create two users
        user1_data = {"user_id": "1", "username": "user1", "role": "user"}
        user2_data = {"user_id": "2", "username": "user2", "role": "user"}
        
        user1_token = create_access_token(user1_data)
        user2_token = create_access_token(user2_data)
        
        user1_headers = {"Authorization": f"Bearer {user1_token}"}
        user2_headers = {"Authorization": f"Bearer {user2_token}"}
        
        # User1 uploads document
        import tempfile
        temp_file = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
        temp_file.write(b"%PDF-1.4\nTest content")
        temp_file.close()
        
        try:
            with open(temp_file.name, "rb") as f:
                response = security_test_client.post(
                    "/api/documents/upload",
                    files={"file": ("test.pdf", f, "application/pdf")},
                    headers=user1_headers
                )
            
            if response.status_code == 200:
                doc_id = response.json()["id"]
                
                # User1 should access their own document
                response = security_test_client.get(f"/api/documents/{doc_id}", headers=user1_headers)
                assert response.status_code == 200
                
                # User2 should not access user1's document
                response = security_test_client.get(f"/api/documents/{doc_id}", headers=user2_headers)
                assert response.status_code == 403
        finally:
            import os
            os.unlink(temp_file.name)
    
    def test_session_management(self, security_test_client):
        """Test session management and token refresh."""
        user_data = {"user_id": "123", "username": "testuser", "role": "user"}
        
        # Login
        login_response = security_test_client.post("/api/auth/login", json={
            "username": "testuser",
            "password": "password123"
        })
        
        if login_response.status_code == 200:
            token = login_response.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            
            # Use token
            response = security_test_client.get("/api/documents", headers=headers)
            assert response.status_code in [200, 404]
            
            # Logout
            logout_response = security_test_client.post("/api/auth/logout", headers=headers)
            assert logout_response.status_code == 200
            
            # Token should be invalid after logout
            response = security_test_client.get("/api/documents", headers=headers)
            assert response.status_code == 401
    
    def test_brute_force_protection(self, security_test_client):
        """Test brute force attack protection."""
        # Attempt multiple failed logins
        for i in range(10):
            response = security_test_client.post("/api/auth/login", json={
                "username": "testuser",
                "password": "wrong_password"
            })
            
            if i < 5:
                assert response.status_code == 401
            else:
                # Should be rate limited after several attempts
                assert response.status_code == 429
    
    def test_concurrent_session_limits(self, security_test_client):
        """Test concurrent session limits."""
        user_data = {"user_id": "123", "username": "testuser", "role": "user"}
        
        # Create multiple tokens for same user
        tokens = []
        for i in range(10):
            token = create_access_token(user_data)
            tokens.append(token)
        
        # Test that old tokens are invalidated when limit is exceeded
        headers_list = [{"Authorization": f"Bearer {token}"} for token in tokens]
        
        valid_sessions = 0
        for headers in headers_list:
            response = security_test_client.get("/api/documents", headers=headers)
            if response.status_code in [200, 404]:
                valid_sessions += 1
        
        # Should have limited number of valid sessions
        assert valid_sessions <= 5  # Assuming max 5 concurrent sessions
    
    def test_privilege_escalation_prevention(self, security_test_client):
        """Test prevention of privilege escalation attacks."""
        # Create user token
        user_data = {"user_id": "123", "username": "testuser", "role": "user"}
        user_token = create_access_token(user_data)
        user_headers = {"Authorization": f"Bearer {user_token}"}
        
        # Attempt to modify role through API
        escalation_attempts = [
            {"role": "admin"},
            {"permissions": ["admin"]},
            {"user_id": "1"},  # Try to impersonate admin
        ]
        
        for attempt in escalation_attempts:
            response = security_test_client.put("/api/users/profile", 
                                              json=attempt, 
                                              headers=user_headers)
            
            # Should not allow privilege escalation
            assert response.status_code in [400, 403]
    
    def test_api_key_authentication(self, security_test_client):
        """Test API key authentication for service accounts."""
        # Test with valid API key
        valid_api_key = "test_api_key_123"
        headers = {"X-API-Key": valid_api_key}
        
        with patch('app.utils.access_control.validate_api_key', return_value=True):
            response = security_test_client.get("/api/documents", headers=headers)
            assert response.status_code in [200, 404]
        
        # Test with invalid API key
        invalid_api_key = "invalid_key"
        headers = {"X-API-Key": invalid_api_key}
        
        with patch('app.utils.access_control.validate_api_key', return_value=False):
            response = security_test_client.get("/api/documents", headers=headers)
            assert response.status_code == 401
    
    def test_cors_security(self, security_test_client):
        """Test CORS security configuration."""
        # Test preflight request
        response = security_test_client.options("/api/documents", 
                                               headers={"Origin": "https://malicious-site.com"})
        
        # Should not allow arbitrary origins
        cors_header = response.headers.get("Access-Control-Allow-Origin")
        assert cors_header != "*" or cors_header is None
        
        # Test with allowed origin
        response = security_test_client.options("/api/documents",
                                               headers={"Origin": "https://localhost:3000"})
        
        # Should allow configured origins
        cors_header = response.headers.get("Access-Control-Allow-Origin")
        assert cors_header in ["https://localhost:3000", "http://localhost:3000"]