# NEXUS Security Analyzer Agent

## Overview

The NEXUS Security Analyzer is a comprehensive security vulnerability analysis and threat modeling agent designed specifically for the NEXUS-RSI system. It provides automated security scanning, vulnerability detection, threat assessment, and security patch generation.

## Features

### 🔍 Vulnerability Scanning
- **Static Code Analysis**: Uses Bandit, Semgrep, and custom rules to detect security issues in Python code
- **Dependency Scanning**: Scans Python packages for known vulnerabilities using Safety and pip-audit
- **Secrets Detection**: Identifies exposed credentials, API keys, and sensitive data in source code
- **Container Security**: Analyzes Docker configurations for security misconfigurations

### 🛡️ Security Capabilities
- **Real-time Monitoring**: Continuous security monitoring with configurable scan intervals
- **Threat Modeling**: Automated threat analysis and risk assessment
- **Compliance Checking**: OWASP Top 10, NIST, CIS Controls compliance verification
- **Security Scoring**: Quantitative security score calculation (0-1 scale)

### 🔧 Automated Remediation
- **Security Patch Generation**: Automatically generates patches for critical vulnerabilities
- **Configuration Hardening**: Suggests and applies security hardening configurations
- **Auto-Patcher Integration**: Integrates with NEXUS auto_patcher.py for automated fixes

### 📊 Reporting & Integration
- **Comprehensive Reports**: Detailed security reports in multiple formats (JSON, HTML, PDF)
- **Dashboard Integration**: Real-time security metrics in NEXUS dashboard
- **Alert System**: Configurable security alerts for critical issues
- **Database Storage**: SQLite database for historical security metrics

## Installation

### Prerequisites
- Python 3.8+
- NEXUS-RSI system
- Git (for commit monitoring)
- Docker (for container security analysis)

### Setup Instructions

1. **Run the setup script:**
   ```bash
   cd C:\Users\Jean-SamuelLeboeuf\NEXUS-RSI\agents
   python setup_security_analyzer.py
   ```

2. **Install external tools (optional but recommended):**
   - **Trivy**: Container vulnerability scanner
     ```bash
     # Windows (using Chocolatey)
     choco install trivy
     
     # Or download from: https://aquasecurity.github.io/trivy/
     ```
   
   - **Gitleaks**: Git secrets scanner
     ```bash
     # Windows (using Chocolatey)
     choco install gitleaks
     
     # Or download from: https://github.com/gitleaks/gitleaks
     ```

3. **Verify installation:**
   ```bash
   python init_security_analyzer.py --scan
   ```

## Configuration

### Agent Configuration

The security analyzer is configured via `security_analyzer.json`:

```json
{
  "agent_metadata": {
    "name": "nexus-security-analyzer",
    "model": "opus",
    "thinking_mode": true,
    "specialization": "Security vulnerability analysis and threat modeling"
  },
  "triggers": {
    "security_thresholds": {
      "security_score_threshold": 0.9,
      "critical_vulnerabilities": 0,
      "high_vulnerabilities": 3
    },
    "monitoring_intervals": {
      "vulnerability_scanning": 3600,
      "dependency_scanning": 86400
    }
  }
}
```

### Security Tools Configuration

Individual security tools can be configured:

- **Bandit**: `config/bandit.yaml`
- **Gitleaks**: `config/.gitleaks.toml`
- **Safety**: `config/safety.json`
- **Semgrep**: `config/semgrep.yaml`

## Usage

### Quick Security Scan

Run a quick security assessment:

```bash
python scripts/quick_security_scan.py
```

### Comprehensive Security Audit

Perform a full security audit with patch generation:

```bash
python scripts/full_security_audit.py
```

### Interactive Agent Mode

Start the security analyzer in interactive mode:

```bash
python init_security_analyzer.py
```

Options:
1. Run security scan
2. Check security status
3. Apply security patches
4. Start monitoring daemon
5. Exit

### Daemon Mode

Run continuous security monitoring:

```bash
python init_security_analyzer.py --daemon
```

### Manual Scan with Custom Path

Scan a specific directory:

```bash
python init_security_analyzer.py --scan --path /path/to/code
```

## Security Dashboard

Access the security dashboard:

```bash
streamlit run nexus_security_dashboard.py
```

The dashboard provides:
- Real-time security metrics
- Vulnerability trends
- Security score history
- Interactive vulnerability breakdown
- Recent scan results

## Integration with NEXUS-RSI

### Automatic Integration

The security analyzer automatically integrates with NEXUS-RSI:

1. **Configuration Update**: Updates `config/nexus_config.json` with security agent settings
2. **Metrics Database**: Stores security metrics in `nexus_security.db`
3. **Alert System**: Sends security alerts to NEXUS monitoring
4. **Auto-Patcher**: Generates patches compatible with `scripts/auto_patcher.py`

### Manual Integration

To manually integrate with existing NEXUS workflows:

```python
from agents.security_analyzer import SecurityAnalyzer

# Initialize analyzer
analyzer = SecurityAnalyzer()

# Run security scan
results = await analyzer.analyze_codebase(".")

# Check security score
security_score = results["metrics"]["security_score"]

# Generate patches for critical issues
if security_score < 0.8:
    patches = await analyzer.generate_security_patches(".")
```

## Security Scanning Process

### 1. Static Code Analysis
- Scans Python files using Bandit
- Applies custom security rules
- Detects common vulnerabilities (SQL injection, XSS, code injection)
- Analyzes cryptographic implementations

### 2. Dependency Analysis
- Scans `requirements.txt`, `pyproject.toml`, `Pipfile`
- Checks for known vulnerabilities using Safety database
- Verifies license compliance
- Identifies outdated packages

### 3. Secrets Detection
- Pattern-based detection of API keys, passwords, tokens
- Entropy analysis for high-entropy strings
- Git history scanning (if Gitleaks available)
- Configuration file analysis

### 4. Container Security
- Dockerfile analysis for security best practices
- Docker Compose configuration review
- Base image vulnerability scanning (if Trivy available)
- Runtime security assessment

### 5. Risk Assessment
- Vulnerability severity scoring
- Impact analysis
- Exploitability assessment
- Compliance gap analysis

## Security Metrics

### Security Score Calculation

The security score is calculated based on:
- **Vulnerability Count**: Weighted by severity
- **Compliance Status**: OWASP, NIST framework adherence
- **Configuration Security**: Container, API, database security
- **Secret Management**: Proper credential handling

Score ranges:
- **0.9-1.0**: Excellent security posture
- **0.8-0.9**: Good security with minor issues
- **0.7-0.8**: Moderate security, improvement needed
- **0.6-0.7**: Poor security, significant issues
- **0.0-0.6**: Critical security problems

### Vulnerability Severity Levels

1. **Critical**: Immediate security risk, exploitation likely
2. **High**: Significant security risk, should be patched quickly
3. **Medium**: Moderate security risk, patch when convenient
4. **Low**: Minor security issue, consider addressing
5. **Info**: Security notice, no immediate action required

## Automated Patch Generation

The security analyzer can generate patches for common vulnerability types:

### Supported Vulnerability Types
- **Hardcoded Secrets**: Replace with environment variables
- **Code Injection**: Replace eval/exec with safe alternatives
- **Weak Cryptography**: Upgrade to secure algorithms
- **Container Issues**: Security hardening configurations
- **Dependency Issues**: Version upgrade recommendations

### Patch Application Process
1. **Generate Patches**: Automatically create fix recommendations
2. **Review Required**: Manual approval for non-critical patches
3. **Auto-Apply**: Critical patches can be auto-applied (configurable)
4. **Backup**: Original files backed up before patching
5. **Validation**: Post-patch security verification

## Monitoring and Alerts

### Alert Types
- **Critical Vulnerabilities**: Immediate notification
- **Security Score Drop**: Below threshold alerts
- **New Secrets**: Exposed credentials detected
- **Compliance Violations**: Regulatory requirement failures
- **Suspicious Activity**: Anomaly detection

### Alert Channels
- **Log Files**: `logs/security_alerts.json`
- **NEXUS Dashboard**: Real-time dashboard alerts
- **Email Notifications**: Configurable email alerts
- **Webhook Integration**: Custom webhook endpoints

### Monitoring Configuration

```json
{
  "triggers": {
    "monitoring_intervals": {
      "real_time_monitoring": 30,
      "vulnerability_scanning": 3600,
      "dependency_scanning": 86400,
      "compliance_checking": 604800
    },
    "alert_conditions": {
      "new_vulnerabilities": true,
      "exposed_credentials": true,
      "suspicious_activity": true,
      "compliance_violations": true
    }
  }
}
```

## Best Practices

### Security Configuration
1. **Enable All Scans**: Activate all security scanning capabilities
2. **Regular Updates**: Keep security tools and databases updated
3. **Threshold Tuning**: Adjust security thresholds based on risk tolerance
4. **Patch Management**: Establish clear patch approval and deployment process

### Integration Best Practices
1. **CI/CD Integration**: Include security scans in build pipelines
2. **Pre-commit Hooks**: Prevent secrets from being committed
3. **Regular Audits**: Schedule comprehensive security audits
4. **Team Training**: Ensure development team understands security practices

### Performance Optimization
1. **Incremental Scanning**: Scan only changed files when possible
2. **Cache Results**: Use result caching to avoid redundant scans
3. **Parallel Execution**: Run multiple security tools concurrently
4. **Resource Limits**: Configure appropriate memory and CPU limits

## Troubleshooting

### Common Issues

1. **Tool Not Found Errors**
   ```bash
   # Install missing tools
   pip install bandit safety semgrep
   ```

2. **Permission Errors**
   ```bash
   # Ensure proper file permissions
   chmod +x scripts/quick_security_scan.py
   ```

3. **Database Lock Errors**
   ```bash
   # Stop other NEXUS processes and restart
   python init_security_analyzer.py --scan
   ```

4. **High Memory Usage**
   ```bash
   # Reduce concurrent scans in configuration
   # Scan smaller directories in batches
   ```

### Debug Mode

Enable debug logging:

```bash
export NEXUS_DEBUG=1
python init_security_analyzer.py --scan
```

### Log Files

Security analyzer logs are stored in:
- `logs/security_agent.log`: Agent operation logs
- `logs/security_alerts.json`: Security alert history
- `logs/security_scan_*.json`: Individual scan results

## API Reference

### SecurityAnalyzer Class

```python
class SecurityAnalyzer:
    async def analyze_codebase(self, root_path: str) -> Dict
    async def generate_security_patches(self, target_path: str) -> List[Dict]
    def generate_security_report(self) -> str
    def get_security_status(self) -> Dict
```

### SecurityAnalyzerAgent Class

```python
class SecurityAnalyzerAgent:
    async def start(self)
    async def stop(self)
    async def run_security_scan(self, target_path: str = ".") -> Dict
    async def apply_security_patches(self, patch_ids: List[str] = None) -> Dict
    async def get_security_status(self) -> Dict
```

## Contributing

### Adding Custom Security Rules

1. **Create Rule Definition**:
   ```python
   new_rule = {
       "pattern": r"dangerous_function\(",
       "category": VulnerabilityCategory.CODE_INJECTION,
       "severity": SecurityLevel.HIGH,
       "title": "Dangerous Function Usage",
       "description": "Usage of dangerous_function() detected"
   }
   ```

2. **Add to Security Patterns**:
   Update `_check_security_patterns()` in `security_analyzer.py`

3. **Test Rule**:
   ```bash
   python init_security_analyzer.py --scan --path test_code/
   ```

### Extending Vulnerability Categories

Add new categories to `VulnerabilityCategory` enum:

```python
class VulnerabilityCategory(Enum):
    # Existing categories...
    NEW_CATEGORY = "new_category"
```

## License

This security analyzer is part of the NEXUS-RSI system and follows the same licensing terms.

## Support

For support and questions:
1. Check the logs in `logs/` directory
2. Review configuration files in `config/`
3. Run debug mode for detailed output
4. Consult NEXUS-RSI documentation

---

**⚠️ Security Notice**: This tool is designed to identify security vulnerabilities but should not be considered a complete security solution. Regular security audits by qualified professionals are recommended for production systems.