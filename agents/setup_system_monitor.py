#!/usr/bin/env python3
"""
Setup script for NEXUS System Monitor Agent
Installs dependencies and configures the monitoring system
"""

import os
import sys
import subprocess
import json
import sqlite3
from pathlib import Path

def install_dependencies():
    """Install required Python packages"""
    packages = [
        "psutil>=5.9.0",
        "docker>=6.0.0", 
        "requests>=2.28.0",
        "asyncio",
        "watchdog>=2.1.0"
    ]
    
    print("Installing system monitor dependencies...")
    for package in packages:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print(f"✓ Installed {package}")
        except subprocess.CalledProcessError as e:
            print(f"✗ Failed to install {package}: {e}")
            return False
    
    return True

def setup_directories():
    """Create necessary directories"""
    directories = [
        "logs/system_monitor",
        "backups/system_monitor",
        "data/system_monitor"
    ]
    
    print("Creating directories...")
    for directory in directories:
        try:
            Path(directory).mkdir(parents=True, exist_ok=True)
            print(f"✓ Created directory: {directory}")
        except Exception as e:
            print(f"✗ Failed to create directory {directory}: {e}")
            return False
    
    return True

def initialize_database():
    """Initialize the monitoring database"""
    print("Initializing monitoring database...")
    
    try:
        # Import the SystemMonitor class to use its database initialization
        sys.path.append(str(Path(__file__).parent))
        from system_monitor import SystemMonitor
        
        monitor = SystemMonitor()
        print("✓ Database initialized successfully")
        return True
        
    except Exception as e:
        print(f"✗ Failed to initialize database: {e}")
        return False

def verify_docker_access():
    """Verify Docker daemon is accessible"""
    print("Verifying Docker access...")
    
    try:
        import docker
        client = docker.from_env()
        client.ping()
        print("✓ Docker daemon is accessible")
        return True
    except Exception as e:
        print(f"⚠ Docker access verification failed: {e}")
        print("  System monitoring will continue without Docker container monitoring")
        return True  # Non-critical failure

def create_startup_script():
    """Create Windows batch file to start the system monitor"""
    startup_script = """@echo off
echo Starting NEXUS System Monitor...
cd /d "C:\\Users\\Jean-SamuelLeboeuf\\NEXUS-RSI"
python agents/system_monitor.py
pause
"""
    
    try:
        with open("start_system_monitor.bat", "w") as f:
            f.write(startup_script)
        print("✓ Created startup script: start_system_monitor.bat")
        return True
    except Exception as e:
        print(f"✗ Failed to create startup script: {e}")
        return False

def create_service_registration():
    """Create a service registration for Windows Task Scheduler"""
    service_xml = f"""<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.4" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo>
    <Date>2025-08-15T00:00:00</Date>
    <Author>NEXUS-RSI System</Author>
    <Description>NEXUS System Monitor Agent - Real-time system monitoring</Description>
  </RegistrationInfo>
  <Triggers>
    <BootTrigger>
      <Enabled>true</Enabled>
    </BootTrigger>
  </Triggers>
  <Principals>
    <Principal id="Author">
      <UserId>S-1-5-18</UserId>
      <RunLevel>HighestAvailable</RunLevel>
    </Principal>
  </Principals>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <AllowHardTerminate>true</AllowHardTerminate>
    <StartWhenAvailable>true</StartWhenAvailable>
    <RunOnlyIfNetworkAvailable>false</RunOnlyIfNetworkAvailable>
    <IdleSettings>
      <StopOnIdleEnd>false</StopOnIdleEnd>
      <RestartOnIdle>false</RestartOnIdle>
    </IdleSettings>
    <AllowStartOnDemand>true</AllowStartOnDemand>
    <Enabled>true</Enabled>
    <Hidden>false</Hidden>
    <RunOnlyIfIdle>false</RunOnlyIfIdle>
    <DisallowStartOnRemoteAppSession>false</DisallowStartOnRemoteAppSession>
    <UseUnifiedSchedulingEngine>true</UseUnifiedSchedulingEngine>
    <WakeToRun>false</WakeToRun>
    <ExecutionTimeLimit>PT0S</ExecutionTimeLimit>
    <Priority>7</Priority>
    <RestartOnFailure>
      <Interval>PT1M</Interval>
      <Count>3</Count>
    </RestartOnFailure>
  </Settings>
  <Actions Context="Author">
    <Exec>
      <Command>{sys.executable}</Command>
      <Arguments>agents/system_monitor.py</Arguments>
      <WorkingDirectory>C:\\Users\\Jean-SamuelLeboeuf\\NEXUS-RSI</WorkingDirectory>
    </Exec>
  </Actions>
</Task>"""

    try:
        with open("nexus_system_monitor_service.xml", "w") as f:
            f.write(service_xml)
        print("✓ Created service definition: nexus_system_monitor_service.xml")
        print("  To install as Windows service, run as administrator:")
        print("  schtasks /create /xml nexus_system_monitor_service.xml /tn \"NEXUS System Monitor\"")
        return True
    except Exception as e:
        print(f"✗ Failed to create service definition: {e}")
        return False

def test_system_monitor():
    """Test the system monitor functionality"""
    print("Testing system monitor...")
    
    try:
        sys.path.append(str(Path(__file__).parent))
        from system_monitor import SystemMonitor
        
        monitor = SystemMonitor()
        status = monitor.get_system_status()
        
        print("✓ System monitor test successful")
        print(f"  Current CPU: {status['system_metrics'].get('cpu_percent', 'N/A')}%")
        print(f"  Current Memory: {status['system_metrics'].get('memory_percent', 'N/A')}%")
        print(f"  Active Services: {len(status['services'])}")
        
        return True
        
    except Exception as e:
        print(f"✗ System monitor test failed: {e}")
        return False

def main():
    """Main setup function"""
    print("=== NEXUS System Monitor Setup ===")
    print()
    
    # Change to NEXUS-RSI directory
    try:
        os.chdir("C:/Users/Jean-SamuelLeboeuf/NEXUS-RSI")
        print("✓ Changed to NEXUS-RSI directory")
    except Exception as e:
        print(f"✗ Failed to change to NEXUS-RSI directory: {e}")
        return False
    
    setup_steps = [
        ("Installing dependencies", install_dependencies),
        ("Setting up directories", setup_directories),
        ("Initializing database", initialize_database),
        ("Verifying Docker access", verify_docker_access),
        ("Creating startup script", create_startup_script),
        ("Creating service registration", create_service_registration),
        ("Testing system monitor", test_system_monitor)
    ]
    
    failed_steps = []
    
    for step_name, step_function in setup_steps:
        print(f"\n{step_name}...")
        try:
            if not step_function():
                failed_steps.append(step_name)
        except Exception as e:
            print(f"✗ {step_name} failed with exception: {e}")
            failed_steps.append(step_name)
    
    print("\n=== Setup Summary ===")
    if not failed_steps:
        print("✓ All setup steps completed successfully!")
        print("\nNext steps:")
        print("1. Start the system monitor: python agents/system_monitor.py")
        print("2. Or use the batch file: start_system_monitor.bat")
        print("3. Monitor logs in: logs/system_monitor/")
        print("4. View metrics in: nexus_metrics.db")
        print("\nOptional:")
        print("5. Install as Windows service (run as administrator):")
        print("   schtasks /create /xml nexus_system_monitor_service.xml /tn \"NEXUS System Monitor\"")
    else:
        print(f"✗ {len(failed_steps)} setup steps failed:")
        for step in failed_steps:
            print(f"  - {step}")
        print("\nPlease resolve the issues and run setup again.")
    
    return len(failed_steps) == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)