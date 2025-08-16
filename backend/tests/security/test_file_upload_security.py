"""Test file upload security measures."""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, Mock

from app.utils.file_validation import validate_file_upload, FileValidationError
from app.utils.security import scan_file_for_malware, detect_malicious_content


class TestFileUploadSecurity:
    """Test file upload security measures."""
    
    def test_reject_executable_files(self, security_test_client, malicious_files):
        """Test that executable files are rejected."""
        exe_file = malicious_files["executable"]
        
        with open(exe_file, "rb") as f:
            response = security_test_client.post(
                "/api/documents/upload",
                files={"file": ("malicious.exe", f, "application/octet-stream")}
            )
        
        assert response.status_code == 400
        assert "rejected" in response.json()["detail"].lower()
        assert "executable" in response.json()["detail"].lower()
    
    def test_reject_script_files(self, security_test_client, malicious_files):
        """Test that script files are rejected."""
        js_file = malicious_files["javascript"]
        
        with open(js_file, "rb") as f:
            response = security_test_client.post(
                "/api/documents/upload",
                files={"file": ("malicious.js", f, "application/javascript")}
            )
        
        assert response.status_code == 400
        assert "rejected" in response.json()["detail"].lower()
    
    def test_reject_php_files(self, security_test_client, malicious_files):
        """Test that PHP files are rejected."""
        php_file = malicious_files["php"]
        
        with open(php_file, "rb") as f:
            response = security_test_client.post(
                "/api/documents/upload",
                files={"file": ("malicious.php", f, "application/x-php")}
            )
        
        assert response.status_code == 400
        assert "rejected" in response.json()["detail"].lower()
    
    def test_reject_oversized_files(self, security_test_client, malicious_files):
        """Test that oversized files are rejected."""
        large_file = malicious_files["oversized"]
        
        with open(large_file, "rb") as f:
            response = security_test_client.post(
                "/api/documents/upload",
                files={"file": ("large.pdf", f, "application/pdf")}
            )
        
        assert response.status_code == 413  # Payload Too Large
        assert "too large" in response.json()["detail"].lower()
    
    def test_reject_files_with_null_bytes(self, security_test_client, malicious_files):
        """Test that files with null bytes are rejected."""
        null_file = malicious_files["null_bytes"]
        
        with open(null_file, "rb") as f:
            response = security_test_client.post(
                "/api/documents/upload",
                files={"file": ("null_bytes.txt", f, "text/plain")}
            )
        
        assert response.status_code == 400
        assert "invalid" in response.json()["detail"].lower()
    
    def test_reject_double_extension_files(self, security_test_client, malicious_files):
        """Test that files with double extensions are rejected."""
        double_ext = malicious_files["double_extension"]
        
        with open(double_ext, "rb") as f:
            response = security_test_client.post(
                "/api/documents/upload",
                files={"file": ("document.pdf.exe", f, "application/pdf")}
            )
        
        assert response.status_code == 400
        assert "suspicious" in response.json()["detail"].lower()
    
    def test_file_validation_utility(self, malicious_files):
        """Test file validation utility functions."""
        # Test executable detection
        with pytest.raises(FileValidationError, match="executable"):
            validate_file_upload(malicious_files["executable"])
        
        # Test script detection
        with pytest.raises(FileValidationError, match="script"):
            validate_file_upload(malicious_files["javascript"])
        
        # Test size validation
        with pytest.raises(FileValidationError, match="too large"):
            validate_file_upload(malicious_files["oversized"])
    
    def test_malware_scanning(self, malicious_files):
        """Test malware scanning functionality."""
        # Test executable scanning
        is_malicious = scan_file_for_malware(malicious_files["executable"])
        assert is_malicious is True
        
        # Test script content scanning
        is_malicious = detect_malicious_content(malicious_files["javascript"])
        assert is_malicious is True
        
        # Test PHP content scanning
        is_malicious = detect_malicious_content(malicious_files["php"])
        assert is_malicious is True
    
    def test_mime_type_validation(self, security_test_client):
        """Test MIME type validation."""
        # Create a file with mismatched extension and content
        temp_file = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
        temp_file.write(b"<html><script>alert('XSS')</script></html>")
        temp_file.close()
        
        try:
            with open(temp_file.name, "rb") as f:
                response = security_test_client.post(
                    "/api/documents/upload",
                    files={"file": ("fake.pdf", f, "application/pdf")}
                )
            
            assert response.status_code == 400
            assert "mime type" in response.json()["detail"].lower()
        finally:
            os.unlink(temp_file.name)
    
    def test_filename_sanitization(self, security_test_client):
        """Test filename sanitization."""
        malicious_filenames = [
            "../../../etc/passwd",
            "..\\..\\windows\\system32\\config\\sam",
            "file<script>alert('xss')</script>.pdf",
            "file\x00.pdf.exe",
            "CON.pdf",  # Windows reserved name
            "file|rm -rf /.pdf"
        ]
        
        for filename in malicious_filenames:
            # Create a valid PDF content
            temp_file = tempfile.NamedTemporaryFile(delete=False)
            temp_file.write(b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n>>\nendobj\nxref\n0 1\n0000000000 65535 f \ntrailer\n<<\n/Size 1\n/Root 1 0 R\n>>\nstartxref\n9\n%%EOF")
            temp_file.close()
            
            try:
                with open(temp_file.name, "rb") as f:
                    response = security_test_client.post(
                        "/api/documents/upload",
                        files={"file": (filename, f, "application/pdf")}
                    )
                
                # Should either reject or sanitize the filename
                if response.status_code == 200:
                    # If accepted, filename should be sanitized
                    doc_data = response.json()
                    assert filename not in doc_data.get("filename", "")
                else:
                    # Should be rejected with appropriate error
                    assert response.status_code == 400
            finally:
                os.unlink(temp_file.name)
    
    @patch('app.utils.security.virus_scanner_available', return_value=True)
    @patch('app.utils.security.scan_with_clamav')
    def test_virus_scanning_integration(self, mock_clamav, mock_available, security_test_client):
        """Test virus scanning integration."""
        # Mock virus detection
        mock_clamav.return_value = {"infected": True, "virus": "Test.Virus"}
        
        temp_file = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
        temp_file.write(b"%PDF-1.4\nmalicious content")
        temp_file.close()
        
        try:
            with open(temp_file.name, "rb") as f:
                response = security_test_client.post(
                    "/api/documents/upload",
                    files={"file": ("test.pdf", f, "application/pdf")}
                )
            
            assert response.status_code == 400
            assert "virus" in response.json()["detail"].lower()
            mock_clamav.assert_called_once()
        finally:
            os.unlink(temp_file.name)
    
    def test_upload_rate_limiting(self, security_test_client):
        """Test upload rate limiting."""
        # Create a small valid PDF
        temp_file = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
        temp_file.write(b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n>>\nendobj\nxref\n0 1\n0000000000 65535 f \ntrailer\n<<\n/Size 1\n/Root 1 0 R\n>>\nstartxref\n9\n%%EOF")
        temp_file.close()
        
        try:
            # Attempt multiple rapid uploads
            responses = []
            for i in range(10):
                with open(temp_file.name, "rb") as f:
                    response = security_test_client.post(
                        "/api/documents/upload",
                        files={"file": (f"test_{i}.pdf", f, "application/pdf")}
                    )
                responses.append(response.status_code)
            
            # Should have some rate limiting after several requests
            rate_limited = any(status == 429 for status in responses)
            assert rate_limited, "Rate limiting should be applied to rapid uploads"
        finally:
            os.unlink(temp_file.name)