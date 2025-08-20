"""
User Feedback Collection and Analysis System
"""
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict, Counter
import re
from pathlib import Path

from .models import (
    UserFeedback, FeedbackType, UserSatisfactionSurvey,
    SatisfactionLevel, UXMetric
)

logger = logging.getLogger(__name__)


class FeedbackCollector:
    """Collects and manages user feedback"""
    
    def __init__(self, storage_path: str = "backend/app/user_acceptance/feedback"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.feedback_store: Dict[str, UserFeedback] = {}
        self.surveys_store: Dict[str, UserSatisfactionSurvey] = {}
        self._load_existing_feedback()
    
    def _load_existing_feedback(self):
        """Load existing feedback from storage"""
        feedback_files = self.storage_path.glob("feedback_*.json")
        for file_path in feedback_files:
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    feedback = UserFeedback(**data)
                    self.feedback_store[feedback.id] = feedback
            except Exception as e:
                logger.error(f"Error loading feedback from {file_path}: {e}")
        
        survey_files = self.storage_path.glob("survey_*.json")
        for file_path in survey_files:
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    survey = UserSatisfactionSurvey(**data)
                    self.surveys_store[survey.id] = survey
            except Exception as e:
                logger.error(f"Error loading survey from {file_path}: {e}")
    
    def collect_feedback(self, feedback_data: Dict[str, Any]) -> UserFeedback:
        """Collect new user feedback"""
        feedback = UserFeedback(**feedback_data)
        
        # Auto-categorize feedback
        feedback.category = self._categorize_feedback(feedback.description)
        
        # Auto-tag feedback
        feedback.tags = self._extract_tags(feedback.description)
        
        # Store feedback
        self.feedback_store[feedback.id] = feedback
        self._save_feedback(feedback)
        
        logger.info(f"Collected feedback {feedback.id} from user {feedback.user_id}")
        return feedback
    
    def collect_survey(self, survey_data: Dict[str, Any]) -> UserSatisfactionSurvey:
        """Collect user satisfaction survey"""
        survey = UserSatisfactionSurvey(**survey_data)
        self.surveys_store[survey.id] = survey
        self._save_survey(survey)
        
        logger.info(f"Collected survey {survey.id} from user {survey.user_id}")
        return survey
    
    def _save_feedback(self, feedback: UserFeedback):
        """Save feedback to storage"""
        file_path = self.storage_path / f"feedback_{feedback.id}.json"
        with open(file_path, 'w') as f:
            json.dump(feedback.dict(), f, indent=2, default=str)
    
    def _save_survey(self, survey: UserSatisfactionSurvey):
        """Save survey to storage"""
        file_path = self.storage_path / f"survey_{survey.id}.json"
        with open(file_path, 'w') as f:
            json.dump(survey.dict(), f, indent=2, default=str)
    
    def _categorize_feedback(self, description: str) -> str:
        """Auto-categorize feedback based on content"""
        description_lower = description.lower()
        
        # UI/UX related keywords
        ui_keywords = ['interface', 'design', 'layout', 'button', 'menu', 'navigation', 'color', 'font']
        if any(keyword in description_lower for keyword in ui_keywords):
            return "ui_ux"
        
        # Performance related keywords
        perf_keywords = ['slow', 'fast', 'loading', 'performance', 'speed', 'lag', 'delay']
        if any(keyword in description_lower for keyword in perf_keywords):
            return "performance"
        
        # Functionality related keywords
        func_keywords = ['feature', 'function', 'work', 'broken', 'error', 'bug', 'crash']
        if any(keyword in description_lower for keyword in func_keywords):
            return "functionality"
        
        # Content related keywords
        content_keywords = ['content', 'text', 'document', 'card', 'search', 'chapter']
        if any(keyword in description_lower for keyword in content_keywords):
            return "content"
        
        return "general"
    
    def _extract_tags(self, description: str) -> List[str]:
        """Extract relevant tags from feedback description"""
        tags = []
        description_lower = description.lower()
        
        # Feature tags
        feature_patterns = {
            'upload': r'\b(upload|file|document)\b',
            'search': r'\b(search|find|query)\b',
            'cards': r'\b(card|flashcard|review)\b',
            'navigation': r'\b(navigate|menu|link)\b',
            'mobile': r'\b(mobile|phone|tablet|touch)\b',
            'accessibility': r'\b(accessibility|screen reader|keyboard)\b'
        }
        
        for tag, pattern in feature_patterns.items():
            if re.search(pattern, description_lower):
                tags.append(tag)
        
        # Sentiment tags
        if any(word in description_lower for word in ['love', 'great', 'excellent', 'amazing']):
            tags.append('positive')
        elif any(word in description_lower for word in ['hate', 'terrible', 'awful', 'frustrating']):
            tags.append('negative')
        
        # Priority tags
        if any(word in description_lower for word in ['urgent', 'critical', 'important', 'asap']):
            tags.append('high_priority')
        
        return tags
    
    def get_feedback_by_type(self, feedback_type: FeedbackType) -> List[UserFeedback]:
        """Get feedback by type"""
        return [f for f in self.feedback_store.values() if f.feedback_type == feedback_type]
    
    def get_feedback_by_category(self, category: str) -> List[UserFeedback]:
        """Get feedback by category"""
        return [f for f in self.feedback_store.values() if f.category == category]
    
    def get_recent_feedback(self, days: int = 7) -> List[UserFeedback]:
        """Get recent feedback within specified days"""
        cutoff_date = datetime.now() - timedelta(days=days)
        return [f for f in self.feedback_store.values() if f.created_at >= cutoff_date]


class FeedbackAnalyzer:
    """Analyzes user feedback and generates insights"""
    
    def __init__(self, feedback_collector: FeedbackCollector):
        self.collector = feedback_collector
    
    def analyze_satisfaction_trends(self, days: int = 30) -> Dict[str, Any]:
        """Analyze satisfaction trends over time"""
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_surveys = [
            s for s in self.collector.surveys_store.values() 
            if s.created_at >= cutoff_date
        ]
        
        if not recent_surveys:
            return {"error": "No recent surveys found"}
        
        # Calculate averages
        avg_overall = sum(s.overall_satisfaction for s in recent_surveys) / len(recent_surveys)
        avg_ease = sum(s.ease_of_use for s in recent_surveys) / len(recent_surveys)
        avg_features = sum(s.feature_completeness for s in recent_surveys) / len(recent_surveys)
        avg_performance = sum(s.performance_satisfaction for s in recent_surveys) / len(recent_surveys)
        avg_design = sum(s.design_satisfaction for s in recent_surveys) / len(recent_surveys)
        avg_nps = sum(s.likelihood_to_recommend for s in recent_surveys) / len(recent_surveys)
        
        # Calculate NPS score
        promoters = len([s for s in recent_surveys if s.likelihood_to_recommend >= 9])
        detractors = len([s for s in recent_surveys if s.likelihood_to_recommend <= 6])
        nps_score = ((promoters - detractors) / len(recent_surveys)) * 100
        
        return {
            "period_days": days,
            "total_responses": len(recent_surveys),
            "averages": {
                "overall_satisfaction": round(avg_overall, 2),
                "ease_of_use": round(avg_ease, 2),
                "feature_completeness": round(avg_features, 2),
                "performance_satisfaction": round(avg_performance, 2),
                "design_satisfaction": round(avg_design, 2),
                "nps_score": round(nps_score, 1)
            },
            "nps_breakdown": {
                "promoters": promoters,
                "passives": len(recent_surveys) - promoters - detractors,
                "detractors": detractors
            }
        }
    
    def analyze_feedback_themes(self, days: int = 30) -> Dict[str, Any]:
        """Analyze common themes in feedback"""
        recent_feedback = self.collector.get_recent_feedback(days)
        
        if not recent_feedback:
            return {"error": "No recent feedback found"}
        
        # Analyze by type
        type_counts = Counter(f.feedback_type for f in recent_feedback)
        
        # Analyze by category
        category_counts = Counter(f.category for f in recent_feedback)
        
        # Analyze by severity
        severity_counts = Counter(f.severity for f in recent_feedback)
        
        # Analyze tags
        all_tags = []
        for f in recent_feedback:
            all_tags.extend(f.tags)
        tag_counts = Counter(all_tags)
        
        # Find most common issues
        bug_reports = [f for f in recent_feedback if f.feedback_type == FeedbackType.BUG_REPORT]
        usability_issues = [f for f in recent_feedback if f.feedback_type == FeedbackType.USABILITY_ISSUE]
        
        return {
            "period_days": days,
            "total_feedback": len(recent_feedback),
            "by_type": dict(type_counts),
            "by_category": dict(category_counts),
            "by_severity": dict(severity_counts),
            "top_tags": dict(tag_counts.most_common(10)),
            "critical_issues": len([f for f in recent_feedback if f.severity == "critical"]),
            "bug_reports": len(bug_reports),
            "usability_issues": len(usability_issues)
        }
    
    def identify_improvement_opportunities(self) -> List[Dict[str, Any]]:
        """Identify key improvement opportunities from feedback"""
        opportunities = []
        
        # Analyze satisfaction surveys for low scores
        low_satisfaction_areas = self._find_low_satisfaction_areas()
        for area in low_satisfaction_areas:
            opportunities.append({
                "type": "satisfaction_improvement",
                "area": area["area"],
                "current_score": area["score"],
                "priority": "high" if area["score"] < 3 else "medium",
                "description": f"Users rate {area['area']} at {area['score']}/5"
            })
        
        # Analyze frequent issues
        frequent_issues = self._find_frequent_issues()
        for issue in frequent_issues:
            opportunities.append({
                "type": "issue_resolution",
                "category": issue["category"],
                "frequency": issue["count"],
                "priority": "high" if issue["count"] > 10 else "medium",
                "description": f"{issue['count']} reports in {issue['category']} category"
            })
        
        # Analyze feature requests
        feature_requests = self.collector.get_feedback_by_type(FeedbackType.FEATURE_REQUEST)
        request_themes = self._analyze_feature_request_themes(feature_requests)
        for theme in request_themes:
            opportunities.append({
                "type": "feature_enhancement",
                "theme": theme["theme"],
                "requests": theme["count"],
                "priority": "medium",
                "description": f"{theme['count']} users requested {theme['theme']}"
            })
        
        # Sort by priority and frequency
        priority_order = {"high": 3, "medium": 2, "low": 1}
        opportunities.sort(key=lambda x: priority_order.get(x["priority"], 0), reverse=True)
        
        return opportunities[:10]  # Return top 10 opportunities
    
    def _find_low_satisfaction_areas(self) -> List[Dict[str, Any]]:
        """Find areas with low satisfaction scores"""
        surveys = list(self.collector.surveys_store.values())
        if not surveys:
            return []
        
        areas = {
            "overall_satisfaction": [s.overall_satisfaction for s in surveys],
            "ease_of_use": [s.ease_of_use for s in surveys],
            "feature_completeness": [s.feature_completeness for s in surveys],
            "performance_satisfaction": [s.performance_satisfaction for s in surveys],
            "design_satisfaction": [s.design_satisfaction for s in surveys]
        }
        
        low_areas = []
        for area, scores in areas.items():
            avg_score = sum(scores) / len(scores)
            if avg_score < 3.5:  # Below 3.5/5 is concerning
                low_areas.append({
                    "area": area,
                    "score": round(avg_score, 2)
                })
        
        return low_areas
    
    def _find_frequent_issues(self) -> List[Dict[str, Any]]:
        """Find frequently reported issues"""
        feedback = list(self.collector.feedback_store.values())
        category_counts = Counter(f.category for f in feedback)
        
        frequent = []
        for category, count in category_counts.items():
            if count >= 5:  # 5 or more reports
                frequent.append({
                    "category": category,
                    "count": count
                })
        
        return frequent
    
    def _analyze_feature_request_themes(self, requests: List[UserFeedback]) -> List[Dict[str, Any]]:
        """Analyze themes in feature requests"""
        themes = defaultdict(int)
        
        for request in requests:
            # Simple keyword-based theme detection
            description = request.description.lower()
            
            if any(word in description for word in ['export', 'download', 'save']):
                themes['export_functionality'] += 1
            if any(word in description for word in ['collaboration', 'share', 'team']):
                themes['collaboration_features'] += 1
            if any(word in description for word in ['mobile', 'app', 'phone']):
                themes['mobile_improvements'] += 1
            if any(word in description for word in ['search', 'filter', 'find']):
                themes['search_enhancements'] += 1
            if any(word in description for word in ['notification', 'reminder', 'alert']):
                themes['notification_system'] += 1
        
        return [{"theme": theme, "count": count} for theme, count in themes.items()]
    
    def generate_feedback_report(self, days: int = 30) -> Dict[str, Any]:
        """Generate comprehensive feedback report"""
        satisfaction_analysis = self.analyze_satisfaction_trends(days)
        theme_analysis = self.analyze_feedback_themes(days)
        opportunities = self.identify_improvement_opportunities()
        
        return {
            "report_period": f"Last {days} days",
            "generated_at": datetime.now().isoformat(),
            "satisfaction_trends": satisfaction_analysis,
            "feedback_themes": theme_analysis,
            "improvement_opportunities": opportunities,
            "summary": {
                "total_feedback_items": len(self.collector.get_recent_feedback(days)),
                "total_surveys": len([
                    s for s in self.collector.surveys_store.values()
                    if s.created_at >= datetime.now() - timedelta(days=days)
                ]),
                "critical_issues": len([
                    f for f in self.collector.get_recent_feedback(days)
                    if f.severity == "critical"
                ]),
                "high_priority_opportunities": len([
                    o for o in opportunities if o["priority"] == "high"
                ])
            }
        }