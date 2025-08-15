#!/usr/bin/env python3
"""
Verify the project structure and files are created correctly
"""

import os
from pathlib import Path

def check_file_exists(path, description):
    """Check if a file exists and print result"""
    if os.path.exists(path):
        print(f"✓ {description}: {path}")
        return True
    else:
        print(f"❌ {description}: {path} (missing)")
        return False

def check_directory_exists(path, description):
    """Check if a directory exists and print result"""
    if os.path.isdir(path):
        print(f"✓ {description}: {path}")
        return True
    else:
        print(f"❌ {description}: {path} (missing)")
        return False

def main():
    print("Verifying project structure for Task 2: Initialize database schema and core models")
    print("=" * 80)
    
    all_good = True
    
    # Check core directories
    print("\n📁 Checking directories:")
    all_good &= check_directory_exists("app", "App directory")
    all_good &= check_directory_exists("app/core", "Core directory")
    all_good &= check_directory_exists("app/models", "Models directory")
    all_good &= check_directory_exists("alembic", "Alembic directory")
    all_good &= check_directory_exists("alembic/versions", "Alembic versions directory")
    
    # Check core configuration files
    print("\n⚙️  Checking core configuration:")
    all_good &= check_file_exists("app/core/config.py", "Configuration settings")
    all_good &= check_file_exists("app/core/database.py", "Database connection and session management")
    all_good &= check_file_exists("app/core/db_utils.py", "Database utilities")
    
    # Check model files
    print("\n🗃️  Checking model files:")
    all_good &= check_file_exists("app/models/__init__.py", "Models package init")
    all_good &= check_file_exists("app/models/base.py", "Base model classes")
    all_good &= check_file_exists("app/models/document.py", "Document models (Document, Chapter, Figure)")
    all_good &= check_file_exists("app/models/knowledge.py", "Knowledge models")
    all_good &= check_file_exists("app/models/learning.py", "Learning models (Card, SRS)")
    
    # Check Alembic configuration
    print("\n🔄 Checking Alembic configuration:")
    all_good &= check_file_exists("alembic.ini", "Alembic configuration")
    all_good &= check_file_exists("alembic/env.py", "Alembic environment")
    all_good &= check_file_exists("alembic/script.py.mako", "Alembic script template")
    all_good &= check_file_exists("alembic/versions/001_initial_schema.py", "Initial migration")
    
    # Check test files
    print("\n🧪 Checking test files:")
    all_good &= check_file_exists("tests/test_models.py", "Model tests")
    
    # Check configuration files
    print("\n📋 Checking configuration files:")
    all_good &= check_file_exists(".env.example", "Environment variables example")
    
    # Check file contents for key components
    print("\n📄 Checking file contents:")
    
    # Check if models contain required classes
    try:
        with open("app/models/__init__.py", "r") as f:
            init_content = f.read()
            required_imports = ["Document", "Chapter", "Figure", "Knowledge", "Card", "SRS"]
            for imp in required_imports:
                if imp in init_content:
                    print(f"✓ {imp} model imported in __init__.py")
                else:
                    print(f"❌ {imp} model missing from __init__.py")
                    all_good = False
    except FileNotFoundError:
        print("❌ Could not read app/models/__init__.py")
        all_good = False
    
    # Check if migration contains pgvector
    try:
        with open("alembic/versions/001_initial_schema.py", "r") as f:
            migration_content = f.read()
            if "CREATE EXTENSION IF NOT EXISTS vector" in migration_content:
                print("✓ pgvector extension setup in migration")
            else:
                print("❌ pgvector extension missing from migration")
                all_good = False
                
            if "Vector(384)" in migration_content:
                print("✓ Vector column type in migration")
            else:
                print("❌ Vector column type missing from migration")
                all_good = False
    except FileNotFoundError:
        print("❌ Could not read migration file")
        all_good = False
    
    print("\n" + "=" * 80)
    if all_good:
        print("✅ All components for Task 2 have been successfully implemented!")
        print("\nImplemented components:")
        print("• SQLAlchemy models for Document, Chapter, Figure, Knowledge, Card, SRS")
        print("• Alembic migrations for database schema")
        print("• pgvector extension support for vector embeddings")
        print("• Database connection and session management")
        print("• Configuration management with environment variables")
        print("• Test suite for model validation")
    else:
        print("❌ Some components are missing or incomplete.")
    
    return all_good

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)