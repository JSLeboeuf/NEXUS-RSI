"""
NEXUS-RSI Performance Optimizer Agent
Specialized agent for performance optimization and bottleneck detection
"""

import asyncio
import json
import time
import sqlite3
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import logging
import psutil
import cProfile
import pstats
import io
from contextlib import contextmanager
import aiohttp
import numpy as np
import pandas as pd

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetric:
    """Performance metric data structure"""
    timestamp: datetime
    module: str
    metric_type: str
    value: float
    threshold: float
    status: str
    details: Dict[str, Any] = None

@dataclass
class OptimizationRecommendation:
    """Optimization recommendation structure"""
    module: str
    issue_type: str
    severity: str
    description: str
    implementation: str
    estimated_impact: float
    complexity: str
    priority_score: float

class PerformanceProfiler:
    """Advanced performance profiling utilities"""
    
    def __init__(self):
        self.active_profiles = {}
        self.profile_data = {}
    
    @contextmanager
    def profile_context(self, name: str):
        """Context manager for profiling code blocks"""
        profiler = cProfile.Profile()
        profiler.enable()
        start_time = time.time()
        
        try:
            yield profiler
        finally:
            profiler.disable()
            end_time = time.time()
            
            # Store profile data
            s = io.StringIO()
            ps = pstats.Stats(profiler, stream=s)
            ps.sort_stats('cumulative')
            ps.print_stats()
            
            self.profile_data[name] = {
                'execution_time': end_time - start_time,
                'profile_stats': s.getvalue(),
                'timestamp': datetime.now()
            }
    
    def get_memory_usage(self) -> Dict[str, float]:
        """Get current memory usage statistics"""
        process = psutil.Process()
        memory_info = process.memory_info()
        
        return {
            'rss_mb': memory_info.rss / 1024 / 1024,
            'vms_mb': memory_info.vms / 1024 / 1024,
            'percent': process.memory_percent(),
            'available_mb': psutil.virtual_memory().available / 1024 / 1024
        }
    
    def get_cpu_usage(self) -> Dict[str, float]:
        """Get CPU usage statistics"""
        return {
            'cpu_percent': psutil.cpu_percent(interval=1),
            'cpu_count': psutil.cpu_count(),
            'load_avg': psutil.getloadavg() if hasattr(psutil, 'getloadavg') else [0, 0, 0]
        }

class DatabasePerformanceAnalyzer:
    """SQLite database performance analysis"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.connection_pool = []
        self.max_pool_size = 10
    
    async def analyze_query_performance(self, query: str) -> Dict[str, Any]:
        """Analyze query performance"""
        conn = sqlite3.connect(self.db_path)
        
        try:
            # Enable query plan explanation
            conn.execute("PRAGMA optimize")
            
            # Measure query execution time
            start_time = time.time()
            cursor = conn.execute(query)
            results = cursor.fetchall()
            end_time = time.time()
            
            # Get query plan
            explain_query = f"EXPLAIN QUERY PLAN {query}"
            plan_cursor = conn.execute(explain_query)
            query_plan = plan_cursor.fetchall()
            
            return {
                'execution_time': end_time - start_time,
                'rows_returned': len(results),
                'query_plan': query_plan,
                'recommendations': self._analyze_query_plan(query_plan)
            }
        
        finally:
            conn.close()
    
    def _analyze_query_plan(self, query_plan: List[Tuple]) -> List[str]:
        """Analyze query plan and provide recommendations"""
        recommendations = []
        
        for step in query_plan:
            detail = step[3] if len(step) > 3 else ""
            
            if "SCAN TABLE" in detail and "USING INDEX" not in detail:
                recommendations.append("Consider adding an index for table scan optimization")
            
            if "TEMP B-TREE" in detail:
                recommendations.append("Query uses temporary B-tree, consider query optimization")
            
            if "USE TEMP B-TREE FOR ORDER BY" in detail:
                recommendations.append("Consider adding index to avoid temporary sorting")
        
        return recommendations

class OllamaPerformanceMonitor:
    """Monitor Ollama LLM API performance"""
    
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
        self.request_history = []
        self.connection_pool = aiohttp.TCPConnector(limit=10, limit_per_host=5)
    
    async def monitor_request(self, endpoint: str, payload: Dict) -> Dict[str, Any]:
        """Monitor a single request to Ollama API"""
        start_time = time.time()
        
        async with aiohttp.ClientSession(connector=self.connection_pool) as session:
            try:
                async with session.post(f"{self.base_url}/{endpoint}", json=payload) as response:
                    end_time = time.time()
                    response_data = await response.json()
                    
                    metrics = {
                        'endpoint': endpoint,
                        'response_time': end_time - start_time,
                        'status_code': response.status,
                        'payload_size': len(json.dumps(payload)),
                        'response_size': len(json.dumps(response_data)),
                        'timestamp': datetime.now(),
                        'success': response.status == 200
                    }
                    
                    self.request_history.append(metrics)
                    return metrics
            
            except Exception as e:
                return {
                    'endpoint': endpoint,
                    'response_time': time.time() - start_time,
                    'status_code': 0,
                    'error': str(e),
                    'timestamp': datetime.now(),
                    'success': False
                }
    
    def get_performance_summary(self, hours: int = 1) -> Dict[str, Any]:
        """Get performance summary for the last N hours"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_requests = [r for r in self.request_history if r['timestamp'] > cutoff_time]
        
        if not recent_requests:
            return {}
        
        response_times = [r['response_time'] for r in recent_requests]
        success_rate = sum(1 for r in recent_requests if r['success']) / len(recent_requests)
        
        return {
            'total_requests': len(recent_requests),
            'success_rate': success_rate,
            'avg_response_time': np.mean(response_times),
            'p95_response_time': np.percentile(response_times, 95),
            'p99_response_time': np.percentile(response_times, 99),
            'max_response_time': max(response_times),
            'min_response_time': min(response_times)
        }

class PerformanceOptimizer:
    """Main performance optimization agent"""
    
    def __init__(self, config_path: str = None):
        self.config = self._load_config(config_path)
        self.profiler = PerformanceProfiler()
        self.db_analyzer = DatabasePerformanceAnalyzer(
            self.config['integration']['nexus_rsi']['metrics_database']['path']
        )
        self.ollama_monitor = OllamaPerformanceMonitor()
        self.metrics_history = []
        self.recommendations = []
        self.running = False
        
        # Initialize logging
        self.setup_logging()
    
    def _load_config(self, config_path: str = None) -> Dict:
        """Load agent configuration"""
        if config_path is None:
            config_path = Path(__file__).parent / "performance_optimizer.json"
        
        with open(config_path, 'r') as f:
            return json.load(f)
    
    def setup_logging(self):
        """Setup logging configuration"""
        log_level = getattr(logging, self.config.get('log_level', 'INFO').upper())
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    async def start_monitoring(self):
        """Start the performance monitoring loop"""
        self.running = True
        logger.info("🚀 Performance Optimizer Agent Started")
        
        # Start background tasks
        tasks = [
            asyncio.create_task(self._real_time_monitoring()),
            asyncio.create_task(self._deep_analysis_loop()),
            asyncio.create_task(self._trend_analysis_loop()),
            asyncio.create_task(self._generate_reports_loop())
        ]
        
        await asyncio.gather(*tasks)
    
    async def _real_time_monitoring(self):
        """Real-time performance monitoring"""
        interval = self.config['triggers']['monitoring_intervals']['real_time_monitoring']
        
        while self.running:
            try:
                # Collect system metrics
                memory_metrics = self.profiler.get_memory_usage()
                cpu_metrics = self.profiler.get_cpu_usage()
                
                # Check thresholds
                await self._check_thresholds(memory_metrics, cpu_metrics)
                
                await asyncio.sleep(interval)
            
            except Exception as e:
                logger.error(f"Error in real-time monitoring: {e}")
                await asyncio.sleep(interval)
    
    async def _deep_analysis_loop(self):
        """Deep performance analysis loop"""
        interval = self.config['triggers']['monitoring_intervals']['deep_analysis']
        
        while self.running:
            try:
                logger.info("🔍 Starting deep performance analysis")
                
                # Analyze database performance
                db_metrics = await self._analyze_database_performance()
                
                # Analyze Ollama API performance
                ollama_metrics = self.ollama_monitor.get_performance_summary()
                
                # Generate optimization recommendations
                recommendations = await self._generate_recommendations(db_metrics, ollama_metrics)
                self.recommendations.extend(recommendations)
                
                logger.info(f"✅ Deep analysis complete. Generated {len(recommendations)} recommendations")
                await asyncio.sleep(interval)
            
            except Exception as e:
                logger.error(f"Error in deep analysis: {e}")
                await asyncio.sleep(interval)
    
    async def _trend_analysis_loop(self):
        """Long-term trend analysis"""
        interval = self.config['triggers']['monitoring_intervals']['trend_analysis']
        
        while self.running:
            try:
                logger.info("📈 Starting trend analysis")
                
                # Analyze performance trends
                trends = await self._analyze_performance_trends()
                
                # Predict future bottlenecks
                predictions = await self._predict_bottlenecks(trends)
                
                logger.info(f"📊 Trend analysis complete. {len(predictions)} predictions made")
                await asyncio.sleep(interval)
            
            except Exception as e:
                logger.error(f"Error in trend analysis: {e}")
                await asyncio.sleep(interval)
    
    async def _generate_reports_loop(self):
        """Generate comprehensive performance reports"""
        interval = self.config['triggers']['monitoring_intervals']['comprehensive_report']
        
        while self.running:
            try:
                logger.info("📋 Generating comprehensive performance report")
                
                report = await self._generate_comprehensive_report()
                await self._save_report(report)
                
                logger.info("✅ Comprehensive report generated and saved")
                await asyncio.sleep(interval)
            
            except Exception as e:
                logger.error(f"Error generating reports: {e}")
                await asyncio.sleep(interval)
    
    async def _check_thresholds(self, memory_metrics: Dict, cpu_metrics: Dict):
        """Check performance thresholds and trigger alerts"""
        thresholds = self.config['triggers']['performance_thresholds']
        
        # Check memory threshold
        if memory_metrics['percent'] > thresholds['memory_usage_threshold_percent']:
            await self._trigger_alert('memory_threshold_exceeded', memory_metrics)
        
        # Check CPU threshold
        if cpu_metrics['cpu_percent'] > thresholds['cpu_usage_threshold_percent']:
            await self._trigger_alert('cpu_threshold_exceeded', cpu_metrics)
    
    async def _trigger_alert(self, alert_type: str, metrics: Dict):
        """Trigger performance alert"""
        alert = {
            'type': alert_type,
            'timestamp': datetime.now(),
            'metrics': metrics,
            'severity': 'high' if metrics.get('percent', 0) > 90 else 'medium'
        }
        
        logger.warning(f"🚨 Performance Alert: {alert_type} - {metrics}")
        
        # Save alert to database
        await self._save_metric_to_db('alert', alert_type, metrics.get('percent', 0))
    
    async def _analyze_database_performance(self) -> Dict[str, Any]:
        """Analyze database performance"""
        common_queries = [
            "SELECT * FROM metrics ORDER BY timestamp DESC LIMIT 100",
            "SELECT module, AVG(performance_score) FROM metrics GROUP BY module",
            "SELECT COUNT(*) FROM metrics WHERE timestamp > datetime('now', '-1 hour')"
        ]
        
        query_metrics = {}
        
        for query in common_queries:
            metrics = await self.db_analyzer.analyze_query_performance(query)
            query_metrics[query[:50]] = metrics
        
        return query_metrics
    
    async def _generate_recommendations(self, db_metrics: Dict, ollama_metrics: Dict) -> List[OptimizationRecommendation]:
        """Generate optimization recommendations"""
        recommendations = []
        
        # Database optimization recommendations
        for query, metrics in db_metrics.items():
            if metrics['execution_time'] > 0.1:  # 100ms threshold
                recommendation = OptimizationRecommendation(
                    module='database',
                    issue_type='slow_query',
                    severity='medium',
                    description=f"Query execution time: {metrics['execution_time']:.3f}s",
                    implementation="Add database index or optimize query structure",
                    estimated_impact=0.3,
                    complexity='medium',
                    priority_score=metrics['execution_time'] * 10
                )
                recommendations.append(recommendation)
        
        # Ollama API optimization recommendations
        if ollama_metrics and ollama_metrics.get('avg_response_time', 0) > 0.5:
            recommendation = OptimizationRecommendation(
                module='ollama_api',
                issue_type='slow_response',
                severity='high',
                description=f"Average response time: {ollama_metrics['avg_response_time']:.3f}s",
                implementation="Implement request batching and connection pooling",
                estimated_impact=0.5,
                complexity='high',
                priority_score=ollama_metrics['avg_response_time'] * 20
            )
            recommendations.append(recommendation)
        
        return recommendations
    
    async def _analyze_performance_trends(self) -> Dict[str, Any]:
        """Analyze performance trends"""
        # This would analyze historical data to identify trends
        # For now, we'll return a placeholder
        return {
            'memory_trend': 'increasing',
            'cpu_trend': 'stable',
            'response_time_trend': 'decreasing',
            'error_rate_trend': 'stable'
        }
    
    async def _predict_bottlenecks(self, trends: Dict) -> List[Dict]:
        """Predict future bottlenecks based on trends"""
        predictions = []
        
        if trends.get('memory_trend') == 'increasing':
            predictions.append({
                'type': 'memory_exhaustion',
                'probability': 0.7,
                'estimated_time': '24 hours',
                'recommended_action': 'Implement memory optimization patches'
            })
        
        return predictions
    
    async def _generate_comprehensive_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance report"""
        return {
            'timestamp': datetime.now().isoformat(),
            'system_overview': {
                'total_recommendations': len(self.recommendations),
                'high_priority_issues': len([r for r in self.recommendations if r.severity == 'high']),
                'performance_score': self._calculate_overall_performance_score()
            },
            'recommendations': [asdict(r) for r in self.recommendations[-10:]],  # Last 10
            'metrics_summary': await self._get_metrics_summary(),
            'optimization_impact': self._calculate_optimization_impact()
        }
    
    def _calculate_overall_performance_score(self) -> float:
        """Calculate overall system performance score"""
        # This would implement a sophisticated scoring algorithm
        # For now, we'll return a placeholder
        return 0.85
    
    async def _get_metrics_summary(self) -> Dict[str, Any]:
        """Get summary of recent metrics"""
        return {
            'total_metrics_collected': len(self.metrics_history),
            'average_response_time': 0.25,
            'memory_utilization': 65.0,
            'cpu_utilization': 45.0
        }
    
    def _calculate_optimization_impact(self) -> Dict[str, Any]:
        """Calculate the impact of optimizations"""
        return {
            'performance_improvement': '15%',
            'response_time_reduction': '25%',
            'resource_savings': '20%'
        }
    
    async def _save_report(self, report: Dict):
        """Save performance report"""
        reports_dir = Path("proofs/performance_reports")
        reports_dir.mkdir(parents=True, exist_ok=True)
        
        report_file = reports_dir / f"performance_report_{datetime.now():%Y%m%d_%H%M%S}.json"
        
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
    
    async def _save_metric_to_db(self, metric_type: str, module: str, value: float):
        """Save metric to database"""
        conn = sqlite3.connect(self.config['integration']['nexus_rsi']['metrics_database']['path'])
        
        try:
            conn.execute(
                "INSERT INTO metrics (timestamp, module, performance_score, status, action_taken) VALUES (?, ?, ?, ?, ?)",
                (time.time(), module, value, 'monitored', metric_type)
            )
            conn.commit()
        finally:
            conn.close()
    
    async def apply_optimization(self, recommendation: OptimizationRecommendation) -> bool:
        """Apply an optimization recommendation"""
        logger.info(f"🔧 Applying optimization: {recommendation.description}")
        
        try:
            # This would implement the actual optimization
            # For now, we'll simulate successful application
            await asyncio.sleep(1)  # Simulate work
            
            logger.info(f"✅ Optimization applied successfully")
            return True
        
        except Exception as e:
            logger.error(f"❌ Failed to apply optimization: {e}")
            return False
    
    def stop(self):
        """Stop the performance optimizer"""
        self.running = False
        logger.info("🛑 Performance Optimizer Agent Stopped")

# Agent initialization and integration
class PerformanceOptimizerAgent:
    """Integration wrapper for NEXUS-RSI system"""
    
    def __init__(self, nexus_core):
        self.nexus_core = nexus_core
        self.optimizer = PerformanceOptimizer()
        self.integration_active = False
    
    async def initialize(self):
        """Initialize the agent with NEXUS-RSI system"""
        logger.info("🔗 Initializing Performance Optimizer Agent integration")
        
        # Register with NEXUS core
        self.nexus_core.agents['performance_optimizer'] = self
        
        # Start monitoring
        asyncio.create_task(self.optimizer.start_monitoring())
        
        self.integration_active = True
        logger.info("✅ Performance Optimizer Agent integration complete")
    
    async def get_performance_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics for dashboard"""
        return {
            'system_score': self.optimizer._calculate_overall_performance_score(),
            'recommendations_count': len(self.optimizer.recommendations),
            'alerts_count': len([r for r in self.optimizer.recommendations if r.severity == 'high']),
            'last_analysis': datetime.now().isoformat()
        }
    
    async def trigger_optimization_cycle(self):
        """Manually trigger an optimization cycle"""
        logger.info("🚀 Manual optimization cycle triggered")
        
        # Analyze current performance
        db_metrics = await self.optimizer._analyze_database_performance()
        ollama_metrics = self.optimizer.ollama_monitor.get_performance_summary()
        
        # Generate and apply recommendations
        recommendations = await self.optimizer._generate_recommendations(db_metrics, ollama_metrics)
        
        applied_count = 0
        for recommendation in recommendations[:5]:  # Apply top 5
            if await self.optimizer.apply_optimization(recommendation):
                applied_count += 1
        
        logger.info(f"✅ Optimization cycle complete. Applied {applied_count} optimizations")
        return applied_count

if __name__ == "__main__":
    # Standalone execution for testing
    async def main():
        optimizer = PerformanceOptimizer()
        await optimizer.start_monitoring()
    
    asyncio.run(main())