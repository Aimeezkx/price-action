"""Initial database schema

Revision ID: 001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from pgvector.sqlalchemy import Vector
import uuid

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enable pgvector extension
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')
    
    # Create documents table
    op.create_table('documents',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('filename', sa.String(255), nullable=False),
        sa.Column('file_type', sa.String(10), nullable=False),
        sa.Column('file_path', sa.String(500), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=False),
        sa.Column('status', sa.Enum('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED', name='processingstatus'), nullable=False),
        sa.Column('doc_metadata', postgresql.JSON(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_documents_id', 'documents', ['id'])
    op.create_index('ix_documents_filename', 'documents', ['filename'])
    op.create_index('ix_documents_status', 'documents', ['status'])
    
    # Create chapters table
    op.create_table('chapters',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('document_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('level', sa.Integer(), nullable=False, default=1),
        sa.Column('order_index', sa.Integer(), nullable=False),
        sa.Column('page_start', sa.Integer(), nullable=True),
        sa.Column('page_end', sa.Integer(), nullable=True),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ),
    )
    op.create_index('ix_chapters_id', 'chapters', ['id'])
    op.create_index('ix_chapters_document_id', 'chapters', ['document_id'])
    
    # Create figures table
    op.create_table('figures',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('chapter_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('image_path', sa.String(500), nullable=False),
        sa.Column('caption', sa.Text(), nullable=True),
        sa.Column('page_number', sa.Integer(), nullable=True),
        sa.Column('bbox', postgresql.JSON(), nullable=True),
        sa.Column('image_format', sa.String(10), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['chapter_id'], ['chapters.id'], ),
    )
    op.create_index('ix_figures_id', 'figures', ['id'])
    op.create_index('ix_figures_chapter_id', 'figures', ['chapter_id'])
    
    # Create knowledge table
    op.create_table('knowledge',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('chapter_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('kind', sa.Enum('DEFINITION', 'FACT', 'THEOREM', 'PROCESS', 'EXAMPLE', 'CONCEPT', name='knowledgetype'), nullable=False),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('entities', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('anchors', postgresql.JSON(), nullable=True),
        sa.Column('embedding', Vector(384), nullable=True),
        sa.Column('confidence_score', sa.Float(), nullable=False, default=1.0),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['chapter_id'], ['chapters.id'], ),
    )
    op.create_index('ix_knowledge_id', 'knowledge', ['id'])
    op.create_index('ix_knowledge_chapter_id', 'knowledge', ['chapter_id'])
    op.create_index('ix_knowledge_kind', 'knowledge', ['kind'])
    
    # Create cards table
    op.create_table('cards',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('knowledge_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('card_type', sa.Enum('QA', 'CLOZE', 'IMAGE_HOTSPOT', name='cardtype'), nullable=False),
        sa.Column('front', sa.Text(), nullable=False),
        sa.Column('back', sa.Text(), nullable=False),
        sa.Column('difficulty', sa.Float(), nullable=False, default=1.0),
        sa.Column('card_metadata', postgresql.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['knowledge_id'], ['knowledge.id'], ),
    )
    op.create_index('ix_cards_id', 'cards', ['id'])
    op.create_index('ix_cards_knowledge_id', 'cards', ['knowledge_id'])
    op.create_index('ix_cards_card_type', 'cards', ['card_type'])
    
    # Create srs table
    op.create_table('srs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('card_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('ease_factor', sa.Float(), nullable=False, default=2.5),
        sa.Column('interval', sa.Integer(), nullable=False, default=1),
        sa.Column('repetitions', sa.Integer(), nullable=False, default=0),
        sa.Column('due_date', sa.DateTime(), nullable=False),
        sa.Column('last_reviewed', sa.DateTime(), nullable=True),
        sa.Column('last_grade', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['card_id'], ['cards.id'], ),
    )
    op.create_index('ix_srs_id', 'srs', ['id'])
    op.create_index('ix_srs_card_id', 'srs', ['card_id'])
    op.create_index('ix_srs_user_id', 'srs', ['user_id'])
    op.create_index('ix_srs_due_date', 'srs', ['due_date'])


def downgrade() -> None:
    op.drop_table('srs')
    op.drop_table('cards')
    op.drop_table('knowledge')
    op.drop_table('figures')
    op.drop_table('chapters')
    op.drop_table('documents')
    
    # Drop enums
    op.execute('DROP TYPE IF EXISTS processingstatus')
    op.execute('DROP TYPE IF EXISTS knowledgetype')
    op.execute('DROP TYPE IF EXISTS cardtype')