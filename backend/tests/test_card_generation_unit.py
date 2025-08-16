"""Comprehensive unit tests for card generation algorithms and SRS calculations."""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
import numpy as np

from app.services.card_generation_service import CardGenerationService
from app.services.srs_service import SRSService
from app.models.knowledge import KnowledgeType
from app.models.learning import CardType


@pytest.mark.unit
class TestCardGenerationService:
    """Test card generation algorithms."""
    
    def test_service_initialization(self):
        """Test service initializes correctly."""
        service = CardGenerationService()
        assert service is not None
        assert hasattr(service, 'generate_cards')
    
    @pytest.mark.asyncio
    async def test_qa_card_generation(self):
        """Test Q&A card generation from knowledge points."""
        service = CardGenerationService()
        
        knowledge_point = {
            "text": "Machine learning is a method of data analysis that automates analytical model building.",
            "kind": KnowledgeType.DEFINITION,
            "entities": ["machine learning", "data analysis", "analytical model"]
        }
        
        with patch.object(service, '_generate_qa_card') as mock_qa:
            mock_qa.return_value = {
                "card_type": CardType.QA,
                "front": "What is machine learning?",
                "back": "Machine learning is a method of data analysis that automates analytical model building.",
                "difficulty": 0.6,
                "metadata": {
                    "source_knowledge": knowledge_point,
                    "generation_method": "definition_to_qa"
                }
            }
            
            cards = await service.generate_cards([knowledge_point])
            
            assert len(cards) == 1
            assert cards[0]["card_type"] == CardType.QA
            assert "What is machine learning?" in cards[0]["front"]
            assert "data analysis" in cards[0]["back"]
            assert 0.0 <= cards[0]["difficulty"] <= 1.0
    
    @pytest.mark.asyncio
    async def test_cloze_card_generation(self):
        """Test cloze deletion card generation."""
        service = CardGenerationService()
        
        knowledge_point = {
            "text": "Python was created by Guido van Rossum in 1991.",
            "kind": KnowledgeType.FACT,
            "entities": ["Python", "Guido van Rossum", "1991"]
        }
        
        with patch.object(service, '_generate_cloze_card') as mock_cloze:
            mock_cloze.return_value = {
                "card_type": CardType.CLOZE,
                "front": "Python was created by {{c1::Guido van Rossum}} in {{c2::1991}}.",
                "back": "Python was created by Guido van Rossum in 1991.",
                "difficulty": 0.4,
                "metadata": {
                    "cloze_deletions": ["Guido van Rossum", "1991"],
                    "entity_based": True
                }
            }
            
            cards = await service.generate_cards([knowledge_point], card_types=[CardType.CLOZE])
            
            assert len(cards) == 1
            assert cards[0]["card_type"] == CardType.CLOZE
            assert "{{c1::" in cards[0]["front"]
            assert "{{c2::" in cards[0]["front"]
            assert "Guido van Rossum" in cards[0]["metadata"]["cloze_deletions"]
    
    @pytest.mark.asyncio
    async def test_image_hotspot_card_generation(self):
        """Test image hotspot card generation."""
        service = CardGenerationService()
        
        knowledge_point = {
            "text": "The neural network architecture shows input layer, hidden layers, and output layer.",
            "kind": KnowledgeType.CONCEPT,
            "entities": ["neural network", "input layer", "hidden layers", "output layer"],
            "image_path": "/path/to/neural_network_diagram.png"
        }
        
        with patch.object(service, '_generate_image_hotspot_card') as mock_hotspot:
            mock_hotspot.return_value = {
                "card_type": CardType.IMAGE_HOTSPOT,
                "front": "Identify the components of this neural network architecture.",
                "back": "Input layer, hidden layers, and output layer",
                "difficulty": 0.7,
                "metadata": {
                    "image_path": "/path/to/neural_network_diagram.png",
                    "hotspots": [
                        {"label": "input layer", "bbox": {"x": 10, "y": 20, "width": 50, "height": 30}},
                        {"label": "hidden layers", "bbox": {"x": 80, "y": 20, "width": 60, "height": 30}},
                        {"label": "output layer", "bbox": {"x": 160, "y": 20, "width": 50, "height": 30}}
                    ]
                }
            }
            
            cards = await service.generate_cards([knowledge_point], card_types=[CardType.IMAGE_HOTSPOT])
            
            assert len(cards) == 1
            assert cards[0]["card_type"] == CardType.IMAGE_HOTSPOT
            assert "hotspots" in cards[0]["metadata"]
            assert len(cards[0]["metadata"]["hotspots"]) == 3
    
    @pytest.mark.asyncio
    async def test_difficulty_calculation(self):
        """Test card difficulty calculation."""
        service = CardGenerationService()
        
        # Simple knowledge point
        simple_knowledge = {
            "text": "Python is a programming language.",
            "kind": KnowledgeType.FACT,
            "entities": ["Python", "programming language"],
            "complexity_score": 0.2
        }
        
        # Complex knowledge point
        complex_knowledge = {
            "text": "The backpropagation algorithm computes gradients by applying the chain rule of calculus to update neural network weights through gradient descent optimization.",
            "kind": KnowledgeType.PROCESS,
            "entities": ["backpropagation", "gradients", "chain rule", "neural network", "gradient descent"],
            "complexity_score": 0.9
        }
        
        with patch.object(service, '_calculate_difficulty') as mock_difficulty:
            mock_difficulty.side_effect = [0.3, 0.8]  # Simple, then complex
            
            simple_difficulty = await service._calculate_difficulty(simple_knowledge)
            complex_difficulty = await service._calculate_difficulty(complex_knowledge)
            
            assert simple_difficulty < complex_difficulty
            assert 0.0 <= simple_difficulty <= 1.0
            assert 0.0 <= complex_difficulty <= 1.0
    
    @pytest.mark.asyncio
    async def test_card_quality_scoring(self):
        """Test card quality scoring algorithm."""
        service = CardGenerationService()
        
        high_quality_card = {
            "front": "What is the primary purpose of the activation function in neural networks?",
            "back": "To introduce non-linearity into the network, allowing it to learn complex patterns.",
            "difficulty": 0.6,
            "clarity_score": 0.9,
            "specificity_score": 0.8,
            "educational_value": 0.9
        }
        
        low_quality_card = {
            "front": "What is it?",
            "back": "Something important.",
            "difficulty": 0.5,
            "clarity_score": 0.3,
            "specificity_score": 0.2,
            "educational_value": 0.3
        }
        
        with patch.object(service, '_score_card_quality') as mock_quality:
            mock_quality.side_effect = [0.87, 0.27]  # High quality, then low quality
            
            high_score = await service._score_card_quality(high_quality_card)
            low_score = await service._score_card_quality(low_quality_card)
            
            assert high_score > low_score
            assert high_score > 0.8
            assert low_score < 0.5
    
    @pytest.mark.asyncio
    async def test_card_filtering_by_quality(self):
        """Test filtering cards by quality threshold."""
        service = CardGenerationService()
        
        knowledge_points = [
            {"text": "High quality knowledge", "kind": KnowledgeType.DEFINITION},
            {"text": "Medium quality knowledge", "kind": KnowledgeType.FACT},
            {"text": "Low quality knowledge", "kind": KnowledgeType.CONCEPT}
        ]
        
        with patch.object(service, '_generate_and_score_cards') as mock_generate:
            mock_generate.return_value = [
                {"front": "Good question?", "back": "Good answer", "quality_score": 0.9},
                {"front": "OK question?", "back": "OK answer", "quality_score": 0.7},
                {"front": "Bad question?", "back": "Bad answer", "quality_score": 0.4}
            ]
            
            cards = await service.generate_cards(
                knowledge_points, 
                min_quality_threshold=0.6
            )
            
            assert len(cards) == 2  # Only high and medium quality cards
            assert all(card["quality_score"] >= 0.6 for card in cards)
    
    @pytest.mark.asyncio
    async def test_batch_card_generation(self):
        """Test generating cards for multiple knowledge points."""
        service = CardGenerationService()
        
        knowledge_points = [
            {"text": "First knowledge point", "kind": KnowledgeType.DEFINITION},
            {"text": "Second knowledge point", "kind": KnowledgeType.FACT},
            {"text": "Third knowledge point", "kind": KnowledgeType.PROCESS}
        ]
        
        with patch.object(service, 'generate_cards') as mock_generate:
            mock_generate.return_value = [
                {"front": "Q1?", "back": "A1", "source_index": 0},
                {"front": "Q2?", "back": "A2", "source_index": 1},
                {"front": "Q3?", "back": "A3", "source_index": 2}
            ]
            
            cards = await service.generate_cards_batch(knowledge_points)
            
            assert len(cards) == 3
            assert cards[0]["source_index"] == 0
            assert cards[2]["source_index"] == 2
    
    @pytest.mark.asyncio
    async def test_adaptive_card_generation(self):
        """Test adaptive card generation based on user performance."""
        service = CardGenerationService()
        
        knowledge_point = {
            "text": "Complex algorithm explanation",
            "kind": KnowledgeType.PROCESS
        }
        
        user_performance = {
            "average_grade": 2.5,  # Struggling (out of 5)
            "difficulty_preference": 0.4,  # Prefers easier cards
            "learning_style": "visual"
        }
        
        with patch.object(service, '_adapt_to_user_performance') as mock_adapt:
            mock_adapt.return_value = [
                {
                    "front": "What is the first step in this algorithm?",
                    "back": "Initialize the variables",
                    "difficulty": 0.3,  # Easier due to poor performance
                    "adapted": True
                }
            ]
            
            cards = await service.generate_cards(
                [knowledge_point], 
                user_performance=user_performance
            )
            
            assert len(cards) == 1
            assert cards[0]["difficulty"] < 0.5  # Adapted to be easier
            assert cards[0]["adapted"] is True
    
    def test_card_validation(self):
        """Test card validation and error handling."""
        service = CardGenerationService()
        
        # Test invalid card structure
        invalid_card = {
            "front": "",  # Empty front
            "back": "Some answer"
        }
        
        with pytest.raises(ValueError, match="Card front cannot be empty"):
            service._validate_card(invalid_card)
        
        # Test missing required fields
        incomplete_card = {
            "front": "Question?"
            # Missing back
        }
        
        with pytest.raises(ValueError, match="Card must have both front and back"):
            service._validate_card(incomplete_card)
    
    @pytest.mark.asyncio
    async def test_card_deduplication(self):
        """Test card deduplication algorithm."""
        service = CardGenerationService()
        
        similar_cards = [
            {"front": "What is machine learning?", "back": "ML is AI subset"},
            {"front": "What is ML?", "back": "Machine learning is AI subset"},  # Similar
            {"front": "Define deep learning", "back": "DL uses neural networks"}  # Different
        ]
        
        with patch.object(service, '_deduplicate_cards') as mock_dedup:
            mock_dedup.return_value = [
                {"front": "What is machine learning?", "back": "ML is AI subset"},
                {"front": "Define deep learning", "back": "DL uses neural networks"}
            ]
            
            deduplicated = await service._deduplicate_cards(similar_cards)
            
            assert len(deduplicated) == 2  # One duplicate removed
            assert any("machine learning" in card["front"] for card in deduplicated)
            assert any("deep learning" in card["front"] for card in deduplicated)


@pytest.mark.unit
class TestSRSService:
    """Test Spaced Repetition System calculations."""
    
    def test_service_initialization(self):
        """Test SRS service initializes correctly."""
        service = SRSService()
        assert service is not None
        assert hasattr(service, 'calculate_next_review')
    
    def test_initial_srs_state(self):
        """Test initial SRS state for new cards."""
        service = SRSService()
        
        initial_state = service.create_initial_state()
        
        assert initial_state["ease_factor"] == 2.5
        assert initial_state["interval"] == 1
        assert initial_state["repetitions"] == 0
        assert initial_state["due_date"] is not None
    
    def test_srs_calculation_grade_5(self):
        """Test SRS calculation for perfect grade (5)."""
        service = SRSService()
        
        current_state = {
            "ease_factor": 2.5,
            "interval": 1,
            "repetitions": 0,
            "due_date": datetime.now()
        }
        
        new_state = service.calculate_next_review(current_state, grade=5)
        
        assert new_state["repetitions"] == 1
        assert new_state["interval"] > current_state["interval"]
        assert new_state["ease_factor"] >= current_state["ease_factor"]
        assert new_state["due_date"] > current_state["due_date"]
    
    def test_srs_calculation_grade_4(self):
        """Test SRS calculation for good grade (4)."""
        service = SRSService()
        
        current_state = {
            "ease_factor": 2.5,
            "interval": 6,
            "repetitions": 2,
            "due_date": datetime.now()
        }
        
        new_state = service.calculate_next_review(current_state, grade=4)
        
        assert new_state["repetitions"] == 3
        assert new_state["interval"] > current_state["interval"]
        assert new_state["ease_factor"] >= 2.5  # Should not decrease
    
    def test_srs_calculation_grade_3(self):
        """Test SRS calculation for satisfactory grade (3)."""
        service = SRSService()
        
        current_state = {
            "ease_factor": 2.5,
            "interval": 6,
            "repetitions": 2,
            "due_date": datetime.now()
        }
        
        new_state = service.calculate_next_review(current_state, grade=3)
        
        assert new_state["repetitions"] == 3
        assert new_state["interval"] > current_state["interval"]
        assert new_state["ease_factor"] < current_state["ease_factor"]  # Should decrease
    
    def test_srs_calculation_grade_2_or_below(self):
        """Test SRS calculation for failing grades (≤2)."""
        service = SRSService()
        
        current_state = {
            "ease_factor": 2.5,
            "interval": 6,
            "repetitions": 3,
            "due_date": datetime.now()
        }
        
        new_state = service.calculate_next_review(current_state, grade=2)
        
        assert new_state["repetitions"] == 0  # Reset repetitions
        assert new_state["interval"] == 1  # Reset to initial interval
        assert new_state["ease_factor"] < current_state["ease_factor"]  # Decrease ease
        
        # Due date should be soon (within a day)
        time_diff = new_state["due_date"] - datetime.now()
        assert time_diff.total_seconds() < 24 * 3600  # Less than 24 hours
    
    def test_ease_factor_bounds(self):
        """Test that ease factor stays within bounds."""
        service = SRSService()
        
        # Test minimum ease factor
        low_ease_state = {
            "ease_factor": 1.3,  # Already at minimum
            "interval": 1,
            "repetitions": 0,
            "due_date": datetime.now()
        }
        
        new_state = service.calculate_next_review(low_ease_state, grade=1)
        assert new_state["ease_factor"] >= 1.3  # Should not go below minimum
        
        # Test maximum ease factor (if implemented)
        high_ease_state = {
            "ease_factor": 4.0,
            "interval": 1,
            "repetitions": 0,
            "due_date": datetime.now()
        }
        
        new_state = service.calculate_next_review(high_ease_state, grade=5)
        # Ease factor should have reasonable upper bound
        assert new_state["ease_factor"] <= 5.0
    
    def test_interval_progression(self):
        """Test interval progression through multiple reviews."""
        service = SRSService()
        
        state = service.create_initial_state()
        intervals = [state["interval"]]
        
        # Simulate several successful reviews
        for grade in [5, 4, 5, 4, 5]:
            state = service.calculate_next_review(state, grade)
            intervals.append(state["interval"])
        
        # Intervals should generally increase
        assert intervals[-1] > intervals[0]
        assert len(set(intervals)) > 1  # Should have different intervals
    
    def test_due_date_calculation(self):
        """Test due date calculation accuracy."""
        service = SRSService()
        
        current_time = datetime.now()
        state = {
            "ease_factor": 2.5,
            "interval": 7,  # 7 days
            "repetitions": 1,
            "due_date": current_time
        }
        
        new_state = service.calculate_next_review(state, grade=4)
        
        expected_due = current_time + timedelta(days=new_state["interval"])
        actual_due = new_state["due_date"]
        
        # Should be within a few minutes of expected
        time_diff = abs((actual_due - expected_due).total_seconds())
        assert time_diff < 300  # Less than 5 minutes difference
    
    def test_srs_statistics(self):
        """Test SRS statistics calculation."""
        service = SRSService()
        
        review_history = [
            {"grade": 5, "date": datetime.now() - timedelta(days=10)},
            {"grade": 4, "date": datetime.now() - timedelta(days=8)},
            {"grade": 3, "date": datetime.now() - timedelta(days=5)},
            {"grade": 5, "date": datetime.now() - timedelta(days=2)},
        ]
        
        stats = service.calculate_statistics(review_history)
        
        assert "average_grade" in stats
        assert "success_rate" in stats
        assert "retention_rate" in stats
        assert stats["average_grade"] == 4.25  # (5+4+3+5)/4
        assert stats["success_rate"] == 0.75  # 3 out of 4 grades >= 4
    
    def test_optimal_review_scheduling(self):
        """Test optimal review scheduling algorithm."""
        service = SRSService()
        
        cards_due = [
            {"id": 1, "due_date": datetime.now() - timedelta(days=1), "difficulty": 0.8},
            {"id": 2, "due_date": datetime.now() - timedelta(hours=2), "difficulty": 0.3},
            {"id": 3, "due_date": datetime.now() + timedelta(hours=1), "difficulty": 0.6},
        ]
        
        scheduled = service.schedule_optimal_review_order(cards_due)
        
        # Should prioritize overdue cards and difficulty
        assert len(scheduled) == 3
        assert scheduled[0]["id"] == 1  # Most overdue and difficult
        assert scheduled[1]["id"] == 2  # Overdue but easier
    
    def test_srs_performance_prediction(self):
        """Test SRS performance prediction."""
        service = SRSService()
        
        card_state = {
            "ease_factor": 2.2,
            "interval": 14,
            "repetitions": 4,
            "difficulty": 0.7,
            "recent_grades": [4, 3, 5, 4]
        }
        
        prediction = service.predict_performance(card_state)
        
        assert "success_probability" in prediction
        assert "recommended_grade" in prediction
        assert 0.0 <= prediction["success_probability"] <= 1.0
        assert 1 <= prediction["recommended_grade"] <= 5
    
    def test_adaptive_difficulty_adjustment(self):
        """Test adaptive difficulty adjustment based on performance."""
        service = SRSService()
        
        # Card that user consistently struggles with
        struggling_card = {
            "difficulty": 0.5,
            "recent_grades": [2, 1, 3, 2, 2],
            "success_rate": 0.2
        }
        
        adjusted_difficulty = service.adjust_difficulty(struggling_card)
        assert adjusted_difficulty < struggling_card["difficulty"]  # Should be easier
        
        # Card that user finds too easy
        easy_card = {
            "difficulty": 0.8,
            "recent_grades": [5, 5, 5, 5, 4],
            "success_rate": 0.95
        }
        
        adjusted_difficulty = service.adjust_difficulty(easy_card)
        assert adjusted_difficulty > easy_card["difficulty"]  # Should be harder
    
    def test_srs_validation(self):
        """Test SRS input validation."""
        service = SRSService()
        
        # Test invalid grade
        with pytest.raises(ValueError, match="Grade must be between 1 and 5"):
            service.calculate_next_review({}, grade=6)
        
        with pytest.raises(ValueError, match="Grade must be between 1 and 5"):
            service.calculate_next_review({}, grade=0)
        
        # Test invalid state
        invalid_state = {
            "ease_factor": -1,  # Invalid
            "interval": 1,
            "repetitions": 0
        }
        
        with pytest.raises(ValueError, match="Invalid SRS state"):
            service.calculate_next_review(invalid_state, grade=4)
    
    def test_srs_algorithm_variants(self):
        """Test different SRS algorithm variants."""
        service = SRSService()
        
        state = {
            "ease_factor": 2.5,
            "interval": 1,
            "repetitions": 0,
            "due_date": datetime.now()
        }
        
        # Test SM-2 algorithm (default)
        sm2_result = service.calculate_next_review(state, grade=4, algorithm="SM2")
        
        # Test modified algorithm
        modified_result = service.calculate_next_review(state, grade=4, algorithm="MODIFIED")
        
        # Results should be different but valid
        assert sm2_result["interval"] != modified_result["interval"]
        assert both_results_valid(sm2_result, modified_result)


def both_results_valid(result1, result2):
    """Helper function to validate both SRS results."""
    for result in [result1, result2]:
        if not (result["ease_factor"] >= 1.3 and 
                result["interval"] >= 1 and 
                result["repetitions"] >= 0):
            return False
    return True


@pytest.mark.integration
class TestCardGenerationSRSIntegration:
    """Test integration between card generation and SRS."""
    
    @pytest.mark.asyncio
    async def test_card_to_srs_workflow(self):
        """Test complete workflow from card generation to SRS scheduling."""
        card_service = CardGenerationService()
        srs_service = SRSService()
        
        knowledge_point = {
            "text": "Test knowledge for integration",
            "kind": KnowledgeType.DEFINITION
        }
        
        with patch.object(card_service, 'generate_cards') as mock_cards:
            mock_cards.return_value = [
                {
                    "front": "What is the test knowledge?",
                    "back": "Test knowledge for integration",
                    "difficulty": 0.6
                }
            ]
            
            # Generate cards
            cards = await card_service.generate_cards([knowledge_point])
            
            # Initialize SRS for each card
            srs_states = []
            for card in cards:
                srs_state = srs_service.create_initial_state()
                srs_state["card_difficulty"] = card["difficulty"]
                srs_states.append(srs_state)
            
            assert len(cards) == 1
            assert len(srs_states) == 1
            assert srs_states[0]["card_difficulty"] == 0.6
    
    @pytest.mark.asyncio
    async def test_difficulty_based_srs_adjustment(self):
        """Test SRS adjustment based on card difficulty."""
        card_service = CardGenerationService()
        srs_service = SRSService()
        
        # Easy card
        easy_card = {"difficulty": 0.2}
        easy_srs = srs_service.create_initial_state()
        easy_srs["card_difficulty"] = easy_card["difficulty"]
        
        # Hard card
        hard_card = {"difficulty": 0.9}
        hard_srs = srs_service.create_initial_state()
        hard_srs["card_difficulty"] = hard_card["difficulty"]
        
        # Same grade for both cards
        easy_result = srs_service.calculate_next_review(easy_srs, grade=4)
        hard_result = srs_service.calculate_next_review(hard_srs, grade=4)
        
        # Hard card should have different scheduling
        assert easy_result["interval"] != hard_result["interval"]
    
    @pytest.mark.asyncio
    async def test_performance_feedback_to_card_generation(self):
        """Test using SRS performance to improve card generation."""
        card_service = CardGenerationService()
        srs_service = SRSService()
        
        # Simulate poor performance on certain card types
        performance_data = {
            "card_type_performance": {
                CardType.CLOZE: {"average_grade": 2.1, "success_rate": 0.3},
                CardType.QA: {"average_grade": 4.2, "success_rate": 0.8}
            }
        }
        
        knowledge_point = {
            "text": "Test knowledge",
            "kind": KnowledgeType.FACT
        }
        
        with patch.object(card_service, '_adapt_generation_strategy') as mock_adapt:
            mock_adapt.return_value = [CardType.QA]  # Prefer QA cards based on performance
            
            preferred_types = await card_service._adapt_generation_strategy(
                knowledge_point, 
                performance_data
            )
            
            assert CardType.QA in preferred_types
            assert CardType.CLOZE not in preferred_types