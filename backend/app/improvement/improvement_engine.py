"""
Main continuous improvement engine that orchestrates all components
"""
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from .models import (
    Improvement, FeatureRequest, UserFeedback, 
    ImprovementStatus, ImprovementPriority
)
from .code_quality_analyzer import CodeQualityAnalyzer
from .performance_optimizer import PerformanceOptimizer
from .feedback_analyzer import FeedbackAnalyzer
from .prioritization_engine import PrioritizationEngine
from .impact_tracker import ImpactTracker


class ContinuousImprovementEngine:
    """Main engine that coordinates all improvement activities"""
    
    def __init__(self, project_root: str = "."):
        self.project_root = project_root
        
        # Initialize all components
        self.code_analyzer = CodeQualityAnalyzer(project_root)
        self.performance_optimizer = PerformanceOptimizer()
        self.feedback_analyzer = FeedbackAnalyzer()
        self.prioritization_engine = PrioritizationEngine()
        self.impact_tracker = ImpactTracker()
        
        # Storage for improvements and requests
        self.improvements = []
        self.feature_requests = []
        self.improvement_history = []
        
        # Configuration
        self.analysis_schedule = {
            'code_quality': 24,      # hours
            'performance': 6,        # hours
            'feedback': 12,          # hours
            'prioritization': 48     # hours
        }
        
        self.last_analysis = {}
    
    async def run_continuous_analysis(self) -> Dict[str, Any]:
        """Run comprehensive continuous improvement analysis"""
        analysis_results = {
            'timestamp': datetime.now(),
            'analysis_components': {},
            'new_improvements': [],
            'updated_priorities': [],
            'impact_measurements': [],
            'summary': {}
        }
        
        try:
            # 1. Code Quality Analysis
            if self._should_run_analysis('code_quality'):
                print("Running code quality analysis...")
                code_results = await self._run_code_quality_analysis()
                analysis_results['analysis_components']['code_quality'] = code_results
                self.last_analysis['code_quality'] = datetime.now()
            
            # 2. Performance Analysis
            if self._should_run_analysis('performance'):
                print("Running performance analysis...")
                perf_results = await self._run_performance_analysis()
                analysis_results['analysis_components']['performance'] = perf_results
                self.last_analysis['performance'] = datetime.now()
            
            # 3. User Feedback Analysis
            if self._should_run_analysis('feedback'):
                print("Running feedback analysis...")
                feedback_results = await self._run_feedback_analysis()
                analysis_results['analysis_components']['feedback'] = feedback_results
                self.last_analysis['feedback'] = datetime.now()
            
            # 4. Prioritization Update
            if self._should_run_analysis('prioritization'):
                print("Updating prioritization...")
                priority_results = await self._run_prioritization_update()
                analysis_results['analysis_components']['prioritization'] = priority_results
                self.last_analysis['prioritization'] = datetime.now()
            
            # 5. Impact Tracking
            print("Tracking improvement impacts...")
            impact_results = await self._run_impact_tracking()
            analysis_results['analysis_components']['impact_tracking'] = impact_results
            
            # 6. Generate Summary
            analysis_results['summary'] = await self._generate_analysis_summary(analysis_results)
            
        except Exception as e:
            analysis_results['error'] = str(e)
            print(f"Error in continuous analysis: {e}")
        
        return analysis_results
    
    def _should_run_analysis(self, analysis_type: str) -> bool:
        """Check if analysis should run based on schedule"""
        if analysis_type not in self.last_analysis:
            return True
        
        last_run = self.last_analysis[analysis_type]
        schedule_hours = self.analysis_schedule[analysis_type]
        
        return datetime.now() - last_run > timedelta(hours=schedule_hours)
    
    async def _run_code_quality_analysis(self) -> Dict[str, Any]:
        """Run code quality analysis and generate improvements"""
        try:
            # Analyze project code quality
            quality_metrics = await self.code_analyzer.analyze_project()
            
            # Generate improvement suggestions
            quality_improvements = await self.code_analyzer.generate_improvements(quality_metrics)
            
            # Add to improvements list
            for improvement in quality_improvements:
                if not self._improvement_exists(improvement):
                    self.improvements.append(improvement)
            
            return {
                'metrics_analyzed': len(quality_metrics),
                'improvements_generated': len(quality_improvements),
                'average_complexity': sum(m.complexity for m in quality_metrics) / len(quality_metrics) if quality_metrics else 0,
                'average_coverage': sum(m.test_coverage for m in quality_metrics) / len(quality_metrics) if quality_metrics else 0,
                'total_code_smells': sum(m.code_smells for m in quality_metrics),
                'status': 'completed'
            }
            
        except Exception as e:
            return {'status': 'error', 'error': str(e)}
    
    async def _run_performance_analysis(self) -> Dict[str, Any]:
        """Run performance analysis and generate optimizations"""
        try:
            # Analyze performance for key operations
            operations = [
                'document_processing',
                'search_query',
                'card_generation',
                'user_authentication'
            ]
            
            performance_improvements = []
            
            for operation in operations:
                # Analyze performance trends
                analysis = await self.performance_optimizer.analyze_performance_trends(operation, days=7)
                
                if 'error' not in analysis:
                    # Generate improvements
                    improvements = await self.performance_optimizer.generate_performance_improvements(analysis)
                    performance_improvements.extend(improvements)
            
            # Add to improvements list
            for improvement in performance_improvements:
                if not self._improvement_exists(improvement):
                    self.improvements.append(improvement)
            
            return {
                'operations_analyzed': len(operations),
                'improvements_generated': len(performance_improvements),
                'status': 'completed'
            }
            
        except Exception as e:
            return {'status': 'error', 'error': str(e)}
    
    async def _run_feedback_analysis(self) -> Dict[str, Any]:
        """Run user feedback analysis and generate improvements"""
        try:
            # Analyze recent feedback trends
            feedback_analysis = await self.feedback_analyzer.analyze_feedback_trends(days=30)
            
            if 'error' not in feedback_analysis:
                # Generate improvements from feedback
                feedback_improvements = await self.feedback_analyzer.generate_feedback_improvements(feedback_analysis)
                
                # Add to improvements list
                for improvement in feedback_improvements:
                    if not self._improvement_exists(improvement):
                        self.improvements.append(improvement)
                
                return {
                    'feedback_analyzed': feedback_analysis.get('total_feedback', 0),
                    'improvements_generated': len(feedback_improvements),
                    'average_rating': feedback_analysis.get('overall_rating', {}).get('average', 0),
                    'top_issues_count': len(feedback_analysis.get('top_issues', [])),
                    'status': 'completed'
                }
            else:
                return {'status': 'no_data', 'message': 'No recent feedback found'}
                
        except Exception as e:
            return {'status': 'error', 'error': str(e)}
    
    async def _run_prioritization_update(self) -> Dict[str, Any]:
        """Update improvement prioritization"""
        try:
            # Prioritize current improvements
            prioritized_improvements = await self.prioritization_engine.prioritize_improvements(
                self.improvements
            )
            
            # Update improvements list with new priorities
            self.improvements = prioritized_improvements
            
            # Prioritize feature requests
            prioritized_features = await self.prioritization_engine.prioritize_feature_requests(
                self.feature_requests
            )
            
            self.feature_requests = prioritized_features
            
            # Generate implementation roadmap
            roadmap = await self.prioritization_engine.create_implementation_roadmap(
                self.improvements[:20],  # Top 20 improvements
                self.feature_requests[:10],  # Top 10 features
                {'total_capacity_hours': 160, 'sprint_capacity_hours': 40}
            )
            
            return {
                'improvements_prioritized': len(self.improvements),
                'features_prioritized': len(self.feature_requests),
                'roadmap_sprints': len(roadmap.get('sprints', [])),
                'status': 'completed'
            }
            
        except Exception as e:
            return {'status': 'error', 'error': str(e)}
    
    async def _run_impact_tracking(self) -> Dict[str, Any]:
        """Track impact of implemented improvements"""
        try:
            # Find completed improvements
            completed_improvements = [
                imp for imp in self.improvement_history 
                if imp.status == ImprovementStatus.COMPLETED
            ]
            
            impact_reports = []
            
            for improvement in completed_improvements[-10:]:  # Last 10 completed
                try:
                    impact_report = await self.impact_tracker.generate_impact_report(
                        improvement.id, report_period_days=30
                    )
                    
                    if 'error' not in impact_report:
                        impact_reports.append(impact_report)
                        
                except Exception as e:
                    print(f"Error tracking impact for {improvement.id}: {e}")
            
            return {
                'improvements_tracked': len(impact_reports),
                'average_success_rate': sum(
                    report['summary']['overall_success_rate'] 
                    for report in impact_reports
                ) / len(impact_reports) if impact_reports else 0,
                'status': 'completed'
            }
            
        except Exception as e:
            return {'status': 'error', 'error': str(e)}
    
    def _improvement_exists(self, new_improvement: Improvement) -> bool:
        """Check if similar improvement already exists"""
        for existing in self.improvements:
            # Simple similarity check based on title and category
            if (existing.title.lower() == new_improvement.title.lower() and
                existing.category == new_improvement.category):
                return True
        return False
    
    async def _generate_analysis_summary(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate summary of analysis results"""
        components = analysis_results.get('analysis_components', {})
        
        total_improvements = 0
        total_errors = 0
        
        for component, results in components.items():
            if results.get('status') == 'completed':
                total_improvements += results.get('improvements_generated', 0)
            elif results.get('status') == 'error':
                total_errors += 1
        
        # Calculate priority distribution
        priority_distribution = {}
        for improvement in self.improvements:
            priority = improvement.priority.value
            priority_distribution[priority] = priority_distribution.get(priority, 0) + 1
        
        # Calculate category distribution
        category_distribution = {}
        for improvement in self.improvements:
            category = improvement.category.value
            category_distribution[category] = category_distribution.get(category, 0) + 1
        
        return {
            'total_improvements_identified': total_improvements,
            'total_active_improvements': len(self.improvements),
            'total_feature_requests': len(self.feature_requests),
            'analysis_errors': total_errors,
            'priority_distribution': priority_distribution,
            'category_distribution': category_distribution,
            'next_analysis_schedule': {
                component: (
                    self.last_analysis.get(component, datetime.now()) + 
                    timedelta(hours=self.analysis_schedule[component])
                ).isoformat() if component in self.analysis_schedule else None
                for component in self.analysis_schedule.keys()
            }
        }
    
    async def submit_user_feedback(self, feedback: UserFeedback) -> str:
        """Submit user feedback for analysis"""
        feedback_id = await self.feedback_analyzer.collect_feedback(feedback)
        
        # Trigger immediate feedback analysis if significant feedback
        if feedback.rating <= 2 or feedback.severity in ['critical', 'high']:
            await self._run_feedback_analysis()
        
        return feedback_id
    
    async def create_feature_request(self, 
                                   title: str,
                                   description: str,
                                   requested_by: str,
                                   user_votes: int = 1) -> FeatureRequest:
        """Create new feature request"""
        feature_request = await self.feedback_analyzer.create_feature_request(
            title, description, requested_by, user_votes
        )
        
        self.feature_requests.append(feature_request)
        
        # Trigger prioritization update
        await self._run_prioritization_update()
        
        return feature_request
    
    async def mark_improvement_completed(self, 
                                       improvement_id: str,
                                       implementation_notes: str = "") -> bool:
        """Mark improvement as completed and start impact tracking"""
        # Find improvement
        improvement = None
        for imp in self.improvements:
            if imp.id == improvement_id:
                improvement = imp
                break
        
        if not improvement:
            return False
        
        # Update status
        improvement.status = ImprovementStatus.COMPLETED
        improvement.updated_at = datetime.now()
        
        # Move to history
        self.improvement_history.append(improvement)
        self.improvements.remove(improvement)
        
        # Establish baseline for impact tracking
        baseline_metrics = await self._collect_baseline_metrics(improvement)
        await self.impact_tracker.establish_baseline(improvement_id, baseline_metrics)
        
        return True
    
    async def _collect_baseline_metrics(self, improvement: Improvement) -> Dict[str, Any]:
        """Collect baseline metrics for improvement impact tracking"""
        baseline = {}
        
        # Performance metrics
        if improvement.category.value == 'performance':
            baseline.update({
                'response_time': 2.0,
                'memory_usage': 300,
                'cpu_usage': 60,
                'throughput': 100,
                'error_rate': 0.05
            })
        
        # Code quality metrics
        if improvement.category.value == 'code_quality':
            baseline.update({
                'complexity': 12.0,
                'maintainability': 75.0,
                'test_coverage': 80.0,
                'code_smells': 8,
                'technical_debt': 20.0
            })
        
        # User experience metrics
        if improvement.category.value == 'user_experience':
            baseline.update({
                'user_satisfaction': {
                    'average_rating': 3.5,
                    'sentiment_score': 0.1,
                    'total_feedback': 25
                }
            })
        
        return baseline
    
    async def get_improvement_dashboard(self) -> Dict[str, Any]:
        """Get comprehensive improvement dashboard data"""
        # Current improvements summary
        improvements_summary = {
            'total': len(self.improvements),
            'by_priority': {},
            'by_category': {},
            'by_status': {}
        }
        
        for improvement in self.improvements:
            # Priority distribution
            priority = improvement.priority.value
            improvements_summary['by_priority'][priority] = improvements_summary['by_priority'].get(priority, 0) + 1
            
            # Category distribution
            category = improvement.category.value
            improvements_summary['by_category'][category] = improvements_summary['by_category'].get(category, 0) + 1
            
            # Status distribution
            status = improvement.status.value
            improvements_summary['by_status'][status] = improvements_summary['by_status'].get(status, 0) + 1
        
        # Feature requests summary
        features_summary = {
            'total': len(self.feature_requests),
            'total_votes': sum(f.user_votes for f in self.feature_requests),
            'average_priority_score': sum(f.priority_score for f in self.feature_requests) / len(self.feature_requests) if self.feature_requests else 0
        }
        
        # Recent activity
        recent_activity = []
        
        # Add recent improvements
        recent_improvements = sorted(self.improvements, key=lambda x: x.created_at, reverse=True)[:5]
        for imp in recent_improvements:
            recent_activity.append({
                'type': 'improvement_identified',
                'title': imp.title,
                'priority': imp.priority.value,
                'timestamp': imp.created_at
            })
        
        # Add recent completions
        recent_completions = sorted(self.improvement_history, key=lambda x: x.updated_at, reverse=True)[:3]
        for comp in recent_completions:
            recent_activity.append({
                'type': 'improvement_completed',
                'title': comp.title,
                'timestamp': comp.updated_at
            })
        
        # Sort by timestamp
        recent_activity.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return {
            'improvements': improvements_summary,
            'feature_requests': features_summary,
            'recent_activity': recent_activity[:10],
            'last_analysis': self.last_analysis,
            'next_scheduled_analysis': {
                component: (
                    self.last_analysis.get(component, datetime.now()) + 
                    timedelta(hours=self.analysis_schedule[component])
                ).isoformat() if component in self.last_analysis else 'pending'
                for component in self.analysis_schedule.keys()
            }
        }
    
    async def get_top_improvements(self, limit: int = 10) -> List[Improvement]:
        """Get top priority improvements"""
        return self.improvements[:limit]
    
    async def get_roi_analysis(self) -> Dict[str, Any]:
        """Get ROI analysis for current improvements"""
        return await self.prioritization_engine.calculate_roi_estimates(self.improvements)