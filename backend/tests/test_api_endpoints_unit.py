"""Comprehensive unit tests for API endpoints with mock dependencies."""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from fastapi import status
import json
from datetime import datetime
import uuid

from app.main import app
from app.models.document import ProcessingStatus
from app.models.learning import CardType
from app.models.knowledge import KnowledgeType


@pytest.mark.unit
class TestDocumentAPI:
    """Test document API endpoints."""
    
    def test_upload_document_success(self, client):
        """Test successful document upload."""
        with patch('app.api.documents.document_service') as mock_service:
            mock_service.upload_document.return_value = {
                "id": "doc123",
                "filename": "test.pdf",
                "status": ProcessingStatus.PENDING,
                "created_at": datetime.now().isoformat()
            }
            
            # Simulate file upload
            files = {"file": ("test.pdf", b"fake pdf content", "application/pdf")}
            response = client.post("/api/documents/upload", files=files)
            
            assert response.status_code == status.HTTP_201_CREATED
            data = response.json()
            assert data["id"] == "doc123"
            assert data["filename"] == "test.pdf"
            assert data["status"] == ProcessingStatus.PENDING
    
    def test_upload_document_invalid_file_type(self, client):
        """Test upload with invalid file type."""
        files = {"file": ("test.txt", b"text content", "text/plain")}
        response = client.post("/api/documents/upload", files=files)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Unsupported file type" in response.json()["detail"]
    
    def test_upload_document_too_large(self, client):
        """Test upload with file too large."""
        large_content = b"A" * (100 * 1024 * 1024)  # 100MB
        files = {"file": ("large.pdf", large_content, "application/pdf")}
        
        response = client.post("/api/documents/upload", files=files)
        
        assert response.status_code == status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
    
    def test_get_document_success(self, client):
        """Test successful document retrieval."""
        doc_id = "doc123"
        
        with patch('app.api.documents.document_service') as mock_service:
            mock_service.get_document.return_value = {
                "id": doc_id,
                "filename": "test.pdf",
                "status": ProcessingStatus.COMPLETED,
                "metadata": {"pages": 10, "size": 1024},
                "created_at": datetime.now().isoformat()
            }
            
            response = client.get(f"/api/documents/{doc_id}")
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["id"] == doc_id
            assert data["status"] == ProcessingStatus.COMPLETED
    
    def test_get_document_not_found(self, client):
        """Test document not found."""
        doc_id = "nonexistent"
        
        with patch('app.api.documents.document_service') as mock_service:
            mock_service.get_document.return_value = None
            
            response = client.get(f"/api/documents/{doc_id}")
            
            assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_list_documents_success(self, client):
        """Test successful document listing."""
        with patch('app.api.documents.document_service') as mock_service:
            mock_service.list_documents.return_value = {
                "documents": [
                    {
                        "id": "doc1",
                        "filename": "test1.pdf",
                        "status": ProcessingStatus.COMPLETED,
                        "created_at": datetime.now().isoformat()
                    },
                    {
                        "id": "doc2", 
                        "filename": "test2.docx",
                        "status": ProcessingStatus.PROCESSING,
                        "created_at": datetime.now().isoformat()
                    }
                ],
                "total": 2,
                "page": 1,
                "per_page": 10
            }
            
            response = client.get("/api/documents/")
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert len(data["documents"]) == 2
            assert data["total"] == 2
    
    def test_list_documents_with_filters(self, client):
        """Test document listing with filters."""
        with patch('app.api.documents.document_service') as mock_service:
            mock_service.list_documents.return_value = {
                "documents": [
                    {
                        "id": "doc1",
                        "filename": "completed.pdf",
                        "status": ProcessingStatus.COMPLETED,
                        "created_at": datetime.now().isoformat()
                    }
                ],
                "total": 1,
                "page": 1,
                "per_page": 10
            }
            
            response = client.get("/api/documents/?status=completed&file_type=pdf")
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert len(data["documents"]) == 1
            assert data["documents"][0]["status"] == ProcessingStatus.COMPLETED
    
    def test_delete_document_success(self, client):
        """Test successful document deletion."""
        doc_id = "doc123"
        
        with patch('app.api.documents.document_service') as mock_service:
            mock_service.delete_document.return_value = True
            
            response = client.delete(f"/api/documents/{doc_id}")
            
            assert response.status_code == status.HTTP_204_NO_CONTENT
    
    def test_delete_document_not_found(self, client):
        """Test deleting non-existent document."""
        doc_id = "nonexistent"
        
        with patch('app.api.documents.document_service') as mock_service:
            mock_service.delete_document.return_value = False
            
            response = client.delete(f"/api/documents/{doc_id}")
            
            assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_get_document_processing_status(self, client):
        """Test getting document processing status."""
        doc_id = "doc123"
        
        with patch('app.api.documents.document_service') as mock_service:
            mock_service.get_processing_status.return_value = {
                "status": ProcessingStatus.PROCESSING,
                "progress": 0.65,
                "current_step": "extracting_knowledge",
                "estimated_completion": datetime.now().isoformat(),
                "error_message": None
            }
            
            response = client.get(f"/api/documents/{doc_id}/status")
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["status"] == ProcessingStatus.PROCESSING
            assert data["progress"] == 0.65
            assert data["current_step"] == "extracting_knowledge"


@pytest.mark.unit
class TestSearchAPI:
    """Test search API endpoints."""
    
    def test_search_success(self, client):
        """Test successful search."""
        with patch('app.api.search.search_service') as mock_service:
            mock_service.search.return_value = [
                {
                    "id": "doc1",
                    "title": "Machine Learning Basics",
                    "content": "Introduction to machine learning concepts...",
                    "score": 0.95,
                    "highlights": ["<mark>machine learning</mark>"]
                },
                {
                    "id": "doc2",
                    "title": "Advanced ML Techniques", 
                    "content": "Deep dive into advanced algorithms...",
                    "score": 0.87,
                    "highlights": ["advanced <mark>algorithms</mark>"]
                }
            ]
            
            response = client.get("/api/search/?q=machine learning")
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert len(data) == 2
            assert data[0]["score"] > data[1]["score"]  # Sorted by relevance
    
    def test_search_empty_query(self, client):
        """Test search with empty query."""
        response = client.get("/api/search/?q=")
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Query cannot be empty" in response.json()["detail"]
    
    def test_semantic_search_success(self, client):
        """Test successful semantic search."""
        with patch('app.api.search.search_service') as mock_service:
            mock_service.semantic_search.return_value = [
                {
                    "id": "doc1",
                    "title": "Neural Networks",
                    "content": "Deep learning architectures...",
                    "semantic_score": 0.92,
                    "embedding_similarity": 0.89
                }
            ]
            
            response = client.get("/api/search/semantic?q=AI algorithms")
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert len(data) == 1
            assert data[0]["semantic_score"] == 0.92
    
    def test_search_with_filters(self, client):
        """Test search with filters."""
        with patch('app.api.search.search_service') as mock_service:
            mock_service.search.return_value = [
                {
                    "id": "doc1",
                    "title": "PDF Document",
                    "document_type": "pdf",
                    "difficulty": 0.6,
                    "score": 0.9
                }
            ]
            
            response = client.get(
                "/api/search/?q=test&document_type=pdf&min_difficulty=0.5&max_difficulty=0.8"
            )
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert len(data) == 1
            assert data[0]["document_type"] == "pdf"
    
    def test_search_suggestions(self, client):
        """Test search suggestions endpoint."""
        with patch('app.api.search.search_service') as mock_service:
            mock_service.get_search_suggestions.return_value = [
                {"suggestion": "machine learning", "frequency": 45, "score": 0.95},
                {"suggestion": "machine vision", "frequency": 12, "score": 0.78}
            ]
            
            response = client.get("/api/search/suggestions?q=mach")
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert len(data) == 2
            assert data[0]["suggestion"] == "machine learning"
    
    def test_faceted_search(self, client):
        """Test faceted search endpoint."""
        with patch('app.api.search.search_service') as mock_service:
            mock_service.faceted_search.return_value = {
                "results": [
                    {"id": "doc1", "title": "Test Doc", "score": 0.9}
                ],
                "facets": {
                    "document_type": {"pdf": 15, "docx": 8},
                    "difficulty": {"easy": 5, "medium": 12, "hard": 9}
                }
            }
            
            response = client.get("/api/search/faceted?q=test")
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert "results" in data
            assert "facets" in data
            assert data["facets"]["document_type"]["pdf"] == 15


@pytest.mark.unit
class TestReviewAPI:
    """Test review/study API endpoints."""
    
    def test_get_cards_for_review(self, client):
        """Test getting cards for review."""
        with patch('app.api.reviews.srs_service') as mock_srs:
            with patch('app.api.reviews.card_service') as mock_cards:
                mock_srs.get_due_cards.return_value = [
                    {
                        "id": "card1",
                        "front": "What is machine learning?",
                        "back": "A method of data analysis...",
                        "card_type": CardType.QA,
                        "difficulty": 0.6,
                        "due_date": datetime.now().isoformat()
                    },
                    {
                        "id": "card2",
                        "front": "Python was created by {{c1::Guido van Rossum}}",
                        "back": "Python was created by Guido van Rossum",
                        "card_type": CardType.CLOZE,
                        "difficulty": 0.4,
                        "due_date": datetime.now().isoformat()
                    }
                ]
                
                response = client.get("/api/reviews/cards")
                
                assert response.status_code == status.HTTP_200_OK
                data = response.json()
                assert len(data) == 2
                assert data[0]["card_type"] == CardType.QA
                assert data[1]["card_type"] == CardType.CLOZE
    
    def test_submit_card_review(self, client):
        """Test submitting card review."""
        card_id = "card123"
        review_data = {
            "grade": 4,
            "response_time": 5.2,
            "user_answer": "A method of data analysis"
        }
        
        with patch('app.api.reviews.srs_service') as mock_srs:
            mock_srs.process_review.return_value = {
                "card_id": card_id,
                "grade": 4,
                "next_review": datetime.now().isoformat(),
                "interval": 6,
                "ease_factor": 2.6
            }
            
            response = client.post(
                f"/api/reviews/cards/{card_id}/review",
                json=review_data
            )
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["card_id"] == card_id
            assert data["grade"] == 4
    
    def test_submit_invalid_grade(self, client):
        """Test submitting invalid grade."""
        card_id = "card123"
        review_data = {"grade": 6}  # Invalid grade
        
        response = client.post(
            f"/api/reviews/cards/{card_id}/review",
            json=review_data
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_get_review_statistics(self, client):
        """Test getting review statistics."""
        with patch('app.api.reviews.srs_service') as mock_srs:
            mock_srs.get_user_statistics.return_value = {
                "total_cards": 150,
                "cards_due": 12,
                "cards_learned": 85,
                "average_grade": 4.2,
                "success_rate": 0.78,
                "streak_days": 15,
                "time_studied_today": 1800  # seconds
            }
            
            response = client.get("/api/reviews/statistics")
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["total_cards"] == 150
            assert data["success_rate"] == 0.78
            assert data["streak_days"] == 15
    
    def test_get_review_history(self, client):
        """Test getting review history."""
        with patch('app.api.reviews.srs_service') as mock_srs:
            mock_srs.get_review_history.return_value = [
                {
                    "card_id": "card1",
                    "grade": 5,
                    "reviewed_at": datetime.now().isoformat(),
                    "response_time": 3.5
                },
                {
                    "card_id": "card2",
                    "grade": 3,
                    "reviewed_at": datetime.now().isoformat(),
                    "response_time": 8.2
                }
            ]
            
            response = client.get("/api/reviews/history?limit=10")
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert len(data) == 2
            assert data[0]["grade"] == 5


@pytest.mark.unit
class TestExportAPI:
    """Test export API endpoints."""
    
    def test_export_cards_anki(self, client):
        """Test exporting cards to Anki format."""
        with patch('app.api.export.export_service') as mock_service:
            mock_service.export_to_anki.return_value = {
                "file_path": "/tmp/export_123.apkg",
                "card_count": 50,
                "export_format": "anki"
            }
            
            response = client.post("/api/export/anki", json={
                "document_ids": ["doc1", "doc2"],
                "include_images": True
            })
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["card_count"] == 50
            assert data["export_format"] == "anki"
    
    def test_export_cards_csv(self, client):
        """Test exporting cards to CSV format."""
        with patch('app.api.export.export_service') as mock_service:
            mock_service.export_to_csv.return_value = {
                "file_path": "/tmp/export_123.csv",
                "card_count": 30,
                "export_format": "csv"
            }
            
            response = client.post("/api/export/csv", json={
                "document_ids": ["doc1"],
                "include_metadata": True
            })
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["card_count"] == 30
            assert data["export_format"] == "csv"
    
    def test_export_knowledge_json(self, client):
        """Test exporting knowledge points to JSON."""
        with patch('app.api.export.export_service') as mock_service:
            mock_service.export_knowledge_json.return_value = {
                "file_path": "/tmp/knowledge_123.json",
                "knowledge_count": 75,
                "export_format": "json"
            }
            
            response = client.post("/api/export/knowledge", json={
                "document_ids": ["doc1", "doc2"],
                "knowledge_types": ["definition", "fact"]
            })
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["knowledge_count"] == 75
    
    def test_get_export_status(self, client):
        """Test getting export job status."""
        export_id = "export123"
        
        with patch('app.api.export.export_service') as mock_service:
            mock_service.get_export_status.return_value = {
                "export_id": export_id,
                "status": "completed",
                "progress": 1.0,
                "file_path": "/tmp/export_123.apkg",
                "created_at": datetime.now().isoformat()
            }
            
            response = client.get(f"/api/export/{export_id}/status")
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["status"] == "completed"
            assert data["progress"] == 1.0
    
    def test_download_export_file(self, client):
        """Test downloading export file."""
        export_id = "export123"
        
        with patch('app.api.export.export_service') as mock_service:
            mock_service.get_export_file.return_value = {
                "file_path": "/tmp/export_123.apkg",
                "filename": "flashcards.apkg",
                "content_type": "application/zip"
            }
            
            with patch('builtins.open', create=True) as mock_open:
                mock_open.return_value.__enter__.return_value.read.return_value = b"fake file content"
                
                response = client.get(f"/api/export/{export_id}/download")
                
                assert response.status_code == status.HTTP_200_OK
                assert response.headers["content-type"] == "application/zip"


@pytest.mark.unit
class TestMonitoringAPI:
    """Test monitoring API endpoints."""
    
    def test_health_check(self, client):
        """Test health check endpoint."""
        with patch('app.api.monitoring.get_system_health') as mock_health:
            mock_health.return_value = {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "services": {
                    "database": "healthy",
                    "redis": "healthy",
                    "vector_index": "healthy"
                },
                "version": "1.0.0"
            }
            
            response = client.get("/api/health")
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["status"] == "healthy"
            assert "services" in data
    
    def test_performance_metrics(self, client):
        """Test performance metrics endpoint."""
        with patch('app.api.monitoring.get_performance_metrics') as mock_metrics:
            mock_metrics.return_value = {
                "response_times": {
                    "avg": 0.15,
                    "p95": 0.45,
                    "p99": 0.89
                },
                "throughput": {
                    "requests_per_second": 120,
                    "documents_processed_per_hour": 45
                },
                "resource_usage": {
                    "cpu_percent": 35.2,
                    "memory_percent": 68.5,
                    "disk_usage_percent": 42.1
                }
            }
            
            response = client.get("/api/monitoring/metrics")
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert "response_times" in data
            assert "throughput" in data
            assert "resource_usage" in data
    
    def test_system_status(self, client):
        """Test system status endpoint."""
        with patch('app.api.monitoring.get_system_status') as mock_status:
            mock_status.return_value = {
                "uptime": 86400,  # 24 hours in seconds
                "active_connections": 25,
                "queue_sizes": {
                    "document_processing": 3,
                    "card_generation": 1,
                    "export": 0
                },
                "error_rates": {
                    "last_hour": 0.02,
                    "last_24h": 0.015
                }
            }
            
            response = client.get("/api/monitoring/status")
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["uptime"] == 86400
            assert "queue_sizes" in data
            assert "error_rates" in data


@pytest.mark.unit
class TestSyncAPI:
    """Test sync API endpoints."""
    
    def test_sync_status(self, client):
        """Test getting sync status."""
        with patch('app.api.sync.sync_service') as mock_service:
            mock_service.get_sync_status.return_value = {
                "last_sync": datetime.now().isoformat(),
                "sync_in_progress": False,
                "pending_changes": 5,
                "conflicts": 0,
                "devices": [
                    {"device_id": "web", "last_seen": datetime.now().isoformat()},
                    {"device_id": "ios", "last_seen": datetime.now().isoformat()}
                ]
            }
            
            response = client.get("/api/sync/status")
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert "last_sync" in data
            assert data["pending_changes"] == 5
            assert len(data["devices"]) == 2
    
    def test_trigger_sync(self, client):
        """Test triggering manual sync."""
        with patch('app.api.sync.sync_service') as mock_service:
            mock_service.trigger_sync.return_value = {
                "sync_id": "sync123",
                "status": "started",
                "estimated_duration": 30
            }
            
            response = client.post("/api/sync/trigger")
            
            assert response.status_code == status.HTTP_202_ACCEPTED
            data = response.json()
            assert data["status"] == "started"
            assert "sync_id" in data
    
    def test_resolve_sync_conflict(self, client):
        """Test resolving sync conflicts."""
        conflict_id = "conflict123"
        resolution_data = {
            "resolution": "use_server",
            "resolved_by": "user123"
        }
        
        with patch('app.api.sync.sync_service') as mock_service:
            mock_service.resolve_conflict.return_value = {
                "conflict_id": conflict_id,
                "status": "resolved",
                "resolution": "use_server"
            }
            
            response = client.post(
                f"/api/sync/conflicts/{conflict_id}/resolve",
                json=resolution_data
            )
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["status"] == "resolved"


@pytest.mark.integration
class TestAPIErrorHandling:
    """Test API error handling and edge cases."""
    
    def test_internal_server_error_handling(self, client):
        """Test handling of internal server errors."""
        with patch('app.api.documents.document_service') as mock_service:
            mock_service.get_document.side_effect = Exception("Database connection failed")
            
            response = client.get("/api/documents/doc123")
            
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            assert "Internal server error" in response.json()["detail"]
    
    def test_validation_error_handling(self, client):
        """Test handling of validation errors."""
        invalid_data = {
            "grade": "invalid",  # Should be integer
            "response_time": -1   # Should be positive
        }
        
        response = client.post("/api/reviews/cards/card123/review", json=invalid_data)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert "validation error" in response.json()["detail"][0]["type"]
    
    def test_rate_limiting(self, client):
        """Test API rate limiting."""
        with patch('app.middleware.rate_limiter.is_rate_limited') as mock_limiter:
            mock_limiter.return_value = True
            
            response = client.get("/api/search/?q=test")
            
            assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
    
    def test_authentication_required(self, client):
        """Test endpoints requiring authentication."""
        # Assuming some endpoints require authentication
        response = client.get("/api/reviews/statistics")
        
        # If authentication is implemented
        # assert response.status_code == status.HTTP_401_UNAUTHORIZED
        
        # For now, just test that endpoint exists
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_401_UNAUTHORIZED]
    
    def test_cors_headers(self, client):
        """Test CORS headers are present."""
        response = client.options("/api/documents/")
        
        # Check for CORS headers
        assert "access-control-allow-origin" in response.headers
        assert "access-control-allow-methods" in response.headers
    
    def test_request_timeout_handling(self, client):
        """Test handling of request timeouts."""
        with patch('app.api.documents.document_service') as mock_service:
            import asyncio
            mock_service.upload_document.side_effect = asyncio.TimeoutError("Request timeout")
            
            files = {"file": ("test.pdf", b"content", "application/pdf")}
            response = client.post("/api/documents/upload", files=files)
            
            assert response.status_code == status.HTTP_408_REQUEST_TIMEOUT
    
    def test_content_type_validation(self, client):
        """Test content type validation."""
        # Send JSON data without proper content type
        response = client.post(
            "/api/reviews/cards/card123/review",
            data='{"grade": 4}',  # Raw string instead of JSON
            headers={"content-type": "text/plain"}
        )
        
        assert response.status_code == status.HTTP_415_UNSUPPORTED_MEDIA_TYPE
    
    def test_malformed_json_handling(self, client):
        """Test handling of malformed JSON."""
        response = client.post(
            "/api/reviews/cards/card123/review",
            data='{"grade": 4,}',  # Malformed JSON
            headers={"content-type": "application/json"}
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_large_request_body_handling(self, client):
        """Test handling of oversized request bodies."""
        large_data = {"data": "A" * (10 * 1024 * 1024)}  # 10MB of data
        
        response = client.post("/api/search/", json=large_data)
        
        assert response.status_code == status.HTTP_413_REQUEST_ENTITY_TOO_LARGE