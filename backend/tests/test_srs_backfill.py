from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.models.document import Chapter, Document, ProcessingStatus
from app.models.knowledge import Knowledge, KnowledgeType
from app.models.learning import Card, CardType, SRS
from app.services.srs_service import SRSService


def test_backfill_missing_srs_records_is_idempotent() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    try:
        document = Document(
            filename="study.md",
            file_type="markdown",
            file_path="study.md",
            file_size=10,
            status=ProcessingStatus.COMPLETED,
        )
        session.add(document)
        session.flush()
        chapter = Chapter(
            document_id=document.id,
            title="Chapter",
            level=1,
            order_index=0,
        )
        session.add(chapter)
        session.flush()
        knowledge = Knowledge(
            chapter_id=chapter.id,
            kind=KnowledgeType.CONCEPT,
            text="Price action",
        )
        session.add(knowledge)
        session.flush()
        session.add_all(
            [
                Card(
                    knowledge_id=knowledge.id,
                    card_type=CardType.QA,
                    front="Question",
                    back="Answer",
                ),
                Card(
                    knowledge_id=knowledge.id,
                    card_type=CardType.CLOZE,
                    front="Price [1]",
                    back="Price action",
                ),
            ]
        )
        session.commit()

        service = SRSService(session)
        assert service.backfill_missing_records() == 2
        assert service.backfill_missing_records() == 0
        assert session.query(SRS).count() == 2
    finally:
        session.close()
        engine.dispose()
