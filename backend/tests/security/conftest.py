"""Security testing configuration and fixtures."""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import get_db
from app.core.config import settings
from app.models.base import Base
from main import app


@pytest.fixture
def security_test_client():
    """Create test client for security testing."""
    # Use in-memory SQLite for security tests
    SQLALCHEMY_DATABASE_URL = "sqlite:///./test_security.db"
    engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    Base.metadata.create_all(bind=engine)
    
    def override_get_db():
        try:
            db = TestingSessionLocal()
            yield db
        finally:
            db.close()
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as client:
        yield client
    
    # Clean up
    app.dependency_overrides.clear()
    os.unlink("./test_security.db")


@pytest.fixture
def malicious_files():
    """Create malicious test files for security testing."""
    files = {}
    
    # Create temporary directory for malicious files
    temp_dir = tempfile.mkdtemp()
    
    # Executable file
    exe_file = Path(temp_dir) / "malicious.exe"
    exe_file.write_bytes(b"MZ\x90\x00")  # PE header
    files["executable"] = exe_file
    
    # Script file with malicious content
    js_file = Path(temp_dir) / "malicious.js"
    js_file.write_text("alert('XSS'); document.location='http://evil.com'")
    files["javascript"] = js_file
    
    # PHP file with malicious content
    php_file = Path(temp_dir) / "malicious.php"
    php_file.write_text("<?php system($_GET['cmd']); ?>")
    files["php"] = php_file
    
    # Oversized file (simulated)
    large_file = Path(temp_dir) / "large.pdf"
    large_file.write_bytes(b"PDF" + b"A" * (100 * 1024 * 1024))  # 100MB
    files["oversized"] = large_file
    
    # File with null bytes
    null_file = Path(temp_dir) / "null_bytes.txt"
    null_file.write_bytes(b"Normal content\x00malicious content")
    files["null_bytes"] = null_file
    
    # File with suspicious extension
    double_ext = Path(temp_dir) / "document.pdf.exe"
    double_ext.write_bytes(b"MZ\x90\x00")
    files["double_extension"] = double_ext
    
    yield files
    
    # Cleanup
    import shutil
    shutil.rmtree(temp_dir)


@pytest.fixture
def mock_privacy_mode():
    """Mock privacy mode settings."""
    with patch('app.core.config.settings.privacy_mode', True):
        yield


@pytest.fixture
def mock_external_api_calls():
    """Mock and track external API calls."""
    external_calls = []
    
    def track_call(url, *args, **kwargs):
        external_calls.append(url)
        return Mock()
    
    with patch('requests.get', side_effect=track_call), \
         patch('requests.post', side_effect=track_call), \
         patch('httpx.get', side_effect=track_call), \
         patch('httpx.post', side_effect=track_call):
        yield external_calls


@pytest.fixture
def sensitive_test_data():
    """Create test data with sensitive information."""
    return {
        "filename": "john_doe_medical_records.pdf",
        "content": "Patient: John Doe, SSN: 123-45-6789, DOB: 1980-01-01",
        "email": "john.doe@example.com",
        "phone": "+1-555-123-4567",
        "address": "123 Main St, Anytown, ST 12345"
    }


@pytest.fixture
def sql_injection_payloads():
    """SQL injection test payloads."""
    return [
        "'; DROP TABLE documents; --",
        "' OR '1'='1",
        "' UNION SELECT * FROM users --",
        "'; INSERT INTO users (username, password) VALUES ('hacker', 'password'); --",
        "' OR 1=1 --",
        "admin'--",
        "admin'/*",
        "' OR 'x'='x",
        "'; EXEC xp_cmdshell('dir'); --"
    ]


@pytest.fixture
def xss_payloads():
    """XSS test payloads."""
    return [
        "<script>alert('XSS')</script>",
        "<img src=x onerror=alert('XSS')>",
        "javascript:alert('XSS')",
        "<svg onload=alert('XSS')>",
        "<iframe src=javascript:alert('XSS')>",
        "<body onload=alert('XSS')>",
        "<input onfocus=alert('XSS') autofocus>",
        "<select onfocus=alert('XSS') autofocus>",
        "<textarea onfocus=alert('XSS') autofocus>",
        "<keygen onfocus=alert('XSS') autofocus>"
    ]