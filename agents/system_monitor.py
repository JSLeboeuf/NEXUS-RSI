#!/usr/bin/env python3
"""
NEXUS System Monitor Agent
Real-time system monitoring and alerting for NEXUS-RSI infrastructure
"""

import asyncio
import json
import logging
import sqlite3
import time
import psutil
import requests
import subprocess
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from collections import defaultdict, deque
import docker
import os
import sys

# Add the NEXUS-RSI root to the path
sys.path.append(str(Path(__file__).parent.parent))

@dataclass
class ServiceStatus:
    name: str
    status: str
    health: str
    uptime: float
    last_check: datetime
    error_count: int
    response_time: float

@dataclass
class SystemMetrics:
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    network_sent: int
    network_recv: int
    process_count: int

@dataclass
class Alert:
    severity: str
    source: str
    message: str
    timestamp: datetime
    acknowledged: bool = False
    resolved: bool = False

class SystemMonitor:
    def __init__(self, config_path: str = None):
        """Initialize the System Monitor Agent"""
        self.config_path = config_path or "agents/system_monitor.json"
        self.config = self._load_config()
        self.logger = self._setup_logging()
        self.db_path = "nexus_metrics.db"
        self.running = False
        self.docker_client = None
        
        # Monitoring data structures
        self.service_statuses: Dict[str, ServiceStatus] = {}
        self.system_metrics_history = deque(maxlen=1000)
        self.alerts: List[Alert] = []
        self.error_patterns = deque(maxlen=100)
        
        # Initialize components
        self._init_database()
        self._init_docker_client()
        self._init_monitoring_threads()
        
        self.logger.info("NEXUS System Monitor Agent initialized")

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from JSON file"""
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            self.logger.error(f"Configuration file not found: {self.config_path}")
            return {}
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON configuration: {e}")
            return {}

    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration"""
        logger = logging.getLogger("nexus_system_monitor")
        logger.setLevel(logging.INFO)
        
        # Create logs directory if it doesn't exist
        log_dir = Path("logs/system_monitor")
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # File handler
        fh = logging.FileHandler(log_dir / "system_monitor.log")
        fh.setLevel(logging.INFO)
        
        # Console handler
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)
        
        logger.addHandler(fh)
        logger.addHandler(ch)
        
        return logger

    def _init_database(self):
        """Initialize SQLite database for metrics storage"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create tables
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS system_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME,
                    cpu_percent REAL,
                    memory_percent REAL,
                    disk_percent REAL,
                    network_sent INTEGER,
                    network_recv INTEGER,
                    process_count INTEGER
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS service_status (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME,
                    service_name TEXT,
                    status TEXT,
                    health TEXT,
                    uptime REAL,
                    error_count INTEGER,
                    response_time REAL
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME,
                    severity TEXT,
                    source TEXT,
                    message TEXT,
                    acknowledged INTEGER DEFAULT 0,
                    resolved INTEGER DEFAULT 0
                )
            """)
            
            conn.commit()
            conn.close()
            
            self.logger.info("Database initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize database: {e}")

    def _init_docker_client(self):
        """Initialize Docker client for container monitoring"""
        try:
            self.docker_client = docker.from_env()
            self.logger.info("Docker client initialized")
        except Exception as e:
            self.logger.warning(f"Failed to initialize Docker client: {e}")
            self.docker_client = None

    def _init_monitoring_threads(self):
        """Initialize monitoring thread pools"""
        self.monitor_threads = {}
        self.thread_pool = []

    async def start_monitoring(self):
        """Start all monitoring tasks"""
        self.running = True
        self.logger.info("Starting NEXUS System Monitor")
        
        # Start monitoring tasks concurrently
        tasks = [
            self.monitor_system_resources(),
            self.monitor_docker_services(),
            self.monitor_process_health(),
            self.monitor_service_endpoints(),
            self.monitor_log_files(),
            self.generate_alerts(),
            self.cleanup_old_data()
        ]
        
        await asyncio.gather(*tasks)

    async def monitor_system_resources(self):
        """Monitor system resource utilization"""
        while self.running:
            try:
                # Collect system metrics
                cpu_percent = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()
                disk = psutil.disk_usage('/')
                network = psutil.net_io_counters()
                process_count = len(psutil.pids())
                
                metrics = SystemMetrics(
                    timestamp=datetime.now(),
                    cpu_percent=cpu_percent,
                    memory_percent=memory.percent,
                    disk_percent=disk.percent,
                    network_sent=network.bytes_sent,
                    network_recv=network.bytes_recv,
                    process_count=process_count
                )
                
                # Store metrics
                self.system_metrics_history.append(metrics)
                await self._store_system_metrics(metrics)
                
                # Check thresholds
                await self._check_resource_thresholds(metrics)
                
                await asyncio.sleep(
                    self.config.get("capabilities", {})
                    .get("metric_collection_storage", {})
                    .get("collection_agents", {})
                    .get("real_time", 10)
                )
                
            except Exception as e:
                self.logger.error(f"Error monitoring system resources: {e}")
                await asyncio.sleep(10)

    async def monitor_docker_services(self):
        """Monitor Docker container health"""
        if not self.docker_client:
            return
            
        while self.running:
            try:
                containers = self.docker_client.containers.list(all=True)
                
                for container in containers:
                    service_name = container.name
                    
                    # Get container status
                    status = container.status
                    health = self._get_container_health(container)
                    
                    # Calculate uptime
                    uptime = 0
                    if status == "running":
                        started_at = container.attrs['State']['StartedAt']
                        start_time = datetime.fromisoformat(started_at.replace('Z', '+00:00'))
                        uptime = (datetime.now() - start_time.replace(tzinfo=None)).total_seconds()
                    
                    # Update service status
                    service_status = ServiceStatus(
                        name=service_name,
                        status=status,
                        health=health,
                        uptime=uptime,
                        last_check=datetime.now(),
                        error_count=0,  # TODO: Get from logs
                        response_time=0  # TODO: Measure endpoint response
                    )
                    
                    self.service_statuses[service_name] = service_status
                    await self._store_service_status(service_status)
                    
                    # Check for service issues
                    if status != "running" or health == "unhealthy":
                        await self._trigger_service_alert(service_name, status, health)
                
                await asyncio.sleep(30)
                
            except Exception as e:
                self.logger.error(f"Error monitoring Docker services: {e}")
                await asyncio.sleep(30)

    async def monitor_process_health(self):
        """Monitor critical NEXUS processes"""
        monitored_processes = self.config.get("capabilities", {}).get(
            "process_monitoring_restart", {}
        ).get("monitored_processes", [])
        
        while self.running:
            try:
                for process_name in monitored_processes:
                    is_running = await self._is_process_running(process_name)
                    
                    if not is_running:
                        self.logger.warning(f"Process {process_name} is not running")
                        
                        # Attempt auto-restart if enabled
                        if self.config.get("capabilities", {}).get(
                            "process_monitoring_restart", {}
                        ).get("auto_restart", False):
                            await self._restart_process(process_name)
                        
                        await self._create_alert(
                            "major", 
                            f"process_{process_name}", 
                            f"Process {process_name} is down"
                        )
                
                await asyncio.sleep(60)
                
            except Exception as e:
                self.logger.error(f"Error monitoring process health: {e}")
                await asyncio.sleep(60)

    async def monitor_service_endpoints(self):
        """Monitor service endpoint health"""
        health_endpoints = self.config.get("capabilities", {}).get(
            "docker_container_health_checks", {}
        ).get("health_endpoints", {})
        
        while self.running:
            try:
                for service, endpoint in health_endpoints.items():
                    start_time = time.time()
                    
                    try:
                        response = requests.get(endpoint, timeout=10)
                        response_time = (time.time() - start_time) * 1000
                        
                        if response.status_code == 200:
                            self.logger.debug(f"{service} health check passed ({response_time:.2f}ms)")
                        else:
                            await self._create_alert(
                                "warning",
                                f"endpoint_{service}",
                                f"Service {service} returned status {response.status_code}"
                            )
                            
                    except requests.exceptions.RequestException as e:
                        await self._create_alert(
                            "critical",
                            f"endpoint_{service}",
                            f"Service {service} endpoint unreachable: {e}"
                        )
                        response_time = 0
                    
                    # Update service status with response time
                    if service in self.service_statuses:
                        self.service_statuses[service].response_time = response_time
                
                await asyncio.sleep(30)
                
            except Exception as e:
                self.logger.error(f"Error monitoring service endpoints: {e}")
                await asyncio.sleep(30)

    async def monitor_log_files(self):
        """Monitor log files for errors and patterns"""
        log_sources = self.config.get("capabilities", {}).get(
            "log_aggregation_analysis", {}
        ).get("log_sources", [])
        
        error_patterns = self.config.get("capabilities", {}).get(
            "log_aggregation_analysis", {}
        ).get("log_parsing_rules", {}).get("error_patterns", [])
        
        while self.running:
            try:
                for log_source in log_sources:
                    if "*" in log_source:
                        # Handle glob patterns
                        from glob import glob
                        log_files = glob(log_source)
                    else:
                        log_files = [log_source]
                    
                    for log_file in log_files:
                        if os.path.exists(log_file):
                            await self._scan_log_file(log_file, error_patterns)
                
                await asyncio.sleep(60)
                
            except Exception as e:
                self.logger.error(f"Error monitoring log files: {e}")
                await asyncio.sleep(60)

    async def generate_alerts(self):
        """Generate and route alerts based on conditions"""
        while self.running:
            try:
                # Process pending alerts
                for alert in self.alerts:
                    if not alert.acknowledged:
                        await self._route_alert(alert)
                
                # Clean up old resolved alerts
                current_time = datetime.now()
                self.alerts = [
                    alert for alert in self.alerts
                    if not alert.resolved or 
                    (current_time - alert.timestamp).days < 7
                ]
                
                await asyncio.sleep(30)
                
            except Exception as e:
                self.logger.error(f"Error generating alerts: {e}")
                await asyncio.sleep(30)

    async def cleanup_old_data(self):
        """Clean up old metrics and logs"""
        while self.running:
            try:
                # Clean up old database records
                retention_days = self.config.get("monitoring", {}).get("retention_days", 30)
                cutoff_date = datetime.now() - timedelta(days=retention_days)
                
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cursor.execute(
                    "DELETE FROM system_metrics WHERE timestamp < ?",
                    (cutoff_date,)
                )
                cursor.execute(
                    "DELETE FROM service_status WHERE timestamp < ?",
                    (cutoff_date,)
                )
                cursor.execute(
                    "DELETE FROM alerts WHERE timestamp < ? AND resolved = 1",
                    (cutoff_date,)
                )
                
                conn.commit()
                conn.close()
                
                self.logger.info(f"Cleaned up data older than {retention_days} days")
                
                # Sleep for 24 hours
                await asyncio.sleep(86400)
                
            except Exception as e:
                self.logger.error(f"Error during cleanup: {e}")
                await asyncio.sleep(3600)

    # Helper methods
    def _get_container_health(self, container) -> str:
        """Get container health status"""
        try:
            health = container.attrs.get('State', {}).get('Health', {})
            if health:
                return health.get('Status', 'unknown')
            return 'no_healthcheck'
        except Exception:
            return 'unknown'

    async def _is_process_running(self, process_name: str) -> bool:
        """Check if a process is running"""
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                if process_name in ' '.join(proc.info['cmdline'] or []):
                    return True
            return False
        except Exception:
            return False

    async def _restart_process(self, process_name: str):
        """Restart a failed process"""
        try:
            self.logger.info(f"Attempting to restart process: {process_name}")
            
            # Get the full path to the script
            script_path = Path("C:/Users/Jean-SamuelLeboeuf/NEXUS-RSI") / process_name
            
            if script_path.exists():
                subprocess.Popen([sys.executable, str(script_path)])
                self.logger.info(f"Restarted process: {process_name}")
            else:
                self.logger.error(f"Script not found: {script_path}")
                
        except Exception as e:
            self.logger.error(f"Failed to restart process {process_name}: {e}")

    async def _store_system_metrics(self, metrics: SystemMetrics):
        """Store system metrics in database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO system_metrics 
                (timestamp, cpu_percent, memory_percent, disk_percent, 
                 network_sent, network_recv, process_count)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                metrics.timestamp,
                metrics.cpu_percent,
                metrics.memory_percent,
                metrics.disk_percent,
                metrics.network_sent,
                metrics.network_recv,
                metrics.process_count
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Failed to store system metrics: {e}")

    async def _store_service_status(self, status: ServiceStatus):
        """Store service status in database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO service_status 
                (timestamp, service_name, status, health, uptime, error_count, response_time)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                status.last_check,
                status.name,
                status.status,
                status.health,
                status.uptime,
                status.error_count,
                status.response_time
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Failed to store service status: {e}")

    async def _check_resource_thresholds(self, metrics: SystemMetrics):
        """Check if resource usage exceeds thresholds"""
        thresholds = self.config.get("triggers", {}).get("resource_threshold_triggers", {})
        
        # Check CPU threshold
        cpu_warning = thresholds.get("cpu_usage", {}).get("warning", 70)
        cpu_critical = thresholds.get("cpu_usage", {}).get("critical", 85)
        
        if metrics.cpu_percent > cpu_critical:
            await self._create_alert(
                "critical", "cpu_usage", 
                f"CPU usage critical: {metrics.cpu_percent:.1f}%"
            )
        elif metrics.cpu_percent > cpu_warning:
            await self._create_alert(
                "warning", "cpu_usage", 
                f"CPU usage high: {metrics.cpu_percent:.1f}%"
            )
        
        # Check Memory threshold
        memory_warning = thresholds.get("memory_usage", {}).get("warning", 75)
        memory_critical = thresholds.get("memory_usage", {}).get("critical", 90)
        
        if metrics.memory_percent > memory_critical:
            await self._create_alert(
                "critical", "memory_usage", 
                f"Memory usage critical: {metrics.memory_percent:.1f}%"
            )
        elif metrics.memory_percent > memory_warning:
            await self._create_alert(
                "warning", "memory_usage", 
                f"Memory usage high: {metrics.memory_percent:.1f}%"
            )
        
        # Check Disk threshold
        disk_warning = thresholds.get("disk_usage", {}).get("warning", 80)
        disk_critical = thresholds.get("disk_usage", {}).get("critical", 95)
        
        if metrics.disk_percent > disk_critical:
            await self._create_alert(
                "critical", "disk_usage", 
                f"Disk usage critical: {metrics.disk_percent:.1f}%"
            )
        elif metrics.disk_percent > disk_warning:
            await self._create_alert(
                "warning", "disk_usage", 
                f"Disk usage high: {metrics.disk_percent:.1f}%"
            )

    async def _trigger_service_alert(self, service_name: str, status: str, health: str):
        """Trigger alert for service issues"""
        message = f"Service {service_name} - Status: {status}, Health: {health}"
        severity = "critical" if status != "running" else "warning"
        
        await self._create_alert(severity, f"service_{service_name}", message)

    async def _create_alert(self, severity: str, source: str, message: str):
        """Create a new alert"""
        alert = Alert(
            severity=severity,
            source=source,
            message=message,
            timestamp=datetime.now()
        )
        
        self.alerts.append(alert)
        self.logger.log(
            logging.CRITICAL if severity == "critical" else 
            logging.WARNING if severity == "warning" else logging.INFO,
            f"ALERT [{severity.upper()}] {source}: {message}"
        )
        
        # Store alert in database
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO alerts (timestamp, severity, source, message)
                VALUES (?, ?, ?, ?)
            """, (alert.timestamp, alert.severity, alert.source, alert.message))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Failed to store alert: {e}")

    async def _route_alert(self, alert: Alert):
        """Route alert to configured channels"""
        alert_channels = self.config.get("capabilities", {}).get(
            "alert_generation_routing", {}
        ).get("alert_channels", [])
        
        for channel in alert_channels:
            try:
                if channel == "console_output":
                    print(f"[{alert.severity.upper()}] {alert.source}: {alert.message}")
                elif channel == "windows_notifications":
                    # Could implement Windows toast notifications here
                    pass
                    
            except Exception as e:
                self.logger.error(f"Failed to route alert to {channel}: {e}")

    async def _scan_log_file(self, log_file: str, error_patterns: List[str]):
        """Scan log file for error patterns"""
        try:
            # Read the last few lines of the log file
            with open(log_file, 'r', errors='ignore') as f:
                lines = f.readlines()
                
            # Check last 10 lines for error patterns
            for line in lines[-10:]:
                for pattern in error_patterns:
                    if pattern.lower() in line.lower():
                        await self._create_alert(
                            "warning",
                            f"log_{Path(log_file).name}",
                            f"Error pattern '{pattern}' found: {line.strip()}"
                        )
                        break
                        
        except Exception as e:
            self.logger.debug(f"Could not scan log file {log_file}: {e}")

    def get_system_status(self) -> Dict[str, Any]:
        """Get current system status summary"""
        latest_metrics = self.system_metrics_history[-1] if self.system_metrics_history else None
        
        return {
            "timestamp": datetime.now().isoformat(),
            "services": {name: {
                "status": svc.status,
                "health": svc.health,
                "uptime": svc.uptime,
                "response_time": svc.response_time
            } for name, svc in self.service_statuses.items()},
            "system_metrics": {
                "cpu_percent": latest_metrics.cpu_percent if latest_metrics else 0,
                "memory_percent": latest_metrics.memory_percent if latest_metrics else 0,
                "disk_percent": latest_metrics.disk_percent if latest_metrics else 0,
                "process_count": latest_metrics.process_count if latest_metrics else 0
            } if latest_metrics else {},
            "active_alerts": len([a for a in self.alerts if not a.resolved]),
            "total_alerts": len(self.alerts)
        }

    async def stop_monitoring(self):
        """Stop all monitoring tasks"""
        self.running = False
        self.logger.info("NEXUS System Monitor stopped")

async def main():
    """Main entry point"""
    # Change to the NEXUS-RSI directory
    os.chdir("C:/Users/Jean-SamuelLeboeuf/NEXUS-RSI")
    
    monitor = SystemMonitor()
    
    try:
        await monitor.start_monitoring()
    except KeyboardInterrupt:
        print("\nShutting down System Monitor...")
        await monitor.stop_monitoring()
    except Exception as e:
        monitor.logger.error(f"System Monitor crashed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())