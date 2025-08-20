#!/usr/bin/env python3
"""
Production Readiness CLI
Command-line interface for production readiness validation
"""

import asyncio
import argparse
import json
import sys
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.production_readiness.validator import ProductionReadinessOrchestrator
from app.production_readiness.models import ValidationStatus


class ProductionReadinessCLI:
    """Command-line interface for production readiness validation"""
    
    def __init__(self):
        self.parser = self._create_parser()
    
    def _create_parser(self) -> argparse.ArgumentParser:
        """Create command-line argument parser"""
        parser = argparse.ArgumentParser(
            description="Production Readiness Validation CLI",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  # Run validation with config files
  python production_readiness_cli.py validate --env-config env.json --deploy-config deploy.json
  
  # Run validation with sample configs
  python production_readiness_cli.py validate --sample
  
  # Generate sample configuration files
  python production_readiness_cli.py generate-config --output-dir ./configs
  
  # Run quick validation check
  python production_readiness_cli.py quick-check --env-config env.json --deploy-config deploy.json
            """
        )
        
        subparsers = parser.add_subparsers(dest='command', help='Available commands')
        
        # Validate command
        validate_parser = subparsers.add_parser('validate', help='Run full production readiness validation')
        validate_parser.add_argument('--env-config', type=str, help='Path to environment configuration JSON file')
        validate_parser.add_argument('--deploy-config', type=str, help='Path to deployment configuration JSON file')
        validate_parser.add_argument('--sample', action='store_true', help='Use sample configurations')
        validate_parser.add_argument('--output', type=str, help='Output file for validation report (JSON)')
        validate_parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
        
        # Quick check command
        quick_parser = subparsers.add_parser('quick-check', help='Run quick validation check')
        quick_parser.add_argument('--env-config', type=str, required=True, help='Path to environment configuration JSON file')
        quick_parser.add_argument('--deploy-config', type=str, required=True, help='Path to deployment configuration JSON file')
        quick_parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
        
        # Generate config command
        config_parser = subparsers.add_parser('generate-config', help='Generate sample configuration files')
        config_parser.add_argument('--output-dir', type=str, default='.', help='Output directory for configuration files')
        config_parser.add_argument('--environment', type=str, default='production', help='Environment name')
        
        # List checks command
        list_parser = subparsers.add_parser('list-checks', help='List available validation checks')
        list_parser.add_argument('--category', type=str, help='Filter by category')
        list_parser.add_argument('--severity', type=str, help='Filter by severity')
        
        return parser
    
    async def run(self):
        """Run the CLI"""
        args = self.parser.parse_args()
        
        if not args.command:
            self.parser.print_help()
            return
        
        try:
            if args.command == 'validate':
                await self._run_validation(args)
            elif args.command == 'quick-check':
                await self._run_quick_check(args)
            elif args.command == 'generate-config':
                self._generate_config(args)
            elif args.command == 'list-checks':
                self._list_checks(args)
        except Exception as e:
            print(f"Error: {str(e)}", file=sys.stderr)
            sys.exit(1)
    
    async def _run_validation(self, args):
        """Run full production readiness validation"""
        print("🚀 Starting Production Readiness Validation...")
        print("=" * 60)
        
        # Load configurations
        if args.sample:
            print("📋 Using sample configurations")
            env_config = ProductionReadinessOrchestrator.create_sample_environment_config()
            deploy_config = ProductionReadinessOrchestrator.create_sample_deployment_config()
        else:
            if not args.env_config or not args.deploy_config:
                print("Error: --env-config and --deploy-config are required when not using --sample", file=sys.stderr)
                sys.exit(1)
            
            print(f"📋 Loading environment config from: {args.env_config}")
            print(f"📋 Loading deployment config from: {args.deploy_config}")
            
            env_config = self._load_json_file(args.env_config)
            deploy_config = self._load_json_file(args.deploy_config)
        
        # Display configuration summary
        print(f"\n🏗️  Environment: {env_config.get('name', 'unknown')}")
        print(f"🏗️  Version: {deploy_config.get('version', 'unknown')}")
        print(f"🏗️  URL: {env_config.get('url', 'unknown')}")
        
        # Run validation
        print("\n⏳ Running validation checks...")
        start_time = datetime.now()
        
        try:
            report = await ProductionReadinessOrchestrator.validate_production_readiness(
                env_config, deploy_config
            )
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            # Display results
            self._display_validation_results(report, duration, args.verbose)
            
            # Save report if requested
            if args.output:
                self._save_report(report, args.output)
                print(f"\n💾 Report saved to: {args.output}")
            
            # Exit with appropriate code
            sys.exit(0 if report.production_ready else 1)
            
        except Exception as e:
            print(f"\n❌ Validation failed: {str(e)}", file=sys.stderr)
            sys.exit(1)
    
    async def _run_quick_check(self, args):
        """Run quick validation check"""
        print("⚡ Running Quick Validation Check...")
        print("=" * 40)
        
        # Load configurations
        env_config = self._load_json_file(args.env_config)
        deploy_config = self._load_json_file(args.deploy_config)
        
        print(f"🏗️  Environment: {env_config.get('name', 'unknown')}")
        print(f"🏗️  Version: {deploy_config.get('version', 'unknown')}")
        
        # Run quick validation (simplified version)
        print("\n⏳ Running critical checks...")
        
        try:
            # For CLI, we'll run a subset of validation
            from app.production_readiness.models import ProductionEnvironment, DeploymentConfig
            from app.production_readiness.validator import ProductionReadinessValidator
            
            environment = ProductionEnvironment(**env_config)
            config = DeploymentConfig(**deploy_config)
            validator = ProductionReadinessValidator(environment, config)
            
            # Run only deployment checks for quick validation
            deployment_checks = await validator.deployment_validator.validate_deployment_readiness()
            
            # Filter critical checks
            critical_checks = [
                check for check in deployment_checks 
                if check.severity.value in ["critical", "high"]
            ]
            
            failed_critical = [c for c in critical_checks if c.status == ValidationStatus.FAILED]
            
            # Display results
            print(f"\n📊 Quick Check Results:")
            print(f"   Total critical checks: {len(critical_checks)}")
            print(f"   Failed critical checks: {len(failed_critical)}")
            
            if failed_critical:
                print(f"\n❌ Critical Issues Found:")
                for check in failed_critical:
                    print(f"   • {check.name}: {check.error_message}")
                
                print(f"\n🔧 Recommendation: Fix critical issues before full validation")
                sys.exit(1)
            else:
                print(f"\n✅ All critical checks passed!")
                print(f"🔧 Recommendation: Ready for full validation")
                sys.exit(0)
                
        except Exception as e:
            print(f"\n❌ Quick check failed: {str(e)}", file=sys.stderr)
            sys.exit(1)
    
    def _generate_config(self, args):
        """Generate sample configuration files"""
        print("📝 Generating sample configuration files...")
        
        output_dir = Path(args.output_dir)
        output_dir.mkdir(exist_ok=True)
        
        # Generate environment config
        env_config = ProductionReadinessOrchestrator.create_sample_environment_config()
        env_config["name"] = args.environment
        
        env_file = output_dir / f"{args.environment}_environment.json"
        with open(env_file, 'w') as f:
            json.dump(env_config, f, indent=2)
        
        # Generate deployment config
        deploy_config = ProductionReadinessOrchestrator.create_sample_deployment_config()
        
        deploy_file = output_dir / f"{args.environment}_deployment.json"
        with open(deploy_file, 'w') as f:
            json.dump(deploy_config, f, indent=2)
        
        print(f"✅ Generated configuration files:")
        print(f"   Environment: {env_file}")
        print(f"   Deployment: {deploy_file}")
        print(f"\n📝 Edit these files with your actual configuration values")
    
    def _list_checks(self, args):
        """List available validation checks"""
        print("📋 Available Validation Checks")
        print("=" * 40)
        
        # Define available checks (in a real implementation, this would be dynamic)
        checks = [
            {"name": "Database Connectivity", "category": "deployment", "severity": "critical"},
            {"name": "Redis Connectivity", "category": "deployment", "severity": "high"},
            {"name": "Environment Variables", "category": "deployment", "severity": "critical"},
            {"name": "Resource Limits", "category": "deployment", "severity": "high"},
            {"name": "Service Dependencies", "category": "deployment", "severity": "critical"},
            {"name": "Health Check Endpoints", "category": "deployment", "severity": "high"},
            {"name": "SSL/TLS Configuration", "category": "security", "severity": "critical"},
            {"name": "System Resources", "category": "deployment", "severity": "high"},
            {"name": "API Endpoints Functionality", "category": "deployment", "severity": "critical"},
            {"name": "Database Performance", "category": "performance", "severity": "high"},
            {"name": "Load Balancer Health", "category": "deployment", "severity": "high"},
            {"name": "Static Assets Delivery", "category": "deployment", "severity": "medium"},
            {"name": "Monitoring Systems", "category": "monitoring", "severity": "high"},
            {"name": "Backup Systems", "category": "disaster_recovery", "severity": "critical"},
            {"name": "Application Rollback", "category": "rollback", "severity": "critical"},
            {"name": "Database Rollback", "category": "rollback", "severity": "critical"},
            {"name": "Disaster Recovery", "category": "disaster_recovery", "severity": "critical"},
            {"name": "Backup Restoration", "category": "disaster_recovery", "severity": "high"},
            {"name": "Data Consistency", "category": "disaster_recovery", "severity": "critical"},
            {"name": "Recovery Time Objectives", "category": "disaster_recovery", "severity": "high"},
            {"name": "Prometheus Metrics Endpoint", "category": "monitoring", "severity": "critical"},
            {"name": "Alert Rules Configuration", "category": "monitoring", "severity": "high"},
            {"name": "Monitoring Dashboards", "category": "monitoring", "severity": "medium"},
            {"name": "Notification Channels", "category": "monitoring", "severity": "high"},
            {"name": "Metrics Collection", "category": "monitoring", "severity": "high"},
            {"name": "Log Aggregation", "category": "monitoring", "severity": "medium"},
            {"name": "API Response Time Baseline", "category": "baseline", "severity": "high"},
            {"name": "Database Performance Baseline", "category": "baseline", "severity": "high"},
            {"name": "Frontend Loading Baseline", "category": "baseline", "severity": "medium"},
            {"name": "System Resource Baseline", "category": "baseline", "severity": "medium"},
            {"name": "System Throughput Baseline", "category": "baseline", "severity": "high"}
        ]
        
        # Filter checks if requested
        filtered_checks = checks
        if args.category:
            filtered_checks = [c for c in filtered_checks if c["category"] == args.category]
        if args.severity:
            filtered_checks = [c for c in filtered_checks if c["severity"] == args.severity]
        
        # Group by category
        categories = {}
        for check in filtered_checks:
            category = check["category"]
            if category not in categories:
                categories[category] = []
            categories[category].append(check)
        
        # Display checks
        for category, category_checks in categories.items():
            print(f"\n📂 {category.upper()}")
            for check in category_checks:
                severity_icon = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}.get(check["severity"], "⚪")
                print(f"   {severity_icon} {check['name']} ({check['severity']})")
        
        print(f"\nTotal checks: {len(filtered_checks)}")
    
    def _load_json_file(self, file_path: str) -> Dict[str, Any]:
        """Load JSON configuration file"""
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            raise Exception(f"Configuration file not found: {file_path}")
        except json.JSONDecodeError as e:
            raise Exception(f"Invalid JSON in {file_path}: {str(e)}")
    
    def _display_validation_results(self, report, duration: float, verbose: bool):
        """Display validation results"""
        print(f"\n📊 Validation Results (completed in {duration:.1f}s)")
        print("=" * 60)
        
        # Overall status
        status_icon = "✅" if report.production_ready else "❌"
        status_text = "READY FOR PRODUCTION" if report.production_ready else "NOT READY FOR PRODUCTION"
        print(f"{status_icon} {status_text}")
        
        # Summary statistics
        summary = report.summary
        print(f"\n📈 Summary:")
        print(f"   Total checks: {summary.get('total_checks', 0)}")
        print(f"   Passed: {summary.get('passed_checks', 0)}")
        print(f"   Failed: {summary.get('failed_checks', 0)}")
        print(f"   Warnings: {summary.get('warning_checks', 0)}")
        print(f"   Critical failures: {summary.get('critical_failures', 0)}")
        print(f"   Success rate: {summary.get('success_rate', 0):.1f}%")
        
        # Failed checks
        failed_checks = [c for c in report.check_results if c["status"] == "failed"]
        if failed_checks:
            print(f"\n❌ Failed Checks:")
            for check in failed_checks:
                severity_icon = {"critical": "🔴", "high": "🟠", "medium": "🟡"}.get(check["severity"], "⚪")
                print(f"   {severity_icon} {check['name']}")
                if verbose and check.get("error_message"):
                    print(f"      Error: {check['error_message']}")
        
        # Warning checks
        warning_checks = [c for c in report.check_results if c["status"] == "warning"]
        if warning_checks:
            print(f"\n⚠️  Warning Checks:")
            for check in warning_checks:
                print(f"   🟡 {check['name']}")
                if verbose and check.get("error_message"):
                    print(f"      Warning: {check['error_message']}")
        
        # Recommendations
        if report.recommendations:
            print(f"\n💡 Recommendations:")
            for i, rec in enumerate(report.recommendations, 1):
                print(f"   {i}. {rec}")
        
        # Next steps
        if report.next_steps:
            print(f"\n🔧 Next Steps:")
            for step in report.next_steps:
                print(f"   {step}")
    
    def _save_report(self, report, output_file: str):
        """Save validation report to file"""
        # Convert report to dictionary for JSON serialization
        report_dict = {
            "suite_id": report.suite_id,
            "environment": report.environment,
            "version": report.version,
            "generated_at": report.generated_at.isoformat(),
            "summary": report.summary,
            "check_results": report.check_results,
            "recommendations": report.recommendations,
            "production_ready": report.production_ready,
            "next_steps": report.next_steps
        }
        
        with open(output_file, 'w') as f:
            json.dump(report_dict, f, indent=2)


def main():
    """Main entry point"""
    cli = ProductionReadinessCLI()
    asyncio.run(cli.run())


if __name__ == "__main__":
    main()