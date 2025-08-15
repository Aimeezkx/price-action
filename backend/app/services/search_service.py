"""
Search service for full-text and semantic search functionality
"""

import logging
import re
from typing import List, Optional, Dict, Any, Union, Tuple
from enum import Enum
from sqlalchemy.orm import Session
from sqlalchemy import text, func, or_, and_
from dataclasses import dataclass
import math

from ..models.knowledge import Knowledge, KnowledgeType
from ..models.document import Chapter, Document
from ..models.learning import Card, CardType
from .embedding_service import embedding_service

logger = logging.getLogger(__name__)


class SearchType(str, Enum):
    """Types of search"""
    FULL_TEXT = "full_text"
    SEMANTIC = "semantic"
    HYBRID = "hybrid"


@dataclass
class SearchFilters:
    """Search filters"""
    chapter_ids: Optional[List[str]] = None
    knowledge_types: Optional[List[KnowledgeType]] = None
    card_types: Optional[List[CardType]] = None
    difficulty_min: Optional[float] = None
    difficulty_max: Optional[float] = None
    document_ids: Optional[List[str]] = None


@dataclass
class SearchResult:
    """Search result item"""
    id: str
    type: str  # 'knowledge' or 'card'
    title: str
    content: str
    snippet: str
    score: float
    metadata: Dict[str, Any]
    highlights: List[str] = None
    rank_factors: Dict[str, float] = None  # For debugging ranking


class SearchService:
    """Service for searching knowledge points and cards"""
    
    def __init__(self):
        self.default_limit = 20
        self.max_limit = 100
        self.snippet_length = 200
        self.highlight_tag_start = "<mark>"
        self.highlight_tag_end = "</mark>"
        self.max_highlights = 5
    
    def search(
        self,
        db: Session,
        query: str,
        search_type: SearchType = SearchType.HYBRID,
        filters: Optional[SearchFilters] = None,
        limit: int = None,
        offset: int = 0,
        similarity_threshold: float = 0.7
    ) -> List[SearchResult]:
        """
        Main search function that routes to appropriate search method
        
        Args:
            db: Database session
            query: Search query text
            search_type: Type of search to perform
            filters: Optional search filters
            limit: Maximum number of results
            offset: Number of results to skip
            similarity_threshold: Minimum similarity for semantic search
            
        Returns:
            List of search results
        """
        if not query or not query.strip():
            return []
        
        limit = min(limit or self.default_limit, self.max_limit)
        filters = filters or SearchFilters()
        
        try:
            if search_type == SearchType.FULL_TEXT:
                return self._full_text_search(db, query, filters, limit, offset)
            elif search_type == SearchType.SEMANTIC:
                return self._semantic_search(db, query, filters, limit, offset, similarity_threshold)
            elif search_type == SearchType.HYBRID:
                return self._hybrid_search(db, query, filters, limit, offset, similarity_threshold)
            else:
                raise ValueError(f"Unsupported search type: {search_type}")
                
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
    
    def _full_text_search(
        self,
        db: Session,
        query: str,
        filters: SearchFilters,
        limit: int,
        offset: int
    ) -> List[SearchResult]:
        """
        Perform full-text search using PostgreSQL's text search capabilities
        """
        results = []
        
        # Search knowledge points
        knowledge_results = self._search_knowledge_full_text(db, query, filters, limit, offset)
        results.extend(knowledge_results)
        
        # Search cards if we haven't reached the limit
        remaining_limit = limit - len(results)
        if remaining_limit > 0:
            card_results = self._search_cards_full_text(db, query, filters, remaining_limit, offset)
            results.extend(card_results)
        
        # Sort by relevance score
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:limit]
    
    def _semantic_search(
        self,
        db: Session,
        query: str,
        filters: SearchFilters,
        limit: int,
        offset: int,
        similarity_threshold: float
    ) -> List[SearchResult]:
        """
        Perform semantic search using vector embeddings
        """
        # Generate query embedding
        query_embedding = embedding_service.generate_embedding(query)
        
        # Search knowledge points using vector similarity
        knowledge_query = db.query(Knowledge).filter(Knowledge.embedding.isnot(None))
        
        # Apply filters
        knowledge_query = self._apply_knowledge_filters(knowledge_query, filters)
        
        # Add similarity calculation
        similarity_expr = Knowledge.embedding.cosine_distance(query_embedding)
        knowledge_query = knowledge_query.add_columns(similarity_expr.label('distance'))
        knowledge_query = knowledge_query.filter(similarity_expr < (1 - similarity_threshold))
        knowledge_query = knowledge_query.order_by(similarity_expr)
        knowledge_query = knowledge_query.offset(offset).limit(limit)
        
        results = []
        for knowledge, distance in knowledge_query.all():
            similarity = 1 - distance
            result = self._knowledge_to_search_result(knowledge, similarity, query)
            results.append(result)
        
        return results
    
    def _hybrid_search(
        self,
        db: Session,
        query: str,
        filters: SearchFilters,
        limit: int,
        offset: int,
        similarity_threshold: float
    ) -> List[SearchResult]:
        """
        Perform hybrid search combining full-text and semantic search
        """
        # Get results from both search types
        full_text_results = self._full_text_search(db, query, filters, limit * 2, offset)
        semantic_results = self._semantic_search(db, query, filters, limit * 2, offset, similarity_threshold)
        
        # Combine and deduplicate results
        combined_results = {}
        
        # Add full-text results with weight
        for result in full_text_results:
            key = f"{result.type}_{result.id}"
            combined_results[key] = result
            result.score *= 0.6  # Weight full-text search
        
        # Add semantic results with weight, combining scores if duplicate
        for result in semantic_results:
            key = f"{result.type}_{result.id}"
            if key in combined_results:
                # Combine scores for items found in both searches
                combined_results[key].score += result.score * 0.4
            else:
                result.score *= 0.4  # Weight semantic search
                combined_results[key] = result
        
        # Sort by combined score and return top results
        final_results = list(combined_results.values())
        final_results.sort(key=lambda x: x.score, reverse=True)
        
        return final_results[:limit]
    
    def _search_knowledge_full_text(
        self,
        db: Session,
        query: str,
        filters: SearchFilters,
        limit: int,
        offset: int
    ) -> List[SearchResult]:
        """Search knowledge points using full-text search"""
        try:
            # Build base query
            knowledge_query = db.query(Knowledge)
            
            # Apply filters
            knowledge_query = self._apply_knowledge_filters(knowledge_query, filters)
            
            # Add full-text search using PostgreSQL's text search
            search_vector = func.to_tsvector('english', Knowledge.text)
            search_query = func.plainto_tsquery('english', query)
            
            knowledge_query = knowledge_query.filter(search_vector.match(search_query))
            knowledge_query = knowledge_query.add_columns(
                func.ts_rank(search_vector, search_query).label('rank')
            )
            knowledge_query = knowledge_query.order_by(text('rank DESC'))
            knowledge_query = knowledge_query.offset(offset).limit(limit)
            
            results = []
            for knowledge, rank in knowledge_query.all():
                result = self._knowledge_to_search_result(knowledge, float(rank), query)
                results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"Full-text search for knowledge failed: {e}")
            # Fallback to simple LIKE search
            return self._search_knowledge_simple(db, query, filters, limit, offset)
    
    def _search_knowledge_simple(
        self,
        db: Session,
        query: str,
        filters: SearchFilters,
        limit: int,
        offset: int
    ) -> List[SearchResult]:
        """Fallback simple search for knowledge points"""
        knowledge_query = db.query(Knowledge)
        knowledge_query = self._apply_knowledge_filters(knowledge_query, filters)
        
        # Simple text matching
        search_terms = query.lower().split()
        for term in search_terms:
            knowledge_query = knowledge_query.filter(
                Knowledge.text.ilike(f'%{term}%')
            )
        
        knowledge_query = knowledge_query.offset(offset).limit(limit)
        
        results = []
        for knowledge in knowledge_query.all():
            # Calculate simple relevance score based on term frequency
            score = self._calculate_simple_relevance(knowledge.text, query)
            result = self._knowledge_to_search_result(knowledge, score, query)
            results.append(result)
        
        return results
    
    def _search_cards_full_text(
        self,
        db: Session,
        query: str,
        filters: SearchFilters,
        limit: int,
        offset: int
    ) -> List[SearchResult]:
        """Search cards using full-text search"""
        try:
            # Build base query
            card_query = db.query(Card).join(Knowledge).join(Chapter)
            
            # Apply filters
            card_query = self._apply_card_filters(card_query, filters)
            
            # Add full-text search
            search_vector = func.to_tsvector('english', 
                func.concat(Card.front, ' ', Card.back)
            )
            search_query = func.plainto_tsquery('english', query)
            
            card_query = card_query.filter(search_vector.match(search_query))
            card_query = card_query.add_columns(
                func.ts_rank(search_vector, search_query).label('rank')
            )
            card_query = card_query.order_by(text('rank DESC'))
            card_query = card_query.offset(offset).limit(limit)
            
            results = []
            for card, rank in card_query.all():
                result = self._card_to_search_result(card, float(rank), query)
                results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"Full-text search for cards failed: {e}")
            return []
    
    def _apply_knowledge_filters(self, query, filters: SearchFilters):
        """Apply filters to knowledge query"""
        if filters.chapter_ids:
            query = query.filter(Knowledge.chapter_id.in_(filters.chapter_ids))
        
        if filters.knowledge_types:
            query = query.filter(Knowledge.kind.in_(filters.knowledge_types))
        
        if filters.document_ids:
            query = query.join(Chapter).filter(Chapter.document_id.in_(filters.document_ids))
        
        return query
    
    def _apply_card_filters(self, query, filters: SearchFilters):
        """Apply filters to card query"""
        if filters.chapter_ids:
            query = query.filter(Knowledge.chapter_id.in_(filters.chapter_ids))
        
        if filters.card_types:
            query = query.filter(Card.card_type.in_(filters.card_types))
        
        if filters.difficulty_min is not None:
            query = query.filter(Card.difficulty >= filters.difficulty_min)
        
        if filters.difficulty_max is not None:
            query = query.filter(Card.difficulty <= filters.difficulty_max)
        
        if filters.document_ids:
            query = query.filter(Chapter.document_id.in_(filters.document_ids))
        
        return query
    
    def _knowledge_to_search_result(self, knowledge: Knowledge, score: float, query: str = None) -> SearchResult:
        """Convert knowledge point to search result"""
        metadata = {
            "kind": knowledge.kind.value,
            "entities": knowledge.entities or [],
            "anchors": knowledge.anchors or {},
            "chapter_id": str(knowledge.chapter_id),
            "confidence_score": knowledge.confidence_score
        }
        
        # Apply advanced ranking if query is provided
        final_score = score
        rank_factors = None
        
        if query:
            advanced_score, rank_factors = self._calculate_advanced_ranking(knowledge.text, query, metadata)
            # Combine original score with advanced ranking
            final_score = (score * 0.6) + (advanced_score * 0.4)
        
        # Create snippet with highlighting
        snippet = self._create_snippet(knowledge.text, query)
        
        # Add highlighting to content
        highlighted_content = knowledge.text
        highlights = []
        
        if query:
            highlighted_content, highlights = self._highlight_text(knowledge.text, query)
        
        return SearchResult(
            id=str(knowledge.id),
            type="knowledge",
            title=f"{knowledge.kind.value.title()} Knowledge",
            content=highlighted_content,
            snippet=snippet,
            score=final_score,
            metadata=metadata,
            highlights=highlights,
            rank_factors=rank_factors
        )
    
    def _card_to_search_result(self, card: Card, score: float, query: str = None) -> SearchResult:
        """Convert card to search result"""
        content = f"Front: {card.front}\nBack: {card.back}"
        
        metadata = {
            "card_type": card.card_type.value,
            "difficulty": card.difficulty,
            "knowledge_id": str(card.knowledge_id),
            "card_metadata": card.card_metadata or {}
        }
        
        # Apply advanced ranking if query is provided
        final_score = score
        rank_factors = None
        
        if query:
            advanced_score, rank_factors = self._calculate_advanced_ranking(content, query, metadata)
            # Combine original score with advanced ranking
            final_score = (score * 0.6) + (advanced_score * 0.4)
        
        # Create snippet with highlighting
        snippet = self._create_snippet(content, query)
        
        # Add highlighting to content
        highlighted_content = content
        highlights = []
        
        if query:
            highlighted_content, highlights = self._highlight_text(content, query)
        
        return SearchResult(
            id=str(card.id),
            type="card",
            title=f"{card.card_type.value.replace('_', ' ').title()} Card",
            content=highlighted_content,
            snippet=snippet,
            score=final_score,
            metadata=metadata,
            highlights=highlights,
            rank_factors=rank_factors
        )
    
    def _create_snippet(self, text: str, query: str = None) -> str:
        """Create a snippet from text, optionally highlighting query terms"""
        if len(text) <= self.snippet_length:
            snippet = text
        else:
            # Try to find the best snippet containing query terms
            if query:
                snippet = self._find_best_snippet(text, query)
            else:
                # Default snippet from beginning
                snippet = text[:self.snippet_length]
                last_period = snippet.rfind('.')
                last_space = snippet.rfind(' ')
                
                if last_period > self.snippet_length * 0.7:
                    snippet = snippet[:last_period + 1]
                elif last_space > self.snippet_length * 0.7:
                    snippet = snippet[:last_space] + "..."
                else:
                    snippet = snippet + "..."
        
        return snippet
    
    def _find_best_snippet(self, text: str, query: str) -> str:
        """Find the best snippet containing query terms"""
        query_terms = self._extract_query_terms(query)
        if not query_terms:
            return text[:self.snippet_length] + ("..." if len(text) > self.snippet_length else "")
        
        # Find positions of query terms
        term_positions = []
        text_lower = text.lower()
        
        for term in query_terms:
            term_lower = term.lower()
            start = 0
            while True:
                pos = text_lower.find(term_lower, start)
                if pos == -1:
                    break
                term_positions.append((pos, pos + len(term)))
                start = pos + 1
        
        if not term_positions:
            return text[:self.snippet_length] + ("..." if len(text) > self.snippet_length else "")
        
        # Find the best window that contains the most terms
        best_start = 0
        best_score = 0
        
        for start_pos, _ in term_positions:
            window_start = max(0, start_pos - self.snippet_length // 2)
            window_end = min(len(text), window_start + self.snippet_length)
            
            # Count terms in this window
            score = sum(1 for pos_start, pos_end in term_positions 
                       if window_start <= pos_start < window_end)
            
            if score > best_score:
                best_score = score
                best_start = window_start
        
        # Extract the best snippet
        snippet_end = min(len(text), best_start + self.snippet_length)
        snippet = text[best_start:snippet_end]
        
        # Clean up snippet boundaries
        if best_start > 0:
            # Find word boundary
            space_pos = snippet.find(' ')
            if space_pos > 0 and space_pos < 50:
                snippet = "..." + snippet[space_pos:]
            else:
                snippet = "..." + snippet
        
        if snippet_end < len(text):
            # Find word boundary from end
            last_space = snippet.rfind(' ')
            if last_space > len(snippet) - 50:
                snippet = snippet[:last_space] + "..."
            else:
                snippet = snippet + "..."
        
        return snippet
    
    def _extract_query_terms(self, query: str) -> List[str]:
        """Extract meaningful terms from query"""
        # Remove common stop words and short terms
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should'}
        
        # Split query into terms and filter
        terms = re.findall(r'\b\w+\b', query.lower())
        meaningful_terms = [term for term in terms if len(term) > 2 and term not in stop_words]
        
        return meaningful_terms[:10]  # Limit to 10 terms
    
    def _highlight_text(self, text: str, query: str) -> Tuple[str, List[str]]:
        """Add highlighting to text and return highlighted text and highlight list"""
        query_terms = self._extract_query_terms(query)
        if not query_terms:
            return text, []
        
        highlighted_text = text
        highlights = []
        
        # Sort terms by length (longest first) to avoid partial replacements
        query_terms.sort(key=len, reverse=True)
        
        for term in query_terms:
            # Use word boundaries to match whole words
            pattern = r'\b' + re.escape(term) + r'\b'
            matches = list(re.finditer(pattern, highlighted_text, re.IGNORECASE))
            
            if matches:
                # Replace matches with highlighted versions
                offset = 0
                for match in matches:
                    start = match.start() + offset
                    end = match.end() + offset
                    original = highlighted_text[start:end]
                    highlighted = f"{self.highlight_tag_start}{original}{self.highlight_tag_end}"
                    highlighted_text = highlighted_text[:start] + highlighted + highlighted_text[end:]
                    offset += len(highlighted) - len(original)
                    
                    # Add to highlights list (limit to max_highlights)
                    if len(highlights) < self.max_highlights:
                        highlights.append(original)
        
        return highlighted_text, highlights[:self.max_highlights]
    
    def _calculate_simple_relevance(self, text: str, query: str) -> float:
        """Calculate simple relevance score based on term frequency"""
        text_lower = text.lower()
        query_terms = query.lower().split()
        
        score = 0.0
        for term in query_terms:
            count = text_lower.count(term)
            score += count / len(text_lower) * 100
        
        return score
    
    def _calculate_advanced_ranking(self, text: str, query: str, metadata: Dict[str, Any]) -> Tuple[float, Dict[str, float]]:
        """Calculate advanced ranking score with multiple factors"""
        query_terms = self._extract_query_terms(query)
        if not query_terms:
            return 0.0, {}
        
        text_lower = text.lower()
        factors = {}
        
        # 1. Term frequency score
        tf_score = 0.0
        total_matches = 0
        for term in query_terms:
            count = text_lower.count(term.lower())
            if count > 0:
                # TF-IDF like scoring
                tf = count / len(text_lower.split())
                tf_score += tf
                total_matches += count
        
        factors['term_frequency'] = tf_score
        
        # 2. Term coverage (how many query terms are found)
        matched_terms = sum(1 for term in query_terms if term.lower() in text_lower)
        coverage_score = matched_terms / len(query_terms) if query_terms else 0
        factors['term_coverage'] = coverage_score
        
        # 3. Position bonus (terms appearing early get higher score)
        position_score = 0.0
        for term in query_terms:
            pos = text_lower.find(term.lower())
            if pos != -1:
                # Higher score for terms appearing earlier
                position_bonus = max(0, 1 - (pos / len(text_lower)))
                position_score += position_bonus
        
        position_score = position_score / len(query_terms) if query_terms else 0
        factors['position_bonus'] = position_score
        
        # 4. Exact phrase bonus
        phrase_score = 0.0
        if len(query_terms) > 1:
            # Check for exact phrase matches
            query_phrase = ' '.join(query_terms)
            if query_phrase in text_lower:
                phrase_score = 0.5  # Significant bonus for exact phrase
        factors['phrase_bonus'] = phrase_score
        
        # 5. Content type bonus
        content_bonus = 0.0
        if metadata.get('kind') == 'definition':
            content_bonus = 0.2  # Definitions are often more relevant
        elif metadata.get('kind') == 'fact':
            content_bonus = 0.1
        factors['content_bonus'] = content_bonus
        
        # 6. Confidence score bonus (for knowledge points)
        confidence_bonus = 0.0
        if 'confidence_score' in metadata:
            confidence_bonus = metadata['confidence_score'] * 0.1
        factors['confidence_bonus'] = confidence_bonus
        
        # 7. Length penalty (very short or very long texts get penalty)
        length_penalty = 0.0
        text_length = len(text.split())
        if text_length < 10:
            length_penalty = -0.1  # Too short
        elif text_length > 500:
            length_penalty = -0.05  # Too long
        factors['length_penalty'] = length_penalty
        
        # Combine all factors
        final_score = (
            tf_score * 2.0 +           # Term frequency is most important
            coverage_score * 1.5 +     # Term coverage is very important
            position_score * 0.5 +     # Position matters less
            phrase_score +             # Exact phrases are valuable
            content_bonus +            # Content type bonus
            confidence_bonus +         # Confidence bonus
            length_penalty             # Length penalty
        )
        
        return max(0.0, final_score), factors
    
    def get_search_suggestions(
        self,
        db: Session,
        query: str,
        limit: int = 5
    ) -> List[str]:
        """
        Get search suggestions based on existing knowledge points
        """
        if not query or len(query) < 2:
            return []
        
        try:
            # Get entities that start with the query
            entity_query = db.query(Knowledge.entities).filter(
                Knowledge.entities.isnot(None)
            ).limit(100)
            
            suggestions = set()
            for (entities,) in entity_query.all():
                if entities:
                    for entity in entities:
                        if entity.lower().startswith(query.lower()):
                            suggestions.add(entity)
                        if len(suggestions) >= limit:
                            break
                if len(suggestions) >= limit:
                    break
            
            return list(suggestions)[:limit]
            
        except Exception as e:
            logger.error(f"Failed to get search suggestions: {e}")
            return []
    
    def calculate_mrr(self, search_results: List[List[SearchResult]], relevant_results: List[List[str]]) -> float:
        """
        Calculate Mean Reciprocal Rank (MRR) for search performance evaluation
        
        Args:
            search_results: List of search result lists for each query
            relevant_results: List of relevant result IDs for each query
            
        Returns:
            MRR score (0.0 to 1.0)
        """
        if not search_results or not relevant_results or len(search_results) != len(relevant_results):
            return 0.0
        
        reciprocal_ranks = []
        
        for results, relevant_ids in zip(search_results, relevant_results):
            if not relevant_ids:
                reciprocal_ranks.append(0.0)
                continue
            
            # Find the rank of the first relevant result
            first_relevant_rank = None
            for i, result in enumerate(results):
                if result.id in relevant_ids:
                    first_relevant_rank = i + 1  # Rank is 1-based
                    break
            
            if first_relevant_rank:
                reciprocal_ranks.append(1.0 / first_relevant_rank)
            else:
                reciprocal_ranks.append(0.0)
        
        return sum(reciprocal_ranks) / len(reciprocal_ranks)
    
    def get_search_performance_metrics(
        self,
        db: Session,
        test_queries: List[str],
        expected_results: List[List[str]],
        search_type: SearchType = SearchType.HYBRID
    ) -> Dict[str, float]:
        """
        Evaluate search performance using test queries
        
        Args:
            db: Database session
            test_queries: List of test queries
            expected_results: List of expected result IDs for each query
            search_type: Type of search to evaluate
            
        Returns:
            Dictionary with performance metrics
        """
        if len(test_queries) != len(expected_results):
            raise ValueError("Number of test queries must match number of expected results")
        
        all_results = []
        response_times = []
        
        for query in test_queries:
            import time
            start_time = time.time()
            
            results = self.search(
                db=db,
                query=query,
                search_type=search_type,
                limit=20
            )
            
            end_time = time.time()
            response_times.append(end_time - start_time)
            all_results.append(results)
        
        # Calculate metrics
        mrr = self.calculate_mrr(all_results, expected_results)
        avg_response_time = sum(response_times) / len(response_times)
        
        # Calculate precision at different ranks
        precision_at_1 = self._calculate_precision_at_k(all_results, expected_results, 1)
        precision_at_5 = self._calculate_precision_at_k(all_results, expected_results, 5)
        precision_at_10 = self._calculate_precision_at_k(all_results, expected_results, 10)
        
        return {
            'mrr': mrr,
            'avg_response_time': avg_response_time,
            'precision_at_1': precision_at_1,
            'precision_at_5': precision_at_5,
            'precision_at_10': precision_at_10,
            'total_queries': len(test_queries)
        }
    
    def _calculate_precision_at_k(
        self,
        search_results: List[List[SearchResult]],
        relevant_results: List[List[str]],
        k: int
    ) -> float:
        """Calculate precision at rank k"""
        if not search_results or not relevant_results:
            return 0.0
        
        precisions = []
        
        for results, relevant_ids in zip(search_results, relevant_results):
            if not relevant_ids:
                precisions.append(0.0)
                continue
            
            # Take top k results
            top_k_results = results[:k]
            
            # Count relevant results in top k
            relevant_count = sum(1 for result in top_k_results if result.id in relevant_ids)
            
            # Calculate precision
            precision = relevant_count / min(k, len(top_k_results)) if top_k_results else 0.0
            precisions.append(precision)
        
        return sum(precisions) / len(precisions)
    
    def optimize_search_query(self, query: str) -> str:
        """
        Optimize search query for better performance
        
        Args:
            query: Original search query
            
        Returns:
            Optimized query
        """
        # Remove extra whitespace
        query = ' '.join(query.split())
        
        # Remove very common words that don't add value
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        words = query.lower().split()
        
        # Keep stop words if they're part of a phrase or if the query is very short
        if len(words) > 3:
            meaningful_words = [word for word in words if word not in stop_words or len(word) > 3]
            if meaningful_words:  # Don't return empty query
                query = ' '.join(meaningful_words)
        
        # Limit query length to prevent performance issues
        if len(query) > 200:
            query = query[:200].rsplit(' ', 1)[0]  # Cut at word boundary
        
        return query
    
    def get_search_analytics(self, db: Session) -> Dict[str, Any]:
        """
        Get search analytics and statistics
        
        Returns:
            Dictionary with search analytics
        """
        try:
            # Count total searchable items
            total_knowledge = db.query(Knowledge).count()
            total_cards = db.query(Card).count()
            
            # Count items with embeddings
            knowledge_with_embeddings = db.query(Knowledge).filter(Knowledge.embedding.isnot(None)).count()
            
            # Get knowledge type distribution
            knowledge_types = db.query(Knowledge.kind, func.count(Knowledge.id)).group_by(Knowledge.kind).all()
            
            # Get card type distribution
            card_types = db.query(Card.card_type, func.count(Card.id)).group_by(Card.card_type).all()
            
            # Calculate embedding coverage
            embedding_coverage = (knowledge_with_embeddings / total_knowledge * 100) if total_knowledge > 0 else 0
            
            return {
                'total_searchable_items': total_knowledge + total_cards,
                'total_knowledge': total_knowledge,
                'total_cards': total_cards,
                'knowledge_with_embeddings': knowledge_with_embeddings,
                'embedding_coverage_percent': round(embedding_coverage, 2),
                'knowledge_type_distribution': {kt.value: count for kt, count in knowledge_types},
                'card_type_distribution': {ct.value: count for ct, count in card_types},
                'search_capabilities': {
                    'full_text_search': True,
                    'semantic_search': knowledge_with_embeddings > 0,
                    'hybrid_search': knowledge_with_embeddings > 0,
                    'filtering': True,
                    'highlighting': True
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get search analytics: {e}")
            return {'error': str(e)}


# Global search service instance
search_service = SearchService()