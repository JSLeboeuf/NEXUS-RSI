"""
Quick Setup Script for Performance Optimizer Agent
Adds the performance optimizer to existing NEXUS-RSI installation
"""

import json
import sys
from pathlib import Path
from datetime import datetime

def update_nexus_config():
    """Update NEXUS configuration to include performance optimizer"""
    config_path = Path("config/nexus_config.json")
    
    if not config_path.exists():
        print(f"❌ NEXUS config not found at {config_path}")
        return False
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        # Add performance optimizer agent configuration
        if 'agents' not in config:
            config['agents'] = {}
        
        config['agents']['performance_optimizer'] = {
            "enabled": True,
            "model": "sonnet",
            "temperature": 0.3,
            "max_tokens": 4000,
            "auto_optimization": True,
            "real_time_monitoring": True
        }
        
        # Add performance monitoring settings
        if 'performance' not in config:
            config['performance'] = {}
        
        config['performance'].update({
            "optimization_enabled": True,
            "monitoring_interval": 10,
            "deep_analysis_interval": 300,
            "report_generation_interval": 3600,
            "auto_apply_optimizations": False
        })
        
        # Add performance thresholds
        if 'thresholds' not in config:
            config['thresholds'] = {}
        
        config['thresholds'].update({
            "performance_score_threshold": 0.8,
            "response_time_threshold_ms": 500,
            "memory_threshold_percent": 80,
            "cpu_threshold_percent": 70
        })
        
        # Save updated configuration
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        print("✅ NEXUS configuration updated successfully")
        return True
    
    except Exception as e:
        print(f"❌ Failed to update NEXUS config: {e}")
        return False

def create_startup_script():
    """Create a startup script for the performance optimizer"""
    startup_script = """#!/usr/bin/env python3
\"\"\"
NEXUS-RSI with Performance Optimizer
Enhanced startup script with performance monitoring
\"\"\"

import asyncio
import sys
from pathlib import Path

# Add current directory to path
sys.path.append(str(Path(__file__).parent))

from nexus_core import NexusCore
from agents.init_performance_optimizer import PerformanceOptimizerInitializer

async def start_enhanced_nexus():
    \"\"\"Start NEXUS-RSI with performance optimization\"\"\"
    print("🚀 Starting Enhanced NEXUS-RSI with Performance Optimization...")
    
    # Initialize performance optimizer
    initializer = PerformanceOptimizerInitializer()
    
    success = await initializer.initialize_complete_system()
    
    if not success:
        print("❌ Failed to initialize performance optimizer")
        sys.exit(1)
    
    print("🎉 Enhanced NEXUS-RSI system is running!")
    print("📊 Performance optimization is active")
    print("🌐 Dashboard: http://localhost:8501")
    
    try:
        # Keep system running
        while True:
            await asyncio.sleep(60)
            
            # Display status update
            metrics = await initializer.perf_agent.get_performance_metrics()
            print(f"📈 Performance Score: {metrics['system_score']:.2f} | "
                  f"Active Monitoring: ✅ | "
                  f"Optimizations: {metrics['recommendations_count']}")
    
    except KeyboardInterrupt:
        print("\\n🛑 Shutting down Enhanced NEXUS-RSI...")
        initializer.perf_agent.optimizer.stop()
        initializer.nexus_core.stop()
        print("✅ Shutdown complete")

if __name__ == "__main__":
    asyncio.run(start_enhanced_nexus())
"""
    
    startup_file = Path("start_enhanced_nexus.py")
    
    with open(startup_file, 'w') as f:
        f.write(startup_script)
    
    print(f"✅ Enhanced startup script created: {startup_file}")
    return True

def setup_requirements():
    """Add performance optimizer requirements"""
    requirements_additions = [
        "psutil>=5.9.0",
        "aiohttp>=3.8.0",
        "memory-profiler>=0.60.0",
        "pandas>=1.5.0",
        "numpy>=1.24.0"
    ]
    
    requirements_file = Path("requirements.txt")
    
    if requirements_file.exists():
        with open(requirements_file, 'r') as f:
            existing_requirements = f.read()
        
        # Add new requirements if not already present
        new_requirements = []
        for req in requirements_additions:
            package_name = req.split('>=')[0]
            if package_name not in existing_requirements:
                new_requirements.append(req)
        
        if new_requirements:
            with open(requirements_file, 'a') as f:
                f.write('\n# Performance Optimizer Dependencies\n')
                for req in new_requirements:
                    f.write(f"{req}\n")
            
            print(f"✅ Added {len(new_requirements)} new requirements")
        else:
            print("✅ All requirements already present")
    
    else:
        print("⚠️  requirements.txt not found, creating new one")
        with open(requirements_file, 'w') as f:
            f.write("# NEXUS-RSI Requirements\n")
            for req in requirements_additions:
                f.write(f"{req}\n")
    
    return True

def create_integration_guide():
    """Create integration guide"""
    guide_content = f"""
# Performance Optimizer Agent Integration Guide

## Quick Start

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Start Enhanced NEXUS-RSI**:
   ```bash
   python start_enhanced_nexus.py
   ```

3. **Access Dashboard**:
   Open http://localhost:8501 in your browser

## Manual Integration

If you prefer to integrate manually:

```python
from agents.performance_optimizer import PerformanceOptimizerAgent

# In your existing NEXUS code:
perf_agent = PerformanceOptimizerAgent(nexus_core)
await perf_agent.initialize()
```

## Configuration

The performance optimizer is configured via:
- `agents/performance_optimizer.json` - Main agent configuration
- `config/nexus_config.json` - NEXUS integration settings

## Monitoring Features

- **Real-time Performance Monitoring**: Every 10 seconds
- **Deep Analysis**: Every 5 minutes
- **Trend Analysis**: Every hour
- **Comprehensive Reports**: Daily

## Performance Triggers

- Module score < 0.8
- Response time > 500ms
- Memory usage > 80%
- CPU usage > 70%

## Capabilities

- Python async code profiling
- SQLite query optimization
- Docker resource optimization
- Ollama LLM inference optimization
- Multi-level caching strategies
- Bottleneck detection and resolution

## Reports and Logs

Performance reports are saved to:
- `proofs/performance_reports/` - Comprehensive reports
- Standard logs via Python logging

## Integration Points

- **Database**: Connects to `nexus_metrics.db`
- **Ollama API**: Monitors at `http://localhost:11434`
- **GitHub Actions**: Workflow performance tracking
- **Auto-Patcher**: Automatic optimization application

## Troubleshooting

1. **Database Connection Issues**: Ensure `nexus_metrics.db` exists
2. **Ollama Monitoring**: Verify Ollama is running on port 11434
3. **Permission Issues**: Check file permissions for log directories
4. **Memory Issues**: Adjust monitoring intervals in configuration

## Generated: {datetime.now():%Y-%m-%d %H:%M:%S}
"""
    
    guide_file = Path("agents/PERFORMANCE_OPTIMIZER_GUIDE.md")
    
    with open(guide_file, 'w') as f:
        f.write(guide_content)
    
    print(f"✅ Integration guide created: {guide_file}")
    return True

def main():
    """Main setup function"""
    print("🔧 Setting up Performance Optimizer Agent for NEXUS-RSI")
    print("=" * 60)
    
    steps = [
        ("Updating NEXUS configuration", update_nexus_config),
        ("Adding required dependencies", setup_requirements),
        ("Creating enhanced startup script", create_startup_script),
        ("Creating integration guide", create_integration_guide)
    ]
    
    completed_steps = 0
    
    for step_name, step_function in steps:
        print(f"🔄 {step_name}...")
        try:
            if step_function():
                completed_steps += 1
                print(f"✅ {step_name} completed")
            else:
                print(f"❌ {step_name} failed")
        except Exception as e:
            print(f"❌ {step_name} failed with error: {e}")
    
    print("=" * 60)
    
    if completed_steps == len(steps):
        print("🎉 Performance Optimizer Agent setup complete!")
        print("\n📋 Next Steps:")
        print("1. Install dependencies: pip install -r requirements.txt")
        print("2. Start enhanced system: python start_enhanced_nexus.py")
        print("3. Access dashboard: http://localhost:8501")
        print("4. Review guide: agents/PERFORMANCE_OPTIMIZER_GUIDE.md")
        print("\n🌟 Your NEXUS-RSI system now has advanced performance optimization!")
    else:
        print(f"⚠️  Setup partially complete: {completed_steps}/{len(steps)} steps succeeded")
        print("🔧 Please review the errors above and retry failed steps")
    
    return completed_steps == len(steps)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)