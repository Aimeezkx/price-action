"""
Improvement impact measurement and tracking system
"""
import json
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import statistics
from .models import (
    Improvement, ImprovementImpact, PerformanceMetric, 
    CodeQualityMetric, UserFeedback, ImprovementStatus
)


class ImpactTracker:
    """Tracks and measures the impact of implemented improvements"""
    
    def __init__(self):
        self.impact_storage = []
        self.baseline_metrics = {}
        self.tracking_periods = {
            'immediate': 1,    # 1 day
            'short_term': 7,   # 1 week
            'medium_term': 30, # 1 month
            'long_term': 90    # 3 months
        }
    
    async def establish_baseline(self, 
                               improvement_id: str,
                               metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Establish baseline metrics before implementing improvement"""
        baseline = {
            'improvement_id': improvement_id,
            'timestamp': datetime.now(),
            'metrics': metrics,
            'measurement_type': 'baseline'
        }
        
        self.baseline_metrics[improvement_id] = baseline
        return baseline
    
    async def measure_impact(self, 
                           improvement_id: str,
                           post_implementation_metrics: Dict[str, Any],
                           measurement_period: str = 'immediate') -> List[ImprovementImpact]:
        """Measure impact after improvement implementation"""
        if improvement_id not in self.baseline_metrics:
            raise ValueError(f"No baseline found for improvement {improvement_id}")
        
        baseline = self.baseline_metrics[improvement_id]
        baseline_metrics = baseline['metrics']
        
        impacts = []
        
        # Compare each metric
        for metric_name, after_value in post_implementation_metrics.items():
            if metric_name in baseline_metrics:
                before_value = baseline_metrics[metric_name]
                
                # Calculate improvement percentage
                if before_value != 0:
                    improvement_percentage = ((after_value - before_value) / abs(before_value)) * 100
                else:
                    improvement_percentage = 100 if after_value > 0 else 0
                
                # Determine validation method based on metric type
                validation_method = self._determine_validation_method(metric_name)
                
                impact = ImprovementImpact(
                    improvement_id=improvement_id,
                    metric_name=metric_name,
                    before_value=before_value,
                    after_value=after_value,
                    improvement_percentage=improvement_percentage,
                    validation_method=validation_method
                )
                
                impacts.append(impact)
                self.impact_storage.append(impact)
        
        return impacts
    
    def _determine_validation_method(self, metric_name: str) -> str:
        """Determine appropriate validation method for metric"""
        validation_methods = {
            'response_time': 'performance_monitoring',
            'memory_usage': 'resource_monitoring',
            'cpu_usage': 'resource_monitoring',
            'throughput': 'load_testing',
            'error_rate': 'error_monitoring',
            'test_coverage': 'code_analysis',
            'complexity': 'static_analysis',
            'user_satisfaction': 'user_feedback',
            'bug_count': 'issue_tracking',
            'deployment_frequency': 'deployment_metrics'
        }
        
        for key, method in validation_methods.items():
            if key in metric_name.lower():
                return method
        
        return 'manual_measurement'
    
    async def track_performance_impact(self, 
                                     improvement_id: str,
                                     operation: str,
                                     tracking_period_days: int = 7) -> Dict[str, Any]:
        """Track performance impact over time"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=tracking_period_days)
        
        # Get baseline performance
        baseline = self.baseline_metrics.get(improvement_id, {})
        baseline_metrics = baseline.get('metrics', {})
        
        # Simulate performance data collection (in real implementation, 
        # this would query actual monitoring systems)
        performance_data = await self._collect_performance_data(
            operation, start_date, end_date
        )
        
        analysis = {
            'improvement_id': improvement_id,
            'operation': operation,
            'tracking_period_days': tracking_period_days,
            'baseline_metrics': baseline_metrics,
            'current_metrics': performance_data.get('current', {}),
            'trend_analysis': performance_data.get('trend', {}),
            'impact_summary': {}
        }
        
        # Calculate impact summary
        if baseline_metrics:
            current_metrics = performance_data.get('current', {})
            impact_summary = {}
            
            for metric, baseline_value in baseline_metrics.items():
                if metric in current_metrics:
                    current_value = current_metrics[metric]
                    
                    if baseline_value != 0:
                        improvement_pct = ((baseline_value - current_value) / abs(baseline_value)) * 100
                        
                        # For metrics where lower is better (response_time, error_rate)
                        if metric in ['response_time', 'error_rate', 'memory_usage', 'cpu_usage']:
                            impact_summary[metric] = {
                                'baseline': baseline_value,
                                'current': current_value,
                                'improvement_percentage': improvement_pct,
                                'status': 'improved' if improvement_pct > 0 else 'degraded'
                            }
                        # For metrics where higher is better (throughput, coverage)
                        else:
                            impact_summary[metric] = {
                                'baseline': baseline_value,
                                'current': current_value,
                                'improvement_percentage': -improvement_pct,
                                'status': 'improved' if improvement_pct < 0 else 'degraded'
                            }
            
            analysis['impact_summary'] = impact_summary
        
        return analysis
    
    async def _collect_performance_data(self, 
                                      operation: str,
                                      start_date: datetime,
                                      end_date: datetime) -> Dict[str, Any]:
        """Collect performance data for specified period"""
        # Simulate performance data collection
        # In real implementation, this would query monitoring systems
        
        # Generate sample data points
        days = (end_date - start_date).days
        data_points = []
        
        for i in range(days):
            date = start_date + timedelta(days=i)
            # Simulate improving performance over time
            improvement_factor = 1 - (i * 0.05)  # 5% improvement per day
            
            data_point = {
                'date': date,
                'response_time': max(0.5, 2.0 * improvement_factor),
                'memory_usage': max(100, 300 * improvement_factor),
                'cpu_usage': max(20, 60 * improvement_factor),
                'throughput': min(200, 100 / improvement_factor),
                'error_rate': max(0.01, 0.05 * improvement_factor)
            }
            data_points.append(data_point)
        
        # Calculate current metrics (average of last 3 days)
        recent_points = data_points[-3:] if len(data_points) >= 3 else data_points
        current_metrics = {}
        
        if recent_points:
            for metric in ['response_time', 'memory_usage', 'cpu_usage', 'throughput', 'error_rate']:
                values = [point[metric] for point in recent_points]
                current_metrics[metric] = statistics.mean(values)
        
        # Calculate trend
        trend_analysis = {}
        if len(data_points) >= 2:
            for metric in ['response_time', 'memory_usage', 'cpu_usage', 'throughput', 'error_rate']:
                values = [point[metric] for point in data_points]
                trend = self._calculate_trend(values)
                trend_analysis[metric] = trend
        
        return {
            'current': current_metrics,
            'trend': trend_analysis,
            'data_points': data_points
        }
    
    def _calculate_trend(self, values: List[float]) -> Dict[str, Any]:
        """Calculate trend analysis for metric values"""
        if len(values) < 2:
            return {'direction': 'stable', 'slope': 0, 'confidence': 0}
        
        # Simple linear regression
        n = len(values)
        x_values = list(range(n))
        
        x_mean = sum(x_values) / n
        y_mean = sum(values) / n
        
        numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_values, values))
        denominator = sum((x - x_mean) ** 2 for x in x_values)
        
        if denominator == 0:
            return {'direction': 'stable', 'slope': 0, 'confidence': 0}
        
        slope = numerator / denominator
        
        # Calculate R-squared for confidence
        y_pred = [y_mean + slope * (x - x_mean) for x in x_values]
        ss_res = sum((y - y_pred) ** 2 for y, y_pred in zip(values, y_pred))
        ss_tot = sum((y - y_mean) ** 2 for y in values)
        
        r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
        
        # Determine direction
        if abs(slope) < 0.01:
            direction = 'stable'
        elif slope > 0:
            direction = 'increasing'
        else:
            direction = 'decreasing'
        
        return {
            'direction': direction,
            'slope': slope,
            'confidence': max(0, r_squared)
        }
    
    async def track_code_quality_impact(self, 
                                      improvement_id: str,
                                      file_paths: List[str]) -> Dict[str, Any]:
        """Track code quality impact for specific files"""
        baseline = self.baseline_metrics.get(improvement_id, {})
        baseline_quality = baseline.get('metrics', {}).get('code_quality', {})
        
        # Simulate current code quality metrics
        current_quality = await self._collect_code_quality_metrics(file_paths)
        
        quality_impact = {
            'improvement_id': improvement_id,
            'files_analyzed': len(file_paths),
            'baseline_quality': baseline_quality,
            'current_quality': current_quality,
            'improvements': {}
        }
        
        # Calculate improvements for each metric
        quality_metrics = ['complexity', 'maintainability', 'test_coverage', 'code_smells', 'technical_debt']
        
        for metric in quality_metrics:
            if metric in baseline_quality and metric in current_quality:
                baseline_value = baseline_quality[metric]
                current_value = current_quality[metric]
                
                if baseline_value != 0:
                    # For metrics where lower is better (complexity, code_smells, technical_debt)
                    if metric in ['complexity', 'code_smells', 'technical_debt']:
                        improvement_pct = ((baseline_value - current_value) / abs(baseline_value)) * 100
                    # For metrics where higher is better (maintainability, test_coverage)
                    else:
                        improvement_pct = ((current_value - baseline_value) / abs(baseline_value)) * 100
                    
                    quality_impact['improvements'][metric] = {
                        'baseline': baseline_value,
                        'current': current_value,
                        'improvement_percentage': improvement_pct,
                        'status': 'improved' if improvement_pct > 0 else 'degraded'
                    }
        
        return quality_impact
    
    async def _collect_code_quality_metrics(self, file_paths: List[str]) -> Dict[str, float]:
        """Collect current code quality metrics"""
        # Simulate improved code quality metrics
        return {
            'complexity': 8.5,      # Reduced from baseline
            'maintainability': 85.0, # Increased from baseline
            'test_coverage': 92.0,   # Increased from baseline
            'code_smells': 3,        # Reduced from baseline
            'technical_debt': 12.0   # Reduced from baseline
        }
    
    async def track_user_satisfaction_impact(self, 
                                           improvement_id: str,
                                           feature_area: str,
                                           tracking_period_days: int = 30) -> Dict[str, Any]:
        """Track user satisfaction impact"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=tracking_period_days)
        
        # Get baseline user satisfaction
        baseline = self.baseline_metrics.get(improvement_id, {})
        baseline_satisfaction = baseline.get('metrics', {}).get('user_satisfaction', {})
        
        # Simulate user feedback collection
        current_feedback = await self._collect_user_feedback(feature_area, start_date, end_date)
        
        satisfaction_impact = {
            'improvement_id': improvement_id,
            'feature_area': feature_area,
            'tracking_period_days': tracking_period_days,
            'baseline_satisfaction': baseline_satisfaction,
            'current_satisfaction': current_feedback,
            'impact_analysis': {}
        }
        
        # Calculate satisfaction impact
        if baseline_satisfaction and current_feedback:
            baseline_rating = baseline_satisfaction.get('average_rating', 3.0)
            current_rating = current_feedback.get('average_rating', 3.0)
            
            baseline_sentiment = baseline_satisfaction.get('sentiment_score', 0.0)
            current_sentiment = current_feedback.get('sentiment_score', 0.0)
            
            satisfaction_impact['impact_analysis'] = {
                'rating_improvement': current_rating - baseline_rating,
                'sentiment_improvement': current_sentiment - baseline_sentiment,
                'feedback_volume_change': (
                    current_feedback.get('total_feedback', 0) - 
                    baseline_satisfaction.get('total_feedback', 0)
                ),
                'satisfaction_trend': self._determine_satisfaction_trend(
                    baseline_rating, current_rating, baseline_sentiment, current_sentiment
                )
            }
        
        return satisfaction_impact
    
    async def _collect_user_feedback(self, 
                                   feature_area: str,
                                   start_date: datetime,
                                   end_date: datetime) -> Dict[str, Any]:
        """Collect user feedback for specified period and feature area"""
        # Simulate improved user feedback
        return {
            'total_feedback': 45,
            'average_rating': 4.2,  # Improved from baseline
            'sentiment_score': 0.3,  # More positive
            'rating_distribution': {
                '5': 20, '4': 15, '3': 8, '2': 2, '1': 0
            },
            'common_themes': [
                'much faster now',
                'easier to use',
                'great improvement'
            ]
        }
    
    def _determine_satisfaction_trend(self, 
                                    baseline_rating: float,
                                    current_rating: float,
                                    baseline_sentiment: float,
                                    current_sentiment: float) -> str:
        """Determine overall satisfaction trend"""
        rating_change = current_rating - baseline_rating
        sentiment_change = current_sentiment - baseline_sentiment
        
        # Weighted score (rating is more important)
        overall_change = (rating_change * 0.7) + (sentiment_change * 0.3)
        
        if overall_change > 0.2:
            return 'significantly_improved'
        elif overall_change > 0.05:
            return 'improved'
        elif overall_change > -0.05:
            return 'stable'
        elif overall_change > -0.2:
            return 'declined'
        else:
            return 'significantly_declined'
    
    async def generate_impact_report(self, 
                                   improvement_id: str,
                                   report_period_days: int = 30) -> Dict[str, Any]:
        """Generate comprehensive impact report for an improvement"""
        # Get all impacts for this improvement
        improvement_impacts = [
            impact for impact in self.impact_storage 
            if impact.improvement_id == improvement_id
        ]
        
        if not improvement_impacts:
            return {'error': f'No impact data found for improvement {improvement_id}'}
        
        # Group impacts by metric type
        metric_groups = {}
        for impact in improvement_impacts:
            metric_type = self._categorize_metric(impact.metric_name)
            if metric_type not in metric_groups:
                metric_groups[metric_type] = []
            metric_groups[metric_type].append(impact)
        
        # Calculate summary statistics
        total_improvements = len([i for i in improvement_impacts if i.improvement_percentage > 0])
        total_degradations = len([i for i in improvement_impacts if i.improvement_percentage < 0])
        
        avg_improvement = statistics.mean([
            abs(i.improvement_percentage) for i in improvement_impacts 
            if i.improvement_percentage > 0
        ]) if total_improvements > 0 else 0
        
        report = {
            'improvement_id': improvement_id,
            'report_period_days': report_period_days,
            'generated_at': datetime.now(),
            'summary': {
                'total_metrics_tracked': len(improvement_impacts),
                'metrics_improved': total_improvements,
                'metrics_degraded': total_degradations,
                'average_improvement_percentage': avg_improvement,
                'overall_success_rate': (total_improvements / len(improvement_impacts)) * 100
            },
            'metric_groups': {},
            'recommendations': []
        }
        
        # Analyze each metric group
        for group_name, impacts in metric_groups.items():
            group_analysis = {
                'metrics_count': len(impacts),
                'average_improvement': statistics.mean([i.improvement_percentage for i in impacts]),
                'best_improvement': max(impacts, key=lambda x: x.improvement_percentage),
                'worst_impact': min(impacts, key=lambda x: x.improvement_percentage),
                'validation_methods': list(set(i.validation_method for i in impacts))
            }
            report['metric_groups'][group_name] = group_analysis
        
        # Generate recommendations
        report['recommendations'] = await self._generate_impact_recommendations(
            improvement_impacts, metric_groups
        )
        
        return report
    
    def _categorize_metric(self, metric_name: str) -> str:
        """Categorize metric by type"""
        metric_categories = {
            'performance': ['response_time', 'throughput', 'latency', 'speed'],
            'resource_usage': ['memory_usage', 'cpu_usage', 'disk_usage'],
            'quality': ['test_coverage', 'complexity', 'maintainability', 'code_smells'],
            'reliability': ['error_rate', 'uptime', 'availability', 'failure_rate'],
            'user_experience': ['satisfaction', 'rating', 'sentiment', 'usability']
        }
        
        metric_lower = metric_name.lower()
        for category, keywords in metric_categories.items():
            if any(keyword in metric_lower for keyword in keywords):
                return category
        
        return 'other'
    
    async def _generate_impact_recommendations(self, 
                                            impacts: List[ImprovementImpact],
                                            metric_groups: Dict[str, List[ImprovementImpact]]) -> List[str]:
        """Generate recommendations based on impact analysis"""
        recommendations = []
        
        # Check for significant improvements
        significant_improvements = [i for i in impacts if i.improvement_percentage > 20]
        if significant_improvements:
            recommendations.append(
                f"Excellent results achieved with {len(significant_improvements)} metrics showing >20% improvement. "
                "Consider applying similar techniques to other areas."
            )
        
        # Check for degradations
        degradations = [i for i in impacts if i.improvement_percentage < -5]
        if degradations:
            recommendations.append(
                f"Monitor {len(degradations)} metrics that showed degradation. "
                "Investigate potential side effects and consider mitigation strategies."
            )
        
        # Performance-specific recommendations
        if 'performance' in metric_groups:
            perf_impacts = metric_groups['performance']
            avg_perf_improvement = statistics.mean([i.improvement_percentage for i in perf_impacts])
            
            if avg_perf_improvement > 10:
                recommendations.append(
                    "Performance improvements are successful. Consider documenting the approach "
                    "for future performance optimization efforts."
                )
            elif avg_perf_improvement < 0:
                recommendations.append(
                    "Performance has degraded. Review implementation and consider rollback "
                    "or additional optimization."
                )
        
        # Quality-specific recommendations
        if 'quality' in metric_groups:
            quality_impacts = metric_groups['quality']
            quality_improvements = [i for i in quality_impacts if i.improvement_percentage > 0]
            
            if len(quality_improvements) == len(quality_impacts):
                recommendations.append(
                    "Code quality improvements are comprehensive. Consider establishing "
                    "these practices as team standards."
                )
        
        # General recommendations
        if len(recommendations) == 0:
            recommendations.append(
                "Impact results are mixed. Continue monitoring and consider iterative "
                "improvements based on the most significant findings."
            )
        
        return recommendations
    
    async def compare_improvements(self, 
                                 improvement_ids: List[str]) -> Dict[str, Any]:
        """Compare impact across multiple improvements"""
        comparison_data = {}
        
        for improvement_id in improvement_ids:
            impacts = [i for i in self.impact_storage if i.improvement_id == improvement_id]
            
            if impacts:
                avg_improvement = statistics.mean([i.improvement_percentage for i in impacts])
                success_rate = len([i for i in impacts if i.improvement_percentage > 0]) / len(impacts)
                
                comparison_data[improvement_id] = {
                    'total_metrics': len(impacts),
                    'average_improvement': avg_improvement,
                    'success_rate': success_rate,
                    'best_metric': max(impacts, key=lambda x: x.improvement_percentage).metric_name,
                    'best_improvement': max(i.improvement_percentage for i in impacts)
                }
        
        # Rank improvements
        ranked_improvements = sorted(
            comparison_data.items(),
            key=lambda x: x[1]['average_improvement'],
            reverse=True
        )
        
        return {
            'comparison_data': comparison_data,
            'ranked_improvements': ranked_improvements,
            'best_performing': ranked_improvements[0] if ranked_improvements else None,
            'analysis_summary': {
                'total_improvements_compared': len(improvement_ids),
                'average_success_rate': statistics.mean([
                    data['success_rate'] for data in comparison_data.values()
                ]) if comparison_data else 0
            }
        }