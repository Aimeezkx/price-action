"""
Tests for privacy and security features
"""

import pytest
import tempfile
import os
from unittest.mock import Mock, patch
from fastapi import UploadFile, HTTPException
from io import BytesIO

from app.utils.security import SecurityValidator, generate_secure_filename, hash_sensitive_data
from app.utils.access_control import AccessController, DataProtection
from app.utils.logging import PrivacyFilter, SecurityLogger
from app.utils.privacy_service import PrivacyManager, LLMService, privacy_manager
from app.core.config import settings


class TestSecurityValidator:
    """Test security validation utilities"""
    
    @pytest.mark.asyncio
    async def test_validate_pdf_file(self):
        """Test PDF file validation"""
        # Create a mock PDF file
        pdf_content = b'%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n>>\nendobj\nxref\n0 1\n0000000000 65535 f \ntrailer\n<<\n/Size 1\n/Root 1 0 R\n>>\nstartxref\n9\n%%EOF'
        
        file = UploadFile(
            filename="test.pdf",
            file=BytesIO(pdf_content)
        )
        file.content_type = "application/pdf"
        
        file_type, safe_filename = await SecurityValidator.validate_upload_file(file)
        
        assert file_type == "pdf"
        assert safe_filename == "test.pdf"
    
    @pytest.mark.asyncio
    async def test_reject_invalid_file_type(self):
        """Test rejection of invalid file types"""
        file = UploadFile(
            filename="malicious.exe",
            file=BytesIO(b"MZ\x90\x00")  # PE header
        )
        file.content_type = "application/octet-stream"
        
        with pytest.raises(HTTPException) as exc_info:
            await SecurityValidator.validate_upload_file(file)
        
        assert exc_info.value.status_code == 400
        assert "not allowed" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_reject_oversized_file(self):
        """Test rejection of oversized files"""
        # Create a large file content
        large_content = b"A" * (101 * 1024 * 1024)  # 101MB
        
        file = UploadFile(
            filename="large.pdf",
            file=BytesIO(large_content)
        )
        file.content_type = "application/pdf"
        
        with pytest.raises(HTTPException) as exc_info:
            await SecurityValidator.validate_upload_file(file)
        
        assert exc_info.value.status_code == 413
        assert "too large" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_detect_malicious_content(self):
        """Test detection of malicious content"""
        malicious_content = b'%PDF-1.4\n<script>alert("xss")</script>'
        
        file = UploadFile(
            filename="malicious.pdf",
            file=BytesIO(malicious_content)
        )
        file.content_type = "application/pdf"
        
        with pytest.raises(HTTPException) as exc_info:
            await SecurityValidator.validate_upload_file(file)
        
        assert exc_info.value.status_code == 400
        assert "malicious content" in str(exc_info.value.detail)
    
    def test_sanitize_filename(self):
        """Test filename sanitization"""
        dangerous_filename = "../../../etc/passwd"
        safe_filename = SecurityValidator._sanitize_filename(dangerous_filename)
        
        assert ".." not in safe_filename
        assert "/" not in safe_filename
        assert safe_filename != dangerous_filename
    
    def test_generate_secure_filename(self):
        """Test secure filename generation"""
        original = "my document.pdf"
        doc_id = "123e4567-e89b-12d3-a456-426614174000"
        
        secure_name = generate_secure_filename(original, doc_id)
        
        assert doc_id in secure_name
        assert secure_name.endswith(".pdf")
        assert " " not in secure_name
        assert len(secure_name) > len(original)


class TestAccessController:
    """Test access control utilities"""
    
    def test_rate_limiting(self):
        """Test rate limiting functionality"""
        # Mock request
        mock_request = Mock()
        mock_request.client.host = "127.0.0.1"
        mock_request.headers = {}
        
        # First few requests should pass
        for i in range(5):
            assert AccessController.check_rate_limit(mock_request, "upload") == True
        
        # 6th request should fail
        assert AccessController.check_rate_limit(mock_request, "upload") == False
    
    def test_sanitize_user_input(self):
        """Test user input sanitization"""
        dangerous_input = '<script>alert("xss")</script>'
        sanitized = AccessController.sanitize_user_input(dangerous_input)
        
        assert "<script>" not in sanitized
        assert "alert" in sanitized  # Content preserved, tags removed
    
    def test_hash_user_identifier(self):
        """Test user identifier hashing"""
        identifier = "user@example.com"
        hashed = AccessController.hash_user_identifier(identifier)
        
        assert hashed != identifier
        assert len(hashed) == 16
        assert hashed.isalnum()
    
    def test_hash_sensitive_data(self):
        """Test sensitive data hashing"""
        sensitive = "secret_filename.pdf"
        hashed = hash_sensitive_data(sensitive)
        
        assert hashed.startswith("[hash:")
        assert hashed.endswith("]")
        assert sensitive not in hashed


class TestDataProtection:
    """Test data protection utilities"""
    
    def test_anonymize_document_metadata(self):
        """Test document metadata anonymization"""
        metadata = {
            "author": "John Doe",
            "title": "Confidential Document",
            "creation_date": "2023-01-01",
            "pages": 10
        }
        
        # Test with anonymization enabled
        with patch.object(settings, 'anonymize_logs', True):
            anonymized = DataProtection.anonymize_document_metadata(metadata)
            
            assert anonymized["author"] == "[author:anonymized]"
            assert anonymized["title"] == "[title:anonymized]"
            assert anonymized["creation_date"] == "[date:anonymized]"
            assert anonymized["pages"] == 10  # Non-sensitive field preserved
    
    def test_clean_text_content(self):
        """Test text content cleaning"""
        text = "Contact John at john@example.com or call 555-123-4567"
        
        with patch.object(settings, 'anonymize_logs', True):
            cleaned = DataProtection.clean_text_content(text)
            
            assert "john@example.com" not in cleaned
            assert "555-123-4567" not in cleaned
            assert "[email]" in cleaned
            assert "[phone]" in cleaned
    
    def test_secure_delete_file(self):
        """Test secure file deletion"""
        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(b"sensitive data")
            temp_path = temp_file.name
        
        # Verify file exists
        assert os.path.exists(temp_path)
        
        # Securely delete
        result = DataProtection.secure_delete_file(temp_path)
        
        assert result == True
        assert not os.path.exists(temp_path)


class TestPrivacyFilter:
    """Test privacy-aware logging filter"""
    
    def test_anonymize_log_message(self):
        """Test log message anonymization"""
        filter_instance = PrivacyFilter()
        
        # Test with sensitive data
        sensitive_message = "Processing file /home/user/documents/secret.pdf"
        anonymized = filter_instance._anonymize_message(sensitive_message)
        
        assert "/home/user/documents/secret.pdf" not in anonymized
        assert "[path:" in anonymized or "[file:" in anonymized
    
    def test_preserve_non_sensitive_data(self):
        """Test that non-sensitive data is preserved"""
        filter_instance = PrivacyFilter()
        
        normal_message = "Processing completed successfully with 5 chapters"
        result = filter_instance._anonymize_message(normal_message)
        
        assert result == normal_message


class TestSecurityLogger:
    """Test security logger functionality"""
    
    def test_log_file_upload(self):
        """Test file upload logging"""
        logger = SecurityLogger("test")
        
        with patch.object(logger.logger, 'info') as mock_info:
            logger.log_file_upload("test.pdf", 1024, "user123")
            
            mock_info.assert_called_once()
            call_args = mock_info.call_args[0][0]
            assert "File upload" in call_args
    
    def test_log_security_event(self):
        """Test security event logging"""
        logger = SecurityLogger("test")
        
        with patch.object(logger.logger, 'warning') as mock_warning:
            logger.log_security_event(
                "test_event",
                {"filename": "test.pdf", "user_id": "user123"},
                "WARNING"
            )
            
            mock_warning.assert_called_once()
            call_args = mock_warning.call_args[0][0]
            assert "Security event: test_event" in call_args


class TestPrivacyService:
    """Test privacy-compliant service integration"""
    
    @pytest.mark.asyncio
    async def test_llm_service_privacy_mode(self):
        """Test LLM service respects privacy mode"""
        llm_service = LLMService()
        
        # Test with privacy mode enabled
        with patch.object(settings, 'privacy_mode', True):
            result = await llm_service.extract_knowledge("test text", "doc-id")
            
            # Should use local extraction
            assert result is not None
            assert isinstance(result, list)
    
    @pytest.mark.asyncio
    async def test_privacy_manager_status(self):
        """Test privacy manager status reporting"""
        status = privacy_manager.get_privacy_status()
        
        assert "privacy_mode" in status
        assert "anonymize_logs" in status
        assert "external_services" in status
        assert isinstance(status["external_services"], dict)
    
    def test_privacy_settings_validation(self):
        """Test privacy settings validation"""
        warnings = privacy_manager.validate_privacy_settings()
        
        assert isinstance(warnings, list)
        # Warnings should be present if privacy mode is disabled
        if not settings.privacy_mode:
            assert len(warnings) > 0


class TestIntegration:
    """Integration tests for privacy and security features"""
    
    @pytest.mark.asyncio
    async def test_end_to_end_secure_upload(self):
        """Test complete secure upload flow"""
        # Create a valid PDF file
        pdf_content = b'%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n>>\nendobj\nxref\n0 1\n0000000000 65535 f \ntrailer\n<<\n/Size 1\n/Root 1 0 R\n>>\nstartxref\n9\n%%EOF'
        
        file = UploadFile(
            filename="test_document.pdf",
            file=BytesIO(pdf_content)
        )
        file.content_type = "application/pdf"
        
        # Validate file
        file_type, safe_filename = await SecurityValidator.validate_upload_file(file)
        
        # Generate secure filename
        doc_id = "test-doc-id"
        secure_filename = generate_secure_filename(safe_filename, doc_id)
        
        assert file_type == "pdf"
        assert safe_filename == "test_document.pdf"
        assert doc_id in secure_filename
        assert secure_filename.endswith(".pdf")
    
    def test_privacy_mode_configuration(self):
        """Test privacy mode affects all components"""
        # Test with privacy mode enabled
        with patch.object(settings, 'privacy_mode', True):
            # Privacy manager should report privacy mode as enabled
            status = privacy_manager.get_privacy_status()
            assert status["privacy_mode"] == True
            
            # External services should be disabled
            assert status["external_services"]["llm"] == False
            assert status["external_services"]["ocr"] == False
    
    def test_security_features_enabled(self):
        """Test that all security features are properly enabled"""
        # Check that security features are available
        assert hasattr(SecurityValidator, 'validate_upload_file')
        assert hasattr(AccessController, 'check_rate_limit')
        assert hasattr(DataProtection, 'anonymize_document_metadata')
        assert hasattr(privacy_manager, 'get_privacy_status')
        
        # Check configuration
        assert hasattr(settings, 'privacy_mode')
        assert hasattr(settings, 'anonymize_logs')
        assert hasattr(settings, 'enable_file_scanning')