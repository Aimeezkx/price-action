"""
Deduplication service for detecting and removing duplicate flashcards
"""

import logging
from typing import List, Dict, Set, Tuple, Optional, Any
from dataclasses import dataclass
from collections import defaultdict
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from ..models.learning import Card, CardType
from ..models.knowledge import Knowledge
from ..services.embedding_service import EmbeddingService
from ..core.database import get_async_session

logger = logging.getLogger(__name__)


@dataclass
class DuplicateGroup:
    """Represents a group of duplicate cards"""
    
    primary_card: Card
    duplicate_cards: List[Card]
    similarity_scores: List[float]
    merge_strategy: str
    source_traceability: Dict[str, Any]


@dataclass
class DeduplicationConfig:
    """Configuration for deduplication process"""
    
    # Similarity thresholds
    semantic_similarity_threshold: float = 0.9
    exact_match_threshold: float = 0.99
    
    # Content comparison weights
    front_text_weight: float = 0.6
    back_text_weight: float = 0.4
    metadata_weight: float = 0.1
    
    # Deduplication targets
    max_duplicate_rate: float = 0.05  # 5% max duplicates
    
    # Merge preferences
    prefer_comprehensive_content: bool = True
    preserve_source_links: bool = True
    keep_higher_difficulty: bool = True


class DeduplicationService:
    """Service for detecting and removing duplicate flashcards"""
    
    def __init__(self, config: Optional[DeduplicationConfig] = None):
        """Initialize the deduplication service"""
        self.config = config or DeduplicationConfig()
        self.embedding_service = EmbeddingService()
    
    async def deduplicate_cards(
        self, 
        db: Session, 
        cards: List[Card],
        chapter_ids: Optional[List[str]] = None
    ) -> Tuple[List[Card], Dict[str, Any]]:
        """
        Main deduplication method that detects and removes duplicates
        
        Args:
            db: Database session
            cards: List of cards to deduplicate
            chapter_ids: Optional chapter filter
            
        Returns:
            Tuple of (deduplicated_cards, deduplication_stats)
        """
        if not cards:
            return [], {"total_cards": 0, "duplicates_removed": 0, "duplicate_rate": 0.0}
        
        logger.info(f"Starting deduplication for {len(cards)} cards")
        
        # Step 1: Detect duplicates
        duplicate_groups = await self._detect_duplicates(cards)
        
        # Step 2: Merge or remove duplicates
        deduplicated_cards, merge_stats = await self._process_duplicates(
            db, cards, duplicate_groups
        )
        
        # Step 3: Calculate final statistics
        stats = self._calculate_deduplication_stats(
            len(cards), len(deduplicated_cards), duplicate_groups, merge_stats
        )
        
        logger.info(f"Deduplication complete: {stats['duplicates_removed']} duplicates removed, "
                   f"final duplicate rate: {stats['duplicate_rate']:.2%}")
        
        return deduplicated_cards, stats
    
    async def _detect_duplicates(self, cards: List[Card]) -> List[DuplicateGroup]:
        """
        Detect duplicate cards using semantic similarity
        
        Args:
            cards: List of cards to analyze
            
        Returns:
            List of duplicate groups
        """
        duplicate_groups = []
        processed_card_ids = set()
        
        # Group cards by type for more efficient comparison
        cards_by_type = defaultdict(list)
        for card in cards:
            cards_by_type[card.card_type].append(card)
        
        # Process each card type separately
        for card_type, type_cards in cards_by_type.items():
            logger.info(f"Detecting duplicates for {len(type_cards)} {card_type} cards")
            
            type_duplicates = await self._detect_duplicates_by_type(
                type_cards, processed_card_ids
            )
            duplicate_groups.extend(type_duplicates)
        
        logger.info(f"Found {len(duplicate_groups)} duplicate groups")
        return duplicate_groups
    
    async def _detect_duplicates_by_type(
        self, 
        cards: List[Card], 
        processed_card_ids: Set[str]
    ) -> List[DuplicateGroup]:
        """
        Detect duplicates within cards of the same type
        
        Args:
            cards: Cards of the same type
            processed_card_ids: Set of already processed card IDs
            
        Returns:
            List of duplicate groups for this type
        """
        duplicate_groups = []
        
        for i, card1 in enumerate(cards):
            if str(card1.id) in processed_card_ids:
                continue
            
            duplicates = []
            similarities = []
            
            for j, card2 in enumerate(cards[i + 1:], i + 1):
                if str(card2.id) in processed_card_ids:
                    continue
                
                similarity = await self._calculate_card_similarity(card1, card2)
                
                if similarity >= self.config.semantic_similarity_threshold:
                    duplicates.append(card2)
                    similarities.append(similarity)
                    processed_card_ids.add(str(card2.id))
            
            if duplicates:
                # Determine primary card (most comprehensive or highest difficulty)
                primary_card = self._select_primary_card([card1] + duplicates)
                
                # Remove primary from duplicates list
                if primary_card != card1:
                    duplicates.remove(primary_card)
                    duplicates.insert(0, card1)
                    primary_card, duplicates[0] = duplicates[0], primary_card
                
                duplicate_group = DuplicateGroup(
                    primary_card=primary_card,
                    duplicate_cards=duplicates,
                    similarity_scores=similarities,
                    merge_strategy=self._determine_merge_strategy(primary_card, duplicates),
                    source_traceability=self._build_source_traceability([primary_card] + duplicates)
                )
                
                duplicate_groups.append(duplicate_group)
                processed_card_ids.add(str(primary_card.id))
        
        return duplicate_groups
    
    async def _calculate_card_similarity(self, card1: Card, card2: Card) -> float:
        """
        Calculate semantic similarity between two cards
        
        Args:
            card1: First card
            card2: Second card
            
        Returns:
            Similarity score between 0 and 1
        """
        # Check for exact matches first
        if self._is_exact_match(card1, card2):
            return 1.0
        
        # Calculate semantic similarity for text content
        front_similarity = self._calculate_text_similarity(card1.front, card2.front)
        back_similarity = self._calculate_text_similarity(card1.back, card2.back)
        
        # Calculate metadata similarity
        metadata_similarity = self._calculate_metadata_similarity(
            card1.card_metadata, card2.card_metadata
        )
        
        # Weighted combination
        total_similarity = (
            front_similarity * self.config.front_text_weight +
            back_similarity * self.config.back_text_weight +
            metadata_similarity * self.config.metadata_weight
        )
        
        # Normalize by total weight
        total_weight = (
            self.config.front_text_weight + 
            self.config.back_text_weight + 
            self.config.metadata_weight
        )
        
        return total_similarity / total_weight
    
    def _is_exact_match(self, card1: Card, card2: Card) -> bool:
        """Check if two cards are exact matches"""
        return (
            card1.card_type == card2.card_type and
            card1.front.strip().lower() == card2.front.strip().lower() and
            card1.back.strip().lower() == card2.back.strip().lower()
        )
    
    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """Calculate semantic similarity between two texts"""
        if not text1 or not text2:
            return 0.0
        
        # Generate embeddings
        embedding1 = self.embedding_service.generate_embedding(text1)
        embedding2 = self.embedding_service.generate_embedding(text2)
        
        # Calculate cosine similarity
        return self.embedding_service.calculate_similarity(embedding1, embedding2)
    
    def _calculate_metadata_similarity(self, metadata1: Dict, metadata2: Dict) -> float:
        """Calculate similarity between card metadata"""
        if not metadata1 and not metadata2:
            return 1.0
        
        if not metadata1 or not metadata2:
            return 0.0
        
        # Compare key metadata fields
        similarity_scores = []
        
        # Compare knowledge type
        if metadata1.get('knowledge_type') and metadata2.get('knowledge_type'):
            type_sim = 1.0 if metadata1['knowledge_type'] == metadata2['knowledge_type'] else 0.0
            similarity_scores.append(type_sim)
        
        # Compare blanked entities for cloze cards
        if 'blanked_entities' in metadata1 and 'blanked_entities' in metadata2:
            entities1 = set(e['entity'] for e in metadata1['blanked_entities'])
            entities2 = set(e['entity'] for e in metadata2['blanked_entities'])
            
            if entities1 and entities2:
                entity_overlap = len(entities1.intersection(entities2)) / len(entities1.union(entities2))
                similarity_scores.append(entity_overlap)
        
        # Compare hotspots for image cards
        if 'hotspots' in metadata1 and 'hotspots' in metadata2:
            hotspots1 = metadata1['hotspots']
            hotspots2 = metadata2['hotspots']
            
            if hotspots1 and hotspots2:
                hotspot_sim = self._compare_hotspots(hotspots1, hotspots2)
                similarity_scores.append(hotspot_sim)
        
        return sum(similarity_scores) / len(similarity_scores) if similarity_scores else 0.5
    
    def _compare_hotspots(self, hotspots1: List[Dict], hotspots2: List[Dict]) -> float:
        """Compare hotspot metadata for image cards"""
        if not hotspots1 or not hotspots2:
            return 0.0
        
        # Simple comparison based on number and labels
        labels1 = set(h.get('label', '') for h in hotspots1)
        labels2 = set(h.get('label', '') for h in hotspots2)
        
        if not labels1 and not labels2:
            return 1.0
        
        if not labels1 or not labels2:
            return 0.0
        
        return len(labels1.intersection(labels2)) / len(labels1.union(labels2))
    
    def _select_primary_card(self, cards: List[Card]) -> Card:
        """
        Select the primary card from a group of duplicates
        
        Args:
            cards: List of duplicate cards
            
        Returns:
            The card to keep as primary
        """
        if len(cards) == 1:
            return cards[0]
        
        # Score each card based on various factors
        card_scores = []
        
        for card in cards:
            score = 0.0
            
            # Content comprehensiveness (longer content is often more comprehensive)
            content_length = len(card.front) + len(card.back)
            score += min(content_length / 1000, 1.0) * 0.3
            
            # Difficulty score (higher difficulty might indicate more detailed content)
            if self.config.keep_higher_difficulty:
                score += (card.difficulty / 5.0) * 0.2
            
            # Metadata richness
            metadata_richness = len(card.card_metadata) if card.card_metadata else 0
            score += min(metadata_richness / 10, 1.0) * 0.2
            
            # Knowledge source quality (prefer cards with more entities)
            if hasattr(card, 'knowledge') and card.knowledge:
                entity_count = len(card.knowledge.entities) if card.knowledge.entities else 0
                score += min(entity_count / 5, 1.0) * 0.3
            
            card_scores.append((card, score))
        
        # Return card with highest score
        card_scores.sort(key=lambda x: x[1], reverse=True)
        return card_scores[0][0]
    
    def _determine_merge_strategy(self, primary_card: Card, duplicates: List[Card]) -> str:
        """Determine the best merge strategy for a duplicate group"""
        
        # For now, use simple removal strategy
        # In future, could implement content merging
        return "remove_duplicates"
    
    def _build_source_traceability(self, cards: List[Card]) -> Dict[str, Any]:
        """Build source traceability information for duplicate group"""
        
        traceability = {
            "original_card_ids": [str(card.id) for card in cards],
            "knowledge_ids": [],
            "chapter_ids": [],
            "source_anchors": []
        }
        
        for card in cards:
            if hasattr(card, 'knowledge') and card.knowledge:
                traceability["knowledge_ids"].append(str(card.knowledge.id))
                traceability["chapter_ids"].append(str(card.knowledge.chapter_id))
                if card.knowledge.anchors:
                    traceability["source_anchors"].append(card.knowledge.anchors)
        
        # Remove duplicates
        traceability["knowledge_ids"] = list(set(traceability["knowledge_ids"]))
        traceability["chapter_ids"] = list(set(traceability["chapter_ids"]))
        
        return traceability
    
    async def _process_duplicates(
        self, 
        db: Session, 
        original_cards: List[Card], 
        duplicate_groups: List[DuplicateGroup]
    ) -> Tuple[List[Card], Dict[str, Any]]:
        """
        Process duplicate groups by merging or removing duplicates
        
        Args:
            db: Database session
            original_cards: Original list of cards
            duplicate_groups: Detected duplicate groups
            
        Returns:
            Tuple of (processed_cards, merge_statistics)
        """
        # Create set of all duplicate card IDs to remove
        cards_to_remove = set()
        merge_stats = {
            "groups_processed": len(duplicate_groups),
            "cards_removed": 0,
            "cards_merged": 0,
            "source_links_preserved": 0
        }
        
        for group in duplicate_groups:
            # Mark duplicate cards for removal
            for duplicate_card in group.duplicate_cards:
                cards_to_remove.add(str(duplicate_card.id))
                merge_stats["cards_removed"] += 1
            
            # Update primary card with merged information if needed
            if group.merge_strategy == "merge_content":
                await self._merge_card_content(db, group)
                merge_stats["cards_merged"] += 1
            
            # Preserve source traceability
            await self._preserve_source_traceability(db, group)
            merge_stats["source_links_preserved"] += len(group.source_traceability["original_card_ids"])
        
        # Filter out duplicate cards
        deduplicated_cards = [
            card for card in original_cards 
            if str(card.id) not in cards_to_remove
        ]
        
        return deduplicated_cards, merge_stats
    
    async def _merge_card_content(self, db: Session, group: DuplicateGroup) -> None:
        """
        Merge content from duplicate cards into primary card
        
        Args:
            db: Database session
            group: Duplicate group to merge
        """
        # For now, just update metadata to include source information
        # In future, could implement more sophisticated content merging
        
        primary_card = group.primary_card
        
        # Merge metadata
        merged_metadata = dict(primary_card.card_metadata) if primary_card.card_metadata else {}
        merged_metadata["merged_from"] = group.source_traceability["original_card_ids"]
        merged_metadata["merge_timestamp"] = str(datetime.utcnow())
        
        primary_card.card_metadata = merged_metadata
        
        # Update in database
        db.add(primary_card)
    
    async def _preserve_source_traceability(self, db: Session, group: DuplicateGroup) -> None:
        """
        Preserve source traceability information for duplicate group
        
        Args:
            db: Database session
            group: Duplicate group
        """
        # Update primary card metadata with source traceability
        primary_card = group.primary_card
        metadata = dict(primary_card.card_metadata) if primary_card.card_metadata else {}
        
        metadata["source_traceability"] = group.source_traceability
        metadata["duplicate_similarity_scores"] = group.similarity_scores
        
        primary_card.card_metadata = metadata
        db.add(primary_card)
    
    def _calculate_deduplication_stats(
        self, 
        original_count: int, 
        final_count: int, 
        duplicate_groups: List[DuplicateGroup],
        merge_stats: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate comprehensive deduplication statistics"""
        
        duplicates_removed = original_count - final_count
        duplicate_rate = duplicates_removed / original_count if original_count > 0 else 0.0
        
        # Calculate average similarity scores
        all_similarities = []
        for group in duplicate_groups:
            all_similarities.extend(group.similarity_scores)
        
        avg_similarity = sum(all_similarities) / len(all_similarities) if all_similarities else 0.0
        
        stats = {
            "total_cards": original_count,
            "final_cards": final_count,
            "duplicates_removed": duplicates_removed,
            "duplicate_rate": duplicate_rate,
            "duplicate_groups": len(duplicate_groups),
            "average_similarity": avg_similarity,
            "meets_target": duplicate_rate <= self.config.max_duplicate_rate,
            "merge_stats": merge_stats
        }
        
        return stats
    
    async def validate_deduplication_quality(
        self, 
        db: Session, 
        cards: List[Card]
    ) -> Dict[str, Any]:
        """
        Validate the quality of deduplication results
        
        Args:
            db: Database session
            cards: Deduplicated cards
            
        Returns:
            Validation results
        """
        # Re-run duplicate detection to check remaining duplicates
        remaining_duplicates = await self._detect_duplicates(cards)
        
        remaining_duplicate_rate = 0.0
        if cards:
            total_remaining_duplicates = sum(len(group.duplicate_cards) for group in remaining_duplicates)
            remaining_duplicate_rate = total_remaining_duplicates / len(cards)
        
        validation_results = {
            "remaining_duplicate_groups": len(remaining_duplicates),
            "remaining_duplicate_rate": remaining_duplicate_rate,
            "meets_quality_threshold": remaining_duplicate_rate <= self.config.max_duplicate_rate,
            "total_cards_validated": len(cards)
        }
        
        return validation_results


# Global deduplication service instance
deduplication_service = DeduplicationService()