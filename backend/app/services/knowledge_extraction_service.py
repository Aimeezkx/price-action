"""
Knowledge point extraction service for identifying and classifying learning content.
"""

import json
import re
import asyncio
from dataclasses import dataclass
from typing import Dict, List, Optional, Union, Any
from enum import Enum
import logging

from ..models.knowledge import Knowledge, KnowledgeType
from ..services.text_segmentation_service import TextSegment, TextSegmentationService
from ..services.entity_extraction_service import EntityExtractionService, Entity
from ..core.database import get_async_session

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class KnowledgeExtractionConfig:
    """Configuration for knowledge extraction."""
    
    # LLM settings
    use_llm: bool = True
    llm_model: str = "gpt-3.5-turbo"
    llm_temperature: float = 0.1
    llm_max_tokens: int = 1000
    llm_timeout: int = 30
    
    # Fallback settings
    enable_fallback: bool = True
    fallback_confidence: float = 0.6
    
    # Classification settings
    min_confidence: float = 0.5
    max_knowledge_points_per_segment: int = 3
    
    # Rule-based extraction patterns
    definition_patterns: List[str] = None
    fact_patterns: List[str] = None
    theorem_patterns: List[str] = None
    process_patterns: List[str] = None
    example_patterns: List[str] = None


@dataclass
class ExtractedKnowledge:
    """Represents an extracted knowledge point before database storage."""
    
    text: str
    kind: KnowledgeType
    entities: List[str]
    confidence: float
    anchors: Dict[str, Any]
    context: str = ""
    source_segment: Optional[TextSegment] = None


class KnowledgeExtractionService:
    """Service for extracting and classifying knowledge points from text segments."""
    
    def __init__(self, config: Optional[KnowledgeExtractionConfig] = None):
        """Initialize the knowledge extraction service."""
        self.config = config or KnowledgeExtractionConfig()
        self.text_segmentation = TextSegmentationService()
        self.entity_extraction = EntityExtractionService()
        
        # Initialize rule-based patterns
        self._load_extraction_patterns()
        
        # LLM client (placeholder - would be initialized with actual LLM client)
        self.llm_client = None
        self._initialize_llm_client()
    
    def _initialize_llm_client(self):
        """Initialize LLM client if available."""
        # Placeholder for LLM client initialization
        # In a real implementation, this would initialize OpenAI, Anthropic, or local LLM client
        try:
            # Example: self.llm_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            self.llm_client = None  # Disabled for now
            logger.info("LLM client initialized successfully")
        except Exception as e:
            logger.warning(f"Failed to initialize LLM client: {e}")
            self.llm_client = None
    
    def _load_extraction_patterns(self):
        """Load regex patterns for rule-based knowledge extraction."""
        
        # Definition patterns
        self.definition_patterns = [
            r'(.+?)\s+(?:is|are|means?|refers?\s+to|defined?\s+as|can\s+be\s+defined\s+as)\s+(.+?)(?:\.|$)',
            r'(.+?)[:：]\s*(.+?)(?:\.|$)',
            r'(?:Definition|定义)[:：]?\s*(.+?)(?:\.|$)',
            r'(.+?)\s+(?:—|–|-)\s+(.+?)(?:\.|$)',
        ]
        
        # Fact patterns
        self.fact_patterns = [
            r'(?:It\s+is\s+(?:a\s+)?fact\s+that|The\s+fact\s+is\s+that|Fact[:：])\s*(.+?)(?:\.|$)',
            r'(?:Research\s+shows?|Studies\s+show|Evidence\s+suggests?)\s+(?:that\s+)?(.+?)(?:\.|$)',
            r'(?:According\s+to|Based\s+on)\s+.+?,\s*(.+?)(?:\.|$)',
            r'(?:Statistics\s+show|Data\s+indicates?)\s+(?:that\s+)?(.+?)(?:\.|$)',
        ]
        
        # Theorem patterns
        self.theorem_patterns = [
            r'(?:Theorem|定理|Lemma|Corollary|Proposition)[:：]?\s*(.+?)(?:\.|$)',
            r'(.+?)\s+(?:theorem|定理|lemma|corollary|proposition)\s*[:：]?\s*(.+?)(?:\.|$)',
            r'(?:If|Given\s+that)\s+(.+?),?\s+then\s+(.+?)(?:\.|$)',
        ]
        
        # Process patterns
        self.process_patterns = [
            r'(?:Step\s+\d+|First|Second|Third|Next|Then|Finally)[:：]?\s*(.+?)(?:\.|$)',
            r'(?:Process|Procedure|Method|Algorithm)[:：]?\s*(.+?)(?:\.|$)',
            r'(?:To\s+\w+|In\s+order\s+to)\s+(.+?),\s*(.+?)(?:\.|$)',
            r'(?:The\s+steps?\s+(?:are|is)|Follow\s+these\s+steps?)\s*[:：]?\s*(.+?)(?:\.|$)',
        ]
        
        # Example patterns
        self.example_patterns = [
            r'(?:For\s+example|Example|Instance|Such\s+as)[:：]?\s*(.+?)(?:\.|$)',
            r'(?:Consider|Take)\s+(.+?)(?:\.|$)',
            r'(?:A\s+typical\s+example|An\s+example)\s+(?:is|of)\s+(.+?)(?:\.|$)',
            r'(?:例如|比如|举例)[:：]?\s*(.+?)(?:\.|$)',
        ]
        
        # Compile patterns
        self.compiled_patterns = {
            KnowledgeType.DEFINITION: [re.compile(p, re.IGNORECASE | re.MULTILINE) for p in self.definition_patterns],
            KnowledgeType.FACT: [re.compile(p, re.IGNORECASE | re.MULTILINE) for p in self.fact_patterns],
            KnowledgeType.THEOREM: [re.compile(p, re.IGNORECASE | re.MULTILINE) for p in self.theorem_patterns],
            KnowledgeType.PROCESS: [re.compile(p, re.IGNORECASE | re.MULTILINE) for p in self.process_patterns],
            KnowledgeType.EXAMPLE: [re.compile(p, re.IGNORECASE | re.MULTILINE) for p in self.example_patterns],
        }
    
    async def extract_knowledge_from_segments(
        self, 
        segments: List[TextSegment], 
        chapter_id: str
    ) -> List[ExtractedKnowledge]:
        """
        Extract knowledge points from text segments.
        
        Args:
            segments: List of text segments to process
            chapter_id: ID of the chapter these segments belong to
            
        Returns:
            List of extracted knowledge points
        """
        if not segments:
            return []
        
        all_knowledge = []
        
        for segment in segments:
            try:
                # Extract entities from the segment first
                entities = await self.entity_extraction.extract_entities(segment.text)
                entity_texts = [entity.text for entity in entities]
                
                # Try LLM extraction first if enabled
                knowledge_points = []
                if self.config.use_llm and self.llm_client:
                    try:
                        knowledge_points = await self._extract_with_llm(segment, entity_texts, chapter_id)
                    except Exception as e:
                        logger.warning(f"LLM extraction failed for segment: {e}")
                        knowledge_points = []
                
                # Fall back to rule-based extraction if LLM failed or is disabled
                if not knowledge_points and self.config.enable_fallback:
                    knowledge_points = await self._extract_with_rules(segment, entity_texts, chapter_id)
                
                # Filter by confidence and add to results
                for kp in knowledge_points:
                    if kp.confidence >= self.config.min_confidence:
                        all_knowledge.append(kp)
                
            except Exception as e:
                logger.error(f"Error extracting knowledge from segment: {e}")
                continue
        
        return all_knowledge
    
    async def _extract_with_llm(
        self, 
        segment: TextSegment, 
        entities: List[str], 
        chapter_id: str
    ) -> List[ExtractedKnowledge]:
        """Extract knowledge using LLM with structured output."""
        
        # Define JSON schema for LLM output validation
        schema = {
            "type": "object",
            "properties": {
                "knowledge_points": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "text": {"type": "string"},
                            "type": {
                                "type": "string",
                                "enum": ["definition", "fact", "theorem", "process", "example", "concept"]
                            },
                            "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                            "key_entities": {
                                "type": "array",
                                "items": {"type": "string"}
                            },
                            "explanation": {"type": "string"}
                        },
                        "required": ["text", "type", "confidence"]
                    }
                }
            },
            "required": ["knowledge_points"]
        }
        
        # Create prompt for LLM
        prompt = self._create_llm_prompt(segment.text, entities)
        
        try:
            # Make LLM request (placeholder implementation)
            response = await self._call_llm(prompt, schema)
            
            # Parse and validate response
            knowledge_points = []
            if response and "knowledge_points" in response:
                for kp_data in response["knowledge_points"]:
                    try:
                        knowledge_type = KnowledgeType(kp_data["type"])
                        
                        # Create anchors with segment information
                        anchors = segment.anchors.copy()
                        anchors["extraction_method"] = "llm"
                        anchors["chapter_id"] = chapter_id
                        
                        knowledge_points.append(ExtractedKnowledge(
                            text=kp_data["text"],
                            kind=knowledge_type,
                            entities=kp_data.get("key_entities", entities),
                            confidence=kp_data["confidence"],
                            anchors=anchors,
                            context=kp_data.get("explanation", ""),
                            source_segment=segment
                        ))
                    except (ValueError, KeyError) as e:
                        logger.warning(f"Invalid knowledge point data from LLM: {e}")
                        continue
            
            return knowledge_points
            
        except Exception as e:
            logger.error(f"LLM extraction failed: {e}")
            raise
    
    def _create_llm_prompt(self, text: str, entities: List[str]) -> str:
        """Create a prompt for LLM knowledge extraction."""
        
        entities_str = ", ".join(entities[:10]) if entities else "None identified"
        
        prompt = f"""
Analyze the following text and extract key knowledge points. Classify each knowledge point as one of:
- definition: Explanations of what something is or means
- fact: Statements of truth or verified information
- theorem: Mathematical or logical propositions with proofs
- process: Step-by-step procedures or methods
- example: Illustrations or instances of concepts
- concept: General ideas or abstract notions

Text to analyze:
{text}

Key entities identified: {entities_str}

For each knowledge point, provide:
1. The exact text containing the knowledge
2. The classification type
3. A confidence score (0.0 to 1.0)
4. Key entities mentioned in this knowledge point
5. A brief explanation of why this is important

Return your response as JSON following this schema:
{{
    "knowledge_points": [
        {{
            "text": "extracted knowledge text",
            "type": "definition|fact|theorem|process|example|concept",
            "confidence": 0.8,
            "key_entities": ["entity1", "entity2"],
            "explanation": "why this is a key knowledge point"
        }}
    ]
}}

Extract at most {self.config.max_knowledge_points_per_segment} knowledge points.
"""
        return prompt
    
    async def _call_llm(self, prompt: str, schema: Dict) -> Optional[Dict]:
        """Make a call to the LLM service."""
        # Placeholder implementation - would integrate with actual LLM service
        # For now, return None to trigger fallback to rule-based extraction
        return None
    
    async def _extract_with_rules(
        self, 
        segment: TextSegment, 
        entities: List[str], 
        chapter_id: str
    ) -> List[ExtractedKnowledge]:
        """Extract knowledge using rule-based pattern matching."""
        
        knowledge_points = []
        text = segment.text
        
        # Try each knowledge type pattern
        for knowledge_type, patterns in self.compiled_patterns.items():
            for pattern in patterns:
                matches = pattern.finditer(text)
                
                for match in matches:
                    # Extract the knowledge text
                    if match.groups():
                        # Use the captured groups
                        knowledge_text = " ".join(group.strip() for group in match.groups() if group)
                    else:
                        # Use the full match
                        knowledge_text = match.group().strip()
                    
                    if len(knowledge_text) < 10:  # Skip very short matches
                        continue
                    
                    # Calculate confidence based on pattern strength and context
                    confidence = self._calculate_rule_confidence(knowledge_type, match, text)
                    
                    if confidence >= self.config.min_confidence:
                        # Create anchors with segment information
                        anchors = segment.anchors.copy()
                        anchors["extraction_method"] = "rule_based"
                        anchors["chapter_id"] = chapter_id
                        anchors["pattern_match"] = {
                            "start": match.start(),
                            "end": match.end(),
                            "pattern_type": knowledge_type.value
                        }
                        
                        # Filter entities that appear in this knowledge text
                        relevant_entities = [
                            entity for entity in entities 
                            if entity.lower() in knowledge_text.lower()
                        ]
                        
                        knowledge_points.append(ExtractedKnowledge(
                            text=knowledge_text,
                            kind=knowledge_type,
                            entities=relevant_entities,
                            confidence=confidence,
                            anchors=anchors,
                            context=f"Extracted using {knowledge_type.value} pattern",
                            source_segment=segment
                        ))
        
        # Remove duplicates and limit results
        knowledge_points = self._deduplicate_knowledge_points(knowledge_points)
        return knowledge_points[:self.config.max_knowledge_points_per_segment]
    
    def _calculate_rule_confidence(
        self, 
        knowledge_type: KnowledgeType, 
        match: re.Match, 
        full_text: str
    ) -> float:
        """Calculate confidence score for rule-based extraction."""
        
        base_confidence = self.config.fallback_confidence
        
        # Adjust confidence based on various factors
        matched_text = match.group()
        
        # Length factor - longer matches might be more reliable
        length_factor = min(1.0, len(matched_text) / 100.0)
        
        # Position factor - matches at the beginning might be more reliable
        position_factor = 1.0 - (match.start() / len(full_text)) * 0.2
        
        # Pattern specificity factor
        specificity_factors = {
            KnowledgeType.DEFINITION: 0.8,  # Definition patterns are usually reliable
            KnowledgeType.THEOREM: 0.9,    # Theorem patterns are very specific
            KnowledgeType.FACT: 0.6,       # Fact patterns can be ambiguous
            KnowledgeType.PROCESS: 0.7,    # Process patterns are moderately reliable
            KnowledgeType.EXAMPLE: 0.5,    # Example patterns are common
        }
        
        specificity = specificity_factors.get(knowledge_type, 0.6)
        
        # Calculate final confidence
        confidence = base_confidence * (
            specificity * 0.5 +
            length_factor * 0.3 +
            position_factor * 0.2
        )
        
        return min(1.0, confidence)
    
    def _deduplicate_knowledge_points(
        self, 
        knowledge_points: List[ExtractedKnowledge]
    ) -> List[ExtractedKnowledge]:
        """Remove duplicate knowledge points."""
        
        if not knowledge_points:
            return knowledge_points
        
        # Sort by confidence (highest first)
        sorted_points = sorted(knowledge_points, key=lambda x: x.confidence, reverse=True)
        
        deduplicated = []
        seen_texts = set()
        
        for kp in sorted_points:
            # Normalize text for comparison
            normalized_text = kp.text.lower().strip()
            
            # Check for exact duplicates
            if normalized_text in seen_texts:
                continue
            
            # Check for substantial overlap with existing knowledge points
            is_duplicate = False
            for existing_kp in deduplicated:
                if self._calculate_text_overlap(kp.text, existing_kp.text) > 0.8:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                deduplicated.append(kp)
                seen_texts.add(normalized_text)
        
        return deduplicated
    
    def _calculate_text_overlap(self, text1: str, text2: str) -> float:
        """Calculate overlap between two text strings."""
        
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 and not words2:
            return 1.0
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union)
    
    async def save_knowledge_points(
        self, 
        knowledge_points: List[ExtractedKnowledge], 
        chapter_id: str
    ) -> List[Knowledge]:
        """Save extracted knowledge points to the database."""
        
        saved_knowledge = []
        
        async with get_async_session() as session:
            for kp in knowledge_points:
                try:
                    # Create Knowledge model instance
                    knowledge = Knowledge(
                        chapter_id=chapter_id,
                        kind=kp.kind,
                        text=kp.text,
                        entities=kp.entities,
                        anchors=kp.anchors,
                        confidence_score=kp.confidence
                    )
                    
                    session.add(knowledge)
                    saved_knowledge.append(knowledge)
                    
                except Exception as e:
                    logger.error(f"Error saving knowledge point: {e}")
                    continue
            
            try:
                await session.commit()
                logger.info(f"Saved {len(saved_knowledge)} knowledge points for chapter {chapter_id}")
            except Exception as e:
                logger.error(f"Error committing knowledge points: {e}")
                await session.rollback()
                saved_knowledge = []
        
        return saved_knowledge
    
    async def extract_and_save_knowledge(
        self, 
        segments: List[TextSegment], 
        chapter_id: str
    ) -> List[Knowledge]:
        """
        Complete pipeline: extract knowledge points from segments and save to database.
        
        Args:
            segments: Text segments to process
            chapter_id: ID of the chapter
            
        Returns:
            List of saved Knowledge model instances
        """
        
        # Extract knowledge points
        extracted_knowledge = await self.extract_knowledge_from_segments(segments, chapter_id)
        
        if not extracted_knowledge:
            logger.info(f"No knowledge points extracted for chapter {chapter_id}")
            return []
        
        # Save to database
        saved_knowledge = await self.save_knowledge_points(extracted_knowledge, chapter_id)
        
        logger.info(
            f"Knowledge extraction complete for chapter {chapter_id}: "
            f"{len(extracted_knowledge)} extracted, {len(saved_knowledge)} saved"
        )
        
        return saved_knowledge
    
    def get_extraction_statistics(
        self, 
        knowledge_points: List[ExtractedKnowledge]
    ) -> Dict[str, Any]:
        """Get statistics about extracted knowledge points."""
        
        if not knowledge_points:
            return {
                "total_knowledge_points": 0,
                "by_type": {},
                "avg_confidence": 0.0,
                "extraction_methods": {}
            }
        
        # Count by type
        type_counts = {}
        for kp in knowledge_points:
            type_counts[kp.kind.value] = type_counts.get(kp.kind.value, 0) + 1
        
        # Count by extraction method
        method_counts = {}
        for kp in knowledge_points:
            method = kp.anchors.get("extraction_method", "unknown")
            method_counts[method] = method_counts.get(method, 0) + 1
        
        # Calculate average confidence
        avg_confidence = sum(kp.confidence for kp in knowledge_points) / len(knowledge_points)
        
        return {
            "total_knowledge_points": len(knowledge_points),
            "by_type": type_counts,
            "avg_confidence": round(avg_confidence, 3),
            "extraction_methods": method_counts,
            "highest_confidence": max(knowledge_points, key=lambda x: x.confidence).text[:50] + "..."
        }