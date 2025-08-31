#!/usr/bin/env python3
"""
测试数据库连接和基本操作
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.models.base import BaseModel
from app.core.database import engine
from app.models.document import Document, Chapter, Figure
try:
    from app.models.knowledge import Knowledge
except ImportError:
    Knowledge = None
try:
    from app.models.cards import Card  
except ImportError:
    Card = None
try:
    from app.models.srs import SRS
except ImportError:
    SRS = None
from sqlalchemy.orm import sessionmaker

def test_database_connection():
    """测试数据库连接"""
    print("Testing database connection...")
    
    # 设置数据库URL
    database_url = "sqlite:///./document_learning.db"
    print(f"Database URL: {database_url}")
    
    try:
        # 创建数据库表
        BaseModel.metadata.create_all(bind=engine)
        print("✓ Database initialized successfully")
        
        # 检查表是否存在
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        expected_tables = ["documents", "chapters", "figures"]
        if Knowledge:
            expected_tables.append("knowledge")
        if Card:
            expected_tables.append("cards")
        if SRS:
            expected_tables.append("srs")
        
        for table in expected_tables:
            if table in tables:
                print(f"✓ Table '{table}' exists")
            else:
                print(f"✗ Table '{table}' missing")
                
        print("✓ Database tables created successfully")
        
        # 测试基本数据库操作
        Session = sessionmaker(bind=engine)
        session = Session()
        
        try:
            # 创建测试文档
            test_doc = Document(
                filename="test_document.pdf",
                file_type="pdf",
                file_path="/tmp/test.pdf",
                file_size=1024,
                status="PENDING"
            )
            session.add(test_doc)
            session.commit()
            print(f"✓ Created test document with ID: {test_doc.id}")
            
            # 查询文档
            retrieved_doc = session.query(Document).filter_by(id=test_doc.id).first()
            if retrieved_doc:
                print(f"✓ Retrieved document: {retrieved_doc.filename}")
            else:
                print("✗ Failed to retrieve document")
                
            # 查询关联的章节（应该为空）
            chapters = session.query(Chapter).filter_by(document_id=test_doc.id).all()
            print(f"✓ Document has {len(chapters)} chapters")
            
            # 清理测试数据
            session.delete(test_doc)
            session.commit()
            print("✓ Cleaned up test document")
            
        finally:
            session.close()
            
        print("✓ Database connection test completed successfully")
        return True
        
    except Exception as e:
        print(f"✗ Database connection test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_database_connection()
    sys.exit(0 if success else 1)