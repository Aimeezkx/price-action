#!/usr/bin/env python3
"""
Test Alembic migration setup and database schema
"""

import sys
import os
import tempfile
import shutil

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

def test_alembic_configuration():
    """Test that Alembic is properly configured"""
    try:
        from alembic.config import Config
        from alembic import command
        import tempfile
        
        print("Testing Alembic configuration...")
        
        # Check alembic.ini exists
        alembic_ini = os.path.join(os.path.dirname(__file__), "alembic.ini")
        assert os.path.exists(alembic_ini), "alembic.ini not found"
        print("✓ alembic.ini found")
        
        # Check alembic directory exists
        alembic_dir = os.path.join(os.path.dirname(__file__), "alembic")
        assert os.path.exists(alembic_dir), "alembic directory not found"
        print("✓ alembic directory found")
        
        # Check env.py exists
        env_py = os.path.join(alembic_dir, "env.py")
        assert os.path.exists(env_py), "alembic/env.py not found"
        print("✓ alembic/env.py found")
        
        # Check versions directory exists
        versions_dir = os.path.join(alembic_dir, "versions")
        assert os.path.exists(versions_dir), "alembic/versions directory not found"
        print("✓ alembic/versions directory found")
        
        # Check initial migration exists
        initial_migration = os.path.join(versions_dir, "001_initial_schema.py")
        assert os.path.exists(initial_migration), "Initial migration not found"
        print("✓ Initial migration found")
        
        print("✓ Alembic configuration test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Alembic configuration test failed: {e}")
        return False

def test_migration_content():
    """Test that the migration contains expected tables"""
    try:
        print("Testing migration content...")
        
        # Read the migration file
        versions_dir = os.path.join(os.path.dirname(__file__), "alembic", "versions")
        initial_migration = os.path.join(versions_dir, "001_initial_schema.py")
        
        with open(initial_migration, 'r') as f:
            content = f.read()
        
        # Check for expected tables
        expected_tables = [
            'documents', 'chapters', 'figures', 
            'knowledge', 'cards', 'srs'
        ]
        
        for table in expected_tables:
            assert f"create_table('{table}'" in content, f"Table {table} not found in migration"
            print(f"✓ Table {table} found in migration")
        
        # Check for pgvector extension
        assert "CREATE EXTENSION IF NOT EXISTS vector" in content, "pgvector extension not found"
        print("✓ pgvector extension found in migration")
        
        # Check for vector column
        assert "Vector(384)" in content, "Vector column not found"
        print("✓ Vector column found in migration")
        
        print("✓ Migration content test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Migration content test failed: {e}")
        return False

def test_model_metadata():
    """Test that model metadata is properly configured"""
    try:
        print("Testing model metadata...")
        
        from app.core.database import Base
        from app.models import Document, Chapter, Figure, Knowledge, Card, SRS
        
        # Check that all models are registered with Base
        table_names = [table.name for table in Base.metadata.tables.values()]
        expected_tables = ['documents', 'chapters', 'figures', 'knowledge', 'cards', 'srs']
        
        for table in expected_tables:
            assert table in table_names, f"Table {table} not registered with Base metadata"
            print(f"✓ Table {table} registered with Base metadata")
        
        # Check that models have proper table names
        assert Document.__tablename__ == 'documents'
        assert Chapter.__tablename__ == 'chapters'
        assert Figure.__tablename__ == 'figures'
        assert Knowledge.__tablename__ == 'knowledge'
        assert Card.__tablename__ == 'cards'
        assert SRS.__tablename__ == 'srs'
        print("✓ All models have correct table names")
        
        print("✓ Model metadata test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Model metadata test failed: {e}")
        return False

def test_database_utilities():
    """Test database utility functions"""
    try:
        print("Testing database utilities...")
        
        from app.core.db_utils import run_migrations, create_migration
        
        # Check that functions exist and are callable
        assert callable(run_migrations), "run_migrations is not callable"
        assert callable(create_migration), "create_migration is not callable"
        print("✓ Database utility functions are available")
        
        print("✓ Database utilities test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Database utilities test failed: {e}")
        return False

def main():
    """Run all migration and schema tests"""
    print("Running migration and schema tests...\n")
    
    tests = [
        test_alembic_configuration,
        test_migration_content,
        test_model_metadata,
        test_database_utilities
    ]
    
    results = []
    for test in tests:
        results.append(test())
        print()  # Add spacing between tests
    
    if all(results):
        print("✅ All migration and schema tests passed!")
    else:
        print("❌ Some migration and schema tests failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()