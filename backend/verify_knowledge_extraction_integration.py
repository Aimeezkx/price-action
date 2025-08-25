#!/usr/bin/env python3
"""
Final verification that knowledge extraction is properly integrated into the pipeline.
This test verifies Task 12 completion.
"""

import asyncio
import sys
from pathlib import Path
from uuid import uuid4

# Add the backend directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.document_processing_pipeline import DocumentProcessingPipeline
from app.services.knowledge_extraction_service import KnowledgeExtractionService
from app.models.knowledge import KnowledgeType


async def main():
    """Verify knowledge extraction integration."""
    
    print("Verifying Knowledge Extraction Integration (Task 12)")
    print("=" * 55)
    
    try:
        # 1. Initialize pipeline
        pipeline = DocumentProcessingPipeline()
        print("✅ Pipeline initialized successfully")
        
        # 2. Verify knowledge extraction service is integrated
        assert hasattr(pipeline, 'knowledge_extraction'), "Pipeline missing knowledge extraction service"
        assert isinstance(pipeline.knowledge_extraction, KnowledgeExtractionService), "Wrong service type"
        print("✅ Knowledge extraction service properly integrated")
        
        # 3. Test with sample content
        mock_chapter = type('MockChapter', (), {
            'id': uuid4(),
            'content': """
            Machine learning is a method of data analysis that automates analytical model building.
            It is a branch of artificial intelligence based on the idea that systems can learn from data.
            
            For example, neural networks are used in image recognition systems.
            
            The training process involves several steps: data preparation, model training, and evaluation.
            """,
            'title': 'ML Fundamentals',
            'page_start': 1,
            'page_end': 1
        })()
        
        # 4. Test text segmentation
        segments = await pipeline.text_segmentation.segment_text(
            mock_chapter.content, str(mock_chapter.id), 1
        )
        assert len(segments) > 0, "No segments created"
        print(f"✅ Text segmentation working: {len(segments)} segments")
        
        # 5. Test knowledge extraction
        knowledge_points = await pipeline.knowledge_extraction.extract_knowledge_from_segments(
            segments, str(mock_chapter.id)
        )
        assert len(knowledge_points) > 0, "No knowledge points extracted"
        print(f"✅ Knowledge extraction working: {len(knowledge_points)} knowledge points")
        
        # 6. Verify knowledge point structure
        for kp in knowledge_points:
            assert hasattr(kp, 'text') and kp.text, "Missing text"
            assert hasattr(kp, 'kind') and isinstance(kp.kind, KnowledgeType), "Missing/invalid kind"
            assert hasattr(kp, 'entities') and isinstance(kp.entities, list), "Missing/invalid entities"
            assert hasattr(kp, 'anchors') and isinstance(kp.anchors, dict), "Missing/invalid anchors"
            assert hasattr(kp, 'confidence') and 0.0 <= kp.confidence <= 1.0, "Missing/invalid confidence"
        print("✅ Knowledge points have correct structure")
        
        # 7. Test pipeline integration
        mock_session = type('MockSession', (), {
            'add': lambda self, obj: None,
            'commit': lambda self: asyncio.create_task(asyncio.sleep(0)),
            'rollback': lambda self: asyncio.create_task(asyncio.sleep(0))
        })()
        
        processed_knowledge = await pipeline._process_chapter(mock_session, mock_chapter)
        assert len(processed_knowledge) > 0, "Pipeline integration failed"
        print(f"✅ Pipeline integration working: {len(processed_knowledge)} knowledge points processed")
        
        # 8. Verify entity extraction
        all_entities = []
        for kp in knowledge_points:
            all_entities.extend(kp.entities)
        unique_entities = list(set(all_entities))
        assert len(unique_entities) > 0, "No entities extracted"
        print(f"✅ Entity extraction working: {len(unique_entities)} unique entities")
        
        # 9. Verify knowledge classification
        types_found = set(kp.kind for kp in knowledge_points)
        assert len(types_found) > 0, "No knowledge types classified"
        print(f"✅ Knowledge classification working: {[t.value for t in types_found]}")
        
        print("\n" + "=" * 55)
        print("🎉 TASK 12 COMPLETED SUCCESSFULLY!")
        print("\n✅ All requirements implemented:")
        print("   • Knowledge extraction service integrated into pipeline")
        print("   • Chapter and structure extraction working")
        print("   • Entity recognition and classification implemented")
        print("   • Knowledge points stored with proper data structure")
        print("\nThe knowledge extraction service is now fully connected")
        print("to the document processing pipeline.")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Verification failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)