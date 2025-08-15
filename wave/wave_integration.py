#!/usr/bin/env python3
"""
NEXUS-RSI Wave Integration Module
Bridges Wave Orchestration with existing Multi-Agent System
"""

import asyncio
import json
import sys
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from wave_orchestrator import WaveOrchestrator, WaveContext, WaveStrategy, WavePhase
sys.path.append(str(Path(__file__).parent.parent / "agents"))
from master_orchestrator import AgentOrchestrator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('WaveIntegration')

class WaveAgentBridge:
    """Bridge between Wave Orchestration and Agent System"""
    
    def __init__(self):
        self.wave_orchestrator = WaveOrchestrator()
        self.agent_orchestrator = AgentOrchestrator()
        
        # Map wave phases to agent workflows
        self.phase_workflow_map = {
            WavePhase.REVIEW: 'quality_analysis',
            WavePhase.PLANNING: 'architecture_design',
            WavePhase.IMPLEMENTATION: 'code_modification',
            WavePhase.VALIDATION: 'testing_validation',
            WavePhase.OPTIMIZATION: 'performance_optimization'
        }
        
        # Agent capabilities for wave phases
        self.phase_agent_map = {
            WavePhase.REVIEW: {
                'primary': 'quality',
                'secondary': ['security', 'performance'],
                'parallel': True
            },
            WavePhase.PLANNING: {
                'primary': 'performance',
                'secondary': ['quality'],
                'parallel': False
            },
            WavePhase.IMPLEMENTATION: {
                'primary': 'quality',
                'secondary': ['security'],
                'parallel': False
            },
            WavePhase.VALIDATION: {
                'primary': 'security',
                'secondary': ['quality', 'monitor'],
                'parallel': True
            },
            WavePhase.OPTIMIZATION: {
                'primary': 'performance',
                'secondary': ['monitor'],
                'parallel': True
            }
        }
        
    async def execute_wave_with_agents(self, context: WaveContext) -> Dict[str, Any]:
        """Execute wave using the multi-agent system"""
        logger.info(f"[BRIDGE] Executing wave {context.wave_id} with agents")
        
        results = {
            'wave_id': context.wave_id,
            'strategy': context.strategy.value,
            'agent_results': {},
            'phase_results': {}
        }
        
        # Get strategy configuration
        strategy_config = self.wave_orchestrator.strategy_configs[context.strategy]
        phases = strategy_config['phases']
        
        # Dynamic phase selection for adaptive strategy
        if context.strategy == WaveStrategy.ADAPTIVE:
            phases = self.wave_orchestrator.select_adaptive_phases(context)
            
        # Execute each phase with agents
        for phase in phases:
            logger.info(f"[BRIDGE] Phase {phase.value} starting")
            
            # Get agent configuration for phase
            agent_config = self.phase_agent_map[phase]
            primary_agent = agent_config['primary']
            secondary_agents = agent_config['secondary']
            parallel = agent_config['parallel']
            
            # Start primary agent
            await self.agent_orchestrator.start_agent(primary_agent)
            
            # Start secondary agents
            if parallel:
                # Start all secondary agents in parallel
                tasks = []
                for agent in secondary_agents:
                    tasks.append(self.agent_orchestrator.start_agent(agent))
                await asyncio.gather(*tasks)
            else:
                # Start secondary agents sequentially
                for agent in secondary_agents:
                    await self.agent_orchestrator.start_agent(agent)
                    await asyncio.sleep(1)
                    
            # Collect results
            phase_results = {
                'phase': phase.value,
                'primary_agent': primary_agent,
                'secondary_agents': secondary_agents,
                'execution_mode': 'parallel' if parallel else 'sequential'
            }
            
            # Get agent scores for this phase
            primary_score = await self.agent_orchestrator.get_agent_score(primary_agent)
            secondary_scores = {}
            for agent in secondary_agents:
                secondary_scores[agent] = await self.agent_orchestrator.get_agent_score(agent)
                
            phase_results['scores'] = {
                'primary': primary_score,
                'secondary': secondary_scores,
                'average': (primary_score + sum(secondary_scores.values())) / (1 + len(secondary_scores))
            }
            
            results['phase_results'][phase.value] = phase_results
            
            # Create checkpoint after each phase
            if strategy_config['checkpoint_frequency'] in ['per_phase', 'continuous']:
                await self.wave_orchestrator.create_checkpoint(context, phase)
                
        # Calculate overall wave score
        total_score = sum(
            pr['scores']['average'] 
            for pr in results['phase_results'].values()
        ) / len(results['phase_results'])
        
        results['overall_score'] = total_score
        results['status'] = 'success' if total_score > 0.7 else 'needs_improvement'
        
        return results
        
    async def run_adaptive_wave(self, target: str) -> Dict[str, Any]:
        """Run adaptive wave based on target analysis"""
        
        # Analyze target
        complexity, files, ops, domains = await self.wave_orchestrator.analyze_complexity(target)
        
        # Create context
        context = WaveContext(
            wave_id="",
            strategy=WaveStrategy.ADAPTIVE,
            complexity_score=complexity,
            file_count=files,
            operation_types=ops,
            domains=domains
        )
        context.wave_id = context.generate_id()
        
        # Execute wave with agents
        results = await self.execute_wave_with_agents(context)
        
        return results
        
    async def run_enterprise_wave(self, targets: List[str]) -> Dict[str, Any]:
        """Run enterprise-scale wave for multiple targets"""
        
        all_results = {
            'strategy': 'enterprise',
            'targets': {},
            'summary': {
                'total_targets': len(targets),
                'successful': 0,
                'failed': 0,
                'average_score': 0
            }
        }
        
        # Process each target
        tasks = []
        for target in targets:
            # Analyze target
            complexity, files, ops, domains = await self.wave_orchestrator.analyze_complexity(target)
            
            # Create context
            context = WaveContext(
                wave_id="",
                strategy=WaveStrategy.ENTERPRISE,
                complexity_score=complexity,
                file_count=files,
                operation_types=ops,
                domains=domains
            )
            context.wave_id = context.generate_id()
            
            # Add to parallel execution
            tasks.append(self.execute_wave_with_agents(context))
            
        # Execute all waves in parallel
        results = await asyncio.gather(*tasks)
        
        # Compile results
        for i, target in enumerate(targets):
            all_results['targets'][target] = results[i]
            if results[i]['status'] == 'success':
                all_results['summary']['successful'] += 1
            else:
                all_results['summary']['failed'] += 1
                
        # Calculate average score
        all_results['summary']['average_score'] = sum(
            r['overall_score'] for r in results
        ) / len(results)
        
        return all_results

class WaveMonitor:
    """Monitor and visualize wave execution"""
    
    def __init__(self):
        self.active_waves = {}
        self.completed_waves = []
        
    def display_wave_status(self, wave_id: str, phase: str, progress: float):
        """Display real-time wave status"""
        bar_length = 40
        filled = int(bar_length * progress)
        bar = '=' * filled + '-' * (bar_length - filled)
        
        print(f"\r[WAVE {wave_id}] Phase: {phase} [{bar}] {progress*100:.1f}%", end='')
        
    def generate_wave_report(self, results: Dict[str, Any]) -> str:
        """Generate formatted wave execution report"""
        report = []
        report.append("=" * 60)
        report.append("WAVE EXECUTION REPORT")
        report.append("=" * 60)
        report.append(f"Wave ID: {results['wave_id']}")
        report.append(f"Strategy: {results['strategy']}")
        report.append(f"Overall Score: {results.get('overall_score', 0):.2f}")
        report.append(f"Status: {results.get('status', 'unknown')}")
        report.append("")
        report.append("Phase Results:")
        report.append("-" * 40)
        
        for phase_name, phase_data in results.get('phase_results', {}).items():
            report.append(f"\n{phase_name.upper()}:")
            report.append(f"  Primary Agent: {phase_data['primary_agent']}")
            report.append(f"  Secondary Agents: {', '.join(phase_data['secondary_agents'])}")
            report.append(f"  Execution: {phase_data['execution_mode']}")
            report.append(f"  Score: {phase_data['scores']['average']:.2f}")
            
        report.append("")
        report.append("=" * 60)
        
        return "\n".join(report)

async def demonstration():
    """Demonstrate wave integration capabilities"""
    print("""
============================================================
    NEXUS-RSI WAVE MODE - AGENT INTEGRATION
    Compound Intelligence through Multi-Phase Orchestration
============================================================
    """)
    
    bridge = WaveAgentBridge()
    monitor = WaveMonitor()
    
    # Demo 1: Adaptive Wave
    print("\n[DEMO 1] Running Adaptive Wave for NEXUS-RSI")
    print("-" * 60)
    
    target = "C:\\Users\\Jean-SamuelLeboeuf\\NEXUS-RSI"
    results = await bridge.run_adaptive_wave(target)
    
    report = monitor.generate_wave_report(results)
    print(report)
    
    # Demo 2: Progressive Enhancement
    print("\n[DEMO 2] Progressive Enhancement Wave")
    print("-" * 60)
    
    context = WaveContext(
        wave_id="prog_demo",
        strategy=WaveStrategy.PROGRESSIVE,
        complexity_score=0.75,
        file_count=50,
        operation_types=['optimization', 'refactoring'],
        domains=['backend', 'performance']
    )
    
    results = await bridge.execute_wave_with_agents(context)
    report = monitor.generate_wave_report(results)
    print(report)
    
    print("\n[SUCCESS] Wave integration demonstration completed")

if __name__ == "__main__":
    asyncio.run(demonstration())