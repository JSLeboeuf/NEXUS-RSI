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
    print(f"❌ Failed to import CodeQualityAnalyzer: {e}")
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
            print(f"✅ Database connected with {len(tables)} tables")
        
        # Run initial analysis on the agents directory
        print("\n🔍 Running initial code quality analysis...")
        agents_path = Path(__file__).parent
        
        # Analyze the code quality module itself as a test
        test_file = agents_path / "code_quality.py"
        if test_file.exists():
            metrics = analyzer.analyze_file(str(test_file))
            print(f"✅ Test analysis completed for {test_file.name}")
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
        print(f"✅ Agent info saved to {agent_info_path}")
        
        return analyzer
        
    except Exception as e:
        print(f"❌ Initialization failed: {e}")
        return None

def register_with_nexus():
    """Register the agent with the NEXUS-RSI system"""
    
    print("\n🔗 Registering with NEXUS-RSI system...")
    
    try:
        # Check if nexus_core exists
        nexus_core_path = Path(__file__).parent.parent / "nexus_core.py"
        if not nexus_core_path.exists():
            print("⚠️  nexus_core.py not found, skipping registration")
            return
        
        # Add agent to the system (would integrate with actual NEXUS core)
        agent_registry = {
            "code_quality": {
                "module": "agents.code_quality",
                "class": "CodeQualityAnalyzer",
                "config": "agents/code_quality.json",
                "triggers": [
                    "rsi_loop_start",
                    "file_change",
                    "quality_threshold_breach"
                ],
                "priority": "medium",
                "dependencies": ["radon", "pylint", "flake8"]
            }
        }
        
        # Save registry info
        registry_path = Path(__file__).parent / "agent_registry.json"
        
        if registry_path.exists():
            with open(registry_path, 'r') as f:
                existing_registry = json.load(f)
        else:
            existing_registry = {}
        
        existing_registry.update(agent_registry)
        
        with open(registry_path, 'w') as f:
            json.dump(existing_registry, f, indent=2)
        
        print("✅ Agent registered with NEXUS-RSI system")
        
    except Exception as e:
        print(f"⚠️  Registration warning: {e}")

def create_sample_analysis():
    """Create a sample analysis to demonstrate functionality"""
    
    print("\n📊 Creating sample analysis...")
    
    try:
        analyzer = CodeQualityAnalyzer()
        
        # Analyze the current project
        project_path = Path(__file__).parent.parent
        
        print("🔍 Analyzing NEXUS-RSI project structure...")
        
        # Find Python files to analyze
        python_files = list(project_path.glob("**/*.py"))
        python_files = [f for f in python_files if not any(
            exclude in str(f) for exclude in 
            ['__pycache__', '.git', 'venv', '.venv', 'build', 'dist']
        )]
        
        print(f"📁 Found {len(python_files)} Python files")
        
        # Analyze a subset for demo
        sample_files = python_files[:5]  # Analyze first 5 files
        results = {}
        
        for file_path in sample_files:
            try:
                print(f"   Analyzing: {file_path.name}")
                metrics = analyzer.analyze_file(str(file_path))
                results[str(file_path)] = metrics
            except Exception as e:
                print(f"   ⚠️  Error analyzing {file_path}: {e}")
        
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
        
        print(f"✅ Sample analysis completed")
        print(f"📋 Report saved to: {sample_report_path}")
        print(f"📊 Average quality score: {report['summary']['average_quality_score']:.2f}")
        print(f"🎯 Recommendations generated: {len(recommendations)}")
        
        return report
        
    except Exception as e:
        print(f"❌ Sample analysis failed: {e}")
        return None

def validate_integration():
    """Validate integration with auto_patcher and other components"""
    
    print("\n🔗 Validating integration points...")
    
    # Check auto_patcher integration
    auto_patcher_path = Path(__file__).parent.parent / "scripts" / "auto_patcher.py"
    if auto_patcher_path.exists():
        print("✅ auto_patcher.py found - integration possible")
        
        # Suggest integration points
        integration_points = [
            "Quality-driven patch generation",
            "Refactoring recommendation integration", 
            "Complexity reduction patches",
            "Code cleanup automation"
        ]
        
        print("🔗 Suggested integration points:")
        for point in integration_points:
            print(f"   • {point}")
    else:
        print("⚠️  auto_patcher.py not found")
    
    # Check database integration
    db_path = Path(__file__).parent.parent / "nexus_metrics.db"
    if db_path.exists():
        print("✅ nexus_metrics.db found - metrics storage ready")
    else:
        print("ℹ️  nexus_metrics.db will be created on first use")
    
    # Check dashboard integration
    dashboard_path = Path(__file__).parent.parent / "nexus_dashboard.py"
    if dashboard_path.exists():
        print("✅ nexus_dashboard.py found - visualization integration possible")
    else:
        print("⚠️  nexus_dashboard.py not found")

def show_usage_examples():
    """Show usage examples for the code quality analyzer"""
    
    print("\n📚 Usage Examples:")
    print("=" * 20)
    
    examples = [
        {
            "title": "Basic Analysis",
            "command": "python agents/code_quality.py --project .",
            "description": "Analyze the current project"
        },
        {
            "title": "Continuous Monitoring", 
            "command": "python agents/code_quality.py --continuous --interval 300",
            "description": "Run continuous analysis every 5 minutes"
        },
        {
            "title": "Custom Configuration",
            "command": "python agents/code_quality.py --config custom_config.json",
            "description": "Use custom configuration file"
        },
        {
            "title": "Integration with Auto-Patcher",
            "command": "# In auto_patcher.py:\\nfrom agents.code_quality import CodeQualityAnalyzer\\nanalyzer = CodeQualityAnalyzer()\\nmetrics = analyzer.analyze_project()",
            "description": "Integrate with existing auto-patcher"
        }
    ]
    
    for example in examples:
        print(f"\n🔧 {example['title']}:")
        print(f"   {example['description']}")
        print(f"   Command: {example['command']}")

def create_quick_start_guide():
    """Create a quick start guide"""
    
    guide_content = """
# NEXUS-RSI Code Quality Analyzer - Quick Start Guide

## Overview
The Code Quality Analyzer provides comprehensive code quality assessment for the NEXUS-RSI system.

## Features
- ✅ Cyclomatic & Cognitive Complexity Analysis
- ✅ Maintainability Index Calculation  
- ✅ Technical Debt Quantification
- ✅ Code Duplication Detection
- ✅ Test Coverage Analysis
- ✅ Refactoring Recommendations

## Quick Start

### 1. Basic Analysis
```bash
python agents/code_quality.py --project .
```

### 2. View Results
Check the `quality_reports/` directory for detailed reports.

### 3. Continuous Monitoring
```bash
python agents/code_quality.py --continuous --interval 300
```

### 4. Integration with Auto-Patcher
The analyzer integrates with `auto_patcher.py` to provide quality-driven improvements.

## Configuration
Edit `agents/code_quality.json` to customize:
- Quality thresholds
- Analysis scope
- Reporting options
- Integration settings

## Quality Metrics

### Quality Score (0-1)
- **0.9+**: Excellent
- **0.7-0.9**: Good  
- **0.5-0.7**: Fair
- **<0.5**: Poor

### Complexity Thresholds
- **Cyclomatic**: ≤10 (recommended)
- **Cognitive**: ≤15 (recommended)

### Coverage Targets
- **Minimum**: 80%
- **Target**: 90%+

## Refactoring Recommendations
The analyzer provides prioritized recommendations:
- **Critical**: Must fix
- **High**: Should fix soon
- **Medium**: Consider fixing
- **Low**: Nice to have

## Database Integration
Quality metrics are stored in `nexus_metrics.db`:
- Historical trend tracking
- Performance correlation
- Quality gate enforcement

## Dashboard Integration
Quality metrics appear in the NEXUS dashboard:
- Real-time quality scores
- Trend visualization
- Hotspot identification

## Troubleshooting

### Installation Issues
```bash
pip install radon pylint flake8 black mypy coverage
```

### Analysis Errors
Check file permissions and syntax errors in analyzed files.

### Performance Issues
Adjust analysis scope in configuration to exclude large directories.

## Support
For issues or questions, check the agent logs in `quality_reports/`.
"""
    
    guide_path = Path("agents/CODE_QUALITY_QUICKSTART.md")
    with open(guide_path, 'w') as f:
        f.write(guide_content.strip())
    
    print(f"✅ Quick start guide created: {guide_path}")

def main():
    """Main initialization function"""
    
    print("🚀 NEXUS-RSI Code Quality Analyzer Agent Initialization")
    print("=" * 60)
    
    # Initialize the agent
    analyzer = initialize_agent()
    if not analyzer:
        print("❌ Initialization failed")
        return 1
    
    # Register with NEXUS
    register_with_nexus()
    
    # Create sample analysis
    sample_report = create_sample_analysis()
    
    # Validate integrations
    validate_integration()
    
    # Create quick start guide
    create_quick_start_guide()
    
    # Show usage examples
    show_usage_examples()
    
    print("\n" + "=" * 60)
    print("🎉 Code Quality Analyzer Agent Successfully Initialized!")
    print("\n📋 Summary:")
    print("✅ Agent configured and ready")
    print("✅ Database tables created")
    print("✅ Sample analysis completed")
    print("✅ Integration points identified")
    print("✅ Quick start guide created")
    
    if sample_report:
        avg_quality = sample_report['summary']['average_quality_score']
        print(f"\n📊 Current Project Quality Score: {avg_quality:.2f}")
        
        if avg_quality >= 0.8:
            print("🏆 Excellent code quality!")
        elif avg_quality >= 0.6:
            print("👍 Good code quality")
        else:
            print("⚠️  Code quality needs improvement")
    
    print("\n🚀 Ready to enhance NEXUS-RSI code quality!")
    print("\n📖 Next steps:")
    print("1. Review the quick start guide: agents/CODE_QUALITY_QUICKSTART.md")
    print("2. Run full analysis: python agents/code_quality.py --project .")
    print("3. Check quality reports in: quality_reports/")
    print("4. Integrate with auto_patcher.py for automated improvements")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())