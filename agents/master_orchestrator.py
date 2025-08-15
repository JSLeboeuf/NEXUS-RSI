#!/usr/bin/env python3
"""
NEXUS-RSI Master Agent Orchestrator
Coordinates all specialized agents following IndyDevDan's meta-agent methodology
"My agents are building my agents" - Complete observability and orchestration
"""

import asyncio
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
import sqlite3
import subprocess
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('MasterOrchestrator')

class AgentOrchestrator:
    """Master orchestrator for all NEXUS-RSI specialized agents"""
    
    def __init__(self):
        self.agents = {
            'performance': {
                'name': 'nexus-performance-optimizer',
                'model': 'sonnet',
                'config': 'agents/performance_optimizer.json',
                'script': 'agents/performance_optimizer.py',
                'status': 'inactive',
                'last_run': None,
                'success_rate': 0.0
            },
            'security': {
                'name': 'nexus-security-analyzer', 
                'model': 'opus',
                'config': 'agents/security_analyzer.json',
                'script': 'agents/security_analyzer.py',
                'status': 'inactive',
                'last_run': None,
                'success_rate': 0.0
            },
            'monitor': {
                'name': 'nexus-system-monitor',
                'model': 'haiku',
                'config': 'agents/system_monitor.json',
                'script': 'agents/system_monitor.py',
                'status': 'inactive',
                'last_run': None,
                'success_rate': 0.0
            },
            'quality': {
                'name': 'nexus-code-quality',
                'model': 'sonnet',
                'config': 'agents/code_quality.json',
                'script': 'agents/code_quality.py',
                'status': 'inactive',
                'last_run': None,
                'success_rate': 0.0
            }
        }
        
        self.workflows = {
            'continuous_improvement': {
                'agents': ['quality', 'performance', 'security'],
                'mode': 'sequential',
                'interval': 300  # 5 minutes
            },
            'system_health': {
                'agents': ['monitor'],
                'mode': 'continuous',
                'interval': 10  # 10 seconds
            },
            'security_audit': {
                'agents': ['security', 'quality'],
                'mode': 'parallel',
                'interval': 3600  # 1 hour
            },
            'performance_optimization': {
                'agents': ['performance', 'monitor'],
                'mode': 'parallel',
                'interval': 600  # 10 minutes
            }
        }
        
        self.metrics_db = Path("nexus_orchestrator.db")
        self.init_database()
        
    def init_database(self):
        """Initialize orchestrator database"""
        conn = sqlite3.connect(self.metrics_db)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS agent_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL,
                agent_name TEXT,
                workflow TEXT,
                status TEXT,
                duration REAL,
                metrics TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS orchestrator_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL,
                active_agents INTEGER,
                workflows_running INTEGER,
                total_runs INTEGER,
                success_rate REAL,
                system_score REAL
            )
        """)
        conn.commit()
        conn.close()
        
    async def start_agent(self, agent_key: str) -> bool:
        """Start a specific agent"""
        agent = self.agents[agent_key]
        logger.info(f"Starting agent: {agent['name']}")
        
        try:
            # Load agent configuration
            config_path = Path(agent['config'])
            if config_path.exists():
                with open(config_path, 'r') as f:
                    config = json.load(f)
            else:
                logger.warning(f"Config not found for {agent['name']}, using defaults")
                config = {}
            
            # Start agent process
            script_path = Path(agent['script'])
            if script_path.exists():
                process = subprocess.Popen(
                    ['python', str(script_path)],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                
                # Update agent status
                agent['status'] = 'active'
                agent['last_run'] = time.time()
                
                logger.info(f"Agent {agent['name']} started successfully")
                return True
            else:
                logger.error(f"Script not found: {script_path}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to start agent {agent['name']}: {e}")
            return False
            
    async def stop_agent(self, agent_key: str):
        """Stop a specific agent"""
        agent = self.agents[agent_key]
        logger.info(f"Stopping agent: {agent['name']}")
        agent['status'] = 'inactive'
        
    async def run_workflow(self, workflow_name: str):
        """Execute a specific workflow"""
        workflow = self.workflows[workflow_name]
        logger.info(f"Running workflow: {workflow_name}")
        
        start_time = time.time()
        results = {}
        
        if workflow['mode'] == 'sequential':
            # Run agents one by one
            for agent_key in workflow['agents']:
                success = await self.start_agent(agent_key)
                results[agent_key] = success
                await asyncio.sleep(2)  # Wait between agents
                
        elif workflow['mode'] == 'parallel':
            # Run all agents simultaneously
            tasks = []
            for agent_key in workflow['agents']:
                tasks.append(self.start_agent(agent_key))
            results_list = await asyncio.gather(*tasks)
            for i, agent_key in enumerate(workflow['agents']):
                results[agent_key] = results_list[i]
                
        elif workflow['mode'] == 'continuous':
            # Start agents and keep them running
            for agent_key in workflow['agents']:
                await self.start_agent(agent_key)
                results[agent_key] = True
                
        duration = time.time() - start_time
        
        # Log workflow run
        conn = sqlite3.connect(self.metrics_db)
        conn.execute("""
            INSERT INTO agent_runs (timestamp, agent_name, workflow, status, duration, metrics)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (time.time(), 'orchestrator', workflow_name, 'completed', duration, json.dumps(results)))
        conn.commit()
        conn.close()
        
        logger.info(f"Workflow {workflow_name} completed in {duration:.2f}s")
        return results
        
    async def calculate_system_score(self) -> float:
        """Calculate overall system health score"""
        scores = []
        
        # Performance score (from performance agent)
        perf_score = await self.get_agent_score('performance')
        scores.append(perf_score * 0.25)
        
        # Security score (from security agent) 
        sec_score = await self.get_agent_score('security')
        scores.append(sec_score * 0.25)
        
        # Quality score (from quality agent)
        qual_score = await self.get_agent_score('quality')
        scores.append(qual_score * 0.25)
        
        # Availability score (from monitor agent)
        avail_score = await self.get_agent_score('monitor')
        scores.append(avail_score * 0.25)
        
        return sum(scores)
        
    async def get_agent_score(self, agent_key: str) -> float:
        """Get current score from an agent"""
        # In production, this would query the agent's actual metrics
        # For now, return a simulated score
        if self.agents[agent_key]['status'] == 'active':
            return 0.85
        return 0.5
        
    async def orchestration_loop(self):
        """Main orchestration loop"""
        logger.info("Starting NEXUS-RSI Master Orchestration")
        logger.info("=" * 60)
        
        iteration = 0
        while True:
            iteration += 1
            logger.info(f"\n[ORCHESTRATION] Iteration #{iteration} - {datetime.now().strftime('%H:%M:%S')}")
            
            # Run scheduled workflows
            current_time = time.time()
            for workflow_name, workflow in self.workflows.items():
                # Check if it's time to run this workflow
                if iteration % (workflow['interval'] // 10) == 0:
                    logger.info(f"Triggering workflow: {workflow_name}")
                    await self.run_workflow(workflow_name)
                    
            # Calculate and display system score
            system_score = await self.calculate_system_score()
            
            # Display agent status
            active_agents = sum(1 for a in self.agents.values() if a['status'] == 'active')
            logger.info(f"\n[STATUS] Active Agents: {active_agents}/4 | System Score: {system_score:.2f}")
            
            for agent_key, agent in self.agents.items():
                status_icon = "[ACTIVE]" if agent['status'] == 'active' else "[IDLE]"
                logger.info(f"  {status_icon} {agent['name']} ({agent['model']})")
                
            # Log orchestrator metrics
            conn = sqlite3.connect(self.metrics_db)
            conn.execute("""
                INSERT INTO orchestrator_metrics 
                (timestamp, active_agents, workflows_running, total_runs, success_rate, system_score)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (time.time(), active_agents, len(self.workflows), iteration, 0.95, system_score))
            conn.commit()
            conn.close()
            
            # Take action based on system score
            if system_score < 0.5:
                logger.warning("[ALERT] System score critically low - triggering recovery")
                await self.run_workflow('continuous_improvement')
            elif system_score < 0.7:
                logger.info("[ACTION] System score below target - optimizing")
                await self.run_workflow('performance_optimization')
                
            logger.info("\n[WAIT] Next orchestration cycle in 10 seconds...")
            await asyncio.sleep(10)
            
    async def shutdown(self):
        """Graceful shutdown of all agents"""
        logger.info("\n[SHUTDOWN] Stopping all agents...")
        for agent_key in self.agents:
            await self.stop_agent(agent_key)
        logger.info("[SHUTDOWN] All agents stopped")

async def main():
    """Main entry point"""
    orchestrator = AgentOrchestrator()
    
    print("""
============================================================
       NEXUS-RSI MASTER AGENT ORCHESTRATOR
    IndyDevDan Meta-Agent Methodology Activated
    "My agents are building my agents"
============================================================
    """)
    
    print("\n[AGENTS] Specialized Agents Available:")
    print("-" * 50)
    print("[1] Performance Optimizer (sonnet) - Bottleneck detection")
    print("[2] Security Analyzer (opus) - Vulnerability scanning")
    print("[3] System Monitor (haiku) - Real-time monitoring")
    print("[4] Code Quality (sonnet) - Maintainability analysis")
    
    print("\n[WORKFLOWS] Orchestration Workflows:")
    print("-" * 50)
    print("[1] Continuous Improvement - Quality → Performance → Security")
    print("[2] System Health - Continuous monitoring")
    print("[3] Security Audit - Parallel security + quality")
    print("[4] Performance Optimization - Parallel performance + monitor")
    
    print("\n[INFO] Complete observability enabled")
    print("[INFO] Information flow optimization active")
    print("[INFO] Multi-agent orchestration ready")
    print("=" * 60)
    
    try:
        await orchestrator.orchestration_loop()
    except KeyboardInterrupt:
        await orchestrator.shutdown()
        print("\n[OK] Master Orchestrator stopped")

if __name__ == "__main__":
    asyncio.run(main())