#!/usr/bin/env python3
"""
Improvement Plan Generator
Creates prioritized bug fix and improvement plan based on test analysis.
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any
from dataclasses import dataclass
from enum import Enum

class ActionType(Enum):
    BUG_FIX = "bug_fix"
    OPTIMIZATION = "optimization"
    ENHANCEMENT = "enhancement"
    INFRASTRUCTURE = "infrastructure"
    SECURITY = "security"

class Priority(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

@dataclass
class Action:
    id: str
    title: str
    description: str
    action_type: ActionType
    priority: Priority
    estimated_effort: str  # hours/days/weeks
    dependencies: List[str]
    implementation_steps: List[str]
    acceptance_criteria: List[str]
    assigned_to: str
    due_date: str
    status: str = "not_started"

class ImprovementPlanGenerator:
    """Generate prioritized improvement plan from test analysis"""
    
    def __init__(self, analysis_file: str = 'test_analysis_report.json'):
        self.analysis_file = analysis_file
        self.analysis = self.load_analysis()
        self.actions = []
        
    def load_analysis(self) -> Dict[str, Any]:
        """Load test analysis results"""
        if not os.path.exists(self.analysis_file):
            raise FileNotFoundError(f"Analysis file not found: {self.analysis_file}")
            
        with open(self.analysis_file, 'r') as f:
            return json.load(f)
            
    def generate_improvement_plan(self) -> List[Action]:
        """Generate comprehensive improvement plan"""
        print("📋 Generating improvement plan...")
        
        # Convert issues to bug fix actions
        self.create_bug_fix_actions()
        
        # Convert improvements to enhancement actions
        self.create_enhancement_actions()
        
        # Add infrastructure improvements
        self.create_infrastructure_actions()
        
        # Add security hardening actions
        self.create_security_actions()
        
        # Add performance optimization actions
        self.create_performance_actions()
        
        # Sort by priority and dependencies
        self.prioritize_actions()
        
        # Set realistic timelines
        self.set_timelines()
        
        return self.actions
        
    def create_bug_fix_actions(self):
        """Create actions for bug fixes from issues"""
        issues = self.analysis.get('issues', [])
        
        for i, issue in enumerate(issues):
            if issue['category'] in ['bug', 'security']:
                action = Action(
                    id=f"BUG-{i+1:03d}",
                    title=f"Fix: {issue['title']}",
                    description=issue['description'],
                    action_type=ActionType.BUG_FIX if issue['category'] == 'bug' else ActionType.SECURITY,
                    priority=Priority(issue['severity']),
                    estimated_effort=self.estimate_effort(issue),
                    dependencies=[],
                    implementation_steps=issue['reproduction_steps'] + [issue['suggested_fix']],
                    acceptance_criteria=[
                        f"Test suite {issue['test_suite']} passes",
                        "No regression in related functionality",
                        "Code review completed"
                    ],
                    assigned_to="development_team",
                    due_date=""  # Will be set later
                )
                
                self.actions.append(action)
                
    def create_enhancement_actions(self):
        """Create actions for improvements and enhancements"""
        improvements = self.analysis.get('improvements', [])
        
        for i, improvement in enumerate(improvements):
            action = Action(
                id=f"ENH-{i+1:03d}",
                title=improvement['title'],
                description=improvement['description'],
                action_type=ActionType.ENHANCEMENT,
                priority=self.convert_priority_score(improvement['priority_score']),
                estimated_effort=improvement['effort'],
                dependencies=[],
                implementation_steps=improvement['implementation_steps'],
                acceptance_criteria=[
                    "Implementation completed according to specifications",
                    "All tests pass",
                    "Performance impact measured and acceptable",
                    "Documentation updated"
                ],
                assigned_to="development_team",
                due_date=""
            )
            
            self.actions.append(action)
            
    def create_infrastructure_actions(self):
        """Create infrastructure improvement actions"""
        
        # Test automation improvements
        if self.needs_test_automation():
            action = Action(
                id="INF-001",
                title="Enhance Test Automation Infrastructure",
                description="Improve test automation coverage and reliability",
                action_type=ActionType.INFRASTRUCTURE,
                priority=Priority.HIGH,
                estimated_effort="2 weeks",
                dependencies=[],
                implementation_steps=[
                    "Set up comprehensive CI/CD pipeline",
                    "Implement parallel test execution",
                    "Add automated test reporting",
                    "Create test data management system",
                    "Set up test environment isolation"
                ],
                acceptance_criteria=[
                    "All test suites run automatically on commits",
                    "Test execution time reduced by 50%",
                    "Test results are automatically reported",
                    "Test environments are properly isolated"
                ],
                assigned_to="devops_team",
                due_date=""
            )
            
            self.actions.append(action)
            
        # Monitoring and alerting
        action = Action(
            id="INF-002",
            title="Implement Production Monitoring",
            description="Set up comprehensive monitoring and alerting for production systems",
            action_type=ActionType.INFRASTRUCTURE,
            priority=Priority.HIGH,
            estimated_effort="1 week",
            dependencies=["INF-001"],
            implementation_steps=[
                "Set up application performance monitoring",
                "Configure error tracking and alerting",
                "Implement health check endpoints",
                "Create monitoring dashboards",
                "Set up log aggregation and analysis"
            ],
            acceptance_criteria=[
                "All critical metrics are monitored",
                "Alerts are configured for anomalies",
                "Dashboards provide real-time visibility",
                "Log analysis is automated"
            ],
            assigned_to="devops_team",
            due_date=""
        )
        
        self.actions.append(action)
        
    def create_security_actions(self):
        """Create security hardening actions"""
        
        # Security testing
        security_issues = [
            issue for issue in self.analysis.get('issues', [])
            if issue['category'] == 'security'
        ]
        
        if security_issues or not self.has_passing_security_tests():
            action = Action(
                id="SEC-001",
                title="Implement Comprehensive Security Testing",
                description="Establish robust security testing and vulnerability management",
                action_type=ActionType.SECURITY,
                priority=Priority.CRITICAL,
                estimated_effort="1 week",
                dependencies=[],
                implementation_steps=[
                    "Set up automated security scanning",
                    "Implement dependency vulnerability checking",
                    "Add input validation testing",
                    "Create security code review checklist",
                    "Set up penetration testing procedures"
                ],
                acceptance_criteria=[
                    "All security tests pass",
                    "No high-severity vulnerabilities detected",
                    "Security scanning is automated",
                    "Security review process is documented"
                ],
                assigned_to="security_team",
                due_date=""
            )
            
            self.actions.append(action)
            
        # Data protection
        action = Action(
            id="SEC-002",
            title="Enhance Data Protection Measures",
            description="Implement comprehensive data protection and privacy controls",
            action_type=ActionType.SECURITY,
            priority=Priority.HIGH,
            estimated_effort="3 days",
            dependencies=["SEC-001"],
            implementation_steps=[
                "Implement data encryption at rest and in transit",
                "Add access control and audit logging",
                "Create data retention and deletion policies",
                "Implement privacy mode enhancements",
                "Add data anonymization for logs"
            ],
            acceptance_criteria=[
                "All sensitive data is encrypted",
                "Access controls are properly implemented",
                "Audit logs capture all data access",
                "Privacy mode prevents data leakage"
            ],
            assigned_to="security_team",
            due_date=""
        )
        
        self.actions.append(action)
        
    def create_performance_actions(self):
        """Create performance optimization actions"""
        
        # Performance optimization
        performance_issues = [
            issue for issue in self.analysis.get('issues', [])
            if issue['category'] == 'performance'
        ]
        
        if performance_issues or self.needs_performance_optimization():
            action = Action(
                id="PERF-001",
                title="Optimize Application Performance",
                description="Implement performance optimizations based on test results",
                action_type=ActionType.OPTIMIZATION,
                priority=Priority.MEDIUM,
                estimated_effort="1 week",
                dependencies=[],
                implementation_steps=[
                    "Profile application bottlenecks",
                    "Optimize database queries and indexes",
                    "Implement caching strategies",
                    "Optimize frontend bundle size",
                    "Add performance monitoring"
                ],
                acceptance_criteria=[
                    "Document processing time meets SLA",
                    "Search response time < 500ms",
                    "Frontend load time < 2 seconds",
                    "Performance regression tests pass"
                ],
                assigned_to="development_team",
                due_date=""
            )
            
            self.actions.append(action)
            
        # Load testing
        action = Action(
            id="PERF-002",
            title="Implement Load Testing Framework",
            description="Create comprehensive load testing to validate scalability",
            action_type=ActionType.INFRASTRUCTURE,
            priority=Priority.MEDIUM,
            estimated_effort="5 days",
            dependencies=["PERF-001"],
            implementation_steps=[
                "Set up load testing infrastructure",
                "Create realistic user scenarios",
                "Implement automated load testing",
                "Set up performance baselines",
                "Create scalability testing procedures"
            ],
            acceptance_criteria=[
                "Load tests run automatically",
                "System handles expected user load",
                "Performance baselines are established",
                "Scalability limits are documented"
            ],
            assigned_to="qa_team",
            due_date=""
        )
        
        self.actions.append(action)
        
    def estimate_effort(self, issue: Dict[str, Any]) -> str:
        """Estimate effort required to fix an issue"""
        severity = issue['severity']
        category = issue['category']
        
        if severity == 'critical':
            if category == 'security':
                return "1-2 days"
            else:
                return "2-3 days"
        elif severity == 'high':
            return "1-2 days"
        elif severity == 'medium':
            return "4-8 hours"
        else:
            return "2-4 hours"
            
    def convert_priority_score(self, score: int) -> Priority:
        """Convert numeric priority score to Priority enum"""
        if score >= 90:
            return Priority.CRITICAL
        elif score >= 70:
            return Priority.HIGH
        elif score >= 50:
            return Priority.MEDIUM
        else:
            return Priority.LOW
            
    def needs_test_automation(self) -> bool:
        """Check if test automation improvements are needed"""
        test_suites = self.analysis.get('test_suites', {})
        
        # Check for skipped or failed test suites
        skipped_suites = [
            name for name, result in test_suites.items()
            if result.get('skipped', False)
        ]
        
        failed_suites = [
            name for name, result in test_suites.items()
            if not result.get('passed', False)
        ]
        
        return len(skipped_suites) > 2 or len(failed_suites) > 3
        
    def has_passing_security_tests(self) -> bool:
        """Check if security tests are passing"""
        security_suite = self.analysis.get('test_suites', {}).get('security_tests', {})
        return security_suite.get('passed', False)
        
    def needs_performance_optimization(self) -> bool:
        """Check if performance optimization is needed"""
        execution_time = self.analysis.get('total_execution_time', 0)
        return execution_time > 1800  # 30 minutes
        
    def prioritize_actions(self):
        """Sort actions by priority and dependencies"""
        
        # Create priority order
        priority_order = {
            Priority.CRITICAL: 4,
            Priority.HIGH: 3,
            Priority.MEDIUM: 2,
            Priority.LOW: 1
        }
        
        # Sort by priority first, then by action type
        self.actions.sort(
            key=lambda x: (
                priority_order[x.priority],
                1 if x.action_type == ActionType.SECURITY else 0,
                1 if x.action_type == ActionType.BUG_FIX else 0
            ),
            reverse=True
        )
        
    def set_timelines(self):
        """Set realistic timelines for actions"""
        start_date = datetime.now()
        current_date = start_date
        
        # Group actions by priority
        critical_actions = [a for a in self.actions if a.priority == Priority.CRITICAL]
        high_actions = [a for a in self.actions if a.priority == Priority.HIGH]
        medium_actions = [a for a in self.actions if a.priority == Priority.MEDIUM]
        low_actions = [a for a in self.actions if a.priority == Priority.LOW]
        
        # Set due dates for critical actions (immediate)
        for action in critical_actions:
            if "day" in action.estimated_effort:
                days = int(action.estimated_effort.split()[0].split('-')[-1])
                action.due_date = (current_date + timedelta(days=days)).isoformat()
            else:
                action.due_date = (current_date + timedelta(days=3)).isoformat()
                
        # Set due dates for high priority actions (within 2 weeks)
        current_date += timedelta(days=3)
        for action in high_actions:
            if "week" in action.estimated_effort:
                weeks = int(action.estimated_effort.split()[0].split('-')[-1])
                action.due_date = (current_date + timedelta(weeks=weeks)).isoformat()
            else:
                action.due_date = (current_date + timedelta(days=7)).isoformat()
                
        # Set due dates for medium priority actions (within 1 month)
        current_date += timedelta(weeks=2)
        for action in medium_actions:
            action.due_date = (current_date + timedelta(weeks=2)).isoformat()
            
        # Set due dates for low priority actions (within 2 months)
        current_date += timedelta(weeks=2)
        for action in low_actions:
            action.due_date = (current_date + timedelta(weeks=4)).isoformat()
            
    def generate_plan_document(self) -> Dict[str, Any]:
        """Generate improvement plan document"""
        return {
            'plan_created': datetime.now().isoformat(),
            'based_on_analysis': self.analysis.get('analysis_timestamp'),
            'overall_status': self.analysis.get('overall_status'),
            'summary': {
                'total_actions': len(self.actions),
                'critical_actions': len([a for a in self.actions if a.priority == Priority.CRITICAL]),
                'high_priority_actions': len([a for a in self.actions if a.priority == Priority.HIGH]),
                'estimated_completion': max([a.due_date for a in self.actions]) if self.actions else None
            },
            'actions': [
                {
                    'id': action.id,
                    'title': action.title,
                    'description': action.description,
                    'action_type': action.action_type.value,
                    'priority': action.priority.value,
                    'estimated_effort': action.estimated_effort,
                    'dependencies': action.dependencies,
                    'implementation_steps': action.implementation_steps,
                    'acceptance_criteria': action.acceptance_criteria,
                    'assigned_to': action.assigned_to,
                    'due_date': action.due_date,
                    'status': action.status
                }
                for action in self.actions
            ]
        }
        
    def save_plan(self, filepath: str = 'improvement_plan.json'):
        """Save improvement plan to file"""
        plan = self.generate_plan_document()
        
        with open(filepath, 'w') as f:
            json.dump(plan, f, indent=2)
            
        print(f"📋 Improvement plan saved to {filepath}")
        return plan
        
    def generate_markdown_report(self, filepath: str = 'IMPROVEMENT_PLAN.md'):
        """Generate markdown report for the improvement plan"""
        plan = self.generate_plan_document()
        
        markdown_content = f"""# Product Improvement Plan

Generated: {plan['plan_created']}
Based on Analysis: {plan['based_on_analysis']}
Overall Status: {plan['overall_status']}

## Summary

- **Total Actions**: {plan['summary']['total_actions']}
- **Critical Actions**: {plan['summary']['critical_actions']}
- **High Priority Actions**: {plan['summary']['high_priority_actions']}
- **Estimated Completion**: {plan['summary']['estimated_completion']}

## Action Items

"""
        
        # Group actions by priority
        priorities = ['critical', 'high', 'medium', 'low']
        
        for priority in priorities:
            priority_actions = [a for a in plan['actions'] if a['priority'] == priority]
            
            if priority_actions:
                markdown_content += f"\n### {priority.title()} Priority Actions\n\n"
                
                for action in priority_actions:
                    markdown_content += f"#### {action['id']}: {action['title']}\n\n"
                    markdown_content += f"**Description**: {action['description']}\n\n"
                    markdown_content += f"**Type**: {action['action_type']}\n"
                    markdown_content += f"**Effort**: {action['estimated_effort']}\n"
                    markdown_content += f"**Assigned To**: {action['assigned_to']}\n"
                    markdown_content += f"**Due Date**: {action['due_date']}\n"
                    
                    if action['dependencies']:
                        markdown_content += f"**Dependencies**: {', '.join(action['dependencies'])}\n"
                        
                    markdown_content += "\n**Implementation Steps**:\n"
                    for step in action['implementation_steps']:
                        markdown_content += f"- {step}\n"
                        
                    markdown_content += "\n**Acceptance Criteria**:\n"
                    for criteria in action['acceptance_criteria']:
                        markdown_content += f"- {criteria}\n"
                        
                    markdown_content += "\n---\n\n"
                    
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
            
        print(f"📄 Markdown report saved to {filepath}")

def main():
    """Main execution function"""
    try:
        generator = ImprovementPlanGenerator()
        actions = generator.generate_improvement_plan()
        plan = generator.save_plan()
        generator.generate_markdown_report()
        
        # Print summary
        print("\n" + "="*60)
        print("📋 IMPROVEMENT PLAN SUMMARY")
        print("="*60)
        
        print(f"Total Actions: {plan['summary']['total_actions']}")
        print(f"Critical Actions: {plan['summary']['critical_actions']}")
        print(f"High Priority Actions: {plan['summary']['high_priority_actions']}")
        
        if actions:
            print("\n🚨 Next 5 Actions to Take:")
            for action in actions[:5]:
                print(f"  {action.priority.value.upper()}: {action.title} (Due: {action.due_date[:10]})")
                
        return True
        
    except Exception as e:
        print(f"💥 Plan generation failed: {str(e)}")
        return False

if __name__ == "__main__":
    main()