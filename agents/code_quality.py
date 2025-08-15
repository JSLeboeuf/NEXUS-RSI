"""
NEXUS-RSI Code Quality Analyzer Agent
Advanced code quality, maintainability, and technical debt analysis
"""

import json
import sqlite3
import subprocess
import ast
import os
import sys
import time
import math
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from collections import defaultdict
import logging

try:
    import radon.complexity as radon_complexity
    import radon.raw as radon_raw
    import radon.metrics as radon_metrics
    RADON_AVAILABLE = True
except ImportError:
    RADON_AVAILABLE = False

@dataclass
class QualityMetrics:
    """Code quality metrics for a module/file"""
    file_path: str
    lines_of_code: int
    cyclomatic_complexity: float
    cognitive_complexity: float
    maintainability_index: float
    test_coverage: float
    code_duplication: float
    technical_debt_ratio: float
    quality_score: float
    timestamp: datetime
    issues: List[Dict] = None
    
    def __post_init__(self):
        if self.issues is None:
            self.issues = []

@dataclass 
class RefactoringRecommendation:
    """Refactoring recommendation"""
    file_path: str
    recommendation_type: str
    description: str
    priority: str  # 'low', 'medium', 'high', 'critical'
    estimated_effort: int  # hours
    impact_score: float
    code_snippet: str
    suggested_fix: str
    timestamp: datetime

class CodeQualityAnalyzer:
    """Advanced code quality analyzer for NEXUS-RSI"""
    
    def __init__(self, config_path: str = None):
        self.config = self._load_config(config_path)
        self.db_path = "nexus_metrics.db"
        self.logger = self._setup_logging()
        self.quality_cache = {}
        self.analysis_start_time = None
        
        # Initialize database
        self._init_database()
        
        # Quality thresholds from config
        self.thresholds = self.config['triggers']['quality_thresholds']
        
    def _load_config(self, config_path: str = None) -> Dict:
        """Load configuration from JSON file"""
        if config_path is None:
            config_path = Path(__file__).parent / "code_quality.json"
        
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            self.logger.warning(f"Config file not found: {config_path}. Using defaults.")
            return self._default_config()
    
    def _default_config(self) -> Dict:
        """Default configuration"""
        return {
            'triggers': {
                'quality_thresholds': {
                    'code_quality_score': 0.7,
                    'maintainability_index': 0.7,
                    'complexity_threshold': 10,
                    'duplication_threshold': 10,
                    'test_coverage_threshold': 80,
                    'technical_debt_ratio': 0.05
                }
            },
            'configuration': {
                'quality_settings': {
                    'analysis_scope': ['src', 'lib', 'modules', 'agents'],
                    'exclude_patterns': ['tests', 'migrations', 'vendor', '__pycache__'],
                    'file_extensions': ['.py'],
                    'max_file_size_mb': 10
                }
            }
        }
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        return logging.getLogger('CodeQualityAnalyzer')
    
    def _init_database(self):
        """Initialize SQLite database for quality metrics"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS code_quality_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_path TEXT NOT NULL,
                    lines_of_code INTEGER,
                    cyclomatic_complexity REAL,
                    cognitive_complexity REAL,
                    maintainability_index REAL,
                    test_coverage REAL,
                    code_duplication REAL,
                    technical_debt_ratio REAL,
                    quality_score REAL,
                    timestamp TEXT,
                    issues TEXT,
                    UNIQUE(file_path, timestamp)
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS refactoring_recommendations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_path TEXT NOT NULL,
                    recommendation_type TEXT,
                    description TEXT,
                    priority TEXT,
                    estimated_effort INTEGER,
                    impact_score REAL,
                    code_snippet TEXT,
                    suggested_fix TEXT,
                    timestamp TEXT,
                    status TEXT DEFAULT 'open'
                )
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_quality_file_time 
                ON code_quality_metrics(file_path, timestamp)
            """)
    
    def analyze_file(self, file_path: str) -> QualityMetrics:
        """Analyze a single Python file for quality metrics"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse AST
            try:
                tree = ast.parse(content)
            except SyntaxError as e:
                self.logger.error(f"Syntax error in {file_path}: {e}")
                return self._create_error_metrics(file_path, "syntax_error")
            
            # Calculate metrics
            loc = self._calculate_lines_of_code(content)
            cyclomatic = self._calculate_cyclomatic_complexity(content, file_path)
            cognitive = self._calculate_cognitive_complexity(tree)
            maintainability = self._calculate_maintainability_index(content, file_path)
            coverage = self._estimate_test_coverage(file_path)
            duplication = self._detect_code_duplication(content, file_path)
            debt_ratio = self._calculate_technical_debt_ratio(file_path)
            
            # Calculate overall quality score
            quality_score = self._calculate_quality_score(
                cyclomatic, cognitive, maintainability, coverage, duplication, debt_ratio
            )
            
            # Detect issues
            issues = self._detect_quality_issues(
                file_path, cyclomatic, cognitive, maintainability, coverage, duplication, debt_ratio
            )
            
            return QualityMetrics(
                file_path=file_path,
                lines_of_code=loc,
                cyclomatic_complexity=cyclomatic,
                cognitive_complexity=cognitive,
                maintainability_index=maintainability,
                test_coverage=coverage,
                code_duplication=duplication,
                technical_debt_ratio=debt_ratio,
                quality_score=quality_score,
                timestamp=datetime.now(),
                issues=issues
            )
            
        except Exception as e:
            self.logger.error(f"Error analyzing {file_path}: {e}")
            return self._create_error_metrics(file_path, "analysis_error")
    
    def _calculate_lines_of_code(self, content: str) -> int:
        """Calculate lines of code (excluding comments and blank lines)"""
        lines = content.split('\n')
        loc = 0
        
        for line in lines:
            stripped = line.strip()
            if stripped and not stripped.startswith('#'):
                loc += 1
        
        return loc
    
    def _calculate_cyclomatic_complexity(self, content: str, file_path: str) -> float:
        """Calculate cyclomatic complexity using radon or fallback method"""
        if RADON_AVAILABLE:
            try:
                results = radon_complexity.cc_visit(content)
                if results:
                    total_complexity = sum(result.complexity for result in results)
                    return total_complexity / len(results) if results else 1.0
            except Exception as e:
                self.logger.warning(f"Radon complexity analysis failed for {file_path}: {e}")
        
        # Fallback: simple complexity calculation
        return self._simple_cyclomatic_complexity(content)
    
    def _simple_cyclomatic_complexity(self, content: str) -> float:
        """Simple cyclomatic complexity calculation"""
        complexity_keywords = [
            'if', 'elif', 'while', 'for', 'try', 'except', 'finally',
            'with', 'assert', 'and', 'or'
        ]
        
        lines = content.split('\n')
        complexity = 1  # Base complexity
        
        for line in lines:
            for keyword in complexity_keywords:
                if f' {keyword} ' in line or line.strip().startswith(keyword):
                    complexity += 1
        
        return float(complexity)
    
    def _calculate_cognitive_complexity(self, tree: ast.AST) -> float:
        """Calculate cognitive complexity"""
        class CognitiveComplexityVisitor(ast.NodeVisitor):
            def __init__(self):
                self.complexity = 0
                self.nesting_level = 0
            
            def visit_If(self, node):
                self.complexity += 1 + self.nesting_level
                self.nesting_level += 1
                self.generic_visit(node)
                self.nesting_level -= 1
            
            def visit_While(self, node):
                self.complexity += 1 + self.nesting_level
                self.nesting_level += 1
                self.generic_visit(node)
                self.nesting_level -= 1
            
            def visit_For(self, node):
                self.complexity += 1 + self.nesting_level
                self.nesting_level += 1
                self.generic_visit(node)
                self.nesting_level -= 1
            
            def visit_Try(self, node):
                self.complexity += 1 + self.nesting_level
                self.nesting_level += 1
                self.generic_visit(node)
                self.nesting_level -= 1
            
            def visit_BoolOp(self, node):
                self.complexity += len(node.values) - 1
                self.generic_visit(node)
        
        visitor = CognitiveComplexityVisitor()
        visitor.visit(tree)
        return float(visitor.complexity)
    
    def _calculate_maintainability_index(self, content: str, file_path: str) -> float:
        """Calculate maintainability index (0-1 scale)"""
        if RADON_AVAILABLE:
            try:
                mi = radon_metrics.mi_visit(content, multi=True)
                if mi:
                    # Convert from 0-171 scale to 0-1 scale
                    return max(0.0, min(1.0, mi / 171.0))
            except Exception as e:
                self.logger.warning(f"Radon MI calculation failed for {file_path}: {e}")
        
        # Fallback: simple maintainability calculation
        loc = self._calculate_lines_of_code(content)
        complexity = self._simple_cyclomatic_complexity(content)
        
        # Simple heuristic: penalize long files and high complexity
        if loc == 0:
            return 1.0
        
        complexity_penalty = min(complexity / 20.0, 1.0)
        length_penalty = min(loc / 1000.0, 1.0)
        
        return max(0.0, 1.0 - (complexity_penalty + length_penalty) / 2.0)
    
    def _estimate_test_coverage(self, file_path: str) -> float:
        """Estimate test coverage (placeholder - would integrate with coverage.py)"""
        # This is a placeholder - in a real implementation, you would:
        # 1. Run coverage.py
        # 2. Parse coverage reports
        # 3. Extract coverage for specific file
        
        # For now, return a mock value based on file characteristics
        if 'test' in file_path.lower():
            return 95.0  # Test files have high "coverage"
        
        # Check if corresponding test file exists
        test_patterns = [
            file_path.replace('.py', '_test.py'),
            file_path.replace('.py', '.test.py'),
            f"test_{Path(file_path).name}",
            f"tests/test_{Path(file_path).name}"
        ]
        
        for pattern in test_patterns:
            if Path(pattern).exists():
                return 75.0  # Assume decent coverage if test file exists
        
        return 45.0  # Default low coverage
    
    def _detect_code_duplication(self, content: str, file_path: str) -> float:
        """Detect code duplication percentage"""
        lines = [line.strip() for line in content.split('\n') 
                if line.strip() and not line.strip().startswith('#')]
        
        if len(lines) < 10:
            return 0.0
        
        # Simple duplicate detection
        line_counts = defaultdict(int)
        for line in lines:
            if len(line) > 10:  # Ignore very short lines
                line_counts[line] += 1
        
        duplicate_lines = sum(count - 1 for count in line_counts.values() if count > 1)
        duplication_percentage = (duplicate_lines / len(lines)) * 100
        
        return min(duplication_percentage, 100.0)
    
    def _calculate_technical_debt_ratio(self, file_path: str) -> float:
        """Calculate technical debt ratio"""
        # This would integrate with tools like SonarQube in production
        # For now, use heuristics based on code patterns
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except:
            return 0.0
        
        debt_indicators = [
            'TODO', 'FIXME', 'HACK', 'BUG', 'XXX',
            'temporary', 'quick fix', 'workaround'
        ]
        
        lines = content.split('\n')
        debt_lines = 0
        
        for line in lines:
            line_lower = line.lower()
            for indicator in debt_indicators:
                if indicator.lower() in line_lower:
                    debt_lines += 1
                    break
        
        if len(lines) == 0:
            return 0.0
        
        return min((debt_lines / len(lines)) * 100, 100.0) / 100.0
    
    def _calculate_quality_score(self, cyclomatic: float, cognitive: float, 
                                maintainability: float, coverage: float, 
                                duplication: float, debt_ratio: float) -> float:
        """Calculate overall quality score (0-1)"""
        # Normalize metrics to 0-1 scale
        complexity_score = max(0.0, 1.0 - min(cyclomatic / 20.0, 1.0))
        cognitive_score = max(0.0, 1.0 - min(cognitive / 30.0, 1.0))
        coverage_score = coverage / 100.0
        duplication_score = max(0.0, 1.0 - min(duplication / 50.0, 1.0))
        debt_score = max(0.0, 1.0 - debt_ratio)
        
        # Weighted average
        weights = {
            'complexity': 0.25,
            'cognitive': 0.20,
            'maintainability': 0.20,
            'coverage': 0.20,
            'duplication': 0.10,
            'debt': 0.05
        }
        
        quality_score = (
            complexity_score * weights['complexity'] +
            cognitive_score * weights['cognitive'] +
            maintainability * weights['maintainability'] +
            coverage_score * weights['coverage'] +
            duplication_score * weights['duplication'] +
            debt_score * weights['debt']
        )
        
        return max(0.0, min(1.0, quality_score))
    
    def _detect_quality_issues(self, file_path: str, cyclomatic: float, 
                              cognitive: float, maintainability: float, 
                              coverage: float, duplication: float, 
                              debt_ratio: float) -> List[Dict]:
        """Detect quality issues based on thresholds"""
        issues = []
        
        if cyclomatic > self.thresholds['complexity_threshold']:
            issues.append({
                'type': 'high_complexity',
                'severity': 'warning' if cyclomatic < 15 else 'error',
                'message': f'Cyclomatic complexity ({cyclomatic:.1f}) exceeds threshold',
                'metric': 'cyclomatic_complexity',
                'value': cyclomatic,
                'threshold': self.thresholds['complexity_threshold']
            })
        
        if cognitive > 15:  # Cognitive complexity threshold
            issues.append({
                'type': 'high_cognitive_complexity',
                'severity': 'warning' if cognitive < 25 else 'error',
                'message': f'Cognitive complexity ({cognitive:.1f}) is too high',
                'metric': 'cognitive_complexity',
                'value': cognitive,
                'threshold': 15
            })
        
        if maintainability < self.thresholds['maintainability_index']:
            issues.append({
                'type': 'low_maintainability',
                'severity': 'warning',
                'message': f'Maintainability index ({maintainability:.2f}) is below threshold',
                'metric': 'maintainability_index',
                'value': maintainability,
                'threshold': self.thresholds['maintainability_index']
            })
        
        if coverage < self.thresholds['test_coverage_threshold']:
            issues.append({
                'type': 'low_coverage',
                'severity': 'warning' if coverage > 50 else 'error',
                'message': f'Test coverage ({coverage:.1f}%) is below threshold',
                'metric': 'test_coverage',
                'value': coverage,
                'threshold': self.thresholds['test_coverage_threshold']
            })
        
        if duplication > self.thresholds['duplication_threshold']:
            issues.append({
                'type': 'high_duplication',
                'severity': 'warning',
                'message': f'Code duplication ({duplication:.1f}%) exceeds threshold',
                'metric': 'code_duplication',
                'value': duplication,
                'threshold': self.thresholds['duplication_threshold']
            })
        
        if debt_ratio > self.thresholds['technical_debt_ratio']:
            issues.append({
                'type': 'high_technical_debt',
                'severity': 'warning',
                'message': f'Technical debt ratio ({debt_ratio:.2f}) is too high',
                'metric': 'technical_debt_ratio',
                'value': debt_ratio,
                'threshold': self.thresholds['technical_debt_ratio']
            })
        
        return issues
    
    def _create_error_metrics(self, file_path: str, error_type: str) -> QualityMetrics:
        """Create error metrics for failed analysis"""
        return QualityMetrics(
            file_path=file_path,
            lines_of_code=0,
            cyclomatic_complexity=0.0,
            cognitive_complexity=0.0,
            maintainability_index=0.0,
            test_coverage=0.0,
            code_duplication=0.0,
            technical_debt_ratio=1.0,
            quality_score=0.0,
            timestamp=datetime.now(),
            issues=[{
                'type': error_type,
                'severity': 'error',
                'message': f'Failed to analyze file: {error_type}',
                'metric': 'analysis',
                'value': 0,
                'threshold': 0
            }]
        )
    
    def analyze_project(self, project_path: str = None) -> Dict[str, QualityMetrics]:
        """Analyze all Python files in the project"""
        if project_path is None:
            project_path = Path.cwd()
        else:
            project_path = Path(project_path)
        
        self.analysis_start_time = time.time()
        self.logger.info(f"Starting code quality analysis for: {project_path}")
        
        # Find Python files
        python_files = self._find_python_files(project_path)
        self.logger.info(f"Found {len(python_files)} Python files to analyze")
        
        # Analyze each file
        results = {}
        for i, file_path in enumerate(python_files, 1):
            self.logger.info(f"Analyzing {i}/{len(python_files)}: {file_path}")
            
            try:
                metrics = self.analyze_file(str(file_path))
                results[str(file_path)] = metrics
                
                # Store in database
                self._store_metrics(metrics)
                
            except Exception as e:
                self.logger.error(f"Failed to analyze {file_path}: {e}")
                results[str(file_path)] = self._create_error_metrics(str(file_path), "analysis_error")
        
        analysis_time = time.time() - self.analysis_start_time
        self.logger.info(f"Analysis completed in {analysis_time:.2f} seconds")
        
        return results
    
    def _find_python_files(self, project_path: Path) -> List[Path]:
        """Find all Python files in the project"""
        python_files = []
        scope = self.config['configuration']['quality_settings']['analysis_scope']
        exclude_patterns = self.config['configuration']['quality_settings']['exclude_patterns']
        
        for root, dirs, files in os.walk(project_path):
            # Filter directories based on scope and exclude patterns
            dirs[:] = [d for d in dirs if not any(pattern in d for pattern in exclude_patterns)]
            
            for file in files:
                if file.endswith('.py'):
                    file_path = Path(root) / file
                    
                    # Check if file should be excluded
                    if any(pattern in str(file_path) for pattern in exclude_patterns):
                        continue
                    
                    # Check file size
                    try:
                        size_mb = file_path.stat().st_size / (1024 * 1024)
                        max_size = self.config['configuration']['quality_settings']['max_file_size_mb']
                        if size_mb > max_size:
                            continue
                    except:
                        continue
                    
                    python_files.append(file_path)
        
        return python_files
    
    def _store_metrics(self, metrics: QualityMetrics):
        """Store metrics in database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO code_quality_metrics
                (file_path, lines_of_code, cyclomatic_complexity, cognitive_complexity,
                 maintainability_index, test_coverage, code_duplication, 
                 technical_debt_ratio, quality_score, timestamp, issues)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                metrics.file_path,
                metrics.lines_of_code,
                metrics.cyclomatic_complexity,
                metrics.cognitive_complexity,
                metrics.maintainability_index,
                metrics.test_coverage,
                metrics.code_duplication,
                metrics.technical_debt_ratio,
                metrics.quality_score,
                metrics.timestamp.isoformat(),
                json.dumps(metrics.issues)
            ))
    
    def generate_refactoring_recommendations(self, metrics: Dict[str, QualityMetrics]) -> List[RefactoringRecommendation]:
        """Generate refactoring recommendations based on metrics"""
        recommendations = []
        
        for file_path, metric in metrics.items():
            # High complexity recommendations
            if metric.cyclomatic_complexity > 15:
                recommendations.append(RefactoringRecommendation(
                    file_path=file_path,
                    recommendation_type="extract_method",
                    description=f"Extract methods to reduce cyclomatic complexity from {metric.cyclomatic_complexity:.1f}",
                    priority="high" if metric.cyclomatic_complexity > 20 else "medium",
                    estimated_effort=4,
                    impact_score=0.8,
                    code_snippet="",
                    suggested_fix="Break down large functions into smaller, focused methods",
                    timestamp=datetime.now()
                ))
            
            # Low maintainability recommendations
            if metric.maintainability_index < 0.5:
                recommendations.append(RefactoringRecommendation(
                    file_path=file_path,
                    recommendation_type="improve_maintainability",
                    description=f"Improve maintainability index from {metric.maintainability_index:.2f}",
                    priority="medium",
                    estimated_effort=6,
                    impact_score=0.7,
                    code_snippet="",
                    suggested_fix="Add documentation, reduce complexity, improve naming",
                    timestamp=datetime.now()
                ))
            
            # High duplication recommendations
            if metric.code_duplication > 20:
                recommendations.append(RefactoringRecommendation(
                    file_path=file_path,
                    recommendation_type="eliminate_duplication",
                    description=f"Eliminate code duplication ({metric.code_duplication:.1f}%)",
                    priority="medium",
                    estimated_effort=3,
                    impact_score=0.6,
                    code_snippet="",
                    suggested_fix="Extract common code into reusable functions or classes",
                    timestamp=datetime.now()
                ))
            
            # Low coverage recommendations
            if metric.test_coverage < 60:
                recommendations.append(RefactoringRecommendation(
                    file_path=file_path,
                    recommendation_type="increase_test_coverage",
                    description=f"Increase test coverage from {metric.test_coverage:.1f}%",
                    priority="high" if metric.test_coverage < 40 else "medium",
                    estimated_effort=8,
                    impact_score=0.9,
                    code_snippet="",
                    suggested_fix="Add unit tests for uncovered code paths",
                    timestamp=datetime.now()
                ))
        
        # Store recommendations in database
        for rec in recommendations:
            self._store_recommendation(rec)
        
        return recommendations
    
    def _store_recommendation(self, recommendation: RefactoringRecommendation):
        """Store refactoring recommendation in database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO refactoring_recommendations
                (file_path, recommendation_type, description, priority, 
                 estimated_effort, impact_score, code_snippet, suggested_fix, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                recommendation.file_path,
                recommendation.recommendation_type,
                recommendation.description,
                recommendation.priority,
                recommendation.estimated_effort,
                recommendation.impact_score,
                recommendation.code_snippet,
                recommendation.suggested_fix,
                recommendation.timestamp.isoformat()
            ))
    
    def generate_report(self, metrics: Dict[str, QualityMetrics], 
                       recommendations: List[RefactoringRecommendation]) -> Dict:
        """Generate comprehensive quality report"""
        total_files = len(metrics)
        total_loc = sum(m.lines_of_code for m in metrics.values())
        avg_quality = sum(m.quality_score for m in metrics.values()) / total_files if total_files > 0 else 0
        avg_complexity = sum(m.cyclomatic_complexity for m in metrics.values()) / total_files if total_files > 0 else 0
        avg_coverage = sum(m.test_coverage for m in metrics.values()) / total_files if total_files > 0 else 0
        
        # Count issues by severity
        issue_counts = defaultdict(int)
        for metric in metrics.values():
            for issue in metric.issues:
                issue_counts[issue['severity']] += 1
        
        # Quality distribution
        quality_distribution = {
            'excellent': len([m for m in metrics.values() if m.quality_score >= 0.9]),
            'good': len([m for m in metrics.values() if 0.7 <= m.quality_score < 0.9]),
            'fair': len([m for m in metrics.values() if 0.5 <= m.quality_score < 0.7]),
            'poor': len([m for m in metrics.values() if m.quality_score < 0.5])
        }
        
        report = {
            'summary': {
                'timestamp': datetime.now().isoformat(),
                'total_files': total_files,
                'total_lines_of_code': total_loc,
                'average_quality_score': avg_quality,
                'average_complexity': avg_complexity,
                'average_test_coverage': avg_coverage,
                'analysis_time_seconds': time.time() - self.analysis_start_time if self.analysis_start_time else 0
            },
            'quality_distribution': quality_distribution,
            'issue_summary': dict(issue_counts),
            'recommendations_summary': {
                'total': len(recommendations),
                'high_priority': len([r for r in recommendations if r.priority == 'high']),
                'medium_priority': len([r for r in recommendations if r.priority == 'medium']),
                'low_priority': len([r for r in recommendations if r.priority == 'low'])
            },
            'top_issues': self._get_top_issues(metrics),
            'improvement_opportunities': self._get_improvement_opportunities(metrics),
            'quality_trends': self._get_quality_trends()
        }
        
        return report
    
    def _get_top_issues(self, metrics: Dict[str, QualityMetrics]) -> List[Dict]:
        """Get top quality issues across the project"""
        all_issues = []
        
        for file_path, metric in metrics.items():
            for issue in metric.issues:
                all_issues.append({
                    'file': file_path,
                    'type': issue['type'],
                    'severity': issue['severity'],
                    'message': issue['message'],
                    'value': issue.get('value', 0)
                })
        
        # Sort by severity and value
        severity_order = {'error': 3, 'warning': 2, 'info': 1}
        all_issues.sort(key=lambda x: (severity_order.get(x['severity'], 0), x['value']), reverse=True)
        
        return all_issues[:10]  # Top 10 issues
    
    def _get_improvement_opportunities(self, metrics: Dict[str, QualityMetrics]) -> List[Dict]:
        """Get improvement opportunities ranked by impact"""
        opportunities = []
        
        for file_path, metric in metrics.items():
            # Low quality score opportunity
            if metric.quality_score < 0.7:
                opportunities.append({
                    'file': file_path,
                    'type': 'overall_quality',
                    'current_score': metric.quality_score,
                    'potential_improvement': min(0.9 - metric.quality_score, 0.3),
                    'effort': 'medium'
                })
            
            # High complexity opportunity
            if metric.cyclomatic_complexity > 10:
                opportunities.append({
                    'file': file_path,
                    'type': 'complexity_reduction',
                    'current_complexity': metric.cyclomatic_complexity,
                    'potential_improvement': (metric.cyclomatic_complexity - 10) / metric.cyclomatic_complexity,
                    'effort': 'high'
                })
            
            # Low coverage opportunity
            if metric.test_coverage < 80:
                opportunities.append({
                    'file': file_path,
                    'type': 'test_coverage',
                    'current_coverage': metric.test_coverage,
                    'potential_improvement': min(90 - metric.test_coverage, 40),
                    'effort': 'medium'
                })
        
        # Sort by potential improvement
        opportunities.sort(key=lambda x: x['potential_improvement'], reverse=True)
        
        return opportunities[:5]  # Top 5 opportunities
    
    def _get_quality_trends(self) -> Dict:
        """Get quality trends from historical data"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT DATE(timestamp) as date, 
                       AVG(quality_score) as avg_quality,
                       AVG(cyclomatic_complexity) as avg_complexity,
                       AVG(test_coverage) as avg_coverage
                FROM code_quality_metrics
                WHERE timestamp >= date('now', '-30 days')
                GROUP BY DATE(timestamp)
                ORDER BY date
            """)
            
            trends = cursor.fetchall()
            
            if not trends:
                return {'message': 'No historical data available'}
            
            return {
                'period_days': 30,
                'data_points': len(trends),
                'quality_trend': 'improving' if trends[-1][1] > trends[0][1] else 'declining',
                'complexity_trend': 'improving' if trends[-1][2] < trends[0][2] else 'declining',
                'coverage_trend': 'improving' if trends[-1][3] > trends[0][3] else 'declining'
            }
    
    def run_continuous_analysis(self, project_path: str = None, interval_seconds: int = 300):
        """Run continuous quality analysis"""
        self.logger.info("Starting continuous code quality analysis")
        
        while True:
            try:
                self.logger.info("Running quality analysis cycle")
                
                # Analyze project
                metrics = self.analyze_project(project_path)
                
                # Generate recommendations
                recommendations = self.generate_refactoring_recommendations(metrics)
                
                # Generate report
                report = self.generate_report(metrics, recommendations)
                
                # Check for quality alerts
                self._check_quality_alerts(metrics, report)
                
                # Save report
                self._save_report(report)
                
                self.logger.info(f"Analysis cycle completed. Sleeping for {interval_seconds} seconds")
                time.sleep(interval_seconds)
                
            except KeyboardInterrupt:
                self.logger.info("Continuous analysis stopped by user")
                break
            except Exception as e:
                self.logger.error(f"Error in continuous analysis: {e}")
                time.sleep(interval_seconds)
    
    def _check_quality_alerts(self, metrics: Dict[str, QualityMetrics], report: Dict):
        """Check for quality alerts and trigger notifications"""
        alerts = []
        
        # Check overall quality degradation
        avg_quality = report['summary']['average_quality_score']
        if avg_quality < self.thresholds['code_quality_score']:
            alerts.append({
                'type': 'quality_degradation',
                'severity': 'warning',
                'message': f'Average quality score ({avg_quality:.2f}) below threshold',
                'threshold': self.thresholds['code_quality_score']
            })
        
        # Check for files with critical issues
        critical_files = [
            file_path for file_path, metric in metrics.items()
            if any(issue['severity'] == 'error' for issue in metric.issues)
        ]
        
        if critical_files:
            alerts.append({
                'type': 'critical_issues',
                'severity': 'error',
                'message': f'{len(critical_files)} files have critical quality issues',
                'files': critical_files[:5]  # Top 5
            })
        
        if alerts:
            self.logger.warning(f"Quality alerts triggered: {len(alerts)} alerts")
            # Here you could integrate with notification systems
            
    def _save_report(self, report: Dict):
        """Save quality report to file"""
        reports_dir = Path("quality_reports")
        reports_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = reports_dir / f"quality_report_{timestamp}.json"
        
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        self.logger.info(f"Quality report saved to: {report_path}")


def main():
    """Main entry point for code quality analyzer"""
    import argparse
    
    parser = argparse.ArgumentParser(description="NEXUS-RSI Code Quality Analyzer")
    parser.add_argument("--project", default=".", help="Project path to analyze")
    parser.add_argument("--config", help="Configuration file path")
    parser.add_argument("--continuous", action="store_true", help="Run continuous analysis")
    parser.add_argument("--interval", type=int, default=300, help="Analysis interval in seconds")
    
    args = parser.parse_args()
    
    # Create analyzer
    analyzer = CodeQualityAnalyzer(config_path=args.config)
    
    if args.continuous:
        analyzer.run_continuous_analysis(args.project, args.interval)
    else:
        # Single analysis run
        print("🔍 Starting code quality analysis...")
        
        # Analyze project
        metrics = analyzer.analyze_project(args.project)
        
        # Generate recommendations
        recommendations = analyzer.generate_refactoring_recommendations(metrics)
        
        # Generate report
        report = analyzer.generate_report(metrics, recommendations)
        
        # Save report
        analyzer._save_report(report)
        
        # Print summary
        print(f"✅ Analysis complete!")
        print(f"📊 Analyzed {report['summary']['total_files']} files")
        print(f"📈 Average quality score: {report['summary']['average_quality_score']:.2f}")
        print(f"🎯 Generated {len(recommendations)} recommendations")
        
        if report['issue_summary']:
            print(f"⚠️  Issues found: {sum(report['issue_summary'].values())}")


if __name__ == "__main__":
    main()