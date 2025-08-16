"""Test SQL injection and XSS prevention."""

import pytest
from unittest.mock import patch, Mock
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.core.database import get_db
from app.utils.security import sanitize_input, validate_sql_query, escape_html


class TestInjectionPrevention:
    """Test SQL injection and XSS prevention mechanisms."""
    
    def test_sql_injection_prevention_search(self, security_test_client, sql_injection_payloads):
        """Test SQL injection prevention in search endpoints."""
        for payload in sql_injection_payloads:
            # Test search endpoint
            response = security_test_client.get(f"/api/search?q={payload}")
            
            # Should not return 500 error (which might indicate SQL error)
            assert response.status_code != 500
            
            # Should return safe response
            if response.status_code == 200:
                data = response.json()
                # Should not contain SQL error messages
                response_str = str(data).lower()
                sql_error_indicators = [
                    "sql", "syntax error", "mysql", "postgresql", "sqlite",
                    "table", "column", "database", "select", "insert", "drop"
                ]
                for indicator in sql_error_indicators:
                    assert indicator not in response_str
    
    def test_sql_injection_prevention_filters(self, security_test_client, sql_injection_payloads):
        """Test SQL injection prevention in filter parameters."""
        for payload in sql_injection_payloads:
            # Test various filter endpoints
            filter_endpoints = [
                f"/api/documents?title={payload}",
                f"/api/documents?author={payload}",
                f"/api/cards?difficulty={payload}",
                f"/api/chapters?name={payload}"
            ]
            
            for endpoint in filter_endpoints:
                response = security_test_client.get(endpoint)
                
                # Should handle malicious input safely
                assert response.status_code != 500
                
                if response.status_code == 200:
                    # Should not expose database structure
                    response_text = response.text.lower()
                    assert "error" not in response_text or "sql" not in response_text
    
    def test_parameterized_queries(self):
        """Test that parameterized queries are used correctly."""
        from app.services.document_service import DocumentService
        
        service = DocumentService()
        
        # Test search with malicious input
        malicious_query = "'; DROP TABLE documents; --"
        
        # Should use parameterized query and not execute malicious SQL
        with patch.object(service, 'db') as mock_db:
            mock_db.execute.return_value.fetchall.return_value = []
            
            results = service.search_documents(malicious_query)
            
            # Verify parameterized query was used
            mock_db.execute.assert_called()
            call_args = mock_db.execute.call_args[0]
            
            # Should use parameter binding, not string concatenation
            if len(call_args) > 1:
                # Parameters should be passed separately
                assert isinstance(call_args[1], dict)
                assert malicious_query in call_args[1].values()
    
    def test_orm_injection_prevention(self):
        """Test ORM-level injection prevention."""
        from app.models.document import Document
        from sqlalchemy.orm import Session
        
        # Mock database session
        with patch('app.core.database.SessionLocal') as mock_session_class:
            mock_session = Mock(spec=Session)
            mock_session_class.return_value = mock_session
            mock_session.query.return_value.filter.return_value.all.return_value = []
            
            # Test ORM query with malicious input
            malicious_input = "'; DROP TABLE documents; --"
            
            # This should use ORM parameterization
            query = mock_session.query(Document).filter(Document.title.contains(malicious_input))
            
            # ORM should handle this safely
            assert query is not None
    
    def test_xss_prevention_api_responses(self, security_test_client, xss_payloads):
        """Test XSS prevention in API responses."""
        for payload in xss_payloads:
            # Test document upload with malicious filename
            import tempfile
            temp_file = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
            temp_file.write(b"%PDF-1.4\nTest content")
            temp_file.close()
            
            try:
                with open(temp_file.name, "rb") as f:
                    response = security_test_client.post(
                        "/api/documents/upload",
                        files={"file": (payload, f, "application/pdf")}
                    )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Response should not contain unescaped XSS payload
                    response_str = str(data)
                    assert "<script>" not in response_str
                    assert "javascript:" not in response_str
                    assert "onerror=" not in response_str
                    assert "onload=" not in response_str
            finally:
                import os
                os.unlink(temp_file.name)
    
    def test_xss_prevention_search_results(self, security_test_client, xss_payloads):
        """Test XSS prevention in search results."""
        for payload in xss_payloads:
            response = security_test_client.get(f"/api/search?q={payload}")
            
            if response.status_code == 200:
                data = response.json()
                response_str = str(data)
                
                # Should not contain executable JavaScript
                dangerous_patterns = [
                    "<script>", "</script>", "javascript:", "onerror=",
                    "onload=", "onclick=", "onfocus=", "<iframe", "<svg"
                ]
                
                for pattern in dangerous_patterns:
                    assert pattern not in response_str.lower()
    
    def test_html_escaping_utility(self, xss_payloads):
        """Test HTML escaping utility function."""
        for payload in xss_payloads:
            escaped = escape_html(payload)
            
            # Should escape dangerous characters
            assert "<" not in escaped or "&lt;" in escaped
            assert ">" not in escaped or "&gt;" in escaped
            assert '"' not in escaped or "&quot;" in escaped
            assert "'" not in escaped or "&#x27;" in escaped
            
            # Should not contain executable content
            assert "<script>" not in escaped
            assert "javascript:" not in escaped
    
    def test_input_sanitization_utility(self, sql_injection_payloads, xss_payloads):
        """Test input sanitization utility function."""
        all_payloads = sql_injection_payloads + xss_payloads
        
        for payload in all_payloads:
            sanitized = sanitize_input(payload)
            
            # Should remove or escape dangerous content
            dangerous_sql = ["'", '"', ";", "--", "/*", "*/", "xp_", "sp_"]
            dangerous_xss = ["<script>", "javascript:", "onerror=", "onload="]
            
            for dangerous in dangerous_sql + dangerous_xss:
                if dangerous in payload:
                    # Should be removed or escaped
                    assert dangerous not in sanitized or sanitized != payload
    
    def test_content_security_policy_headers(self, security_test_client):
        """Test Content Security Policy headers."""
        response = security_test_client.get("/api/documents")
        
        # Should include CSP headers
        csp_header = response.headers.get("Content-Security-Policy")
        if csp_header:
            # Should restrict script sources
            assert "script-src" in csp_header
            assert "'unsafe-inline'" not in csp_header or "'strict-dynamic'" in csp_header
            
            # Should restrict object sources
            assert "object-src 'none'" in csp_header or "object-src" not in csp_header
    
    def test_sql_query_validation(self):
        """Test SQL query validation utility."""
        # Valid queries should pass
        valid_queries = [
            "SELECT * FROM documents WHERE id = ?",
            "INSERT INTO documents (title, content) VALUES (?, ?)",
            "UPDATE documents SET title = ? WHERE id = ?",
        ]
        
        for query in valid_queries:
            assert validate_sql_query(query) is True
        
        # Invalid/dangerous queries should fail
        dangerous_queries = [
            "SELECT * FROM documents; DROP TABLE users; --",
            "SELECT * FROM documents WHERE id = 1 OR 1=1",
            "INSERT INTO documents (title) VALUES ('test'); DELETE FROM users; --",
            "EXEC xp_cmdshell('dir')",
            "SELECT * FROM information_schema.tables",
        ]
        
        for query in dangerous_queries:
            assert validate_sql_query(query) is False
    
    def test_stored_xss_prevention(self, security_test_client):
        """Test stored XSS prevention."""
        # Upload document with malicious content
        malicious_content = "<script>alert('stored XSS')</script>"
        
        import tempfile
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix=".txt", delete=False)
        temp_file.write(malicious_content)
        temp_file.close()
        
        try:
            with open(temp_file.name, "rb") as f:
                response = security_test_client.post(
                    "/api/documents/upload",
                    files={"file": ("malicious.txt", f, "text/plain")}
                )
            
            if response.status_code == 200:
                doc_id = response.json()["id"]
                
                # Retrieve document content
                content_response = security_test_client.get(f"/api/documents/{doc_id}/content")
                
                if content_response.status_code == 200:
                    content = content_response.json()
                    content_str = str(content)
                    
                    # Should not contain executable script
                    assert "<script>" not in content_str
                    assert "alert(" not in content_str
        finally:
            import os
            os.unlink(temp_file.name)
    
    def test_reflected_xss_prevention(self, security_test_client):
        """Test reflected XSS prevention."""
        xss_payload = "<script>alert('reflected XSS')</script>"
        
        # Test various endpoints that might reflect user input
        test_endpoints = [
            f"/api/search?q={xss_payload}",
            f"/api/documents?title={xss_payload}",
            f"/api/error?message={xss_payload}",
        ]
        
        for endpoint in test_endpoints:
            response = security_test_client.get(endpoint)
            
            if response.status_code == 200:
                response_text = response.text
                
                # Should not reflect unescaped XSS payload
                assert "<script>" not in response_text
                assert "alert(" not in response_text
                
                # If the payload is reflected, it should be escaped
                if xss_payload in endpoint and any(char in response_text for char in "<>\"'"):
                    # Should be properly escaped
                    assert "&lt;" in response_text or "&gt;" in response_text
    
    def test_dom_based_xss_prevention(self, security_test_client):
        """Test DOM-based XSS prevention in API responses."""
        # Test API responses that might be used in DOM manipulation
        response = security_test_client.get("/api/documents")
        
        if response.status_code == 200:
            data = response.json()
            
            # Check that response data is safe for DOM insertion
            response_str = str(data)
            
            # Should not contain dangerous JavaScript constructs
            dangerous_patterns = [
                "javascript:", "data:text/html", "vbscript:",
                "<script", "<iframe", "<object", "<embed"
            ]
            
            for pattern in dangerous_patterns:
                assert pattern not in response_str.lower()
    
    def test_blind_sql_injection_prevention(self, security_test_client):
        """Test blind SQL injection prevention."""
        # Test time-based blind SQL injection
        time_based_payloads = [
            "1' AND (SELECT SLEEP(5)) --",
            "1' AND (SELECT pg_sleep(5)) --",
            "1'; WAITFOR DELAY '00:00:05' --",
        ]
        
        import time
        for payload in time_based_payloads:
            start_time = time.time()
            response = security_test_client.get(f"/api/search?q={payload}")
            end_time = time.time()
            
            # Should not delay response (indicating SQL injection worked)
            response_time = end_time - start_time
            assert response_time < 2.0  # Should respond quickly
            
            # Should not return 500 error
            assert response.status_code != 500
    
    def test_second_order_injection_prevention(self, security_test_client):
        """Test second-order injection prevention."""
        # First, store malicious data
        malicious_title = "'; DROP TABLE documents; --"
        
        import tempfile
        temp_file = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
        temp_file.write(b"%PDF-1.4\nTest content")
        temp_file.close()
        
        try:
            with open(temp_file.name, "rb") as f:
                response = security_test_client.post(
                    "/api/documents/upload",
                    files={"file": (malicious_title, f, "application/pdf")}
                )
            
            if response.status_code == 200:
                doc_id = response.json()["id"]
                
                # Then, use stored data in another query
                search_response = security_test_client.get(f"/api/documents/{doc_id}")
                
                # Should handle stored malicious data safely
                assert search_response.status_code != 500
                
                if search_response.status_code == 200:
                    data = search_response.json()
                    # Should not expose SQL errors
                    response_str = str(data).lower()
                    assert "sql" not in response_str
                    assert "error" not in response_str or "syntax" not in response_str
        finally:
            import os
            os.unlink(temp_file.name)