#!/usr/bin/env python3
"""
Notification service for automated testing pipeline.
Sends alerts for test failures, performance regressions, and other issues.
"""

import argparse
import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Any, Optional
import urllib.request
import urllib.parse
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


class NotificationService:
    """Service for sending test failure notifications"""
    
    def __init__(self):
        self.slack_webhook_url = os.getenv('SLACK_WEBHOOK_URL')
        self.email_config = {
            'smtp_server': os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
            'smtp_port': int(os.getenv('SMTP_PORT', '587')),
            'username': os.getenv('EMAIL_USERNAME'),
            'password': os.getenv('EMAIL_PASSWORD'),
            'from_email': os.getenv('FROM_EMAIL'),
            'to_emails': os.getenv('TO_EMAILS', '').split(',') if os.getenv('TO_EMAILS') else []
        }
        self.github_token = os.getenv('GITHUB_TOKEN')
        self.repository = os.getenv('GITHUB_REPOSITORY')
    
    def send_slack_notification(self, message: Dict[str, Any]) -> bool:
        """Send notification to Slack"""
        if not self.slack_webhook_url:
            print("Warning: SLACK_WEBHOOK_URL not configured")
            return False
        
        try:
            payload = json.dumps(message).encode('utf-8')
            req = urllib.request.Request(
                self.slack_webhook_url,
                data=payload,
                headers={'Content-Type': 'application/json'}
            )
            
            with urllib.request.urlopen(req) as response:
                if response.status == 200:
                    print("Slack notification sent successfully")
                    return True
                else:
                    print(f"Slack notification failed with status: {response.status}")
                    return False
        
        except Exception as e:
            print(f"Error sending Slack notification: {e}")
            return False
    
    def send_email_notification(self, subject: str, body: str, html_body: Optional[str] = None) -> bool:
        """Send email notification"""
        if not all([self.email_config['username'], self.email_config['password'], 
                   self.email_config['from_email'], self.email_config['to_emails']]):
            print("Warning: Email configuration incomplete")
            return False
        
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.email_config['from_email']
            msg['To'] = ', '.join(self.email_config['to_emails'])
            
            # Add text part
            text_part = MIMEText(body, 'plain')
            msg.attach(text_part)
            
            # Add HTML part if provided
            if html_body:
                html_part = MIMEText(html_body, 'html')
                msg.attach(html_part)
            
            # Send email
            with smtplib.SMTP(self.email_config['smtp_server'], self.email_config['smtp_port']) as server:
                server.starttls()
                server.login(self.email_config['username'], self.email_config['password'])
                server.send_message(msg)
            
            print("Email notification sent successfully")
            return True
        
        except Exception as e:
            print(f"Error sending email notification: {e}")
            return False
    
    def create_github_issue(self, title: str, body: str, labels: List[str] = None) -> bool:
        """Create GitHub issue for test failures"""
        if not all([self.github_token, self.repository]):
            print("Warning: GitHub configuration incomplete")
            return False
        
        try:
            url = f"https://api.github.com/repos/{self.repository}/issues"
            
            issue_data = {
                'title': title,
                'body': body,
                'labels': labels or ['bug', 'automated-testing']
            }
            
            req = urllib.request.Request(
                url,
                data=json.dumps(issue_data).encode('utf-8'),
                headers={
                    'Authorization': f'token {self.github_token}',
                    'Content-Type': 'application/json',
                    'Accept': 'application/vnd.github.v3+json'
                }
            )
            
            with urllib.request.urlopen(req) as response:
                if response.status == 201:
                    issue_data = json.loads(response.read().decode('utf-8'))
                    print(f"GitHub issue created: {issue_data['html_url']}")
                    return True
                else:
                    print(f"GitHub issue creation failed with status: {response.status}")
                    return False
        
        except Exception as e:
            print(f"Error creating GitHub issue: {e}")
            return False
    
    def notify_test_failure(self, test_results: Dict[str, Any], context: Dict[str, Any] = None):
        """Send notifications for test failures"""
        context = context or {}
        
        # Extract failure information
        failure_summary = self._extract_failure_summary(test_results)
        
        # Create notification messages
        slack_message = self._create_slack_failure_message(failure_summary, context)
        email_subject, email_body, email_html = self._create_email_failure_message(failure_summary, context)
        github_title, github_body = self._create_github_issue_content(failure_summary, context)
        
        # Send notifications
        notifications_sent = []
        
        if self.send_slack_notification(slack_message):
            notifications_sent.append('Slack')
        
        if self.send_email_notification(email_subject, email_body, email_html):
            notifications_sent.append('Email')
        
        # Only create GitHub issue for critical failures
        if failure_summary['critical_failures'] > 0:
            if self.create_github_issue(github_title, github_body, ['critical', 'bug', 'automated-testing']):
                notifications_sent.append('GitHub Issue')
        
        print(f"Notifications sent via: {', '.join(notifications_sent) if notifications_sent else 'None'}")
        return notifications_sent
    
    def notify_performance_regression(self, regression_results: Dict[str, Any], context: Dict[str, Any] = None):
        """Send notifications for performance regressions"""
        context = context or {}
        
        # Create notification messages
        slack_message = self._create_slack_regression_message(regression_results, context)
        email_subject, email_body, email_html = self._create_email_regression_message(regression_results, context)
        
        # Send notifications
        notifications_sent = []
        
        if self.send_slack_notification(slack_message):
            notifications_sent.append('Slack')
        
        if self.send_email_notification(email_subject, email_body, email_html):
            notifications_sent.append('Email')
        
        print(f"Performance regression notifications sent via: {', '.join(notifications_sent) if notifications_sent else 'None'}")
        return notifications_sent
    
    def notify_security_issues(self, security_results: Dict[str, Any], context: Dict[str, Any] = None):
        """Send notifications for security issues"""
        context = context or {}
        
        # Extract security issue information
        high_severity_issues = [
            issue for issue in security_results.get('results', [])
            if issue.get('issue_severity') == 'HIGH'
        ]
        
        if not high_severity_issues:
            return []
        
        # Create notification messages
        slack_message = self._create_slack_security_message(security_results, context)
        email_subject, email_body, email_html = self._create_email_security_message(security_results, context)
        github_title, github_body = self._create_github_security_issue_content(security_results, context)
        
        # Send notifications
        notifications_sent = []
        
        if self.send_slack_notification(slack_message):
            notifications_sent.append('Slack')
        
        if self.send_email_notification(email_subject, email_body, email_html):
            notifications_sent.append('Email')
        
        if self.create_github_issue(github_title, github_body, ['security', 'high-priority']):
            notifications_sent.append('GitHub Issue')
        
        print(f"Security notifications sent via: {', '.join(notifications_sent) if notifications_sent else 'None'}")
        return notifications_sent
    
    def _extract_failure_summary(self, test_results: Dict[str, Any]) -> Dict[str, Any]:
        """Extract failure summary from test results"""
        summary = {
            'total_failures': 0,
            'critical_failures': 0,
            'failed_tests': [],
            'error_tests': [],
            'test_types': {}
        }
        
        # Process different test result formats
        if 'summary' in test_results:
            test_summary = test_results['summary']
            summary['total_failures'] = test_summary.get('total_failed', 0) + test_summary.get('total_errors', 0)
            
            for test_type, type_data in test_summary.get('test_types', {}).items():
                if type_data.get('failed', 0) > 0 or type_data.get('errors', 0) > 0:
                    summary['test_types'][test_type] = type_data
                    
                    # Consider security and integration test failures as critical
                    if test_type in ['security', 'integration']:
                        summary['critical_failures'] += type_data.get('failed', 0) + type_data.get('errors', 0)
        
        return summary
    
    def _create_slack_failure_message(self, failure_summary: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Create Slack message for test failures"""
        repo = context.get('repository', 'Unknown Repository')
        branch = context.get('branch', 'unknown')
        commit = context.get('commit', 'unknown')[:8]
        workflow_url = context.get('workflow_url', '')
        
        color = "danger" if failure_summary['critical_failures'] > 0 else "warning"
        
        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"🚨 *Test Failures Detected*\n\n*Repository:* {repo}\n*Branch:* {branch}\n*Commit:* {commit}"
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Total Failures:*\n{failure_summary['total_failures']}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Critical Failures:*\n{failure_summary['critical_failures']}"
                    }
                ]
            }
        ]
        
        # Add test type breakdown
        if failure_summary['test_types']:
            test_type_text = ""
            for test_type, data in failure_summary['test_types'].items():
                failed = data.get('failed', 0)
                errors = data.get('errors', 0)
                test_type_text += f"• {test_type.title()}: {failed + errors} failures\n"
            
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Failed Test Types:*\n{test_type_text}"
                }
            })
        
        # Add action button
        if workflow_url:
            blocks.append({
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "View Details"
                        },
                        "url": workflow_url,
                        "style": "danger" if failure_summary['critical_failures'] > 0 else "primary"
                    }
                ]
            })
        
        return {
            "text": "Test Failures Detected",
            "attachments": [
                {
                    "color": color,
                    "blocks": blocks
                }
            ]
        }
    
    def _create_email_failure_message(self, failure_summary: Dict[str, Any], context: Dict[str, Any]) -> tuple:
        """Create email message for test failures"""
        repo = context.get('repository', 'Unknown Repository')
        branch = context.get('branch', 'unknown')
        commit = context.get('commit', 'unknown')
        workflow_url = context.get('workflow_url', '')
        
        subject = f"🚨 Test Failures in {repo} ({branch})"
        
        # Text body
        text_body = f"""
Test Failures Detected

Repository: {repo}
Branch: {branch}
Commit: {commit}
Timestamp: {datetime.now().isoformat()}

Summary:
- Total Failures: {failure_summary['total_failures']}
- Critical Failures: {failure_summary['critical_failures']}

Failed Test Types:
"""
        
        for test_type, data in failure_summary['test_types'].items():
            failed = data.get('failed', 0)
            errors = data.get('errors', 0)
            text_body += f"- {test_type.title()}: {failed + errors} failures\n"
        
        if workflow_url:
            text_body += f"\nView Details: {workflow_url}"
        
        # HTML body
        html_body = f"""
<html>
<body>
    <h2>🚨 Test Failures Detected</h2>
    
    <table style="border-collapse: collapse; width: 100%;">
        <tr>
            <td style="padding: 8px; border: 1px solid #ddd;"><strong>Repository:</strong></td>
            <td style="padding: 8px; border: 1px solid #ddd;">{repo}</td>
        </tr>
        <tr>
            <td style="padding: 8px; border: 1px solid #ddd;"><strong>Branch:</strong></td>
            <td style="padding: 8px; border: 1px solid #ddd;">{branch}</td>
        </tr>
        <tr>
            <td style="padding: 8px; border: 1px solid #ddd;"><strong>Commit:</strong></td>
            <td style="padding: 8px; border: 1px solid #ddd;">{commit}</td>
        </tr>
        <tr>
            <td style="padding: 8px; border: 1px solid #ddd;"><strong>Total Failures:</strong></td>
            <td style="padding: 8px; border: 1px solid #ddd; color: red;"><strong>{failure_summary['total_failures']}</strong></td>
        </tr>
        <tr>
            <td style="padding: 8px; border: 1px solid #ddd;"><strong>Critical Failures:</strong></td>
            <td style="padding: 8px; border: 1px solid #ddd; color: red;"><strong>{failure_summary['critical_failures']}</strong></td>
        </tr>
    </table>
    
    <h3>Failed Test Types:</h3>
    <ul>
"""
        
        for test_type, data in failure_summary['test_types'].items():
            failed = data.get('failed', 0)
            errors = data.get('errors', 0)
            html_body += f"<li>{test_type.title()}: {failed + errors} failures</li>"
        
        html_body += "</ul>"
        
        if workflow_url:
            html_body += f'<p><a href="{workflow_url}" style="background-color: #dc3545; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">View Details</a></p>'
        
        html_body += "</body></html>"
        
        return subject, text_body, html_body
    
    def _create_github_issue_content(self, failure_summary: Dict[str, Any], context: Dict[str, Any]) -> tuple:
        """Create GitHub issue content for test failures"""
        repo = context.get('repository', 'Unknown Repository')
        branch = context.get('branch', 'unknown')
        commit = context.get('commit', 'unknown')
        workflow_url = context.get('workflow_url', '')
        
        title = f"Critical Test Failures in {branch} branch"
        
        body = f"""
## Test Failure Report

**Repository:** {repo}
**Branch:** {branch}
**Commit:** {commit}
**Timestamp:** {datetime.now().isoformat()}

### Summary
- **Total Failures:** {failure_summary['total_failures']}
- **Critical Failures:** {failure_summary['critical_failures']}

### Failed Test Types
"""
        
        for test_type, data in failure_summary['test_types'].items():
            failed = data.get('failed', 0)
            errors = data.get('errors', 0)
            body += f"- **{test_type.title()}:** {failed + errors} failures\n"
        
        body += "\n### Action Required\n"
        body += "This issue was automatically created due to critical test failures. Please investigate and fix the failing tests.\n\n"
        
        if workflow_url:
            body += f"**Workflow Details:** {workflow_url}\n"
        
        body += "\n---\n*This issue was automatically created by the testing pipeline.*"
        
        return title, body
    
    def _create_slack_regression_message(self, regression_results: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Create Slack message for performance regressions"""
        repo = context.get('repository', 'Unknown Repository')
        branch = context.get('branch', 'unknown')
        
        regressions = regression_results.get('regressions', [])
        
        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"⚠️ *Performance Regressions Detected*\n\n*Repository:* {repo}\n*Branch:* {branch}"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Regressions Found:* {len(regressions)}"
                }
            }
        ]
        
        # Add top regressions
        if regressions:
            regression_text = ""
            for regression in regressions[:3]:  # Show top 3
                name = regression['name']
                change = regression['change_percent']
                regression_text += f"• {name}: {change:+.1f}%\n"
            
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Top Regressions:*\n{regression_text}"
                }
            })
        
        return {
            "text": "Performance Regressions Detected",
            "attachments": [
                {
                    "color": "warning",
                    "blocks": blocks
                }
            ]
        }
    
    def _create_email_regression_message(self, regression_results: Dict[str, Any], context: Dict[str, Any]) -> tuple:
        """Create email message for performance regressions"""
        repo = context.get('repository', 'Unknown Repository')
        branch = context.get('branch', 'unknown')
        
        regressions = regression_results.get('regressions', [])
        
        subject = f"⚠️ Performance Regressions in {repo} ({branch})"
        
        text_body = f"""
Performance Regressions Detected

Repository: {repo}
Branch: {branch}
Timestamp: {datetime.now().isoformat()}

Regressions Found: {len(regressions)}

Top Regressions:
"""
        
        for regression in regressions[:5]:  # Show top 5
            name = regression['name']
            change = regression['change_percent']
            text_body += f"- {name}: {change:+.1f}%\n"
        
        html_body = f"""
<html>
<body>
    <h2>⚠️ Performance Regressions Detected</h2>
    <p><strong>Repository:</strong> {repo}</p>
    <p><strong>Branch:</strong> {branch}</p>
    <p><strong>Regressions Found:</strong> {len(regressions)}</p>
    
    <h3>Top Regressions:</h3>
    <ul>
"""
        
        for regression in regressions[:5]:
            name = regression['name']
            change = regression['change_percent']
            html_body += f"<li>{name}: <span style='color: red;'>{change:+.1f}%</span></li>"
        
        html_body += "</ul></body></html>"
        
        return subject, text_body, html_body
    
    def _create_slack_security_message(self, security_results: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Create Slack message for security issues"""
        repo = context.get('repository', 'Unknown Repository')
        branch = context.get('branch', 'unknown')
        
        severity_counts = security_results.get('severity_counts', {})
        high_issues = severity_counts.get('HIGH', 0)
        
        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"🔒 *Security Issues Detected*\n\n*Repository:* {repo}\n*Branch:* {branch}"
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*High Severity:*\n{high_issues}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Medium Severity:*\n{severity_counts.get('MEDIUM', 0)}"
                    }
                ]
            }
        ]
        
        return {
            "text": "Security Issues Detected",
            "attachments": [
                {
                    "color": "danger",
                    "blocks": blocks
                }
            ]
        }
    
    def _create_email_security_message(self, security_results: Dict[str, Any], context: Dict[str, Any]) -> tuple:
        """Create email message for security issues"""
        repo = context.get('repository', 'Unknown Repository')
        branch = context.get('branch', 'unknown')
        
        severity_counts = security_results.get('severity_counts', {})
        
        subject = f"🔒 Security Issues in {repo} ({branch})"
        
        text_body = f"""
Security Issues Detected

Repository: {repo}
Branch: {branch}
Timestamp: {datetime.now().isoformat()}

Severity Breakdown:
- High: {severity_counts.get('HIGH', 0)}
- Medium: {severity_counts.get('MEDIUM', 0)}
- Low: {severity_counts.get('LOW', 0)}
"""
        
        html_body = f"""
<html>
<body>
    <h2>🔒 Security Issues Detected</h2>
    <p><strong>Repository:</strong> {repo}</p>
    <p><strong>Branch:</strong> {branch}</p>
    
    <h3>Severity Breakdown:</h3>
    <ul>
        <li>High: <span style='color: red;'>{severity_counts.get('HIGH', 0)}</span></li>
        <li>Medium: <span style='color: orange;'>{severity_counts.get('MEDIUM', 0)}</span></li>
        <li>Low: {severity_counts.get('LOW', 0)}</li>
    </ul>
</body>
</html>
"""
        
        return subject, text_body, html_body
    
    def _create_github_security_issue_content(self, security_results: Dict[str, Any], context: Dict[str, Any]) -> tuple:
        """Create GitHub issue content for security issues"""
        repo = context.get('repository', 'Unknown Repository')
        branch = context.get('branch', 'unknown')
        
        severity_counts = security_results.get('severity_counts', {})
        high_issues = severity_counts.get('HIGH', 0)
        
        title = f"High Severity Security Issues in {branch} branch"
        
        body = f"""
## Security Issue Report

**Repository:** {repo}
**Branch:** {branch}
**Timestamp:** {datetime.now().isoformat()}

### Severity Breakdown
- **High:** {high_issues}
- **Medium:** {severity_counts.get('MEDIUM', 0)}
- **Low:** {severity_counts.get('LOW', 0)}

### Action Required
This issue was automatically created due to high severity security issues detected by automated scanning. Please review and address these security concerns immediately.

---
*This issue was automatically created by the security testing pipeline.*
"""
        
        return title, body


def main():
    parser = argparse.ArgumentParser(description='Send test failure notifications')
    parser.add_argument('--type', choices=['test-failure', 'performance-regression', 'security-issues'], 
                       required=True, help='Type of notification to send')
    parser.add_argument('--results-file', required=True, help='Results file to process')
    parser.add_argument('--context-file', help='Context file with additional information')
    
    args = parser.parse_args()
    
    # Load results
    try:
        with open(args.results_file, 'r') as f:
            results = json.load(f)
    except Exception as e:
        print(f"Error loading results file: {e}")
        sys.exit(1)
    
    # Load context
    context = {}
    if args.context_file:
        try:
            with open(args.context_file, 'r') as f:
                context = json.load(f)
        except Exception as e:
            print(f"Warning: Could not load context file: {e}")
    
    # Add environment context
    context.update({
        'repository': os.getenv('GITHUB_REPOSITORY', 'Unknown'),
        'branch': os.getenv('GITHUB_REF_NAME', 'unknown'),
        'commit': os.getenv('GITHUB_SHA', 'unknown'),
        'workflow_url': f"https://github.com/{os.getenv('GITHUB_REPOSITORY', '')}/actions/runs/{os.getenv('GITHUB_RUN_ID', '')}"
    })
    
    # Send notifications
    service = NotificationService()
    
    if args.type == 'test-failure':
        service.notify_test_failure(results, context)
    elif args.type == 'performance-regression':
        service.notify_performance_regression(results, context)
    elif args.type == 'security-issues':
        service.notify_security_issues(results, context)
    
    print("Notification process completed")


if __name__ == '__main__':
    main()