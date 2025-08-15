# NEXUS System Monitor Agent

## Overview

The NEXUS System Monitor Agent is a specialized real-time monitoring and alerting system designed specifically for the NEXUS-RSI infrastructure. It provides comprehensive monitoring of services, resources, and system health with automated recovery capabilities.

## Features

### Core Monitoring Capabilities
- **Service Health Monitoring**: Ollama, Neo4j, Temporal, Docker, Grafana, Prometheus
- **GitHub Actions Integration**: Workflow status tracking and failure detection
- **Resource Utilization**: CPU, Memory, Disk, Network, GPU monitoring
- **Error Detection**: Log parsing, pattern recognition, cascade failure prevention
- **Uptime Tracking**: SLA monitoring, availability reporting, MTTR/MTBF calculation

### Advanced Features
- **Auto-Recovery**: Automatic service restart and resource cleanup
- **Alert Management**: Multi-channel alerting with severity-based routing
- **Metric Storage**: SQLite database with configurable retention policies
- **Performance Optimization**: Low-overhead monitoring with adaptive sampling
- **Dashboard Integration**: Grafana dashboard support and custom visualizations

## Architecture

```
NEXUS System Monitor
├── Configuration (system_monitor.json)
├── Core Engine (system_monitor.py)
├── Setup Tools (setup_system_monitor.py)
├── PowerShell Integration (system_monitor_tools.ps1)
└── Database (nexus_metrics.db)
```

## Installation

### Quick Setup

1. **Install Dependencies**:
   ```bash
   python agents/setup_system_monitor.py
   ```

2. **PowerShell Installation** (Recommended):
   ```powershell
   .\agents\system_monitor_tools.ps1 -Action install
   ```

### Manual Installation

1. **Install Python Packages**:
   ```bash
   pip install psutil>=5.9.0 docker>=6.0.0 requests>=2.28.0 watchdog>=2.1.0
   ```

2. **Create Directories**:
   ```bash
   mkdir logs\system_monitor
   mkdir backups\system_monitor
   mkdir data\system_monitor
   ```

3. **Initialize Database**:
   ```bash
   python agents/system_monitor.py --init-db
   ```

## Configuration

The system monitor is configured via `agents/system_monitor.json`:

### Key Configuration Sections

#### Service Health Monitoring
```json
{
  "primary_focus": {
    "service_health_monitoring": {
      "services": ["ollama", "neo4j", "temporal", "grafana", "prometheus"],
      "health_check_interval": 30,
      "failure_detection_timeout": 60
    }
  }
}
```

#### Resource Thresholds
```json
{
  "triggers": {
    "resource_threshold_triggers": {
      "cpu_usage": { "warning": 70, "critical": 85 },
      "memory_usage": { "warning": 75, "critical": 90 },
      "disk_usage": { "warning": 80, "critical": 95 }
    }
  }
}
```

#### Alert Configuration
```json
{
  "capabilities": {
    "alert_generation_routing": {
      "alert_channels": ["console_output", "log_file", "prometheus_alertmanager"],
      "alert_rules": {
        "service_down": { "severity": "critical", "cooldown": 300 },
        "high_resource_usage": { "severity": "warning", "cooldown": 600 }
      }
    }
  }
}
```

## Usage

### Starting the Monitor

#### Command Line
```bash
python agents/system_monitor.py
```

#### Background Service
```bash
# Windows
start_system_monitor.bat

# PowerShell
.\agents\system_monitor_tools.ps1 -Action start
```

#### Windows Service (Requires Admin)
```powershell
.\agents\system_monitor_tools.ps1 -Action service
.\agents\system_monitor_tools.ps1 -Action start -AsService
```

### Monitoring Operations

#### Check Status
```powershell
.\agents\system_monitor_tools.ps1 -Action status
```

#### View Logs
```powershell
.\agents\system_monitor_tools.ps1 -Action logs
```

#### Stop Monitor
```powershell
.\agents\system_monitor_tools.ps1 -Action stop
```

## Monitoring Capabilities

### Docker Container Health
- Monitors all NEXUS-RSI Docker containers
- Tracks container status, health checks, and resource usage
- Automatic restart on failure (configurable)

### Service Endpoint Monitoring
```
Ollama:     http://localhost:11434/api/version
Neo4j:      http://localhost:7474/db/data/
Temporal:   http://localhost:8088/health
Grafana:    http://localhost:3000/api/health
Prometheus: http://localhost:9090/-/healthy
```

### System Resource Tracking
- **CPU Usage**: Real-time percentage and load average
- **Memory Usage**: Available, used, and swap statistics
- **Disk Usage**: Free space and I/O metrics
- **Network Usage**: Bytes sent/received and connection counts
- **Process Monitoring**: NEXUS-specific process health

### Log File Analysis
Monitors logs from:
- `C:\Users\Jean-SamuelLeboeuf\AppData\Local\Ollama\*.log`
- `C:\Users\Jean-SamuelLeboeuf\NEXUS-RSI\*.log`
- Docker container logs
- Windows Event Logs

## Alert System

### Alert Severity Levels
- **Critical**: Service down, system failure
- **Major**: Performance degradation, error rate spike
- **Warning**: Resource threshold exceeded
- **Minor**: General notices, maintenance

### Alert Channels
- Console output with colored formatting
- Log file storage with rotation
- Windows toast notifications
- Prometheus AlertManager integration
- Grafana annotation support

### Auto-Recovery Actions
1. **Service Restart**: Docker containers and processes
2. **Resource Cleanup**: Memory, temporary files, logs
3. **Dependency Validation**: Network, ports, file access
4. **Recovery Verification**: Post-recovery health checks

## Database Schema

### System Metrics Table
```sql
CREATE TABLE system_metrics (
    id INTEGER PRIMARY KEY,
    timestamp DATETIME,
    cpu_percent REAL,
    memory_percent REAL,
    disk_percent REAL,
    network_sent INTEGER,
    network_recv INTEGER,
    process_count INTEGER
);
```

### Service Status Table
```sql
CREATE TABLE service_status (
    id INTEGER PRIMARY KEY,
    timestamp DATETIME,
    service_name TEXT,
    status TEXT,
    health TEXT,
    uptime REAL,
    error_count INTEGER,
    response_time REAL
);
```

### Alerts Table
```sql
CREATE TABLE alerts (
    id INTEGER PRIMARY KEY,
    timestamp DATETIME,
    severity TEXT,
    source TEXT,
    message TEXT,
    acknowledged INTEGER DEFAULT 0,
    resolved INTEGER DEFAULT 0
);
```

## Integration

### Grafana Dashboard
- Custom NEXUS System Overview dashboard
- Real-time metric visualization
- Alert annotation support
- Historical trend analysis

### GitHub Actions Monitoring
- Webhook integration for workflow status
- Build failure detection and notification
- Deployment pipeline monitoring
- Automatic issue creation on failures

### Prometheus Integration
- Metrics export in Prometheus format
- AlertManager rule integration
- Custom metric definitions
- Historical data queries

## Performance Optimization

### Low Overhead Design
- **Maximum CPU Usage**: 5%
- **Maximum Memory Usage**: 256MB
- **Adaptive Sampling**: Reduces frequency under low activity
- **Batch Processing**: Efficient database operations
- **Async Operations**: Non-blocking monitoring tasks

### Data Management
- **Retention Policies**: Configurable data cleanup
- **Compression**: Automatic log and metric compression
- **Indexing**: Optimized database queries
- **Archival**: Long-term storage strategies

## Troubleshooting

### Common Issues

#### Monitor Won't Start
```bash
# Check dependencies
python -c "import psutil, docker, requests"

# Check configuration
python -c "import json; json.load(open('agents/system_monitor.json'))"

# Check permissions
python agents/system_monitor.py --test
```

#### Docker Access Issues
```bash
# Verify Docker daemon
docker version

# Check user permissions
docker ps

# Restart Docker service if needed
```

#### High Resource Usage
```bash
# Check monitor configuration
# Increase sampling intervals in system_monitor.json
# Reduce retention periods
# Enable compression
```

### Log Analysis
Monitor logs are stored in:
- `logs/system_monitor/system_monitor.log`
- Windows Event Viewer (when run as service)
- Console output (when run interactively)

### Database Maintenance
```bash
# Check database size
ls -la nexus_metrics.db

# Manual cleanup (if needed)
sqlite3 nexus_metrics.db "DELETE FROM system_metrics WHERE timestamp < datetime('now', '-30 days');"

# Vacuum database
sqlite3 nexus_metrics.db "VACUUM;"
```

## API Reference

### SystemMonitor Class Methods

#### get_system_status()
Returns current system status summary including services, metrics, and alerts.

#### start_monitoring()
Begins all monitoring tasks asynchronously.

#### stop_monitoring()
Gracefully stops all monitoring tasks.

### Configuration Options

#### Model Settings
```json
{
  "agent_settings": {
    "model_temperature": 0.1,
    "max_tokens": 2000,
    "timeout_seconds": 120
  }
}
```

#### Safety Settings
```json
{
  "safety_settings": {
    "auto_recovery_enabled": true,
    "max_recovery_attempts": 3,
    "human_approval_required": false
  }
}
```

## Support

For issues and questions:
1. Check the logs: `logs/system_monitor/system_monitor.log`
2. Review configuration: `agents/system_monitor.json`
3. Test connectivity: `python agents/system_monitor.py --test`
4. Check resource usage: Task Manager or `psutil`

## Version History

- **v1.0.0**: Initial release with core monitoring capabilities
  - Service health monitoring
  - Resource utilization tracking
  - Basic alert system
  - Docker integration
  - SQLite metrics storage