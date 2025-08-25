#!/usr/bin/env python3
"""
Test enhanced file upload validation functionality.
This script tests the comprehensive file validation system.
"""

import os
import tempfile
import pytest
from pathlib import Path
from fastapi import UploadFile
from io import BytesIO

# Import the validation modules
from app.utils.file_validation import FileValidator, validate_file_upload
from app.utils.security import SecurityValidator


class TestEnhancedFileValidation:
    """Test enhanced file validation functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.validator = FileValidator()
        self.security_validator = SecurityValidator()
        self.temp_dir = Path(tempfile.mkdtemp())
    
    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def create_test_file(self, filename: str, content: bytes) -> Path:
        """Create a test file with given content."""
        file_path = self.temp_dir / filename
        with open(file_path, 'wb') as f:
            f.write(content)
        return file_path
    
    def create_upload_file(self, filename: str, content: bytes, content_type: str = None):
        """Create a mock UploadFile object."""
        file_obj = BytesIO(content)
        file_obj.name = filename
        
        # Create a mock object that behaves like UploadFile
        class MockUploadFile:
            def __init__(self, filename, file_obj, content_type, size):
                self.filename = filename
                self.file = file_obj
                self.content_type = content_type
                self.size = size
        
        return MockUploadFile(filename, file_obj, content_type, len(content))
    
    def test_valid_pdf_file(self):
        """Test validation of a valid PDF file."""
        # Create a minimal valid PDF
        pdf_content = b'%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n>>\nendobj\nxref\n0 1\n0000000000 65535 f \ntrailer\n<<\n/Size 1\n/Root 1 0 R\n>>\nstartxref\n9\n%%EOF'
        file_path = self.create_test_file('test.pdf', pdf_content)
        
        result = self.validator.validate_file_upload(file_path)
        assert result.is_valid, f"Valid PDF should pass validation: {result.error_message}"
    
    def test_valid_text_file(self):
        """Test validation of a valid text file."""
        text_content = b'This is a valid text file with normal content.\nIt has multiple lines.\nAnd normal characters.'
        file_path = self.create_test_file('test.txt', text_content)
        
        result = self.validator.validate_file_upload(file_path)
        assert result.is_valid, f"Valid text file should pass validation: {result.error_message}"
    
    def test_valid_markdown_file(self):
        """Test validation of a valid markdown file."""
        md_content = b'# Test Markdown\n\nThis is a **valid** markdown file.\n\n- Item 1\n- Item 2\n\n```python\nprint("hello")\n```'
        file_path = self.create_test_file('test.md', md_content)
        
        result = self.validator.validate_file_upload(file_path)
        assert result.is_valid, f"Valid markdown file should pass validation: {result.error_message}"
    
    def test_reject_executable_file(self):
        """Test rejection of executable files."""
        # PE executable header
        exe_content = b'MZ\x90\x00\x03\x00\x00\x00\x04\x00\x00\x00\xff\xff\x00\x00'
        file_path = self.create_test_file('malicious.exe', exe_content)
        
        result = self.validator.validate_file_upload(file_path)
        assert not result.is_valid, f"Executable file should be rejected: {result.error_message}"
        assert "not allowed" in result.error_message or "Dangerous file type detected" in result.error_message
    
    def test_reject_script_content_in_text(self):
        """Test rejection of script content in text files."""
        malicious_content = b'<script>alert("XSS")</script>\nSome normal text here.'
        file_path = self.create_test_file('malicious.txt', malicious_content)
        
        result = self.validator.validate_file_upload(file_path)
        assert not result.is_valid, f"Text file with script content should be rejected: {result.error_message}"
        assert ("malicious content detected" in result.error_message.lower() or 
                "script tag" in result.error_message.lower() or
                "dangerous file type detected" in result.error_message.lower())
    
    def test_reject_php_content(self):
        """Test rejection of PHP content in text files."""
        php_content = b'<?php\necho "Hello World";\nsystem($_GET["cmd"]);\n?>'
        file_path = self.create_test_file('malicious.txt', php_content)
        
        result = self.validator.validate_file_upload(file_path)
        assert not result.is_valid, f"Text file with PHP content should be rejected: {result.error_message}"
        assert ("malicious content detected" in result.error_message.lower() or 
                "php opening tag" in result.error_message.lower() or
                "dangerous file type detected" in result.error_message.lower())
    
    def test_reject_oversized_file(self):
        """Test rejection of oversized files."""
        # Create a file larger than the limit
        large_content = b'A' * (101 * 1024 * 1024)  # 101MB
        file_path = self.create_test_file('large.pdf', large_content)
        
        result = self.validator.validate_file_upload(file_path)
        assert not result.is_valid, "Oversized file should be rejected"
        assert "too large" in result.error_message.lower()
    
    def test_reject_empty_file(self):
        """Test rejection of empty files."""
        file_path = self.create_test_file('empty.txt', b'')
        
        result = self.validator.validate_file_upload(file_path)
        assert not result.is_valid, "Empty file should be rejected"
        assert "too small" in result.error_message.lower()
    
    def test_reject_null_bytes_in_text(self):
        """Test rejection of null bytes in text files."""
        null_content = b'Normal text\x00with null byte'
        file_path = self.create_test_file('null.txt', null_content)
        
        result = self.validator.validate_file_upload(file_path)
        assert not result.is_valid, f"Text file with null bytes should be rejected: {result.error_message}"
        assert "null byte" in result.error_message.lower() or "binary content" in result.error_message.lower()
    
    def test_reject_invalid_extension(self):
        """Test rejection of invalid file extensions."""
        content = b'Some content'
        file_path = self.create_test_file('test.exe', content)
        
        result = self.validator.validate_file_upload(file_path)
        assert not result.is_valid, "File with invalid extension should be rejected"
        assert "not allowed" in result.error_message.lower()
    
    def test_filename_sanitization(self):
        """Test filename sanitization."""
        dangerous_filename = '../../../etc/passwd'
        result = self.validator._validate_filename(dangerous_filename)
        assert not result.is_valid, "Dangerous filename should be rejected"
        assert "path traversal" in result.error_message.lower()
    
    def test_reserved_filename_rejection(self):
        """Test rejection of Windows reserved filenames."""
        reserved_names = ['CON.txt', 'PRN.pdf', 'AUX.md', 'NUL.docx']
        
        for filename in reserved_names:
            result = self.validator._validate_filename(filename)
            assert not result.is_valid, f"Reserved filename {filename} should be rejected"
    
    def test_double_extension_detection(self):
        """Test detection of suspicious double extensions."""
        # Use a valid extension with suspicious double extension
        upload_file = self.create_upload_file('document.txt.exe.txt', b'fake content')
        result = self.security_validator.validate_upload_file(upload_file)
        
        assert not result['is_secure'], f"Double extension file should be rejected: {result['issues']}"
        # Should be rejected either for double extension or invalid extension
        assert (any('double extension' in issue.lower() for issue in result['issues']) or
                any('not allowed' in issue.lower() for issue in result['issues']))
    
    def test_content_type_validation(self):
        """Test content type validation."""
        # Test mismatched content type
        upload_file = self.create_upload_file('test.pdf', b'%PDF-1.4', 'text/plain')
        result = self.security_validator.validate_upload_file(upload_file)
        
        assert not result['is_secure'], "Mismatched content type should be rejected"
    
    def test_pdf_with_javascript_warning(self):
        """Test PDF with JavaScript generates warning."""
        pdf_with_js = b'%PDF-1.4\n/JavaScript (alert("test"))\n%%EOF'
        file_path = self.create_test_file('test.pdf', pdf_with_js)
        
        result = self.validator.validate_file_upload(file_path)
        # Should pass but with warnings
        assert result.is_valid, "PDF with JavaScript should pass with warnings"
        assert result.warnings and any('javascript' in w.lower() for w in result.warnings)
    
    def test_docx_structure_validation(self):
        """Test DOCX structure validation."""
        # Create a fake DOCX (just ZIP header without proper structure)
        fake_docx = b'PK\x03\x04\x14\x00\x00\x00fake docx content'
        file_path = self.create_test_file('test.docx', fake_docx)
        
        result = self.validator.validate_file_upload(file_path)
        assert not result.is_valid, "Invalid DOCX structure should be rejected"
    
    def test_suspicious_url_in_text(self):
        """Test detection of suspicious URLs in text files."""
        suspicious_content = b'Download from: http://malicious.com/virus.exe'
        file_path = self.create_test_file('suspicious.txt', suspicious_content)
        
        result = self.validator.validate_file_upload(file_path)
        assert not result.is_valid, "Text with suspicious URL should be rejected"
        assert "suspicious" in result.error_message.lower()
    
    def test_high_special_char_ratio_warning(self):
        """Test warning for high special character ratio."""
        obfuscated_content = b'!@#$%^&*()_+{}|:"<>?[]\\;\',./'
        file_path = self.create_test_file('obfuscated.txt', obfuscated_content)
        
        result = self.validator.validate_file_upload(file_path)
        # Should pass but with warning about obfuscation
        if result.is_valid and result.warnings:
            assert any('obfuscation' in w.lower() for w in result.warnings)
    
    def test_upload_file_security_validation(self):
        """Test UploadFile security validation."""
        # Test valid file
        valid_content = b'This is valid content'
        upload_file = self.create_upload_file('test.txt', valid_content, 'text/plain')
        result = self.security_validator.validate_upload_file(upload_file)
        
        assert result['is_secure'], f"Valid upload should pass: {result['issues']}"
        
        # Test invalid filename
        upload_file = self.create_upload_file('../../../etc/passwd', valid_content, 'text/plain')
        result = self.security_validator.validate_upload_file(upload_file)
        
        assert not result['is_secure'], "Upload with dangerous filename should be rejected"
    
    def test_control_characters_in_filename(self):
        """Test rejection of control characters in filename."""
        filename_with_control = 'test\x01\x02.txt'
        upload_file = self.create_upload_file(filename_with_control, b'content', 'text/plain')
        result = self.security_validator.validate_upload_file(upload_file)
        
        assert not result['is_secure'], "Filename with control characters should be rejected"
    
    def test_long_filename_rejection(self):
        """Test rejection of overly long filenames."""
        long_filename = 'a' * 300 + '.txt'
        upload_file = self.create_upload_file(long_filename, b'content', 'text/plain')
        result = self.security_validator.validate_upload_file(upload_file)
        
        assert not result['is_secure'], "Overly long filename should be rejected"
    
    def test_embedded_executable_detection(self):
        """Test detection of embedded executables."""
        # Content with embedded PE header
        embedded_exe = b'Normal content\nMZ\x90\x00This program cannot be run in DOS mode'
        file_path = self.create_test_file('embedded.txt', embedded_exe)
        
        result = self.validator.validate_file_upload(file_path)
        assert not result.is_valid, "File with embedded executable should be rejected"


def run_comprehensive_tests():
    """Run comprehensive file validation tests."""
    print("Running comprehensive file validation tests...")
    
    test_instance = TestEnhancedFileValidation()
    test_methods = [method for method in dir(test_instance) if method.startswith('test_')]
    
    passed = 0
    failed = 0
    
    for test_method in test_methods:
        try:
            test_instance.setup_method()
            getattr(test_instance, test_method)()
            test_instance.teardown_method()
            print(f"✓ {test_method}")
            passed += 1
        except Exception as e:
            print(f"✗ {test_method}: {str(e)}")
            failed += 1
            test_instance.teardown_method()
    
    print(f"\nTest Results: {passed} passed, {failed} failed")
    return failed == 0


if __name__ == "__main__":
    success = run_comprehensive_tests()
    exit(0 if success else 1)