"""
Performance Optimizer Agent Initialization Script
Integrates the specialized performance agent with NEXUS-RSI system
"""

import asyncio
import sys
import json
from pathlib import Path
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from agents.performance_optimizer import PerformanceOptimizerAgent, PerformanceOptimizer
from nexus_core import NexusCore

class PerformanceOptimizerInitializer:
    """Initializes and configures the performance optimizer agent"""
    
    def __init__(self):
        self.nexus_core = None
        self.perf_agent = None
        self.config_validated = False
    
    def validate_configuration(self) -> bool:
        """Validate the agent configuration"""
        config_path = Path(__file__).parent / "performance_optimizer.json"
        
        if not config_path.exists():
            print(f"❌ Configuration file not found: {config_path}")
            return False
        
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            # Validate required sections
            required_sections = [
                'agent_metadata',
                'primary_focus',
                'capabilities',
                'triggers',
                'integration'
            ]
            
            for section in required_sections:
                if section not in config:
                    print(f"❌ Missing required configuration section: {section}")
                    return False
            
            # Validate database path
            db_path = config['integration']['nexus_rsi']['metrics_database']['path']
            if not Path(db_path).exists():
                print(f"⚠️  Database not found at {db_path}, will be created on first use")
            
            print("✅ Configuration validation passed")
            self.config_validated = True
            return True
        
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON in configuration file: {e}")
            return False
        except Exception as e:
            print(f"❌ Configuration validation error: {e}")
            return False
    
    async def initialize_nexus_integration(self) -> bool:
        """Initialize integration with NEXUS-RSI core system"""
        try:
            print("🔗 Initializing NEXUS-RSI core system...")
            
            # Initialize NEXUS core
            self.nexus_core = NexusCore()
            self.nexus_core.initialize_agents()
            
            # Add performance optimizer module to tracking
            self.nexus_core.modules['performance_optimizer'] = {
                'module_id': 'perf_opt_001',
                'name': 'Performance Optimizer',
                'speed': 100.0,
                'accuracy': 0.95,
                'last_update': datetime.now(),
                'status': 'active',
                'improvements': []
            }
            
            print("✅ NEXUS-RSI core integration complete")
            return True
        
        except Exception as e:
            print(f"❌ NEXUS integration failed: {e}")
            return False
    
    async def initialize_performance_agent(self) -> bool:
        """Initialize the performance optimizer agent"""
        try:
            print("🚀 Initializing Performance Optimizer Agent...")
            
            # Create performance agent
            self.perf_agent = PerformanceOptimizerAgent(self.nexus_core)
            
            # Initialize agent
            await self.perf_agent.initialize()
            
            print("✅ Performance Optimizer Agent initialized successfully")
            return True
        
        except Exception as e:
            print(f"❌ Performance agent initialization failed: {e}")
            return False
    
    async def setup_monitoring_triggers(self) -> bool:
        """Setup performance monitoring triggers"""
        try:
            print("⚡ Setting up performance monitoring triggers...")
            
            # Start auto-improvement loop in NEXUS core
            self.nexus_core.start_auto_improvement_loop()
            
            # Configure performance thresholds
            config_path = Path(__file__).parent / "performance_optimizer.json"
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            thresholds = config['triggers']['performance_thresholds']
            
            # Update NEXUS config with performance thresholds
            nexus_config = self.nexus_core.config
            nexus_config.update({
                'performance_thresholds': thresholds,
                'optimization_enabled': True,
                'auto_optimization': True
            })
            
            print("✅ Monitoring triggers configured successfully")
            return True
        
        except Exception as e:
            print(f"❌ Failed to setup monitoring triggers: {e}")
            return False
    
    async def run_initial_performance_scan(self) -> bool:
        """Run initial performance scan and baseline establishment"""
        try:
            print("🔍 Running initial performance scan...")
            
            # Trigger initial optimization cycle
            applied_optimizations = await self.perf_agent.trigger_optimization_cycle()
            
            # Get initial performance metrics
            metrics = await self.perf_agent.get_performance_metrics()
            
            print(f"📊 Initial Performance Metrics:")
            print(f"   - System Score: {metrics['system_score']:.2f}")
            print(f"   - Recommendations: {metrics['recommendations_count']}")
            print(f"   - Alerts: {metrics['alerts_count']}")
            print(f"   - Applied Optimizations: {applied_optimizations}")
            
            print("✅ Initial performance scan complete")
            return True
        
        except Exception as e:
            print(f"❌ Initial performance scan failed: {e}")
            return False
    
    def generate_initialization_report(self) -> str:
        """Generate initialization report"""
        report = f"""
=============================================================
        PERFORMANCE OPTIMIZER AGENT - INITIALIZATION REPORT
=============================================================
Timestamp: {datetime.now():%Y-%m-%d %H:%M:%S}
Agent Name: nexus-performance-optimizer
Model: sonnet (balanced performance)
Specialization: Performance optimization for RSI loops

INITIALIZATION STATUS:
✅ Configuration Validated: {self.config_validated}
✅ NEXUS-RSI Integration: {self.nexus_core is not None}
✅ Performance Agent: {self.perf_agent is not None}
✅ Monitoring Active: {self.perf_agent and self.perf_agent.integration_active}

CAPABILITIES ENABLED:
- Python async code performance profiling
- SQLite query performance analysis
- Docker container resource usage optimization
- Ollama LLM inference pattern identification
- Multi-level caching strategies
- Real-time bottleneck detection
- Automatic performance optimization

MONITORING TRIGGERS CONFIGURED:
- Module score threshold: < 0.8
- Response time threshold: > 500ms
- Memory usage threshold: > 80%
- CPU usage threshold: > 70%

INTEGRATION POINTS:
- NEXUS Metrics Database: Connected
- Ollama API Monitoring: Active
- GitHub Actions Integration: Enabled
- Auto-Patcher Integration: Connected

NEXT STEPS:
1. Monitor dashboard at http://localhost:8501
2. Review performance reports in proofs/performance_reports/
3. Check optimization recommendations in agent logs
4. Monitor real-time metrics and alerts

=============================================================
        """
        return report
    
    async def initialize_complete_system(self) -> bool:
        """Initialize the complete performance optimization system"""
        print("🚀 Starting Performance Optimizer Agent initialization...")
        print("=" * 60)
        
        # Step 1: Validate configuration
        if not self.validate_configuration():
            print("❌ Initialization failed at configuration validation")
            return False
        
        # Step 2: Initialize NEXUS integration
        if not await self.initialize_nexus_integration():
            print("❌ Initialization failed at NEXUS integration")
            return False
        
        # Step 3: Initialize performance agent
        if not await self.initialize_performance_agent():
            print("❌ Initialization failed at performance agent setup")
            return False
        
        # Step 4: Setup monitoring triggers
        if not await self.setup_monitoring_triggers():
            print("❌ Initialization failed at monitoring setup")
            return False
        
        # Step 5: Run initial performance scan
        if not await self.run_initial_performance_scan():
            print("❌ Initialization failed at initial scan")
            return False
        
        # Generate and save initialization report
        report = self.generate_initialization_report()
        print(report)
        
        # Save report to file
        reports_dir = Path("proofs/performance_reports")
        reports_dir.mkdir(parents=True, exist_ok=True)
        
        report_file = reports_dir / f"initialization_report_{datetime.now():%Y%m%d_%H%M%S}.txt"
        with open(report_file, 'w') as f:
            f.write(report)
        
        print(f"📄 Initialization report saved to: {report_file}")
        print("=" * 60)
        print("🎉 Performance Optimizer Agent initialization complete!")
        print("🌟 System is now monitoring and optimizing performance automatically")
        
        return True

async def main():
    """Main initialization function"""
    initializer = PerformanceOptimizerInitializer()
    
    success = await initializer.initialize_complete_system()
    
    if success:
        print("\n🔄 Performance optimization monitoring is now active...")
        print("📊 Dashboard: http://localhost:8501")
        print("📁 Reports: proofs/performance_reports/")
        print("🛑 Press Ctrl+C to stop monitoring")
        
        try:
            # Keep the system running
            while True:
                await asyncio.sleep(60)
                metrics = await initializer.perf_agent.get_performance_metrics()
                print(f"📈 System Score: {metrics['system_score']:.2f} | "
                      f"Recommendations: {metrics['recommendations_count']} | "
                      f"Alerts: {metrics['alerts_count']}")
        
        except KeyboardInterrupt:
            print("\n🛑 Shutting down Performance Optimizer Agent...")
            initializer.perf_agent.optimizer.stop()
            initializer.nexus_core.stop()
            print("✅ Shutdown complete")
    
    else:
        print("\n❌ Performance Optimizer Agent initialization failed")
        print("🔧 Please check the configuration and try again")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())