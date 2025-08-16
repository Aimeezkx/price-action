"""
Comprehensive unit tests demonstrating the testing infrastructure.
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient

from app.parsers.pdf_parser import PDFParser
from app.services.knowledge_extraction_service import KnowledgeExtractionService
from app.services.card_generation_service import CardGenerationService
from app.services.srs_service import SRSService
from tests.factories import DocumentFactory, KnowledgeFactory, CardFactory


@pytest.mark.unit
class TestPDFParser:
    """Test PDF parsing functionality."""
    
    def test_pdf_parser_initialization(self):
        """Test PDF parser can be initialized."""
        parser = PDFParser()
        assert parser is not None
    
    @patch('fitz.open')
    def test_pdf_text_extraction(self, mock_fitz_open, sample_pdf_path):
        """Test PDF text extraction."""
        # Mock PyMuPDF document
        mock_doc = Mock()
        mock_page = Mock()
        mock_page.get_text.return_value = "Sample text content"
        mock_page.number = 0
        mock_doc.__iter__.return_value = [mock_page]
        mock_doc.page_count = 1
        mock_fitz_open.return_value = mock_doc
        
        parser = PDFParser()
        result = parser.parse(str(sample_pdf_path))
        
        assert len(result.text_blocks) > 0
        assert result.text_blocks[0].text == "Sample text content"
        assert result.text_blocks[0].page == 1  # 1-indexed
    
    @patch('fitz.open')
    def test_pdf_image_extraction(self, mock_fitz_open, sample_pdf_path):
        """Test PDF image extraction."""
        # Mock PyMuPDF document with images
        mock_doc = Mock()
        mock_page = Mock()
        mock_page.get_images.return_value = [(0, 0, 100, 100, 8, 'DeviceRGB', '', 'Im1', 'DCTDecode')]
        mock_page.number = 0
        mock_doc.__iter__.return_value = [mock_page]
        mock_doc.page_count = 1
        mock_fitz_open.return_value = mock_doc
        
        parser = PDFParser()
        result = parser.parse(str(sample_pdf_path))
        
        # Should extract images
        assert len(result.images) > 0


@pytest.mark.unit
class TestKnowledgeExtractionService:
    """Test knowledge extraction service."""
    
    @pytest.fixture
    def service(self, mock_embedding_model, mock_llm_client):
        """Create knowledge extraction service with mocks."""
        with patch('app.services.knowledge_extraction_service.SentenceTransformer') as mock_st:
            mock_st.return_value = mock_embedding_model
            service = KnowledgeExtractionService()
            service.llm_client = mock_llm_client
            return service
    
    async def test_extract_knowledge_from_text(self, service):
        """Test knowledge extraction from text."""
        text_segments = [
            {
                "text": "Machine learning is a subset of artificial intelligence that focuses on algorithms.",
                "page": 1,
                "chapter_id": "test-chapter"
            }
        ]
        
        knowledge_points = await service.extract_knowledge(text_segments)
        
        assert len(knowledge_points) > 0
        assert knowledge_points[0]["kind"] == "definition"
        assert "machine learning" in knowledge_points[0]["entities"]
    
    async def test_entity_extraction(self, service):
        """Test entity extraction from text."""
        text = "Neural networks and deep learning are important concepts in AI."
        
        entities = await service.extract_entities(text)
        
        assert len(entities) > 0
        assert any("neural networks" in entity.lower() for entity in entities)


@pytest.mark.unit
class TestCardGenerationService:
    """Test flashcard generation service."""
    
    @pytest.fixture
    def service(self):
        """Create card generation service."""
        return CardGenerationService()
    
    def test_generate_qa_card(self, service):
        """Test Q&A card generation."""
        knowledge = KnowledgeFactory(
            kind="definition",
            text="Machine learning is a method of data analysis that automates analytical model building.",
            entities=["machine learning", "data analysis"]
        )
        
        card = service.generate_qa_card(knowledge)
        
        assert card.card_type == "qa"
        assert "machine learning" in card.front.lower()
        assert card.back == knowledge.text
    
    def test_generate_cloze_card(self, service):
        """Test cloze deletion card generation."""
        knowledge = KnowledgeFactory(
            kind="fact",
            text="Python is a high-level programming language known for its simplicity.",
            entities=["Python", "programming language"]
        )
        
        card = service.generate_cloze_card(knowledge)
        
        assert card.card_type == "cloze"
        assert "___" in card.front  # Should have blanks
        assert "blanks" in card.metadata
    
    def test_calculate_difficulty(self, service):
        """Test difficulty calculation."""
        easy_text = "This is simple text."
        hard_text = "The implementation of quantum entanglement in cryptographic protocols requires sophisticated mathematical frameworks."
        
        easy_difficulty = service.calculate_difficulty(easy_text, ["simple"])
        hard_difficulty = service.calculate_difficulty(hard_text, ["quantum", "entanglement", "cryptographic", "protocols"])
        
        assert easy_difficulty < hard_difficulty
        assert 0.0 <= easy_difficulty <= 1.0
        assert 0.0 <= hard_difficulty <= 1.0


@pytest.mark.unit
class TestSRSService:
    """Test spaced repetition system service."""
    
    @pytest.fixture
    def service(self):
        """Create SRS service."""
        return SRSService()
    
    def test_sm2_algorithm_good_grade(self, service):
        """Test SM-2 algorithm with good grade."""
        srs_state = {
            "ease_factor": 2.5,
            "interval": 1,
            "repetitions": 0
        }
        
        new_state = service.update_srs_state(srs_state, grade=4)
        
        assert new_state["interval"] > srs_state["interval"]
        assert new_state["repetitions"] == 1
        assert new_state["ease_factor"] >= 2.5
    
    def test_sm2_algorithm_poor_grade(self, service):
        """Test SM-2 algorithm with poor grade."""
        srs_state = {
            "ease_factor": 2.5,
            "interval": 7,
            "repetitions": 3
        }
        
        new_state = service.update_srs_state(srs_state, grade=1)
        
        assert new_state["interval"] == 1  # Reset to 1
        assert new_state["repetitions"] == 0  # Reset repetitions
        assert new_state["ease_factor"] < 2.5  # Decreased ease factor
    
    def test_calculate_due_date(self, service):
        """Test due date calculation."""
        from datetime import datetime, timedelta
        
        base_date = datetime.now()
        interval = 7
        
        due_date = service.calculate_due_date(base_date, interval)
        expected_date = base_date + timedelta(days=interval)
        
        assert abs((due_date - expected_date).total_seconds()) < 60  # Within 1 minute


@pytest.mark.unit
@pytest.mark.performance
class TestPerformanceBenchmarks:
    """Performance benchmark tests."""
    
    def test_document_parsing_performance(self, benchmark, sample_pdf_path):
        """Benchmark document parsing performance."""
        parser = PDFParser()
        
        # Benchmark the parsing operation
        result = benchmark(parser.parse, str(sample_pdf_path))
        
        assert result is not None
        # Performance assertion: should complete within reasonable time
        # The benchmark fixture will automatically measure and report timing
    
    def test_search_performance(self, benchmark, performance_test_data):
        """Benchmark search performance."""
        from app.services.search_service import SearchService
        
        # Mock search service for performance testing
        search_service = SearchService()
        
        def search_operation():
            # Simulate search operation
            query = performance_test_data["test_queries"][0]
            return search_service.search(query, limit=10)
        
        result = benchmark(search_operation)
        assert result is not None


@pytest.mark.unit
@pytest.mark.security
class TestSecurityValidation:
    """Security validation tests."""
    
    def test_file_type_validation(self, client, malicious_files):
        """Test file type validation rejects malicious files."""
        # Test executable file rejection
        with open(malicious_files["exe"], "rb") as f:
            response = client.post(
                "/api/documents/upload",
                files={"file": ("malicious.exe", f, "application/octet-stream")}
            )
        
        assert response.status_code == 400
        assert "unsupported" in response.json()["detail"].lower()
    
    def test_file_size_validation(self, client, malicious_files):
        """Test file size validation."""
        # Test oversized file rejection
        with open(malicious_files["large"], "rb") as f:
            response = client.post(
                "/api/documents/upload",
                files={"file": ("large.pdf", f, "application/pdf")}
            )
        
        assert response.status_code == 400
        assert "size" in response.json()["detail"].lower()
    
    def test_input_sanitization(self, client):
        """Test input sanitization."""
        # Test XSS prevention in search
        malicious_query = "<script>alert('xss')</script>"
        
        response = client.get(f"/api/search?q={malicious_query}")
        
        # Should not return the script tag in response
        assert "<script>" not in response.text
        assert response.status_code in [200, 400]  # Either sanitized or rejected