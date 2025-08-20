"""
User feedback integration and analysis system
"""
import re
import json
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from collections import Counter
import statistics
from .models import (
    UserFeedback, Improvement, ImprovementPriority, 
    ImprovementCategory, FeatureRequest
)


class FeedbackAnalyzer:
    """Analyzes user feedback and generates improvement suggestions"""
    
    def __init__(self):
        self.feedback_storage = []
        self.sentiment_keywords = {
            'positive': [
                'love', 'great', 'awesome', 'excellent', 'perfect', 'amazing',
                'helpful', 'useful', 'easy', 'fast', 'smooth', 'intuitive'
            ],
            'negative': [
                'hate', 'terrible', 'awful', 'horrible', 'broken', 'slow',
                'confusing', 'difficult', 'frustrating', 'annoying', 'buggy'
            ],
            'neutral': [
                'okay', 'fine', 'average', 'decent', 'acceptable'
            ]
        }
        
        self.feature_keywords = {
            'search': ['search', 'find', 'lookup', 'query', 'filter'],
            'upload': ['upload', 'import', 'add document', 'file'],
            'cards': ['card', 'flashcard', 'review', 'study', 'quiz'],
            'performance': ['slow', 'fast', 'speed', 'loading', 'lag'],
            'ui': ['interface', 'design', 'layout', 'button', 'menu'],
            'mobile': ['mobile', 'phone', 'tablet', 'responsive', 'touch']
        }
    
    async def collect_feedback(self, feedback: UserFeedback) -> str:
        """Collect and store user feedback"""
        # Validate feedback
        if not feedback.comment or len(feedback.comment.strip()) < 5:
            raise ValueError("Feedback comment must be at least 5 characters")
        
        if feedback.rating < 1 or feedback.rating > 5:
            raise ValueError("Rating must be between 1 and 5")
        
        # Store feedback
        self.feedback_storage.append(feedback)
        
        # Auto-categorize if not provided
        if not feedback.category:
            feedback.category = await self._categorize_feedback(feedback.comment)
        
        # Auto-determine severity
        if not feedback.severity:
            feedback.severity = await self._determine_severity(feedback)
        
        return feedback.id
    
    async def _categorize_feedback(self, comment: str) -> str:
        """Automatically categorize feedback based on content"""
        comment_lower = comment.lower()
        
        # Count keyword matches for each category
        category_scores = {}
        for category, keywords in self.feature_keywords.items():
            score = sum(1 for keyword in keywords if keyword in comment_lower)
            if score > 0:
                category_scores[category] = score
        
        # Return category with highest score, or 'general' if no matches
        if category_scores:
            return max(category_scores, key=category_scores.get)
        else:
            return 'general'
    
    async def _determine_severity(self, feedback: UserFeedback) -> str:
        """Determine feedback severity based on rating and content"""
        comment_lower = feedback.comment.lower()
        
        # Critical issues
        critical_keywords = ['crash', 'broken', 'error', 'bug', 'fail', 'lost data']
        if any(keyword in comment_lower for keyword in critical_keywords):
            return 'critical'
        
        # High severity for low ratings with negative sentiment
        if feedback.rating <= 2:
            negative_count = sum(1 for word in self.sentiment_keywords['negative'] 
                               if word in comment_lower)
            if negative_count >= 2:
                return 'high'
            else:
                return 'medium'
        
        # Medium severity for moderate ratings
        if feedback.rating == 3:
            return 'medium'
        
        # Low severity for positive feedback (feature requests)
        return 'low'
    
    async def analyze_feedback_trends(self, days: int = 30) -> Dict[str, Any]:
        """Analyze feedback trends over specified period"""
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_feedback = [
            f for f in self.feedback_storage 
            if f.timestamp >= cutoff_date
        ]
        
        if not recent_feedback:
            return {"error": "No recent feedback found"}
        
        # Overall statistics
        ratings = [f.rating for f in recent_feedback]
        categories = [f.category for f in recent_feedback]
        severities = [f.severity for f in recent_feedback]
        
        # Sentiment analysis
        sentiment_scores = []
        for feedback in recent_feedback:
            sentiment = await self._analyze_sentiment(feedback.comment)
            sentiment_scores.append(sentiment)
        
        # Category analysis
        category_ratings = {}
        for category in set(categories):
            category_feedback = [f for f in recent_feedback if f.category == category]
            category_ratings[category] = {
                'count': len(category_feedback),
                'avg_rating': statistics.mean([f.rating for f in category_feedback]),
                'satisfaction': len([f for f in category_feedback if f.rating >= 4]) / len(category_feedback)
            }
        
        analysis = {
            "period_days": days,
            "total_feedback": len(recent_feedback),
            "overall_rating": {
                "average": statistics.mean(ratings),
                "median": statistics.median(ratings),
                "distribution": dict(Counter(ratings))
            },
            "sentiment": {
                "average": statistics.mean(sentiment_scores),
                "positive_ratio": len([s for s in sentiment_scores if s > 0.1]) / len(sentiment_scores),
                "negative_ratio": len([s for s in sentiment_scores if s < -0.1]) / len(sentiment_scores)
            },
            "categories": category_ratings,
            "severity_distribution": dict(Counter(severities)),
            "top_issues": await self._identify_top_issues(recent_feedback),
            "improvement_opportunities": await self._identify_improvement_opportunities(recent_feedback)
        }
        
        return analysis
    
    async def _analyze_sentiment(self, comment: str) -> float:
        """Analyze sentiment of feedback comment (-1 to 1 scale)"""
        comment_lower = comment.lower()
        
        positive_count = sum(1 for word in self.sentiment_keywords['positive'] 
                           if word in comment_lower)
        negative_count = sum(1 for word in self.sentiment_keywords['negative'] 
                           if word in comment_lower)
        
        # Simple sentiment score
        total_words = len(comment_lower.split())
        if total_words == 0:
            return 0.0
        
        sentiment = (positive_count - negative_count) / total_words
        return max(-1.0, min(1.0, sentiment * 10))  # Scale and clamp
    
    async def _identify_top_issues(self, feedback_list: List[UserFeedback]) -> List[Dict[str, Any]]:
        """Identify most common issues from feedback"""
        # Group by similar issues (simplified)
        issue_patterns = {}
        
        for feedback in feedback_list:
            if feedback.rating <= 3:  # Only consider negative/neutral feedback
                # Extract key phrases (simplified)
                words = re.findall(r'\b\w+\b', feedback.comment.lower())
                key_phrases = []
                
                # Look for common issue patterns
                for i in range(len(words) - 1):
                    phrase = f"{words[i]} {words[i+1]}"
                    if any(keyword in phrase for keyword in 
                          ['slow', 'error', 'broken', 'difficult', 'confusing']):
                        key_phrases.append(phrase)
                
                for phrase in key_phrases:
                    if phrase not in issue_patterns:
                        issue_patterns[phrase] = []
                    issue_patterns[phrase].append(feedback)
        
        # Sort by frequency and severity
        top_issues = []
        for phrase, feedbacks in issue_patterns.items():
            if len(feedbacks) >= 2:  # At least 2 reports
                avg_severity_score = {
                    'critical': 4, 'high': 3, 'medium': 2, 'low': 1
                }
                severity_score = statistics.mean([
                    avg_severity_score.get(f.severity, 1) for f in feedbacks
                ])
                
                top_issues.append({
                    'issue': phrase,
                    'frequency': len(feedbacks),
                    'avg_rating': statistics.mean([f.rating for f in feedbacks]),
                    'severity_score': severity_score,
                    'sample_comments': [f.comment for f in feedbacks[:3]]
                })
        
        # Sort by combined score (frequency * severity)
        top_issues.sort(key=lambda x: x['frequency'] * x['severity_score'], reverse=True)
        return top_issues[:10]
    
    async def _identify_improvement_opportunities(self, 
                                                feedback_list: List[UserFeedback]) -> List[Dict[str, Any]]:
        """Identify improvement opportunities from positive feedback"""
        opportunities = []
        
        # Look for feature requests in positive feedback
        positive_feedback = [f for f in feedback_list if f.rating >= 4]
        
        for feedback in positive_feedback:
            comment_lower = feedback.comment.lower()
            
            # Look for suggestion patterns
            suggestion_patterns = [
                r'would be nice if (.+)',
                r'could you add (.+)',
                r'wish it had (.+)',
                r'suggestion: (.+)',
                r'feature request: (.+)'
            ]
            
            for pattern in suggestion_patterns:
                matches = re.findall(pattern, comment_lower)
                for match in matches:
                    opportunities.append({
                        'suggestion': match.strip(),
                        'user_rating': feedback.rating,
                        'category': feedback.category,
                        'full_comment': feedback.comment
                    })
        
        return opportunities
    
    async def generate_feedback_improvements(self, 
                                           analysis: Dict[str, Any]) -> List[Improvement]:
        """Generate improvement suggestions based on feedback analysis"""
        improvements = []
        
        # Address top issues
        top_issues = analysis.get('top_issues', [])
        for issue in top_issues[:5]:  # Top 5 issues
            priority = self._determine_issue_priority(issue)
            
            improvements.append(Improvement(
                title=f"Address user issue: {issue['issue']}",
                description=f"Users report issues with '{issue['issue']}' (frequency: {issue['frequency']}, avg rating: {issue['avg_rating']:.1f})",
                priority=priority,
                category=self._map_issue_to_category(issue['issue']),
                suggested_actions=self._generate_issue_actions(issue),
                estimated_effort=self._estimate_issue_effort(issue),
                expected_impact=0.8,
                confidence=0.7,
                source_data={"feedback_analysis": issue}
            ))
        
        # Address category-specific issues
        categories = analysis.get('categories', {})
        for category, data in categories.items():
            if data['avg_rating'] < 3.5 and data['count'] >= 5:
                improvements.append(Improvement(
                    title=f"Improve {category} functionality",
                    description=f"Category '{category}' has low satisfaction (avg rating: {data['avg_rating']:.1f})",
                    priority=ImprovementPriority.MEDIUM,
                    category=ImprovementCategory.USER_EXPERIENCE,
                    suggested_actions=[
                        f"Conduct user research on {category} pain points",
                        f"Redesign {category} user interface",
                        f"Add user guidance for {category} features",
                        f"Optimize {category} performance"
                    ],
                    estimated_effort=20,
                    expected_impact=0.6,
                    confidence=0.6,
                    source_data={"category_analysis": data}
                ))
        
        # Feature enhancement opportunities
        opportunities = analysis.get('improvement_opportunities', [])
        feature_requests = self._group_feature_requests(opportunities)
        
        for feature, requests in feature_requests.items():
            if len(requests) >= 3:  # At least 3 requests
                avg_rating = statistics.mean([r['user_rating'] for r in requests])
                
                improvements.append(Improvement(
                    title=f"Implement requested feature: {feature}",
                    description=f"Multiple users requested '{feature}' (requests: {len(requests)}, avg user rating: {avg_rating:.1f})",
                    priority=ImprovementPriority.LOW,
                    category=ImprovementCategory.FEATURE_ENHANCEMENT,
                    suggested_actions=[
                        f"Design {feature} functionality",
                        f"Implement {feature} with user testing",
                        f"Document {feature} usage",
                        f"Gather feedback on {feature} implementation"
                    ],
                    estimated_effort=self._estimate_feature_effort(feature),
                    expected_impact=0.4,
                    confidence=0.5,
                    source_data={"feature_requests": requests}
                ))
        
        return improvements
    
    def _determine_issue_priority(self, issue: Dict[str, Any]) -> ImprovementPriority:
        """Determine priority based on issue characteristics"""
        frequency = issue['frequency']
        severity_score = issue['severity_score']
        avg_rating = issue['avg_rating']
        
        # Calculate combined priority score
        priority_score = (frequency * 0.4 + severity_score * 0.4 + 
                         (5 - avg_rating) * 0.2)
        
        if priority_score >= 8:
            return ImprovementPriority.CRITICAL
        elif priority_score >= 6:
            return ImprovementPriority.HIGH
        elif priority_score >= 4:
            return ImprovementPriority.MEDIUM
        else:
            return ImprovementPriority.LOW
    
    def _map_issue_to_category(self, issue: str) -> ImprovementCategory:
        """Map issue description to improvement category"""
        issue_lower = issue.lower()
        
        if any(word in issue_lower for word in ['slow', 'speed', 'loading', 'lag']):
            return ImprovementCategory.PERFORMANCE
        elif any(word in issue_lower for word in ['confusing', 'difficult', 'interface']):
            return ImprovementCategory.USER_EXPERIENCE
        elif any(word in issue_lower for word in ['error', 'broken', 'bug']):
            return ImprovementCategory.CODE_QUALITY
        else:
            return ImprovementCategory.USER_EXPERIENCE
    
    def _generate_issue_actions(self, issue: Dict[str, Any]) -> List[str]:
        """Generate specific actions to address an issue"""
        issue_text = issue['issue'].lower()
        
        actions = ["Investigate root cause of reported issue"]
        
        if 'slow' in issue_text or 'loading' in issue_text:
            actions.extend([
                "Profile performance bottlenecks",
                "Optimize slow operations",
                "Add loading indicators",
                "Implement caching where appropriate"
            ])
        elif 'confusing' in issue_text or 'difficult' in issue_text:
            actions.extend([
                "Conduct usability testing",
                "Improve user interface design",
                "Add helpful tooltips and guidance",
                "Simplify complex workflows"
            ])
        elif 'error' in issue_text or 'broken' in issue_text:
            actions.extend([
                "Fix reported bugs",
                "Add better error handling",
                "Improve error messages",
                "Add validation and safeguards"
            ])
        else:
            actions.extend([
                "Gather more detailed user feedback",
                "Design solution based on user needs",
                "Implement and test solution",
                "Monitor for improvement"
            ])
        
        return actions
    
    def _estimate_issue_effort(self, issue: Dict[str, Any]) -> int:
        """Estimate effort required to address issue"""
        frequency = issue['frequency']
        severity_score = issue['severity_score']
        
        # Base effort on complexity indicators
        base_effort = 8
        
        if severity_score >= 3:  # High severity
            base_effort += 16
        
        if frequency >= 10:  # High frequency
            base_effort += 8
        
        return min(base_effort, 40)  # Cap at 40 hours
    
    def _group_feature_requests(self, opportunities: List[Dict[str, Any]]) -> Dict[str, List]:
        """Group similar feature requests"""
        grouped = {}
        
        for opportunity in opportunities:
            suggestion = opportunity['suggestion']
            
            # Simple grouping by key words
            key_words = suggestion.split()[:3]  # First 3 words
            key = ' '.join(key_words)
            
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(opportunity)
        
        return grouped
    
    def _estimate_feature_effort(self, feature: str) -> int:
        """Estimate effort for implementing a feature"""
        feature_lower = feature.lower()
        
        # Simple heuristics based on feature type
        if any(word in feature_lower for word in ['search', 'filter']):
            return 24
        elif any(word in feature_lower for word in ['export', 'import']):
            return 16
        elif any(word in feature_lower for word in ['ui', 'interface', 'design']):
            return 20
        elif any(word in feature_lower for word in ['mobile', 'responsive']):
            return 32
        else:
            return 16  # Default
    
    async def create_feature_request(self, 
                                   title: str,
                                   description: str,
                                   requested_by: str,
                                   user_votes: int = 1) -> FeatureRequest:
        """Create a feature request from user feedback"""
        # Calculate priority score based on various factors
        priority_score = self._calculate_feature_priority(description, user_votes)
        
        # Estimate business value and technical complexity
        business_value = self._estimate_business_value(description)
        technical_complexity = self._estimate_technical_complexity(description)
        
        # Estimate effort
        estimated_effort = self._estimate_feature_effort(description)
        
        feature_request = FeatureRequest(
            title=title,
            description=description,
            requested_by=requested_by,
            priority_score=priority_score,
            user_votes=user_votes,
            business_value=business_value,
            technical_complexity=technical_complexity,
            estimated_effort=estimated_effort
        )
        
        return feature_request
    
    def _calculate_feature_priority(self, description: str, user_votes: int) -> float:
        """Calculate feature priority score"""
        base_score = user_votes * 10
        
        # Boost for high-impact keywords
        high_impact_keywords = ['productivity', 'efficiency', 'time-saving', 'essential']
        for keyword in high_impact_keywords:
            if keyword in description.lower():
                base_score += 20
        
        return min(base_score, 100)  # Cap at 100
    
    def _estimate_business_value(self, description: str) -> float:
        """Estimate business value of feature (0-1 scale)"""
        description_lower = description.lower()
        
        value_indicators = {
            'user retention': 0.9,
            'productivity': 0.8,
            'efficiency': 0.7,
            'user experience': 0.6,
            'convenience': 0.5
        }
        
        max_value = 0.3  # Default
        for indicator, value in value_indicators.items():
            if indicator in description_lower:
                max_value = max(max_value, value)
        
        return max_value
    
    def _estimate_technical_complexity(self, description: str) -> float:
        """Estimate technical complexity (0-1 scale)"""
        description_lower = description.lower()
        
        complexity_indicators = {
            'ai': 0.9,
            'machine learning': 0.9,
            'real-time': 0.8,
            'integration': 0.7,
            'mobile': 0.6,
            'ui': 0.4,
            'export': 0.3
        }
        
        max_complexity = 0.3  # Default
        for indicator, complexity in complexity_indicators.items():
            if indicator in description_lower:
                max_complexity = max(max_complexity, complexity)
        
        return max_complexity