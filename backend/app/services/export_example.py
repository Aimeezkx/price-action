"""
Example usage of export service
"""

import asyncio
from datetime import datetime, timedelta
from uuid import uuid4
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..models.document import Document, Chapter, Figure, ProcessingStatus
from ..models.knowledge import Knowledge, KnowledgeType
from ..models.learning import Card, SRS, CardType
from .export_service import ExportService


async def create_sample_data(db: Session):
    """Create sample data for export demonstration"""
    print("Creating sample data...")
    
    # Create document
    document = Document(
        id=uuid4(),
        filename="sample_textbook.pdf",
        file_type="pdf",
        file_path="/uploads/sample_textbook.pdf",
        file_size=5242880,  # 5MB
        status=ProcessingStatus.COMPLETED,
        doc_metadata={"pages": 25, "language": "en"}
    )
    db.add(document)
    
    # Create chapters
    chapters_data = [
        {"title": "Introduction to Machine Learning", "level": 1, "order": 1, "pages": (1, 5)},
        {"title": "Supervised Learning", "level": 1, "order": 2, "pages": (6, 15)},
        {"title": "Neural Networks", "level": 2, "order": 3, "pages": (16, 20)},
        {"title": "Deep Learning", "level": 2, "order": 4, "pages": (21, 25)}
    ]
    
    chapters = []
    for ch_data in chapters_data:
        chapter = Chapter(
            id=uuid4(),
            document_id=document.id,
            title=ch_data["title"],
            level=ch_data["level"],
            order_index=ch_data["order"],
            page_start=ch_data["pages"][0],
            page_end=ch_data["pages"][1],
            content=f"Content for {ch_data['title']}"
        )
        db.add(chapter)
        chapters.append(chapter)
    
    # Create figures
    figures_data = [
        {"chapter": 0, "path": "/images/ml_overview.png", "caption": "Machine Learning Overview Diagram", "page": 3},
        {"chapter": 1, "path": "/images/supervised_flow.png", "caption": "Supervised Learning Workflow", "page": 8},
        {"chapter": 2, "path": "/images/neural_network.png", "caption": "Neural Network Architecture", "page": 17},
        {"chapter": 3, "path": "/images/deep_learning.png", "caption": "Deep Learning Model Structure", "page": 22}
    ]
    
    figures = []
    for fig_data in figures_data:
        figure = Figure(
            id=uuid4(),
            chapter_id=chapters[fig_data["chapter"]].id,
            image_path=fig_data["path"],
            caption=fig_data["caption"],
            page_number=fig_data["page"],
            bbox={"x": 100, "y": 150, "width": 400, "height": 300},
            image_format="png"
        )
        db.add(figure)
        figures.append(figure)
    
    # Create knowledge points
    knowledge_data = [
        {
            "chapter": 0,
            "kind": KnowledgeType.DEFINITION,
            "text": "Machine Learning is a subset of artificial intelligence that enables computers to learn and make decisions from data without being explicitly programmed.",
            "entities": ["machine learning", "artificial intelligence", "data"],
            "page": 2
        },
        {
            "chapter": 1,
            "kind": KnowledgeType.CONCEPT,
            "text": "Supervised learning uses labeled training data to learn a mapping function from input variables to output variables.",
            "entities": ["supervised learning", "labeled data", "mapping function"],
            "page": 7
        },
        {
            "chapter": 1,
            "kind": KnowledgeType.EXAMPLE,
            "text": "Linear regression is a supervised learning algorithm used to predict continuous numerical values based on input features.",
            "entities": ["linear regression", "continuous values", "input features"],
            "page": 10
        },
        {
            "chapter": 2,
            "kind": KnowledgeType.DEFINITION,
            "text": "A neural network is a computing system inspired by biological neural networks, consisting of interconnected nodes (neurons) that process information.",
            "entities": ["neural network", "neurons", "nodes"],
            "page": 16
        },
        {
            "chapter": 2,
            "kind": KnowledgeType.PROCESS,
            "text": "Backpropagation is the algorithm used to train neural networks by calculating gradients and updating weights to minimize error.",
            "entities": ["backpropagation", "gradients", "weights"],
            "page": 18
        },
        {
            "chapter": 3,
            "kind": KnowledgeType.THEOREM,
            "text": "The Universal Approximation Theorem states that a neural network with at least one hidden layer can approximate any continuous function.",
            "entities": ["Universal Approximation Theorem", "hidden layer", "continuous function"],
            "page": 23
        }
    ]
    
    knowledge_points = []
    for kp_data in knowledge_data:
        knowledge = Knowledge(
            id=uuid4(),
            chapter_id=chapters[kp_data["chapter"]].id,
            kind=kp_data["kind"],
            text=kp_data["text"],
            entities=kp_data["entities"],
            anchors={"page": kp_data["page"], "chapter": chapters[kp_data["chapter"]].title, "position": 100},
            confidence_score=0.85 + (len(kp_data["entities"]) * 0.03)  # Vary confidence
        )
        db.add(knowledge)
        knowledge_points.append(knowledge)
    
    # Create cards for each knowledge point
    cards = []
    for i, knowledge in enumerate(knowledge_points):
        # Create Q&A card
        if knowledge.kind in [KnowledgeType.DEFINITION, KnowledgeType.CONCEPT, KnowledgeType.THEOREM]:
            qa_card = Card(
                id=uuid4(),
                knowledge_id=knowledge.id,
                card_type=CardType.QA,
                front=f"What is {knowledge.entities[0] if knowledge.entities else 'this concept'}?",
                back=knowledge.text,
                difficulty=1.5 + (i % 3) * 0.5,  # Vary difficulty
                card_metadata={}
            )
            db.add(qa_card)
            cards.append(qa_card)
        
        # Create cloze card if there are entities
        if knowledge.entities and len(knowledge.entities) >= 2:
            # Create cloze deletions for up to 3 entities
            cloze_text = knowledge.text
            blanks = knowledge.entities[:3]
            
            for j, entity in enumerate(blanks, 1):
                cloze_text = cloze_text.replace(entity, f"{{{{c{j}::{entity}}}}}", 1)
            
            cloze_card = Card(
                id=uuid4(),
                knowledge_id=knowledge.id,
                card_type=CardType.CLOZE,
                front=cloze_text,
                back=knowledge.text,
                difficulty=2.0 + (i % 3) * 0.3,
                card_metadata={"blanks": blanks}
            )
            db.add(cloze_card)
            cards.append(cloze_card)
    
    # Create image hotspot cards for figures
    for i, figure in enumerate(figures):
        # Find related knowledge point
        related_knowledge = next(
            (kp for kp in knowledge_points if kp.chapter_id == figure.chapter_id),
            None
        )
        
        if related_knowledge:
            image_card = Card(
                id=uuid4(),
                knowledge_id=related_knowledge.id,
                card_type=CardType.IMAGE_HOTSPOT,
                front=figure.image_path,
                back=figure.caption,
                difficulty=1.2 + (i * 0.2),
                card_metadata={
                    "hotspots": [f"region_{j}" for j in range(1, 4)],  # 3 hotspot regions
                    "image_id": str(figure.id)
                }
            )
            db.add(image_card)
            cards.append(image_card)
    
    # Create SRS records for some cards (simulate learning progress)
    for i, card in enumerate(cards[:len(cards)//2]):  # Half the cards have SRS data
        srs = SRS(
            id=uuid4(),
            card_id=card.id,
            ease_factor=2.5 - (i % 5) * 0.1,  # Vary ease factor
            interval=max(1, i % 7),  # Vary interval
            repetitions=i % 4,  # Vary repetitions
            due_date=datetime.utcnow() + timedelta(days=i % 10),
            last_reviewed=datetime.utcnow() - timedelta(hours=i * 6),
            last_grade=3 + (i % 3)  # Grades 3-5
        )
        db.add(srs)
    
    db.commit()
    
    print(f"Created sample data:")
    print(f"- 1 document: {document.filename}")
    print(f"- {len(chapters)} chapters")
    print(f"- {len(figures)} figures")
    print(f"- {len(knowledge_points)} knowledge points")
    print(f"- {len(cards)} cards")
    print(f"- {len(cards)//2} SRS records")
    
    return document.id


async def demonstrate_exports(db: Session, document_id):
    """Demonstrate different export formats"""
    export_service = ExportService(db)
    
    print("\n" + "="*60)
    print("EXPORT DEMONSTRATIONS")
    print("="*60)
    
    # 1. Anki CSV Export
    print("\n1. ANKI CSV EXPORT")
    print("-" * 30)
    
    anki_csv = export_service.export_anki_csv(document_id=document_id)
    
    # Show first few lines
    lines = anki_csv.split('\n')
    print(f"Total lines: {len(lines)}")
    print("First 3 lines:")
    for i, line in enumerate(lines[:3]):
        print(f"  {i+1}: {line[:100]}{'...' if len(line) > 100 else ''}")
    
    # Save to file
    with open("anki_export_sample.csv", "w", encoding="utf-8") as f:
        f.write(anki_csv)
    print("✓ Saved to: anki_export_sample.csv")
    
    # 2. Notion CSV Export
    print("\n2. NOTION CSV EXPORT")
    print("-" * 30)
    
    notion_csv = export_service.export_notion_csv(document_id=document_id)
    
    lines = notion_csv.split('\n')
    print(f"Total lines: {len(lines)}")
    print("First 3 lines:")
    for i, line in enumerate(lines[:3]):
        print(f"  {i+1}: {line[:100]}{'...' if len(line) > 100 else ''}")
    
    # Save to file
    with open("notion_export_sample.csv", "w", encoding="utf-8") as f:
        f.write(notion_csv)
    print("✓ Saved to: notion_export_sample.csv")
    
    # 3. JSONL Backup Export
    print("\n3. JSONL BACKUP EXPORT")
    print("-" * 30)
    
    jsonl_backup = export_service.export_jsonl_backup(document_id=document_id)
    
    lines = jsonl_backup.strip().split('\n')
    print(f"Total documents: {len(lines)}")
    
    # Parse first document to show structure
    if lines:
        doc_data = eval(lines[0])  # Using eval for demo - use json.loads in production
        metadata = doc_data.get('export_metadata', {})
        print(f"Export metadata:")
        print(f"  - Export date: {metadata.get('export_date', 'N/A')}")
        print(f"  - Total chapters: {metadata.get('total_chapters', 0)}")
        print(f"  - Total figures: {metadata.get('total_figures', 0)}")
        print(f"  - Total knowledge: {metadata.get('total_knowledge', 0)}")
        print(f"  - Total cards: {metadata.get('total_cards', 0)}")
    
    # Save to file
    with open("backup_sample.jsonl", "w", encoding="utf-8") as f:
        f.write(jsonl_backup)
    print("✓ Saved to: backup_sample.jsonl")
    
    # 4. Filtered Export (by chapter)
    print("\n4. FILTERED EXPORT (First Chapter Only)")
    print("-" * 30)
    
    # Get first chapter ID
    from ..models.document import Chapter
    first_chapter = db.query(Chapter).filter(Chapter.document_id == document_id).first()
    
    if first_chapter:
        filtered_csv = export_service.export_anki_csv(chapter_ids=[first_chapter.id])
        lines = filtered_csv.split('\n')
        print(f"Filtered export lines: {len(lines)}")
        print(f"Chapter: {first_chapter.title}")
        
        # Save to file
        with open("anki_filtered_sample.csv", "w", encoding="utf-8") as f:
            f.write(filtered_csv)
        print("✓ Saved to: anki_filtered_sample.csv")


async def demonstrate_import(db: Session):
    """Demonstrate JSONL import functionality"""
    print("\n5. JSONL IMPORT DEMONSTRATION")
    print("-" * 30)
    
    # Read the backup file we created
    try:
        with open("backup_sample.jsonl", "r", encoding="utf-8") as f:
            jsonl_content = f.read()
        
        export_service = ExportService(db)
        
        # Clear existing data first (for demo purposes)
        print("Clearing existing data...")
        db.query(SRS).delete()
        db.query(Card).delete()
        db.query(Knowledge).delete()
        db.query(Figure).delete()
        db.query(Chapter).delete()
        db.query(Document).delete()
        db.commit()
        
        # Import the data
        print("Importing data from backup...")
        result = export_service.import_jsonl_backup(jsonl_content)
        
        print("Import results:")
        print(f"  - Documents imported: {result['imported_documents']}")
        print(f"  - Chapters imported: {result['imported_chapters']}")
        print(f"  - Figures imported: {result['imported_figures']}")
        print(f"  - Knowledge imported: {result['imported_knowledge']}")
        print(f"  - Cards imported: {result['imported_cards']}")
        print(f"  - Errors: {len(result['errors'])}")
        
        if result['errors']:
            print("Errors encountered:")
            for error in result['errors'][:3]:  # Show first 3 errors
                print(f"    - {error}")
        
        print("✓ Import completed successfully!")
        
    except FileNotFoundError:
        print("❌ Backup file not found. Run export demonstration first.")


async def main():
    """Main demonstration function"""
    print("EXPORT SERVICE DEMONSTRATION")
    print("="*60)
    
    # Get database session
    db = next(get_db())
    
    try:
        # Create sample data
        document_id = await create_sample_data(db)
        
        # Demonstrate exports
        await demonstrate_exports(db, document_id)
        
        # Demonstrate import
        await demonstrate_import(db)
        
        print("\n" + "="*60)
        print("DEMONSTRATION COMPLETED")
        print("="*60)
        print("\nFiles created:")
        print("- anki_export_sample.csv")
        print("- notion_export_sample.csv") 
        print("- backup_sample.jsonl")
        print("- anki_filtered_sample.csv")
        print("\nYou can now:")
        print("1. Import anki_export_sample.csv into Anki")
        print("2. Import notion_export_sample.csv into Notion")
        print("3. Use backup_sample.jsonl for data restoration")
        
    except Exception as e:
        print(f"❌ Error during demonstration: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(main())