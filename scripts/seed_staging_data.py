#!/usr/bin/env python3
"""
Staging environment test data seeding script.
Creates consistent test data for integration testing.
"""

import asyncio
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
import json

# Add the backend app to the Python path
sys.path.insert(0, '/app')

from app.core.database import get_db_session
from app.models.document import Document
from app.models.knowledge import KnowledgePoint, Chapter
from app.models.learning import Card, SRSState
from app.services.document_service import DocumentService
from app.services.card_generation_service import CardGenerationService


class StagingDataSeeder:
    """Seed test data for staging environment"""
    
    def __init__(self):
        self.db_session = None
        self.document_service = DocumentService()
        self.card_service = CardGenerationService()
        
    async def setup(self):
        """Setup database session"""
        self.db_session = await get_db_session()
        
    async def cleanup(self):
        """Cleanup database session"""
        if self.db_session:
            await self.db_session.close()
    
    async def seed_all_data(self):
        """Seed all test data"""
        print("🌱 Starting staging data seeding...")
        
        # Clear existing data
        await self.clear_existing_data()
        
        # Seed test documents
        documents = await self.seed_documents()
        
        # Seed chapters and knowledge points
        await self.seed_chapters_and_knowledge(documents)
        
        # Seed cards and SRS states
        await self.seed_cards_and_srs(documents)
        
        # Create test user data
        await self.seed_user_data()
        
        print("✅ Staging data seeding completed successfully!")
        
    async def clear_existing_data(self):
        """Clear existing test data"""
        print("🧹 Clearing existing data...")
        
        try:
            # Delete in reverse dependency order
            await self.db_session.execute("DELETE FROM srs_states")
            await self.db_session.execute("DELETE FROM cards")
            await self.db_session.execute("DELETE FROM knowledge_points")
            await self.db_session.execute("DELETE FROM chapters")
            await self.db_session.execute("DELETE FROM documents")
            
            await self.db_session.commit()
            print("✅ Existing data cleared")
            
        except Exception as e:
            print(f"⚠️  Warning: Could not clear existing data: {e}")
            await self.db_session.rollback()
    
    async def seed_documents(self) -> list:
        """Seed test documents"""
        print("📄 Seeding test documents...")
        
        test_documents = [
            {
                'filename': 'machine_learning_basics.pdf',
                'title': 'Machine Learning Basics',
                'content': self._generate_ml_content(),
                'file_size': 1024 * 1024,  # 1MB
                'mime_type': 'application/pdf',
                'status': 'completed'
            },
            {
                'filename': 'data_structures_algorithms.pdf',
                'title': 'Data Structures and Algorithms',
                'content': self._generate_dsa_content(),
                'file_size': 2 * 1024 * 1024,  # 2MB
                'mime_type': 'application/pdf',
                'status': 'completed'
            },
            {
                'filename': 'python_programming.pdf',
                'title': 'Python Programming Guide',
                'content': self._generate_python_content(),
                'file_size': 1.5 * 1024 * 1024,  # 1.5MB
                'mime_type': 'application/pdf',
                'status': 'completed'
            },
            {
                'filename': 'web_development.pdf',
                'title': 'Modern Web Development',
                'content': self._generate_web_dev_content(),
                'file_size': 3 * 1024 * 1024,  # 3MB
                'mime_type': 'application/pdf',
                'status': 'processing'  # One document still processing
            }
        ]
        
        documents = []
        for doc_data in test_documents:
            document = Document(
                filename=doc_data['filename'],
                title=doc_data['title'],
                file_size=doc_data['file_size'],
                mime_type=doc_data['mime_type'],
                status=doc_data['status'],
                upload_date=datetime.now() - timedelta(days=len(documents)),
                processing_completed_at=datetime.now() if doc_data['status'] == 'completed' else None
            )
            
            self.db_session.add(document)
            documents.append(document)
        
        await self.db_session.commit()
        print(f"✅ Seeded {len(documents)} test documents")
        
        return documents
    
    async def seed_chapters_and_knowledge(self, documents: list):
        """Seed chapters and knowledge points"""
        print("📚 Seeding chapters and knowledge points...")
        
        chapter_data = {
            'Machine Learning Basics': [
                {
                    'title': 'Introduction to Machine Learning',
                    'content': 'Machine learning is a subset of artificial intelligence...',
                    'knowledge_points': [
                        'Definition of machine learning',
                        'Types of machine learning algorithms',
                        'Supervised vs unsupervised learning'
                    ]
                },
                {
                    'title': 'Linear Regression',
                    'content': 'Linear regression is a fundamental algorithm...',
                    'knowledge_points': [
                        'Linear regression equation',
                        'Cost function and optimization',
                        'Gradient descent algorithm'
                    ]
                },
                {
                    'title': 'Classification Algorithms',
                    'content': 'Classification is used to predict categories...',
                    'knowledge_points': [
                        'Logistic regression',
                        'Decision trees',
                        'Support vector machines'
                    ]
                }
            ],
            'Data Structures and Algorithms': [
                {
                    'title': 'Arrays and Lists',
                    'content': 'Arrays are fundamental data structures...',
                    'knowledge_points': [
                        'Array operations and complexity',
                        'Dynamic arrays vs static arrays',
                        'Linked lists implementation'
                    ]
                },
                {
                    'title': 'Sorting Algorithms',
                    'content': 'Sorting is a fundamental operation...',
                    'knowledge_points': [
                        'Bubble sort algorithm',
                        'Quick sort implementation',
                        'Merge sort complexity'
                    ]
                }
            ],
            'Python Programming Guide': [
                {
                    'title': 'Python Basics',
                    'content': 'Python is a high-level programming language...',
                    'knowledge_points': [
                        'Python syntax and variables',
                        'Data types and operations',
                        'Control flow statements'
                    ]
                },
                {
                    'title': 'Object-Oriented Programming',
                    'content': 'OOP is a programming paradigm...',
                    'knowledge_points': [
                        'Classes and objects',
                        'Inheritance and polymorphism',
                        'Encapsulation principles'
                    ]
                }
            ]
        }
        
        total_chapters = 0
        total_knowledge_points = 0
        
        for document in documents:
            if document.title in chapter_data and document.status == 'completed':
                chapters_info = chapter_data[document.title]
                
                for i, chapter_info in enumerate(chapters_info):
                    chapter = Chapter(
                        document_id=document.id,
                        title=chapter_info['title'],
                        content=chapter_info['content'],
                        chapter_number=i + 1,
                        page_start=i * 10 + 1,
                        page_end=(i + 1) * 10
                    )
                    
                    self.db_session.add(chapter)
                    await self.db_session.flush()  # Get chapter ID
                    
                    # Add knowledge points
                    for j, kp_text in enumerate(chapter_info['knowledge_points']):
                        knowledge_point = KnowledgePoint(
                            document_id=document.id,
                            chapter_id=chapter.id,
                            content=kp_text,
                            importance_score=0.7 + (j * 0.1),  # Varying importance
                            extraction_confidence=0.85 + (j * 0.05)
                        )
                        
                        self.db_session.add(knowledge_point)
                        total_knowledge_points += 1
                    
                    total_chapters += 1
        
        await self.db_session.commit()
        print(f"✅ Seeded {total_chapters} chapters and {total_knowledge_points} knowledge points")
    
    async def seed_cards_and_srs(self, documents: list):
        """Seed flashcards and SRS states"""
        print("🃏 Seeding flashcards and SRS states...")
        
        card_templates = [
            {
                'question': 'What is machine learning?',
                'answer': 'Machine learning is a subset of artificial intelligence that enables computers to learn and make decisions from data without being explicitly programmed.',
                'difficulty': 0.5,
                'card_type': 'basic'
            },
            {
                'question': 'What is the difference between supervised and unsupervised learning?',
                'answer': 'Supervised learning uses labeled data to train models, while unsupervised learning finds patterns in unlabeled data.',
                'difficulty': 0.6,
                'card_type': 'basic'
            },
            {
                'question': 'Explain the gradient descent algorithm',
                'answer': 'Gradient descent is an optimization algorithm that iteratively adjusts parameters to minimize a cost function by moving in the direction of steepest descent.',
                'difficulty': 0.8,
                'card_type': 'detailed'
            },
            {
                'question': 'What is the time complexity of bubble sort?',
                'answer': 'The time complexity of bubble sort is O(n²) in the worst and average cases, and O(n) in the best case when the array is already sorted.',
                'difficulty': 0.4,
                'card_type': 'basic'
            },
            {
                'question': 'How does a linked list differ from an array?',
                'answer': 'Arrays store elements in contiguous memory with O(1) access time, while linked lists use pointers with O(n) access time but dynamic size.',
                'difficulty': 0.6,
                'card_type': 'comparison'
            }
        ]
        
        total_cards = 0
        
        for document in documents:
            if document.status == 'completed':
                # Create 3-5 cards per completed document
                num_cards = min(len(card_templates), 5)
                
                for i in range(num_cards):
                    template = card_templates[i % len(card_templates)]
                    
                    card = Card(
                        document_id=document.id,
                        question=f"[{document.title}] {template['question']}",
                        answer=template['answer'],
                        difficulty=template['difficulty'],
                        card_type=template['card_type'],
                        created_at=datetime.now() - timedelta(days=total_cards)
                    )
                    
                    self.db_session.add(card)
                    await self.db_session.flush()  # Get card ID
                    
                    # Create SRS state for the card
                    srs_state = SRSState(
                        card_id=card.id,
                        ease_factor=2.5,
                        interval=1,
                        repetitions=0,
                        due_date=datetime.now() + timedelta(days=1),
                        last_reviewed=None
                    )
                    
                    self.db_session.add(srs_state)
                    total_cards += 1
        
        await self.db_session.commit()
        print(f"✅ Seeded {total_cards} flashcards with SRS states")
    
    async def seed_user_data(self):
        """Seed user-related test data"""
        print("👤 Seeding user data...")
        
        # Create some review history by updating SRS states
        cards = await self.db_session.execute(
            "SELECT id FROM cards ORDER BY created_at LIMIT 5"
        )
        card_ids = [row[0] for row in cards.fetchall()]
        
        # Simulate some reviews
        for i, card_id in enumerate(card_ids):
            if i < 3:  # Review first 3 cards
                await self.db_session.execute(
                    """
                    UPDATE srs_states 
                    SET last_reviewed = %s, 
                        repetitions = %s,
                        interval = %s,
                        due_date = %s
                    WHERE card_id = %s
                    """,
                    (
                        datetime.now() - timedelta(days=i + 1),
                        i + 1,
                        (i + 1) * 2,
                        datetime.now() + timedelta(days=(i + 1) * 2),
                        card_id
                    )
                )
        
        await self.db_session.commit()
        print("✅ User data seeded")
    
    def _generate_ml_content(self) -> str:
        """Generate machine learning content"""
        return """
        Machine Learning Basics
        
        Chapter 1: Introduction to Machine Learning
        Machine learning is a subset of artificial intelligence (AI) that provides systems 
        the ability to automatically learn and improve from experience without being 
        explicitly programmed. Machine learning focuses on the development of computer 
        programs that can access data and use it to learn for themselves.
        
        Chapter 2: Types of Machine Learning
        There are three main types of machine learning:
        1. Supervised Learning - Uses labeled data
        2. Unsupervised Learning - Finds patterns in unlabeled data  
        3. Reinforcement Learning - Learns through interaction with environment
        
        Chapter 3: Linear Regression
        Linear regression is one of the most fundamental algorithms in machine learning.
        It models the relationship between a dependent variable and independent variables
        by fitting a linear equation to observed data.
        """
    
    def _generate_dsa_content(self) -> str:
        """Generate data structures and algorithms content"""
        return """
        Data Structures and Algorithms
        
        Chapter 1: Arrays and Lists
        Arrays are collections of elements stored in contiguous memory locations.
        They provide O(1) access time but have fixed size in most implementations.
        Dynamic arrays like Python lists can grow and shrink as needed.
        
        Chapter 2: Sorting Algorithms
        Sorting is the process of arranging elements in a particular order.
        Common sorting algorithms include:
        - Bubble Sort: O(n²) time complexity
        - Quick Sort: O(n log n) average case
        - Merge Sort: O(n log n) guaranteed
        """
    
    def _generate_python_content(self) -> str:
        """Generate Python programming content"""
        return """
        Python Programming Guide
        
        Chapter 1: Python Basics
        Python is a high-level, interpreted programming language known for its
        simplicity and readability. It supports multiple programming paradigms
        including procedural, object-oriented, and functional programming.
        
        Chapter 2: Object-Oriented Programming
        OOP is a programming paradigm based on the concept of objects, which
        contain data (attributes) and code (methods). Key principles include:
        - Encapsulation
        - Inheritance  
        - Polymorphism
        - Abstraction
        """
    
    def _generate_web_dev_content(self) -> str:
        """Generate web development content"""
        return """
        Modern Web Development
        
        Chapter 1: Frontend Technologies
        Modern web development involves various frontend technologies:
        - HTML5 for structure
        - CSS3 for styling
        - JavaScript for interactivity
        - React/Vue/Angular for frameworks
        
        Chapter 2: Backend Development
        Backend development handles server-side logic:
        - RESTful APIs
        - Database management
        - Authentication and authorization
        - Deployment and scaling
        """


async def main():
    """Main seeding function"""
    seeder = StagingDataSeeder()
    
    try:
        await seeder.setup()
        await seeder.seed_all_data()
        
        # Create summary file
        summary = {
            'seeded_at': datetime.now().isoformat(),
            'environment': 'staging',
            'status': 'completed',
            'data_types': [
                'documents',
                'chapters', 
                'knowledge_points',
                'cards',
                'srs_states',
                'user_data'
            ]
        }
        
        with open('/app/staging_seed_summary.json', 'w') as f:
            json.dump(summary, f, indent=2)
        
        print("📊 Seeding summary saved to staging_seed_summary.json")
        
    except Exception as e:
        print(f"❌ Error during seeding: {e}")
        raise
    finally:
        await seeder.cleanup()


if __name__ == '__main__':
    asyncio.run(main())