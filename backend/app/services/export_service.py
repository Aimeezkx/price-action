"""
Export service for flashcards and learning data
"""

import csv
import json
import io
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
from uuid import UUID
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_

from ..models.document import Document, Chapter, Figure
from ..models.knowledge import Knowledge, KnowledgeType
from ..models.learning import Card, SRS, CardType
from ..core.database import get_db


class ExportService:
    """Service for exporting flashcards and learning data"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def export_anki_csv(self, document_id: Optional[UUID] = None, chapter_ids: Optional[List[UUID]] = None) -> str:
        """
        Export cards in Anki-compatible CSV format
        
        Anki CSV format:
        Front, Back, Tags, Type, Deck, Note ID, Card ID
        """
        cards = self._get_cards_for_export(document_id, chapter_ids)
        
        output = io.StringIO()
        writer = csv.writer(output, quoting=csv.QUOTE_ALL)
        
        # Write header
        writer.writerow(['Front', 'Back', 'Tags', 'Type', 'Deck', 'Difficulty', 'Source'])
        
        for card in cards:
            # Get document and chapter info for tags and deck
            chapter = card.knowledge.chapter
            document = chapter.document
            
            # Create tags from entities and knowledge type
            tags = []
            if card.knowledge.entities:
                tags.extend(card.knowledge.entities[:3])  # Limit to 3 entities
            tags.append(f"type:{card.knowledge.kind}")
            tags.append(f"difficulty:{self._difficulty_to_tag(card.difficulty)}")
            
            # Create deck name from document
            deck_name = f"{document.filename}::{chapter.title}"
            
            # Format front and back based on card type
            front, back = self._format_card_content(card)
            
            # Create source reference
            source = f"Page {card.knowledge.anchors.get('page', 'N/A')} - {chapter.title}"
            
            writer.writerow([
                front,
                back,
                ' '.join(tags),
                card.card_type,
                deck_name,
                card.difficulty,
                source
            ])
        
        return output.getvalue()
    
    def export_notion_csv(self, document_id: Optional[UUID] = None, chapter_ids: Optional[List[UUID]] = None) -> str:
        """
        Export cards in Notion-compatible CSV format
        
        Notion format with proper field mapping:
        Question, Answer, Category, Difficulty, Source Document, Chapter, Page, Created Date, Last Reviewed
        """
        cards = self._get_cards_for_export(document_id, chapter_ids)
        
        output = io.StringIO()
        writer = csv.writer(output, quoting=csv.QUOTE_ALL)
        
        # Write header with Notion-friendly column names
        writer.writerow([
            'Question', 'Answer', 'Category', 'Difficulty', 'Source Document', 
            'Chapter', 'Page', 'Knowledge Type', 'Entities', 'Created Date', 'Last Reviewed'
        ])
        
        for card in cards:
            chapter = card.knowledge.chapter
            document = chapter.document
            
            # Get SRS info for last reviewed
            srs = self.db.query(SRS).filter(SRS.card_id == card.id).first()
            last_reviewed = srs.last_reviewed.isoformat() if srs and srs.last_reviewed else ""
            
            # Format content
            front, back = self._format_card_content(card)
            
            writer.writerow([
                front,
                back,
                self._get_card_category(card),
                self._difficulty_to_label(card.difficulty),
                document.filename,
                chapter.title,
                card.knowledge.anchors.get('page', ''),
                card.knowledge.kind,
                ', '.join(card.knowledge.entities) if card.knowledge.entities else '',
                card.created_at.isoformat(),
                last_reviewed
            ])
        
        return output.getvalue()
    
    def export_jsonl_backup(self, document_id: Optional[UUID] = None) -> str:
        """
        Export complete data in JSONL format for backup
        Each line is a JSON object representing a complete document with all related data
        """
        if document_id:
            documents = self.db.query(Document).filter(Document.id == document_id).all()
        else:
            documents = self.db.query(Document).all()
        
        output = io.StringIO()
        
        for document in documents:
            # Build complete document data structure
            doc_data = {
                'document': {
                    'id': str(document.id),
                    'filename': document.filename,
                    'file_type': document.file_type,
                    'file_path': document.file_path,
                    'file_size': document.file_size,
                    'status': document.status,
                    'doc_metadata': document.doc_metadata,
                    'created_at': document.created_at.isoformat(),
                    'updated_at': document.updated_at.isoformat()
                },
                'chapters': [],
                'export_metadata': {
                    'export_date': datetime.utcnow().isoformat(),
                    'export_version': '1.0',
                    'total_chapters': 0,
                    'total_figures': 0,
                    'total_knowledge': 0,
                    'total_cards': 0
                }
            }
            
            # Get chapters with all related data
            chapters = self.db.query(Chapter).filter(Chapter.document_id == document.id)\
                .options(
                    joinedload(Chapter.figures),
                    joinedload(Chapter.knowledge_points).joinedload(Knowledge.cards).joinedload(Card.srs_records)
                ).all()
            
            for chapter in chapters:
                chapter_data = {
                    'id': str(chapter.id),
                    'title': chapter.title,
                    'level': chapter.level,
                    'order_index': chapter.order_index,
                    'page_start': chapter.page_start,
                    'page_end': chapter.page_end,
                    'content': chapter.content,
                    'created_at': chapter.created_at.isoformat(),
                    'updated_at': chapter.updated_at.isoformat(),
                    'figures': [],
                    'knowledge_points': []
                }
                
                # Add figures
                for figure in chapter.figures:
                    figure_data = {
                        'id': str(figure.id),
                        'image_path': figure.image_path,
                        'caption': figure.caption,
                        'page_number': figure.page_number,
                        'bbox': figure.bbox,
                        'image_format': figure.image_format,
                        'created_at': figure.created_at.isoformat(),
                        'updated_at': figure.updated_at.isoformat()
                    }
                    chapter_data['figures'].append(figure_data)
                    doc_data['export_metadata']['total_figures'] += 1
                
                # Add knowledge points with cards and SRS data
                for knowledge in chapter.knowledge_points:
                    knowledge_data = {
                        'id': str(knowledge.id),
                        'kind': knowledge.kind,
                        'text': knowledge.text,
                        'entities': knowledge.entities,
                        'anchors': knowledge.anchors,
                        'confidence_score': knowledge.confidence_score,
                        'created_at': knowledge.created_at.isoformat(),
                        'updated_at': knowledge.updated_at.isoformat(),
                        'cards': []
                    }
                    
                    # Add cards with SRS data
                    for card in knowledge.cards:
                        card_data = {
                            'id': str(card.id),
                            'card_type': card.card_type,
                            'front': card.front,
                            'back': card.back,
                            'difficulty': card.difficulty,
                            'card_metadata': card.card_metadata,
                            'created_at': card.created_at.isoformat(),
                            'updated_at': card.updated_at.isoformat(),
                            'srs_records': []
                        }
                        
                        # Add SRS records
                        for srs in card.srs_records:
                            srs_data = {
                                'id': str(srs.id),
                                'user_id': str(srs.user_id) if srs.user_id else None,
                                'ease_factor': srs.ease_factor,
                                'interval': srs.interval,
                                'repetitions': srs.repetitions,
                                'due_date': srs.due_date.isoformat(),
                                'last_reviewed': srs.last_reviewed.isoformat() if srs.last_reviewed else None,
                                'last_grade': srs.last_grade,
                                'created_at': srs.created_at.isoformat(),
                                'updated_at': srs.updated_at.isoformat()
                            }
                            card_data['srs_records'].append(srs_data)
                        
                        knowledge_data['cards'].append(card_data)
                        doc_data['export_metadata']['total_cards'] += 1
                    
                    chapter_data['knowledge_points'].append(knowledge_data)
                    doc_data['export_metadata']['total_knowledge'] += 1
                
                doc_data['chapters'].append(chapter_data)
                doc_data['export_metadata']['total_chapters'] += 1
            
            # Write document as single JSON line
            output.write(json.dumps(doc_data, ensure_ascii=False) + '\n')
        
        return output.getvalue()
    
    def validate_jsonl_backup(self, jsonl_content: str) -> Dict[str, Any]:
        """
        Validate JSONL backup format without importing
        Returns validation results
        """
        errors = []
        warnings = []
        valid_lines = 0
        total_lines = 0
        
        try:
            lines = jsonl_content.strip().split('\n')
            total_lines = len([line for line in lines if line.strip()])
            
            for line_num, line in enumerate(lines, 1):
                if not line.strip():
                    continue
                
                try:
                    doc_data = json.loads(line)
                    
                    # Validate document structure
                    if not self._validate_document_structure(doc_data):
                        errors.append(f"Line {line_num}: Invalid document structure")
                        continue
                    
                    # Validate required fields
                    if not self._validate_required_fields(doc_data):
                        errors.append(f"Line {line_num}: Missing required fields")
                        continue
                    
                    # Check for potential data issues
                    line_warnings = self._validate_data_quality(doc_data, line_num)
                    warnings.extend(line_warnings)
                    
                    valid_lines += 1
                    
                except json.JSONDecodeError as e:
                    errors.append(f"Line {line_num}: Invalid JSON - {str(e)}")
                except Exception as e:
                    errors.append(f"Line {line_num}: Validation error - {str(e)}")
        
        except Exception as e:
            errors.append(f"General validation error: {str(e)}")
        
        is_valid = len(errors) == 0 and valid_lines > 0
        
        return {
            'valid': is_valid,
            'total_lines': total_lines,
            'valid_lines': valid_lines,
            'errors': errors,
            'warnings': warnings,
            'summary': {
                'documents_found': valid_lines,
                'validation_passed': is_valid,
                'error_count': len(errors),
                'warning_count': len(warnings)
            }
        }
    
    def import_jsonl_backup(self, jsonl_content: str) -> Dict[str, Any]:
        """
        Import data from JSONL backup format
        Returns summary of imported data
        """
        imported_docs = 0
        imported_chapters = 0
        imported_figures = 0
        imported_knowledge = 0
        imported_cards = 0
        errors = []
        
        try:
            lines = jsonl_content.strip().split('\n')
            
            for line_num, line in enumerate(lines, 1):
                if not line.strip():
                    continue
                
                try:
                    doc_data = json.loads(line)
                    
                    # Import document
                    document = self._import_document(doc_data['document'])
                    imported_docs += 1
                    
                    # Import chapters and related data
                    for chapter_data in doc_data['chapters']:
                        chapter = self._import_chapter(chapter_data, document.id)
                        imported_chapters += 1
                        
                        # Import figures
                        for figure_data in chapter_data['figures']:
                            self._import_figure(figure_data, chapter.id)
                            imported_figures += 1
                        
                        # Import knowledge points
                        for knowledge_data in chapter_data['knowledge_points']:
                            knowledge = self._import_knowledge(knowledge_data, chapter.id)
                            imported_knowledge += 1
                            
                            # Import cards
                            for card_data in knowledge_data['cards']:
                                card = self._import_card(card_data, knowledge.id)
                                imported_cards += 1
                                
                                # Import SRS records
                                for srs_data in card_data['srs_records']:
                                    self._import_srs(srs_data, card.id)
                    
                    self.db.commit()
                    
                except json.JSONDecodeError as e:
                    errors.append(f"Line {line_num}: Invalid JSON - {str(e)}")
                except Exception as e:
                    errors.append(f"Line {line_num}: Import error - {str(e)}")
                    self.db.rollback()
        
        except Exception as e:
            errors.append(f"General import error: {str(e)}")
            self.db.rollback()
        
        return {
            'imported_documents': imported_docs,
            'imported_chapters': imported_chapters,
            'imported_figures': imported_figures,
            'imported_knowledge': imported_knowledge,
            'imported_cards': imported_cards,
            'errors': errors
        }
    
    def _get_cards_for_export(self, document_id: Optional[UUID] = None, chapter_ids: Optional[List[UUID]] = None) -> List[Card]:
        """Get cards for export based on filters"""
        query = self.db.query(Card).join(Knowledge).join(Chapter).join(Document)\
            .options(
                joinedload(Card.knowledge).joinedload(Knowledge.chapter).joinedload(Chapter.document)
            )
        
        if document_id:
            query = query.filter(Document.id == document_id)
        
        if chapter_ids:
            query = query.filter(Chapter.id.in_(chapter_ids))
        
        return query.all()
    
    def _format_card_content(self, card: Card) -> tuple[str, str]:
        """Format card content based on card type"""
        if card.card_type == CardType.CLOZE:
            # For cloze cards, front has blanks, back has full text
            return card.front, card.back
        elif card.card_type == CardType.IMAGE_HOTSPOT:
            # For image cards, include image reference
            front = f"[IMAGE: {card.front}]"
            if card.card_metadata.get('hotspots'):
                front += f" (Click on: {', '.join(card.card_metadata['hotspots'])})"
            return front, card.back
        else:
            # Standard Q&A format
            return card.front, card.back
    
    def _difficulty_to_tag(self, difficulty: float) -> str:
        """Convert difficulty score to tag"""
        if difficulty <= 1.5:
            return "easy"
        elif difficulty <= 2.5:
            return "medium"
        else:
            return "hard"
    
    def _difficulty_to_label(self, difficulty: float) -> str:
        """Convert difficulty score to human-readable label"""
        if difficulty <= 1.5:
            return "Easy"
        elif difficulty <= 2.5:
            return "Medium"
        else:
            return "Hard"
    
    def _get_card_category(self, card: Card) -> str:
        """Get card category for Notion export"""
        knowledge_type = card.knowledge.kind
        card_type = card.card_type
        
        category_map = {
            (KnowledgeType.DEFINITION, CardType.QA): "Definition",
            (KnowledgeType.FACT, CardType.QA): "Fact",
            (KnowledgeType.THEOREM, CardType.QA): "Theorem",
            (KnowledgeType.PROCESS, CardType.QA): "Process",
            (KnowledgeType.EXAMPLE, CardType.QA): "Example",
            (KnowledgeType.CONCEPT, CardType.QA): "Concept"
        }
        
        if card_type == CardType.CLOZE:
            return f"Cloze - {knowledge_type.title()}"
        elif card_type == CardType.IMAGE_HOTSPOT:
            return f"Image - {knowledge_type.title()}"
        else:
            return category_map.get((knowledge_type, card_type), f"{knowledge_type.title()} - {card_type.title()}")
    
    def _import_document(self, doc_data: Dict[str, Any]) -> Document:
        """Import document from backup data"""
        # Check if document already exists
        existing = self.db.query(Document).filter(Document.id == doc_data['id']).first()
        if existing:
            return existing
        
        document = Document(
            id=doc_data['id'],
            filename=doc_data['filename'],
            file_type=doc_data['file_type'],
            file_path=doc_data['file_path'],
            file_size=doc_data['file_size'],
            status=doc_data['status'],
            doc_metadata=doc_data['doc_metadata']
        )
        
        self.db.add(document)
        self.db.flush()
        return document
    
    def _import_chapter(self, chapter_data: Dict[str, Any], document_id: UUID) -> Chapter:
        """Import chapter from backup data"""
        chapter = Chapter(
            id=chapter_data['id'],
            document_id=document_id,
            title=chapter_data['title'],
            level=chapter_data['level'],
            order_index=chapter_data['order_index'],
            page_start=chapter_data['page_start'],
            page_end=chapter_data['page_end'],
            content=chapter_data['content']
        )
        
        self.db.add(chapter)
        self.db.flush()
        return chapter
    
    def _import_figure(self, figure_data: Dict[str, Any], chapter_id: UUID) -> Figure:
        """Import figure from backup data"""
        figure = Figure(
            id=figure_data['id'],
            chapter_id=chapter_id,
            image_path=figure_data['image_path'],
            caption=figure_data['caption'],
            page_number=figure_data['page_number'],
            bbox=figure_data['bbox'],
            image_format=figure_data['image_format']
        )
        
        self.db.add(figure)
        self.db.flush()
        return figure
    
    def _import_knowledge(self, knowledge_data: Dict[str, Any], chapter_id: UUID) -> Knowledge:
        """Import knowledge from backup data"""
        knowledge = Knowledge(
            id=knowledge_data['id'],
            chapter_id=chapter_id,
            kind=knowledge_data['kind'],
            text=knowledge_data['text'],
            entities=knowledge_data['entities'],
            anchors=knowledge_data['anchors'],
            confidence_score=knowledge_data['confidence_score']
        )
        
        self.db.add(knowledge)
        self.db.flush()
        return knowledge
    
    def _import_card(self, card_data: Dict[str, Any], knowledge_id: UUID) -> Card:
        """Import card from backup data"""
        card = Card(
            id=card_data['id'],
            knowledge_id=knowledge_id,
            card_type=card_data['card_type'],
            front=card_data['front'],
            back=card_data['back'],
            difficulty=card_data['difficulty'],
            card_metadata=card_data['card_metadata']
        )
        
        self.db.add(card)
        self.db.flush()
        return card
    
    def _import_srs(self, srs_data: Dict[str, Any], card_id: UUID) -> SRS:
        """Import SRS record from backup data"""
        srs = SRS(
            id=srs_data['id'],
            card_id=card_id,
            user_id=srs_data['user_id'],
            ease_factor=srs_data['ease_factor'],
            interval=srs_data['interval'],
            repetitions=srs_data['repetitions'],
            due_date=datetime.fromisoformat(srs_data['due_date']),
            last_reviewed=datetime.fromisoformat(srs_data['last_reviewed']) if srs_data['last_reviewed'] else None,
            last_grade=srs_data['last_grade']
        )
        
        self.db.add(srs)
        self.db.flush()
        return srs
    
    def _validate_document_structure(self, doc_data: Dict[str, Any]) -> bool:
        """Validate basic document structure"""
        required_keys = ['document', 'chapters', 'export_metadata']
        return all(key in doc_data for key in required_keys)
    
    def _validate_required_fields(self, doc_data: Dict[str, Any]) -> bool:
        """Validate required fields in document data"""
        try:
            # Check document fields
            doc = doc_data['document']
            doc_required = ['id', 'filename', 'file_type', 'status']
            if not all(field in doc for field in doc_required):
                return False
            
            # Check chapters structure
            for chapter in doc_data['chapters']:
                chapter_required = ['id', 'title', 'level', 'order_index']
                if not all(field in chapter for field in chapter_required):
                    return False
                
                # Check knowledge points
                for knowledge in chapter.get('knowledge_points', []):
                    knowledge_required = ['id', 'kind', 'text']
                    if not all(field in knowledge for field in knowledge_required):
                        return False
                    
                    # Check cards
                    for card in knowledge.get('cards', []):
                        card_required = ['id', 'card_type', 'front', 'back']
                        if not all(field in card for field in card_required):
                            return False
            
            return True
            
        except (KeyError, TypeError):
            return False
    
    def _validate_data_quality(self, doc_data: Dict[str, Any], line_num: int) -> List[str]:
        """Validate data quality and return warnings"""
        warnings = []
        
        try:
            # Check for empty content
            if not doc_data['chapters']:
                warnings.append(f"Line {line_num}: Document has no chapters")
            
            # Check chapter content
            for i, chapter in enumerate(doc_data['chapters']):
                if not chapter.get('knowledge_points'):
                    warnings.append(f"Line {line_num}: Chapter {i+1} has no knowledge points")
                
                # Check for cards without SRS data
                for j, knowledge in enumerate(chapter.get('knowledge_points', [])):
                    for k, card in enumerate(knowledge.get('cards', [])):
                        if not card.get('srs_records'):
                            warnings.append(f"Line {line_num}: Card {k+1} in knowledge {j+1} has no SRS data")
            
            # Check export metadata
            metadata = doc_data.get('export_metadata', {})
            if not metadata.get('export_date'):
                warnings.append(f"Line {line_num}: Missing export date in metadata")
            
        except Exception as e:
            warnings.append(f"Line {line_num}: Data quality check failed - {str(e)}")
        
        return warnings


def get_export_service(db: Session = None) -> ExportService:
    """Get export service instance"""
    if db is None:
        db = next(get_db())
    return ExportService(db)