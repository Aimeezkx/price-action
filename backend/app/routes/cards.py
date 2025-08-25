# app/routes/cards.py
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

try:
    from app.core.database import get_async_db
except ImportError:
    # Fallback if database module not available
    def get_async_db():
        return None

router = APIRouter(prefix="/api", tags=["cards"])

class Card(BaseModel):
    id: int
    front: str
    back: str
    deck: Optional[str] = None
    due_at: Optional[datetime] = None

async def fetch_cards(db: Optional[AsyncSession] = None):
    # 尝试从 Postgres 读；库/表不存在就返回空列表，避免 500
    if not db:
        return []
    
    try:
        result = await db.execute(text("""
            SELECT id, front, back, deck, due_at
            FROM cards
            ORDER BY id DESC
            LIMIT 200
        """))
        rows = result.fetchall()
        return [Card(
            id=row[0],
            front=row[1],
            back=row[2],
            deck=row[3],
            due_at=row[4]
        ) for row in rows]
    except Exception:
        return []

@router.get("/cards", response_model=List[Card])
async def list_cards(db: AsyncSession = Depends(get_async_db)):
    return await fetch_cards(db)

@router.get("/review/today", response_model=List[Card])
async def review_today(db: AsyncSession = Depends(get_async_db)):
    # 取今天应复习的卡（due_at <= now），如果没有表/数据就返回空
    if not db:
        return []
    
    try:
        result = await db.execute(text("""
            SELECT id, front, back, deck, due_at
            FROM cards
            WHERE due_at IS NOT NULL AND due_at <= NOW()
            ORDER BY due_at ASC
            LIMIT 200
        """))
        rows = result.fetchall()
        return [Card(
            id=row[0],
            front=row[1],
            back=row[2],
            deck=row[3],
            due_at=row[4]
        ) for row in rows]
    except Exception:
        return []