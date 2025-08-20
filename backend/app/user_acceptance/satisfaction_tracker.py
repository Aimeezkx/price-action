"""
User Satisfaction Measurement and Improvement Tracking System
"""
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from collections import defaultdict, Counter
import statistics

from .models import (
    UserSatisfactionSurvey, SatisfactionLevel, UserFeedback,
    FeedbackType, UXMetric
)

logger = logging.getLogger(__name__)


class SatisfactionTracker:
    """Tracks user satisfaction over time and identifies improvement opportunities"""
    
    def __init__(self, storage_path: str = "backend/app/user_acceptance/satisfaction"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.surveys: Dict[str, UserSatisfactionSurvey] = {}
        self.satisfaction_history: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self._load_existing_data()
    
    def _load_existing_data(self):
        """Load existing satisfaction data from storage"""
        survey_files = self.storage_path.glob("survey_*.json")
        for file_path in survey_files:
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    survey = UserSatisfactionSurvey(**data)
                    self.surveys[survey.id] = survey
                    
                    # Add to history
                    self.satisfaction_history[survey.user_id].append({
                        "date": survey.created_at,
                        "overall_satisfaction": survey.overall_satisfaction,
                        "ease_of_use": survey.ease_of_use,
                        "feature_completeness": survey.feature_completeness,
                        "performance_satisfaction": survey.performance_satisfaction,
                        "design_satisfaction": survey.design_satisfaction,
                        "nps_score": survey.likelihood_to_recommend
                    })
            except Exception as e:
                logger.error(f"Error loading satisfaction survey from {file_path}: {e}")
    
    def record_satisfaction_survey(self, survey_data: Dict[str, Any]) -> UserSatisfactionSurvey:
        """Record a new satisfaction survey"""
        survey = UserSatisfactionSurvey(**survey_data)
        self.surveys[survey.id] = survey
        
        # Add to user history
        self.satisfaction_history[survey.user_id].append({
            "date": survey.created_at,
            "overall_satisfaction": survey.overall_satisfaction,
            "ease_of_use": survey.ease_of_use,
            "feature_completeness": survey.feature_completeness,
            "performance_satisfaction": survey.performance_satisfaction,
            "design_satisfaction": survey.design_satisfaction,
            "nps_score": survey.likelihood_to_recommend
        })
        
        self._save_survey(survey)
        logger.info(f"Recorded satisfaction survey {survey.id} for user {survey.user_id}")
        return survey
    
    def _save_survey(self, survey: UserSatisfactionSurvey):
        """Save survey to storage"""
        file_path = self.storage_path / f"survey_{survey.id}.json"
        with open(file_path, 'w') as f:
            json.dump(survey.dict(), f, indent=2, default=str)
    
    def get_user_satisfaction_trend(self, user_id: str) -> Dict[str, Any]:
        """Get satisfaction trend for a specific user"""
        user_history = self.satisfaction_history.get(user_id, [])
        
        if not user_history:
            return {"error": "No satisfaction data found for user"}
        
        # Sort by date
        sorted_history = sorted(user_history, key=lambda x: x["date"])
        
        # Calculate trends
        trends = {}
        metrics = ["overall_satisfaction", "ease_of_use", "feature_completeness", 
                  "performance_satisfaction", "design_satisfaction", "nps_score"]
        
        for metric in metrics:
            values = [entry[metric] for entry in sorted_history]
            if len(values) >= 2:
                # Simple trend calculation (last - first)
                trend = values[-1] - values[0]
                trends[metric] = {
                    "current": values[-1],
                    "initial": values[0],
                    "trend": trend,
                    "trend_direction": "improving" if trend > 0 else "declining" if trend < 0 else "stable"
                }
            else:
                trends[metric] = {
                    "current": values[0] if values else 0,
                    "initial": values[0] if values else 0,
                    "trend": 0,
                    "trend_direction": "stable"
                }
        
        return {
            "user_id": user_id,
            "survey_count": len(sorted_history),
            "date_range": {
                "first_survey": sorted_history[0]["date"].isoformat(),
                "last_survey": sorted_history[-1]["date"].isoformat()
            },
            "trends": trends,
            "overall_trend": self._calculate_overall_trend(trends)
        }
    
    def get_satisfaction_overview(self, days: int = 30) -> Dict[str, Any]:
        """Get overall satisfaction overview for the specified period"""
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_surveys = [
            survey for survey in self.surveys.values()
            if survey.created_at >= cutoff_date
        ]
        
        if not recent_surveys:
            return {"error": "No recent surveys found"}
        
        # Calculate averages
        metrics = {
            "overall_satisfaction": [s.overall_satisfaction for s in recent_surveys],
            "ease_of_use": [s.ease_of_use for s in recent_surveys],
            "feature_completeness": [s.feature_completeness for s in recent_surveys],
            "performance_satisfaction": [s.performance_satisfaction for s in recent_surveys],
            "design_satisfaction": [s.design_satisfaction for s in recent_surveys],
            "nps_score": [s.likelihood_to_recommend for s in recent_surveys]
        }
        
        averages = {}
        for metric, values in metrics.items():
            averages[metric] = {
                "mean": statistics.mean(values),
                "median": statistics.median(values),
                "std_dev": statistics.stdev(values) if len(values) > 1 else 0,
                "min": min(values),
                "max": max(values),
                "count": len(values)
            }
        
        # Calculate NPS
        nps_scores = [s.likelihood_to_recommend for s in recent_surveys]
        promoters = len([score for score in nps_scores if score >= 9])
        detractors = len([score for score in nps_scores if score <= 6])
        nps = ((promoters - detractors) / len(nps_scores)) * 100 if nps_scores else 0
        
        # Satisfaction distribution
        satisfaction_distribution = Counter(s.overall_satisfaction for s in recent_surveys)
        
        return {
            "period_days": days,
            "total_responses": len(recent_surveys),
            "averages": averages,
            "nps": {
                "score": round(nps, 1),
                "promoters": promoters,
                "passives": len(nps_scores) - promoters - detractors,
                "detractors": detractors
            },
            "satisfaction_distribution": dict(satisfaction_distribution),
            "insights": self._generate_satisfaction_insights(averages, nps)
        }
    
    def identify_satisfaction_issues(self, days: int = 30) -> List[Dict[str, Any]]:
        """Identify areas with low satisfaction that need improvement"""
        overview = self.get_satisfaction_overview(days)
        
        if "error" in overview:
            return []
        
        issues = []
        averages = overview["averages"]
        
        # Check each satisfaction metric
        for metric, stats in averages.items():
            if metric == "nps_score":
                continue  # Handle NPS separately
            
            mean_score = stats["mean"]
            if mean_score < 3.0:  # Below 3/5 is concerning
                issues.append({
                    "type": "low_satisfaction",
                    "metric": metric,
                    "current_score": round(mean_score, 2),
                    "severity": "high" if mean_score < 2.5 else "medium",
                    "sample_size": stats["count"],
                    "description": f"{metric.replace('_', ' ').title()} rated {mean_score:.1f}/5"
                })
        
        # Check NPS
        nps_score = overview["nps"]["score"]
        if nps_score < 0:
            issues.append({
                "type": "negative_nps",
                "metric": "nps_score",
                "current_score": nps_score,
                "severity": "high",
                "sample_size": overview["total_responses"],
                "description": f"Negative NPS score: {nps_score}"
            })
        elif nps_score < 30:
            issues.append({
                "type": "low_nps",
                "metric": "nps_score",
                "current_score": nps_score,
                "severity": "medium",
                "sample_size": overview["total_responses"],
                "description": f"Low NPS score: {nps_score}"
            })
        
        # Sort by severity
        severity_order = {"high": 3, "medium": 2, "low": 1}
        issues.sort(key=lambda x: severity_order.get(x["severity"], 0), reverse=True)
        
        return issues
    
    def track_improvement_impact(self, improvement_id: str, 
                               baseline_period: Tuple[datetime, datetime],
                               measurement_period: Tuple[datetime, datetime]) -> Dict[str, Any]:
        """Track the impact of an improvement on satisfaction"""
        baseline_start, baseline_end = baseline_period
        measure_start, measure_end = measurement_period
        
        # Get baseline surveys
        baseline_surveys = [
            survey for survey in self.surveys.values()
            if baseline_start <= survey.created_at <= baseline_end
        ]
        
        # Get measurement period surveys
        measurement_surveys = [
            survey for survey in self.surveys.values()
            if measure_start <= survey.created_at <= measure_end
        ]
        
        if not baseline_surveys or not measurement_surveys:
            return {"error": "Insufficient data for comparison"}
        
        # Calculate metrics for both periods
        baseline_metrics = self._calculate_period_metrics(baseline_surveys)
        measurement_metrics = self._calculate_period_metrics(measurement_surveys)
        
        # Calculate improvements
        improvements = {}
        for metric in baseline_metrics:
            baseline_value = baseline_metrics[metric]["mean"]
            measurement_value = measurement_metrics[metric]["mean"]
            
            improvement = measurement_value - baseline_value
            improvement_pct = (improvement / baseline_value * 100) if baseline_value > 0 else 0
            
            improvements[metric] = {
                "baseline": baseline_value,
                "measurement": measurement_value,
                "absolute_improvement": improvement,
                "percentage_improvement": improvement_pct,
                "is_significant": abs(improvement_pct) > 5  # 5% threshold
            }
        
        # Overall assessment
        significant_improvements = [
            metric for metric, data in improvements.items()
            if data["is_significant"] and data["absolute_improvement"] > 0
        ]
        
        significant_declines = [
            metric for metric, data in improvements.items()
            if data["is_significant"] and data["absolute_improvement"] < 0
        ]
        
        return {
            "improvement_id": improvement_id,
            "baseline_period": {
                "start": baseline_start.isoformat(),
                "end": baseline_end.isoformat(),
                "sample_size": len(baseline_surveys)
            },
            "measurement_period": {
                "start": measure_start.isoformat(),
                "end": measure_end.isoformat(),
                "sample_size": len(measurement_surveys)
            },
            "metric_improvements": improvements,
            "summary": {
                "significant_improvements": significant_improvements,
                "significant_declines": significant_declines,
                "overall_impact": "positive" if len(significant_improvements) > len(significant_declines) else "negative" if len(significant_declines) > 0 else "neutral"
            }
        }
    
    def _calculate_period_metrics(self, surveys: List[UserSatisfactionSurvey]) -> Dict[str, Dict[str, float]]:
        """Calculate metrics for a period of surveys"""
        metrics = {
            "overall_satisfaction": [s.overall_satisfaction for s in surveys],
            "ease_of_use": [s.ease_of_use for s in surveys],
            "feature_completeness": [s.feature_completeness for s in surveys],
            "performance_satisfaction": [s.performance_satisfaction for s in surveys],
            "design_satisfaction": [s.design_satisfaction for s in surveys],
            "nps_score": [s.likelihood_to_recommend for s in surveys]
        }
        
        result = {}
        for metric, values in metrics.items():
            result[metric] = {
                "mean": statistics.mean(values),
                "median": statistics.median(values),
                "std_dev": statistics.stdev(values) if len(values) > 1 else 0
            }
        
        return result
    
    def _calculate_overall_trend(self, trends: Dict[str, Any]) -> str:
        """Calculate overall trend direction"""
        improving_count = len([t for t in trends.values() if t["trend_direction"] == "improving"])
        declining_count = len([t for t in trends.values() if t["trend_direction"] == "declining"])
        
        if improving_count > declining_count:
            return "improving"
        elif declining_count > improving_count:
            return "declining"
        else:
            return "stable"
    
    def _generate_satisfaction_insights(self, averages: Dict[str, Any], nps: float) -> List[str]:
        """Generate insights from satisfaction data"""
        insights = []
        
        # Overall satisfaction insights
        overall_score = averages["overall_satisfaction"]["mean"]
        if overall_score >= 4.0:
            insights.append("High overall satisfaction (4.0+/5)")
        elif overall_score >= 3.5:
            insights.append("Good overall satisfaction (3.5+/5)")
        elif overall_score >= 3.0:
            insights.append("Moderate overall satisfaction (3.0+/5)")
        else:
            insights.append("Low overall satisfaction (<3.0/5) - needs attention")
        
        # NPS insights
        if nps >= 50:
            insights.append("Excellent NPS score (50+)")
        elif nps >= 30:
            insights.append("Good NPS score (30+)")
        elif nps >= 0:
            insights.append("Neutral NPS score (0+)")
        else:
            insights.append("Negative NPS score - critical issue")
        
        # Specific area insights
        performance_score = averages["performance_satisfaction"]["mean"]
        if performance_score < 3.0:
            insights.append("Performance satisfaction is low - prioritize optimization")
        
        ease_score = averages["ease_of_use"]["mean"]
        if ease_score < 3.0:
            insights.append("Ease of use is low - focus on UX improvements")
        
        feature_score = averages["feature_completeness"]["mean"]
        if feature_score < 3.0:
            insights.append("Feature completeness is low - consider feature expansion")
        
        return insights
    
    def generate_satisfaction_report(self, days: int = 30) -> Dict[str, Any]:
        """Generate comprehensive satisfaction report"""
        overview = self.get_satisfaction_overview(days)
        issues = self.identify_satisfaction_issues(days)
        
        # Get user trends for active users
        recent_user_ids = set(
            survey.user_id for survey in self.surveys.values()
            if survey.created_at >= datetime.now() - timedelta(days=days)
        )
        
        user_trends = {}
        for user_id in list(recent_user_ids)[:10]:  # Limit to 10 users for report
            user_trends[user_id] = self.get_user_satisfaction_trend(user_id)
        
        return {
            "report_period": f"Last {days} days",
            "generated_at": datetime.now().isoformat(),
            "overview": overview,
            "identified_issues": issues,
            "user_trends_sample": user_trends,
            "recommendations": self._generate_satisfaction_recommendations(overview, issues),
            "action_items": self._generate_action_items(issues)
        }
    
    def _generate_satisfaction_recommendations(self, overview: Dict[str, Any], 
                                            issues: List[Dict[str, Any]]) -> List[str]:
        """Generate recommendations based on satisfaction data"""
        recommendations = []
        
        if "error" in overview:
            return ["Collect more satisfaction survey data to generate recommendations"]
        
        # High-level recommendations based on NPS
        nps_score = overview["nps"]["score"]
        if nps_score < 0:
            recommendations.append("Critical: Implement immediate user experience improvements")
        elif nps_score < 30:
            recommendations.append("Focus on core user experience and feature improvements")
        
        # Specific recommendations based on issues
        for issue in issues:
            metric = issue["metric"]
            if "performance" in metric:
                recommendations.append("Prioritize performance optimization initiatives")
            elif "ease_of_use" in metric:
                recommendations.append("Conduct UX research and implement usability improvements")
            elif "feature" in metric:
                recommendations.append("Evaluate feature gaps and plan feature enhancements")
            elif "design" in metric:
                recommendations.append("Review and improve visual design and user interface")
        
        # Remove duplicates
        return list(set(recommendations))
    
    def _generate_action_items(self, issues: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate specific action items from identified issues"""
        action_items = []
        
        for issue in issues:
            if issue["severity"] == "high":
                action_items.append({
                    "priority": "high",
                    "area": issue["metric"],
                    "action": f"Address {issue['metric'].replace('_', ' ')} issues immediately",
                    "target_improvement": "Increase score by 1.0 point within 30 days",
                    "suggested_methods": self._get_improvement_methods(issue["metric"])
                })
            elif issue["severity"] == "medium":
                action_items.append({
                    "priority": "medium",
                    "area": issue["metric"],
                    "action": f"Plan improvements for {issue['metric'].replace('_', ' ')}",
                    "target_improvement": "Increase score by 0.5 points within 60 days",
                    "suggested_methods": self._get_improvement_methods(issue["metric"])
                })
        
        return action_items
    
    def _get_improvement_methods(self, metric: str) -> List[str]:
        """Get suggested improvement methods for a specific metric"""
        methods = {
            "overall_satisfaction": [
                "Conduct user interviews to identify pain points",
                "Implement quick wins based on user feedback",
                "Improve onboarding experience"
            ],
            "ease_of_use": [
                "Simplify user interface and navigation",
                "Add contextual help and tooltips",
                "Conduct usability testing sessions"
            ],
            "performance_satisfaction": [
                "Optimize page load times",
                "Improve server response times",
                "Implement caching strategies"
            ],
            "feature_completeness": [
                "Prioritize most requested features",
                "Improve existing feature discoverability",
                "Add feature tutorials and guides"
            ],
            "design_satisfaction": [
                "Update visual design and branding",
                "Improve color scheme and typography",
                "Enhance mobile responsiveness"
            ]
        }
        
        return methods.get(metric, ["Conduct user research to identify specific improvement areas"])