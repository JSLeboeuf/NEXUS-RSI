"""
Initialization script for NEXUS Security Analyzer Agent
Integrates with the NEXUS-RSI system for automated security monitoring
"""

import asyncio
import json
import sys
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from security_analyzer import SecurityAnalyzer


class SecurityAnalyzerAgent:
    """NEXUS Security Analyzer Agent for automated security monitoring"""
    
    def __init__(self, config_path: str = None):
        self.config_path = config_path or Path(__file__).parent / "security_analyzer.json"
        self.analyzer = SecurityAnalyzer(str(self.config_path))
        self.logger = self._setup_logging()
        self.is_running = False
        self.last_scan_time = None
        
    def _setup_logging(self) -> logging.Logger:
        """Setup logging for the agent"""
        logger = logging.getLogger("nexus_security_agent")
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            # Console handler
            console_handler = logging.StreamHandler()
            console_formatter = logging.Formatter(
                '%(asctime)s - SECURITY - %(levelname)s - %(message)s'
            )
            console_handler.setFormatter(console_formatter)
            logger.addHandler(console_handler)
            
            # File handler
            log_file = Path("logs") / "security_agent.log"
            log_file.parent.mkdir(exist_ok=True)
            
            file_handler = logging.FileHandler(log_file)
            file_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)
        
        return logger

    async def start(self):
        """Start the security analyzer agent"""
        self.logger.info("🔒 Starting NEXUS Security Analyzer Agent...")
        self.is_running = True
        
        try:
            # Initial security scan
            await self.run_security_scan()
            
            # Start monitoring loop
            await self._monitoring_loop()
            
        except Exception as e:
            self.logger.error(f"❌ Security agent failed to start: {e}")
            self.is_running = False
            raise

    async def stop(self):
        """Stop the security analyzer agent"""
        self.logger.info("🛑 Stopping NEXUS Security Analyzer Agent...")
        self.is_running = False

    async def _monitoring_loop(self):
        """Main monitoring loop"""
        scan_interval = self.analyzer.config.get("triggers", {}).get(
            "monitoring_intervals", {}
        ).get("vulnerability_scanning", 3600)  # Default 1 hour
        
        self.logger.info(f"🔄 Starting security monitoring (scan every {scan_interval}s)")
        
        while self.is_running:
            try:
                # Check if it's time for a scan
                if self._should_run_scan(scan_interval):
                    await self.run_security_scan()
                
                # Check for security alerts
                await self._check_security_alerts()
                
                # Check for new commits (if git monitoring enabled)
                await self._check_new_commits()
                
                # Sleep for a short interval before next check
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                self.logger.error(f"❌ Error in monitoring loop: {e}")
                await asyncio.sleep(60)  # Wait before retrying

    def _should_run_scan(self, interval: int) -> bool:
        """Check if it's time to run a security scan"""
        if not self.last_scan_time:
            return True
        
        time_since_last_scan = datetime.now() - self.last_scan_time
        return time_since_last_scan.total_seconds() >= interval

    async def run_security_scan(self, target_path: str = ".") -> Dict:
        """Run comprehensive security scan"""
        self.logger.info(f"🔍 Running security scan on {target_path}")
        
        try:
            # Run security analysis
            results = await self.analyzer.analyze_codebase(target_path)
            
            # Update last scan time
            self.last_scan_time = datetime.now()
            
            # Check thresholds and trigger alerts
            await self._process_scan_results(results)
            
            # Generate patches for critical issues
            if self._should_generate_patches(results):
                patches = await self.analyzer.generate_security_patches(target_path)
                results["patches"] = patches
                self.logger.info(f"🔧 Generated {len(patches)} security patches")
            
            # Save scan results
            await self._save_scan_results(results)
            
            self.logger.info(f"✅ Security scan complete. Score: {results['metrics']['security_score']:.2f}")
            
            return results
            
        except Exception as e:
            self.logger.error(f"❌ Security scan failed: {e}")
            return {"error": str(e)}

    async def _process_scan_results(self, results: Dict):
        """Process scan results and trigger appropriate actions"""
        metrics = results.get("metrics", {})
        
        # Check security score threshold
        security_score = metrics.get("security_score", 0)
        threshold = self.analyzer.config.get("triggers", {}).get(
            "security_thresholds", {}
        ).get("security_score_threshold", 0.9)
        
        if security_score < threshold:
            await self._trigger_security_alert(
                "LOW_SECURITY_SCORE",
                f"Security score {security_score:.2f} below threshold {threshold}",
                metrics
            )
        
        # Check critical vulnerabilities
        critical_count = metrics.get("critical_count", 0)
        critical_threshold = self.analyzer.config.get("triggers", {}).get(
            "security_thresholds", {}
        ).get("critical_vulnerabilities", 0)
        
        if critical_count > critical_threshold:
            await self._trigger_security_alert(
                "CRITICAL_VULNERABILITIES",
                f"Found {critical_count} critical vulnerabilities",
                metrics
            )
        
        # Check high vulnerabilities
        high_count = metrics.get("high_count", 0)
        high_threshold = self.analyzer.config.get("triggers", {}).get(
            "security_thresholds", {}
        ).get("high_vulnerabilities", 3)
        
        if high_count > high_threshold:
            await self._trigger_security_alert(
                "HIGH_VULNERABILITIES",
                f"Found {high_count} high severity vulnerabilities",
                metrics
            )

    async def _trigger_security_alert(self, alert_type: str, message: str, data: Dict):
        """Trigger security alert"""
        self.logger.warning(f"🚨 SECURITY ALERT: {alert_type} - {message}")
        
        alert = {
            "timestamp": datetime.now().isoformat(),
            "type": alert_type,
            "message": message,
            "data": data,
            "severity": "HIGH" if "CRITICAL" in alert_type else "MEDIUM"
        }
        
        # Save alert to file
        alerts_file = Path("logs") / "security_alerts.json"
        alerts_file.parent.mkdir(exist_ok=True)
        
        alerts = []
        if alerts_file.exists():
            try:
                with open(alerts_file, "r") as f:
                    alerts = json.load(f)
            except:
                alerts = []
        
        alerts.append(alert)
        
        # Keep only last 100 alerts
        alerts = alerts[-100:]
        
        with open(alerts_file, "w") as f:
            json.dump(alerts, f, indent=2)
        
        # Send to NEXUS monitoring system if available
        await self._send_to_nexus_monitoring(alert)

    async def _send_to_nexus_monitoring(self, alert: Dict):
        """Send alert to NEXUS monitoring system"""
        try:
            # Try to integrate with NEXUS monitoring
            nexus_metrics_db = Path("nexus_metrics.db")
            if nexus_metrics_db.exists():
                import sqlite3
                with sqlite3.connect(nexus_metrics_db) as conn:
                    conn.execute("""
                        INSERT OR REPLACE INTO security_alerts 
                        (timestamp, type, message, severity, data)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        alert["timestamp"],
                        alert["type"],
                        alert["message"],
                        alert["severity"],
                        json.dumps(alert["data"])
                    ))
                    
        except Exception as e:
            self.logger.warning(f"Could not send alert to NEXUS monitoring: {e}")

    def _should_generate_patches(self, results: Dict) -> bool:
        """Check if patches should be generated"""
        metrics = results.get("metrics", {})
        
        # Generate patches for critical vulnerabilities
        critical_count = metrics.get("critical_count", 0)
        
        # Check configuration
        auto_patch = self.analyzer.config.get("remediation", {}).get(
            "automated_fixes", {}
        ).get("patch_application", False)
        
        return critical_count > 0 and auto_patch

    async def _save_scan_results(self, results: Dict):
        """Save scan results to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = Path("logs") / f"security_scan_{timestamp}.json"
        results_file.parent.mkdir(exist_ok=True)
        
        with open(results_file, "w") as f:
            json.dump(results, f, indent=2, default=str)

    async def _check_security_alerts(self):
        """Check for new security alerts"""
        # This could check external threat intelligence feeds
        # For now, it's a placeholder for future implementation
        pass

    async def _check_new_commits(self):
        """Check for new Git commits and scan them"""
        try:
            # Check if git monitoring is enabled
            git_monitoring = self.analyzer.config.get("integration", {}).get(
                "nexus_rsi", {}
            ).get("code_monitoring", {}).get("commit_scanning", False)
            
            if not git_monitoring:
                return
            
            # Check for new commits (simplified implementation)
            import subprocess
            
            # Get latest commit hash
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                capture_output=True,
                text=True,
                cwd="."
            )
            
            if result.returncode == 0:
                current_commit = result.stdout.strip()
                
                # Check if this is a new commit
                last_commit_file = Path("logs") / "last_scanned_commit.txt"
                
                if last_commit_file.exists():
                    with open(last_commit_file, "r") as f:
                        last_commit = f.read().strip()
                    
                    if current_commit != last_commit:
                        self.logger.info(f"🔍 New commit detected: {current_commit[:8]}")
                        
                        # Run quick security scan on changed files
                        await self._scan_commit_changes(last_commit, current_commit)
                        
                        # Update last scanned commit
                        with open(last_commit_file, "w") as f:
                            f.write(current_commit)
                else:
                    # First time, just save current commit
                    with open(last_commit_file, "w") as f:
                        f.write(current_commit)
                        
        except Exception as e:
            self.logger.debug(f"Git monitoring error: {e}")

    async def _scan_commit_changes(self, old_commit: str, new_commit: str):
        """Scan changes in a specific commit"""
        try:
            import subprocess
            
            # Get list of changed files
            result = subprocess.run(
                ["git", "diff", "--name-only", old_commit, new_commit],
                capture_output=True,
                text=True,
                cwd="."
            )
            
            if result.returncode == 0:
                changed_files = result.stdout.strip().split('\n')
                python_files = [f for f in changed_files if f.endswith('.py')]
                
                if python_files:
                    self.logger.info(f"🔍 Scanning {len(python_files)} changed Python files")
                    
                    # Run targeted scan on changed files
                    for file_path in python_files:
                        if Path(file_path).exists():
                            await self._scan_single_file(file_path)
                            
        except Exception as e:
            self.logger.error(f"Error scanning commit changes: {e}")

    async def _scan_single_file(self, file_path: str):
        """Scan a single file for security issues"""
        try:
            # Simple implementation - could be enhanced
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for secrets
            vulnerabilities = self.analyzer._check_security_patterns(content, file_path)
            
            if vulnerabilities:
                self.logger.warning(f"🚨 Found {len(vulnerabilities)} issues in {file_path}")
                
                # Trigger alert for high-severity issues
                high_severity = [v for v in vulnerabilities 
                               if v.get('severity') in ['critical', 'high']]
                
                if high_severity:
                    await self._trigger_security_alert(
                        "NEW_VULNERABILITIES",
                        f"Found {len(high_severity)} high-severity issues in {file_path}",
                        {"file": file_path, "vulnerabilities": high_severity}
                    )
                    
        except Exception as e:
            self.logger.error(f"Error scanning file {file_path}: {e}")

    async def get_security_status(self) -> Dict:
        """Get current security status"""
        try:
            # Load latest metrics from database
            import sqlite3
            
            with sqlite3.connect(self.analyzer.db_path) as conn:
                cursor = conn.execute("""
                    SELECT * FROM security_metrics 
                    ORDER BY scan_timestamp DESC 
                    LIMIT 1
                """)
                
                row = cursor.fetchone()
                
                if row:
                    columns = [desc[0] for desc in cursor.description]
                    metrics = dict(zip(columns, row))
                    
                    return {
                        "status": "healthy" if metrics["security_score"] > 0.8 else "warning",
                        "security_score": metrics["security_score"],
                        "total_vulnerabilities": metrics["total_vulnerabilities"],
                        "critical_count": metrics["critical_count"],
                        "high_count": metrics["high_count"],
                        "last_scan": metrics["scan_timestamp"],
                        "agent_running": self.is_running
                    }
                else:
                    return {
                        "status": "unknown",
                        "message": "No security scans performed yet",
                        "agent_running": self.is_running
                    }
                    
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "agent_running": self.is_running
            }

    async def run_manual_scan(self, target_path: str = ".") -> Dict:
        """Run manual security scan (for API/dashboard integration)"""
        self.logger.info(f"🔍 Running manual security scan on {target_path}")
        return await self.run_security_scan(target_path)

    async def apply_security_patches(self, patch_ids: List[str] = None) -> Dict:
        """Apply security patches (with approval)"""
        self.logger.info("🔧 Applying security patches...")
        
        try:
            # Load available patches
            patches_file = Path("logs") / "security_patches.json"
            
            if not patches_file.exists():
                return {"error": "No patches available"}
            
            with open(patches_file, "r") as f:
                all_patches = json.load(f)
            
            # Filter patches if specific IDs provided
            if patch_ids:
                patches_to_apply = [p for p in all_patches if p.get("vulnerability_id") in patch_ids]
            else:
                # Apply only auto-approved patches
                patches_to_apply = [p for p in all_patches if p.get("auto_apply", False)]
            
            applied_patches = []
            
            for patch in patches_to_apply:
                try:
                    # Apply patch (simplified implementation)
                    file_path = patch.get("file_path", "")
                    patch_content = patch.get("patch_content", "")
                    
                    if file_path and patch_content:
                        # Backup original file
                        backup_path = f"{file_path}.security_backup"
                        if Path(file_path).exists():
                            import shutil
                            shutil.copy2(file_path, backup_path)
                        
                        # Apply patch (append for now - could be more sophisticated)
                        with open(file_path, "a") as f:
                            f.write(f"\n\n{patch_content}")
                        
                        applied_patches.append(patch)
                        self.logger.info(f"✅ Applied patch for {patch.get('vulnerability_id')}")
                
                except Exception as e:
                    self.logger.error(f"❌ Failed to apply patch {patch.get('vulnerability_id')}: {e}")
            
            return {
                "patches_applied": len(applied_patches),
                "patches": applied_patches
            }
            
        except Exception as e:
            self.logger.error(f"❌ Error applying patches: {e}")
            return {"error": str(e)}


async def main():
    """Main entry point for the security analyzer agent"""
    import argparse
    
    parser = argparse.ArgumentParser(description="NEXUS Security Analyzer Agent")
    parser.add_argument("--config", help="Configuration file path")
    parser.add_argument("--scan", action="store_true", help="Run single scan and exit")
    parser.add_argument("--path", default=".", help="Path to scan")
    parser.add_argument("--daemon", action="store_true", help="Run as daemon")
    
    args = parser.parse_args()
    
    # Initialize agent
    agent = SecurityAnalyzerAgent(config_path=args.config)
    
    try:
        if args.scan:
            # Run single scan
            results = await agent.run_manual_scan(args.path)
            print(f"Security Score: {results.get('metrics', {}).get('security_score', 0):.2f}")
            print(f"Total Vulnerabilities: {results.get('metrics', {}).get('total_vulnerabilities', 0)}")
        
        elif args.daemon:
            # Run as daemon
            await agent.start()
        
        else:
            # Interactive mode
            print("🔒 NEXUS Security Analyzer Agent")
            print("1. Run security scan")
            print("2. Check security status")
            print("3. Apply security patches")
            print("4. Start monitoring daemon")
            print("5. Exit")
            
            while True:
                choice = input("\nSelect option (1-5): ").strip()
                
                if choice == "1":
                    results = await agent.run_manual_scan(args.path)
                    print(f"\n✅ Scan complete!")
                    print(f"Security Score: {results.get('metrics', {}).get('security_score', 0):.2f}")
                    
                elif choice == "2":
                    status = await agent.get_security_status()
                    print(f"\n📊 Security Status: {status}")
                    
                elif choice == "3":
                    patches = await agent.apply_security_patches()
                    print(f"\n🔧 Applied {patches.get('patches_applied', 0)} patches")
                    
                elif choice == "4":
                    print("\n🔄 Starting monitoring daemon...")
                    await agent.start()
                    
                elif choice == "5":
                    break
                
                else:
                    print("Invalid option. Please select 1-5.")
    
    except KeyboardInterrupt:
        print("\n🛑 Shutting down security analyzer agent...")
        await agent.stop()
    
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())