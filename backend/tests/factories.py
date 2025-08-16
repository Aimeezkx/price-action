"""
Factory classes for creating test data using factory_boy.
"""
import factory
from factory import Faker, SubFactory
from datetime import datetime, timedelta
from uuid import uuid4

from app.models.document import Document, Chapter, Figure
from app.models.knowledge import Knowledge
from app.models.learning import Card, SRS


class DocumentFactory(factory.Factory):
    """Factory for creating test documents."""
    
    class Meta:
        model = Document
    
    id = factory.LazyFunction(uuid4)
    filename = Faker('file_name', extension='pdf')
    file_type = 'pdf'
    status = 'completed'
    metadata = factory.LazyFunction(lambda: {
        'pages': factory.Faker('random_int', min=1, max=100).generate(),
        'size': factory.Faker('random_int', min=1000, max=10000000).generate(),
    })
    created_at = Faker('date_time_this_year')


class ChapterFactory(factory.Factory):
    """Factory for creating test chapters."""
    
    class Meta:
        model = Chapter
    
    id = factory.LazyFunction(uuid4)
    document_id = factory.LazyFunction(uuid4)
    title = Faker('sentence', nb_words=4)
    level = Faker('random_int', min=1, max=3)
    order_index = Faker('random_int', min=1, max=20)
    page_start = Faker('random_int', min=1, max=50)
    page_end = factory.LazyAttribute(lambda obj: obj.page_start + Faker('random_int', min=1, max=10).generate())


class FigureFactory(factory.Factory):
    """Factory for creating test figures."""
    
    class Meta:
        model = Figure
    
    id = factory.LazyFunction(uuid4)
    chapter_id = factory.LazyFunction(uuid4)
    image_path = Faker('file_path', depth=2, extension='png')
    caption = Faker('sentence', nb_words=8)
    page_number = Faker('random_int', min=1, max=100)
    bbox = factory.LazyFunction(lambda: {
        'x': factory.Faker('random_int', min=0, max=500).generate(),
        'y': factory.Faker('random_int', min=0, max=700).generate(),
        'width': factory.Faker('random_int', min=100, max=400).generate(),
        'height': factory.Faker('random_int', min=100, max=300).generate(),
    })


class KnowledgeFactory(factory.Factory):
    """Factory for creating test knowledge points."""
    
    class Meta:
        model = Knowledge
    
    id = factory.LazyFunction(uuid4)
    chapter_id = factory.LazyFunction(uuid4)
    kind = Faker('random_element', elements=['definition', 'fact', 'theorem', 'process', 'example'])
    text = Faker('paragraph', nb_sentences=3)
    entities = factory.LazyFunction(lambda: [
        factory.Faker('word').generate() for _ in range(factory.Faker('random_int', min=1, max=5).generate())
    ])
    anchors = factory.LazyFunction(lambda: {
        'page': factory.Faker('random_int', min=1, max=100).generate(),
        'chapter': factory.Faker('random_int', min=1, max=10).generate(),
        'position': factory.Faker('random_int', min=0, max=1000).generate(),
    })
    embedding = factory.LazyFunction(lambda: [factory.Faker('pyfloat', min_value=-1, max_value=1).generate() for _ in range(384)])


class CardFactory(factory.Factory):
    """Factory for creating test flashcards."""
    
    class Meta:
        model = Card
    
    id = factory.LazyFunction(uuid4)
    knowledge_id = factory.LazyFunction(uuid4)
    card_type = Faker('random_element', elements=['qa', 'cloze', 'image_hotspot'])
    front = Faker('sentence', nb_words=8)
    back = Faker('paragraph', nb_sentences=2)
    difficulty = Faker('pyfloat', min_value=0.1, max_value=1.0)
    metadata = factory.LazyFunction(lambda: {})


class SRSFactory(factory.Factory):
    """Factory for creating test SRS states."""
    
    class Meta:
        model = SRS
    
    id = factory.LazyFunction(uuid4)
    card_id = factory.LazyFunction(uuid4)
    user_id = factory.LazyFunction(uuid4)
    ease_factor = Faker('pyfloat', min_value=1.3, max_value=3.0)
    interval = Faker('random_int', min=1, max=365)
    repetitions = Faker('random_int', min=0, max=10)
    due_date = Faker('date_time_between', start_date='-30d', end_date='+30d')
    last_reviewed = Faker('date_time_this_month')


# Specialized factories for different test scenarios
class CompletedDocumentFactory(DocumentFactory):
    """Factory for completed documents with chapters and knowledge."""
    
    status = 'completed'
    
    @factory.post_generation
    def chapters(self, create, extracted, **kwargs):
        if not create:
            return
        
        if extracted:
            for chapter_data in extracted:
                ChapterFactory(document_id=self.id, **chapter_data)


class ProcessingDocumentFactory(DocumentFactory):
    """Factory for documents currently being processed."""
    
    status = 'processing'
    created_at = factory.LazyFunction(lambda: datetime.now() - timedelta(minutes=5))


class FailedDocumentFactory(DocumentFactory):
    """Factory for failed document processing."""
    
    status = 'failed'
    metadata = factory.LazyFunction(lambda: {
        'error': 'Processing failed',
        'error_code': 'PARSE_ERROR'
    })


class DefinitionKnowledgeFactory(KnowledgeFactory):
    """Factory for definition-type knowledge points."""
    
    kind = 'definition'
    text = factory.LazyAttribute(lambda obj: f"{obj.entities[0]} is defined as a concept that...")


class FactKnowledgeFactory(KnowledgeFactory):
    """Factory for fact-type knowledge points."""
    
    kind = 'fact'
    text = Faker('sentence', nb_words=12)


class QACardFactory(CardFactory):
    """Factory for Q&A type cards."""
    
    card_type = 'qa'
    front = factory.LazyAttribute(lambda obj: f"What is {obj.knowledge.entities[0]}?")
    back = factory.LazyAttribute(lambda obj: obj.knowledge.text)


class ClozeCardFactory(CardFactory):
    """Factory for cloze deletion cards."""
    
    card_type = 'cloze'
    metadata = factory.LazyFunction(lambda: {
        'blanks': ['term1', 'term2'],
        'original_text': 'The term1 is related to term2 in this context.'
    })


class ImageHotspotCardFactory(CardFactory):
    """Factory for image hotspot cards."""
    
    card_type = 'image_hotspot'
    metadata = factory.LazyFunction(lambda: {
        'hotspots': [
            {'x': 100, 'y': 150, 'width': 50, 'height': 30, 'label': 'Feature 1'},
            {'x': 200, 'y': 250, 'width': 60, 'height': 40, 'label': 'Feature 2'},
        ]
    })


class DueCardSRSFactory(SRSFactory):
    """Factory for cards that are due for review."""
    
    due_date = factory.LazyFunction(lambda: datetime.now() - timedelta(hours=1))
    interval = 1
    repetitions = 0


class OverdueCardSRSFactory(SRSFactory):
    """Factory for overdue cards."""
    
    due_date = factory.LazyFunction(lambda: datetime.now() - timedelta(days=3))
    interval = 7
    repetitions = 2