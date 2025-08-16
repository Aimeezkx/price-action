"""
Integration tests for API endpoints and frontend-backend communication.
Tests complete API workflows and data flow between frontend and backend.
"""

import pytest
import json
import asyncio
from httpx import AsyncClient
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
import tempfile
import os

from main import app
from app.core.database import get_db
from app.models.document import Document, DocumentStatus
from app.models.learning import Card


class TestAPIIntegration:
    """Test API integration between frontend and backend"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)
    
    @pytest.fixture
    async def async_client(self):
        """Create async test client"""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            yield ac
    
    @pytest.fixture
    def sample_pdf_file(self):
        """Create sample PDF file for upload testing"""
        content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n"
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            f.write(content)
            yield f.name
        
        os.unlink(f.name)
    
    async def test_document_upload_api_workflow(self, async_client, sample_pdf_file):
        """Test complete document upload API workflow"""
        
        # Step 1: Upload document
        with open(sample_pdf_file, 'rb') as f:
            files = {"file": ("test.pdf", f, "application/pdf")}
            response = await async_client.post("/api/documents/upload", files=files)
        
        assert response.status_code == 200
        upload_data = response.json()
        assert "document_id" in upload_data
        document_id = upload_data["document_id"]
        
        # Step 2: Check document status
        response = await async_client.get(f"/api/documents/{document_id}")
        assert response.status_code == 200
        
        doc_data = response.json()
        assert doc_data["id"] == document_id
        assert doc_data["filename"] == "test.pdf"
        assert doc_data["status"] in ["uploaded", "processing", "completed"]
        
        # Step 3: Wait for processing (simulate)
        max_retries = 10
        for _ in range(max_retries):
            response = await async_client.get(f"/api/documents/{document_id}")
            doc_data = response.json()
            
            if doc_data["status"] == "completed":
                break
            
            await asyncio.sleep(0.5)
        
        # Step 4: Get chapters
        response = await async_client.get(f"/api/documents/{document_id}/chapters")
        assert response.status_code == 200
        
        chapters_data = response.json()
        assert isinstance(chapters_data, list)
        
        if len(chapters_data) > 0:
            chapter = chapters_data[0]
            assert "id" in chapter
            assert "title" in chapter
            assert "content" in chapter
            assert chapter["document_id"] == document_id
        
        # Step 5: Get knowledge points
        response = await async_client.get(f"/api/documents/{document_id}/knowledge")
        assert response.status_code == 200
        
        knowledge_data = response.json()
        assert isinstance(knowledge_data, list)
        
        # Step 6: Get cards
        response = await async_client.get(f"/api/documents/{document_id}/cards")
        assert response.status_code == 200
        
        cards_data = response.json()
        assert isinstance(cards_data, list)
        
        if len(cards_data) > 0:
            card = cards_data[0]
            assert "id" in card
            assert "front_content" in card
            assert "back_content" in card
            assert "card_type" in card
    
    async def test_search_api_integration(self, async_client, sample_pdf_file):
        """Test search API integration"""
        
        # First upload a document
        with open(sample_pdf_file, 'rb') as f:
            files = {"file": ("searchable.pdf", f, "application/pdf")}
            response = await async_client.post("/api/documents/upload", files=files)
        
        assert response.status_code == 200
        document_id = response.json()["document_id"]
        
        # Wait for processing
        await asyncio.sleep(1)
        
        # Test text search
        response = await async_client.get(
            "/api/search",
            params={"query": "test", "type": "text"}
        )
        assert response.status_code == 200
        
        search_results = response.json()
        assert "results" in search_results
        assert isinstance(search_results["results"], list)
        
        # Test semantic search
        response = await async_client.get(
            "/api/search",
            params={"query": "learning concepts", "type": "semantic"}
        )
        assert response.status_code == 200
        
        semantic_results = response.json()
        assert "results" in semantic_results
        
        # Test search with filters
        response = await async_client.get(
            "/api/search",
            params={
                "query": "test",
                "document_ids": [document_id],
                "difficulty_min": 0.0,
                "difficulty_max": 1.0
            }
        )
        assert response.status_code == 200
        
        filtered_results = response.json()
        assert "results" in filtered_results
    
    async def test_card_review_api_workflow(self, async_client, sample_pdf_file):
        """Test card review API workflow"""
        
        # Upload and process document
        with open(sample_pdf_file, 'rb') as f:
            files = {"file": ("review_test.pdf", f, "application/pdf")}
            response = await async_client.post("/api/documents/upload", files=files)
        
        document_id = response.json()["document_id"]
        
        # Wait for processing
        await asyncio.sleep(1)
        
        # Get cards for review
        response = await async_client.get("/api/cards/due")
        assert response.status_code == 200
        
        due_cards = response.json()
        assert isinstance(due_cards, list)
        
        if len(due_cards) > 0:
            card = due_cards[0]
            card_id = card["id"]
            
            # Review card
            review_data = {
                "grade": 4,
                "response_time": 5.2,
                "notes": "Good recall"
            }
            
            response = await async_client.post(
                f"/api/cards/{card_id}/review",
                json=review_data
            )
            assert response.status_code == 200
            
            review_result = response.json()
            assert "next_due_date" in review_result
            assert "new_interval" in review_result
            
            # Verify SRS state updated
            response = await async_client.get(f"/api/cards/{card_id}/srs")
            assert response.status_code == 200
            
            srs_data = response.json()
            assert srs_data["interval"] > 1
            assert srs_data["ease_factor"] > 0
    
    async def test_export_api_integration(self, async_client, sample_pdf_file):
        """Test export API integration"""
        
        # Upload document
        with open(sample_pdf_file, 'rb') as f:
            files = {"file": ("export_test.pdf", f, "application/pdf")}
            response = await async_client.post("/api/documents/upload", files=files)
        
        document_id = response.json()["document_id"]
        
        # Wait for processing
        await asyncio.sleep(1)
        
        # Test Anki export
        response = await async_client.post(
            "/api/export/anki",
            json={"document_ids": [document_id]}
        )
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/octet-stream"
        
        # Test JSON export
        response = await async_client.post(
            "/api/export/json",
            json={"document_ids": [document_id]}
        )
        assert response.status_code == 200
        
        export_data = response.json()
        assert "documents" in export_data
        assert "cards" in export_data
        assert "knowledge_points" in export_data
    
    async def test_api_error_handling(self, async_client):
        """Test API error handling"""
        
        # Test invalid document ID
        response = await async_client.get("/api/documents/invalid-id")
        assert response.status_code == 404
        
        error_data = response.json()
        assert "detail" in error_data
        
        # Test invalid file upload
        files = {"file": ("test.txt", b"invalid content", "text/plain")}
        response = await async_client.post("/api/documents/upload", files=files)
        assert response.status_code == 400
        
        # Test invalid search parameters
        response = await async_client.get("/api/search")  # Missing query
        assert response.status_code == 422
        
        # Test invalid card review
        response = await async_client.post(
            "/api/cards/invalid-id/review",
            json={"grade": 10}  # Invalid grade
        )
        assert response.status_code in [400, 404, 422]
    
    async def test_api_authentication_integration(self, async_client):
        """Test API authentication and authorization"""
        
        # Test protected endpoints without authentication
        protected_endpoints = [
            "/api/documents/upload",
            "/api/documents/123",
            "/api/cards/due",
            "/api/search"
        ]
        
        for endpoint in protected_endpoints:
            if endpoint == "/api/documents/upload":
                response = await async_client.post(endpoint)
            else:
                response = await async_client.get(endpoint)
            
            # Should require authentication (adjust based on your auth implementation)
            assert response.status_code in [401, 403, 422]  # Unauthorized or validation error
    
    async def test_api_rate_limiting(self, async_client):
        """Test API rate limiting"""
        
        # Make multiple rapid requests
        responses = []
        for _ in range(10):
            response = await async_client.get("/api/health")
            responses.append(response.status_code)
        
        # Most should succeed, but rate limiting might kick in
        success_count = sum(1 for status in responses if status == 200)
        assert success_count >= 5  # At least some should succeed
    
    async def test_websocket_integration(self, async_client):
        """Test WebSocket integration for real-time updates"""
        
        # This would test WebSocket connections for real-time document processing updates
        # Implementation depends on your WebSocket setup
        
        # Example structure:
        # async with async_client.websocket_connect("/ws/documents") as websocket:
        #     # Send document for processing
        #     await websocket.send_json({"action": "process", "document_id": "123"})
        #     
        #     # Receive processing updates
        #     data = await websocket.receive_json()
        #     assert data["status"] in ["processing", "completed", "error"]
        
        pass  # Placeholder for WebSocket tests
    
    async def test_api_performance_benchmarks(self, async_client, sample_pdf_file):
        """Test API performance benchmarks"""
        
        import time
        
        # Test upload performance
        start_time = time.time()
        
        with open(sample_pdf_file, 'rb') as f:
            files = {"file": ("perf_test.pdf", f, "application/pdf")}
            response = await async_client.post("/api/documents/upload", files=files)
        
        upload_time = time.time() - start_time
        
        assert response.status_code == 200
        assert upload_time < 5.0  # Should upload within 5 seconds
        
        document_id = response.json()["document_id"]
        
        # Test search performance
        start_time = time.time()
        
        response = await async_client.get(
            "/api/search",
            params={"query": "test", "type": "text"}
        )
        
        search_time = time.time() - start_time
        
        assert response.status_code == 200
        assert search_time < 0.5  # Should search within 500ms
        
        # Test concurrent API requests
        async def make_request():
            return await async_client.get(f"/api/documents/{document_id}")
        
        start_time = time.time()
        
        tasks = [make_request() for _ in range(5)]
        responses = await asyncio.gather(*tasks)
        
        concurrent_time = time.time() - start_time
        
        # All requests should succeed
        assert all(r.status_code == 200 for r in responses)
        assert concurrent_time < 2.0  # Should handle concurrent requests efficiently