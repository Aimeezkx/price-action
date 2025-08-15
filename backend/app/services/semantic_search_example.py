"""
Example usage of semantic search and embedding functionality
"""

import asyncio
import logging
from sqlalchemy.orm import Session
from typing import List

from ..core.database import SessionLocal
from ..models.knowledge import Knowledge, KnowledgeType
from ..models.document import Chapter, Document
from .embedding_service import embedding_service
from .search_service import search_service, SearchType, SearchFilters
from .vector_index_service import vector_index_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def create_sample_data(db: Session) -> dict:
    """Create sample data for demonstration"""
    logger.info("Creating sample data...")
    
    # Create a sample document
    document = Document(
        filename="ai_textbook.pdf",
        file_type="pdf",
        file_path="/tmp/ai_textbook.pdf",
        file_size=2048000,
        status="COMPLETED",
        doc_metadata={"pages": 300, "language": "en"}
    )
    db.add(document)
    db.flush()
    
    # Create chapters
    chapters = [
        Chapter(
            document_id=document.id,
            title="Introduction to Artificial Intelligence",
            level=1,
            order_index=1,
            page_start=1,
            page_end=25,
            content="This chapter provides an overview of artificial intelligence and its applications."
        ),
        Chapter(
            document_id=document.id,
            title="Machine Learning Fundamentals",
            level=1,
            order_index=2,
            page_start=26,
            page_end=75,
            content="This chapter covers the basics of machine learning algorithms and techniques."
        ),
        Chapter(
            document_id=document.id,
            title="Deep Learning and Neural Networks",
            level=1,
            order_index=3,
            page_start=76,
            page_end=150,
            content="This chapter explores deep learning architectures and neural network models."
        )
    ]
    
    db.add_all(chapters)
    db.flush()
    
    # Create knowledge points
    knowledge_points = [
        Knowledge(
            chapter_id=chapters[0].id,
            kind=KnowledgeType.DEFINITION,
            text="Artificial Intelligence (AI) is the simulation of human intelligence in machines that are programmed to think and learn like humans.",
            entities=["artificial intelligence", "AI", "human intelligence", "machines"],
            anchors={"page": 5, "chapter": "Introduction", "position": 1},
            confidence_score=0.95
        ),
        Knowledge(
            chapter_id=chapters[0].id,
            kind=KnowledgeType.FACT,
            text="The term 'artificial intelligence' was first coined by John McCarthy in 1956 at the Dartmouth Conference.",
            entities=["John McCarthy", "1956", "Dartmouth Conference"],
            anchors={"page": 8, "chapter": "Introduction", "position": 2},
            confidence_score=0.9
        ),
        Knowledge(
            chapter_id=chapters[1].id,
            kind=KnowledgeType.DEFINITION,
            text="Machine Learning is a subset of artificial intelligence that provides systems the ability to automatically learn and improve from experience without being explicitly programmed.",
            entities=["machine learning", "artificial intelligence", "systems", "experience"],
            anchors={"page": 30, "chapter": "Machine Learning", "position": 1},
            confidence_score=0.92
        ),
        Knowledge(
            chapter_id=chapters[1].id,
            kind=KnowledgeType.PROCESS,
            text="Supervised learning involves training a model on labeled data, where the algorithm learns to map inputs to correct outputs based on example input-output pairs.",
            entities=["supervised learning", "labeled data", "algorithm", "inputs", "outputs"],
            anchors={"page": 35, "chapter": "Machine Learning", "position": 2},
            confidence_score=0.88
        ),
        Knowledge(
            chapter_id=chapters[1].id,
            kind=KnowledgeType.EXAMPLE,
            text="Common supervised learning algorithms include linear regression for predicting continuous values and logistic regression for binary classification tasks.",
            entities=["linear regression", "logistic regression", "continuous values", "binary classification"],
            anchors={"page": 40, "chapter": "Machine Learning", "position": 3},
            confidence_score=0.85
        ),
        Knowledge(
            chapter_id=chapters[2].id,
            kind=KnowledgeType.DEFINITION,
            text="Deep Learning is a subset of machine learning that uses artificial neural networks with multiple layers to model and understand complex patterns in data.",
            entities=["deep learning", "machine learning", "neural networks", "multiple layers", "patterns"],
            anchors={"page": 80, "chapter": "Deep Learning", "position": 1},
            confidence_score=0.94
        ),
        Knowledge(
            chapter_id=chapters[2].id,
            kind=KnowledgeType.CONCEPT,
            text="Convolutional Neural Networks (CNNs) are particularly effective for image recognition tasks because they can detect spatial hierarchies of features.",
            entities=["convolutional neural networks", "CNNs", "image recognition", "spatial hierarchies", "features"],
            anchors={"page": 95, "chapter": "Deep Learning", "position": 2},
            confidence_score=0.87
        ),
        Knowledge(
            chapter_id=chapters[2].id,
            kind=KnowledgeType.PROCESS,
            text="Backpropagation is the algorithm used to train neural networks by calculating gradients of the loss function and updating weights to minimize prediction errors.",
            entities=["backpropagation", "neural networks", "gradients", "loss function", "weights"],
            anchors={"page": 110, "chapter": "Deep Learning", "position": 3},
            confidence_score=0.91
        )
    ]
    
    db.add_all(knowledge_points)
    db.commit()
    
    logger.info(f"Created sample data: 1 document, {len(chapters)} chapters, {len(knowledge_points)} knowledge points")
    
    return {
        "document": document,
        "chapters": chapters,
        "knowledge_points": knowledge_points
    }


async def demonstrate_embedding_generation(db: Session, knowledge_points: List[Knowledge]):
    """Demonstrate embedding generation"""
    logger.info("\n=== Embedding Generation Demo ===")
    
    # Generate embeddings for all knowledge points
    logger.info("Generating embeddings for knowledge points...")
    updated_count = await embedding_service.update_knowledge_embeddings(db)
    logger.info(f"Generated embeddings for {updated_count} knowledge points")
    
    # Demonstrate single embedding generation
    sample_text = "What is the difference between AI and machine learning?"
    embedding = embedding_service.generate_embedding(sample_text)
    logger.info(f"Generated embedding for sample text (dimension: {len(embedding)})")
    
    # Demonstrate batch embedding generation
    sample_texts = [
        "Neural networks are inspired by biological neurons",
        "Supervised learning requires labeled training data",
        "Deep learning uses multiple hidden layers"
    ]
    batch_embeddings = embedding_service.generate_embeddings_batch(sample_texts)
    logger.info(f"Generated batch embeddings for {len(batch_embeddings)} texts")


async def demonstrate_similarity_search(db: Session):
    """Demonstrate similarity-based search"""
    logger.info("\n=== Similarity Search Demo ===")
    
    # Search for similar knowledge points
    query_text = "What are neural networks and how do they work?"
    similar_knowledge = embedding_service.search_similar_knowledge(
        db=db,
        query_text=query_text,
        similarity_threshold=0.3,  # Lower threshold for demo
        limit=5
    )
    
    logger.info(f"Found {len(similar_knowledge)} similar knowledge points for: '{query_text}'")
    for i, (knowledge, similarity) in enumerate(similar_knowledge, 1):
        logger.info(f"{i}. Similarity: {similarity:.3f} | {knowledge.kind.value}")
        logger.info(f"   Text: {knowledge.text[:100]}...")
        logger.info(f"   Entities: {knowledge.entities}")


async def demonstrate_full_text_search(db: Session):
    """Demonstrate full-text search"""
    logger.info("\n=== Full-Text Search Demo ===")
    
    queries = [
        "machine learning algorithms",
        "neural networks",
        "artificial intelligence definition"
    ]
    
    for query in queries:
        results = search_service.search(
            db=db,
            query=query,
            search_type=SearchType.FULL_TEXT,
            limit=3
        )
        
        logger.info(f"\nFull-text search results for: '{query}'")
        logger.info(f"Found {len(results)} results")
        
        for i, result in enumerate(results, 1):
            logger.info(f"{i}. Score: {result.score:.3f} | Type: {result.type}")
            logger.info(f"   Title: {result.title}")
            logger.info(f"   Snippet: {result.snippet}")


async def demonstrate_semantic_search(db: Session):
    """Demonstrate semantic search"""
    logger.info("\n=== Semantic Search Demo ===")
    
    queries = [
        "computer intelligence and learning systems",
        "training models with examples and labels",
        "multi-layer networks for pattern recognition"
    ]
    
    for query in queries:
        results = search_service.search(
            db=db,
            query=query,
            search_type=SearchType.SEMANTIC,
            similarity_threshold=0.2,  # Lower threshold for demo
            limit=3
        )
        
        logger.info(f"\nSemantic search results for: '{query}'")
        logger.info(f"Found {len(results)} results")
        
        for i, result in enumerate(results, 1):
            logger.info(f"{i}. Score: {result.score:.3f} | Type: {result.type}")
            logger.info(f"   Title: {result.title}")
            logger.info(f"   Snippet: {result.snippet}")


async def demonstrate_hybrid_search(db: Session):
    """Demonstrate hybrid search"""
    logger.info("\n=== Hybrid Search Demo ===")
    
    query = "deep learning neural networks"
    results = search_service.search(
        db=db,
        query=query,
        search_type=SearchType.HYBRID,
        limit=5
    )
    
    logger.info(f"Hybrid search results for: '{query}'")
    logger.info(f"Found {len(results)} results")
    
    for i, result in enumerate(results, 1):
        logger.info(f"{i}. Score: {result.score:.3f} | Type: {result.type}")
        logger.info(f"   Title: {result.title}")
        logger.info(f"   Snippet: {result.snippet}")


async def demonstrate_filtered_search(db: Session, chapters: List[Chapter]):
    """Demonstrate search with filters"""
    logger.info("\n=== Filtered Search Demo ===")
    
    # Search only in specific chapters
    filters = SearchFilters(
        chapter_ids=[str(chapters[1].id)],  # Only Machine Learning chapter
        knowledge_types=[KnowledgeType.DEFINITION, KnowledgeType.PROCESS]
    )
    
    results = search_service.search(
        db=db,
        query="learning",
        filters=filters,
        limit=5
    )
    
    logger.info("Filtered search results (Machine Learning chapter, definitions and processes only):")
    logger.info(f"Found {len(results)} results")
    
    for i, result in enumerate(results, 1):
        logger.info(f"{i}. Score: {result.score:.3f} | Type: {result.type}")
        logger.info(f"   Title: {result.title}")
        logger.info(f"   Metadata: {result.metadata}")


async def demonstrate_duplicate_detection(db: Session):
    """Demonstrate duplicate detection"""
    logger.info("\n=== Duplicate Detection Demo ===")
    
    # Add a similar knowledge point to create a potential duplicate
    duplicate_knowledge = Knowledge(
        chapter_id=db.query(Chapter).first().id,
        kind=KnowledgeType.DEFINITION,
        text="AI is the simulation of human intelligence in machines that are designed to think and learn like humans.",  # Very similar to existing
        entities=["AI", "human intelligence", "machines"],
        anchors={"page": 6, "chapter": "Introduction", "position": 4},
        confidence_score=0.8
    )
    db.add(duplicate_knowledge)
    db.commit()
    
    # Generate embedding for the new knowledge point
    await embedding_service.update_knowledge_embeddings(db, [str(duplicate_knowledge.id)])
    
    # Find duplicates
    duplicates = embedding_service.find_duplicate_knowledge(
        db=db,
        similarity_threshold=0.8
    )
    
    logger.info(f"Found {len(duplicates)} potential duplicate pairs")
    
    for i, (kp1, kp2, similarity) in enumerate(duplicates, 1):
        logger.info(f"{i}. Similarity: {similarity:.3f}")
        logger.info(f"   Text 1: {kp1.text[:80]}...")
        logger.info(f"   Text 2: {kp2.text[:80]}...")


async def demonstrate_search_suggestions(db: Session):
    """Demonstrate search suggestions"""
    logger.info("\n=== Search Suggestions Demo ===")
    
    queries = ["mach", "neur", "learn"]
    
    for query in queries:
        suggestions = search_service.get_search_suggestions(
            db=db,
            query=query,
            limit=5
        )
        
        logger.info(f"Suggestions for '{query}': {suggestions}")


async def demonstrate_performance_analysis(db: Session):
    """Demonstrate performance analysis"""
    logger.info("\n=== Performance Analysis Demo ===")
    
    # Analyze vector search performance
    analysis = vector_index_service.analyze_vector_performance(db)
    logger.info("Vector search performance analysis:")
    
    if "error" in analysis:
        logger.info(f"Analysis error (expected with SQLite): {analysis['error']}")
    else:
        logger.info(f"Total knowledge points: {analysis.get('total_knowledge', 0)}")
        logger.info(f"Embedded knowledge points: {analysis.get('embedded_knowledge', 0)}")
        logger.info(f"Embedding coverage: {analysis.get('embedding_coverage', 0):.1f}%")
        
        if analysis.get('recommendations'):
            logger.info("Recommendations:")
            for rec in analysis['recommendations']:
                logger.info(f"  - {rec}")


async def main():
    """Main demonstration function"""
    logger.info("Starting Semantic Search and Embedding Demo")
    
    # Create database session
    db = SessionLocal()
    
    try:
        # Create sample data
        sample_data = await create_sample_data(db)
        
        # Run demonstrations
        await demonstrate_embedding_generation(db, sample_data["knowledge_points"])
        await demonstrate_similarity_search(db)
        await demonstrate_full_text_search(db)
        await demonstrate_semantic_search(db)
        await demonstrate_hybrid_search(db)
        await demonstrate_filtered_search(db, sample_data["chapters"])
        await demonstrate_duplicate_detection(db)
        await demonstrate_search_suggestions(db)
        await demonstrate_performance_analysis(db)
        
        logger.info("\n=== Demo Complete ===")
        logger.info("All semantic search and embedding features demonstrated successfully!")
        
    except Exception as e:
        logger.error(f"Demo failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(main())