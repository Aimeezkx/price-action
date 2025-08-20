"""
User Scenario Manager for User Acceptance Testing
"""
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path

from .models import (
    UserScenario, TestScenarioType, UserTestSession, TestStatus,
    TestExecutionResult, UXMetric
)

logger = logging.getLogger(__name__)


class ScenarioManager:
    """Manages user acceptance test scenarios"""
    
    def __init__(self, scenarios_path: str = "backend/app/user_acceptance/scenarios"):
        self.scenarios_path = Path(scenarios_path)
        self.scenarios_path.mkdir(parents=True, exist_ok=True)
        self.scenarios: Dict[str, UserScenario] = {}
        self.active_sessions: Dict[str, UserTestSession] = {}
        self._load_default_scenarios()
    
    def _load_default_scenarios(self):
        """Load default test scenarios"""
        default_scenarios = [
            {
                "name": "Document Upload and Processing",
                "description": "User uploads a PDF document and waits for processing to complete",
                "scenario_type": TestScenarioType.DOCUMENT_UPLOAD,
                "steps": [
                    "Navigate to the upload page",
                    "Select a PDF file from computer",
                    "Click upload button",
                    "Wait for upload progress to complete",
                    "Verify processing status updates",
                    "Navigate to document view when processing completes"
                ],
                "expected_outcomes": [
                    "File uploads successfully without errors",
                    "Processing completes within reasonable time",
                    "User receives clear status updates",
                    "Document content is properly extracted and displayed"
                ],
                "success_criteria": [
                    "Upload completes in under 30 seconds",
                    "Processing completes in under 2 minutes for 10-page document",
                    "No error messages displayed",
                    "At least 90% of text content extracted correctly"
                ],
                "estimated_duration": 5,
                "difficulty_level": "beginner",
                "test_data_requirements": {
                    "pdf_file": "sample_document.pdf",
                    "expected_pages": 10,
                    "expected_text_blocks": 50
                }
            },
            {
                "name": "Flashcard Study Session",
                "description": "User reviews flashcards in a study session",
                "scenario_type": TestScenarioType.CARD_REVIEW,
                "steps": [
                    "Navigate to study page",
                    "Select a document to study",
                    "Start flashcard review session",
                    "Review 10 flashcards",
                    "Grade each card (1-5 scale)",
                    "Complete session and view progress"
                ],
                "expected_outcomes": [
                    "Cards load quickly and display correctly",
                    "Grading system works smoothly",
                    "Progress is tracked accurately",
                    "SRS algorithm schedules next reviews appropriately"
                ],
                "success_criteria": [
                    "Each card loads in under 1 second",
                    "Grading response is immediate",
                    "Progress statistics are accurate",
                    "Next review dates are calculated correctly"
                ],
                "estimated_duration": 8,
                "difficulty_level": "beginner",
                "prerequisites": ["Document must be uploaded and processed"],
                "test_data_requirements": {
                    "document_id": "test_document_1",
                    "minimum_cards": 10
                }
            },
            {
                "name": "Content Search and Discovery",
                "description": "User searches for specific content across documents",
                "scenario_type": TestScenarioType.SEARCH_USAGE,
                "steps": [
                    "Navigate to search page",
                    "Enter search query",
                    "Review search results",
                    "Apply filters (document, difficulty, etc.)",
                    "Click on a search result",
                    "Verify content relevance"
                ],
                "expected_outcomes": [
                    "Search returns relevant results quickly",
                    "Filters work correctly",
                    "Results are properly ranked",
                    "Content preview is accurate"
                ],
                "success_criteria": [
                    "Search results appear in under 500ms",
                    "At least 80% of results are relevant",
                    "Filters reduce results appropriately",
                    "Content preview matches actual content"
                ],
                "estimated_duration": 6,
                "difficulty_level": "intermediate",
                "test_data_requirements": {
                    "search_queries": ["machine learning", "algorithms", "data structures"],
                    "minimum_documents": 3
                }
            },
            {
                "name": "Chapter Navigation and Browsing",
                "description": "User browses through document chapters and sections",
                "scenario_type": TestScenarioType.CHAPTER_BROWSING,
                "steps": [
                    "Open a processed document",
                    "Navigate through chapter list",
                    "Click on different chapters",
                    "Use chapter navigation controls",
                    "Bookmark interesting sections",
                    "Return to bookmarked content"
                ],
                "expected_outcomes": [
                    "Chapter structure is clear and logical",
                    "Navigation is smooth and intuitive",
                    "Bookmarking works correctly",
                    "Content loads quickly when switching chapters"
                ],
                "success_criteria": [
                    "Chapter navigation responds in under 200ms",
                    "Chapter structure matches document organization",
                    "Bookmarks are saved and retrievable",
                    "No broken links or missing content"
                ],
                "estimated_duration": 7,
                "difficulty_level": "beginner",
                "test_data_requirements": {
                    "structured_document": "textbook_sample.pdf",
                    "minimum_chapters": 5
                }
            },
            {
                "name": "Mobile Learning Experience",
                "description": "User accesses and uses the application on mobile device",
                "scenario_type": TestScenarioType.MOBILE_USAGE,
                "steps": [
                    "Open application on mobile browser",
                    "Navigate through main features",
                    "Upload a document using mobile interface",
                    "Review cards using touch gestures",
                    "Search for content using mobile keyboard",
                    "Test offline functionality if available"
                ],
                "expected_outcomes": [
                    "Interface adapts well to mobile screen",
                    "Touch interactions work smoothly",
                    "Text is readable without zooming",
                    "Performance is acceptable on mobile"
                ],
                "success_criteria": [
                    "All features accessible on mobile",
                    "Touch targets are at least 44px",
                    "Page loads in under 3 seconds on 3G",
                    "No horizontal scrolling required"
                ],
                "estimated_duration": 10,
                "difficulty_level": "intermediate",
                "test_data_requirements": {
                    "mobile_devices": ["iPhone", "Android"],
                    "network_conditions": ["3G", "WiFi"]
                }
            },
            {
                "name": "Accessibility Navigation",
                "description": "User with accessibility needs navigates the application",
                "scenario_type": TestScenarioType.ACCESSIBILITY,
                "steps": [
                    "Navigate using only keyboard",
                    "Use screen reader to access content",
                    "Test high contrast mode",
                    "Verify focus indicators",
                    "Test with voice commands if supported",
                    "Complete core tasks without mouse"
                ],
                "expected_outcomes": [
                    "All features accessible via keyboard",
                    "Screen reader announces content correctly",
                    "Focus indicators are visible",
                    "Color contrast meets WCAG standards"
                ],
                "success_criteria": [
                    "Tab order is logical and complete",
                    "All interactive elements have proper labels",
                    "Color contrast ratio > 4.5:1",
                    "No keyboard traps exist"
                ],
                "estimated_duration": 15,
                "difficulty_level": "advanced",
                "prerequisites": ["Screen reader software", "Keyboard navigation skills"],
                "test_data_requirements": {
                    "accessibility_tools": ["NVDA", "JAWS", "VoiceOver"],
                    "contrast_checker": "WebAIM"
                }
            }
        ]
        
        for scenario_data in default_scenarios:
            scenario = UserScenario(**scenario_data)
            self.scenarios[scenario.id] = scenario
            self._save_scenario(scenario)
    
    def _save_scenario(self, scenario: UserScenario):
        """Save scenario to file"""
        scenario_file = self.scenarios_path / f"{scenario.id}.json"
        with open(scenario_file, 'w') as f:
            json.dump(scenario.dict(), f, indent=2, default=str)
    
    def get_scenario(self, scenario_id: str) -> Optional[UserScenario]:
        """Get scenario by ID"""
        return self.scenarios.get(scenario_id)
    
    def get_scenarios_by_type(self, scenario_type: TestScenarioType) -> List[UserScenario]:
        """Get scenarios by type"""
        return [s for s in self.scenarios.values() if s.scenario_type == scenario_type]
    
    def get_all_scenarios(self) -> List[UserScenario]:
        """Get all scenarios"""
        return list(self.scenarios.values())
    
    def create_scenario(self, scenario_data: Dict[str, Any]) -> UserScenario:
        """Create new scenario"""
        scenario = UserScenario(**scenario_data)
        self.scenarios[scenario.id] = scenario
        self._save_scenario(scenario)
        return scenario
    
    def start_test_session(self, user_id: str, scenario_id: str) -> UserTestSession:
        """Start a new test session"""
        if scenario_id not in self.scenarios:
            raise ValueError(f"Scenario {scenario_id} not found")
        
        session = UserTestSession(
            user_id=user_id,
            scenario_id=scenario_id,
            status=TestStatus.RUNNING,
            start_time=datetime.now()
        )
        
        self.active_sessions[session.id] = session
        logger.info(f"Started test session {session.id} for user {user_id}")
        return session
    
    def update_session_progress(self, session_id: str, step_index: int, 
                              completion_time: float, success: bool = True):
        """Update session progress"""
        if session_id not in self.active_sessions:
            raise ValueError(f"Session {session_id} not found")
        
        session = self.active_sessions[session_id]
        
        # Ensure time_per_step list is long enough
        while len(session.time_per_step) <= step_index:
            session.time_per_step.append(0.0)
        
        session.time_per_step[step_index] = completion_time
        
        # Calculate completion rate
        scenario = self.scenarios[session.scenario_id]
        completed_steps = step_index + 1
        session.completion_rate = completed_steps / len(scenario.steps)
        
        logger.info(f"Updated session {session_id} progress: {session.completion_rate:.2%}")
    
    def complete_session(self, session_id: str, feedback: str = "", 
                        satisfaction: Optional[str] = None) -> TestExecutionResult:
        """Complete a test session"""
        if session_id not in self.active_sessions:
            raise ValueError(f"Session {session_id} not found")
        
        session = self.active_sessions[session_id]
        session.status = TestStatus.COMPLETED
        session.end_time = datetime.now()
        session.feedback = feedback
        
        if satisfaction:
            session.user_satisfaction = satisfaction
        
        # Calculate success rate based on completed steps
        scenario = self.scenarios[session.scenario_id]
        total_steps = len(scenario.steps)
        completed_steps = len([t for t in session.time_per_step if t > 0])
        session.success_rate = completed_steps / total_steps if total_steps > 0 else 0
        
        # Create execution result
        result = TestExecutionResult(
            scenario_id=session.scenario_id,
            session_id=session.id,
            success=session.success_rate >= 0.8,  # 80% completion threshold
            completion_time=sum(session.time_per_step),
            steps_completed=completed_steps,
            total_steps=total_steps,
            issues=session.issues_encountered,
            user_feedback=feedback,
            satisfaction_score=self._satisfaction_to_score(satisfaction),
            metrics={
                "completion_rate": session.completion_rate,
                "success_rate": session.success_rate,
                "average_step_time": sum(session.time_per_step) / len(session.time_per_step) if session.time_per_step else 0
            }
        )
        
        # Remove from active sessions
        del self.active_sessions[session_id]
        
        logger.info(f"Completed session {session_id} with {session.success_rate:.2%} success rate")
        return result
    
    def _satisfaction_to_score(self, satisfaction: Optional[str]) -> Optional[int]:
        """Convert satisfaction level to numeric score"""
        if not satisfaction:
            return None
        
        mapping = {
            "very_dissatisfied": 1,
            "dissatisfied": 2,
            "neutral": 3,
            "satisfied": 4,
            "very_satisfied": 5
        }
        return mapping.get(satisfaction)
    
    def get_session_metrics(self, session_id: str) -> List[UXMetric]:
        """Get UX metrics for a session"""
        if session_id not in self.active_sessions:
            return []
        
        session = self.active_sessions[session_id]
        scenario = self.scenarios[session.scenario_id]
        
        metrics = []
        
        # Task completion time
        if session.time_per_step:
            metrics.append(UXMetric(
                user_id=session.user_id,
                session_id=session_id,
                metric_name="task_completion_time",
                metric_value=sum(session.time_per_step),
                metric_unit="seconds",
                context={"scenario_type": scenario.scenario_type}
            ))
        
        # Step efficiency
        if session.time_per_step and scenario.estimated_duration:
            expected_time = scenario.estimated_duration * 60  # convert to seconds
            actual_time = sum(session.time_per_step)
            efficiency = expected_time / actual_time if actual_time > 0 else 0
            
            metrics.append(UXMetric(
                user_id=session.user_id,
                session_id=session_id,
                metric_name="task_efficiency",
                metric_value=efficiency,
                metric_unit="ratio",
                context={"expected_time": expected_time, "actual_time": actual_time}
            ))
        
        # Completion rate
        metrics.append(UXMetric(
            user_id=session.user_id,
            session_id=session_id,
            metric_name="completion_rate",
            metric_value=session.completion_rate,
            metric_unit="percentage",
            context={"scenario_type": scenario.scenario_type}
        ))
        
        return metrics
    
    def get_scenario_statistics(self, scenario_id: str) -> Dict[str, Any]:
        """Get statistics for a scenario across all sessions"""
        # This would typically query a database
        # For now, return mock statistics
        return {
            "total_sessions": 0,
            "average_completion_rate": 0.0,
            "average_satisfaction": 0.0,
            "common_issues": [],
            "average_completion_time": 0.0
        }