#!/usr/bin/env python3
"""
Simple Test Data Generation (No External Dependencies)

Creates basic test data without requiring external libraries like reportlab.
This is for testing the system functionality.
"""

import json
import os
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any
import random


def create_simple_test_documents():
    """Create simple test documents without external dependencies"""
    docs_dir = Path("backend/tests/test_data/documents")
    docs_dir.mkdir(parents=True, exist_ok=True)
    
    # Create simple text files as placeholders
    test_files = [
        ("small_text.txt", "This is a small test document.\n\nIt contains basic text for testing purposes.\n\nChapter 1: Introduction\nThis chapter introduces the topic.\n\nChapter 2: Details\nThis chapter provides more details."),
        ("medium_document.txt", "This is a medium-sized test document.\n\n" + "Sample content paragraph. " * 50 + "\n\nChapter 1: Overview\n" + "Content for chapter 1. " * 20),
        ("large_document.txt", "This is a large test document.\n\n" + "Sample content paragraph with more text. " * 200 + "\n\nChapter 1: Introduction\n" + "Detailed content. " * 50)
    ]
    
    for filename, content in test_files:
        file_path = docs_dir / filename
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Created {file_path}")


def create_synthetic_test_data():
    """Create synthetic test data"""
    synthetic_dir = Path("backend/tests/test_data/synthetic")
    synthetic_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate user profiles
    users = []
    for i in range(20):
        user = {
            "id": str(uuid.uuid4()),
            "username": f"test_user_{i}",
            "email": f"user{i}@example.com",
            "full_name": f"Test User {i}",
            "created_at": (datetime.now() - timedelta(days=random.randint(1, 365))).isoformat(),
            "preferences": {
                "language": random.choice(["en", "es", "fr"]),
                "theme": random.choice(["light", "dark"]),
                "notifications_enabled": random.choice([True, False])
            },
            "stats": {
                "total_documents": random.randint(1, 50),
                "total_cards_reviewed": random.randint(10, 1000),
                "study_streak_days": random.randint(0, 100)
            }
        }
        users.append(user)
    
    with open(synthetic_dir / "user_profiles.json", 'w') as f:
        json.dump(users, f, indent=2)
    print(f"Created {synthetic_dir / 'user_profiles.json'}")
    
    # Generate document metadata
    documents = []
    for i in range(50):
        doc = {
            "id": str(uuid.uuid4()),
            "filename": f"test_document_{i}.pdf",
            "title": f"Test Document {i}",
            "file_size": random.randint(100000, 10000000),
            "page_count": random.randint(1, 100),
            "language": random.choice(["en", "es", "fr"]),
            "upload_date": (datetime.now() - timedelta(days=random.randint(1, 180))).isoformat(),
            "processing_status": random.choice(["completed", "processing", "failed"]),
            "complexity_score": random.uniform(0.1, 1.0)
        }
        documents.append(doc)
    
    with open(synthetic_dir / "document_metadata.json", 'w') as f:
        json.dump(documents, f, indent=2)
    print(f"Created {synthetic_dir / 'document_metadata.json'}")
    
    # Generate flashcards
    flashcards = []
    for i in range(100):
        card = {
            "id": str(uuid.uuid4()),
            "document_id": random.choice(documents)["id"],
            "type": random.choice(["basic", "cloze", "multiple_choice"]),
            "front": f"Question {i}: What is the main concept?",
            "back": f"Answer {i}: The main concept is...",
            "difficulty": random.uniform(0.1, 1.0),
            "created_at": (datetime.now() - timedelta(days=random.randint(1, 90))).isoformat()
        }
        flashcards.append(card)
    
    with open(synthetic_dir / "flashcards.json", 'w') as f:
        json.dump(flashcards, f, indent=2)
    print(f"Created {synthetic_dir / 'flashcards.json'}")


def create_performance_baselines():
    """Create simple performance baselines"""
    perf_dir = Path("backend/tests/test_data/performance")
    perf_dir.mkdir(parents=True, exist_ok=True)
    
    baselines = [
        {
            "metric_name": "document_processing_time",
            "test_case": "small_document_processing",
            "baseline_value": 5.2,
            "unit": "seconds",
            "confidence_interval": [4.1, 6.3],
            "sample_size": 50,
            "environment": "test",
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "metadata": {
                "file_size_mb": 2.0,
                "page_count": 5
            }
        },
        {
            "metric_name": "search_response_time",
            "test_case": "full_text_search",
            "baseline_value": 145.0,
            "unit": "milliseconds",
            "confidence_interval": [120.0, 170.0],
            "sample_size": 100,
            "environment": "test",
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "metadata": {
                "corpus_size": 100,
                "query_length": 3
            }
        }
    ]
    
    with open(perf_dir / "baselines.json", 'w') as f:
        json.dump(baselines, f, indent=2)
    print(f"Created {perf_dir / 'baselines.json'}")
    
    # Create empty metrics history
    with open(perf_dir / "metrics_history.json", 'w') as f:
        json.dump([], f, indent=2)
    print(f"Created {perf_dir / 'metrics_history.json'}")


def show_test_data_stats():
    """Show statistics about generated test data"""
    base_dir = Path("backend/tests/test_data")
    
    if not base_dir.exists():
        print("No test data found. Run generation first.")
        return
    
    print("\n=== Test Data Statistics ===")
    
    total_size = 0
    file_counts = {}
    
    for file_path in base_dir.rglob("*"):
        if file_path.is_file():
            size = file_path.stat().st_size
            total_size += size
            
            ext = file_path.suffix.lower()
            file_counts[ext] = file_counts.get(ext, 0) + 1
    
    print(f"Total size: {total_size / 1024:.2f} KB")
    print(f"Total files: {sum(file_counts.values())}")
    
    print("\nFile counts by type:")
    for ext, count in sorted(file_counts.items()):
        print(f"  {ext or '(no extension)'}: {count}")
    
    # Check specific directories
    dirs_to_check = ["documents", "synthetic", "performance"]
    for dir_name in dirs_to_check:
        dir_path = base_dir / dir_name
        if dir_path.exists():
            file_count = len(list(dir_path.glob("*")))
            print(f"\n{dir_name}/ directory: {file_count} files")


def cleanup_test_data():
    """Clean up all generated test data"""
    base_dir = Path("backend/tests/test_data")
    
    if not base_dir.exists():
        print("No test data to clean up.")
        return
    
    import shutil
    
    # Remove generated directories
    dirs_to_remove = ["documents", "synthetic", "performance", "isolated", "snapshots", "results"]
    
    for dir_name in dirs_to_remove:
        dir_path = base_dir / dir_name
        if dir_path.exists():
            shutil.rmtree(dir_path)
            print(f"Removed {dir_path}")
    
    print("Test data cleanup complete!")


def main():
    """Main function for simple test data management"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python test_simple_generation.py <command>")
        print("Commands:")
        print("  generate - Generate all test data")
        print("  stats    - Show test data statistics")
        print("  cleanup  - Clean up all test data")
        return
    
    command = sys.argv[1]
    
    if command == "generate":
        print("Generating simple test data...")
        create_simple_test_documents()
        create_synthetic_test_data()
        create_performance_baselines()
        print("\n✓ Test data generation complete!")
        
    elif command == "stats":
        show_test_data_stats()
        
    elif command == "cleanup":
        cleanup_test_data()
        
    else:
        print(f"Unknown command: {command}")


if __name__ == "__main__":
    main()