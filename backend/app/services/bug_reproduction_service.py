"""
Bug Reproduction Documentation Service

This service provides comprehensive bug reproduction step documentation,
automated reproduction script generation, and verification workflows.
"""

import json
import os
import subprocess
import tempfile
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import yaml

from .bug_tracking_service import TestIssue, ReproductionStep

@dataclass
class ReproductionEnvironment:
    """Environment configuration for bug reproduction"""
    os_version: str
    python_version: str
    browser_version: Optional[str]
    database_version: str
    dependencies: Dict[str, str]
    environment_variables: Dict[str, str]
    test_data_version: str

@dataclass
class ReproductionScript:
    """Automated reproduction script"""
    script_id: str
    issue_id: str
    script_type: str  # 'pytest', 'playwright', 'manual'
    script_content: str
    setup_commands: List[str]
    cleanup_commands: List[str]
    expected_outcome: str
    created_at: datetime
    last_run: Optional[datetime] = None
    success_rate: float = 0.0
    run_count: int = 0

class BugReproductionService:
    """Service for documenting and automating bug reproduction"""
    
    def __init__(self, storage_path: str = "bug_reproduction"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(exist_ok=True)
        
        # Create subdirectories
        (self.storage_path / "scripts").mkdir(exist_ok=True)
        (self.storage_path / "environments").mkdir(exist_ok=True)
        (self.storage_path / "reports").mkdir(exist_ok=True)
        
        self.scripts: Dict[str, ReproductionScript] = {}
        self._load_existing_scripts()
    
    def _load_existing_scripts(self):
        """Load existing reproduction scripts"""
        scripts_file = self.storage_path / "scripts.json"
        if scripts_file.exists():
            try:
                with open(scripts_file, 'r') as f:
                    scripts_data = json.load(f)
                
                for script_data in scripts_data:
                    script_data['created_at'] = datetime.fromisoformat(script_data['created_at'])
                    if script_data.get('last_run'):
                        script_data['last_run'] = datetime.fromisoformat(script_data['last_run'])
                    
                    script = ReproductionScript(**script_data)
                    self.scripts[script.script_id] = script
                    
            except Exception as e:
                print(f"Error loading reproduction scripts: {e}")
    
    def _save_scripts(self):
        """Save reproduction scripts to storage"""
        scripts_file = self.storage_path / "scripts.json"
        
        scripts_data = []
        for script in self.scripts.values():
            script_dict = asdict(script)
            script_dict['created_at'] = script.created_at.isoformat()
            if script.last_run:
                script_dict['last_run'] = script.last_run.isoformat()
            scripts_data.append(script_dict)
        
        with open(scripts_file, 'w') as f:
            json.dump(scripts_data, f, indent=2)
    
    def document_reproduction_steps(self, issue: TestIssue) -> str:
        """Generate comprehensive reproduction documentation"""
        doc_content = f"""# Bug Reproduction Guide

## Issue Information
- **Issue ID**: {issue.id}
- **Title**: {issue.title}
- **Severity**: {issue.severity.value}
- **Category**: {issue.category.value}
- **Status**: {issue.status.value}

## Description
{issue.description}

## Environment
"""
        
        for key, value in issue.environment.items():
            doc_content += f"- **{key}**: {value}\n"
        
        doc_content += f"""
## Expected Behavior
{issue.expected_behavior}

## Actual Behavior
{issue.actual_behavior}

## Reproduction Steps
"""
        
        if issue.reproduction_steps:
            for i, step in enumerate(issue.reproduction_steps, 1):
                doc_content += f"""
### Step {step.step_number}: {step.action}

**Expected Result**: {step.expected_result}
**Actual Result**: {step.actual_result}

"""
                if step.data_used:
                    doc_content += f"**Test Data Used**:\n```json\n{json.dumps(step.data_used, indent=2)}\n```\n\n"
                
                if step.screenshot_path:
                    doc_content += f"**Screenshot**: {step.screenshot_path}\n\n"
        else:
            doc_content += "No detailed reproduction steps provided.\n"
        
        if issue.error_trace:
            doc_content += f"""
## Error Trace
```
{issue.error_trace}
```
"""
        
        doc_content += f"""
## Verification
To verify this issue is fixed:
1. Follow the reproduction steps above
2. Confirm the expected behavior occurs instead of the actual behavior
3. Run any associated regression tests

## Notes
- Created: {issue.created_at.strftime('%Y-%m-%d %H:%M:%S')}
- Last Updated: {issue.updated_at.strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        # Save documentation
        doc_file = self.storage_path / "reports" / f"reproduction_{issue.id}.md"
        with open(doc_file, 'w') as f:
            f.write(doc_content)
        
        return doc_content
    
    def create_reproduction_script(self, issue: TestIssue, script_type: str = "pytest") -> ReproductionScript:
        """Create automated reproduction script"""
        script_id = f"repro_{issue.id}_{script_type}"
        
        if script_type == "pytest":
            script_content = self._generate_pytest_reproduction(issue)
        elif script_type == "playwright":
            script_content = self._generate_playwright_reproduction(issue)
        elif script_type == "api":
            script_content = self._generate_api_reproduction(issue)
        else:
            script_content = self._generate_manual_reproduction(issue)
        
        setup_commands = self._generate_setup_commands(issue, script_type)
        cleanup_commands = self._generate_cleanup_commands(issue, script_type)
        
        script = ReproductionScript(
            script_id=script_id,
            issue_id=issue.id,
            script_type=script_type,
            script_content=script_content,
            setup_commands=setup_commands,
            cleanup_commands=cleanup_commands,
            expected_outcome=f"Should reproduce: {issue.actual_behavior}",
            created_at=datetime.now()
        )
        
        self.scripts[script_id] = script
        self._save_scripts()
        
        # Save script to file
        script_file = self.storage_path / "scripts" / f"{script_id}.py"
        with open(script_file, 'w') as f:
            f.write(script_content)
        
        return script
    
    def _generate_pytest_reproduction(self, issue: TestIssue) -> str:
        """Generate pytest reproduction script"""
        return f'''"""
Reproduction script for issue: {issue.title}

Issue ID: {issue.id}
This script reproduces the bug to verify it exists before fixing.
"""

import pytest
import json
from datetime import datetime

class TestIssueReproduction:
    """Reproduction test for issue {issue.id}"""
    
    def test_reproduce_issue_{issue.id.replace("-", "_")}(self):
        """
        Reproduce: {issue.title}
        
        Expected: {issue.expected_behavior}
        Actual: {issue.actual_behavior}
        """
        # Setup test environment
        {self._generate_test_setup(issue)}
        
        # Execute reproduction steps
        {self._generate_reproduction_execution(issue)}
        
        # This test should fail until the bug is fixed
        # When the bug is fixed, this assertion should be updated
        with pytest.raises(Exception, match=r".*{issue.actual_behavior[:50]}.*"):
            # The operation that causes the bug
            result = self._execute_problematic_operation()
            
        # TODO: Update this test when bug is fixed to assert correct behavior
        
    def _execute_problematic_operation(self):
        """Execute the operation that demonstrates the bug"""
        # TODO: Implement the specific operation based on reproduction steps
        {self._format_reproduction_steps_as_code(issue)}
        pass
        
    def setup_method(self):
        """Setup for each test method"""
        {self._generate_method_setup(issue)}
        
    def teardown_method(self):
        """Cleanup after each test method"""
        {self._generate_method_cleanup(issue)}
'''
    
    def _generate_playwright_reproduction(self, issue: TestIssue) -> str:
        """Generate Playwright reproduction script"""
        return f'''"""
Playwright reproduction script for UI issue: {issue.title}

Issue ID: {issue.id}
This script reproduces the UI bug using browser automation.
"""

import pytest
from playwright.async_api import Page, expect

class TestUIReproduction:
    """UI reproduction test for issue {issue.id}"""
    
    @pytest.mark.asyncio
    async def test_reproduce_ui_issue_{issue.id.replace("-", "_")}(self, page: Page):
        """
        Reproduce UI issue: {issue.title}
        
        Expected: {issue.expected_behavior}
        Actual: {issue.actual_behavior}
        """
        # Navigate to the problematic page
        await page.goto("http://localhost:3000")
        
        # Execute reproduction steps
        {self._generate_ui_reproduction_steps(issue)}
        
        # Capture screenshot of the issue
        await page.screenshot(path=f"reproduction_{{datetime.now().strftime('%Y%m%d_%H%M%S')}}.png")
        
        # This assertion should fail until the bug is fixed
        # TODO: Update when bug is fixed
        try:
            {self._generate_ui_assertions(issue)}
            pytest.fail("Expected UI issue did not occur - bug may be fixed")
        except Exception as e:
            # Expected failure - bug is reproduced
            print(f"Successfully reproduced issue: {{e}}")
'''
    
    def _generate_api_reproduction(self, issue: TestIssue) -> str:
        """Generate API reproduction script"""
        return f'''"""
API reproduction script for issue: {issue.title}

Issue ID: {issue.id}
This script reproduces the API bug.
"""

import requests
import json
import pytest

class TestAPIReproduction:
    """API reproduction test for issue {issue.id}"""
    
    def test_reproduce_api_issue_{issue.id.replace("-", "_")}(self):
        """
        Reproduce API issue: {issue.title}
        
        Expected: {issue.expected_behavior}
        Actual: {issue.actual_behavior}
        """
        base_url = "http://localhost:8000"
        
        # Setup test data
        {self._generate_api_test_data(issue)}
        
        # Make the API request that causes the issue
        {self._generate_api_request(issue)}
        
        # Verify the issue occurs
        {self._generate_api_assertions(issue)}
'''
    
    def _generate_manual_reproduction(self, issue: TestIssue) -> str:
        """Generate manual reproduction checklist"""
        return f'''"""
Manual reproduction checklist for issue: {issue.title}

Issue ID: {issue.id}
Follow these steps to manually reproduce the issue.
"""

# Manual Reproduction Checklist

## Prerequisites
{self._format_environment_requirements(issue)}

## Steps to Reproduce
{self._format_manual_steps(issue)}

## Expected vs Actual Results
- **Expected**: {issue.expected_behavior}
- **Actual**: {issue.actual_behavior}

## Verification
- [ ] Issue reproduced successfully
- [ ] Screenshots/evidence captured
- [ ] Environment details documented
- [ ] Ready for developer investigation

## Notes
Add any additional observations or variations here.
'''
    
    def _generate_setup_commands(self, issue: TestIssue, script_type: str) -> List[str]:
        """Generate setup commands for reproduction"""
        commands = [
            "# Setup commands for reproduction",
            "pip install -r requirements.txt",
        ]
        
        if script_type == "playwright":
            commands.extend([
                "playwright install",
                "npm install"
            ])
        elif script_type == "api":
            commands.extend([
                "python -m pytest --setup-only",
                "docker-compose up -d database"
            ])
        
        # Add issue-specific setup
        if "database" in issue.description.lower():
            commands.append("python manage.py migrate")
            commands.append("python manage.py loaddata test_fixtures.json")
        
        return commands
    
    def _generate_cleanup_commands(self, issue: TestIssue, script_type: str) -> List[str]:
        """Generate cleanup commands"""
        commands = [
            "# Cleanup commands",
            "rm -f *.log",
            "rm -f *.tmp"
        ]
        
        if script_type == "playwright":
            commands.append("rm -f test-results/*.png")
        
        if "database" in issue.description.lower():
            commands.extend([
                "python manage.py flush --noinput",
                "docker-compose down"
            ])
        
        return commands
    
    def run_reproduction_script(self, script_id: str) -> Dict[str, Any]:
        """Run a reproduction script and return results"""
        if script_id not in self.scripts:
            return {"error": "Script not found"}
        
        script = self.scripts[script_id]
        script_file = self.storage_path / "scripts" / f"{script_id}.py"
        
        if not script_file.exists():
            return {"error": "Script file not found"}
        
        # Run setup commands
        setup_results = []
        for cmd in script.setup_commands:
            if cmd.startswith("#"):
                continue
            try:
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60)
                setup_results.append({
                    "command": cmd,
                    "success": result.returncode == 0,
                    "output": result.stdout,
                    "error": result.stderr
                })
            except subprocess.TimeoutExpired:
                setup_results.append({
                    "command": cmd,
                    "success": False,
                    "error": "Command timed out"
                })
        
        # Run the reproduction script
        script_result = None
        try:
            if script.script_type == "pytest":
                cmd = f"python -m pytest {script_file} -v"
            elif script.script_type == "playwright":
                cmd = f"python -m pytest {script_file} --browser chromium -v"
            else:
                cmd = f"python {script_file}"
            
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=300)
            script_result = {
                "success": result.returncode == 0,
                "output": result.stdout,
                "error": result.stderr,
                "return_code": result.returncode
            }
        except subprocess.TimeoutExpired:
            script_result = {
                "success": False,
                "error": "Script execution timed out"
            }
        
        # Run cleanup commands
        cleanup_results = []
        for cmd in script.cleanup_commands:
            if cmd.startswith("#"):
                continue
            try:
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
                cleanup_results.append({
                    "command": cmd,
                    "success": result.returncode == 0,
                    "output": result.stdout,
                    "error": result.stderr
                })
            except subprocess.TimeoutExpired:
                cleanup_results.append({
                    "command": cmd,
                    "success": False,
                    "error": "Cleanup command timed out"
                })
        
        # Update script statistics
        script.last_run = datetime.now()
        script.run_count += 1
        if script_result and script_result["success"]:
            script.success_rate = ((script.success_rate * (script.run_count - 1)) + 1) / script.run_count
        else:
            script.success_rate = (script.success_rate * (script.run_count - 1)) / script.run_count
        
        self._save_scripts()
        
        return {
            "script_id": script_id,
            "execution_time": datetime.now().isoformat(),
            "setup_results": setup_results,
            "script_result": script_result,
            "cleanup_results": cleanup_results,
            "overall_success": script_result and script_result["success"]
        }
    
    def verify_fix(self, issue_id: str) -> Dict[str, Any]:
        """Verify that an issue has been fixed by running reproduction scripts"""
        # Find all reproduction scripts for this issue
        issue_scripts = [s for s in self.scripts.values() if s.issue_id == issue_id]
        
        if not issue_scripts:
            return {"error": "No reproduction scripts found for this issue"}
        
        verification_results = []
        
        for script in issue_scripts:
            result = self.run_reproduction_script(script.script_id)
            
            # For reproduction scripts, failure means the bug still exists
            # Success means the bug is fixed (or the script needs updating)
            verification_results.append({
                "script_id": script.script_id,
                "script_type": script.script_type,
                "result": result,
                "bug_still_exists": not result.get("overall_success", False)
            })
        
        # Determine overall fix status
        bugs_still_exist = any(r["bug_still_exists"] for r in verification_results)
        
        return {
            "issue_id": issue_id,
            "verification_time": datetime.now().isoformat(),
            "scripts_run": len(verification_results),
            "bug_fixed": not bugs_still_exist,
            "detailed_results": verification_results
        }
    
    def generate_environment_snapshot(self, issue: TestIssue) -> ReproductionEnvironment:
        """Generate environment snapshot for reproduction"""
        try:
            # Get system information
            import platform
            import sys
            
            env = ReproductionEnvironment(
                os_version=platform.platform(),
                python_version=sys.version,
                browser_version=self._get_browser_version(),
                database_version=self._get_database_version(),
                dependencies=self._get_dependencies(),
                environment_variables=self._get_relevant_env_vars(),
                test_data_version=self._get_test_data_version()
            )
            
            # Save environment snapshot
            env_file = self.storage_path / "environments" / f"env_{issue.id}.json"
            with open(env_file, 'w') as f:
                json.dump(asdict(env), f, indent=2)
            
            return env
            
        except Exception as e:
            print(f"Error generating environment snapshot: {e}")
            return None
    
    def _get_browser_version(self) -> str:
        """Get browser version for UI testing"""
        try:
            result = subprocess.run(["google-chrome", "--version"], capture_output=True, text=True)
            return result.stdout.strip() if result.returncode == 0 else "Unknown"
        except:
            return "Unknown"
    
    def _get_database_version(self) -> str:
        """Get database version"""
        try:
            # This would need to be adapted based on your database
            result = subprocess.run(["psql", "--version"], capture_output=True, text=True)
            return result.stdout.strip() if result.returncode == 0 else "Unknown"
        except:
            return "Unknown"
    
    def _get_dependencies(self) -> Dict[str, str]:
        """Get Python package versions"""
        try:
            result = subprocess.run(["pip", "freeze"], capture_output=True, text=True)
            if result.returncode == 0:
                deps = {}
                for line in result.stdout.split('\n'):
                    if '==' in line:
                        name, version = line.split('==')
                        deps[name] = version
                return deps
        except:
            pass
        return {}
    
    def _get_relevant_env_vars(self) -> Dict[str, str]:
        """Get relevant environment variables"""
        relevant_vars = [
            'DATABASE_URL', 'REDIS_URL', 'DEBUG', 'ENVIRONMENT',
            'API_KEY', 'SECRET_KEY', 'OPENAI_API_KEY'
        ]
        
        env_vars = {}
        for var in relevant_vars:
            value = os.environ.get(var)
            if value:
                # Sanitize sensitive values
                if 'key' in var.lower() or 'secret' in var.lower():
                    env_vars[var] = f"***{value[-4:]}" if len(value) > 4 else "***"
                else:
                    env_vars[var] = value
        
        return env_vars
    
    def _get_test_data_version(self) -> str:
        """Get test data version or hash"""
        try:
            test_data_path = Path("backend/tests/test_data")
            if test_data_path.exists():
                # Simple hash of test data directory
                import hashlib
                hash_md5 = hashlib.md5()
                for file_path in sorted(test_data_path.rglob("*")):
                    if file_path.is_file():
                        hash_md5.update(str(file_path).encode())
                        with open(file_path, 'rb') as f:
                            hash_md5.update(f.read())
                return hash_md5.hexdigest()[:8]
        except:
            pass
        return "unknown"
    
    # Helper methods for code generation
    def _generate_test_setup(self, issue: TestIssue) -> str:
        return "# TODO: Add specific test setup based on issue details"
    
    def _generate_reproduction_execution(self, issue: TestIssue) -> str:
        return "# TODO: Add reproduction execution logic"
    
    def _format_reproduction_steps_as_code(self, issue: TestIssue) -> str:
        if not issue.reproduction_steps:
            return "# No specific reproduction steps provided"
        
        code_lines = []
        for step in issue.reproduction_steps:
            code_lines.append(f"# Step {step.step_number}: {step.action}")
            code_lines.append("# TODO: Implement this step")
        
        return "\n        ".join(code_lines)
    
    def _generate_method_setup(self, issue: TestIssue) -> str:
        return "pass  # TODO: Add method setup"
    
    def _generate_method_cleanup(self, issue: TestIssue) -> str:
        return "pass  # TODO: Add method cleanup"
    
    def _generate_ui_reproduction_steps(self, issue: TestIssue) -> str:
        if not issue.reproduction_steps:
            return "# No UI steps provided"
        
        steps = []
        for step in issue.reproduction_steps:
            steps.append(f"# {step.action}")
            steps.append("# TODO: Implement UI interaction")
        
        return "\n        ".join(steps)
    
    def _generate_ui_assertions(self, issue: TestIssue) -> str:
        return f"# TODO: Add UI assertions for: {issue.expected_behavior}"
    
    def _generate_api_test_data(self, issue: TestIssue) -> str:
        return "test_data = {}  # TODO: Add API test data"
    
    def _generate_api_request(self, issue: TestIssue) -> str:
        return "# TODO: Add API request that causes the issue"
    
    def _generate_api_assertions(self, issue: TestIssue) -> str:
        return "# TODO: Add API response assertions"
    
    def _format_environment_requirements(self, issue: TestIssue) -> str:
        env_text = ""
        for key, value in issue.environment.items():
            env_text += f"- {key}: {value}\n"
        return env_text
    
    def _format_manual_steps(self, issue: TestIssue) -> str:
        if not issue.reproduction_steps:
            return "No detailed steps provided."
        
        steps_text = ""
        for step in issue.reproduction_steps:
            steps_text += f"{step.step_number}. {step.action}\n"
            steps_text += f"   Expected: {step.expected_result}\n"
            steps_text += f"   Actual: {step.actual_result}\n\n"
        
        return steps_text