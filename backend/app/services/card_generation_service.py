"""
Flashcard generation service for creating different types of learning cards.
"""

import re
import json
import random
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Any, Union
from enum import Enum
import logging

from ..models.learning import Card, CardType
from ..models.knowledge import Knowledge, KnowledgeType
from ..models.document import Figure
from ..services.text_segmentation_service import TextSegmentationService
from ..services.deduplication_service import DeduplicationService, DeduplicationConfig
from ..core.database import get_async_session

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class CardGenerationConfig:
    """Configuration for card generation."""
    
    # General settings
    max_cloze_blanks: int = 3
    min_cloze_blanks: int = 1
    min_card_text_length: int = 10
    max_card_text_length: int = 500
    
    # Difficulty calculation
    base_difficulty: float = 1.0
    complexity_weight: float = 0.4
    entity_density_weight: float = 0.3
    length_weight: float = 0.2
    type_weight: float = 0.1
    
    # Type-specific difficulty modifiers
    type_difficulty_modifiers: Dict[CardType, float] = None
    
    # Image hotspot settings
    min_hotspot_size: int = 20  # minimum pixel size for hotspots
    max_hotspots_per_image: int = 5
    hotspot_overlap_threshold: float = 0.3
    
    # Q&A generation settings
    question_templates: Dict[KnowledgeType, List[str]] = None


@dataclass
class GeneratedCard:
    """Represents a generated card before database storage."""
    
    card_type: CardType
    front: str
    back: str
    difficulty: float
    metadata: Dict[str, Any]
    knowledge_id: str
    source_info: Dict[str, Any]


@dataclass
class ImageHotspot:
    """Represents a clickable hotspot on an image."""
    
    x: int
    y: int
    width: int
    height: int
    label: str
    description: str
    correct: bool = False


class CardGenerationService:
    """Service for generating different types of flashcards from knowledge points."""
    
    def __init__(self, config: Optional[CardGenerationConfig] = None):
        """Initialize the card generation service."""
        self.config = config or CardGenerationConfig()
        self.text_segmentation = TextSegmentationService()
        
        # Initialize default configurations
        self._initialize_default_configs()
    
    def _initialize_default_configs(self):
        """Initialize default configuration values."""
        
        # Type-specific difficulty modifiers
        if self.config.type_difficulty_modifiers is None:
            self.config.type_difficulty_modifiers = {
                CardType.QA: 1.0,
                CardType.CLOZE: 1.2,  # Slightly harder
                CardType.IMAGE_HOTSPOT: 1.1
            }
        
        # Question templates for different knowledge types
        if self.config.question_templates is None:
            self.config.question_templates = {
                KnowledgeType.DEFINITION: [
                    "What is {term}?",
                    "Define {term}.",
                    "How would you define {term}?",
                    "What does {term} mean?",
                    "Explain the concept of {term}."
                ],
                KnowledgeType.FACT: [
                    "What is true about {topic}?",
                    "State the fact about {topic}.",
                    "What do we know about {topic}?",
                    "What is the key information regarding {topic}?"
                ],
                KnowledgeType.THEOREM: [
                    "State the {theorem} theorem.",
                    "What does the {theorem} theorem say?",
                    "Explain the {theorem} theorem.",
                    "What is the {theorem} theorem?"
                ],
                KnowledgeType.PROCESS: [
                    "How do you {process}?",
                    "What are the steps to {process}?",
                    "Describe the process of {process}.",
                    "Explain how to {process}."
                ],
                KnowledgeType.EXAMPLE: [
                    "Give an example of {concept}.",
                    "What is an example of {concept}?",
                    "Provide an instance of {concept}.",
                    "Show an example that illustrates {concept}."
                ],
                KnowledgeType.CONCEPT: [
                    "Explain the concept of {concept}.",
                    "What is the {concept} concept?",
                    "Describe {concept}.",
                    "How would you explain {concept}?"
                ]
            }
    
    async def generate_cards_from_knowledge(
        self, 
        knowledge_points: List[Knowledge],
        figures: Optional[List[Figure]] = None
    ) -> List[GeneratedCard]:
        """
        Generate flashcards from knowledge points.
        
        Args:
            knowledge_points: List of knowledge points to generate cards from
            figures: Optional list of figures for image hotspot cards
            
        Returns:
            List of generated cards
        """
        if not knowledge_points:
            return []
        
        all_cards = []
        
        for knowledge in knowledge_points:
            try:
                # Generate Q&A cards for definitions and other types
                qa_cards = await self._generate_qa_cards(knowledge)
                all_cards.extend(qa_cards)
                
                # Generate cloze deletion cards if entities are present
                if knowledge.entities:
                    cloze_cards = await self._generate_cloze_cards(knowledge)
                    all_cards.extend(cloze_cards)
                
            except Exception as e:
                logger.error(f"Error generating cards for knowledge {knowledge.id}: {e}")
                continue
        
        # Generate image hotspot cards if figures are provided
        if figures:
            for figure in figures:
                try:
                    # Find related knowledge points for this figure
                    related_knowledge = self._find_related_knowledge(figure, knowledge_points)
                    if related_knowledge:
                        image_cards = await self._generate_image_hotspot_cards(figure, related_knowledge)
                        all_cards.extend(image_cards)
                except Exception as e:
                    logger.error(f"Error generating image cards for figure {figure.id}: {e}")
                    continue
        
        logger.info(f"Generated {len(all_cards)} cards from {len(knowledge_points)} knowledge points")
        return all_cards
    
    async def _generate_qa_cards(self, knowledge: Knowledge) -> List[GeneratedCard]:
        """Generate Q&A cards from knowledge points."""
        
        cards = []
        
        # Get question templates for this knowledge type
        templates = self.config.question_templates.get(knowledge.kind, [])
        if not templates:
            # Fallback generic templates
            templates = ["What is the key information about this topic?"]
        
        # Extract key terms for question generation
        key_terms = self._extract_key_terms(knowledge)
        
        # Generate questions based on knowledge type
        if knowledge.kind == KnowledgeType.DEFINITION:
            cards.extend(self._generate_definition_qa_cards(knowledge, key_terms, templates))
        elif knowledge.kind == KnowledgeType.FACT:
            cards.extend(self._generate_fact_qa_cards(knowledge, key_terms, templates))
        elif knowledge.kind == KnowledgeType.THEOREM:
            cards.extend(self._generate_theorem_qa_cards(knowledge, key_terms, templates))
        elif knowledge.kind == KnowledgeType.PROCESS:
            cards.extend(self._generate_process_qa_cards(knowledge, key_terms, templates))
        elif knowledge.kind == KnowledgeType.EXAMPLE:
            cards.extend(self._generate_example_qa_cards(knowledge, key_terms, templates))
        else:
            # Generic Q&A card
            cards.extend(self._generate_generic_qa_cards(knowledge, key_terms, templates))
        
        return cards
    
    def _generate_definition_qa_cards(
        self, 
        knowledge: Knowledge, 
        key_terms: List[str], 
        templates: List[str]
    ) -> List[GeneratedCard]:
        """Generate Q&A cards specifically for definitions."""
        
        cards = []
        
        # Try to parse definition structure
        definition_parts = self._parse_definition(knowledge.text)
        
        if definition_parts:
            term, definition = definition_parts
            
            # Generate forward card (term -> definition)
            template = random.choice(templates)
            question = template.format(term=term)
            
            difficulty = self._calculate_card_difficulty(
                knowledge, question + " " + definition, CardType.QA
            )
            
            cards.append(GeneratedCard(
                card_type=CardType.QA,
                front=question,
                back=definition,
                difficulty=difficulty,
                metadata={
                    "term": term,
                    "definition_type": "forward",
                    "knowledge_type": knowledge.kind.value
                },
                knowledge_id=str(knowledge.id),
                source_info={
                    "chapter_id": str(knowledge.chapter_id),
                    "anchors": knowledge.anchors,
                    "entities": knowledge.entities
                }
            ))
            
            # Generate reverse card (definition -> term) for important terms
            if len(term.split()) <= 3 and any(entity.lower() in term.lower() for entity in knowledge.entities):
                reverse_question = f"What term is defined as: {definition}?"
                
                cards.append(GeneratedCard(
                    card_type=CardType.QA,
                    front=reverse_question,
                    back=term,
                    difficulty=difficulty * 1.1,  # Slightly harder
                    metadata={
                        "term": term,
                        "definition_type": "reverse",
                        "knowledge_type": knowledge.kind.value
                    },
                    knowledge_id=str(knowledge.id),
                    source_info={
                        "chapter_id": str(knowledge.chapter_id),
                        "anchors": knowledge.anchors,
                        "entities": knowledge.entities
                    }
                ))
        
        else:
            # Fallback to generic Q&A if definition parsing fails
            cards.extend(self._generate_generic_qa_cards(knowledge, key_terms, templates))
        
        return cards
    
    def _generate_fact_qa_cards(
        self, 
        knowledge: Knowledge, 
        key_terms: List[str], 
        templates: List[str]
    ) -> List[GeneratedCard]:
        """Generate Q&A cards for facts."""
        
        cards = []
        
        # Use the first key term or entity as the topic
        topic = key_terms[0] if key_terms else (knowledge.entities[0] if knowledge.entities else "this topic")
        
        template = random.choice(templates)
        question = template.format(topic=topic)
        
        difficulty = self._calculate_card_difficulty(
            knowledge, question + " " + knowledge.text, CardType.QA
        )
        
        cards.append(GeneratedCard(
            card_type=CardType.QA,
            front=question,
            back=knowledge.text,
            difficulty=difficulty,
            metadata={
                "topic": topic,
                "knowledge_type": knowledge.kind.value
            },
            knowledge_id=str(knowledge.id),
            source_info={
                "chapter_id": str(knowledge.chapter_id),
                "anchors": knowledge.anchors,
                "entities": knowledge.entities
            }
        ))
        
        return cards
    
    def _generate_theorem_qa_cards(
        self, 
        knowledge: Knowledge, 
        key_terms: List[str], 
        templates: List[str]
    ) -> List[GeneratedCard]:
        """Generate Q&A cards for theorems."""
        
        cards = []
        
        # Extract theorem name if possible
        theorem_name = self._extract_theorem_name(knowledge.text)
        if not theorem_name and key_terms:
            theorem_name = key_terms[0]
        
        template = random.choice(templates)
        question = template.format(theorem=theorem_name or "this")
        
        difficulty = self._calculate_card_difficulty(
            knowledge, question + " " + knowledge.text, CardType.QA
        )
        
        cards.append(GeneratedCard(
            card_type=CardType.QA,
            front=question,
            back=knowledge.text,
            difficulty=difficulty * 1.2,  # Theorems are typically harder
            metadata={
                "theorem_name": theorem_name,
                "knowledge_type": knowledge.kind.value
            },
            knowledge_id=str(knowledge.id),
            source_info={
                "chapter_id": str(knowledge.chapter_id),
                "anchors": knowledge.anchors,
                "entities": knowledge.entities
            }
        ))
        
        return cards
    
    def _generate_process_qa_cards(
        self, 
        knowledge: Knowledge, 
        key_terms: List[str], 
        templates: List[str]
    ) -> List[GeneratedCard]:
        """Generate Q&A cards for processes."""
        
        cards = []
        
        # Extract process name
        process_name = key_terms[0] if key_terms else "this process"
        
        template = random.choice(templates)
        question = template.format(process=process_name)
        
        difficulty = self._calculate_card_difficulty(
            knowledge, question + " " + knowledge.text, CardType.QA
        )
        
        cards.append(GeneratedCard(
            card_type=CardType.QA,
            front=question,
            back=knowledge.text,
            difficulty=difficulty,
            metadata={
                "process_name": process_name,
                "knowledge_type": knowledge.kind.value
            },
            knowledge_id=str(knowledge.id),
            source_info={
                "chapter_id": str(knowledge.chapter_id),
                "anchors": knowledge.anchors,
                "entities": knowledge.entities
            }
        ))
        
        return cards
    
    def _generate_example_qa_cards(
        self, 
        knowledge: Knowledge, 
        key_terms: List[str], 
        templates: List[str]
    ) -> List[GeneratedCard]:
        """Generate Q&A cards for examples."""
        
        cards = []
        
        # Use the concept being exemplified
        concept = key_terms[0] if key_terms else "this concept"
        
        template = random.choice(templates)
        question = template.format(concept=concept)
        
        difficulty = self._calculate_card_difficulty(
            knowledge, question + " " + knowledge.text, CardType.QA
        )
        
        cards.append(GeneratedCard(
            card_type=CardType.QA,
            front=question,
            back=knowledge.text,
            difficulty=difficulty * 0.9,  # Examples are typically easier
            metadata={
                "concept": concept,
                "knowledge_type": knowledge.kind.value
            },
            knowledge_id=str(knowledge.id),
            source_info={
                "chapter_id": str(knowledge.chapter_id),
                "anchors": knowledge.anchors,
                "entities": knowledge.entities
            }
        ))
        
        return cards
    
    def _generate_generic_qa_cards(
        self, 
        knowledge: Knowledge, 
        key_terms: List[str], 
        templates: List[str]
    ) -> List[GeneratedCard]:
        """Generate generic Q&A cards."""
        
        cards = []
        
        # Use a generic question
        question = "What is the key information about this topic?"
        if key_terms:
            question = f"What do you know about {key_terms[0]}?"
        
        difficulty = self._calculate_card_difficulty(
            knowledge, question + " " + knowledge.text, CardType.QA
        )
        
        cards.append(GeneratedCard(
            card_type=CardType.QA,
            front=question,
            back=knowledge.text,
            difficulty=difficulty,
            metadata={
                "knowledge_type": knowledge.kind.value,
                "generic": True
            },
            knowledge_id=str(knowledge.id),
            source_info={
                "chapter_id": str(knowledge.chapter_id),
                "anchors": knowledge.anchors,
                "entities": knowledge.entities
            }
        ))
        
        return cards
    
    async def _generate_cloze_cards(self, knowledge: Knowledge) -> List[GeneratedCard]:
        """Generate cloze deletion cards with entity blanking."""
        
        cards = []
        
        if not knowledge.entities:
            return cards
        
        # Select entities to blank out (max 2-3)
        entities_to_blank = self._select_entities_for_cloze(knowledge.entities, knowledge.text)
        
        if not entities_to_blank:
            return cards
        
        # Create cloze text with blanks
        cloze_text, blanked_entities = self._create_cloze_text(knowledge.text, entities_to_blank)
        
        if not blanked_entities:
            return cards
        
        # Create the answer text
        answer_text = knowledge.text
        
        difficulty = self._calculate_card_difficulty(
            knowledge, cloze_text + " " + answer_text, CardType.CLOZE
        )
        
        cards.append(GeneratedCard(
            card_type=CardType.CLOZE,
            front=cloze_text,
            back=answer_text,
            difficulty=difficulty,
            metadata={
                "blanked_entities": blanked_entities,
                "blank_count": len(blanked_entities),
                "knowledge_type": knowledge.kind.value
            },
            knowledge_id=str(knowledge.id),
            source_info={
                "chapter_id": str(knowledge.chapter_id),
                "anchors": knowledge.anchors,
                "entities": knowledge.entities
            }
        ))
        
        return cards
    
    async def _generate_image_hotspot_cards(
        self, 
        figure: Figure, 
        related_knowledge: List[Knowledge]
    ) -> List[GeneratedCard]:
        """Generate image hotspot cards with clickable regions."""
        
        cards = []
        
        if not figure.image_path or not related_knowledge:
            return cards
        
        # Generate hotspots based on related knowledge
        hotspots = self._generate_hotspots_from_knowledge(figure, related_knowledge)
        
        if not hotspots:
            return cards
        
        # Create the card
        question = f"Click on the regions in this image that relate to the concepts discussed."
        if figure.caption:
            question = f"Based on the caption '{figure.caption}', click on the relevant regions in this image."
        
        # Calculate difficulty based on number of hotspots and complexity
        base_difficulty = len(hotspots) * 0.2 + 1.0
        complexity_factor = sum(len(kp.text) for kp in related_knowledge) / (len(related_knowledge) * 100)
        difficulty = min(5.0, base_difficulty + complexity_factor)
        
        cards.append(GeneratedCard(
            card_type=CardType.IMAGE_HOTSPOT,
            front=figure.image_path,
            back=figure.caption or "Image with interactive hotspots",
            difficulty=difficulty,
            metadata={
                "question": question,
                "hotspots": [self._hotspot_to_dict(h) for h in hotspots],
                "figure_id": str(figure.id),
                "related_knowledge_ids": [str(kp.id) for kp in related_knowledge]
            },
            knowledge_id=str(related_knowledge[0].id),  # Use first related knowledge as primary
            source_info={
                "chapter_id": str(figure.chapter_id),
                "figure_bbox": figure.bbox,
                "page_number": figure.page_number
            }
        ))
        
        return cards
    
    def _extract_key_terms(self, knowledge: Knowledge) -> List[str]:
        """Extract key terms from knowledge text and entities."""
        
        key_terms = []
        
        # Start with entities
        if knowledge.entities:
            key_terms.extend(knowledge.entities[:3])  # Top 3 entities
        
        # Extract additional terms from text
        text_terms = self._extract_terms_from_text(knowledge.text)
        
        # Add unique terms not already in entities
        for term in text_terms:
            if term not in key_terms and len(key_terms) < 5:
                key_terms.append(term)
        
        return key_terms
    
    def _extract_terms_from_text(self, text: str) -> List[str]:
        """Extract important terms from text using simple heuristics."""
        
        # Look for capitalized words (proper nouns)
        capitalized_words = re.findall(r'\b[A-Z][a-z]+\b', text)
        
        # Look for quoted terms
        quoted_terms = re.findall(r'"([^"]+)"', text) + re.findall(r"'([^']+)'", text)
        
        # Look for terms in parentheses
        parenthetical_terms = re.findall(r'\(([^)]+)\)', text)
        
        # Combine and filter
        all_terms = capitalized_words + quoted_terms + parenthetical_terms
        
        # Filter out very short or very long terms
        filtered_terms = [
            term.strip() for term in all_terms 
            if 2 <= len(term.strip()) <= 30 and term.strip().replace(' ', '').isalnum()
        ]
        
        return list(set(filtered_terms))[:5]  # Return unique terms, max 5
    
    def _parse_definition(self, text: str) -> Optional[Tuple[str, str]]:
        """Parse definition text to extract term and definition."""
        
        # Common definition patterns
        patterns = [
            r'^(.+?)\s+(?:is|are|means?|refers?\s+to|defined?\s+as|can\s+be\s+defined\s+as)\s+(.+)$',
            r'^(.+?)[:：]\s*(.+)$',
            r'^(?:Definition|定义)[:：]?\s*(.+?)\s+(?:is|are|means?)\s+(.+)$',
            r'^(.+?)\s+(?:—|–|-)\s+(.+)$',
        ]
        
        for pattern in patterns:
            match = re.match(pattern, text.strip(), re.IGNORECASE | re.MULTILINE)
            if match:
                term = match.group(1).strip()
                definition = match.group(2).strip()
                
                # Validate the parsed result
                if 2 <= len(term) <= 50 and len(definition) >= 10:
                    return term, definition
        
        return None
    
    def _extract_theorem_name(self, text: str) -> Optional[str]:
        """Extract theorem name from theorem text."""
        
        # Look for theorem name patterns
        patterns = [
            r'(?:Theorem|定理|Lemma|Corollary|Proposition)\s*[:：]?\s*([^.]+)',
            r'([^.]+?)\s+(?:theorem|定理|lemma|corollary|proposition)',
            r'The\s+([^.]+?)\s+(?:theorem|定理|lemma|corollary|proposition)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                name = match.group(1).strip()
                if 2 <= len(name) <= 50:
                    return name
        
        return None
    
    def _select_entities_for_cloze(self, entities: List[str], text: str) -> List[str]:
        """Select the best entities to blank out for cloze cards."""
        
        if not entities:
            return []
        
        # Score entities based on various factors
        entity_scores = []
        
        for entity in entities:
            score = 0.0
            
            # Length factor (prefer medium-length entities)
            length = len(entity)
            if 3 <= length <= 15:
                score += 1.0
            elif length <= 2:
                score -= 0.5
            elif length > 20:
                score -= 0.3
            
            # Frequency factor (prefer entities that appear once or twice)
            frequency = text.lower().count(entity.lower())
            if frequency == 1:
                score += 1.0
            elif frequency == 2:
                score += 0.5
            elif frequency > 3:
                score -= 0.3
            
            # Position factor (prefer entities not at the very beginning)
            first_occurrence = text.lower().find(entity.lower())
            if first_occurrence > len(text) * 0.1:  # Not in first 10%
                score += 0.3
            
            # Word count factor (prefer single words or short phrases)
            word_count = len(entity.split())
            if word_count == 1:
                score += 0.5
            elif word_count == 2:
                score += 0.3
            elif word_count > 3:
                score -= 0.2
            
            entity_scores.append((entity, score))
        
        # Sort by score and select top entities
        entity_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Select 1-3 entities based on configuration
        max_blanks = min(self.config.max_cloze_blanks, len(entities))
        min_blanks = min(self.config.min_cloze_blanks, max_blanks)
        
        # Ensure we have at least min_blanks entities with positive scores
        positive_score_entities = [e for e, s in entity_scores if s > 0]
        if len(positive_score_entities) < min_blanks:
            # Include some lower-scored entities if needed
            selected_count = min(max_blanks, len(entities))
        else:
            selected_count = min(max_blanks, len(positive_score_entities))
        
        selected_entities = [entity for entity, _ in entity_scores[:selected_count]]
        
        return selected_entities
    
    def _create_cloze_text(self, text: str, entities_to_blank: List[str]) -> Tuple[str, List[str]]:
        """Create cloze text by replacing entities with blanks."""
        
        if not entities_to_blank:
            return text, []
        
        cloze_text = text
        blanked_entities = []
        
        # Sort entities by length (longest first) to avoid partial replacements
        sorted_entities = sorted(entities_to_blank, key=len, reverse=True)
        
        blank_counter = 1
        for entity in sorted_entities:
            # Find all occurrences of the entity (case-insensitive)
            pattern = re.compile(re.escape(entity), re.IGNORECASE)
            matches = list(pattern.finditer(cloze_text))
            
            if matches:
                # Replace only the first occurrence to avoid over-blanking
                match = matches[0]
                blank_placeholder = f"[{blank_counter}]"
                
                cloze_text = (
                    cloze_text[:match.start()] + 
                    blank_placeholder + 
                    cloze_text[match.end():]
                )
                
                blanked_entities.append({
                    "entity": entity,
                    "blank_number": blank_counter,
                    "original_position": match.start()
                })
                
                blank_counter += 1
        
        return cloze_text, blanked_entities
    
    def _find_related_knowledge(self, figure: Figure, knowledge_points: List[Knowledge]) -> List[Knowledge]:
        """Find knowledge points related to a figure."""
        
        related = []
        
        if not figure.caption:
            return related
        
        caption_lower = figure.caption.lower()
        
        for knowledge in knowledge_points:
            # Check if knowledge is from the same chapter
            if str(knowledge.chapter_id) != str(figure.chapter_id):
                continue
            
            # Check for entity overlap
            entity_overlap = any(
                entity.lower() in caption_lower or entity.lower() in knowledge.text.lower()
                for entity in knowledge.entities
            )
            
            # Check for text similarity
            text_similarity = self._calculate_text_similarity(caption_lower, knowledge.text.lower())
            
            if entity_overlap or text_similarity > 0.3:
                related.append(knowledge)
        
        # Limit to most relevant knowledge points
        return related[:3]
    
    def _generate_hotspots_from_knowledge(
        self, 
        figure: Figure, 
        related_knowledge: List[Knowledge]
    ) -> List[ImageHotspot]:
        """Generate hotspots based on related knowledge."""
        
        hotspots = []
        
        # For now, generate simple hotspots based on the number of related knowledge points
        # In a real implementation, this would use image analysis or predefined regions
        
        if not figure.bbox:
            # Default image dimensions if bbox not available
            image_width, image_height = 400, 300
        else:
            image_width = figure.bbox.get('width', 400)
            image_height = figure.bbox.get('height', 300)
        
        # Generate hotspots in different regions of the image
        regions = [
            {"name": "top-left", "x": 0.1, "y": 0.1},
            {"name": "top-right", "x": 0.7, "y": 0.1},
            {"name": "center", "x": 0.4, "y": 0.4},
            {"name": "bottom-left", "x": 0.1, "y": 0.7},
            {"name": "bottom-right", "x": 0.7, "y": 0.7},
        ]
        
        for i, knowledge in enumerate(related_knowledge[:self.config.max_hotspots_per_image]):
            if i >= len(regions):
                break
            
            region = regions[i]
            
            # Calculate hotspot position and size
            hotspot_size = max(self.config.min_hotspot_size, min(80, len(knowledge.text) // 5))
            x = int(region["x"] * image_width)
            y = int(region["y"] * image_height)
            
            # Ensure hotspot stays within image bounds
            x = max(0, min(x, image_width - hotspot_size))
            y = max(0, min(y, image_height - hotspot_size))
            
            # Create hotspot
            hotspot = ImageHotspot(
                x=x,
                y=y,
                width=hotspot_size,
                height=hotspot_size,
                label=f"Concept {i+1}",
                description=knowledge.text[:100] + "..." if len(knowledge.text) > 100 else knowledge.text,
                correct=True  # All generated hotspots are correct for now
            )
            
            hotspots.append(hotspot)
        
        return hotspots
    
    def _hotspot_to_dict(self, hotspot: ImageHotspot) -> Dict[str, Any]:
        """Convert hotspot to dictionary for JSON serialization."""
        
        return {
            "x": hotspot.x,
            "y": hotspot.y,
            "width": hotspot.width,
            "height": hotspot.height,
            "label": hotspot.label,
            "description": hotspot.description,
            "correct": hotspot.correct
        }
    
    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two texts using word overlap."""
        
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 and not words2:
            return 1.0
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union)
    
    def _calculate_card_difficulty(
        self, 
        knowledge: Knowledge, 
        card_text: str, 
        card_type: CardType
    ) -> float:
        """Calculate difficulty score for a card based on multiple factors."""
        
        # Base difficulty
        difficulty = self.config.base_difficulty
        
        # Text complexity factor
        complexity = self.text_segmentation.calculate_text_complexity(card_text)
        difficulty += complexity * self.config.complexity_weight
        
        # Entity density factor (more entities = harder)
        if knowledge.entities:
            entity_density = len(knowledge.entities) / max(1, len(card_text.split()) / 10)
            difficulty += min(1.0, entity_density) * self.config.entity_density_weight
        
        # Length factor (longer text = slightly harder)
        length_factor = min(1.0, len(card_text) / 200.0)
        difficulty += length_factor * self.config.length_weight
        
        # Knowledge type factor
        type_factors = {
            KnowledgeType.DEFINITION: 0.0,    # Baseline
            KnowledgeType.FACT: 0.1,          # Slightly harder
            KnowledgeType.THEOREM: 0.4,       # Much harder
            KnowledgeType.PROCESS: 0.2,       # Moderately harder
            KnowledgeType.EXAMPLE: -0.1,      # Slightly easier
            KnowledgeType.CONCEPT: 0.1,       # Slightly harder
        }
        
        type_factor = type_factors.get(knowledge.kind, 0.0)
        difficulty += type_factor * self.config.type_weight
        
        # Card type modifier
        card_type_modifier = self.config.type_difficulty_modifiers.get(card_type, 1.0)
        difficulty *= card_type_modifier
        
        # Confidence factor (lower confidence = higher difficulty)
        if hasattr(knowledge, 'confidence_score') and knowledge.confidence_score:
            confidence_factor = 1.0 - (knowledge.confidence_score - 0.5)  # Invert confidence
            difficulty += max(0.0, confidence_factor) * 0.2
        
        # Ensure difficulty is within reasonable bounds (0.5 to 5.0)
        difficulty = max(0.5, min(5.0, difficulty))
        
        return round(difficulty, 2)
    
    async def save_generated_cards(self, generated_cards: List[GeneratedCard]) -> List[Card]:
        """Save generated cards to the database."""
        
        if not generated_cards:
            return []
        
        saved_cards = []
        
        async with get_async_session() as session:
            for gen_card in generated_cards:
                try:
                    # Create Card model instance
                    card = Card(
                        knowledge_id=gen_card.knowledge_id,
                        card_type=gen_card.card_type,
                        front=gen_card.front,
                        back=gen_card.back,
                        difficulty=gen_card.difficulty,
                        card_metadata=gen_card.metadata
                    )
                    
                    session.add(card)
                    saved_cards.append(card)
                    
                except Exception as e:
                    logger.error(f"Error saving generated card: {e}")
                    continue
            
            try:
                await session.commit()
                logger.info(f"Saved {len(saved_cards)} generated cards to database")
            except Exception as e:
                logger.error(f"Error committing generated cards: {e}")
                await session.rollback()
                saved_cards = []
        
        return saved_cards
    
    async def generate_and_save_cards(
        self, 
        knowledge_points: List[Knowledge],
        figures: Optional[List[Figure]] = None
    ) -> List[Card]:
        """
        Complete pipeline: generate cards from knowledge points and save to database.
        
        Args:
            knowledge_points: List of knowledge points to generate cards from
            figures: Optional list of figures for image hotspot cards
            
        Returns:
            List of saved Card model instances
        """
        
        # Generate cards
        generated_cards = await self.generate_cards_from_knowledge(knowledge_points, figures)
        
        if not generated_cards:
            logger.info("No cards generated from knowledge points")
            return []
        
        # Save to database
        saved_cards = await self.save_generated_cards(generated_cards)
        
        logger.info(
            f"Card generation complete: "
            f"{len(generated_cards)} generated, {len(saved_cards)} saved"
        )
        
        return saved_cards
    
    def get_generation_statistics(
        self, 
        generated_cards: List[GeneratedCard]
    ) -> Dict[str, Any]:
        """Get statistics about generated cards."""
        
        if not generated_cards:
            return {
                "total_cards": 0,
                "by_type": {},
                "avg_difficulty": 0.0,
                "difficulty_distribution": {}
            }
        
        # Count by type
        type_counts = {}
        for card in generated_cards:
            type_counts[card.card_type.value] = type_counts.get(card.card_type.value, 0) + 1
        
        # Calculate average difficulty
        avg_difficulty = sum(card.difficulty for card in generated_cards) / len(generated_cards)
        
        # Difficulty distribution
        difficulty_ranges = {
            "easy (0.5-1.5)": 0,
            "medium (1.5-2.5)": 0,
            "hard (2.5-3.5)": 0,
            "very_hard (3.5+)": 0
        }
        
        for card in generated_cards:
            if card.difficulty <= 1.5:
                difficulty_ranges["easy (0.5-1.5)"] += 1
            elif card.difficulty <= 2.5:
                difficulty_ranges["medium (1.5-2.5)"] += 1
            elif card.difficulty <= 3.5:
                difficulty_ranges["hard (2.5-3.5)"] += 1
            else:
                difficulty_ranges["very_hard (3.5+)"] += 1
        
        return {
            "total_cards": len(generated_cards),
            "by_type": type_counts,
            "avg_difficulty": round(avg_difficulty, 2),
            "difficulty_distribution": difficulty_ranges,
            "highest_difficulty": max(generated_cards, key=lambda x: x.difficulty).difficulty,
            "lowest_difficulty": min(generated_cards, key=lambda x: x.difficulty).difficulty
        }    

    async def generate_and_deduplicate_cards(
        self,
        knowledge_points: List[Knowledge],
        figures: Optional[List[Figure]] = None,
        enable_deduplication: bool = True,
        dedup_config: Optional[DeduplicationConfig] = None
    ) -> Tuple[List[GeneratedCard], Dict[str, Any]]:
        """
        Generate flashcards from knowledge points and perform deduplication.
        
        Args:
            knowledge_points: List of knowledge points to generate cards from
            figures: Optional list of figures for image hotspot cards
            enable_deduplication: Whether to perform deduplication
            dedup_config: Optional deduplication configuration
            
        Returns:
            Tuple of (deduplicated_cards, deduplication_stats)
        """
        # Generate cards first
        generated_cards = await self.generate_cards_from_knowledge(knowledge_points, figures)
        
        if not enable_deduplication or not generated_cards:
            return generated_cards, {
                "deduplication_enabled": False,
                "total_cards": len(generated_cards),
                "duplicates_removed": 0,
                "duplicate_rate": 0.0
            }
        
        # Convert GeneratedCard objects to Card models for deduplication
        cards_for_dedup = []
        for gen_card in generated_cards:
            card = Card(
                id=None,  # Will be set when saved to database
                knowledge_id=gen_card.knowledge_id,
                card_type=gen_card.card_type,
                front=gen_card.front,
                back=gen_card.back,
                difficulty=gen_card.difficulty,
                card_metadata=gen_card.metadata
            )
            cards_for_dedup.append(card)
        
        # Perform deduplication
        dedup_service = DeduplicationService(dedup_config)
        
        # Mock database session for deduplication
        class MockDB:
            def add(self, obj):
                pass
            def commit(self):
                pass
        
        mock_db = MockDB()
        deduplicated_cards, dedup_stats = await dedup_service.deduplicate_cards(
            mock_db, cards_for_dedup
        )
        
        # Convert back to GeneratedCard objects
        final_generated_cards = []
        for card in deduplicated_cards:
            # Find the original GeneratedCard to preserve source_info
            original_gen_card = None
            for gen_card in generated_cards:
                if (gen_card.card_type == card.card_type and 
                    gen_card.front == card.front and 
                    gen_card.back == card.back):
                    original_gen_card = gen_card
                    break
            
            if original_gen_card:
                # Update metadata with deduplication info if available
                updated_metadata = dict(original_gen_card.metadata)
                if card.card_metadata:
                    updated_metadata.update(card.card_metadata)
                
                final_gen_card = GeneratedCard(
                    card_type=card.card_type,
                    front=card.front,
                    back=card.back,
                    difficulty=card.difficulty,
                    metadata=updated_metadata,
                    knowledge_id=original_gen_card.knowledge_id,
                    source_info=original_gen_card.source_info
                )
                final_generated_cards.append(final_gen_card)
        
        # Update deduplication stats
        dedup_stats["deduplication_enabled"] = True
        
        logger.info(f"Card generation with deduplication complete: "
                   f"{len(generated_cards)} -> {len(final_generated_cards)} cards "
                   f"({dedup_stats['duplicate_rate']:.1%} duplicates removed)")
        
        return final_generated_cards, dedup_stats
    
    async def save_cards_to_database(
        self,
        db_session,
        generated_cards: List[GeneratedCard]
    ) -> List[Card]:
        """
        Save generated cards to the database.
        
        Args:
            db_session: Database session
            generated_cards: List of generated cards to save
            
        Returns:
            List of saved Card models
        """
        saved_cards = []
        
        for gen_card in generated_cards:
            try:
                card = Card(
                    knowledge_id=gen_card.knowledge_id,
                    card_type=gen_card.card_type,
                    front=gen_card.front,
                    back=gen_card.back,
                    difficulty=gen_card.difficulty,
                    card_metadata=gen_card.metadata
                )
                
                db_session.add(card)
                saved_cards.append(card)
                
            except Exception as e:
                logger.error(f"Error saving card to database: {e}")
                continue
        
        try:
            db_session.commit()
            logger.info(f"Saved {len(saved_cards)} cards to database")
        except Exception as e:
            logger.error(f"Error committing cards to database: {e}")
            db_session.rollback()
            return []
        
        return saved_cards