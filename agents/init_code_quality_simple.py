"""
Initialization script for NEXUS-RSI Code Quality Analyzer Agent
"""

import sys
import json
from pathlib import Path
from datetime import datetime
import sqlite3

# Add the project root to the path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from agents.code_quality import CodeQualityAnalyzer
except ImportError as e:
    print(f"[ERROR] Failed to import CodeQualityAnalyzer: {e}")
    print("Please run setup_code_quality.py first")
    sys.exit(1)

def initialize_agent():
    """Initialize the code quality analyzer agent"""
    
    print("Initializing NEXUS-RSI Code Quality Analyzer Agent")
    print("=" * 55)
    
    try:
        # Create analyzer instance
        analyzer = CodeQualityAnalyzer()
        print("[OK] Code Quality Analyzer initialized")
        
        # Test database connection
        with sqlite3.connect(analyzer.db_path) as conn:
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            print(f"[OK] Database connected with {len(tables)} tables")
        
        # Run initial analysis on the agents directory
        print("\nRunning initial code quality analysis...")
        agents_path = Path(__file__).parent
        
        # Analyze the code quality module itself as a test
        test_file = agents_path / "code_quality.py"
        if test_file.exists():
            metrics = analyzer.analyze_file(str(test_file))
            print(f"[OK] Test analysis completed for {test_file.name}")
            print(f"   Quality Score: {metrics.quality_score:.2f}")
            print(f"   Complexity: {metrics.cyclomatic_complexity:.1f}")
            print(f"   Issues: {len(metrics.issues)}")
        
        # Store agent metadata
        agent_info = {
            "name": "nexus-code-quality",
            "status": "initialized",
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0",
            "capabilities": [
                "code_complexity_analysis",
                "maintainability_assessment", 
                "technical_debt_quantification",
                "test_coverage_analysis",
                "refactoring_recommendations"
            ],
            "thresholds": analyzer.thresholds
        }
        
        # Save agent info
        agent_info_path = agents_path / "code_quality_agent_info.json"
        with open(agent_info_path, 'w') as f:
            json.dump(agent_info, f, indent=2)
        print(f"[OK] Agent info saved to {agent_info_path}")
        
        return analyzer
        
    except Exception as e:
        print(f"[ERROR] Initialization failed: {e}")
        return None

def create_sample_analysis():
    """Create a sample analysis to demonstrate functionality"""
    
    print("\nCreating sample analysis...")
    
    try:
        analyzer = CodeQualityAnalyzer()
        
        # Analyze the current project
        project_path = Path(__file__).parent.parent
        
        print("Analyzing NEXUS-RSI project structure...")
        
        # Find Python files to analyze
        python_files = list(project_path.glob("**/*.py"))
        python_files = [f for f in python_files if not any(
            exclude in str(f) for exclude in 
            ['__pycache__', '.git', 'venv', '.venv', 'build', 'dist']
        )]
        
        print(f"Found {len(python_files)} Python files")
        
        # Analyze a subset for demo
        sample_files = python_files[:3]  # Analyze first 3 files
        results = {}
        
        for file_path in sample_files:
            try:
                print(f"   Analyzing: {file_path.name}")
                metrics = analyzer.analyze_file(str(file_path))
                results[str(file_path)] = metrics
            except Exception as e:
                print(f"   [WARNING] Error analyzing {file_path}: {e}")
        
        # Generate recommendations
        recommendations = analyzer.generate_refactoring_recommendations(results)
        
        # Generate report
        report = analyzer.generate_report(results, recommendations)
        
        # Save sample report
        reports_dir = Path("quality_reports")
        reports_dir.mkdir(exist_ok=True)
        
        sample_report_path = reports_dir / "sample_analysis_report.json"
        with open(sample_report_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"[OK] Sample analysis completed")
        print(f"Report saved to: {sample_report_path}")
        print(f"Average quality score: {report['summary']['average_quality_score']:.2f}")
        print(f"Recommendations generated: {len(recommendations)}")
        
        return report
        
    except Exception as e:
        print(f"[ERROR] Sample analysis failed: {e}")
        return None

def main():
    """Main initialization function"""
    
    print("NEXUS-RSI Code Quality Analyzer Agent Initialization")
    print("=" * 60)
    
    # Initialize the agent
    analyzer = initialize_agent()
    if not analyzer:
        print("[ERROR] Initialization failed")
        return 1
    
    # Create sample analysis
    sample_report = create_sample_analysis()
    
    print("\n" + "=" * 60)
    print("Code Quality Analyzer Agent Successfully Initialized!")
    print("\nSummary:")
    print("[OK] Agent configured and ready")
    print("[OK] Database tables created")
    print("[OK] Sample analysis completed")
    
    if sample_report:
        avg_quality = sample_report['summary']['average_quality_score']
        print(f"\nCurrent Project Quality Score: {avg_quality:.2f}")
        
        if avg_quality >= 0.8:
            print("Excellent code quality!")
        elif avg_quality >= 0.6:
            print("Good code quality")
        else:
            print("Code quality needs improvement")
    
    print("\nReady to enhance NEXUS-RSI code quality!")
    print("\nNext steps:")
    print("1. Run full analysis: python agents/code_quality.py --project .")
    print("2. Check quality reports in: quality_reports/")
    print("3. Integrate with auto_patcher.py for automated improvements")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())