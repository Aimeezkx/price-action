"""Test data sanitization in logs and outputs."""

import pytest
import logging
import tempfile
import os
from unittest.mock import patch, Mock
from io import StringIO

from app.utils.logging import sanitize_log_data, SanitizedLogger
from app.utils.privacy_service import PrivacyService


class TestDataSanitization:
    """Test data sanitization functionality."""
    
    def test_log_sanitization_pii(self, caplog):
        """Test PII sanitization in logs."""
        logger = SanitizedLogger("test_logger")
        
        # Test various PII patterns
        test_cases = [
            ("User email: john.doe@example.com", "User email: ***@***.***"),
            ("SSN: 123-45-6789", "SSN: ***-**-****"),
            ("Phone: +1-555-123-4567", "Phone: ***-***-****"),
            ("Credit card: 4532-1234-5678-9012", "Credit card: ****-****-****-****"),
            ("IP address: 192.168.1.100", "IP address: ***.***.***.***"),
            ("Patient John Doe born 1980-01-01", "Patient *** *** born ****-**-**"),
        ]
        
        for original, expected in test_cases:
            logger.info(original)
            
        # Check that logs are sanitized
        log_messages = [record.message for record in caplog.records]
        for i, (original, expected) in enumerate(test_cases):
            assert expected in log_messages[i] or "***" in log_messages[i]
            assert not any(sensitive in log_messages[i] for sensitive in [
                "john.doe@example.com", "123-45-6789", "555-123-4567",
                "4532-1234-5678-9012", "192.168.1.100", "John Doe", "1980-01-01"
            ])
    
    def test_filename_sanitization(self, sensitive_test_data):
        """Test filename sanitization in logs."""
        logger = SanitizedLogger("test_logger")
        
        sensitive_filename = sensitive_test_data["filename"]
        logger.info(f"Processing file: {sensitive_filename}")
        
        # Should not contain the actual sensitive filename
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            logging.getLogger("test_logger").info(f"Processing file: {sensitive_filename}")
            output = mock_stdout.getvalue()
            
            assert "john_doe" not in output.lower()
            assert "medical_records" not in output.lower()
            assert "***" in output or "[REDACTED]" in output
    
    def test_content_sanitization(self, sensitive_test_data):
        """Test content sanitization in logs."""
        privacy_service = PrivacyService()
        
        sensitive_content = sensitive_test_data["content"]
        sanitized = privacy_service.sanitize_content(sensitive_content)
        
        # Should not contain PII
        assert "John Doe" not in sanitized
        assert "123-45-6789" not in sanitized
        assert "1980-01-01" not in sanitized
        
        # Should contain redaction markers
        assert "***" in sanitized or "[REDACTED]" in sanitized
    
    def test_api_response_sanitization(self, security_test_client, sensitive_test_data):
        """Test API response sanitization."""
        # Upload document with sensitive filename
        temp_file = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
        temp_file.write(b"%PDF-1.4\nSensitive content here")
        temp_file.close()
        
        try:
            with open(temp_file.name, "rb") as f:
                response = security_test_client.post(
                    "/api/documents/upload",
                    files={"file": (sensitive_test_data["filename"], f, "application/pdf")}
                )
            
            assert response.status_code == 200
            response_data = response.json()
            
            # Check that response doesn't contain sensitive information
            response_str = str(response_data)
            assert "john_doe" not in response_str.lower()
            assert "medical_records" not in response_str.lower()
        finally:
            os.unlink(temp_file.name)
    
    def test_error_message_sanitization(self, security_test_client, sensitive_test_data):
        """Test error message sanitization."""
        # Try to upload invalid file with sensitive name
        temp_file = tempfile.NamedTemporaryFile(suffix=".exe", delete=False)
        temp_file.write(b"MZ\x90\x00")  # PE header
        temp_file.close()
        
        try:
            with open(temp_file.name, "rb") as f:
                response = security_test_client.post(
                    "/api/documents/upload",
                    files={"file": (sensitive_test_data["filename"], f, "application/octet-stream")}
                )
            
            assert response.status_code == 400
            error_message = response.json()["detail"]
            
            # Error message should not contain sensitive filename
            assert "john_doe" not in error_message.lower()
            assert "medical_records" not in error_message.lower()
        finally:
            os.unlink(temp_file.name)
    
    def test_database_query_sanitization(self):
        """Test database query sanitization."""
        privacy_service = PrivacyService()
        
        # Test SQL query with sensitive data
        query = "SELECT * FROM documents WHERE filename = 'john_doe_medical_records.pdf'"
        sanitized_query = privacy_service.sanitize_sql_query(query)
        
        assert "john_doe" not in sanitized_query
        assert "medical_records" not in sanitized_query
        assert "***" in sanitized_query or "[REDACTED]" in sanitized_query
    
    def test_search_query_sanitization(self, security_test_client):
        """Test search query sanitization in logs."""
        with patch('app.utils.logging.logger') as mock_logger:
            # Search with sensitive terms
            response = security_test_client.get("/api/search?q=john+doe+medical+records")
            
            # Check that logged search queries are sanitized
            logged_calls = [call.args[0] for call in mock_logger.info.call_args_list]
            for call in logged_calls:
                if "search" in call.lower():
                    assert "john" not in call.lower()
                    assert "doe" not in call.lower()
                    assert "medical" not in call.lower()
    
    def test_export_data_sanitization(self, security_test_client):
        """Test data sanitization in exports."""
        # Upload document
        temp_file = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
        temp_file.write(b"%PDF-1.4\nSensitive patient data: John Doe, SSN: 123-45-6789")
        temp_file.close()
        
        try:
            with open(temp_file.name, "rb") as f:
                upload_response = security_test_client.post(
                    "/api/documents/upload",
                    files={"file": ("patient_data.pdf", f, "application/pdf")}
                )
            
            assert upload_response.status_code == 200
            doc_id = upload_response.json()["id"]
            
            # Export document
            export_response = security_test_client.get(f"/api/export/document/{doc_id}")
            
            if export_response.status_code == 200:
                export_data = export_response.json()
                export_str = str(export_data)
                
                # Should not contain sensitive information
                assert "John Doe" not in export_str
                assert "123-45-6789" not in export_str
        finally:
            os.unlink(temp_file.name)
    
    def test_sanitization_configuration(self):
        """Test sanitization configuration."""
        privacy_service = PrivacyService()
        
        # Test custom sanitization patterns
        custom_patterns = {
            r'\b[A-Z][a-z]+ [A-Z][a-z]+\b': '[NAME]',  # Names
            r'\b\d{3}-\d{2}-\d{4}\b': '[SSN]',  # SSN
            r'\b\d{4}-\d{4}-\d{4}-\d{4}\b': '[CARD]'  # Credit card
        }
        
        privacy_service.configure_sanitization_patterns(custom_patterns)
        
        test_text = "Patient John Smith has SSN 123-45-6789 and card 4532-1234-5678-9012"
        sanitized = privacy_service.sanitize_content(test_text)
        
        assert "[NAME]" in sanitized
        assert "[SSN]" in sanitized
        assert "[CARD]" in sanitized
        assert "John Smith" not in sanitized
        assert "123-45-6789" not in sanitized
        assert "4532-1234-5678-9012" not in sanitized
    
    def test_log_level_based_sanitization(self, caplog):
        """Test different sanitization levels based on log level."""
        logger = SanitizedLogger("test_logger")
        
        sensitive_data = "User john.doe@example.com accessed file patient_records.pdf"
        
        # Debug level - more aggressive sanitization
        logger.debug(sensitive_data)
        
        # Info level - moderate sanitization
        logger.info(sensitive_data)
        
        # Warning level - minimal sanitization
        logger.warning(sensitive_data)
        
        debug_logs = [r.message for r in caplog.records if r.levelname == "DEBUG"]
        info_logs = [r.message for r in caplog.records if r.levelname == "INFO"]
        warning_logs = [r.message for r in caplog.records if r.levelname == "WARNING"]
        
        # Debug should be most sanitized
        if debug_logs:
            assert "***" in debug_logs[0] or "[REDACTED]" in debug_logs[0]
        
        # All levels should sanitize email addresses
        for log_list in [debug_logs, info_logs, warning_logs]:
            if log_list:
                assert "john.doe@example.com" not in log_list[0]
    
    def test_sanitization_performance(self):
        """Test sanitization performance with large data."""
        privacy_service = PrivacyService()
        
        # Create large text with sensitive data
        large_text = "Patient John Doe, SSN: 123-45-6789. " * 10000
        
        import time
        start_time = time.time()
        sanitized = privacy_service.sanitize_content(large_text)
        end_time = time.time()
        
        # Should complete within reasonable time (< 1 second)
        assert end_time - start_time < 1.0
        
        # Should still be sanitized
        assert "John Doe" not in sanitized
        assert "123-45-6789" not in sanitized
    
    def test_sanitization_bypass_prevention(self):
        """Test prevention of sanitization bypass attempts."""
        privacy_service = PrivacyService()
        
        bypass_attempts = [
            "J0hn D0e",  # Character substitution
            "John\x00Doe",  # Null byte injection
            "John\tDoe",  # Tab character
            "John\nDoe",  # Newline character
            "John<!---->Doe",  # HTML comment
            "John%20Doe",  # URL encoding
            "Sm1th, J0hn",  # Reversed with substitution
        ]
        
        for attempt in bypass_attempts:
            sanitized = privacy_service.sanitize_content(f"Patient {attempt} has sensitive data")
            
            # Should still be sanitized despite bypass attempts
            assert "***" in sanitized or "[REDACTED]" in sanitized
            # Original attempt should not be present
            assert attempt not in sanitized