"""
Automated code quality analysis system
"""
import os
import ast
import subprocess
import json
from typing import List, Dict, Any
from pathlib import Path
import radon.complexity as radon_cc
import radon.metrics as radon_metrics
from .models import CodeQualityMetric, Improvement, ImprovementPriority, ImprovementCategory


class CodeQualityAnalyzer:
    """Analyzes code quality and suggests improvements"""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.quality_gates = {
            'complexity': 10,
            'maintainability': 20,
            'coverage': 80,
            'duplicated_lines': 5,
            'technical_debt_ratio': 5
        }
    
    async def analyze_project(self) -> List[CodeQualityMetric]:
        """Analyze entire project for code quality metrics"""
        metrics = []
        
        # Analyze Python files
        python_files = list(self.project_root.rglob("*.py"))
        for file_path in python_files:
            if self._should_analyze_file(file_path):
                metric = await self._analyze_python_file(file_path)
                if metric:
                    metrics.append(metric)
        
        # Analyze TypeScript/JavaScript files
        ts_files = list(self.project_root.rglob("*.ts")) + list(self.project_root.rglob("*.tsx"))
        for file_path in ts_files:
            if self._should_analyze_file(file_path):
                metric = await self._analyze_typescript_file(file_path)
                if metric:
                    metrics.append(metric)
        
        return metrics
    
    def _should_analyze_file(self, file_path: Path) -> bool:
        """Determine if file should be analyzed"""
        exclude_patterns = [
            '__pycache__',
            'node_modules',
            '.git',
            'venv',
            'env',
            'build',
            'dist',
            'test_',
            '.test.',
            'spec.'
        ]
        
        file_str = str(file_path)
        return not any(pattern in file_str for pattern in exclude_patterns)
    
    async def _analyze_python_file(self, file_path: Path) -> CodeQualityMetric:
        """Analyze Python file for quality metrics"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse AST
            tree = ast.parse(content)
            
            # Calculate complexity
            complexity = self._calculate_complexity(content)
            
            # Calculate maintainability index
            maintainability = self._calculate_maintainability(content)
            
            # Get test coverage (if available)
            coverage = await self._get_test_coverage(file_path)
            
            # Count code smells
            code_smells = self._count_code_smells(tree)
            
            # Calculate duplicated lines
            duplicated_lines = await self._calculate_duplicated_lines(file_path)
            
            # Calculate technical debt ratio
            tech_debt_ratio = self._calculate_technical_debt_ratio(
                complexity, maintainability, code_smells
            )
            
            return CodeQualityMetric(
                file_path=str(file_path.relative_to(self.project_root)),
                complexity=complexity,
                maintainability_index=maintainability,
                test_coverage=coverage,
                code_smells=code_smells,
                duplicated_lines=duplicated_lines,
                technical_debt_ratio=tech_debt_ratio
            )
            
        except Exception as e:
            print(f"Error analyzing {file_path}: {e}")
            return None
    
    async def _analyze_typescript_file(self, file_path: Path) -> CodeQualityMetric:
        """Analyze TypeScript file for quality metrics"""
        try:
            # Use ESLint for TypeScript analysis
            result = await self._run_eslint(file_path)
            
            # Calculate basic metrics
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            lines = content.split('\n')
            complexity = self._estimate_ts_complexity(content)
            
            return CodeQualityMetric(
                file_path=str(file_path.relative_to(self.project_root)),
                complexity=complexity,
                maintainability_index=self._estimate_ts_maintainability(content),
                test_coverage=await self._get_ts_test_coverage(file_path),
                code_smells=result.get('code_smells', 0),
                duplicated_lines=0,  # Would need additional tooling
                technical_debt_ratio=result.get('tech_debt_ratio', 0)
            )
            
        except Exception as e:
            print(f"Error analyzing TypeScript file {file_path}: {e}")
            return None
    
    def _calculate_complexity(self, content: str) -> float:
        """Calculate cyclomatic complexity"""
        try:
            complexity_data = radon_cc.cc_visit(content)
            if not complexity_data:
                return 1.0
            
            total_complexity = sum(item.complexity for item in complexity_data)
            return total_complexity / len(complexity_data)
        except:
            return 1.0
    
    def _calculate_maintainability(self, content: str) -> float:
        """Calculate maintainability index"""
        try:
            mi = radon_metrics.mi_visit(content, multi=True)
            return mi if mi else 100.0
        except:
            return 100.0
    
    async def _get_test_coverage(self, file_path: Path) -> float:
        """Get test coverage for file"""
        try:
            # Run coverage analysis
            result = subprocess.run([
                'coverage', 'report', '--show-missing', 
                '--include', str(file_path)
            ], capture_output=True, text=True)
            
            # Parse coverage output
            lines = result.stdout.split('\n')
            for line in lines:
                if str(file_path) in line:
                    parts = line.split()
                    if len(parts) >= 4:
                        coverage_str = parts[3].replace('%', '')
                        return float(coverage_str)
            
            return 0.0
        except:
            return 0.0
    
    def _count_code_smells(self, tree: ast.AST) -> int:
        """Count code smells in AST"""
        smells = 0
        
        for node in ast.walk(tree):
            # Long parameter lists
            if isinstance(node, ast.FunctionDef) and len(node.args.args) > 5:
                smells += 1
            
            # Long methods (more than 20 lines)
            if isinstance(node, ast.FunctionDef):
                if hasattr(node, 'end_lineno') and hasattr(node, 'lineno'):
                    if node.end_lineno - node.lineno > 20:
                        smells += 1
            
            # Deeply nested code
            if isinstance(node, (ast.If, ast.For, ast.While)):
                depth = self._calculate_nesting_depth(node)
                if depth > 3:
                    smells += 1
        
        return smells
    
    def _calculate_nesting_depth(self, node: ast.AST, depth: int = 0) -> int:
        """Calculate maximum nesting depth"""
        max_depth = depth
        
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.If, ast.For, ast.While, ast.With)):
                child_depth = self._calculate_nesting_depth(child, depth + 1)
                max_depth = max(max_depth, child_depth)
        
        return max_depth
    
    async def _calculate_duplicated_lines(self, file_path: Path) -> int:
        """Calculate duplicated lines (simplified implementation)"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Simple duplicate detection
            line_counts = {}
            for line in lines:
                stripped = line.strip()
                if len(stripped) > 10:  # Ignore short lines
                    line_counts[stripped] = line_counts.get(stripped, 0) + 1
            
            duplicated = sum(count - 1 for count in line_counts.values() if count > 1)
            return duplicated
        except:
            return 0
    
    def _calculate_technical_debt_ratio(self, complexity: float, 
                                      maintainability: float, 
                                      code_smells: int) -> float:
        """Calculate technical debt ratio"""
        # Normalize metrics to 0-1 scale
        complexity_score = min(complexity / 20, 1.0)  # 20 is high complexity
        maintainability_score = max(0, (100 - maintainability) / 100)
        smells_score = min(code_smells / 10, 1.0)  # 10 smells is high
        
        # Weighted average
        debt_ratio = (complexity_score * 0.4 + 
                     maintainability_score * 0.4 + 
                     smells_score * 0.2) * 100
        
        return debt_ratio
    
    async def _run_eslint(self, file_path: Path) -> Dict[str, Any]:
        """Run ESLint analysis on TypeScript file"""
        try:
            result = subprocess.run([
                'npx', 'eslint', str(file_path), '--format', 'json'
            ], capture_output=True, text=True, cwd=self.project_root)
            
            if result.stdout:
                eslint_data = json.loads(result.stdout)
                if eslint_data and len(eslint_data) > 0:
                    file_data = eslint_data[0]
                    return {
                        'code_smells': len(file_data.get('messages', [])),
                        'tech_debt_ratio': len(file_data.get('messages', [])) * 2
                    }
            
            return {'code_smells': 0, 'tech_debt_ratio': 0}
        except:
            return {'code_smells': 0, 'tech_debt_ratio': 0}
    
    def _estimate_ts_complexity(self, content: str) -> float:
        """Estimate TypeScript complexity"""
        # Simple heuristic based on control structures
        complexity_keywords = ['if', 'else', 'for', 'while', 'switch', 'case', 'catch']
        complexity = 1  # Base complexity
        
        for keyword in complexity_keywords:
            complexity += content.count(keyword)
        
        return complexity / max(content.count('\n'), 1) * 10
    
    def _estimate_ts_maintainability(self, content: str) -> float:
        """Estimate TypeScript maintainability"""
        lines = content.split('\n')
        non_empty_lines = [line for line in lines if line.strip()]
        
        if not non_empty_lines:
            return 100.0
        
        # Simple heuristic based on line length and complexity
        avg_line_length = sum(len(line) for line in non_empty_lines) / len(non_empty_lines)
        complexity_indicators = content.count('any') + content.count('// TODO')
        
        maintainability = 100 - (avg_line_length / 2) - (complexity_indicators * 5)
        return max(0, maintainability)
    
    async def _get_ts_test_coverage(self, file_path: Path) -> float:
        """Get TypeScript test coverage"""
        try:
            # Check if there's a corresponding test file
            test_patterns = [
                file_path.with_suffix('.test.ts'),
                file_path.with_suffix('.test.tsx'),
                file_path.with_suffix('.spec.ts'),
                file_path.with_suffix('.spec.tsx')
            ]
            
            for test_file in test_patterns:
                if test_file.exists():
                    return 80.0  # Assume good coverage if test exists
            
            return 0.0
        except:
            return 0.0
    
    async def generate_improvements(self, metrics: List[CodeQualityMetric]) -> List[Improvement]:
        """Generate improvement suggestions based on metrics"""
        improvements = []
        
        for metric in metrics:
            # Check against quality gates
            if metric.complexity > self.quality_gates['complexity']:
                improvements.append(Improvement(
                    title=f"Reduce complexity in {metric.file_path}",
                    description=f"File has complexity of {metric.complexity:.1f}, exceeding threshold of {self.quality_gates['complexity']}",
                    priority=ImprovementPriority.HIGH if metric.complexity > 15 else ImprovementPriority.MEDIUM,
                    category=ImprovementCategory.CODE_QUALITY,
                    suggested_actions=[
                        "Break down large functions into smaller ones",
                        "Extract complex logic into separate methods",
                        "Reduce nesting levels using early returns",
                        "Consider using design patterns to simplify logic"
                    ],
                    estimated_effort=int(metric.complexity * 2),
                    expected_impact=0.7,
                    confidence=0.8,
                    source_data={"metric": metric.dict()}
                ))
            
            if metric.test_coverage < self.quality_gates['coverage']:
                improvements.append(Improvement(
                    title=f"Improve test coverage for {metric.file_path}",
                    description=f"File has {metric.test_coverage:.1f}% coverage, below threshold of {self.quality_gates['coverage']}%",
                    priority=ImprovementPriority.MEDIUM,
                    category=ImprovementCategory.CODE_QUALITY,
                    suggested_actions=[
                        "Add unit tests for uncovered functions",
                        "Add integration tests for complex workflows",
                        "Add edge case testing",
                        "Mock external dependencies in tests"
                    ],
                    estimated_effort=int((self.quality_gates['coverage'] - metric.test_coverage) / 10),
                    expected_impact=0.6,
                    confidence=0.9,
                    source_data={"metric": metric.dict()}
                ))
            
            if metric.technical_debt_ratio > self.quality_gates['technical_debt_ratio']:
                improvements.append(Improvement(
                    title=f"Reduce technical debt in {metric.file_path}",
                    description=f"File has technical debt ratio of {metric.technical_debt_ratio:.1f}%",
                    priority=ImprovementPriority.MEDIUM,
                    category=ImprovementCategory.CODE_QUALITY,
                    suggested_actions=[
                        "Refactor complex methods",
                        "Remove code smells",
                        "Improve code documentation",
                        "Apply consistent coding standards"
                    ],
                    estimated_effort=int(metric.technical_debt_ratio),
                    expected_impact=0.5,
                    confidence=0.7,
                    source_data={"metric": metric.dict()}
                ))
        
        return improvements