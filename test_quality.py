#!/usr/bin/env python3
"""
Simple test script for NEXUS-RSI Code Quality Analyzer
"""

import sys
from pathlib import Path

# Add agents to path
sys.path.insert(0, str(Path(__file__).parent / "agents"))

from code_quality import CodeQualityAnalyzer

def main():
    print("Starting NEXUS-RSI Code Quality Analysis Test")
    print("=" * 50)
    
    try:
        # Create analyzer
        analyzer = CodeQualityAnalyzer()
        print("[OK] Analyzer initialized")
        
        # Test single file analysis
        test_file = Path(__file__).parent / "agents" / "code_quality.py"
        if test_file.exists():
            print(f"Analyzing: {test_file.name}")
            metrics = analyzer.analyze_file(str(test_file))
            
            print(f"Results for {test_file.name}:")
            print(f"  Lines of Code: {metrics.lines_of_code}")
            print(f"  Quality Score: {metrics.quality_score:.2f}")
            print(f"  Complexity: {metrics.cyclomatic_complexity:.1f}")
            print(f"  Maintainability: {metrics.maintainability_index:.2f}")
            print(f"  Test Coverage: {metrics.test_coverage:.1f}%")
            print(f"  Issues Found: {len(metrics.issues)}")
            
            if metrics.issues:
                print("\nTop Issues:")
                for issue in metrics.issues[:3]:
                    print(f"  - {issue['type']}: {issue['message']}")
        
        # Test project analysis (limited scope)
        print(f"\nAnalyzing agents directory...")
        agents_path = Path(__file__).parent / "agents"
        
        python_files = list(agents_path.glob("*.py"))
        python_files = [f for f in python_files if f.name not in ['__init__.py']]
        
        results = {}
        for file_path in python_files[:3]:  # Limit to 3 files
            print(f"  Analyzing: {file_path.name}")
            try:
                metrics = analyzer.analyze_file(str(file_path))
                results[str(file_path)] = metrics
            except Exception as e:
                print(f"    Error: {e}")
        
        # Generate recommendations
        recommendations = analyzer.generate_refactoring_recommendations(results)
        
        # Generate report
        report = analyzer.generate_report(results, recommendations)
        
        print(f"\n" + "=" * 50)
        print("ANALYSIS SUMMARY")
        print("=" * 50)
        print(f"Files Analyzed: {report['summary']['total_files']}")
        print(f"Total Lines of Code: {report['summary']['total_lines_of_code']}")
        print(f"Average Quality Score: {report['summary']['average_quality_score']:.2f}")
        print(f"Average Complexity: {report['summary']['average_complexity']:.1f}")
        print(f"Recommendations: {len(recommendations)}")
        
        quality_score = report['summary']['average_quality_score']
        if quality_score >= 0.8:
            print("Quality Assessment: EXCELLENT")
        elif quality_score >= 0.6:
            print("Quality Assessment: GOOD")
        elif quality_score >= 0.4:
            print("Quality Assessment: FAIR")
        else:
            print("Quality Assessment: NEEDS IMPROVEMENT")
        
        print("\nTop Recommendations:")
        for i, rec in enumerate(recommendations[:3], 1):
            print(f"{i}. {rec.recommendation_type}: {rec.description}")
            print(f"   Priority: {rec.priority}, Effort: {rec.estimated_effort}h")
        
        print(f"\n[OK] Analysis completed successfully!")
        return 0
        
    except Exception as e:
        print(f"[ERROR] Analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())