"""
Export API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field
import io
import logging

from ..core.database import get_db
from ..services.export_service import get_export_service, ExportService

logger = logging.getLogger(__name__)


router = APIRouter(prefix="/export", tags=["export"])


class ImportResult(BaseModel):
    """Import operation result"""
    success: bool
    message: str
    summary: dict
    errors: Optional[List[str]] = None


class ExportFormat(BaseModel):
    """Export format description"""
    name: str
    description: str
    endpoint: str
    file_extension: str
    fields: List[str]


class ExportFormatsResponse(BaseModel):
    """Available export formats"""
    formats: List[ExportFormat]
    import_formats: List[ExportFormat]


@router.get("/csv")
async def export_csv(
    format: str = Query("anki", description="Export format: 'anki' or 'notion'"),
    document_id: Optional[UUID] = Query(None, description="Filter by document ID"),
    chapter_ids: Optional[List[UUID]] = Query(None, description="Filter by chapter IDs"),
    db: Session = Depends(get_db)
):
    """
    Export flashcards in CSV format
    
    - **format**: Export format ('anki' or 'notion')
    - **document_id**: Optional document ID to filter cards
    - **chapter_ids**: Optional list of chapter IDs to filter cards
    
    Returns CSV file with format-specific columns
    """
    try:
        export_service = get_export_service(db)
        
        if format.lower() == "anki":
            csv_content = export_service.export_anki_csv(document_id, chapter_ids)
            filename_prefix = "anki_export"
        elif format.lower() == "notion":
            csv_content = export_service.export_notion_csv(document_id, chapter_ids)
            filename_prefix = "notion_export"
        else:
            raise HTTPException(status_code=400, detail="Invalid format. Use 'anki' or 'notion'")
        
        # Create filename
        if document_id:
            filename = f"{filename_prefix}_{document_id}.csv"
        else:
            filename = f"{filename_prefix}_all.csv"
        
        # Return as streaming response
        return StreamingResponse(
            io.StringIO(csv_content),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@router.get("/csv/anki")
async def export_anki_csv(
    document_id: Optional[UUID] = Query(None, description="Filter by document ID"),
    chapter_ids: Optional[List[UUID]] = Query(None, description="Filter by chapter IDs"),
    db: Session = Depends(get_db)
):
    """
    Export flashcards in Anki-compatible CSV format
    
    - **document_id**: Optional document ID to filter cards
    - **chapter_ids**: Optional list of chapter IDs to filter cards
    
    Returns CSV file with columns: Front, Back, Tags, Type, Deck, Difficulty, Source
    """
    try:
        export_service = get_export_service(db)
        csv_content = export_service.export_anki_csv(document_id, chapter_ids)
        
        # Create filename
        if document_id:
            filename = f"anki_export_{document_id}.csv"
        else:
            filename = "anki_export_all.csv"
        
        # Return as streaming response
        return StreamingResponse(
            io.StringIO(csv_content),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@router.get("/csv/notion")
async def export_notion_csv(
    document_id: Optional[UUID] = Query(None, description="Filter by document ID"),
    chapter_ids: Optional[List[UUID]] = Query(None, description="Filter by chapter IDs"),
    db: Session = Depends(get_db)
):
    """
    Export flashcards in Notion-compatible CSV format
    
    - **document_id**: Optional document ID to filter cards
    - **chapter_ids**: Optional list of chapter IDs to filter cards
    
    Returns CSV file with columns optimized for Notion import
    """
    try:
        export_service = get_export_service(db)
        csv_content = export_service.export_notion_csv(document_id, chapter_ids)
        
        # Create filename
        if document_id:
            filename = f"notion_export_{document_id}.csv"
        else:
            filename = "notion_export_all.csv"
        
        # Return as streaming response
        return StreamingResponse(
            io.StringIO(csv_content),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@router.get("/jsonl")
async def export_jsonl(
    document_id: Optional[UUID] = Query(None, description="Filter by document ID"),
    db: Session = Depends(get_db)
):
    """
    Export complete data in JSONL format
    
    - **document_id**: Optional document ID to export specific document
    
    Returns JSONL file with complete document data including all relationships
    """
    try:
        export_service = get_export_service(db)
        jsonl_content = export_service.export_jsonl_backup(document_id)
        
        # Create filename
        if document_id:
            filename = f"export_{document_id}.jsonl"
        else:
            filename = "export_all.jsonl"
        
        # Return as streaming response
        return StreamingResponse(
            io.StringIO(jsonl_content),
            media_type="application/jsonl",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@router.get("/jsonl/backup")
async def export_jsonl_backup(
    document_id: Optional[UUID] = Query(None, description="Filter by document ID"),
    db: Session = Depends(get_db)
):
    """
    Export complete data in JSONL format for backup
    
    - **document_id**: Optional document ID to export specific document
    
    Returns JSONL file with complete document data including all relationships
    """
    try:
        export_service = get_export_service(db)
        jsonl_content = export_service.export_jsonl_backup(document_id)
        
        # Create filename
        if document_id:
            filename = f"backup_{document_id}.jsonl"
        else:
            filename = "backup_all.jsonl"
        
        # Return as streaming response
        return StreamingResponse(
            io.StringIO(jsonl_content),
            media_type="application/jsonl",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Backup export failed: {str(e)}")


@router.post("/import/jsonl", response_model=ImportResult)
async def import_jsonl_backup(
    file: UploadFile = File(..., description="JSONL backup file to import"),
    validate_only: bool = Query(False, description="Only validate the file without importing"),
    db: Session = Depends(get_db)
):
    """
    Import data from JSONL backup file
    
    - **file**: JSONL backup file to restore
    - **validate_only**: If true, only validate the file structure without importing
    
    Returns summary of imported data and any errors encountered
    """
    errors = []
    
    try:
        # Validate file exists and has content
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")
        
        # Validate file type
        if not file.filename.lower().endswith('.jsonl'):
            raise HTTPException(status_code=400, detail="File must have .jsonl extension")
        
        # Check file size (limit to 100MB)
        if file.size and file.size > 100 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="File size exceeds 100MB limit")
        
        # Read file content
        try:
            content = await file.read()
            jsonl_content = content.decode('utf-8')
        except UnicodeDecodeError:
            raise HTTPException(status_code=400, detail="File must be UTF-8 encoded")
        
        # Validate content is not empty
        if not jsonl_content.strip():
            raise HTTPException(status_code=400, detail="File is empty")
        
        # Get export service
        export_service = get_export_service(db)
        
        if validate_only:
            # Only validate the file structure
            validation_result = export_service.validate_jsonl_backup(jsonl_content)
            return ImportResult(
                success=validation_result["valid"],
                message="Validation completed",
                summary=validation_result,
                errors=validation_result.get("errors", [])
            )
        else:
            # Import data
            result = export_service.import_jsonl_backup(jsonl_content)
            
            return ImportResult(
                success=result.get("success", True),
                message="Import completed successfully",
                summary=result,
                errors=result.get("errors", [])
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Import failed: {e}")
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")


@router.get("/formats", response_model=ExportFormatsResponse)
async def get_export_formats():
    """
    Get available export formats and their descriptions
    """
    return ExportFormatsResponse(
        formats=[
            ExportFormat(
                name="anki_csv",
                description="Anki-compatible CSV format for flashcard import",
                endpoint="/export/csv?format=anki",
                file_extension=".csv",
                fields=["Front", "Back", "Tags", "Type", "Deck", "Difficulty", "Source"]
            ),
            ExportFormat(
                name="notion_csv", 
                description="Notion-compatible CSV format with detailed metadata",
                endpoint="/export/csv?format=notion",
                file_extension=".csv",
                fields=["Question", "Answer", "Category", "Difficulty", "Source Document", 
                          "Chapter", "Page", "Knowledge Type", "Entities", "Created Date", "Last Reviewed"]
            ),
            ExportFormat(
                name="jsonl_backup",
                description="Complete data backup in JSONL format",
                endpoint="/export/jsonl", 
                file_extension=".jsonl",
                fields=["Complete document structure with all relationships"]
            )
        ],
        import_formats=[
            ExportFormat(
                name="jsonl_backup",
                description="Restore from JSONL backup file",
                endpoint="/export/import/jsonl",
                file_extension=".jsonl",
                fields=["Complete document structure with all relationships"]
            )
        ]
    )