"""
Feature enhancement prioritization system
"""
import math
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from .models import (
    Improvement, FeatureRequest, ImprovementPriority, 
    ImprovementCategory, ImprovementStatus
)


class PrioritizationEngine:
    """Prioritizes improvements and feature requests based on multiple criteria"""
    
    def __init__(self):
        self.scoring_weights = {
            'business_value': 0.25,
            'user_impact': 0.25,
            'technical_feasibility': 0.20,
            'effort_efficiency': 0.15,
            'strategic_alignment': 0.10,
            'urgency': 0.05
        }
        
        self.category_multipliers = {
            ImprovementCategory.PERFORMANCE: 1.2,
            ImprovementCategory.SECURITY: 1.3,
            ImprovementCategory.USER_EXPERIENCE: 1.1,
            ImprovementCategory.CODE_QUALITY: 1.0,
            ImprovementCategory.ACCESSIBILITY: 1.1,
            ImprovementCategory.FEATURE_ENHANCEMENT: 0.9
        }
        
        self.strategic_priorities = {
            'user_retention': 1.3,
            'performance_optimization': 1.2,
            'security_enhancement': 1.4,
            'accessibility_improvement': 1.1,
            'code_quality': 1.0,
            'new_features': 0.8
        }
    
    async def prioritize_improvements(self, 
                                    improvements: List[Improvement],
                                    constraints: Optional[Dict[str, Any]] = None) -> List[Improvement]:
        """Prioritize improvements based on scoring algorithm"""
        if not improvements:
            return []
        
        # Calculate scores for each improvement
        scored_improvements = []
        for improvement in improvements:
            score = await self._calculate_improvement_score(improvement, constraints)
            improvement_copy = improvement.copy()
            improvement_copy.source_data = improvement_copy.source_data or {}
            improvement_copy.source_data['priority_score'] = score
            scored_improvements.append((score, improvement_copy))
        
        # Sort by score (descending)
        scored_improvements.sort(key=lambda x: x[0], reverse=True)
        
        # Return sorted improvements
        return [improvement for score, improvement in scored_improvements]
    
    async def _calculate_improvement_score(self, 
                                         improvement: Improvement,
                                         constraints: Optional[Dict[str, Any]] = None) -> float:
        """Calculate priority score for an improvement"""
        constraints = constraints or {}
        
        # Base scores for each criterion
        business_value_score = self._calculate_business_value_score(improvement)
        user_impact_score = self._calculate_user_impact_score(improvement)
        technical_feasibility_score = self._calculate_technical_feasibility_score(improvement)
        effort_efficiency_score = self._calculate_effort_efficiency_score(improvement)
        strategic_alignment_score = self._calculate_strategic_alignment_score(improvement)
        urgency_score = self._calculate_urgency_score(improvement)
        
        # Weighted score
        weighted_score = (
            business_value_score * self.scoring_weights['business_value'] +
            user_impact_score * self.scoring_weights['user_impact'] +
            technical_feasibility_score * self.scoring_weights['technical_feasibility'] +
            effort_efficiency_score * self.scoring_weights['effort_efficiency'] +
            strategic_alignment_score * self.scoring_weights['strategic_alignment'] +
            urgency_score * self.scoring_weights['urgency']
        )
        
        # Apply category multiplier
        category_multiplier = self.category_multipliers.get(improvement.category, 1.0)
        weighted_score *= category_multiplier
        
        # Apply constraints
        if constraints:
            weighted_score = self._apply_constraints(weighted_score, improvement, constraints)
        
        return weighted_score
    
    def _calculate_business_value_score(self, improvement: Improvement) -> float:
        """Calculate business value score (0-100)"""
        # Base score from expected impact
        base_score = improvement.expected_impact * 100
        
        # Adjust based on category
        if improvement.category == ImprovementCategory.PERFORMANCE:
            # Performance improvements have high business value
            base_score *= 1.2
        elif improvement.category == ImprovementCategory.SECURITY:
            # Security improvements are critical
            base_score *= 1.3
        elif improvement.category == ImprovementCategory.USER_EXPERIENCE:
            # UX improvements drive user satisfaction
            base_score *= 1.1
        
        # Adjust based on priority
        priority_multipliers = {
            ImprovementPriority.CRITICAL: 1.5,
            ImprovementPriority.HIGH: 1.2,
            ImprovementPriority.MEDIUM: 1.0,
            ImprovementPriority.LOW: 0.8
        }
        base_score *= priority_multipliers.get(improvement.priority, 1.0)
        
        return min(base_score, 100)
    
    def _calculate_user_impact_score(self, improvement: Improvement) -> float:
        """Calculate user impact score (0-100)"""
        # Extract user impact indicators from source data
        source_data = improvement.source_data or {}
        
        # Check for user feedback data
        if 'feedback_analysis' in source_data:
            feedback_data = source_data['feedback_analysis']
            frequency = feedback_data.get('frequency', 1)
            avg_rating = feedback_data.get('avg_rating', 3.0)
            
            # Higher frequency and lower rating = higher impact
            impact_score = (frequency * 10) + ((5 - avg_rating) * 20)
            return min(impact_score, 100)
        
        # Check for performance analysis data
        if 'analysis' in source_data:
            analysis_data = source_data['analysis']
            # Performance issues affect all users
            return 80
        
        # Default based on category and priority
        category_impacts = {
            ImprovementCategory.PERFORMANCE: 85,
            ImprovementCategory.SECURITY: 70,
            ImprovementCategory.USER_EXPERIENCE: 90,
            ImprovementCategory.ACCESSIBILITY: 75,
            ImprovementCategory.CODE_QUALITY: 40,
            ImprovementCategory.FEATURE_ENHANCEMENT: 60
        }
        
        base_impact = category_impacts.get(improvement.category, 50)
        
        # Adjust for priority
        if improvement.priority == ImprovementPriority.CRITICAL:
            base_impact *= 1.3
        elif improvement.priority == ImprovementPriority.HIGH:
            base_impact *= 1.1
        
        return min(base_impact, 100)
    
    def _calculate_technical_feasibility_score(self, improvement: Improvement) -> float:
        """Calculate technical feasibility score (0-100)"""
        # Base score from confidence
        base_score = improvement.confidence * 100
        
        # Adjust based on estimated effort
        if improvement.estimated_effort <= 8:  # 1 day
            effort_multiplier = 1.2
        elif improvement.estimated_effort <= 24:  # 3 days
            effort_multiplier = 1.0
        elif improvement.estimated_effort <= 40:  # 1 week
            effort_multiplier = 0.8
        else:  # > 1 week
            effort_multiplier = 0.6
        
        base_score *= effort_multiplier
        
        # Category-based feasibility
        category_feasibility = {
            ImprovementCategory.CODE_QUALITY: 1.1,  # Usually straightforward
            ImprovementCategory.PERFORMANCE: 0.9,   # Can be complex
            ImprovementCategory.SECURITY: 0.8,      # Requires careful implementation
            ImprovementCategory.USER_EXPERIENCE: 1.0,
            ImprovementCategory.ACCESSIBILITY: 1.0,
            ImprovementCategory.FEATURE_ENHANCEMENT: 0.7  # Often complex
        }
        
        base_score *= category_feasibility.get(improvement.category, 1.0)
        
        return min(base_score, 100)
    
    def _calculate_effort_efficiency_score(self, improvement: Improvement) -> float:
        """Calculate effort efficiency score (impact/effort ratio, 0-100)"""
        if improvement.estimated_effort <= 0:
            return 0
        
        # Calculate impact per hour of effort
        efficiency = (improvement.expected_impact * 100) / improvement.estimated_effort
        
        # Normalize to 0-100 scale (assuming max efficiency of 10 impact points per hour)
        normalized_efficiency = min(efficiency * 10, 100)
        
        return normalized_efficiency
    
    def _calculate_strategic_alignment_score(self, improvement: Improvement) -> float:
        """Calculate strategic alignment score (0-100)"""
        # Map categories to strategic priorities
        category_alignment = {
            ImprovementCategory.PERFORMANCE: 'performance_optimization',
            ImprovementCategory.SECURITY: 'security_enhancement',
            ImprovementCategory.USER_EXPERIENCE: 'user_retention',
            ImprovementCategory.ACCESSIBILITY: 'accessibility_improvement',
            ImprovementCategory.CODE_QUALITY: 'code_quality',
            ImprovementCategory.FEATURE_ENHANCEMENT: 'new_features'
        }
        
        strategic_priority = category_alignment.get(improvement.category, 'code_quality')
        multiplier = self.strategic_priorities.get(strategic_priority, 1.0)
        
        # Base alignment score
        base_score = 70  # Default alignment
        
        # Adjust based on strategic importance
        aligned_score = base_score * multiplier
        
        return min(aligned_score, 100)
    
    def _calculate_urgency_score(self, improvement: Improvement) -> float:
        """Calculate urgency score based on priority and age (0-100)"""
        # Priority-based urgency
        priority_urgency = {
            ImprovementPriority.CRITICAL: 100,
            ImprovementPriority.HIGH: 80,
            ImprovementPriority.MEDIUM: 50,
            ImprovementPriority.LOW: 20
        }
        
        base_urgency = priority_urgency.get(improvement.priority, 50)
        
        # Age-based urgency (older issues become more urgent)
        age_days = (datetime.now() - improvement.created_at).days
        age_multiplier = 1.0 + (age_days * 0.01)  # 1% increase per day
        
        urgency_score = base_urgency * min(age_multiplier, 1.5)  # Cap at 50% increase
        
        return min(urgency_score, 100)
    
    def _apply_constraints(self, 
                          score: float, 
                          improvement: Improvement,
                          constraints: Dict[str, Any]) -> float:
        """Apply constraints to modify the score"""
        modified_score = score
        
        # Resource constraints
        max_effort = constraints.get('max_effort_hours')
        if max_effort and improvement.estimated_effort > max_effort:
            modified_score *= 0.5  # Heavily penalize if over effort limit
        
        # Category constraints
        excluded_categories = constraints.get('excluded_categories', [])
        if improvement.category in excluded_categories:
            modified_score *= 0.1  # Almost exclude
        
        preferred_categories = constraints.get('preferred_categories', [])
        if preferred_categories and improvement.category in preferred_categories:
            modified_score *= 1.2  # Boost preferred categories
        
        # Timeline constraints
        max_timeline_days = constraints.get('max_timeline_days')
        if max_timeline_days:
            estimated_days = improvement.estimated_effort / 8  # Assume 8 hours per day
            if estimated_days > max_timeline_days:
                modified_score *= 0.7
        
        return modified_score
    
    async def prioritize_feature_requests(self, 
                                        feature_requests: List[FeatureRequest],
                                        constraints: Optional[Dict[str, Any]] = None) -> List[FeatureRequest]:
        """Prioritize feature requests using specialized scoring"""
        if not feature_requests:
            return []
        
        scored_requests = []
        for request in feature_requests:
            score = await self._calculate_feature_score(request, constraints)
            scored_requests.append((score, request))
        
        # Sort by score (descending)
        scored_requests.sort(key=lambda x: x[0], reverse=True)
        
        return [request for score, request in scored_requests]
    
    async def _calculate_feature_score(self, 
                                     request: FeatureRequest,
                                     constraints: Optional[Dict[str, Any]] = None) -> float:
        """Calculate priority score for a feature request"""
        constraints = constraints or {}
        
        # Weighted scoring for features
        user_demand_score = self._calculate_user_demand_score(request)
        business_value_score = request.business_value * 100
        feasibility_score = (1 - request.technical_complexity) * 100
        effort_efficiency_score = self._calculate_feature_efficiency_score(request)
        
        # Feature-specific weights
        feature_weights = {
            'user_demand': 0.35,
            'business_value': 0.30,
            'feasibility': 0.20,
            'efficiency': 0.15
        }
        
        weighted_score = (
            user_demand_score * feature_weights['user_demand'] +
            business_value_score * feature_weights['business_value'] +
            feasibility_score * feature_weights['feasibility'] +
            effort_efficiency_score * feature_weights['efficiency']
        )
        
        # Apply constraints
        if constraints:
            weighted_score = self._apply_feature_constraints(weighted_score, request, constraints)
        
        return weighted_score
    
    def _calculate_user_demand_score(self, request: FeatureRequest) -> float:
        """Calculate user demand score for feature request"""
        # Base score from user votes
        vote_score = min(request.user_votes * 10, 80)  # Cap at 80 for votes
        
        # Add priority score component
        priority_component = min(request.priority_score, 20)  # Cap at 20
        
        total_score = vote_score + priority_component
        return min(total_score, 100)
    
    def _calculate_feature_efficiency_score(self, request: FeatureRequest) -> float:
        """Calculate efficiency score for feature request"""
        if request.estimated_effort <= 0:
            return 0
        
        # Calculate value per hour of effort
        value_per_hour = (request.business_value * request.user_votes) / request.estimated_effort
        
        # Normalize to 0-100 scale
        normalized_score = min(value_per_hour * 50, 100)
        
        return normalized_score
    
    def _apply_feature_constraints(self, 
                                 score: float,
                                 request: FeatureRequest,
                                 constraints: Dict[str, Any]) -> float:
        """Apply constraints to feature request scoring"""
        modified_score = score
        
        # Effort constraints
        max_effort = constraints.get('max_feature_effort_hours')
        if max_effort and request.estimated_effort > max_effort:
            modified_score *= 0.3
        
        # Complexity constraints
        max_complexity = constraints.get('max_technical_complexity', 1.0)
        if request.technical_complexity > max_complexity:
            modified_score *= 0.5
        
        # Business value threshold
        min_business_value = constraints.get('min_business_value', 0.0)
        if request.business_value < min_business_value:
            modified_score *= 0.4
        
        return modified_score
    
    async def create_implementation_roadmap(self, 
                                          improvements: List[Improvement],
                                          feature_requests: List[FeatureRequest],
                                          constraints: Dict[str, Any]) -> Dict[str, Any]:
        """Create implementation roadmap based on priorities and constraints"""
        # Prioritize all items
        prioritized_improvements = await self.prioritize_improvements(improvements, constraints)
        prioritized_features = await self.prioritize_feature_requests(feature_requests, constraints)
        
        # Combine and create timeline
        total_capacity = constraints.get('total_capacity_hours', 160)  # Default 1 month
        sprint_capacity = constraints.get('sprint_capacity_hours', 40)  # Default 1 week
        
        roadmap = {
            'sprints': [],
            'total_items': len(prioritized_improvements) + len(prioritized_features),
            'total_effort': sum(i.estimated_effort for i in prioritized_improvements) + 
                           sum(f.estimated_effort for f in prioritized_features),
            'constraints': constraints
        }
        
        # Create sprints
        current_sprint = 1
        current_capacity = sprint_capacity
        current_sprint_items = []
        
        # Interleave improvements and features based on priority scores
        all_items = []
        
        # Add improvements with their scores
        for improvement in prioritized_improvements:
            score = improvement.source_data.get('priority_score', 0)
            all_items.append(('improvement', improvement, score))
        
        # Add features with their scores (calculate on the fly)
        for feature in prioritized_features:
            score = await self._calculate_feature_score(feature, constraints)
            all_items.append(('feature', feature, score))
        
        # Sort all items by score
        all_items.sort(key=lambda x: x[2], reverse=True)
        
        # Allocate to sprints
        for item_type, item, score in all_items:
            if current_capacity >= item.estimated_effort:
                current_sprint_items.append({
                    'type': item_type,
                    'item': item,
                    'score': score
                })
                current_capacity -= item.estimated_effort
            else:
                # Finalize current sprint
                if current_sprint_items:
                    roadmap['sprints'].append({
                        'sprint': current_sprint,
                        'items': current_sprint_items,
                        'total_effort': sprint_capacity - current_capacity,
                        'capacity_used': (sprint_capacity - current_capacity) / sprint_capacity
                    })
                
                # Start new sprint
                current_sprint += 1
                current_capacity = sprint_capacity - item.estimated_effort
                current_sprint_items = [{
                    'type': item_type,
                    'item': item,
                    'score': score
                }]
                
                # Check if we've exceeded total capacity
                if (current_sprint - 1) * sprint_capacity >= total_capacity:
                    break
        
        # Add final sprint if it has items
        if current_sprint_items:
            roadmap['sprints'].append({
                'sprint': current_sprint,
                'items': current_sprint_items,
                'total_effort': sprint_capacity - current_capacity,
                'capacity_used': (sprint_capacity - current_capacity) / sprint_capacity
            })
        
        return roadmap
    
    async def calculate_roi_estimates(self, 
                                    improvements: List[Improvement]) -> Dict[str, Any]:
        """Calculate ROI estimates for improvements"""
        total_effort = sum(i.estimated_effort for i in improvements)
        total_expected_impact = sum(i.expected_impact for i in improvements)
        
        # Estimate cost (assuming $100/hour developer cost)
        estimated_cost = total_effort * 100
        
        # Estimate benefits based on impact and category
        category_benefits = {
            ImprovementCategory.PERFORMANCE: 5000,  # User retention, efficiency
            ImprovementCategory.SECURITY: 10000,    # Risk mitigation
            ImprovementCategory.USER_EXPERIENCE: 3000,  # User satisfaction
            ImprovementCategory.CODE_QUALITY: 2000,     # Maintenance savings
            ImprovementCategory.ACCESSIBILITY: 1500,    # Market expansion
            ImprovementCategory.FEATURE_ENHANCEMENT: 4000  # Revenue potential
        }
        
        estimated_benefits = 0
        for improvement in improvements:
            category_benefit = category_benefits.get(improvement.category, 2000)
            estimated_benefits += category_benefit * improvement.expected_impact
        
        roi = ((estimated_benefits - estimated_cost) / estimated_cost * 100) if estimated_cost > 0 else 0
        
        return {
            'total_improvements': len(improvements),
            'total_effort_hours': total_effort,
            'estimated_cost': estimated_cost,
            'estimated_benefits': estimated_benefits,
            'roi_percentage': roi,
            'payback_period_months': (estimated_cost / (estimated_benefits / 12)) if estimated_benefits > 0 else float('inf'),
            'category_breakdown': self._calculate_category_breakdown(improvements, category_benefits)
        }
    
    def _calculate_category_breakdown(self, 
                                   improvements: List[Improvement],
                                   category_benefits: Dict[ImprovementCategory, float]) -> Dict[str, Any]:
        """Calculate ROI breakdown by category"""
        breakdown = {}
        
        for category in ImprovementCategory:
            category_improvements = [i for i in improvements if i.category == category]
            if not category_improvements:
                continue
            
            category_effort = sum(i.estimated_effort for i in category_improvements)
            category_cost = category_effort * 100
            category_benefit = sum(
                category_benefits.get(category, 2000) * i.expected_impact 
                for i in category_improvements
            )
            category_roi = ((category_benefit - category_cost) / category_cost * 100) if category_cost > 0 else 0
            
            breakdown[category.value] = {
                'count': len(category_improvements),
                'effort_hours': category_effort,
                'cost': category_cost,
                'benefits': category_benefit,
                'roi_percentage': category_roi
            }
        
        return breakdown