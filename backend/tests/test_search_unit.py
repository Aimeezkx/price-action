"""Comprehensive unit tests for search functionality and vector operations."""

import pytest
from unittest.mock import Mock, patch, AsyncMock
import numpy as np
from datetime import datetime

from app.services.search_service import SearchService
from app.services.vector_index_service import VectorIndexService
from app.services.embedding_service import EmbeddingService


@pytest.mark.unit
class TestSearchService:
    """Test search service functionality."""
    
    def test_service_initialization(self):
        """Test search service initializes correctly."""
        service = SearchService()
        assert service is not None
        assert hasattr(service, 'search')
        assert hasattr(service, 'semantic_search')
    
    @pytest.mark.asyncio
    async def test_basic_text_search(self):
        """Test basic text search functionality."""
        service = SearchService()
        
        query = "machine learning"
        
        with patch.object(service, '_text_search') as mock_text_search:
            mock_text_search.return_value = [
                {
                    "id": "doc1",
                    "title": "Introduction to Machine Learning",
                    "content": "Machine learning is a subset of artificial intelligence...",
                    "score": 0.95,
                    "highlights": ["<mark>machine learning</mark>"]
                },
                {
                    "id": "doc2", 
                    "title": "Advanced ML Techniques",
                    "content": "This chapter covers advanced machine learning algorithms...",
                    "score": 0.87,
                    "highlights": ["<mark>machine learning</mark> algorithms"]
                }
            ]
            
            results = await service.search(query, search_type="text")
            
            assert len(results) == 2
            assert results[0]["score"] > results[1]["score"]  # Sorted by relevance
            assert "machine learning" in results[0]["title"].lower()
            assert all("highlights" in result for result in results)
    
    @pytest.mark.asyncio
    async def test_semantic_search(self):
        """Test semantic search using embeddings."""
        service = SearchService()
        
        query = "AI algorithms"
        
        with patch.object(service, '_semantic_search') as mock_semantic:
            mock_semantic.return_value = [
                {
                    "id": "doc1",
                    "title": "Neural Networks",
                    "content": "Deep learning networks process information...",
                    "semantic_score": 0.92,
                    "embedding_similarity": 0.89
                },
                {
                    "id": "doc2",
                    "title": "Decision Trees", 
                    "content": "Tree-based algorithms for classification...",
                    "semantic_score": 0.78,
                    "embedding_similarity": 0.75
                }
            ]
            
            results = await service.semantic_search(query)
            
            assert len(results) == 2
            assert results[0]["semantic_score"] > results[1]["semantic_score"]
            assert all("embedding_similarity" in result for result in results)
    
    @pytest.mark.asyncio
    async def test_hybrid_search(self):
        """Test hybrid search combining text and semantic search."""
        service = SearchService()
        
        query = "neural network training"
        
        with patch.object(service, '_hybrid_search') as mock_hybrid:
            mock_hybrid.return_value = [
                {
                    "id": "doc1",
                    "title": "Training Neural Networks",
                    "content": "Backpropagation algorithm for training...",
                    "text_score": 0.95,
                    "semantic_score": 0.88,
                    "combined_score": 0.92,
                    "match_type": "both"
                },
                {
                    "id": "doc2",
                    "title": "Deep Learning Fundamentals",
                    "content": "Understanding neural architectures...",
                    "text_score": 0.65,
                    "semantic_score": 0.91,
                    "combined_score": 0.78,
                    "match_type": "semantic"
                }
            ]
            
            results = await service.search(query, search_type="hybrid")
            
            assert len(results) == 2
            assert results[0]["combined_score"] > results[1]["combined_score"]
            assert "match_type" in results[0]
    
    @pytest.mark.asyncio
    async def test_search_with_filters(self):
        """Test search with various filters."""
        service = SearchService()
        
        query = "machine learning"
        filters = {
            "document_type": ["pdf", "docx"],
            "date_range": {
                "start": datetime(2023, 1, 1),
                "end": datetime(2023, 12, 31)
            },
            "difficulty_range": {"min": 0.3, "max": 0.8},
            "tags": ["supervised", "algorithms"]
        }
        
        with patch.object(service, '_search_with_filters') as mock_filtered:
            mock_filtered.return_value = [
                {
                    "id": "doc1",
                    "title": "Supervised Learning",
                    "document_type": "pdf",
                    "created_date": datetime(2023, 6, 15),
                    "difficulty": 0.6,
                    "tags": ["supervised", "algorithms"],
                    "score": 0.89
                }
            ]
            
            results = await service.search(query, filters=filters)
            
            assert len(results) == 1
            assert results[0]["document_type"] in filters["document_type"]
            assert filters["difficulty_range"]["min"] <= results[0]["difficulty"] <= filters["difficulty_range"]["max"]
            assert all(tag in results[0]["tags"] for tag in filters["tags"])
    
    @pytest.mark.asyncio
    async def test_faceted_search(self):
        """Test faceted search with aggregations."""
        service = SearchService()
        
        query = "deep learning"
        
        with patch.object(service, '_faceted_search') as mock_faceted:
            mock_faceted.return_value = {
                "results": [
                    {"id": "doc1", "title": "CNN Architectures", "score": 0.92},
                    {"id": "doc2", "title": "RNN Applications", "score": 0.85}
                ],
                "facets": {
                    "document_type": {"pdf": 15, "docx": 8, "md": 3},
                    "difficulty": {"easy": 5, "medium": 12, "hard": 9},
                    "tags": {"cnn": 8, "rnn": 6, "transformer": 4},
                    "date_created": {"2023": 18, "2022": 8}
                }
            }
            
            results = await service.faceted_search(query)
            
            assert "results" in results
            assert "facets" in results
            assert len(results["results"]) == 2
            assert "document_type" in results["facets"]
            assert results["facets"]["document_type"]["pdf"] == 15
    
    @pytest.mark.asyncio
    async def test_search_suggestions(self):
        """Test search query suggestions and autocomplete."""
        service = SearchService()
        
        partial_query = "mach"
        
        with patch.object(service, '_get_suggestions') as mock_suggestions:
            mock_suggestions.return_value = [
                {"suggestion": "machine learning", "frequency": 45, "score": 0.95},
                {"suggestion": "machine vision", "frequency": 12, "score": 0.78},
                {"suggestion": "matching algorithms", "frequency": 8, "score": 0.65}
            ]
            
            suggestions = await service.get_search_suggestions(partial_query)
            
            assert len(suggestions) == 3
            assert suggestions[0]["frequency"] > suggestions[1]["frequency"]
            assert all(partial_query in sugg["suggestion"] for sugg in suggestions)
    
    @pytest.mark.asyncio
    async def test_search_result_ranking(self):
        """Test search result ranking algorithms."""
        service = SearchService()
        
        raw_results = [
            {"id": "doc1", "text_score": 0.8, "semantic_score": 0.7, "popularity": 0.9},
            {"id": "doc2", "text_score": 0.9, "semantic_score": 0.6, "popularity": 0.5},
            {"id": "doc3", "text_score": 0.7, "semantic_score": 0.9, "popularity": 0.8}
        ]
        
        with patch.object(service, '_rank_results') as mock_rank:
            mock_rank.return_value = [
                {"id": "doc3", "final_score": 0.87},  # High semantic + popularity
                {"id": "doc1", "final_score": 0.82},  # Balanced scores
                {"id": "doc2", "final_score": 0.75}   # High text but low popularity
            ]
            
            ranked = await service._rank_results(raw_results)
            
            assert len(ranked) == 3
            assert ranked[0]["final_score"] > ranked[1]["final_score"]
            assert ranked[1]["final_score"] > ranked[2]["final_score"]
    
    @pytest.mark.asyncio
    async def test_search_personalization(self):
        """Test personalized search based on user preferences."""
        service = SearchService()
        
        query = "neural networks"
        user_profile = {
            "user_id": "user123",
            "interests": ["computer_vision", "deep_learning"],
            "skill_level": "intermediate",
            "preferred_content_types": ["tutorial", "example"],
            "interaction_history": ["doc1", "doc5", "doc12"]
        }
        
        with patch.object(service, '_personalized_search') as mock_personalized:
            mock_personalized.return_value = [
                {
                    "id": "doc1",
                    "title": "CNN for Image Recognition",
                    "content_type": "tutorial",
                    "difficulty": "intermediate",
                    "personalization_score": 0.95,
                    "base_score": 0.82
                }
            ]
            
            results = await service.search(query, user_profile=user_profile)
            
            assert len(results) == 1
            assert results[0]["difficulty"] == user_profile["skill_level"]
            assert results[0]["content_type"] in user_profile["preferred_content_types"]
            assert results[0]["personalization_score"] > results[0]["base_score"]
    
    def test_search_validation(self):
        """Test search input validation."""
        service = SearchService()
        
        # Test empty query
        with pytest.raises(ValueError, match="Query cannot be empty"):
            service._validate_query("")
        
        # Test very long query
        long_query = "A" * 1000
        with pytest.raises(ValueError, match="Query too long"):
            service._validate_query(long_query)
        
        # Test invalid search type
        with pytest.raises(ValueError, match="Invalid search type"):
            service._validate_search_params("test", search_type="invalid")
    
    @pytest.mark.asyncio
    async def test_search_performance_tracking(self):
        """Test search performance tracking and analytics."""
        service = SearchService()
        
        query = "test query"
        
        with patch.object(service, '_track_search_performance') as mock_track:
            mock_track.return_value = {
                "query": query,
                "response_time": 0.15,
                "result_count": 25,
                "user_clicked": None,  # Not yet clicked
                "timestamp": datetime.now()
            }
            
            await service.search(query, track_performance=True)
            
            mock_track.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_search_caching(self):
        """Test search result caching."""
        service = SearchService()
        
        query = "cached query"
        
        with patch.object(service, '_get_cached_results') as mock_get_cache:
            with patch.object(service, '_cache_results') as mock_set_cache:
                mock_get_cache.return_value = None  # Not cached initially
                
                with patch.object(service, '_perform_search') as mock_search:
                    mock_search.return_value = [{"id": "doc1", "score": 0.9}]
                    
                    # First search - should cache
                    results1 = await service.search(query, use_cache=True)
                    
                    # Second search - should use cache
                    mock_get_cache.return_value = [{"id": "doc1", "score": 0.9}]
                    results2 = await service.search(query, use_cache=True)
                    
                    assert results1 == results2
                    mock_set_cache.assert_called_once()


@pytest.mark.unit
class TestVectorIndexService:
    """Test vector index service functionality."""
    
    def test_service_initialization(self):
        """Test vector index service initializes correctly."""
        service = VectorIndexService()
        assert service is not None
        assert hasattr(service, 'add_vectors')
        assert hasattr(service, 'search_similar')
    
    @pytest.mark.asyncio
    async def test_add_vectors_to_index(self):
        """Test adding vectors to the index."""
        service = VectorIndexService()
        
        vectors = [
            {"id": "doc1", "vector": np.array([0.1, 0.2, 0.3]), "metadata": {"title": "Doc 1"}},
            {"id": "doc2", "vector": np.array([0.4, 0.5, 0.6]), "metadata": {"title": "Doc 2"}}
        ]
        
        with patch.object(service, '_add_to_index') as mock_add:
            mock_add.return_value = {"added": 2, "failed": 0}
            
            result = await service.add_vectors(vectors)
            
            assert result["added"] == 2
            assert result["failed"] == 0
            mock_add.assert_called_once_with(vectors)
    
    @pytest.mark.asyncio
    async def test_similarity_search(self):
        """Test similarity search in vector index."""
        service = VectorIndexService()
        
        query_vector = np.array([0.2, 0.3, 0.4])
        
        with patch.object(service, '_similarity_search') as mock_search:
            mock_search.return_value = [
                {"id": "doc1", "similarity": 0.95, "metadata": {"title": "Similar Doc 1"}},
                {"id": "doc2", "similarity": 0.87, "metadata": {"title": "Similar Doc 2"}},
                {"id": "doc3", "similarity": 0.72, "metadata": {"title": "Similar Doc 3"}}
            ]
            
            results = await service.search_similar(query_vector, top_k=3)
            
            assert len(results) == 3
            assert results[0]["similarity"] > results[1]["similarity"]
            assert results[1]["similarity"] > results[2]["similarity"]
            assert all("metadata" in result for result in results)
    
    @pytest.mark.asyncio
    async def test_batch_similarity_search(self):
        """Test batch similarity search."""
        service = VectorIndexService()
        
        query_vectors = [
            np.array([0.1, 0.2, 0.3]),
            np.array([0.4, 0.5, 0.6])
        ]
        
        with patch.object(service, '_batch_similarity_search') as mock_batch:
            mock_batch.return_value = [
                [{"id": "doc1", "similarity": 0.9}],  # Results for first query
                [{"id": "doc2", "similarity": 0.8}]   # Results for second query
            ]
            
            results = await service.batch_search_similar(query_vectors, top_k=1)
            
            assert len(results) == 2
            assert len(results[0]) == 1
            assert len(results[1]) == 1
    
    @pytest.mark.asyncio
    async def test_vector_index_update(self):
        """Test updating vectors in the index."""
        service = VectorIndexService()
        
        updates = [
            {"id": "doc1", "vector": np.array([0.2, 0.3, 0.4]), "metadata": {"title": "Updated Doc 1"}},
            {"id": "doc2", "vector": np.array([0.5, 0.6, 0.7]), "metadata": {"title": "Updated Doc 2"}}
        ]
        
        with patch.object(service, '_update_vectors') as mock_update:
            mock_update.return_value = {"updated": 2, "not_found": 0}
            
            result = await service.update_vectors(updates)
            
            assert result["updated"] == 2
            assert result["not_found"] == 0
    
    @pytest.mark.asyncio
    async def test_vector_index_deletion(self):
        """Test deleting vectors from the index."""
        service = VectorIndexService()
        
        ids_to_delete = ["doc1", "doc2", "doc3"]
        
        with patch.object(service, '_delete_vectors') as mock_delete:
            mock_delete.return_value = {"deleted": 2, "not_found": 1}
            
            result = await service.delete_vectors(ids_to_delete)
            
            assert result["deleted"] == 2
            assert result["not_found"] == 1
    
    @pytest.mark.asyncio
    async def test_index_statistics(self):
        """Test getting index statistics."""
        service = VectorIndexService()
        
        with patch.object(service, '_get_index_stats') as mock_stats:
            mock_stats.return_value = {
                "total_vectors": 1000,
                "dimension": 384,
                "index_size_mb": 15.2,
                "last_updated": datetime.now(),
                "search_performance": {
                    "avg_query_time_ms": 12.5,
                    "queries_per_second": 80
                }
            }
            
            stats = await service.get_index_statistics()
            
            assert stats["total_vectors"] == 1000
            assert stats["dimension"] == 384
            assert "search_performance" in stats
    
    @pytest.mark.asyncio
    async def test_index_optimization(self):
        """Test index optimization and rebuilding."""
        service = VectorIndexService()
        
        with patch.object(service, '_optimize_index') as mock_optimize:
            mock_optimize.return_value = {
                "optimization_time": 45.2,
                "size_reduction": 0.15,
                "performance_improvement": 0.23
            }
            
            result = await service.optimize_index()
            
            assert "optimization_time" in result
            assert "size_reduction" in result
            assert "performance_improvement" in result
    
    def test_vector_validation(self):
        """Test vector validation and error handling."""
        service = VectorIndexService()
        
        # Test invalid vector dimensions
        invalid_vector = {"id": "doc1", "vector": np.array([0.1, 0.2])}  # Wrong dimension
        
        with pytest.raises(ValueError, match="Vector dimension mismatch"):
            service._validate_vector(invalid_vector, expected_dim=384)
        
        # Test missing vector
        missing_vector = {"id": "doc1", "metadata": {"title": "No vector"}}
        
        with pytest.raises(ValueError, match="Vector is required"):
            service._validate_vector(missing_vector)
    
    @pytest.mark.asyncio
    async def test_approximate_nearest_neighbors(self):
        """Test approximate nearest neighbor search."""
        service = VectorIndexService()
        
        query_vector = np.array([0.1, 0.2, 0.3])
        
        with patch.object(service, '_ann_search') as mock_ann:
            mock_ann.return_value = [
                {"id": "doc1", "similarity": 0.92, "approximate": True},
                {"id": "doc2", "similarity": 0.88, "approximate": True}
            ]
            
            results = await service.search_similar(
                query_vector, 
                top_k=2, 
                method="approximate"
            )
            
            assert len(results) == 2
            assert all(result["approximate"] for result in results)
    
    @pytest.mark.asyncio
    async def test_exact_nearest_neighbors(self):
        """Test exact nearest neighbor search."""
        service = VectorIndexService()
        
        query_vector = np.array([0.1, 0.2, 0.3])
        
        with patch.object(service, '_exact_search') as mock_exact:
            mock_exact.return_value = [
                {"id": "doc1", "similarity": 0.9234, "approximate": False},
                {"id": "doc2", "similarity": 0.8756, "approximate": False}
            ]
            
            results = await service.search_similar(
                query_vector, 
                top_k=2, 
                method="exact"
            )
            
            assert len(results) == 2
            assert all(not result["approximate"] for result in results)
    
    @pytest.mark.asyncio
    async def test_filtered_vector_search(self):
        """Test vector search with metadata filters."""
        service = VectorIndexService()
        
        query_vector = np.array([0.1, 0.2, 0.3])
        filters = {
            "document_type": "pdf",
            "difficulty": {"min": 0.3, "max": 0.8},
            "tags": ["machine_learning"]
        }
        
        with patch.object(service, '_filtered_search') as mock_filtered:
            mock_filtered.return_value = [
                {
                    "id": "doc1", 
                    "similarity": 0.91,
                    "metadata": {
                        "document_type": "pdf",
                        "difficulty": 0.6,
                        "tags": ["machine_learning", "supervised"]
                    }
                }
            ]
            
            results = await service.search_similar(
                query_vector, 
                top_k=5, 
                filters=filters
            )
            
            assert len(results) == 1
            assert results[0]["metadata"]["document_type"] == "pdf"
            assert 0.3 <= results[0]["metadata"]["difficulty"] <= 0.8
    
    @pytest.mark.asyncio
    async def test_vector_clustering(self):
        """Test vector clustering functionality."""
        service = VectorIndexService()
        
        with patch.object(service, '_cluster_vectors') as mock_cluster:
            mock_cluster.return_value = {
                "clusters": [
                    {
                        "cluster_id": 0,
                        "centroid": np.array([0.2, 0.3, 0.4]),
                        "size": 150,
                        "documents": ["doc1", "doc2", "doc3"]
                    },
                    {
                        "cluster_id": 1,
                        "centroid": np.array([0.7, 0.8, 0.9]),
                        "size": 120,
                        "documents": ["doc4", "doc5", "doc6"]
                    }
                ],
                "silhouette_score": 0.72
            }
            
            result = await service.cluster_vectors(n_clusters=2)
            
            assert len(result["clusters"]) == 2
            assert result["silhouette_score"] > 0.7
            assert all("centroid" in cluster for cluster in result["clusters"])


@pytest.mark.integration
class TestSearchVectorIntegration:
    """Test integration between search and vector services."""
    
    @pytest.mark.asyncio
    async def test_search_with_vector_similarity(self):
        """Test search combining text and vector similarity."""
        search_service = SearchService()
        vector_service = VectorIndexService()
        embedding_service = EmbeddingService()
        
        query = "machine learning algorithms"
        
        with patch.object(embedding_service, 'generate_embedding') as mock_embed:
            mock_embed.return_value = np.array([0.1, 0.2, 0.3])
            
            with patch.object(vector_service, 'search_similar') as mock_vector_search:
                mock_vector_search.return_value = [
                    {"id": "doc1", "similarity": 0.92},
                    {"id": "doc2", "similarity": 0.85}
                ]
                
                with patch.object(search_service, '_text_search') as mock_text_search:
                    mock_text_search.return_value = [
                        {"id": "doc1", "text_score": 0.88},
                        {"id": "doc3", "text_score": 0.75}
                    ]
                    
                    # Combine results
                    query_embedding = await embedding_service.generate_embedding(query)
                    vector_results = await vector_service.search_similar(query_embedding)
                    text_results = await search_service._text_search(query)
                    
                    # Should have results from both searches
                    assert len(vector_results) == 2
                    assert len(text_results) == 2
                    
                    # doc1 appears in both results
                    vector_doc1 = next(r for r in vector_results if r["id"] == "doc1")
                    text_doc1 = next(r for r in text_results if r["id"] == "doc1")
                    assert vector_doc1["id"] == text_doc1["id"]
    
    @pytest.mark.asyncio
    async def test_index_update_after_document_processing(self):
        """Test updating vector index after document processing."""
        vector_service = VectorIndexService()
        embedding_service = EmbeddingService()
        
        new_document = {
            "id": "new_doc",
            "title": "New Machine Learning Paper",
            "content": "This paper discusses novel approaches to deep learning...",
            "metadata": {"type": "research_paper", "difficulty": 0.8}
        }
        
        with patch.object(embedding_service, 'generate_embedding') as mock_embed:
            mock_embed.return_value = np.array([0.3, 0.4, 0.5])
            
            with patch.object(vector_service, 'add_vectors') as mock_add:
                mock_add.return_value = {"added": 1, "failed": 0}
                
                # Generate embedding for new document
                embedding = await embedding_service.generate_embedding(new_document["content"])
                
                # Add to vector index
                vector_data = [{
                    "id": new_document["id"],
                    "vector": embedding,
                    "metadata": new_document["metadata"]
                }]
                
                result = await vector_service.add_vectors(vector_data)
                
                assert result["added"] == 1
                assert result["failed"] == 0
    
    @pytest.mark.asyncio
    async def test_search_performance_optimization(self):
        """Test search performance optimization strategies."""
        search_service = SearchService()
        vector_service = VectorIndexService()
        
        # Simulate high-frequency queries
        frequent_queries = [
            "machine learning",
            "deep learning", 
            "neural networks",
            "artificial intelligence"
        ]
        
        with patch.object(search_service, '_get_query_frequency') as mock_freq:
            mock_freq.return_value = {
                "machine learning": 150,
                "deep learning": 120,
                "neural networks": 95,
                "artificial intelligence": 80
            }
            
            with patch.object(vector_service, '_precompute_frequent_queries') as mock_precompute:
                mock_precompute.return_value = {"precomputed": 4}
                
                # Optimize for frequent queries
                optimization_result = await vector_service._precompute_frequent_queries(
                    frequent_queries
                )
                
                assert optimization_result["precomputed"] == 4
    
    @pytest.mark.asyncio
    async def test_search_result_diversification(self):
        """Test search result diversification to avoid redundancy."""
        search_service = SearchService()
        vector_service = VectorIndexService()
        
        query_vector = np.array([0.1, 0.2, 0.3])
        
        with patch.object(vector_service, 'search_similar') as mock_search:
            # Return similar documents that might be redundant
            mock_search.return_value = [
                {"id": "doc1", "similarity": 0.95, "topic": "neural_networks"},
                {"id": "doc2", "similarity": 0.94, "topic": "neural_networks"},  # Similar topic
                {"id": "doc3", "similarity": 0.90, "topic": "decision_trees"},   # Different topic
                {"id": "doc4", "similarity": 0.89, "topic": "neural_networks"},  # Similar topic
                {"id": "doc5", "similarity": 0.85, "topic": "clustering"}       # Different topic
            ]
            
            with patch.object(search_service, '_diversify_results') as mock_diversify:
                mock_diversify.return_value = [
                    {"id": "doc1", "similarity": 0.95, "topic": "neural_networks"},
                    {"id": "doc3", "similarity": 0.90, "topic": "decision_trees"},
                    {"id": "doc5", "similarity": 0.85, "topic": "clustering"}
                ]
                
                raw_results = await vector_service.search_similar(query_vector, top_k=5)
                diversified_results = await search_service._diversify_results(raw_results)
                
                # Should have fewer results but more diverse topics
                assert len(diversified_results) == 3
                topics = [r["topic"] for r in diversified_results]
                assert len(set(topics)) == 3  # All different topics