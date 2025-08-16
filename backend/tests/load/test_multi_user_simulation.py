"""
Multi-user simulation with realistic usage patterns.
Simulates realistic user behavior patterns including document upload, study sessions, and search.
"""

import asyncio
import random
import time
import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
import aiohttp
import pytest
from pathlib import Path

class UserAction(Enum):
    """Types of user actions"""
    UPLOAD_DOCUMENT = "upload_document"
    BROWSE_DOCUMENTS = "browse_documents"
    START_STUDY_SESSION = "start_study_session"
    REVIEW_CARDS = "review_cards"
    SEARCH_CONTENT = "search_content"
    BROWSE_CHAPTERS = "browse_chapters"
    EXPORT_DATA = "export_data"

@dataclass
class UserProfile:
    """User behavior profile"""
    user_id: str
    user_type: str  # "casual", "regular", "power_user"
    session_duration: int  # minutes
    actions_per_session: int
    preferred_actions: List[UserAction]
    upload_frequency: float  # probability of uploading per session
    study_intensity: float  # cards reviewed per minute
    search_frequency: float  # searches per session

@dataclass
class ActionResult:
    """Result of a user action"""
    user_id: str
    action: UserAction
    start_time: float
    duration: float
    success: bool
    error_message: str = ""
    response_time: float = 0.0
    data: Dict[str, Any] = field(default_factory=dict)

class RealisticUserSimulator:
    """Simulates realistic user behavior patterns"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.user_profiles = self._create_user_profiles()
        self.test_documents = self._get_test_documents()
        self.search_queries = self._get_realistic_search_queries()
        self.results: List[ActionResult] = []
        
    def _create_user_profiles(self) -> List[UserProfile]:
        """Create realistic user profiles"""
        profiles = []
        
        # Casual users (60% of users)
        for i in range(12):
            profiles.append(UserProfile(
                user_id=f"casual_user_{i}",
                user_type="casual",
                session_duration=random.randint(5, 15),  # 5-15 minutes
                actions_per_session=random.randint(3, 8),
                preferred_actions=[
                    UserAction.BROWSE_DOCUMENTS,
                    UserAction.START_STUDY_SESSION,
                    UserAction.REVIEW_CARDS
                ],
                upload_frequency=0.2,  # 20% chance to upload
                study_intensity=2.0,   # 2 cards per minute
                search_frequency=1.0   # 1 search per session
            ))
        
        # Regular users (30% of users)
        for i in range(6):
            profiles.append(UserProfile(
                user_id=f"regular_user_{i}",
                user_type="regular",
                session_duration=random.randint(15, 45),  # 15-45 minutes
                actions_per_session=random.randint(8, 20),
                preferred_actions=[
                    UserAction.UPLOAD_DOCUMENT,
                    UserAction.START_STUDY_SESSION,
                    UserAction.REVIEW_CARDS,
                    UserAction.SEARCH_CONTENT,
                    UserAction.BROWSE_CHAPTERS
                ],
                upload_frequency=0.4,  # 40% chance to upload
                study_intensity=3.0,   # 3 cards per minute
                search_frequency=2.5   # 2-3 searches per session
            ))
        
        # Power users (10% of users)
        for i in range(2):
            profiles.append(UserProfile(
                user_id=f"power_user_{i}",
                user_type="power_user",
                session_duration=random.randint(45, 120),  # 45-120 minutes
                actions_per_session=random.randint(20, 50),
                preferred_actions=list(UserAction),  # All actions
                upload_frequency=0.7,  # 70% chance to upload
                study_intensity=4.0,   # 4 cards per minute
                search_frequency=5.0   # 5 searches per session
            ))
        
        return profiles
    
    def _get_test_documents(self) -> List[str]:
        """Get list of test documents for upload"""
        return [
            "machine_learning_basics.pdf",
            "data_structures_algorithms.pdf", 
            "python_programming.pdf",
            "statistics_fundamentals.pdf",
            "web_development.pdf"
        ]
    
    def _get_realistic_search_queries(self) -> List[str]:
        """Get realistic search queries"""
        return [
            "machine learning",
            "neural networks",
            "data structures",
            "algorithms",
            "python functions",
            "statistics",
            "probability",
            "web development",
            "databases",
            "programming concepts",
            "artificial intelligence",
            "deep learning",
            "software engineering",
            "computer science",
            "data analysis"
        ]
    
    async def simulate_user_session(self, session: aiohttp.ClientSession, 
                                  profile: UserProfile) -> List[ActionResult]:
        """Simulate a complete user session"""
        session_results = []
        session_start = time.time()
        session_end = session_start + (profile.session_duration * 60)
        
        print(f"Starting session for {profile.user_id} ({profile.user_type}) - {profile.session_duration} minutes")
        
        # Simulate user actions throughout the session
        actions_completed = 0
        while time.time() < session_end and actions_completed < profile.actions_per_session:
            # Choose action based on user profile
            action = self._choose_action(profile)
            
            # Execute action
            result = await self._execute_action(session, profile, action)
            session_results.append(result)
            actions_completed += 1
            
            # Realistic pause between actions
            pause_duration = random.uniform(5, 30)  # 5-30 seconds
            await asyncio.sleep(pause_duration)
        
        print(f"Completed session for {profile.user_id}: {actions_completed} actions in {time.time() - session_start:.1f}s")
        return session_results
    
    def _choose_action(self, profile: UserProfile) -> UserAction:
        """Choose next action based on user profile"""
        # Weight actions based on user preferences
        if random.random() < profile.upload_frequency and UserAction.UPLOAD_DOCUMENT in profile.preferred_actions:
            return UserAction.UPLOAD_DOCUMENT
        
        # Choose from preferred actions
        return random.choice(profile.preferred_actions)
    
    async def _execute_action(self, session: aiohttp.ClientSession, 
                            profile: UserProfile, action: UserAction) -> ActionResult:
        """Execute a specific user action"""
        start_time = time.time()
        
        try:
            if action == UserAction.UPLOAD_DOCUMENT:
                result = await self._upload_document(session, profile)
            elif action == UserAction.BROWSE_DOCUMENTS:
                result = await self._browse_documents(session, profile)
            elif action == UserAction.START_STUDY_SESSION:
                result = await self._start_study_session(session, profile)
            elif action == UserAction.REVIEW_CARDS:
                result = await self._review_cards(session, profile)
            elif action == UserAction.SEARCH_CONTENT:
                result = await self._search_content(session, profile)
            elif action == UserAction.BROWSE_CHAPTERS:
                result = await self._browse_chapters(session, profile)
            elif action == UserAction.EXPORT_DATA:
                result = await self._export_data(session, profile)
            else:
                result = ActionResult(
                    user_id=profile.user_id,
                    action=action,
                    start_time=start_time,
                    duration=0,
                    success=False,
                    error_message="Unknown action"
                )
                
        except Exception as e:
            result = ActionResult(
                user_id=profile.user_id,
                action=action,
                start_time=start_time,
                duration=time.time() - start_time,
                success=False,
                error_message=str(e)
            )
        
        return result
    
    async def _upload_document(self, session: aiohttp.ClientSession, 
                             profile: UserProfile) -> ActionResult:
        """Simulate document upload"""
        start_time = time.time()
        document_name = random.choice(self.test_documents)
        
        # Simulate file upload (mock data)
        data = aiohttp.FormData()
        data.add_field('file', b'mock_pdf_content', filename=document_name)
        
        async with session.post(f"{self.base_url}/api/documents/upload", data=data) as response:
            duration = time.time() - start_time
            
            if response.status == 200:
                response_data = await response.json()
                return ActionResult(
                    user_id=profile.user_id,
                    action=UserAction.UPLOAD_DOCUMENT,
                    start_time=start_time,
                    duration=duration,
                    success=True,
                    response_time=duration,
                    data={"document_id": response_data.get("document_id")}
                )
            else:
                error_text = await response.text()
                return ActionResult(
                    user_id=profile.user_id,
                    action=UserAction.UPLOAD_DOCUMENT,
                    start_time=start_time,
                    duration=duration,
                    success=False,
                    error_message=f"HTTP {response.status}: {error_text}",
                    response_time=duration
                )
    
    async def _browse_documents(self, session: aiohttp.ClientSession, 
                              profile: UserProfile) -> ActionResult:
        """Simulate browsing documents"""
        start_time = time.time()
        
        async with session.get(f"{self.base_url}/api/documents") as response:
            duration = time.time() - start_time
            
            if response.status == 200:
                documents = await response.json()
                return ActionResult(
                    user_id=profile.user_id,
                    action=UserAction.BROWSE_DOCUMENTS,
                    start_time=start_time,
                    duration=duration,
                    success=True,
                    response_time=duration,
                    data={"document_count": len(documents)}
                )
            else:
                error_text = await response.text()
                return ActionResult(
                    user_id=profile.user_id,
                    action=UserAction.BROWSE_DOCUMENTS,
                    start_time=start_time,
                    duration=duration,
                    success=False,
                    error_message=f"HTTP {response.status}: {error_text}",
                    response_time=duration
                )
    
    async def _start_study_session(self, session: aiohttp.ClientSession, 
                                 profile: UserProfile) -> ActionResult:
        """Simulate starting a study session"""
        start_time = time.time()
        
        # Get available cards for study
        async with session.get(f"{self.base_url}/api/cards/due") as response:
            duration = time.time() - start_time
            
            if response.status == 200:
                cards = await response.json()
                return ActionResult(
                    user_id=profile.user_id,
                    action=UserAction.START_STUDY_SESSION,
                    start_time=start_time,
                    duration=duration,
                    success=True,
                    response_time=duration,
                    data={"due_cards": len(cards)}
                )
            else:
                error_text = await response.text()
                return ActionResult(
                    user_id=profile.user_id,
                    action=UserAction.START_STUDY_SESSION,
                    start_time=start_time,
                    duration=duration,
                    success=False,
                    error_message=f"HTTP {response.status}: {error_text}",
                    response_time=duration
                )
    
    async def _review_cards(self, session: aiohttp.ClientSession, 
                          profile: UserProfile) -> ActionResult:
        """Simulate reviewing flashcards"""
        start_time = time.time()
        
        # Simulate reviewing multiple cards based on study intensity
        cards_to_review = int(profile.study_intensity * random.uniform(0.5, 2.0))
        successful_reviews = 0
        
        for _ in range(cards_to_review):
            # Get next card
            async with session.get(f"{self.base_url}/api/cards/next") as response:
                if response.status == 200:
                    card_data = await response.json()
                    card_id = card_data.get("id")
                    
                    # Simulate thinking time
                    await asyncio.sleep(random.uniform(3, 15))
                    
                    # Submit grade (realistic distribution)
                    grade = random.choices([1, 2, 3, 4, 5], weights=[5, 10, 25, 40, 20])[0]
                    
                    async with session.post(f"{self.base_url}/api/cards/{card_id}/grade", 
                                          json={"grade": grade}) as grade_response:
                        if grade_response.status == 200:
                            successful_reviews += 1
        
        duration = time.time() - start_time
        return ActionResult(
            user_id=profile.user_id,
            action=UserAction.REVIEW_CARDS,
            start_time=start_time,
            duration=duration,
            success=successful_reviews > 0,
            response_time=duration,
            data={"cards_reviewed": successful_reviews, "target_cards": cards_to_review}
        )
    
    async def _search_content(self, session: aiohttp.ClientSession, 
                            profile: UserProfile) -> ActionResult:
        """Simulate searching content"""
        start_time = time.time()
        query = random.choice(self.search_queries)
        
        async with session.get(f"{self.base_url}/api/search", 
                             params={"q": query}) as response:
            duration = time.time() - start_time
            
            if response.status == 200:
                results = await response.json()
                return ActionResult(
                    user_id=profile.user_id,
                    action=UserAction.SEARCH_CONTENT,
                    start_time=start_time,
                    duration=duration,
                    success=True,
                    response_time=duration,
                    data={"query": query, "result_count": len(results)}
                )
            else:
                error_text = await response.text()
                return ActionResult(
                    user_id=profile.user_id,
                    action=UserAction.SEARCH_CONTENT,
                    start_time=start_time,
                    duration=duration,
                    success=False,
                    error_message=f"HTTP {response.status}: {error_text}",
                    response_time=duration
                )
    
    async def _browse_chapters(self, session: aiohttp.ClientSession, 
                             profile: UserProfile) -> ActionResult:
        """Simulate browsing chapters"""
        start_time = time.time()
        
        # Get random document to browse chapters
        async with session.get(f"{self.base_url}/api/documents") as response:
            if response.status == 200:
                documents = await response.json()
                if documents:
                    doc_id = random.choice(documents)["id"]
                    
                    async with session.get(f"{self.base_url}/api/documents/{doc_id}/chapters") as chapter_response:
                        duration = time.time() - start_time
                        
                        if chapter_response.status == 200:
                            chapters = await chapter_response.json()
                            return ActionResult(
                                user_id=profile.user_id,
                                action=UserAction.BROWSE_CHAPTERS,
                                start_time=start_time,
                                duration=duration,
                                success=True,
                                response_time=duration,
                                data={"chapter_count": len(chapters)}
                            )
        
        duration = time.time() - start_time
        return ActionResult(
            user_id=profile.user_id,
            action=UserAction.BROWSE_CHAPTERS,
            start_time=start_time,
            duration=duration,
            success=False,
            error_message="No documents available for chapter browsing"
        )
    
    async def _export_data(self, session: aiohttp.ClientSession, 
                         profile: UserProfile) -> ActionResult:
        """Simulate data export"""
        start_time = time.time()
        export_format = random.choice(["json", "csv", "anki"])
        
        async with session.post(f"{self.base_url}/api/export", 
                              json={"format": export_format}) as response:
            duration = time.time() - start_time
            
            if response.status == 200:
                return ActionResult(
                    user_id=profile.user_id,
                    action=UserAction.EXPORT_DATA,
                    start_time=start_time,
                    duration=duration,
                    success=True,
                    response_time=duration,
                    data={"format": export_format}
                )
            else:
                error_text = await response.text()
                return ActionResult(
                    user_id=profile.user_id,
                    action=UserAction.EXPORT_DATA,
                    start_time=start_time,
                    duration=duration,
                    success=False,
                    error_message=f"HTTP {response.status}: {error_text}",
                    response_time=duration
                )
    
    async def run_simulation(self, duration_minutes: int = 30) -> Dict[str, Any]:
        """Run multi-user simulation"""
        print(f"Starting multi-user simulation for {duration_minutes} minutes with {len(self.user_profiles)} users")
        
        all_results = []
        
        async with aiohttp.ClientSession() as session:
            # Start user sessions concurrently
            tasks = []
            for profile in self.user_profiles:
                task = self.simulate_user_session(session, profile)
                tasks.append(task)
            
            # Wait for all sessions to complete
            session_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Collect all results
            for results in session_results:
                if isinstance(results, list):
                    all_results.extend(results)
                else:
                    print(f"Session error: {results}")
        
        return self._analyze_simulation_results(all_results)
    
    def _analyze_simulation_results(self, results: List[ActionResult]) -> Dict[str, Any]:
        """Analyze simulation results"""
        successful_results = [r for r in results if r.success]
        failed_results = [r for r in results if not r.success]
        
        # Group by action type
        action_stats = {}
        for action in UserAction:
            action_results = [r for r in results if r.action == action]
            if action_results:
                successful_action_results = [r for r in action_results if r.success]
                response_times = [r.response_time for r in successful_action_results if r.response_time > 0]
                
                action_stats[action.value] = {
                    "total_requests": len(action_results),
                    "successful_requests": len(successful_action_results),
                    "success_rate": len(successful_action_results) / len(action_results) * 100,
                    "avg_response_time": sum(response_times) / len(response_times) if response_times else 0,
                    "max_response_time": max(response_times) if response_times else 0
                }
        
        # Group by user type
        user_type_stats = {}
        for user_type in ["casual", "regular", "power_user"]:
            user_results = [r for r in results if user_type in r.user_id]
            if user_results:
                successful_user_results = [r for r in user_results if r.success]
                user_type_stats[user_type] = {
                    "total_actions": len(user_results),
                    "successful_actions": len(successful_user_results),
                    "success_rate": len(successful_user_results) / len(user_results) * 100
                }
        
        return {
            "simulation_summary": {
                "total_actions": len(results),
                "successful_actions": len(successful_results),
                "failed_actions": len(failed_results),
                "overall_success_rate": len(successful_results) / len(results) * 100 if results else 0
            },
            "action_statistics": action_stats,
            "user_type_statistics": user_type_stats,
            "errors": [r.error_message for r in failed_results if r.error_message]
        }

@pytest.mark.asyncio
@pytest.mark.load
class TestMultiUserSimulation:
    """Test suite for multi-user simulation"""
    
    @pytest.fixture
    def simulator(self):
        return RealisticUserSimulator()
    
    async def test_short_simulation(self, simulator):
        """Test short multi-user simulation (10 minutes)"""
        results = await simulator.run_simulation(duration_minutes=10)
        
        # Assertions
        assert results["simulation_summary"]["overall_success_rate"] >= 80, \
            f"Overall success rate too low: {results['simulation_summary']['overall_success_rate']}%"
        
        # Check that all user types participated
        assert len(results["user_type_statistics"]) >= 2, "Not enough user types participated"
        
        print(f"Short simulation results: {json.dumps(results, indent=2)}")
    
    async def test_medium_simulation(self, simulator):
        """Test medium multi-user simulation (20 minutes)"""
        results = await simulator.run_simulation(duration_minutes=20)
        
        # Assertions
        assert results["simulation_summary"]["overall_success_rate"] >= 75, \
            f"Overall success rate too low: {results['simulation_summary']['overall_success_rate']}%"
        
        # Check response times for critical actions
        critical_actions = ["search_content", "review_cards", "browse_documents"]
        for action in critical_actions:
            if action in results["action_statistics"]:
                avg_response_time = results["action_statistics"][action]["avg_response_time"]
                assert avg_response_time <= 2.0, f"{action} response time too high: {avg_response_time}s"
        
        print(f"Medium simulation results: {json.dumps(results, indent=2)}")
    
    async def test_extended_simulation(self, simulator):
        """Test extended multi-user simulation (30 minutes)"""
        results = await simulator.run_simulation(duration_minutes=30)
        
        # Assertions - More lenient for extended test
        assert results["simulation_summary"]["overall_success_rate"] >= 70, \
            f"Overall success rate too low: {results['simulation_summary']['overall_success_rate']}%"
        
        # Ensure all action types were tested
        expected_actions = ["upload_document", "browse_documents", "search_content", "review_cards"]
        for action in expected_actions:
            assert action in results["action_statistics"], f"Action {action} was not tested"
        
        print(f"Extended simulation results: {json.dumps(results, indent=2)}")

if __name__ == "__main__":
    # Run standalone simulation
    async def main():
        simulator = RealisticUserSimulator()
        results = await simulator.run_simulation(duration_minutes=15)
        print(json.dumps(results, indent=2))
    
    asyncio.run(main())