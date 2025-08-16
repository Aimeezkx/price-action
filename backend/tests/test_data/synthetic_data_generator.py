"""
Synthetic Test Data Generator

Generates synthetic test data for various testing scenarios including
user data, document metadata, learning progress, and system states.
"""

import json
import random
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path
import faker


class SyntheticDataGenerator:
    """Generate synthetic test data for various testing scenarios"""
    
    def __init__(self, output_dir: str = "backend/tests/test_data/synthetic"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.fake = faker.Faker()
        
    def generate_all_synthetic_data(self):
        """Generate complete set of synthetic test data"""
        print("Generating synthetic test data...")
        
        # User and authentication data
        self.generate_user_profiles()
        self.generate_user_sessions()
        
        # Document and content data
        self.generate_document_metadata()
        self.generate_chapter_data()
        self.generate_knowledge_points()
        self.generate_flashcards()
        
        # Learning and progress data
        self.generate_learning_sessions()
        self.generate_srs_states()
        self.generate_review_history()
        
        # Search and interaction data
        self.generate_search_queries()
        self.generate_user_interactions()
        
        # Performance and system data
        self.generate_performance_metrics()
        self.generate_error_scenarios()
        
        # Load testing data
        self.generate_load_test_scenarios()
        
        print("Synthetic test data generation complete!")
        
    def generate_user_profiles(self):
        """Generate diverse user profiles for testing"""
        users = []
        
        # Different user types
        user_types = [
            {"type": "student", "documents_per_user": (5, 20), "activity_level": "high"},
            {"type": "researcher", "documents_per_user": (20, 100), "activity_level": "medium"},
            {"type": "professional", "documents_per_user": (10, 50), "activity_level": "medium"},
            {"type": "casual", "documents_per_user": (1, 10), "activity_level": "low"},
        ]
        
        for user_type in user_types:
            for i in range(25):  # 25 users per type
                user = {
                    "id": str(uuid.uuid4()),
                    "username": self.fake.user_name(),
                    "email": self.fake.email(),
                    "full_name": self.fake.name(),
                    "user_type": user_type["type"],
                    "created_at": self.fake.date_time_between(start_date='-2y', end_date='now').isoformat(),
                    "last_login": self.fake.date_time_between(start_date='-30d', end_date='now').isoformat(),
                    "preferences": {
                        "language": random.choice(["en", "es", "fr", "de", "zh"]),
                        "theme": random.choice(["light", "dark", "auto"]),
                        "notifications_enabled": random.choice([True, False]),
                        "privacy_mode": random.choice([True, False]),
                        "cards_per_session": random.randint(10, 50),
                        "difficulty_preference": random.choice(["easy", "medium", "hard", "adaptive"])
                    },
                    "stats": {
                        "total_documents": random.randint(*user_type["documents_per_user"]),
                        "total_cards_reviewed": random.randint(100, 5000),
                        "study_streak_days": random.randint(0, 365),
                        "average_session_duration": random.randint(300, 3600),  # seconds
                        "total_study_time": random.randint(3600, 360000)  # seconds
                    }
                }
                users.append(user)
                
        self._save_json("user_profiles.json", users)
        
    def generate_user_sessions(self):
        """Generate user session data for testing"""
        sessions = []
        
        for i in range(500):  # 500 sessions
            session_start = self.fake.date_time_between(start_date='-30d', end_date='now')
            session_duration = random.randint(60, 7200)  # 1 minute to 2 hours
            
            session = {
                "id": str(uuid.uuid4()),
                "user_id": str(uuid.uuid4()),
                "session_token": self.fake.sha256(),
                "start_time": session_start.isoformat(),
                "end_time": (session_start + timedelta(seconds=session_duration)).isoformat(),
                "duration_seconds": session_duration,
                "ip_address": self.fake.ipv4(),
                "user_agent": self.fake.user_agent(),
                "device_type": random.choice(["desktop", "mobile", "tablet"]),
                "activities": [
                    {
                        "action": random.choice(["document_upload", "card_review", "search", "chapter_browse"]),
                        "timestamp": (session_start + timedelta(seconds=random.randint(0, session_duration))).isoformat(),
                        "details": {"duration": random.randint(10, 300)}
                    }
                    for _ in range(random.randint(1, 20))
                ]
            }
            sessions.append(session)
            
        self._save_json("user_sessions.json", sessions)
        
    def generate_document_metadata(self):
        """Generate document metadata for testing"""
        documents = []
        
        document_types = [
            {"type": "academic_paper", "page_range": (5, 30), "complexity": "high"},
            {"type": "textbook_chapter", "page_range": (10, 50), "complexity": "medium"},
            {"type": "manual", "page_range": (20, 100), "complexity": "medium"},
            {"type": "article", "page_range": (3, 15), "complexity": "low"},
            {"type": "thesis", "page_range": (50, 300), "complexity": "high"},
        ]
        
        subjects = ["computer_science", "mathematics", "physics", "biology", "chemistry", 
                   "history", "literature", "business", "psychology", "engineering"]
        
        for i in range(200):  # 200 documents
            doc_type = random.choice(document_types)
            
            document = {
                "id": str(uuid.uuid4()),
                "filename": f"{self.fake.word()}_{self.fake.word()}.pdf",
                "title": self.fake.sentence(nb_words=6).rstrip('.'),
                "author": self.fake.name(),
                "subject": random.choice(subjects),
                "document_type": doc_type["type"],
                "file_size": random.randint(100000, 50000000),  # 100KB to 50MB
                "page_count": random.randint(*doc_type["page_range"]),
                "language": random.choice(["en", "es", "fr", "de", "zh"]),
                "upload_date": self.fake.date_time_between(start_date='-1y', end_date='now').isoformat(),
                "processing_status": random.choice(["completed", "processing", "failed", "pending"]),
                "processing_time_seconds": random.randint(10, 600),
                "complexity_score": random.uniform(0.1, 1.0),
                "readability_score": random.uniform(0.2, 0.9),
                "metadata": {
                    "creation_date": self.fake.date_time_between(start_date='-5y', end_date='-1y').isoformat(),
                    "modification_date": self.fake.date_time_between(start_date='-1y', end_date='now').isoformat(),
                    "keywords": [self.fake.word() for _ in range(random.randint(3, 10))],
                    "has_images": random.choice([True, False]),
                    "has_tables": random.choice([True, False]),
                    "has_formulas": random.choice([True, False]),
                    "image_count": random.randint(0, 20),
                    "table_count": random.randint(0, 10)
                }
            }
            documents.append(document)
            
        self._save_json("document_metadata.json", documents)
        
    def generate_chapter_data(self):
        """Generate chapter structure data"""
        chapters = []
        
        for doc_id in range(50):  # 50 documents with chapters
            doc_uuid = str(uuid.uuid4())
            chapter_count = random.randint(3, 15)
            
            for chapter_num in range(1, chapter_count + 1):
                chapter = {
                    "id": str(uuid.uuid4()),
                    "document_id": doc_uuid,
                    "chapter_number": chapter_num,
                    "title": f"Chapter {chapter_num}: {self.fake.sentence(nb_words=4).rstrip('.')}",
                    "start_page": chapter_num * 5 - 4,
                    "end_page": chapter_num * 5,
                    "word_count": random.randint(500, 5000),
                    "difficulty_level": random.uniform(0.1, 1.0),
                    "key_concepts": [self.fake.word() for _ in range(random.randint(3, 8))],
                    "summary": self.fake.paragraph(nb_sentences=3),
                    "subsections": [
                        {
                            "title": self.fake.sentence(nb_words=3).rstrip('.'),
                            "start_page": chapter_num * 5 - 4 + i,
                            "key_points": [self.fake.sentence() for _ in range(random.randint(2, 5))]
                        }
                        for i in range(random.randint(2, 5))
                    ]
                }
                chapters.append(chapter)
                
        self._save_json("chapter_data.json", chapters)
        
    def generate_knowledge_points(self):
        """Generate knowledge points extracted from documents"""
        knowledge_points = []
        
        knowledge_types = ["definition", "concept", "formula", "example", "principle", "fact"]
        
        for i in range(1000):  # 1000 knowledge points
            knowledge_point = {
                "id": str(uuid.uuid4()),
                "document_id": str(uuid.uuid4()),
                "chapter_id": str(uuid.uuid4()),
                "type": random.choice(knowledge_types),
                "title": self.fake.sentence(nb_words=4).rstrip('.'),
                "content": self.fake.paragraph(nb_sentences=random.randint(2, 5)),
                "importance_score": random.uniform(0.1, 1.0),
                "difficulty_level": random.uniform(0.1, 1.0),
                "page_number": random.randint(1, 100),
                "position": {
                    "x": random.uniform(0, 1),
                    "y": random.uniform(0, 1),
                    "width": random.uniform(0.1, 0.8),
                    "height": random.uniform(0.05, 0.3)
                },
                "related_concepts": [self.fake.word() for _ in range(random.randint(1, 5))],
                "prerequisites": [str(uuid.uuid4()) for _ in range(random.randint(0, 3))],
                "extraction_confidence": random.uniform(0.5, 1.0),
                "created_at": self.fake.date_time_between(start_date='-6m', end_date='now').isoformat()
            }
            knowledge_points.append(knowledge_point)
            
        self._save_json("knowledge_points.json", knowledge_points)
        
    def generate_flashcards(self):
        """Generate flashcard data"""
        flashcards = []
        
        card_types = ["basic", "cloze", "multiple_choice", "true_false", "image_occlusion"]
        
        for i in range(2000):  # 2000 flashcards
            card_type = random.choice(card_types)
            
            base_card = {
                "id": str(uuid.uuid4()),
                "knowledge_point_id": str(uuid.uuid4()),
                "document_id": str(uuid.uuid4()),
                "chapter_id": str(uuid.uuid4()),
                "type": card_type,
                "difficulty": random.uniform(0.1, 1.0),
                "quality_score": random.uniform(0.3, 1.0),
                "created_at": self.fake.date_time_between(start_date='-6m', end_date='now').isoformat(),
                "tags": [self.fake.word() for _ in range(random.randint(1, 5))]
            }
            
            if card_type == "basic":
                base_card.update({
                    "front": self.fake.sentence(nb_words=8),
                    "back": self.fake.paragraph(nb_sentences=2)
                })
            elif card_type == "cloze":
                sentence = self.fake.sentence(nb_words=12)
                words = sentence.split()
                cloze_word = random.choice(words[2:-2])  # Don't cloze first/last words
                base_card.update({
                    "text": sentence.replace(cloze_word, "{{c1::" + cloze_word + "}}"),
                    "cloze_count": 1
                })
            elif card_type == "multiple_choice":
                base_card.update({
                    "question": self.fake.sentence(nb_words=10),
                    "options": [self.fake.sentence(nb_words=5) for _ in range(4)],
                    "correct_answer": random.randint(0, 3),
                    "explanation": self.fake.paragraph(nb_sentences=2)
                })
            elif card_type == "true_false":
                base_card.update({
                    "statement": self.fake.sentence(nb_words=12),
                    "correct_answer": random.choice([True, False]),
                    "explanation": self.fake.paragraph(nb_sentences=1)
                })
            elif card_type == "image_occlusion":
                base_card.update({
                    "image_path": f"/images/{uuid.uuid4()}.png",
                    "occlusions": [
                        {
                            "id": str(uuid.uuid4()),
                            "x": random.uniform(0, 0.8),
                            "y": random.uniform(0, 0.8),
                            "width": random.uniform(0.1, 0.3),
                            "height": random.uniform(0.1, 0.3),
                            "label": self.fake.word()
                        }
                        for _ in range(random.randint(1, 5))
                    ]
                })
                
            flashcards.append(base_card)
            
        self._save_json("flashcards.json", flashcards)
        
    def generate_learning_sessions(self):
        """Generate learning session data"""
        sessions = []
        
        for i in range(300):  # 300 learning sessions
            session_start = self.fake.date_time_between(start_date='-3m', end_date='now')
            session_duration = random.randint(300, 3600)  # 5 minutes to 1 hour
            
            session = {
                "id": str(uuid.uuid4()),
                "user_id": str(uuid.uuid4()),
                "start_time": session_start.isoformat(),
                "end_time": (session_start + timedelta(seconds=session_duration)).isoformat(),
                "duration_seconds": session_duration,
                "session_type": random.choice(["review", "new_cards", "mixed", "cram"]),
                "cards_studied": random.randint(5, 100),
                "cards_correct": random.randint(0, 100),
                "average_response_time": random.uniform(2.0, 15.0),
                "performance_score": random.uniform(0.3, 1.0),
                "focus_score": random.uniform(0.5, 1.0),  # Based on response time consistency
                "interruptions": random.randint(0, 5),
                "device_type": random.choice(["desktop", "mobile", "tablet"]),
                "study_mode": random.choice(["spaced_repetition", "cramming", "review_mistakes"])
            }
            sessions.append(session)
            
        self._save_json("learning_sessions.json", sessions)
        
    def generate_srs_states(self):
        """Generate spaced repetition system states"""
        srs_states = []
        
        for i in range(2000):  # 2000 SRS states (one per card)
            last_review = self.fake.date_time_between(start_date='-3m', end_date='now')
            
            srs_state = {
                "id": str(uuid.uuid4()),
                "card_id": str(uuid.uuid4()),
                "user_id": str(uuid.uuid4()),
                "interval_days": random.choice([1, 2, 4, 8, 15, 30, 60, 120, 240]),
                "ease_factor": random.uniform(1.3, 3.0),
                "repetitions": random.randint(0, 20),
                "last_review": last_review.isoformat(),
                "next_review": (last_review + timedelta(days=random.randint(0, 30))).isoformat(),
                "review_count": random.randint(1, 50),
                "lapse_count": random.randint(0, 10),
                "average_grade": random.uniform(1.0, 5.0),
                "stability": random.uniform(0.1, 1.0),
                "difficulty": random.uniform(0.1, 1.0),
                "retrievability": random.uniform(0.1, 1.0),
                "last_grade": random.randint(1, 5),
                "streak": random.randint(0, 30),
                "mature": random.choice([True, False])
            }
            srs_states.append(srs_state)
            
        self._save_json("srs_states.json", srs_states)
        
    def generate_review_history(self):
        """Generate detailed review history"""
        reviews = []
        
        for i in range(5000):  # 5000 individual reviews
            review_time = self.fake.date_time_between(start_date='-3m', end_date='now')
            
            review = {
                "id": str(uuid.uuid4()),
                "card_id": str(uuid.uuid4()),
                "user_id": str(uuid.uuid4()),
                "session_id": str(uuid.uuid4()),
                "review_time": review_time.isoformat(),
                "grade": random.randint(1, 5),
                "response_time_ms": random.randint(500, 30000),
                "previous_interval": random.randint(1, 120),
                "new_interval": random.randint(1, 240),
                "ease_factor_before": random.uniform(1.3, 3.0),
                "ease_factor_after": random.uniform(1.3, 3.0),
                "was_correct": random.choice([True, False]),
                "hint_used": random.choice([True, False]),
                "review_type": random.choice(["learning", "review", "relearning", "cram"]),
                "device_type": random.choice(["desktop", "mobile", "tablet"]),
                "context": {
                    "time_of_day": review_time.hour,
                    "day_of_week": review_time.weekday(),
                    "study_streak": random.randint(0, 100)
                }
            }
            reviews.append(review)
            
        self._save_json("review_history.json", reviews)
        
    def generate_search_queries(self):
        """Generate search query data"""
        queries = []
        
        search_types = ["full_text", "semantic", "filtered", "advanced"]
        
        for i in range(1000):  # 1000 search queries
            query_time = self.fake.date_time_between(start_date='-1m', end_date='now')
            
            query = {
                "id": str(uuid.uuid4()),
                "user_id": str(uuid.uuid4()),
                "query_text": self.fake.sentence(nb_words=random.randint(2, 8)).rstrip('.'),
                "search_type": random.choice(search_types),
                "timestamp": query_time.isoformat(),
                "response_time_ms": random.randint(50, 2000),
                "result_count": random.randint(0, 100),
                "clicked_results": random.randint(0, 5),
                "filters_applied": {
                    "document_types": random.sample(["pdf", "docx", "md"], random.randint(0, 3)),
                    "date_range": random.choice([None, "last_week", "last_month", "last_year"]),
                    "difficulty_range": [random.uniform(0, 0.5), random.uniform(0.5, 1.0)] if random.choice([True, False]) else None,
                    "subjects": random.sample(["math", "science", "history", "literature"], random.randint(0, 2))
                },
                "satisfaction_score": random.uniform(0.1, 1.0),  # Implicit from user behavior
                "session_id": str(uuid.uuid4())
            }
            queries.append(query)
            
        self._save_json("search_queries.json", queries)
        
    def generate_user_interactions(self):
        """Generate user interaction events"""
        interactions = []
        
        interaction_types = [
            "page_view", "button_click", "scroll", "hover", "focus", "blur",
            "form_submit", "file_upload", "download", "share", "bookmark"
        ]
        
        for i in range(10000):  # 10000 interactions
            interaction_time = self.fake.date_time_between(start_date='-7d', end_date='now')
            
            interaction = {
                "id": str(uuid.uuid4()),
                "user_id": str(uuid.uuid4()),
                "session_id": str(uuid.uuid4()),
                "timestamp": interaction_time.isoformat(),
                "event_type": random.choice(interaction_types),
                "page_url": f"/app/{random.choice(['documents', 'study', 'search', 'profile'])}",
                "element_id": f"element_{random.randint(1, 100)}",
                "element_type": random.choice(["button", "link", "input", "div", "span"]),
                "coordinates": {
                    "x": random.randint(0, 1920),
                    "y": random.randint(0, 1080)
                },
                "viewport": {
                    "width": random.choice([1920, 1366, 1024, 768, 375]),
                    "height": random.choice([1080, 768, 600, 1024, 667])
                },
                "user_agent": self.fake.user_agent(),
                "duration_ms": random.randint(100, 5000) if random.choice([True, False]) else None
            }
            interactions.append(interaction)
            
        self._save_json("user_interactions.json", interactions)
        
    def generate_performance_metrics(self):
        """Generate performance metrics for testing"""
        metrics = []
        
        metric_types = [
            "response_time", "memory_usage", "cpu_usage", "disk_io",
            "network_latency", "database_query_time", "cache_hit_rate"
        ]
        
        for i in range(5000):  # 5000 metric data points
            timestamp = self.fake.date_time_between(start_date='-7d', end_date='now')
            
            metric = {
                "id": str(uuid.uuid4()),
                "timestamp": timestamp.isoformat(),
                "metric_type": random.choice(metric_types),
                "value": random.uniform(0.1, 100.0),
                "unit": random.choice(["ms", "MB", "%", "req/s", "bytes"]),
                "service": random.choice(["api", "database", "frontend", "worker", "cache"]),
                "endpoint": f"/api/{random.choice(['documents', 'cards', 'search', 'users'])}",
                "status_code": random.choice([200, 201, 400, 404, 500]),
                "user_id": str(uuid.uuid4()) if random.choice([True, False]) else None,
                "metadata": {
                    "server_id": f"server_{random.randint(1, 5)}",
                    "version": f"v{random.randint(1, 3)}.{random.randint(0, 9)}.{random.randint(0, 9)}",
                    "environment": random.choice(["development", "staging", "production"])
                }
            }
            metrics.append(metric)
            
        self._save_json("performance_metrics.json", metrics)
        
    def generate_error_scenarios(self):
        """Generate error scenarios for testing"""
        errors = []
        
        error_types = [
            "validation_error", "authentication_error", "authorization_error",
            "not_found_error", "server_error", "database_error", "network_error",
            "timeout_error", "rate_limit_error", "file_processing_error"
        ]
        
        for i in range(500):  # 500 error scenarios
            error_time = self.fake.date_time_between(start_date='-30d', end_date='now')
            
            error = {
                "id": str(uuid.uuid4()),
                "timestamp": error_time.isoformat(),
                "error_type": random.choice(error_types),
                "error_code": f"E{random.randint(1000, 9999)}",
                "message": self.fake.sentence(nb_words=8),
                "stack_trace": "\n".join([f"  at {self.fake.word()}.{self.fake.word()}({self.fake.file_name()}:{random.randint(1, 1000)})" for _ in range(random.randint(3, 10))]),
                "user_id": str(uuid.uuid4()) if random.choice([True, False]) else None,
                "session_id": str(uuid.uuid4()) if random.choice([True, False]) else None,
                "request_id": str(uuid.uuid4()),
                "endpoint": f"/api/{random.choice(['documents', 'cards', 'search', 'users'])}",
                "method": random.choice(["GET", "POST", "PUT", "DELETE"]),
                "status_code": random.choice([400, 401, 403, 404, 422, 500, 502, 503]),
                "user_agent": self.fake.user_agent(),
                "ip_address": self.fake.ipv4(),
                "severity": random.choice(["low", "medium", "high", "critical"]),
                "resolved": random.choice([True, False]),
                "resolution_time": random.randint(300, 86400) if random.choice([True, False]) else None
            }
            errors.append(error)
            
        self._save_json("error_scenarios.json", errors)
        
    def generate_load_test_scenarios(self):
        """Generate load test scenario configurations"""
        scenarios = []
        
        # Different load patterns
        load_patterns = [
            {"name": "steady_load", "users": 50, "duration": 300, "ramp_up": 60},
            {"name": "spike_test", "users": 200, "duration": 120, "ramp_up": 10},
            {"name": "stress_test", "users": 500, "duration": 600, "ramp_up": 120},
            {"name": "endurance_test", "users": 100, "duration": 3600, "ramp_up": 300},
            {"name": "volume_test", "users": 1000, "duration": 1800, "ramp_up": 600}
        ]
        
        for pattern in load_patterns:
            scenario = {
                "id": str(uuid.uuid4()),
                "name": pattern["name"],
                "description": f"Load test scenario: {pattern['name']}",
                "configuration": {
                    "concurrent_users": pattern["users"],
                    "duration_seconds": pattern["duration"],
                    "ramp_up_seconds": pattern["ramp_up"],
                    "think_time_min": 1,
                    "think_time_max": 5
                },
                "user_behaviors": [
                    {
                        "action": "login",
                        "weight": 10,
                        "expected_response_time": 500
                    },
                    {
                        "action": "upload_document",
                        "weight": 20,
                        "expected_response_time": 5000,
                        "file_sizes": [1000000, 5000000, 10000000]  # 1MB, 5MB, 10MB
                    },
                    {
                        "action": "search_documents",
                        "weight": 30,
                        "expected_response_time": 300,
                        "queries": ["machine learning", "data science", "algorithms"]
                    },
                    {
                        "action": "review_cards",
                        "weight": 40,
                        "expected_response_time": 200,
                        "cards_per_session": random.randint(10, 50)
                    }
                ],
                "success_criteria": {
                    "max_response_time": 2000,
                    "error_rate_threshold": 0.01,
                    "throughput_min": pattern["users"] * 0.8
                },
                "monitoring": {
                    "cpu_threshold": 80,
                    "memory_threshold": 85,
                    "disk_io_threshold": 90
                }
            }
            scenarios.append(scenario)
            
        self._save_json("load_test_scenarios.json", scenarios)
        
    def _save_json(self, filename: str, data: Any):
        """Save data as JSON file"""
        filepath = self.output_dir / filename
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"Generated {filepath}")


if __name__ == "__main__":
    generator = SyntheticDataGenerator()
    generator.generate_all_synthetic_data()