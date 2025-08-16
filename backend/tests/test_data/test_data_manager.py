"""
Test Data Manager

Manages test data lifecycle including cleanup, isolation, and state management.
Ensures tests run in isolated environments with clean data states.
"""

import os
import shutil
import json
import sqlite3
import tempfile
from pathlib import Path
from typing import Dict, List, Any, Optional, Set
from contextlib import contextmanager
from datetime import datetime
import uuid
import logging


class TestDataManager:
    """Manages test data lifecycle and isolation"""
    
    def __init__(self, base_dir: str = "backend/tests/test_data"):
        self.base_dir = Path(base_dir)
        self.temp_dirs: Set[Path] = set()
        self.temp_databases: Set[Path] = set()
        self.active_contexts: Dict[str, Dict] = {}
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        
        # Ensure base directories exist
        self.base_dir.mkdir(parents=True, exist_ok=True)
        (self.base_dir / "isolated").mkdir(exist_ok=True)
        (self.base_dir / "snapshots").mkdir(exist_ok=True)
        
    @contextmanager
    def isolated_test_environment(self, test_name: str, data_sets: Optional[List[str]] = None):
        """
        Create isolated test environment with clean data state
        
        Args:
            test_name: Name of the test for tracking
            data_sets: List of data sets to include (e.g., ['users', 'documents'])
        """
        context_id = f"{test_name}_{uuid.uuid4().hex[:8]}"
        temp_dir = self.base_dir / "isolated" / context_id
        
        try:
            # Create isolated directory
            temp_dir.mkdir(parents=True, exist_ok=True)
            self.temp_dirs.add(temp_dir)
            
            # Setup isolated database
            db_path = temp_dir / "test.db"
            self._setup_test_database(db_path)
            self.temp_databases.add(db_path)
            
            # Copy required data sets
            if data_sets:
                self._copy_data_sets(temp_dir, data_sets)
            
            # Create context
            context = {
                "id": context_id,
                "test_name": test_name,
                "temp_dir": temp_dir,
                "db_path": db_path,
                "created_at": datetime.now().isoformat(),
                "data_sets": data_sets or []
            }
            
            self.active_contexts[context_id] = context
            self.logger.info(f"Created isolated environment for {test_name}: {context_id}")
            
            yield context
            
        finally:
            # Cleanup
            self._cleanup_context(context_id)
            
    def create_data_snapshot(self, name: str, description: str = "") -> str:
        """
        Create a snapshot of current test data state
        
        Args:
            name: Snapshot name
            description: Optional description
            
        Returns:
            Snapshot ID
        """
        snapshot_id = f"{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        snapshot_dir = self.base_dir / "snapshots" / snapshot_id
        snapshot_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy all data files
        for data_file in self.base_dir.glob("*.json"):
            if data_file.name not in ["snapshots.json"]:
                shutil.copy2(data_file, snapshot_dir)
                
        # Copy synthetic data
        synthetic_dir = self.base_dir / "synthetic"
        if synthetic_dir.exists():
            shutil.copytree(synthetic_dir, snapshot_dir / "synthetic")
            
        # Copy documents
        docs_dir = self.base_dir / "documents"
        if docs_dir.exists():
            shutil.copytree(docs_dir, snapshot_dir / "documents")
            
        # Save snapshot metadata
        snapshot_info = {
            "id": snapshot_id,
            "name": name,
            "description": description,
            "created_at": datetime.now().isoformat(),
            "files_count": len(list(snapshot_dir.rglob("*"))),
            "size_bytes": sum(f.stat().st_size for f in snapshot_dir.rglob("*") if f.is_file())
        }
        
        # Update snapshots registry
        snapshots_file = self.base_dir / "snapshots.json"
        snapshots = []
        if snapshots_file.exists():
            with open(snapshots_file, 'r') as f:
                snapshots = json.load(f)
                
        snapshots.append(snapshot_info)
        
        with open(snapshots_file, 'w') as f:
            json.dump(snapshots, f, indent=2)
            
        self.logger.info(f"Created snapshot {snapshot_id}")
        return snapshot_id
        
    def restore_data_snapshot(self, snapshot_id: str):
        """
        Restore test data from a snapshot
        
        Args:
            snapshot_id: ID of snapshot to restore
        """
        snapshot_dir = self.base_dir / "snapshots" / snapshot_id
        
        if not snapshot_dir.exists():
            raise ValueError(f"Snapshot {snapshot_id} not found")
            
        # Clear current data
        self.cleanup_all_test_data()
        
        # Restore from snapshot
        for item in snapshot_dir.iterdir():
            if item.is_file():
                shutil.copy2(item, self.base_dir)
            elif item.is_dir() and item.name in ["synthetic", "documents"]:
                target_dir = self.base_dir / item.name
                if target_dir.exists():
                    shutil.rmtree(target_dir)
                shutil.copytree(item, target_dir)
                
        self.logger.info(f"Restored snapshot {snapshot_id}")
        
    def cleanup_all_test_data(self):
        """Clean up all test data files and directories"""
        # Remove JSON data files
        for json_file in self.base_dir.glob("*.json"):
            if json_file.name not in ["snapshots.json"]:
                json_file.unlink()
                
        # Remove synthetic data
        synthetic_dir = self.base_dir / "synthetic"
        if synthetic_dir.exists():
            shutil.rmtree(synthetic_dir)
            
        # Remove generated documents (keep templates)
        docs_dir = self.base_dir / "documents"
        if docs_dir.exists():
            for doc_file in docs_dir.glob("*.pdf"):
                doc_file.unlink()
            for doc_file in docs_dir.glob("*.docx"):
                doc_file.unlink()
            for doc_file in docs_dir.glob("*.md"):
                if doc_file.name != "README.md":
                    doc_file.unlink()
                    
        # Clean up isolated environments
        isolated_dir = self.base_dir / "isolated"
        if isolated_dir.exists():
            shutil.rmtree(isolated_dir)
            isolated_dir.mkdir()
            
        self.logger.info("Cleaned up all test data")
        
    def cleanup_old_snapshots(self, keep_count: int = 10):
        """
        Clean up old snapshots, keeping only the most recent ones
        
        Args:
            keep_count: Number of snapshots to keep
        """
        snapshots_file = self.base_dir / "snapshots.json"
        if not snapshots_file.exists():
            return
            
        with open(snapshots_file, 'r') as f:
            snapshots = json.load(f)
            
        # Sort by creation date (newest first)
        snapshots.sort(key=lambda x: x['created_at'], reverse=True)
        
        # Remove old snapshots
        snapshots_to_remove = snapshots[keep_count:]
        for snapshot in snapshots_to_remove:
            snapshot_dir = self.base_dir / "snapshots" / snapshot['id']
            if snapshot_dir.exists():
                shutil.rmtree(snapshot_dir)
                self.logger.info(f"Removed old snapshot {snapshot['id']}")
                
        # Update registry
        remaining_snapshots = snapshots[:keep_count]
        with open(snapshots_file, 'w') as f:
            json.dump(remaining_snapshots, f, indent=2)
            
    def get_test_data_stats(self) -> Dict[str, Any]:
        """Get statistics about test data"""
        stats = {
            "total_size_bytes": 0,
            "file_counts": {},
            "snapshot_count": 0,
            "active_contexts": len(self.active_contexts),
            "temp_dirs": len(self.temp_dirs),
            "temp_databases": len(self.temp_databases)
        }
        
        # Calculate total size and file counts
        for file_path in self.base_dir.rglob("*"):
            if file_path.is_file():
                stats["total_size_bytes"] += file_path.stat().st_size
                
                file_type = file_path.suffix.lower()
                stats["file_counts"][file_type] = stats["file_counts"].get(file_type, 0) + 1
                
        # Count snapshots
        snapshots_file = self.base_dir / "snapshots.json"
        if snapshots_file.exists():
            with open(snapshots_file, 'r') as f:
                snapshots = json.load(f)
                stats["snapshot_count"] = len(snapshots)
                
        return stats
        
    def validate_test_data_integrity(self) -> Dict[str, Any]:
        """Validate integrity of test data"""
        validation_results = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "checked_files": 0,
            "corrupted_files": []
        }
        
        # Check JSON files
        for json_file in self.base_dir.rglob("*.json"):
            validation_results["checked_files"] += 1
            try:
                with open(json_file, 'r') as f:
                    json.load(f)
            except json.JSONDecodeError as e:
                validation_results["valid"] = False
                validation_results["errors"].append(f"Invalid JSON in {json_file}: {e}")
                validation_results["corrupted_files"].append(str(json_file))
                
        # Check database files
        for db_file in self.base_dir.rglob("*.db"):
            validation_results["checked_files"] += 1
            try:
                conn = sqlite3.connect(str(db_file))
                conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
                conn.close()
            except sqlite3.Error as e:
                validation_results["valid"] = False
                validation_results["errors"].append(f"Invalid database {db_file}: {e}")
                validation_results["corrupted_files"].append(str(db_file))
                
        # Check for missing required files
        required_files = ["README.md"]
        for required_file in required_files:
            file_path = self.base_dir / "documents" / required_file
            if not file_path.exists():
                validation_results["warnings"].append(f"Missing required file: {required_file}")
                
        return validation_results
        
    def _setup_test_database(self, db_path: Path):
        """Setup isolated test database"""
        conn = sqlite3.connect(str(db_path))
        
        # Create basic tables for testing
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS test_users (
                id TEXT PRIMARY KEY,
                username TEXT UNIQUE,
                email TEXT,
                created_at TEXT
            );
            
            CREATE TABLE IF NOT EXISTS test_documents (
                id TEXT PRIMARY KEY,
                user_id TEXT,
                filename TEXT,
                status TEXT,
                created_at TEXT,
                FOREIGN KEY (user_id) REFERENCES test_users (id)
            );
            
            CREATE TABLE IF NOT EXISTS test_cards (
                id TEXT PRIMARY KEY,
                document_id TEXT,
                front TEXT,
                back TEXT,
                difficulty REAL,
                created_at TEXT,
                FOREIGN KEY (document_id) REFERENCES test_documents (id)
            );
            
            CREATE TABLE IF NOT EXISTS test_reviews (
                id TEXT PRIMARY KEY,
                card_id TEXT,
                user_id TEXT,
                grade INTEGER,
                response_time INTEGER,
                reviewed_at TEXT,
                FOREIGN KEY (card_id) REFERENCES test_cards (id),
                FOREIGN KEY (user_id) REFERENCES test_users (id)
            );
        """)
        
        conn.close()
        
    def _copy_data_sets(self, target_dir: Path, data_sets: List[str]):
        """Copy specified data sets to isolated environment"""
        synthetic_dir = self.base_dir / "synthetic"
        
        for data_set in data_sets:
            source_file = synthetic_dir / f"{data_set}.json"
            if source_file.exists():
                shutil.copy2(source_file, target_dir)
            else:
                self.logger.warning(f"Data set {data_set} not found")
                
    def _cleanup_context(self, context_id: str):
        """Clean up specific test context"""
        if context_id in self.active_contexts:
            context = self.active_contexts[context_id]
            
            # Remove temporary directory
            temp_dir = context["temp_dir"]
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
                self.temp_dirs.discard(temp_dir)
                
            # Remove from active contexts
            del self.active_contexts[context_id]
            
            self.logger.info(f"Cleaned up context {context_id}")
            
    def __del__(self):
        """Cleanup on destruction"""
        # Clean up any remaining temporary resources
        for temp_dir in list(self.temp_dirs):
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
                
        for db_path in list(self.temp_databases):
            if db_path.exists():
                db_path.unlink()


class TestDataFixtures:
    """Provides common test data fixtures"""
    
    def __init__(self, data_manager: TestDataManager):
        self.data_manager = data_manager
        
    def get_sample_user(self) -> Dict[str, Any]:
        """Get a sample user for testing"""
        return {
            "id": str(uuid.uuid4()),
            "username": "test_user",
            "email": "test@example.com",
            "full_name": "Test User",
            "created_at": datetime.now().isoformat(),
            "preferences": {
                "language": "en",
                "theme": "light",
                "notifications_enabled": True
            }
        }
        
    def get_sample_document(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Get a sample document for testing"""
        return {
            "id": str(uuid.uuid4()),
            "user_id": user_id or str(uuid.uuid4()),
            "filename": "test_document.pdf",
            "title": "Test Document",
            "file_size": 1024000,
            "page_count": 10,
            "status": "completed",
            "created_at": datetime.now().isoformat()
        }
        
    def get_sample_flashcard(self, document_id: Optional[str] = None) -> Dict[str, Any]:
        """Get a sample flashcard for testing"""
        return {
            "id": str(uuid.uuid4()),
            "document_id": document_id or str(uuid.uuid4()),
            "type": "basic",
            "front": "What is machine learning?",
            "back": "A subset of AI that focuses on algorithms that can learn from data",
            "difficulty": 0.5,
            "created_at": datetime.now().isoformat()
        }
        
    def get_sample_review(self, card_id: Optional[str] = None, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Get a sample review for testing"""
        return {
            "id": str(uuid.uuid4()),
            "card_id": card_id or str(uuid.uuid4()),
            "user_id": user_id or str(uuid.uuid4()),
            "grade": 4,
            "response_time_ms": 3000,
            "reviewed_at": datetime.now().isoformat()
        }


# Global instance for easy access
test_data_manager = TestDataManager()
test_fixtures = TestDataFixtures(test_data_manager)