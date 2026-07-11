import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.core.database import SyncSessionAsyncAdapter


@pytest.mark.asyncio
async def test_sync_session_adapter_supports_worker_contract() -> None:
    engine = create_engine("sqlite:///:memory:")
    session_factory = sessionmaker(bind=engine)

    async with SyncSessionAsyncAdapter(session_factory()) as session:
        result = await session.execute(text("SELECT 1"))
        assert result.scalar_one() == 1
        await session.commit()
