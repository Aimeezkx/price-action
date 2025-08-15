"""
Search API endpoints
"""

import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from ..core.database import get_db
from ..services.search_service import search_service, SearchType, SearchFilters
from ..services.embedding_service import embedding_service
from ..services.vector_index_service import vector_index_service
from ..models.knowledge import KnowledgeType
from ..models.learning import CardType

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/search", tags=["search"])


class SearchRequest(BaseModel):
    """Search request model"""
    query: str = Field(..., min_length=1, max_length=500, description="Search query")
    search_type: SearchType = Field(SearchType.HYBRID, description="Type of search to perform")
    limit: int = Field(20, ge=1, le=100, description="Maximum number of results")
    offset: int = Field(0, ge=0, description="Number of results to skip")
    similarity_threshold: float = Field(0.7, ge=0.0, le=1.0, description="Minimum similarity for semantic search")
    
    # Filters
    chapter_ids: Optional[List[str]] = Field(None, description="Filter by chapter IDs")
    knowledge_types: Optional[List[KnowledgeType]] = Field(None, description="Filter by knowledge types")
    card_types: Optional[List[CardType]] = Field(None, description="Filter by card types")
    difficulty_min: Optional[float] = Field(None, ge=0.0, le=5.0, description="Minimum difficulty")
    difficulty_max: Optional[float] = Field(None, ge=0.0, le=5.0, description="Maximum difficulty")
    document_ids: Optional[List[str]] = Field(None, description="Filter by document IDs")


class SearchResultResponse(BaseModel):
    """Search result response model"""
    id: str
    type: str
    title: str
    content: str
    snippet: str
    score: float
    metadata: Dict[str, Any]
    highlights: Optional[List[str]] = None
    rank_factors: Optional[Dict[str, float]] = None


class SearchResponse(BaseModel):
    """Search response model"""
    query: str
    search_type: str
    total_results: int
    results: List[SearchResultResponse]
    suggestions: Optional[List[str]] = None


class SimilarityRequest(BaseModel):
    """Request for finding similar content"""
    text: str = Field(..., min_length=1, max_length=2000, description="Text to find similar content for")
    similarity_threshold: float = Field(0.7, ge=0.0, le=1.0, description="Minimum similarity threshold")
    limit: int = Field(10, ge=1, le=50, description="Maximum number of results")
    chapter_ids: Optional[List[str]] = Field(None, description="Filter by chapter IDs")


class VectorIndexResponse(BaseModel):
    """Vector index operation response"""
    success: bool
    message: str
    details: Dict[str, Any]


@router.get("/", response_model=SearchResponse)
async def search_get(
    query: str = Query(..., min_length=1, max_length=500, description="Search query"),
    search_type: SearchType = Query(SearchType.HYBRID, description="Type of search to perform"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    similarity_threshold: float = Query(0.7, ge=0.0, le=1.0, description="Minimum similarity for semantic search"),
    chapter_ids: Optional[str] = Query(None, description="Comma-separated chapter IDs"),
    knowledge_types: Optional[str] = Query(None, description="Comma-separated knowledge types"),
    card_types: Optional[str] = Query(None, description="Comma-separated card types"),
    difficulty_min: Optional[float] = Query(None, ge=0.0, le=5.0, description="Minimum difficulty"),
    difficulty_max: Optional[float] = Query(None, ge=0.0, le=5.0, description="Maximum difficulty"),
    document_ids: Optional[str] = Query(None, description="Comma-separated document IDs"),
    db: Session = Depends(get_db)
):
    """
    Search for knowledge points and cards using GET method
    
    Supports three types of search:
    - full_text: Traditional text-based search
    - semantic: Vector similarity search using embeddings
    - hybrid: Combination of both approaches (recommended)
    
    Query parameters can be passed as comma-separated strings for arrays.
    """
    try:
        # Parse comma-separated strings into lists
        chapter_ids_list = chapter_ids.split(',') if chapter_ids else None
        knowledge_types_list = [KnowledgeType(kt.strip()) for kt in knowledge_types.split(',')] if knowledge_types else None
        card_types_list = [CardType(ct.strip()) for ct in card_types.split(',')] if card_types else None
        document_ids_list = document_ids.split(',') if document_ids else None
        
        # Create search filters
        filters = SearchFilters(
            chapter_ids=chapter_ids_list,
            knowledge_types=knowledge_types_list,
            card_types=card_types_list,
            difficulty_min=difficulty_min,
            difficulty_max=difficulty_max,
            document_ids=document_ids_list
        )
        
        # Perform search
        results = search_service.search(
            db=db,
            query=query,
            search_type=search_type,
            filters=filters,
            limit=limit,
            offset=offset,
            similarity_threshold=similarity_threshold
        )
        
        # Get search suggestions
        suggestions = search_service.get_search_suggestions(
            db=db,
            query=query,
            limit=5
        )
        
        # Convert results to response format
        result_responses = [
            SearchResultResponse(
                id=result.id,
                type=result.type,
                title=result.title,
                content=result.content,
                snippet=result.snippet,
                score=result.score,
                metadata=result.metadata,
                highlights=result.highlights,
                rank_factors=result.rank_factors
            )
            for result in results
        ]
        
        return SearchResponse(
            query=query,
            search_type=search_type.value,
            total_results=len(result_responses),
            results=result_responses,
            suggestions=suggestions if suggestions else None
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid parameter value: {str(e)}")
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.post("/", response_model=SearchResponse)
async def search_post(
    request: SearchRequest,
    db: Session = Depends(get_db)
):
    """
    Search for knowledge points and cards using POST method
    
    Supports three types of search:
    - full_text: Traditional text-based search
    - semantic: Vector similarity search using embeddings
    - hybrid: Combination of both approaches (recommended)
    
    Use this endpoint for complex search requests with multiple filters.
    """
    try:
        # Create search filters
        filters = SearchFilters(
            chapter_ids=request.chapter_ids,
            knowledge_types=request.knowledge_types,
            card_types=request.card_types,
            difficulty_min=request.difficulty_min,
            difficulty_max=request.difficulty_max,
            document_ids=request.document_ids
        )
        
        # Perform search
        results = search_service.search(
            db=db,
            query=request.query,
            search_type=request.search_type,
            filters=filters,
            limit=request.limit,
            offset=request.offset,
            similarity_threshold=request.similarity_threshold
        )
        
        # Get search suggestions
        suggestions = search_service.get_search_suggestions(
            db=db,
            query=request.query,
            limit=5
        )
        
        # Convert results to response format
        result_responses = [
            SearchResultResponse(
                id=result.id,
                type=result.type,
                title=result.title,
                content=result.content,
                snippet=result.snippet,
                score=result.score,
                metadata=result.metadata,
                highlights=result.highlights,
                rank_factors=result.rank_factors
            )
            for result in results
        ]
        
        return SearchResponse(
            query=request.query,
            search_type=request.search_type.value,
            total_results=len(result_responses),
            results=result_responses,
            suggestions=suggestions if suggestions else None
        )
        
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.get("/suggestions")
async def get_search_suggestions(
    query: str = Query(..., min_length=1, max_length=100),
    limit: int = Query(5, ge=1, le=20),
    db: Session = Depends(get_db)
):
    """
    Get search suggestions based on query
    """
    try:
        suggestions = search_service.get_search_suggestions(
            db=db,
            query=query,
            limit=limit
        )
        
        return {"suggestions": suggestions}
        
    except Exception as e:
        logger.error(f"Failed to get search suggestions: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get suggestions: {str(e)}")


@router.post("/similar", response_model=List[SearchResultResponse])
async def find_similar_content(
    request: SimilarityRequest,
    db: Session = Depends(get_db)
):
    """
    Find content similar to the provided text using semantic search
    """
    try:
        # Find similar knowledge points
        similar_knowledge = embedding_service.search_similar_knowledge(
            db=db,
            query_text=request.text,
            similarity_threshold=request.similarity_threshold,
            limit=request.limit,
            chapter_ids=request.chapter_ids
        )
        
        # Convert to search results
        results = []
        for knowledge, similarity in similar_knowledge:
            result = SearchResultResponse(
                id=str(knowledge.id),
                type="knowledge",
                title=f"{knowledge.kind.value.title()} Knowledge",
                content=knowledge.text,
                snippet=knowledge.text[:200] + "..." if len(knowledge.text) > 200 else knowledge.text,
                score=similarity,
                metadata={
                    "kind": knowledge.kind.value,
                    "entities": knowledge.entities or [],
                    "anchors": knowledge.anchors or {},
                    "chapter_id": str(knowledge.chapter_id),
                    "confidence_score": knowledge.confidence_score
                }
            )
            results.append(result)
        
        return results
        
    except Exception as e:
        logger.error(f"Failed to find similar content: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to find similar content: {str(e)}")


@router.post("/embeddings/update")
async def update_embeddings(
    knowledge_ids: Optional[List[str]] = None,
    db: Session = Depends(get_db)
):
    """
    Update embeddings for knowledge points
    
    If knowledge_ids is provided, only update those specific knowledge points.
    Otherwise, update all knowledge points that don't have embeddings.
    """
    try:
        updated_count = await embedding_service.update_knowledge_embeddings(
            db=db,
            knowledge_ids=knowledge_ids
        )
        
        return {
            "success": True,
            "message": f"Updated embeddings for {updated_count} knowledge points",
            "updated_count": updated_count
        }
        
    except Exception as e:
        logger.error(f"Failed to update embeddings: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update embeddings: {str(e)}")


@router.post("/duplicates/find")
async def find_duplicates(
    similarity_threshold: float = Query(0.9, ge=0.7, le=1.0),
    chapter_ids: Optional[List[str]] = None,
    db: Session = Depends(get_db)
):
    """
    Find duplicate knowledge points based on semantic similarity
    """
    try:
        duplicates = embedding_service.find_duplicate_knowledge(
            db=db,
            similarity_threshold=similarity_threshold,
            chapter_ids=chapter_ids
        )
        
        # Format response
        duplicate_pairs = []
        for kp1, kp2, similarity in duplicates:
            duplicate_pairs.append({
                "knowledge1": {
                    "id": str(kp1.id),
                    "text": kp1.text,
                    "kind": kp1.kind.value,
                    "chapter_id": str(kp1.chapter_id)
                },
                "knowledge2": {
                    "id": str(kp2.id),
                    "text": kp2.text,
                    "kind": kp2.kind.value,
                    "chapter_id": str(kp2.chapter_id)
                },
                "similarity": similarity
            })
        
        return {
            "total_duplicates": len(duplicate_pairs),
            "similarity_threshold": similarity_threshold,
            "duplicates": duplicate_pairs
        }
        
    except Exception as e:
        logger.error(f"Failed to find duplicates: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to find duplicates: {str(e)}")


@router.post("/indexes/create", response_model=VectorIndexResponse)
async def create_vector_indexes(db: Session = Depends(get_db)):
    """
    Create vector indexes for improved search performance
    """
    try:
        results = vector_index_service.create_vector_indexes(db)
        
        success = all(results.values())
        message = "All indexes created successfully" if success else "Some indexes failed to create"
        
        return VectorIndexResponse(
            success=success,
            message=message,
            details=results
        )
        
    except Exception as e:
        logger.error(f"Failed to create vector indexes: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create indexes: {str(e)}")


@router.delete("/indexes", response_model=VectorIndexResponse)
async def drop_vector_indexes(db: Session = Depends(get_db)):
    """
    Drop vector indexes
    """
    try:
        results = vector_index_service.drop_vector_indexes(db)
        
        success = all(results.values())
        message = "All indexes dropped successfully" if success else "Some indexes failed to drop"
        
        return VectorIndexResponse(
            success=success,
            message=message,
            details=results
        )
        
    except Exception as e:
        logger.error(f"Failed to drop vector indexes: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to drop indexes: {str(e)}")


@router.get("/performance/analyze")
async def analyze_search_performance(db: Session = Depends(get_db)):
    """
    Analyze vector search performance and get recommendations
    """
    try:
        analysis = vector_index_service.analyze_vector_performance(db)
        return analysis
        
    except Exception as e:
        logger.error(f"Failed to analyze performance: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to analyze performance: {str(e)}")


@router.post("/performance/optimize")
async def optimize_search_performance(db: Session = Depends(get_db)):
    """
    Optimize database settings for vector search performance
    """
    try:
        optimizations = vector_index_service.optimize_vector_search_settings(db)
        return {
            "success": True,
            "message": "Search performance optimized",
            "optimizations": optimizations
        }
        
    except Exception as e:
        logger.error(f"Failed to optimize performance: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to optimize performance: {str(e)}")


@router.post("/maintenance/vacuum")
async def vacuum_vector_tables(db: Session = Depends(get_db)):
    """
    Run VACUUM ANALYZE on vector tables for optimal performance
    """
    try:
        results = vector_index_service.vacuum_analyze_vector_tables(db)
        
        success = all(results.values())
        message = "All tables vacuumed successfully" if success else "Some tables failed to vacuum"
        
        return {
            "success": success,
            "message": message,
            "details": results
        }
        
    except Exception as e:
        logger.error(f"Failed to vacuum tables: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to vacuum tables: {str(e)}")


class PerformanceTestRequest(BaseModel):
    """Request for performance testing"""
    test_queries: List[str] = Field(..., min_items=1, max_items=100, description="Test queries")
    expected_results: List[List[str]] = Field(..., description="Expected result IDs for each query")
    search_type: SearchType = Field(SearchType.HYBRID, description="Type of search to test")


@router.post("/performance/test")
async def test_search_performance(
    request: PerformanceTestRequest,
    db: Session = Depends(get_db)
):
    """
    Test search performance with provided queries and expected results
    """
    try:
        metrics = search_service.get_search_performance_metrics(
            db=db,
            test_queries=request.test_queries,
            expected_results=request.expected_results,
            search_type=request.search_type
        )
        
        # Check if MRR meets requirement
        mrr_meets_requirement = metrics['mrr'] >= 0.8
        
        return {
            "performance_metrics": metrics,
            "mrr_requirement_met": mrr_meets_requirement,
            "requirement_threshold": 0.8,
            "recommendations": _get_performance_recommendations(metrics)
        }
        
    except Exception as e:
        logger.error(f"Failed to test search performance: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to test performance: {str(e)}")


@router.get("/analytics")
async def get_search_analytics(db: Session = Depends(get_db)):
    """
    Get search analytics and statistics
    """
    try:
        analytics = search_service.get_search_analytics(db)
        return analytics
        
    except Exception as e:
        logger.error(f"Failed to get search analytics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get analytics: {str(e)}")


@router.post("/query/optimize")
async def optimize_search_query(
    query: str = Query(..., min_length=1, max_length=500, description="Query to optimize")
):
    """
    Optimize a search query for better performance
    """
    try:
        optimized_query = search_service.optimize_search_query(query)
        
        return {
            "original_query": query,
            "optimized_query": optimized_query,
            "optimizations_applied": _get_query_optimizations(query, optimized_query)
        }
        
    except Exception as e:
        logger.error(f"Failed to optimize query: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to optimize query: {str(e)}")


def _get_performance_recommendations(metrics: Dict[str, float]) -> List[str]:
    """Get performance improvement recommendations based on metrics"""
    recommendations = []
    
    if metrics['mrr'] < 0.8:
        recommendations.append("MRR is below 0.8 threshold. Consider improving ranking algorithm or updating embeddings.")
    
    if metrics['avg_response_time'] > 1.0:
        recommendations.append("Average response time is high. Consider adding database indexes or optimizing queries.")
    
    if metrics['precision_at_1'] < 0.5:
        recommendations.append("Precision at rank 1 is low. Consider improving query understanding or result ranking.")
    
    if metrics['precision_at_5'] < 0.3:
        recommendations.append("Precision at rank 5 is low. Consider expanding search scope or improving semantic matching.")
    
    if not recommendations:
        recommendations.append("Search performance looks good! All metrics are within acceptable ranges.")
    
    return recommendations


def _get_query_optimizations(original: str, optimized: str) -> List[str]:
    """Get list of optimizations applied to query"""
    optimizations = []
    
    if len(optimized.split()) < len(original.split()):
        optimizations.append("Removed stop words")
    
    if len(optimized) < len(original):
        optimizations.append("Trimmed query length")
    
    if original != original.strip():
        optimizations.append("Removed extra whitespace")
    
    if not optimizations:
        optimizations.append("No optimizations needed")
    
    return optimizations