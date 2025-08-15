#!/usr/bin/env python3
"""
NEXUS System Monitor Initialization Script
Integrates the system monitor with the existing NEXUS-RSI system
"""

import os
import sys
import json
import sqlite3
import asyncio
from pathlib import Path
from datetime import datetime

# Add the NEXUS-RSI root to the path
sys.path.append(str(Path(__file__).parent.parent))

def update_nexus_config():
    """Update the main NEXUS configuration to include system monitor"""
    config_path = "config/nexus_config.json"
    
    try:
        with open(config_path, 'r') as f:
            nexus_config = json.load(f)
        
        # Add system monitor agent configuration
        if "agents" not in nexus_config:
            nexus_config["agents"] = {}
        
        nexus_config["agents"]["system_monitor"] = {
            "enabled": True,
            "model": "haiku",
            "temperature": 0.1,
            "max_tokens": 2000,
            "auto_start": True,
            "monitoring_interval": 30,
            "alert_level": "warning"
        }
        
        # Add monitoring configuration
        if "monitoring" not in nexus_config:
            nexus_config["monitoring"] = {}
        
        nexus_config["monitoring"].update({
            "system_monitor_enabled": True,
            "metrics_retention_days": 30,
            "alert_webhooks": [],
            "performance_thresholds": {
                "cpu_warning": 70,
                "cpu_critical": 85,
                "memory_warning": 75,
                "memory_critical": 90,
                "disk_warning": 80,
                "disk_critical": 95
            }
        })
        
        # Save updated configuration
        with open(config_path, 'w') as f:
            json.dump(nexus_config, f, indent=2)
        
        print(f"✓ Updated NEXUS configuration: {config_path}")
        return True
        
    except Exception as e:
        print(f"✗ Failed to update NEXUS configuration: {e}")
        return False

def create_grafana_dashboard():
    """Create Grafana dashboard configuration for system monitor"""
    dashboard_config = {
        "dashboard": {
            "id": None,
            "title": "NEXUS System Monitor",
            "tags": ["nexus", "monitoring", "system"],
            "timezone": "browser",
            "panels": [
                {
                    "id": 1,
                    "title": "System Overview",
                    "type": "stat",
                    "targets": [
                        {
                            "expr": "cpu_percent",
                            "legendFormat": "CPU %"
                        },
                        {
                            "expr": "memory_percent", 
                            "legendFormat": "Memory %"
                        },
                        {
                            "expr": "disk_percent",
                            "legendFormat": "Disk %"
                        }
                    ],
                    "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0}
                },
                {
                    "id": 2,
                    "title": "Service Health",
                    "type": "table",
                    "targets": [
                        {
                            "query": "SELECT service_name, status, health, uptime FROM service_status ORDER BY timestamp DESC LIMIT 10"
                        }
                    ],
                    "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0}
                },
                {
                    "id": 3,
                    "title": "Resource Usage Trends",
                    "type": "graph",
                    "targets": [
                        {
                            "query": "SELECT timestamp, cpu_percent, memory_percent, disk_percent FROM system_metrics WHERE timestamp > datetime('now', '-24 hours')"
                        }
                    ],
                    "gridPos": {"h": 8, "w": 24, "x": 0, "y": 8}
                },
                {
                    "id": 4,
                    "title": "Active Alerts",
                    "type": "logs",
                    "targets": [
                        {
                            "query": "SELECT timestamp, severity, source, message FROM alerts WHERE resolved = 0 ORDER BY timestamp DESC"
                        }
                    ],
                    "gridPos": {"h": 8, "w": 24, "x": 0, "y": 16}
                }
            ],
            "time": {
                "from": "now-24h",
                "to": "now"
            },
            "refresh": "5s"
        }
    }
    
    try:
        dashboard_path = "config/grafana_dashboard_system_monitor.json"
        with open(dashboard_path, 'w') as f:
            json.dump(dashboard_config, f, indent=2)
        
        print(f"✓ Created Grafana dashboard configuration: {dashboard_path}")
        return True
        
    except Exception as e:
        print(f"✗ Failed to create Grafana dashboard: {e}")
        return False

def create_prometheus_config():
    """Create Prometheus configuration for system monitor metrics"""
    prometheus_config = {
        "global": {
            "scrape_interval": "15s"
        },
        "scrape_configs": [
            {
                "job_name": "nexus-system-monitor",
                "static_configs": [
                    {
                        "targets": ["localhost:8502"]
                    }
                ],
                "scrape_interval": "30s",
                "metrics_path": "/metrics"
            }
        ],
        "rule_files": [
            "alert_rules_system_monitor.yml"
        ],
        "alerting": {
            "alertmanagers": [
                {
                    "static_configs": [
                        {
                            "targets": ["localhost:9093"]
                        }
                    ]
                }
            ]
        }
    }
    
    try:
        config_path = "config/prometheus_system_monitor.yml"
        import yaml
        with open(config_path, 'w') as f:
            yaml.dump(prometheus_config, f, default_flow_style=False)
        
        print(f"✓ Created Prometheus configuration: {config_path}")
        return True
        
    except Exception as e:
        print(f"✗ Failed to create Prometheus configuration: {e}")
        return False

def create_alert_rules():
    """Create Prometheus alert rules for system monitor"""
    alert_rules = {
        "groups": [
            {
                "name": "nexus_system_monitor",
                "rules": [
                    {
                        "alert": "HighCPUUsage",
                        "expr": "cpu_percent > 85",
                        "for": "5m",
                        "labels": {
                            "severity": "critical"
                        },
                        "annotations": {
                            "summary": "High CPU usage detected",
                            "description": "CPU usage is above 85% for more than 5 minutes"
                        }
                    },
                    {
                        "alert": "HighMemoryUsage", 
                        "expr": "memory_percent > 90",
                        "for": "5m",
                        "labels": {
                            "severity": "critical"
                        },
                        "annotations": {
                            "summary": "High memory usage detected",
                            "description": "Memory usage is above 90% for more than 5 minutes"
                        }
                    },
                    {
                        "alert": "ServiceDown",
                        "expr": "service_status != 'running'",
                        "for": "1m",
                        "labels": {
                            "severity": "critical"
                        },
                        "annotations": {
                            "summary": "Service is down",
                            "description": "NEXUS service {{ $labels.service_name }} is not running"
                        }
                    },
                    {
                        "alert": "DiskSpaceLow",
                        "expr": "disk_percent > 90",
                        "for": "10m",
                        "labels": {
                            "severity": "warning"
                        },
                        "annotations": {
                            "summary": "Disk space is low",
                            "description": "Disk usage is above 90%"
                        }
                    }
                ]
            }
        ]
    }
    
    try:
        rules_path = "config/alert_rules_system_monitor.yml"
        import yaml
        with open(rules_path, 'w') as f:
            yaml.dump(alert_rules, f, default_flow_style=False)
        
        print(f"✓ Created alert rules: {rules_path}")
        return True
        
    except Exception as e:
        print(f"✗ Failed to create alert rules: {e}")
        return False

def update_docker_compose():
    """Update docker-compose.yml to include system monitor metrics endpoint"""
    compose_path = "docker-compose.yml"
    
    try:
        with open(compose_path, 'r') as f:
            compose_content = f.read()
        
        # Add system monitor metrics service if not already present
        if "nexus-system-monitor" not in compose_content:
            monitor_service = """
  # NEXUS System Monitor Metrics
  nexus-system-monitor:
    build:
      context: .
      dockerfile: Dockerfile.monitor
    ports:
      - "8502:8502"  # Metrics endpoint
    volumes:
      - ./nexus_metrics.db:/app/nexus_metrics.db
      - ./logs:/app/logs
    environment:
      - NEXUS_ENV=production
      - MONITOR_PORT=8502
    networks:
      - nexus_network
    restart: unless-stopped
    depends_on:
      - prometheus
      - grafana
"""
            
            # Insert before the networks section
            networks_index = compose_content.find("\nnetworks:")
            if networks_index != -1:
                compose_content = (
                    compose_content[:networks_index] + 
                    monitor_service + 
                    compose_content[networks_index:]
                )
                
                with open(compose_path, 'w') as f:
                    f.write(compose_content)
                
                print(f"✓ Updated docker-compose.yml with system monitor service")
                return True
        else:
            print(f"✓ System monitor service already exists in docker-compose.yml")
            return True
            
    except Exception as e:
        print(f"✗ Failed to update docker-compose.yml: {e}")
        return False

def create_dockerfile_monitor():
    """Create Dockerfile for system monitor container"""
    dockerfile_content = """FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    procps \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install additional monitoring dependencies
RUN pip install --no-cache-dir \\
    psutil>=5.9.0 \\
    docker>=6.0.0 \\
    requests>=2.28.0 \\
    watchdog>=2.1.0 \\
    prometheus-client>=0.14.0

# Copy application files
COPY agents/system_monitor.py agents/
COPY agents/system_monitor.json agents/
COPY nexus_metrics.db ./

# Create log directory
RUN mkdir -p logs/system_monitor

# Expose metrics port
EXPOSE 8502

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
    CMD curl -f http://localhost:8502/health || exit 1

# Run system monitor
CMD ["python", "agents/system_monitor.py", "--metrics-port", "8502"]
"""
    
    try:
        with open("Dockerfile.monitor", 'w') as f:
            f.write(dockerfile_content)
        
        print(f"✓ Created Dockerfile.monitor")
        return True
        
    except Exception as e:
        print(f"✗ Failed to create Dockerfile.monitor: {e}")
        return False

def initialize_database_schema():
    """Initialize additional database tables for integration"""
    try:
        conn = sqlite3.connect("nexus_metrics.db")
        cursor = conn.cursor()
        
        # Create integration tables
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS github_workflows (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME,
                workflow_name TEXT,
                status TEXT,
                run_id TEXT,
                conclusion TEXT,
                duration INTEGER
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS performance_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME,
                component TEXT,
                metric_name TEXT,
                metric_value REAL,
                unit TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS recovery_actions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME,
                action_type TEXT,
                target_service TEXT,
                success INTEGER,
                details TEXT
            )
        """)
        
        # Create indexes for better performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_system_metrics_timestamp ON system_metrics(timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_service_status_service ON service_status(service_name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_alerts_severity ON alerts(severity)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_github_workflows_status ON github_workflows(status)")
        
        conn.commit()
        conn.close()
        
        print(f"✓ Initialized extended database schema")
        return True
        
    except Exception as e:
        print(f"✗ Failed to initialize database schema: {e}")
        return False

def create_startup_integration():
    """Create startup script integration with existing NEXUS system"""
    startup_script = """#!/usr/bin/env python3
\"\"\"
NEXUS-RSI Startup with System Monitor Integration
\"\"\"

import asyncio
import subprocess
import sys
import time
from pathlib import Path

async def start_system_monitor():
    \"\"\"Start the system monitor in background\"\"\"
    try:
        print("Starting NEXUS System Monitor...")
        monitor_process = subprocess.Popen([
            sys.executable, "agents/system_monitor.py"
        ], cwd=Path(__file__).parent)
        
        # Give it time to initialize
        await asyncio.sleep(3)
        
        # Check if it's still running
        if monitor_process.poll() is None:
            print(f"✓ System Monitor started (PID: {monitor_process.pid})")
            return monitor_process
        else:
            print("✗ System Monitor failed to start")
            return None
            
    except Exception as e:
        print(f"✗ Failed to start System Monitor: {e}")
        return None

async def start_nexus_core():
    \"\"\"Start the main NEXUS-RSI system\"\"\"
    try:
        print("Starting NEXUS Core...")
        from nexus_core import main as nexus_main
        await nexus_main()
    except Exception as e:
        print(f"✗ Failed to start NEXUS Core: {e}")

async def main():
    \"\"\"Main startup function\"\"\"
    print("=== NEXUS-RSI System Startup ===")
    
    # Start system monitor first
    monitor_process = await start_system_monitor()
    
    # Start the main NEXUS system
    try:
        await start_nexus_core()
    except KeyboardInterrupt:
        print("\\nShutting down NEXUS-RSI...")
        if monitor_process and monitor_process.poll() is None:
            monitor_process.terminate()
            print("✓ System Monitor stopped")
    except Exception as e:
        print(f"✗ NEXUS-RSI startup failed: {e}")
        if monitor_process and monitor_process.poll() is None:
            monitor_process.terminate()

if __name__ == "__main__":
    asyncio.run(main())
"""
    
    try:
        with open("launch_nexus_with_monitor.py", 'w') as f:
            f.write(startup_script)
        
        print(f"✓ Created integrated startup script: launch_nexus_with_monitor.py")
        return True
        
    except Exception as e:
        print(f"✗ Failed to create startup script: {e}")
        return False

def main():
    """Main initialization function"""
    print("=== NEXUS System Monitor Integration ===")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print()
    
    # Change to NEXUS-RSI directory
    try:
        os.chdir("C:/Users/Jean-SamuelLeboeuf/NEXUS-RSI")
        print("✓ Changed to NEXUS-RSI directory")
    except Exception as e:
        print(f"✗ Failed to change to NEXUS-RSI directory: {e}")
        return False
    
    # Run initialization steps
    initialization_steps = [
        ("Updating NEXUS configuration", update_nexus_config),
        ("Creating Grafana dashboard", create_grafana_dashboard),
        ("Creating Prometheus configuration", create_prometheus_config),
        ("Creating alert rules", create_alert_rules),
        ("Updating Docker Compose", update_docker_compose),
        ("Creating monitor Dockerfile", create_dockerfile_monitor),
        ("Initializing database schema", initialize_database_schema),
        ("Creating startup integration", create_startup_integration)
    ]
    
    failed_steps = []
    
    for step_name, step_function in initialization_steps:
        print(f"\\n{step_name}...")
        try:
            if not step_function():
                failed_steps.append(step_name)
        except Exception as e:
            print(f"✗ {step_name} failed with exception: {e}")
            failed_steps.append(step_name)
    
    print("\\n=== Integration Summary ===")
    if not failed_steps:
        print("✓ All integration steps completed successfully!")
        print("\\nNext steps:")
        print("1. Start the integrated system: python launch_nexus_with_monitor.py")
        print("2. Or start monitor separately: python agents/system_monitor.py")
        print("3. Access Grafana dashboard: http://localhost:3000")
        print("4. View Prometheus metrics: http://localhost:9090")
        print("5. Monitor logs: logs/system_monitor/")
        print("\\nSystem Monitor Features:")
        print("- Real-time service health monitoring")
        print("- Resource utilization tracking")
        print("- Automated alert generation")
        print("- Auto-recovery mechanisms")
        print("- GitHub Actions integration")
        print("- Grafana dashboard integration")
    else:
        print(f"✗ {len(failed_steps)} integration steps failed:")
        for step in failed_steps:
            print(f"  - {step}")
        print("\\nPlease resolve the issues and run initialization again.")
    
    return len(failed_steps) == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)