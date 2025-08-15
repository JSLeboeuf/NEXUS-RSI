"""
Setup script for NEXUS Security Analyzer Agent
Installs dependencies and configures the security analyzer
"""

import subprocess
import sys
import os
import json
from pathlib import Path


def install_security_tools():
    """Install security analysis tools"""
    print("🔧 Installing security analysis tools...")
    
    # Core security tools
    security_packages = [
        "bandit[toml]>=1.7.5",        # Static security analysis
        "safety>=2.3.0",              # Dependency vulnerability scanning
        "pip-audit>=2.6.0",           # Alternative dependency scanner
        "semgrep>=1.45.0",            # Advanced static analysis
        "detect-secrets>=1.4.0",      # Secrets detection
        "docker>=6.1.0",              # Docker API for container analysis
        "pyyaml>=6.0.1",              # YAML parsing
        "cryptography>=41.0.0",       # Cryptographic libraries
        "requests>=2.31.0",           # HTTP requests
        "aiofiles>=23.2.1",           # Async file operations
        "rich>=13.7.0",               # Rich console output
        "click>=8.1.7",               # CLI framework
        "jinja2>=3.1.2",              # Template engine for reports
        "markdown>=3.5.1",            # Markdown report generation
        "python-dateutil>=2.8.2",    # Date utilities
        "psutil>=5.9.6",              # System monitoring
        "gitpython>=3.1.40",          # Git operations
        "packaging>=23.2"             # Version parsing
    ]
    
    for package in security_packages:
        try:
            print(f"Installing {package}...")
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", package
            ], stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
            print(f"✅ {package} installed successfully")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install {package}: {e}")
            return False
    
    return True


def install_external_tools():
    """Install external security tools"""
    print("🔧 Installing external security tools...")
    
    try:
        # Check if tools are available
        tools_status = {}
        
        # Check for trivy (container vulnerability scanner)
        try:
            subprocess.run(["trivy", "--version"], check=True, 
                         capture_output=True, text=True)
            tools_status["trivy"] = "available"
        except (subprocess.CalledProcessError, FileNotFoundError):
            tools_status["trivy"] = "not_found"
            print("📦 Trivy not found. Install from: https://aquasecurity.github.io/trivy/")
        
        # Check for gitleaks (secrets scanner)
        try:
            subprocess.run(["gitleaks", "version"], check=True, 
                         capture_output=True, text=True)
            tools_status["gitleaks"] = "available"
        except (subprocess.CalledProcessError, FileNotFoundError):
            tools_status["gitleaks"] = "not_found"
            print("📦 Gitleaks not found. Install from: https://github.com/gitleaks/gitleaks")
        
        # Check for semgrep
        try:
            subprocess.run([sys.executable, "-m", "semgrep", "--version"], 
                         check=True, capture_output=True, text=True)
            tools_status["semgrep"] = "available"
        except (subprocess.CalledProcessError, FileNotFoundError):
            tools_status["semgrep"] = "not_found"
            print("📦 Semgrep not found. Installing...")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", "semgrep"])
                tools_status["semgrep"] = "installed"
            except subprocess.CalledProcessError:
                tools_status["semgrep"] = "failed"
        
        return tools_status
        
    except Exception as e:
        print(f"❌ Error checking external tools: {e}")
        return {}


def create_security_config_files():
    """Create security configuration files"""
    print("🔧 Creating security configuration files...")
    
    config_dir = Path("config")
    config_dir.mkdir(exist_ok=True)
    
    # Bandit configuration
    bandit_config = {
        "tests": [
            "B101", "B102", "B103", "B104", "B105", "B106", "B107", "B108", "B110",
            "B201", "B301", "B302", "B303", "B304", "B305", "B306", "B307", "B308",
            "B309", "B310", "B311", "B312", "B313", "B314", "B315", "B316", "B317",
            "B318", "B319", "B320", "B321", "B322", "B323", "B324", "B325", "B401",
            "B402", "B403", "B404", "B405", "B406", "B407", "B408", "B409", "B410",
            "B411", "B412", "B413", "B501", "B502", "B503", "B504", "B505", "B506",
            "B507", "B601", "B602", "B603", "B604", "B605", "B606", "B607", "B608",
            "B609", "B610", "B611", "B612", "B701", "B702", "B703"
        ],
        "skips": ["B404", "B603"],  # Skip subprocess and shell injection for now
        "exclude_dirs": [
            "/tests/",
            "/test/",
            "/.venv/",
            "/venv/",
            "/node_modules/",
            "/.git/"
        ]
    }
    
    with open(config_dir / "bandit.yaml", "w") as f:
        import yaml
        yaml.dump(bandit_config, f)
    
    # Gitleaks configuration
    gitleaks_config = """
title = "NEXUS Security Analyzer - Gitleaks Config"

[[rules]]
id = "aws-access-key"
description = "AWS Access Key"
regex = '''AKIA[0-9A-Z]{16}'''
tags = ["aws", "credentials"]

[[rules]]
id = "github-token"
description = "GitHub Token"
regex = '''ghp_[A-Za-z0-9]{36}'''
tags = ["github", "token"]

[[rules]]
id = "generic-api-key"
description = "Generic API Key"
regex = '''(?i)(api[_-]?key|apikey)['"\\s]*[:=]['"\\s]*[A-Za-z0-9]{20,}'''
tags = ["api", "key"]

[[rules]]
id = "generic-secret"
description = "Generic Secret"
regex = '''(?i)(secret|password|pwd)['"\\s]*[:=]['"\\s]*[A-Za-z0-9]{10,}'''
tags = ["secret", "password"]

[[rules]]
id = "database-url"
description = "Database Connection String"
regex = '''(postgres|mysql|mongodb)://[^\\s]+'''
tags = ["database", "connection"]

[[rules]]
id = "private-key"
description = "Private Key"
regex = '''-----BEGIN [A-Z]+ PRIVATE KEY-----'''
tags = ["private", "key"]

[allowlist]
paths = [
    '''.git/''',
    '''tests/''',
    '''test/''',
    '''docs/''',
    '''*.md''',
    '''*.txt'''
]
"""
    
    with open(config_dir / ".gitleaks.toml", "w") as f:
        f.write(gitleaks_config)
    
    # Safety configuration
    safety_config = {
        "security": {
            "ignore-ids": [],
            "continue-on-error": False,
            "output": "json"
        }
    }
    
    with open(config_dir / "safety.json", "w") as f:
        json.dump(safety_config, f, indent=2)
    
    # Semgrep configuration
    semgrep_config = {
        "rules": [
            "auto",
            "p/security-audit",
            "p/owasp-top-ten",
            "p/cwe-top-25"
        ],
        "exclude": [
            "tests/",
            "test/",
            ".venv/",
            "venv/",
            "node_modules/",
            ".git/"
        ],
        "timeout": 30,
        "max-memory": 2048
    }
    
    with open(config_dir / "semgrep.yaml", "w") as f:
        import yaml
        yaml.dump(semgrep_config, f)
    
    print("✅ Security configuration files created")


def create_security_scripts():
    """Create security analysis scripts"""
    print("🔧 Creating security analysis scripts...")
    
    scripts_dir = Path("scripts")
    scripts_dir.mkdir(exist_ok=True)
    
    # Quick security scan script
    quick_scan_script = """#!/usr/bin/env python3
\"\"\"
Quick Security Scan Script for NEXUS-RSI
\"\"\"

import asyncio
import sys
from pathlib import Path

# Add agents directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "agents"))

from security_analyzer import SecurityAnalyzer


async def main():
    print("🔒 Running quick security scan...")
    
    analyzer = SecurityAnalyzer()
    results = await analyzer.analyze_codebase(".")
    
    # Print summary
    metrics = results.get("metrics", {})
    print(f"\\n📊 Security Scan Results:")
    print(f"Security Score: {metrics.get('security_score', 0):.2f}/1.0")
    print(f"Total Vulnerabilities: {metrics.get('total_vulnerabilities', 0)}")
    print(f"Critical: {metrics.get('critical_count', 0)}")
    print(f"High: {metrics.get('high_count', 0)}")
    print(f"Medium: {metrics.get('medium_count', 0)}")
    
    # Save full report
    report = analyzer.generate_security_report()
    report_file = f"security_report_{analyzer.metrics.last_scan.replace(':', '-')}.txt"
    with open(report_file, 'w') as f:
        f.write(report)
    
    print(f"\\n✅ Full report saved to: {report_file}")


if __name__ == "__main__":
    asyncio.run(main())
"""
    
    with open(scripts_dir / "quick_security_scan.py", "w") as f:
        f.write(quick_scan_script)
    
    # Full security audit script
    full_audit_script = """#!/usr/bin/env python3
\"\"\"
Full Security Audit Script for NEXUS-RSI
\"\"\"

import asyncio
import sys
import json
from pathlib import Path
from datetime import datetime

# Add agents directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "agents"))

from security_analyzer import SecurityAnalyzer


async def main():
    print("🔒 Running comprehensive security audit...")
    
    analyzer = SecurityAnalyzer()
    
    # Run comprehensive analysis
    results = await analyzer.analyze_codebase(".")
    
    # Generate patches for critical issues
    patches = await analyzer.generate_security_patches(".")
    
    # Create audit directory
    audit_dir = Path(f"security_audit_{datetime.now():%Y%m%d_%H%M%S}")
    audit_dir.mkdir(exist_ok=True)
    
    # Save detailed results
    with open(audit_dir / "security_results.json", "w") as f:
        json.dump(results, f, indent=2, default=str)
    
    # Save security report
    report = analyzer.generate_security_report()
    with open(audit_dir / "security_report.txt", "w") as f:
        f.write(report)
    
    # Save patches
    with open(audit_dir / "security_patches.json", "w") as f:
        json.dump(patches, f, indent=2, default=str)
    
    # Generate summary
    summary = f\"\"\"
NEXUS-RSI Security Audit Summary
Generated: {datetime.now():%Y-%m-%d %H:%M:%S}

Security Score: {analyzer.metrics.security_score:.2f}/1.0
Compliance Score: {analyzer.metrics.compliance_score:.2f}/1.0

Vulnerabilities Found:
- Critical: {analyzer.metrics.critical_count}
- High: {analyzer.metrics.high_count}
- Medium: {analyzer.metrics.medium_count}
- Low: {analyzer.metrics.low_count}
- Info: {analyzer.metrics.info_count}

Security Patches Generated: {len(patches)}

Files Generated:
- security_results.json: Detailed scan results
- security_report.txt: Human-readable report
- security_patches.json: Automated patches

Next Steps:
1. Review critical and high severity vulnerabilities
2. Apply security patches (with review)
3. Update dependencies with vulnerabilities
4. Implement security recommendations
\"\"\"
    
    with open(audit_dir / "README.md", "w") as f:
        f.write(summary)
    
    print(f"\\n✅ Comprehensive security audit complete!")
    print(f"📁 Results saved to: {audit_dir}")
    print(f"🔒 Security Score: {analyzer.metrics.security_score:.2f}/1.0")
    print(f"🔧 Patches Generated: {len(patches)}")


if __name__ == "__main__":
    asyncio.run(main())
"""
    
    with open(scripts_dir / "full_security_audit.py", "w") as f:
        f.write(full_audit_script)
    
    # Make scripts executable
    try:
        import stat
        for script in [scripts_dir / "quick_security_scan.py", scripts_dir / "full_security_audit.py"]:
            script.chmod(script.stat().st_mode | stat.S_IEXEC)
    except Exception as e:
        print(f"Warning: Could not make scripts executable: {e}")
    
    print("✅ Security analysis scripts created")


def update_requirements():
    """Update requirements.txt with security tools"""
    print("🔧 Updating requirements.txt with security dependencies...")
    
    security_requirements = """
# Security Analysis Tools
bandit[toml]>=1.7.5
safety>=2.3.0
pip-audit>=2.6.0
semgrep>=1.45.0
detect-secrets>=1.4.0
cryptography>=41.0.0
pyyaml>=6.0.1
aiofiles>=23.2.1
gitpython>=3.1.40
psutil>=5.9.6
packaging>=23.2
"""
    
    requirements_file = Path("requirements.txt")
    
    if requirements_file.exists():
        # Append to existing requirements
        with open(requirements_file, "a") as f:
            f.write(security_requirements)
    else:
        # Create new requirements file
        with open(requirements_file, "w") as f:
            f.write(security_requirements.strip())
    
    print("✅ Requirements.txt updated with security dependencies")


def setup_security_integration():
    """Setup security analyzer integration with NEXUS-RSI"""
    print("🔧 Setting up security analyzer integration...")
    
    # Update nexus_config.json to include security analyzer
    config_file = Path("config/nexus_config.json")
    
    if config_file.exists():
        try:
            with open(config_file, "r") as f:
                config = json.load(f)
            
            # Add security analyzer to agents configuration
            if "agents" not in config:
                config["agents"] = {}
            
            config["agents"]["security_analyzer"] = {
                "enabled": True,
                "model": "opus",
                "thinking_mode": True,
                "temperature": 0.1,
                "max_tokens": 8000,
                "scan_interval": 3600,  # 1 hour
                "auto_patch": False,    # Require manual approval
                "critical_alert": True
            }
            
            # Add security monitoring configuration
            if "monitoring" not in config:
                config["monitoring"] = {}
            
            config["monitoring"]["security"] = {
                "enabled": True,
                "real_time": True,
                "threshold_score": 0.9,
                "alert_on_critical": True,
                "auto_scan_commits": True
            }
            
            # Save updated configuration
            with open(config_file, "w") as f:
                json.dump(config, f, indent=2)
            
            print("✅ NEXUS configuration updated with security analyzer")
            
        except Exception as e:
            print(f"❌ Error updating NEXUS configuration: {e}")
    else:
        print("⚠️  NEXUS configuration not found, skipping integration")


def create_security_dashboard():
    """Create security dashboard integration"""
    print("🔧 Creating security dashboard integration...")
    
    dashboard_code = """
import streamlit as st
import json
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from pathlib import Path


def load_security_metrics():
    \"\"\"Load security metrics from database\"\"\"
    db_path = Path("nexus_security.db")
    
    if not db_path.exists():
        return pd.DataFrame()
    
    with sqlite3.connect(db_path) as conn:
        query = \"\"\"
        SELECT * FROM security_metrics 
        ORDER BY scan_timestamp DESC 
        LIMIT 30
        \"\"\"
        return pd.read_sql_query(query, conn)


def load_vulnerabilities():
    \"\"\"Load vulnerability data\"\"\"
    db_path = Path("nexus_security.db")
    
    if not db_path.exists():
        return pd.DataFrame()
    
    with sqlite3.connect(db_path) as conn:
        query = \"\"\"
        SELECT category, severity, COUNT(*) as count
        FROM vulnerabilities 
        WHERE status = 'open'
        GROUP BY category, severity
        \"\"\"
        return pd.read_sql_query(query, conn)


def security_dashboard():
    \"\"\"Render security dashboard\"\"\"
    st.title("🔒 NEXUS Security Dashboard")
    
    # Load data
    metrics_df = load_security_metrics()
    vulns_df = load_vulnerabilities()
    
    if metrics_df.empty:
        st.warning("No security data available. Run a security scan first.")
        return
    
    # Latest metrics
    latest = metrics_df.iloc[0]
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Security Score",
            f"{latest['security_score']:.2f}",
            delta=f"{latest['security_score'] - 0.9:.2f}" if len(metrics_df) > 1 else None
        )
    
    with col2:
        st.metric(
            "Critical Issues",
            latest['critical_count'],
            delta=-latest['critical_count'] if latest['critical_count'] > 0 else None
        )
    
    with col3:
        st.metric(
            "High Issues",
            latest['high_count'],
            delta=-latest['high_count'] if latest['high_count'] > 0 else None
        )
    
    with col4:
        st.metric(
            "Total Vulnerabilities",
            latest['total_vulnerabilities']
        )
    
    # Security score trend
    st.subheader("📈 Security Score Trend")
    if len(metrics_df) > 1:
        fig = px.line(
            metrics_df[::-1], 
            x='scan_timestamp', 
            y='security_score',
            title="Security Score Over Time"
        )
        fig.add_hline(y=0.9, line_dash="dash", line_color="green", 
                     annotation_text="Target Score (0.9)")
        st.plotly_chart(fig, use_container_width=True)
    
    # Vulnerability breakdown
    st.subheader("🎯 Vulnerability Breakdown")
    
    if not vulns_df.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            # By category
            category_summary = vulns_df.groupby('category')['count'].sum().reset_index()
            fig = px.pie(
                category_summary, 
                values='count', 
                names='category',
                title="Vulnerabilities by Category"
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # By severity
            severity_summary = vulns_df.groupby('severity')['count'].sum().reset_index()
            colors = {
                'critical': '#ff0000',
                'high': '#ff8c00',
                'medium': '#ffa500',
                'low': '#ffff00',
                'info': '#90ee90'
            }
            fig = px.bar(
                severity_summary,
                x='severity',
                y='count',
                title="Vulnerabilities by Severity",
                color='severity',
                color_discrete_map=colors
            )
            st.plotly_chart(fig, use_container_width=True)
    
    # Recent scans
    st.subheader("📋 Recent Security Scans")
    
    if not metrics_df.empty:
        display_df = metrics_df[['scan_timestamp', 'security_score', 'total_vulnerabilities', 
                               'critical_count', 'high_count']].copy()
        display_df['scan_timestamp'] = pd.to_datetime(display_df['scan_timestamp']).dt.strftime('%Y-%m-%d %H:%M')
        st.dataframe(display_df, use_container_width=True)


if __name__ == "__main__":
    security_dashboard()
"""
    
    # Save dashboard to nexus_dashboard.py or create separate security dashboard
    dashboard_file = Path("nexus_security_dashboard.py")
    with open(dashboard_file, "w") as f:
        f.write(dashboard_code)
    
    print("✅ Security dashboard created")


def main():
    """Main setup function"""
    print("🔒 Setting up NEXUS Security Analyzer...")
    print("=" * 60)
    
    try:
        # Install Python security packages
        if not install_security_tools():
            print("❌ Failed to install security tools")
            return False
        
        # Check external tools
        tools_status = install_external_tools()
        
        # Create configuration files
        create_security_config_files()
        
        # Create analysis scripts
        create_security_scripts()
        
        # Update requirements
        update_requirements()
        
        # Setup integration
        setup_security_integration()
        
        # Create dashboard
        create_security_dashboard()
        
        print("\n" + "=" * 60)
        print("✅ NEXUS Security Analyzer setup complete!")
        print("\n📋 Setup Summary:")
        print(f"✅ Security analysis tools installed")
        print(f"✅ Configuration files created")
        print(f"✅ Analysis scripts created")
        print(f"✅ Requirements.txt updated")
        print(f"✅ NEXUS integration configured")
        print(f"✅ Security dashboard created")
        
        print("\n🔧 External Tools Status:")
        for tool, status in tools_status.items():
            status_icon = "✅" if status == "available" else "❌" if status == "not_found" else "⚠️"
            print(f"{status_icon} {tool}: {status}")
        
        print("\n🚀 Next Steps:")
        print("1. Run initial security scan:")
        print("   python scripts/quick_security_scan.py")
        print("\n2. Run comprehensive audit:")
        print("   python scripts/full_security_audit.py")
        print("\n3. Start security dashboard:")
        print("   streamlit run nexus_security_dashboard.py")
        print("\n4. Configure security monitoring in NEXUS-RSI")
        
        return True
        
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)