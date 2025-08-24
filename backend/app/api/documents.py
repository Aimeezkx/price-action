"""
Document upload and management API endpoints
"""

import os
import aiofiles
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, status, Query, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.database import get_async_db
from app.models.document import Document, ProcessingStatus, Chapter, Figure
from app.models.knowledge import Knowledge
from app.models.learning import Card, CardType, SRS
from app.core.config import settings
from app.services.document_service import DocumentService
from app.services.card_generation_service import CardGenerationService
from app.schemas.document import DocumentResponse, DocumentCreate
from app.utils.file_validation import validate_file
from app.utils.security import SecurityValidator, generate_secure_filename
from app.utils.access_control import AccessController, require_rate_limit, check_rate_limit
from app.utils.security import get_client_ip
from app.utils.logging import SecurityLogger
from app.utils.privacy_service import privacy_manager

router = APIRouter(prefix="/api", tags=["documents"])
security_logger = SecurityLogger(__name__)


@router.post("/ingest", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    request: Request,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_async_db)
) -> DocumentResponse:
    """
    Upload and queue a document for processing
    
    Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 11.1, 11.2, 11.3
    """
    # Get client IP for logging
    client_ip = get_client_ip(request)
    
    # Check rate limit
    if check_rate_limit(client_ip, "upload"):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Upload rate limit exceeded. Please try again later."
        )
    
    try:
        # Validate file with security checks
        file_type, safe_filename = await SecurityValidator.validate_upload_file(file)
        
        # Log upload attempt
        security_logger.log_file_upload(
            filename=file.filename or "unknown",
            file_size=file.size or 0,
            user_id=client_ip  # Using IP as user identifier for now
        )
        
        # Create document service
        doc_service = DocumentService(db)
        
        # Create document record and save file with secure filename
        document = await doc_service.create_document(file, safe_filename)
        
        # Queue for background processing
        await doc_service.queue_for_processing(document.id)
        
        # Log successful upload
        security_logger.log_security_event(
            "document_upload_success",
            {
                "document_id": str(document.id),
                "filename": file.filename,
                "file_type": file_type,
                "file_size": file.size,
                "client_ip": client_ip
            },
            "INFO"
        )
        
        return DocumentResponse.model_validate(document)
        
    except HTTPException:
        # Re-raise HTTP exceptions (validation errors, rate limits, etc.)
        raise
    except Exception as e:
        # Log security event for unexpected errors
        security_logger.log_security_event(
            "document_upload_error",
            {
                "filename": getattr(file, 'filename', 'unknown'),
                "error": str(e),
                "client_ip": client_ip
            },
            "ERROR"
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload document. Please try again."
        )


@router.get("/documents", response_model=List[DocumentResponse])
async def list_documents(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_async_db)
) -> List[DocumentResponse]:
    """List all documents with their processing status"""
    
    try:
        stmt = select(Document).offset(skip).limit(limit).order_by(Document.created_at.desc())
        result = await db.execute(stmt)
        documents = result.scalars().all()
        
        return [DocumentResponse.model_validate(doc) for doc in documents]
    except Exception as e:
        # Return empty list if there's an error
        return []


@router.get("/documents/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: UUID,
    db: AsyncSession = Depends(get_async_db)
) -> DocumentResponse:
    """Get document by ID"""
    
    stmt = select(Document).where(Document.id == document_id)
    result = await db.execute(stmt)
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    return DocumentResponse.model_validate(document)


@router.get("/doc/{document_id}", response_model=DocumentResponse)
async def get_document_by_id(
    document_id: UUID,
    db: AsyncSession = Depends(get_async_db)
) -> DocumentResponse:
    """
    Get document by ID
    
    Requirements: 1.1, 1.2 - Document management endpoints
    """
    
    stmt = select(Document).where(Document.id == document_id)
    result = await db.execute(stmt)
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    return DocumentResponse.model_validate(document)


@router.get("/documents/{document_id}/status")
async def get_document_status(
    document_id: UUID,
    db: AsyncSession = Depends(get_async_db)
) -> dict:
    """Get document processing status and progress"""
    
    stmt = select(Document).where(Document.id == document_id)
    result = await db.execute(stmt)
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    return {
        "document_id": document.id,
        "status": document.status,
        "filename": document.filename,
        "error_message": document.error_message,
        "created_at": document.created_at,
        "updated_at": document.updated_at
    }


@router.get("/doc/{document_id}/toc")
async def get_document_table_of_contents(
    document_id: UUID,
    db: AsyncSession = Depends(get_async_db)
) -> dict:
    """
    Get document table of contents (chapter structure)
    
    Requirements: 3.3 - Chapter structure and table of contents
    """
    
    # Verify document exists
    doc_stmt = select(Document).where(Document.id == document_id)
    doc_result = await db.execute(doc_stmt)
    document = doc_result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Get chapters with their structure
    chapters_stmt = (
        select(Chapter)
        .where(Chapter.document_id == document_id)
        .order_by(Chapter.order_index)
    )
    chapters_result = await db.execute(chapters_stmt)
    chapters = chapters_result.scalars().all()
    
    # Build hierarchical table of contents
    toc = {
        "document_id": document_id,
        "document_title": document.filename,
        "total_chapters": len(chapters),
        "chapters": []
    }
    
    for chapter in chapters:
        chapter_info = {
            "id": str(chapter.id),
            "title": chapter.title,
            "level": chapter.level,
            "order_index": chapter.order_index,
            "page_start": chapter.page_start,
            "page_end": chapter.page_end,
            "has_content": bool(chapter.content)
        }
        toc["chapters"].append(chapter_info)
    
    return toc


@router.get("/chapter/{chapter_id}/fig")
async def get_chapter_figures(
    chapter_id: UUID,
    db: AsyncSession = Depends(get_async_db)
) -> dict:
    """
    Get figures/images for a specific chapter
    
    Requirements: 4.5 - Image and caption pairing display
    """
    
    # Verify chapter exists
    chapter_stmt = select(Chapter).where(Chapter.id == chapter_id)
    chapter_result = await db.execute(chapter_stmt)
    chapter = chapter_result.scalar_one_or_none()
    
    if not chapter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chapter not found"
        )
    
    # Get figures for this chapter
    figures_stmt = (
        select(Figure)
        .where(Figure.chapter_id == chapter_id)
        .order_by(Figure.page_number, Figure.id)
    )
    figures_result = await db.execute(figures_stmt)
    figures = figures_result.scalars().all()
    
    # Format response
    response = {
        "chapter_id": str(chapter_id),
        "chapter_title": chapter.title,
        "total_figures": len(figures),
        "figures": []
    }
    
    for figure in figures:
        figure_info = {
            "id": str(figure.id),
            "image_path": figure.image_path,
            "caption": figure.caption,
            "page_number": figure.page_number,
            "bbox": figure.bbox,
            "image_format": figure.image_format
        }
        response["figures"].append(figure_info)
    
    return response


@router.get("/chapter/{chapter_id}/k")
async def get_chapter_knowledge_points(
    chapter_id: UUID,
    knowledge_type: Optional[str] = Query(None, description="Filter by knowledge type"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of knowledge points"),
    offset: int = Query(0, ge=0, description="Number of knowledge points to skip"),
    db: AsyncSession = Depends(get_async_db)
) -> dict:
    """
    Get knowledge points for a specific chapter
    
    Requirements: 5.4 - Knowledge point display with anchors
    """
    
    # Verify chapter exists
    chapter_stmt = select(Chapter).where(Chapter.id == chapter_id)
    chapter_result = await db.execute(chapter_stmt)
    chapter = chapter_result.scalar_one_or_none()
    
    if not chapter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chapter not found"
        )
    
    # Build knowledge query
    knowledge_stmt = select(Knowledge).where(Knowledge.chapter_id == chapter_id)
    
    # Apply knowledge type filter if provided
    if knowledge_type:
        try:
            from app.models.knowledge import KnowledgeType
            knowledge_enum = KnowledgeType(knowledge_type.lower())
            knowledge_stmt = knowledge_stmt.where(Knowledge.kind == knowledge_enum)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid knowledge type: {knowledge_type}"
            )
    
    # Apply pagination
    knowledge_stmt = knowledge_stmt.offset(offset).limit(limit).order_by(Knowledge.created_at)
    
    knowledge_result = await db.execute(knowledge_stmt)
    knowledge_points = knowledge_result.scalars().all()
    
    # Format response
    response = {
        "chapter_id": str(chapter_id),
        "chapter_title": chapter.title,
        "total_knowledge_points": len(knowledge_points),
        "knowledge_points": []
    }
    
    for kp in knowledge_points:
        kp_info = {
            "id": str(kp.id),
            "kind": kp.kind.value,
            "text": kp.text,
            "entities": kp.entities or [],
            "anchors": kp.anchors or {},
            "confidence_score": kp.confidence_score,
            "created_at": kp.created_at.isoformat()
        }
        response["knowledge_points"].append(kp_info)
    
    return response


@router.post("/card/gen")
async def generate_cards_for_chapter(
    chapter_id: UUID = Query(..., description="Chapter ID to generate cards for"),
    card_types: Optional[List[str]] = Query(None, description="Card types to generate (qa, cloze, image_hotspot)"),
    max_cards: int = Query(50, ge=1, le=200, description="Maximum number of cards to generate"),
    db: AsyncSession = Depends(get_async_db)
) -> dict:
    """
    Generate flashcards for a specific chapter
    
    Requirements: 6.4 - Card generation with traceability
    """
    
    # Verify chapter exists
    chapter_stmt = select(Chapter).where(Chapter.id == chapter_id)
    chapter_result = await db.execute(chapter_stmt)
    chapter = chapter_result.scalar_one_or_none()
    
    if not chapter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chapter not found"
        )
    
    try:
        # Get knowledge points for this chapter
        knowledge_stmt = select(Knowledge).where(Knowledge.chapter_id == chapter_id)
        knowledge_result = await db.execute(knowledge_stmt)
        knowledge_points = knowledge_result.scalars().all()
        
        if not knowledge_points:
            return {
                "chapter_id": str(chapter_id),
                "message": "No knowledge points found for this chapter",
                "generated_cards": 0,
                "cards": []
            }
        
        # Get figures for image hotspot cards
        figures_stmt = select(Figure).where(Figure.chapter_id == chapter_id)
        figures_result = await db.execute(figures_stmt)
        figures = figures_result.scalars().all()
        
        # Initialize card generation service
        card_service = CardGenerationService()
        
        # Generate cards
        generated_cards = await card_service.generate_cards_from_knowledge(
            knowledge_points=knowledge_points[:max_cards//2],  # Limit knowledge points to control card count
            figures=figures if not card_types or "image_hotspot" in card_types else None
        )
        
        # Filter by requested card types if specified
        if card_types:
            valid_types = {CardType.QA.value, CardType.CLOZE.value, CardType.IMAGE_HOTSPOT.value}
            requested_types = set(card_types) & valid_types
            if requested_types:
                generated_cards = [
                    card for card in generated_cards 
                    if card.card_type.value in requested_types
                ]
        
        # Limit to max_cards
        generated_cards = generated_cards[:max_cards]
        
        # Save cards to database
        saved_cards = []
        for gen_card in generated_cards:
            # Create Card model
            card = Card(
                knowledge_id=UUID(gen_card.knowledge_id),
                card_type=gen_card.card_type,
                front=gen_card.front,
                back=gen_card.back,
                difficulty=gen_card.difficulty,
                card_metadata=gen_card.metadata
            )
            
            db.add(card)
            await db.flush()  # Get the card ID
            
            # Create SRS record for the card
            srs = SRS(
                card_id=card.id,
                user_id=None  # No user system yet
            )
            db.add(srs)
            
            saved_cards.append({
                "id": str(card.id),
                "card_type": card.card_type.value,
                "front": card.front[:100] + "..." if len(card.front) > 100 else card.front,
                "back": card.back[:100] + "..." if len(card.back) > 100 else card.back,
                "difficulty": card.difficulty,
                "knowledge_id": str(card.knowledge_id),
                "metadata": card.card_metadata
            })
        
        await db.commit()
        
        return {
            "chapter_id": str(chapter_id),
            "chapter_title": chapter.title,
            "generated_cards": len(saved_cards),
            "cards": saved_cards
        }
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate cards: {str(e)}"
        )


@router.get("/cards")
async def get_cards(
    document_id: Optional[UUID] = Query(None, description="Filter by document ID"),
    chapter_id: Optional[UUID] = Query(None, description="Filter by chapter ID"),
    card_type: Optional[str] = Query(None, description="Filter by card type"),
    difficulty_min: Optional[float] = Query(None, ge=0.0, le=5.0, description="Minimum difficulty"),
    difficulty_max: Optional[float] = Query(None, ge=0.0, le=5.0, description="Maximum difficulty"),
    limit: int = Query(50, ge=1, le=200, description="Maximum number of cards"),
    offset: int = Query(0, ge=0, description="Number of cards to skip"),
    db: AsyncSession = Depends(get_async_db)
) -> dict:
    """
    Get flashcards with filtering options
    
    Requirements: 6.4 - Card management and retrieval
    """
    
    # Build base query
    cards_stmt = (
        select(Card, Knowledge, Chapter)
        .join(Knowledge, Card.knowledge_id == Knowledge.id)
        .join(Chapter, Knowledge.chapter_id == Chapter.id)
    )
    
    # Apply filters
    if document_id:
        cards_stmt = cards_stmt.join(Document, Chapter.document_id == Document.id).where(Document.id == document_id)
    
    if chapter_id:
        cards_stmt = cards_stmt.where(Chapter.id == chapter_id)
    
    if card_type:
        try:
            card_type_enum = CardType(card_type.lower())
            cards_stmt = cards_stmt.where(Card.card_type == card_type_enum)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid card type: {card_type}"
            )
    
    if difficulty_min is not None:
        cards_stmt = cards_stmt.where(Card.difficulty >= difficulty_min)
    
    if difficulty_max is not None:
        cards_stmt = cards_stmt.where(Card.difficulty <= difficulty_max)
    
    # Apply pagination and ordering
    cards_stmt = cards_stmt.offset(offset).limit(limit).order_by(Card.created_at.desc())
    
    # Execute query
    cards_result = await db.execute(cards_stmt)
    results = cards_result.all()
    
    # Format response
    cards_data = []
    for card, knowledge, chapter in results:
        card_info = {
            "id": str(card.id),
            "card_type": card.card_type.value,
            "front": card.front,
            "back": card.back,
            "difficulty": card.difficulty,
            "metadata": card.card_metadata or {},
            "knowledge": {
                "id": str(knowledge.id),
                "kind": knowledge.kind.value,
                "text": knowledge.text[:200] + "..." if len(knowledge.text) > 200 else knowledge.text,
                "entities": knowledge.entities or []
            },
            "chapter": {
                "id": str(chapter.id),
                "title": chapter.title,
                "document_id": str(chapter.document_id)
            },
            "created_at": card.created_at.isoformat()
        }
        cards_data.append(card_info)
    
    return {
        "total_cards": len(cards_data),
        "filters_applied": {
            "document_id": str(document_id) if document_id else None,
            "chapter_id": str(chapter_id) if chapter_id else None,
            "card_type": card_type,
            "difficulty_range": [difficulty_min, difficulty_max]
        },
        "cards": cards_data
    }


@router.get("/privacy/status")
async def get_privacy_status() -> dict:
    """
    Get current privacy and security configuration status
    
    Requirements: 11.1, 11.2, 11.3, 11.4, 11.5
    """
    status = privacy_manager.get_privacy_status()
    warnings = privacy_manager.validate_privacy_settings()
    
    return {
        "privacy_configuration": status,
        "warnings": warnings,
        "security_features": {
            "file_validation": True,
            "rate_limiting": True,
            "secure_logging": settings.anonymize_logs,
            "malware_scanning": settings.enable_file_scanning
        }
    }


@router.post("/privacy/toggle")
async def toggle_privacy_mode(
    request: Request,
    enable: bool = Query(..., description="Enable or disable privacy mode")
) -> dict:
    """
    Toggle privacy mode (admin endpoint)
    
    Requirements: 11.1 - Privacy mode toggle
    """
    # In a real application, this would require admin authentication
    # For now, we'll just log the change
    
    client_ip = get_client_ip(request)
    
    # Update settings (in a real app, this would update persistent config)
    old_mode = settings.privacy_mode
    settings.privacy_mode = enable
    
    # Log the change
    security_logger.log_security_event(
        "privacy_mode_changed",
        {
            "old_mode": old_mode,
            "new_mode": enable,
            "client_ip": client_ip
        },
        "WARNING"
    )
    
    return {
        "privacy_mode": settings.privacy_mode,
        "message": f"Privacy mode {'enabled' if enable else 'disabled'}",
        "warnings": privacy_manager.validate_privacy_settings()
    }