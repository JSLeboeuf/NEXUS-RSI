#!/usr/bin/env python
"""
NEXUS-RSI Launcher
Lance tous les composants du système en parallèle
"""

import asyncio
import subprocess
import sys
import time
from pathlib import Path
import json
import threading
import webbrowser
from datetime import datetime

class NexusLauncher:
    def __init__(self):
        self.processes = {}
        self.running = False
        self.config = self._load_config()
        
    def _load_config(self):
        config_path = Path("config/nexus_config.json")
        if config_path.exists():
            with open(config_path) as f:
                return json.load(f)
        return {}
    
    def start_dashboard(self):
        """Lance le dashboard Streamlit"""
        print("Starting Dashboard...")
        cmd = [sys.executable, "-m", "streamlit", "run", "nexus_dashboard.py", 
               "--server.port", str(self.config['monitoring']['dashboard_port']),
               "--server.headless", "true"]
        self.processes['dashboard'] = subprocess.Popen(cmd)
        time.sleep(3)
        webbrowser.open(f"http://localhost:{self.config['monitoring']['dashboard_port']}")
        print(f"[OK] Dashboard running at http://localhost:{self.config['monitoring']['dashboard_port']}")
    
    def start_core(self):
        """Lance le système core"""
        print("Starting NEXUS Core...")
        cmd = [sys.executable, "nexus_core.py"]
        self.processes['core'] = subprocess.Popen(cmd)
        print("[OK] Core system started")
    
    def start_scraper(self):
        """Lance le scraper multi-source"""
        print("Starting Multi-Source Scraper...")
        cmd = [sys.executable, "scrapers/multi_source_scraper.py"]
        self.processes['scraper'] = subprocess.Popen(cmd)
        print("[OK] Scraper started")
    
    def start_monitoring(self):
        """Lance le monitoring en background"""
        def monitor():
            while self.running:
                # Check process health
                for name, proc in self.processes.items():
                    if proc and proc.poll() is not None:
                        print(f"[WARNING] Process {name} crashed! Restarting...")
                        self.restart_process(name)
                time.sleep(30)
        
        self.running = True
        threading.Thread(target=monitor, daemon=True).start()
        print("[OK] Monitoring started")
    
    def restart_process(self, name):
        """Redémarre un processus"""
        if name == 'dashboard':
            self.start_dashboard()
        elif name == 'core':
            self.start_core()
        elif name == 'scraper':
            self.start_scraper()
    
    def show_status(self):
        """Affiche le statut du système"""
        print("\n" + "="*60)
        print("NEXUS-RSI SYSTEM STATUS")
        print("="*60)
        print(f"Time: {datetime.now():%Y-%m-%d %H:%M:%S}")
        print(f"Mode: {self.config['system']['mode']}")
        print(f"Auto-Approve: {self.config['system']['auto_approve']}")
        print(f"Parallel Agents: {self.config['performance']['parallel_agents']}")
        print("\nComponents:")
        
        for name, proc in self.processes.items():
            if proc and proc.poll() is None:
                print(f"  [OK] {name}: Running (PID: {proc.pid})")
            else:
                print(f"  [FAIL] {name}: Stopped")
        
        print("\nAccess Points:")
        print(f"  Dashboard: http://localhost:{self.config['monitoring']['dashboard_port']}")
        print(f"  Logs: ./proofs/")
        print(f"  Config: ./config/nexus_config.json")
        print("="*60 + "\n")
    
    async def launch_all(self):
        """Lance tous les composants"""
        print("""
==============================================================
                    NEXUS-RSI LAUNCHER
           Hyperfast Iteration & Auto-Improvement
==============================================================
        """)
        
        # Create necessary directories
        for dir_name in ['proofs', 'config', 'agents', 'workflows', 'monitoring', 'scrapers/cache']:
            Path(dir_name).mkdir(exist_ok=True, parents=True)
        
        # Start components
        self.start_core()
        await asyncio.sleep(2)
        
        self.start_dashboard()
        await asyncio.sleep(2)
        
        self.start_scraper()
        await asyncio.sleep(2)
        
        self.start_monitoring()
        
        # Show status
        self.show_status()
        
        print("\n[SUCCESS] NEXUS-RSI is now running!")
        print("Press Ctrl+C to stop all components\n")
        
        # Keep running
        try:
            while True:
                await asyncio.sleep(60)
                self.show_status()
        except KeyboardInterrupt:
            self.shutdown()
    
    def shutdown(self):
        """Arrête tous les composants"""
        print("\n[SHUTDOWN] Shutting down NEXUS-RSI...")
        self.running = False
        
        for name, proc in self.processes.items():
            if proc and proc.poll() is None:
                print(f"  Stopping {name}...")
                proc.terminate()
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill()
        
        print("[OK] NEXUS-RSI stopped successfully")
        sys.exit(0)


def main():
    launcher = NexusLauncher()
    
    try:
        asyncio.run(launcher.launch_all())
    except KeyboardInterrupt:
        launcher.shutdown()


if __name__ == "__main__":
    main()