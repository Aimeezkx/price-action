"""Test privacy mode validation."""

import pytest
from unittest.mock import patch, Mock, call
import tempfile
import os

from app.core.config import settings
from app.services.document_service import DocumentService
from app.services.knowledge_extraction_service import KnowledgeExtractionService
from app.services.embedding_service import EmbeddingService


class TestPrivacyMode:
    """Test privacy mode functionality."""
    
    def test_privacy_mode_blocks_external_apis(self, security_test_client, mock_external_api_calls):
        """Test that privacy mode blocks external API calls."""
        # Enable privacy mode
        with patch.object(settings, 'privacy_mode', True):
            # Upload and process a document
            temp_file = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
            temp_file.write(b"%PDF-1.4\nTest content for privacy mode testing")
            temp_file.close()
            
            try:
                with open(temp_file.name, "rb") as f:
                    response = security_test_client.post(
                        "/api/documents/upload",
                        files={"file": ("test.pdf", f, "application/pdf")}
                    )
                
                assert response.status_code == 200
                doc_id = response.json()["id"]
                
                # Wait for processing
                processing_response = security_test_client.get(f"/api/documents/{doc_id}")
                
                # Verify no external API calls were made
                assert len(mock_external_api_calls) == 0, f"External API calls made: {mock_external_api_calls}"
            finally:
                os.unlink(temp_file.name)
    
    def test_privacy_mode_uses_local_models(self, security_test_client):
        """Test that privacy mode uses local models only."""
        with patch.object(settings, 'privacy_mode', True), \
             patch('app.services.embedding_service.EmbeddingService.generate_embeddings') as mock_embed, \
             patch('app.services.knowledge_extraction_service.KnowledgeExtractionService.extract_knowledge') as mock_extract:
            
            # Configure mocks to return local results
            mock_embed.return_value = [[0.1, 0.2, 0.3]]
            mock_extract.return_value = {"entities": [], "concepts": []}
            
            temp_file = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
            temp_file.write(b"%PDF-1.4\nTest content")
            temp_file.close()
            
            try:
                with open(temp_file.name, "rb") as f:
                    response = security_test_client.post(
                        "/api/documents/upload",
                        files={"file": ("test.pdf", f, "application/pdf")}
                    )
                
                assert response.status_code == 200
                
                # Verify local models were used
                mock_embed.assert_called()
                mock_extract.assert_called()
            finally:
                os.unlink(temp_file.name)
    
    def test_privacy_mode_configuration(self):
        """Test privacy mode configuration validation."""
        # Test privacy mode enabled
        with patch.object(settings, 'privacy_mode', True):
            service = DocumentService()
            assert service.is_privacy_mode_enabled() is True
        
        # Test privacy mode disabled
        with patch.object(settings, 'privacy_mode', False):
            service = DocumentService()
            assert service.is_privacy_mode_enabled() is False
    
    def test_privacy_mode_embedding_service(self):
        """Test embedding service respects privacy mode."""
        embedding_service = EmbeddingService()
        
        # Test with privacy mode enabled
        with patch.object(settings, 'privacy_mode', True), \
             patch('app.services.embedding_service.local_embedding_model') as mock_local, \
             patch('requests.post') as mock_external:
            
            mock_local.encode.return_value = [[0.1, 0.2, 0.3]]
            
            embeddings = embedding_service.generate_embeddings(["test text"])
            
            # Should use local model
            mock_local.encode.assert_called_once()
            mock_external.assert_not_called()
            assert embeddings == [[0.1, 0.2, 0.3]]
        
        # Test with privacy mode disabled
        with patch.object(settings, 'privacy_mode', False), \
             patch('requests.post') as mock_external:
            
            mock_external.return_value.json.return_value = {"embeddings": [[0.4, 0.5, 0.6]]}
            mock_external.return_value.status_code = 200
            
            embeddings = embedding_service.generate_embeddings(["test text"])
            
            # Should use external API
            mock_external.assert_called_once()
            assert embeddings == [[0.4, 0.5, 0.6]]
    
    def test_privacy_mode_knowledge_extraction(self):
        """Test knowledge extraction respects privacy mode."""
        knowledge_service = KnowledgeExtractionService()
        
        # Test with privacy mode enabled
        with patch.object(settings, 'privacy_mode', True), \
             patch('app.services.knowledge_extraction_service.local_nlp_model') as mock_local, \
             patch('requests.post') as mock_external:
            
            mock_local.return_value = {"entities": ["entity1"], "concepts": ["concept1"]}
            
            result = knowledge_service.extract_knowledge("test text")
            
            # Should use local model
            mock_local.assert_called_once()
            mock_external.assert_not_called()
            assert result["entities"] == ["entity1"]
        
        # Test with privacy mode disabled
        with patch.object(settings, 'privacy_mode', False), \
             patch('requests.post') as mock_external:
            
            mock_external.return_value.json.return_value = {"entities": ["entity2"], "concepts": ["concept2"]}
            mock_external.return_value.status_code = 200
            
            result = knowledge_service.extract_knowledge("test text")
            
            # Should use external API
            mock_external.assert_called_once()
            assert result["entities"] == ["entity2"]
    
    def test_privacy_mode_data_retention(self, security_test_client):
        """Test data retention policies in privacy mode."""
        with patch.object(settings, 'privacy_mode', True):
            # Upload document
            temp_file = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
            temp_file.write(b"%PDF-1.4\nSensitive content")
            temp_file.close()
            
            try:
                with open(temp_file.name, "rb") as f:
                    response = security_test_client.post(
                        "/api/documents/upload",
                        files={"file": ("sensitive.pdf", f, "application/pdf")}
                    )
                
                assert response.status_code == 200
                doc_id = response.json()["id"]
                
                # Verify document can be deleted immediately in privacy mode
                delete_response = security_test_client.delete(f"/api/documents/{doc_id}")
                assert delete_response.status_code == 200
                
                # Verify document is actually deleted
                get_response = security_test_client.get(f"/api/documents/{doc_id}")
                assert get_response.status_code == 404
            finally:
                os.unlink(temp_file.name)
    
    def test_privacy_mode_search_isolation(self, security_test_client):
        """Test search isolation in privacy mode."""
        with patch.object(settings, 'privacy_mode', True):
            # Test that search doesn't use external services
            with patch('requests.get') as mock_external:
                response = security_test_client.get("/api/search?q=test+query")
                
                # Should work without external calls
                assert response.status_code == 200
                mock_external.assert_not_called()
    
    def test_privacy_mode_logging_restrictions(self, security_test_client, caplog):
        """Test logging restrictions in privacy mode."""
        with patch.object(settings, 'privacy_mode', True):
            temp_file = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
            temp_file.write(b"%PDF-1.4\nConfidential information")
            temp_file.close()
            
            try:
                with open(temp_file.name, "rb") as f:
                    response = security_test_client.post(
                        "/api/documents/upload",
                        files={"file": ("confidential.pdf", f, "application/pdf")}
                    )
                
                assert response.status_code == 200
                
                # Check that sensitive information is not logged
                log_messages = [record.message for record in caplog.records]
                for message in log_messages:
                    assert "confidential" not in message.lower()
                    assert "Confidential information" not in message
            finally:
                os.unlink(temp_file.name)
    
    def test_privacy_mode_api_endpoint_restrictions(self, security_test_client):
        """Test API endpoint restrictions in privacy mode."""
        with patch.object(settings, 'privacy_mode', True):
            # Test that certain endpoints are restricted in privacy mode
            restricted_endpoints = [
                "/api/analytics/usage",
                "/api/export/cloud",
                "/api/sync/external"
            ]
            
            for endpoint in restricted_endpoints:
                response = security_test_client.get(endpoint)
                # Should be forbidden or not found in privacy mode
                assert response.status_code in [403, 404]
    
    def test_privacy_mode_metadata_scrubbing(self, security_test_client):
        """Test metadata scrubbing in privacy mode."""
        with patch.object(settings, 'privacy_mode', True):
            temp_file = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
            # Create PDF with metadata
            pdf_content = b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
/Metadata 3 0 R
>>
endobj
2 0 obj
<<
/Type /Pages
/Kids [4 0 R]
/Count 1
>>
endobj
3 0 obj
<<
/Type /Metadata
/Subtype /XML
/Length 100
>>
stream
<metadata>
<author>John Doe</author>
<company>Secret Corp</company>
</metadata>
endstream
endobj
4 0 obj
<<
/Type /Page
/Parent 2 0 R
/Contents 5 0 R
>>
endobj
5 0 obj
<<
/Length 44
>>
stream
BT
/F1 12 Tf
100 700 Td
(Hello World) Tj
ET
endstream
endobj
xref
0 6
0000000000 65535 f 
0000000009 00000 n 
0000000074 00000 n 
0000000120 00000 n 
0000000300 00000 n 
0000000400 00000 n 
trailer
<<
/Size 6
/Root 1 0 R
>>
startxref
500
%%EOF"""
            temp_file.write(pdf_content)
            temp_file.close()
            
            try:
                with open(temp_file.name, "rb") as f:
                    response = security_test_client.post(
                        "/api/documents/upload",
                        files={"file": ("document_with_metadata.pdf", f, "application/pdf")}
                    )
                
                assert response.status_code == 200
                doc_data = response.json()
                
                # Verify sensitive metadata is scrubbed
                assert "John Doe" not in str(doc_data)
                assert "Secret Corp" not in str(doc_data)
            finally:
                os.unlink(temp_file.name)