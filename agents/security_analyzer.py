"""
NEXUS Security Analyzer Agent
Advanced security vulnerability analysis and threat modeling for NEXUS-RSI system
"""

import json
import sys
import os
import subprocess
import asyncio
import hashlib
import re
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import sqlite3
import yaml
import tempfile

# Security analysis tools
try:
    import bandit
    from bandit.core import manager as bandit_manager
    from bandit.core import config as bandit_config
except ImportError:
    bandit = None

try:
    import safety
except ImportError:
    safety = None

try:
    import docker
except ImportError:
    docker = None


class SecurityLevel(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class VulnerabilityCategory(Enum):
    CODE_INJECTION = "code_injection"
    SQL_INJECTION = "sql_injection"
    XSS = "xss"
    SECRETS = "secrets"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    CRYPTOGRAPHY = "cryptography"
    CONFIGURATION = "configuration"
    DEPENDENCY = "dependency"
    CONTAINER = "container"


@dataclass
class SecurityVulnerability:
    id: str
    category: VulnerabilityCategory
    severity: SecurityLevel
    title: str
    description: str
    file_path: str
    line_number: int
    cve_id: Optional[str] = None
    cvss_score: Optional[float] = None
    remediation: Optional[str] = None
    confidence: float = 1.0
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


@dataclass
class SecurityMetrics:
    total_vulnerabilities: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    info_count: int
    security_score: float
    compliance_score: float
    last_scan: str


class SecurityAnalyzer:
    def __init__(self, config_path: str = None):
        self.config = self._load_config(config_path)
        self.vulnerabilities: List[SecurityVulnerability] = []
        self.metrics = SecurityMetrics(0, 0, 0, 0, 0, 0, 0.0, 0.0, "")
        self.logger = self._setup_logging()
        self.db_path = Path("nexus_security.db")
        self._init_database()

    def _load_config(self, config_path: str) -> Dict:
        """Load security analyzer configuration"""
        if not config_path:
            config_path = Path(__file__).parent / "security_analyzer.json"
        
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            self.logger.warning(f"Config file not found: {config_path}")
            return self._default_config()

    def _default_config(self) -> Dict:
        """Default configuration if file not found"""
        return {
            "capabilities": {
                "static_code_analysis": {"enabled": True},
                "dependency_vulnerability_scanning": {"enabled": True},
                "container_security": {"enabled": True},
                "secrets_detection": {"enabled": True}
            },
            "triggers": {
                "security_thresholds": {
                    "security_score_threshold": 0.9,
                    "critical_vulnerabilities": 0,
                    "high_vulnerabilities": 3
                }
            }
        }

    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration"""
        logger = logging.getLogger("nexus_security_analyzer")
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger

    def _init_database(self):
        """Initialize security database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS vulnerabilities (
                    id TEXT PRIMARY KEY,
                    category TEXT,
                    severity TEXT,
                    title TEXT,
                    description TEXT,
                    file_path TEXT,
                    line_number INTEGER,
                    cve_id TEXT,
                    cvss_score REAL,
                    remediation TEXT,
                    confidence REAL,
                    timestamp TEXT,
                    status TEXT DEFAULT 'open'
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS security_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    total_vulnerabilities INTEGER,
                    critical_count INTEGER,
                    high_count INTEGER,
                    medium_count INTEGER,
                    low_count INTEGER,
                    info_count INTEGER,
                    security_score REAL,
                    compliance_score REAL,
                    scan_timestamp TEXT
                )
            """)

    async def analyze_codebase(self, root_path: str) -> Dict:
        """Comprehensive security analysis of the codebase"""
        self.logger.info(f"🔒 Starting security analysis of {root_path}")
        
        results = {
            "static_analysis": {},
            "dependency_scan": {},
            "secrets_scan": {},
            "container_scan": {},
            "vulnerabilities": [],
            "metrics": {},
            "recommendations": []
        }

        try:
            # Static code analysis
            if self.config["capabilities"]["static_code_analysis"]["enabled"]:
                results["static_analysis"] = await self._static_code_analysis(root_path)

            # Dependency vulnerability scanning
            if self.config["capabilities"]["dependency_vulnerability_scanning"]["enabled"]:
                results["dependency_scan"] = await self._dependency_scan(root_path)

            # Secrets detection
            if self.config["capabilities"]["secrets_detection"]["enabled"]:
                results["secrets_scan"] = await self._secrets_detection(root_path)

            # Container security analysis
            if self.config["capabilities"]["container_security"]["enabled"]:
                results["container_scan"] = await self._container_security_scan(root_path)

            # Aggregate results
            self._aggregate_vulnerabilities(results)
            results["vulnerabilities"] = [asdict(v) for v in self.vulnerabilities]
            results["metrics"] = asdict(self._calculate_metrics())
            results["recommendations"] = self._generate_recommendations()

            # Store results
            self._store_results()

            self.logger.info(f"✅ Security analysis complete. Found {len(self.vulnerabilities)} vulnerabilities")
            
        except Exception as e:
            self.logger.error(f"❌ Security analysis failed: {e}")
            results["error"] = str(e)

        return results

    async def _static_code_analysis(self, root_path: str) -> Dict:
        """Static code analysis using bandit and custom rules"""
        self.logger.info("🔍 Running static code analysis...")
        
        results = {
            "bandit_results": [],
            "custom_rules": [],
            "code_quality": {}
        }

        try:
            # Bandit analysis
            if bandit:
                results["bandit_results"] = await self._run_bandit(root_path)
            
            # Custom security rules
            results["custom_rules"] = await self._run_custom_security_rules(root_path)
            
            # Code quality analysis
            results["code_quality"] = await self._analyze_code_quality(root_path)

        except Exception as e:
            self.logger.error(f"Static analysis error: {e}")
            results["error"] = str(e)

        return results

    async def _run_bandit(self, root_path: str) -> List[Dict]:
        """Run bandit security scanner"""
        try:
            # Create temporary config
            config_content = {
                "tests": ["B101", "B102", "B103", "B104", "B105", "B106", "B107", "B108", "B110"],
                "skips": ["B404", "B603"],  # Skip some noisy checks
            }
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
                yaml.dump(config_content, f)
                config_file = f.name

            # Run bandit
            cmd = [
                sys.executable, "-m", "bandit",
                "-r", root_path,
                "-f", "json",
                "-c", config_file
            ]

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await process.communicate()
            
            # Clean up config file
            os.unlink(config_file)

            if stdout:
                bandit_output = json.loads(stdout.decode())
                return self._parse_bandit_results(bandit_output)

        except Exception as e:
            self.logger.error(f"Bandit scan error: {e}")

        return []

    def _parse_bandit_results(self, bandit_output: Dict) -> List[Dict]:
        """Parse bandit results and create vulnerabilities"""
        vulnerabilities = []
        
        for result in bandit_output.get("results", []):
            vuln = SecurityVulnerability(
                id=f"bandit_{hashlib.md5(str(result).encode()).hexdigest()[:8]}",
                category=self._map_bandit_test_to_category(result.get("test_id", "")),
                severity=self._map_bandit_severity(result.get("issue_severity", "LOW")),
                title=result.get("test_name", "Security Issue"),
                description=result.get("issue_text", ""),
                file_path=result.get("filename", ""),
                line_number=result.get("line_number", 0),
                confidence=self._map_bandit_confidence(result.get("issue_confidence", "LOW")),
                remediation=self._get_bandit_remediation(result.get("test_id", ""))
            )
            
            self.vulnerabilities.append(vuln)
            vulnerabilities.append(asdict(vuln))

        return vulnerabilities

    def _map_bandit_test_to_category(self, test_id: str) -> VulnerabilityCategory:
        """Map bandit test ID to vulnerability category"""
        mapping = {
            "B101": VulnerabilityCategory.CODE_INJECTION,
            "B102": VulnerabilityCategory.CODE_INJECTION,
            "B103": VulnerabilityCategory.CRYPTOGRAPHY,
            "B104": VulnerabilityCategory.AUTHENTICATION,
            "B105": VulnerabilityCategory.SECRETS,
            "B106": VulnerabilityCategory.SECRETS,
            "B107": VulnerabilityCategory.CRYPTOGRAPHY,
            "B108": VulnerabilityCategory.CRYPTOGRAPHY,
            "B110": VulnerabilityCategory.CODE_INJECTION,
            "B201": VulnerabilityCategory.CODE_INJECTION,
            "B301": VulnerabilityCategory.CRYPTOGRAPHY,
            "B302": VulnerabilityCategory.CRYPTOGRAPHY,
            "B303": VulnerabilityCategory.CRYPTOGRAPHY,
            "B304": VulnerabilityCategory.CRYPTOGRAPHY,
            "B305": VulnerabilityCategory.CRYPTOGRAPHY,
            "B306": VulnerabilityCategory.CRYPTOGRAPHY,
            "B307": VulnerabilityCategory.CODE_INJECTION,
            "B308": VulnerabilityCategory.CODE_INJECTION,
            "B309": VulnerabilityCategory.CODE_INJECTION,
            "B310": VulnerabilityCategory.CODE_INJECTION,
            "B311": VulnerabilityCategory.CRYPTOGRAPHY,
            "B312": VulnerabilityCategory.CODE_INJECTION,
            "B313": VulnerabilityCategory.CODE_INJECTION,
            "B314": VulnerabilityCategory.CODE_INJECTION,
            "B315": VulnerabilityCategory.CODE_INJECTION,
            "B316": VulnerabilityCategory.CODE_INJECTION,
            "B317": VulnerabilityCategory.CODE_INJECTION,
            "B318": VulnerabilityCategory.CODE_INJECTION,
            "B319": VulnerabilityCategory.CODE_INJECTION,
            "B320": VulnerabilityCategory.CODE_INJECTION,
            "B321": VulnerabilityCategory.CODE_INJECTION,
            "B322": VulnerabilityCategory.CODE_INJECTION,
            "B323": VulnerabilityCategory.CRYPTOGRAPHY,
            "B324": VulnerabilityCategory.CRYPTOGRAPHY,
            "B325": VulnerabilityCategory.CRYPTOGRAPHY,
            "B401": VulnerabilityCategory.CODE_INJECTION,
            "B402": VulnerabilityCategory.CODE_INJECTION,
            "B403": VulnerabilityCategory.CODE_INJECTION,
            "B404": VulnerabilityCategory.CODE_INJECTION,
            "B405": VulnerabilityCategory.CODE_INJECTION,
            "B406": VulnerabilityCategory.CODE_INJECTION,
            "B407": VulnerabilityCategory.CODE_INJECTION,
            "B408": VulnerabilityCategory.CODE_INJECTION,
            "B409": VulnerabilityCategory.CODE_INJECTION,
            "B410": VulnerabilityCategory.CODE_INJECTION,
            "B411": VulnerabilityCategory.CODE_INJECTION,
            "B412": VulnerabilityCategory.CODE_INJECTION,
            "B413": VulnerabilityCategory.CODE_INJECTION,
            "B501": VulnerabilityCategory.CRYPTOGRAPHY,
            "B502": VulnerabilityCategory.CRYPTOGRAPHY,
            "B503": VulnerabilityCategory.CRYPTOGRAPHY,
            "B504": VulnerabilityCategory.CRYPTOGRAPHY,
            "B505": VulnerabilityCategory.CRYPTOGRAPHY,
            "B506": VulnerabilityCategory.CRYPTOGRAPHY,
            "B507": VulnerabilityCategory.CRYPTOGRAPHY,
            "B601": VulnerabilityCategory.CODE_INJECTION,
            "B602": VulnerabilityCategory.CODE_INJECTION,
            "B603": VulnerabilityCategory.CODE_INJECTION,
            "B604": VulnerabilityCategory.CODE_INJECTION,
            "B605": VulnerabilityCategory.CODE_INJECTION,
            "B606": VulnerabilityCategory.CODE_INJECTION,
            "B607": VulnerabilityCategory.CODE_INJECTION,
            "B608": VulnerabilityCategory.SQL_INJECTION,
            "B609": VulnerabilityCategory.CODE_INJECTION,
            "B610": VulnerabilityCategory.CODE_INJECTION,
            "B611": VulnerabilityCategory.CODE_INJECTION,
            "B612": VulnerabilityCategory.CODE_INJECTION,
            "B701": VulnerabilityCategory.CRYPTOGRAPHY,
            "B702": VulnerabilityCategory.CRYPTOGRAPHY,
            "B703": VulnerabilityCategory.CRYPTOGRAPHY
        }
        return mapping.get(test_id, VulnerabilityCategory.CONFIGURATION)

    def _map_bandit_severity(self, severity: str) -> SecurityLevel:
        """Map bandit severity to security level"""
        mapping = {
            "HIGH": SecurityLevel.HIGH,
            "MEDIUM": SecurityLevel.MEDIUM,
            "LOW": SecurityLevel.LOW
        }
        return mapping.get(severity.upper(), SecurityLevel.LOW)

    def _map_bandit_confidence(self, confidence: str) -> float:
        """Map bandit confidence to float"""
        mapping = {
            "HIGH": 0.9,
            "MEDIUM": 0.7,
            "LOW": 0.5
        }
        return mapping.get(confidence.upper(), 0.5)

    def _get_bandit_remediation(self, test_id: str) -> str:
        """Get remediation advice for bandit test"""
        remediation_map = {
            "B101": "Use ast.literal_eval() instead of eval() for safe evaluation",
            "B102": "Use ast.literal_eval() instead of exec() for safe execution",
            "B103": "Use os.urandom() or secrets module for secure random generation",
            "B104": "Ensure all network connections use TLS/SSL encryption",
            "B105": "Remove hardcoded passwords and use secure credential storage",
            "B106": "Remove hardcoded passwords and use environment variables",
            "B107": "Use secure random generators from secrets module",
            "B108": "Use tempfile.mkstemp() for secure temporary file creation",
            "B110": "Implement proper exception handling to prevent information disclosure",
            "B608": "Use parameterized queries to prevent SQL injection"
        }
        return remediation_map.get(test_id, "Review and remediate the security issue")

    async def _run_custom_security_rules(self, root_path: str) -> List[Dict]:
        """Run custom security rules"""
        vulnerabilities = []
        
        try:
            # Find Python files
            python_files = list(Path(root_path).rglob("*.py"))
            
            for file_path in python_files:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Check for common security issues
                    file_vulns = self._check_security_patterns(content, str(file_path))
                    vulnerabilities.extend(file_vulns)
                    
                except Exception as e:
                    self.logger.warning(f"Error analyzing {file_path}: {e}")

        except Exception as e:
            self.logger.error(f"Custom rules error: {e}")

        return vulnerabilities

    def _check_security_patterns(self, content: str, file_path: str) -> List[Dict]:
        """Check for security patterns in code"""
        vulnerabilities = []
        lines = content.split('\n')
        
        # Security patterns to check
        patterns = [
            {
                "pattern": r"password\s*=\s*['\"][^'\"]+['\"]",
                "category": VulnerabilityCategory.SECRETS,
                "severity": SecurityLevel.HIGH,
                "title": "Hardcoded Password",
                "description": "Password is hardcoded in the source code"
            },
            {
                "pattern": r"api_key\s*=\s*['\"][^'\"]+['\"]",
                "category": VulnerabilityCategory.SECRETS,
                "severity": SecurityLevel.HIGH,
                "title": "Hardcoded API Key",
                "description": "API key is hardcoded in the source code"
            },
            {
                "pattern": r"subprocess\.call\(",
                "category": VulnerabilityCategory.CODE_INJECTION,
                "severity": SecurityLevel.MEDIUM,
                "title": "Subprocess Call",
                "description": "Direct subprocess call may be vulnerable to injection"
            },
            {
                "pattern": r"eval\s*\(",
                "category": VulnerabilityCategory.CODE_INJECTION,
                "severity": SecurityLevel.HIGH,
                "title": "Use of eval()",
                "description": "eval() function can execute arbitrary code"
            },
            {
                "pattern": r"exec\s*\(",
                "category": VulnerabilityCategory.CODE_INJECTION,
                "severity": SecurityLevel.HIGH,
                "title": "Use of exec()",
                "description": "exec() function can execute arbitrary code"
            },
            {
                "pattern": r"shell\s*=\s*True",
                "category": VulnerabilityCategory.CODE_INJECTION,
                "severity": SecurityLevel.HIGH,
                "title": "Shell Injection Risk",
                "description": "Using shell=True can lead to command injection"
            },
            {
                "pattern": r"pickle\.loads?\(",
                "category": VulnerabilityCategory.CODE_INJECTION,
                "severity": SecurityLevel.HIGH,
                "title": "Unsafe Deserialization",
                "description": "pickle.load/loads can execute arbitrary code"
            },
            {
                "pattern": r"random\.random\(",
                "category": VulnerabilityCategory.CRYPTOGRAPHY,
                "severity": SecurityLevel.MEDIUM,
                "title": "Weak Random Generator",
                "description": "Use secrets module for cryptographic random numbers"
            }
        ]
        
        for line_num, line in enumerate(lines, 1):
            for pattern_info in patterns:
                if re.search(pattern_info["pattern"], line, re.IGNORECASE):
                    vuln = SecurityVulnerability(
                        id=f"custom_{hashlib.md5(f'{file_path}:{line_num}'.encode()).hexdigest()[:8]}",
                        category=pattern_info["category"],
                        severity=pattern_info["severity"],
                        title=pattern_info["title"],
                        description=pattern_info["description"],
                        file_path=file_path,
                        line_number=line_num,
                        confidence=0.8,
                        remediation=self._get_pattern_remediation(pattern_info["pattern"])
                    )
                    
                    self.vulnerabilities.append(vuln)
                    vulnerabilities.append(asdict(vuln))

        return vulnerabilities

    def _get_pattern_remediation(self, pattern: str) -> str:
        """Get remediation for custom patterns"""
        remediation_map = {
            r"password\s*=\s*['\"][^'\"]+['\"]": "Use environment variables or secure credential storage",
            r"api_key\s*=\s*['\"][^'\"]+['\"]": "Use environment variables or key management service",
            r"subprocess\.call\(": "Use subprocess.run() with proper input validation",
            r"eval\s*\(": "Use ast.literal_eval() for safe evaluation",
            r"exec\s*\(": "Avoid exec() or use restricted execution environment",
            r"shell\s*=\s*True": "Use shell=False and pass arguments as list",
            r"pickle\.loads?\(": "Use JSON or other safe serialization formats",
            r"random\.random\(": "Use secrets.SystemRandom() for cryptographic purposes"
        }
        
        for p, remediation in remediation_map.items():
            if pattern == p:
                return remediation
        
        return "Review and remediate the security issue"

    async def _analyze_code_quality(self, root_path: str) -> Dict:
        """Analyze code quality metrics"""
        quality_metrics = {
            "complexity": 0,
            "maintainability": 0,
            "security_hotspots": 0,
            "technical_debt": 0
        }
        
        try:
            # Simple complexity analysis
            python_files = list(Path(root_path).rglob("*.py"))
            total_complexity = 0
            total_files = len(python_files)
            
            for file_path in python_files:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Simple cyclomatic complexity approximation
                    complexity_keywords = ['if', 'elif', 'for', 'while', 'except', 'and', 'or']
                    file_complexity = sum(content.count(keyword) for keyword in complexity_keywords)
                    total_complexity += file_complexity
                    
                except Exception as e:
                    self.logger.warning(f"Error analyzing complexity for {file_path}: {e}")
            
            if total_files > 0:
                quality_metrics["complexity"] = total_complexity / total_files
                quality_metrics["maintainability"] = max(0, 100 - (quality_metrics["complexity"] * 2))
            
        except Exception as e:
            self.logger.error(f"Code quality analysis error: {e}")
        
        return quality_metrics

    async def _dependency_scan(self, root_path: str) -> Dict:
        """Scan dependencies for vulnerabilities"""
        self.logger.info("🔍 Scanning dependencies for vulnerabilities...")
        
        results = {
            "vulnerable_packages": [],
            "outdated_packages": [],
            "license_issues": [],
            "total_packages": 0
        }

        try:
            # Find requirements files
            req_files = list(Path(root_path).glob("*requirements*.txt"))
            req_files.extend(list(Path(root_path).glob("pyproject.toml")))
            req_files.extend(list(Path(root_path).glob("Pipfile")))
            
            for req_file in req_files:
                if req_file.name.endswith('.txt'):
                    await self._scan_requirements_txt(req_file, results)
                # TODO: Add support for pyproject.toml and Pipfile
            
        except Exception as e:
            self.logger.error(f"Dependency scan error: {e}")
            results["error"] = str(e)

        return results

    async def _scan_requirements_txt(self, req_file: Path, results: Dict):
        """Scan requirements.txt file"""
        try:
            # Use safety CLI
            cmd = [sys.executable, "-m", "safety", "check", "-r", str(req_file), "--json"]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if stdout:
                try:
                    safety_output = json.loads(stdout.decode())
                    
                    for vuln in safety_output:
                        sec_vuln = SecurityVulnerability(
                            id=f"dep_{vuln.get('advisory', '')[:8]}",
                            category=VulnerabilityCategory.DEPENDENCY,
                            severity=self._map_safety_severity(vuln.get('severity', 'medium')),
                            title=f"Vulnerable dependency: {vuln.get('package_name', 'unknown')}",
                            description=vuln.get('advisory', ''),
                            file_path=str(req_file),
                            line_number=1,
                            cve_id=vuln.get('cve', ''),
                            remediation=f"Upgrade to version {vuln.get('safe_versions', ['latest'])[0]}"
                        )
                        
                        self.vulnerabilities.append(sec_vuln)
                        results["vulnerable_packages"].append(asdict(sec_vuln))
                        
                except json.JSONDecodeError:
                    self.logger.warning("Could not parse safety output")
            
        except FileNotFoundError:
            self.logger.warning("Safety tool not found. Install with: pip install safety")
        except Exception as e:
            self.logger.error(f"Error scanning {req_file}: {e}")

    def _map_safety_severity(self, severity: str) -> SecurityLevel:
        """Map safety severity to security level"""
        mapping = {
            "critical": SecurityLevel.CRITICAL,
            "high": SecurityLevel.HIGH,
            "medium": SecurityLevel.MEDIUM,
            "low": SecurityLevel.LOW
        }
        return mapping.get(severity.lower(), SecurityLevel.MEDIUM)

    async def _secrets_detection(self, root_path: str) -> Dict:
        """Detect secrets in codebase"""
        self.logger.info("🔍 Scanning for exposed secrets...")
        
        results = {
            "secrets_found": [],
            "high_entropy_strings": [],
            "suspicious_files": []
        }

        try:
            # Use trufflehog-like detection
            results = await self._scan_for_secrets(root_path)
            
        except Exception as e:
            self.logger.error(f"Secrets detection error: {e}")
            results["error"] = str(e)

        return results

    async def _scan_for_secrets(self, root_path: str) -> Dict:
        """Scan for secrets using pattern matching and entropy analysis"""
        results = {
            "secrets_found": [],
            "high_entropy_strings": [],
            "suspicious_files": []
        }
        
        # Secret patterns
        secret_patterns = [
            {
                "name": "AWS Access Key",
                "pattern": r"AKIA[0-9A-Z]{16}",
                "severity": SecurityLevel.CRITICAL
            },
            {
                "name": "AWS Secret Key",
                "pattern": r"[A-Za-z0-9/+=]{40}",
                "severity": SecurityLevel.CRITICAL
            },
            {
                "name": "GitHub Token",
                "pattern": r"ghp_[A-Za-z0-9]{36}",
                "severity": SecurityLevel.HIGH
            },
            {
                "name": "Generic API Key",
                "pattern": r"api[_-]?key['\"]?\s*[:=]\s*['\"]?[A-Za-z0-9]{20,}",
                "severity": SecurityLevel.HIGH
            },
            {
                "name": "Generic Secret",
                "pattern": r"secret['\"]?\s*[:=]\s*['\"]?[A-Za-z0-9]{10,}",
                "severity": SecurityLevel.HIGH
            },
            {
                "name": "Database URL",
                "pattern": r"(postgres|mysql|mongodb)://[^\s]+",
                "severity": SecurityLevel.HIGH
            },
            {
                "name": "Private Key",
                "pattern": r"-----BEGIN [A-Z]+ PRIVATE KEY-----",
                "severity": SecurityLevel.CRITICAL
            }
        ]
        
        # Scan files
        exclude_patterns = [".git", "__pycache__", "node_modules", ".pyc"]
        
        for file_path in Path(root_path).rglob("*"):
            if file_path.is_file() and not any(pattern in str(file_path) for pattern in exclude_patterns):
                try:
                    # Skip binary files
                    if not self._is_text_file(file_path):
                        continue
                        
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    
                    # Pattern matching
                    for pattern_info in secret_patterns:
                        matches = re.finditer(pattern_info["pattern"], content, re.IGNORECASE)
                        
                        for match in matches:
                            line_num = content[:match.start()].count('\n') + 1
                            
                            secret_vuln = SecurityVulnerability(
                                id=f"secret_{hashlib.md5(f'{file_path}:{line_num}'.encode()).hexdigest()[:8]}",
                                category=VulnerabilityCategory.SECRETS,
                                severity=pattern_info["severity"],
                                title=f"Exposed {pattern_info['name']}",
                                description=f"Potential {pattern_info['name']} found in source code",
                                file_path=str(file_path),
                                line_number=line_num,
                                confidence=0.9,
                                remediation="Remove secret from code and use environment variables or secure vault"
                            )
                            
                            self.vulnerabilities.append(secret_vuln)
                            results["secrets_found"].append(asdict(secret_vuln))
                    
                    # Entropy analysis for high-entropy strings
                    high_entropy = self._find_high_entropy_strings(content, str(file_path))
                    results["high_entropy_strings"].extend(high_entropy)
                    
                except Exception as e:
                    self.logger.warning(f"Error scanning {file_path}: {e}")

        return results

    def _is_text_file(self, file_path: Path) -> bool:
        """Check if file is likely a text file"""
        text_extensions = {'.py', '.txt', '.json', '.yaml', '.yml', '.md', '.rst', '.cfg', '.ini', '.env'}
        
        if file_path.suffix.lower() in text_extensions:
            return True
        
        try:
            with open(file_path, 'rb') as f:
                chunk = f.read(1024)
                return b'\x00' not in chunk
        except:
            return False

    def _find_high_entropy_strings(self, content: str, file_path: str) -> List[Dict]:
        """Find high-entropy strings that might be secrets"""
        import math
        from collections import Counter
        
        high_entropy_strings = []
        
        # Extract potential secrets (strings longer than 20 chars, alphanumeric)
        potential_secrets = re.findall(r'[A-Za-z0-9+/=]{20,}', content)
        
        for secret in potential_secrets:
            # Calculate Shannon entropy
            entropy = self._calculate_entropy(secret)
            
            # High entropy threshold (typical for encoded secrets)
            if entropy > 4.0:
                line_num = content.find(secret)
                if line_num != -1:
                    line_num = content[:line_num].count('\n') + 1
                
                high_entropy_strings.append({
                    "string": secret[:50] + "..." if len(secret) > 50 else secret,
                    "entropy": entropy,
                    "file_path": file_path,
                    "line_number": line_num,
                    "length": len(secret)
                })

        return high_entropy_strings

    def _calculate_entropy(self, text: str) -> float:
        """Calculate Shannon entropy of a string"""
        import math
        from collections import Counter
        
        if not text:
            return 0
        
        # Count character frequencies
        counter = Counter(text)
        length = len(text)
        
        # Calculate entropy
        entropy = 0
        for count in counter.values():
            probability = count / length
            entropy -= probability * math.log2(probability)
        
        return entropy

    async def _container_security_scan(self, root_path: str) -> Dict:
        """Scan container configurations for security issues"""
        self.logger.info("🔍 Scanning container security...")
        
        results = {
            "dockerfile_issues": [],
            "docker_compose_issues": [],
            "image_vulnerabilities": [],
            "configuration_issues": []
        }

        try:
            # Find Docker files
            docker_files = list(Path(root_path).glob("**/Dockerfile*"))
            compose_files = list(Path(root_path).glob("**/docker-compose*.yml"))
            compose_files.extend(list(Path(root_path).glob("**/docker-compose*.yaml")))
            
            # Analyze Dockerfiles
            for dockerfile in docker_files:
                issues = await self._analyze_dockerfile(dockerfile)
                results["dockerfile_issues"].extend(issues)
            
            # Analyze docker-compose files
            for compose_file in compose_files:
                issues = await self._analyze_docker_compose(compose_file)
                results["docker_compose_issues"].extend(issues)
            
        except Exception as e:
            self.logger.error(f"Container security scan error: {e}")
            results["error"] = str(e)

        return results

    async def _analyze_dockerfile(self, dockerfile_path: Path) -> List[Dict]:
        """Analyze Dockerfile for security issues"""
        issues = []
        
        try:
            with open(dockerfile_path, 'r') as f:
                lines = f.readlines()
            
            for line_num, line in enumerate(lines, 1):
                line = line.strip()
                
                # Check for security issues
                if line.upper().startswith('USER ROOT') or 'USER 0' in line.upper():
                    vuln = SecurityVulnerability(
                        id=f"docker_{hashlib.md5(f'{dockerfile_path}:{line_num}'.encode()).hexdigest()[:8]}",
                        category=VulnerabilityCategory.CONTAINER,
                        severity=SecurityLevel.HIGH,
                        title="Running as root user",
                        description="Container is configured to run as root, which poses security risks",
                        file_path=str(dockerfile_path),
                        line_number=line_num,
                        confidence=0.9,
                        remediation="Create and use a non-root user for running the application"
                    )
                    self.vulnerabilities.append(vuln)
                    issues.append(asdict(vuln))
                
                if 'ADD' in line.upper() and ('http://' in line or 'https://' in line):
                    vuln = SecurityVulnerability(
                        id=f"docker_{hashlib.md5(f'{dockerfile_path}:{line_num}'.encode()).hexdigest()[:8]}",
                        category=VulnerabilityCategory.CONTAINER,
                        severity=SecurityLevel.MEDIUM,
                        title="Remote ADD instruction",
                        description="Using ADD with remote URLs can introduce security risks",
                        file_path=str(dockerfile_path),
                        line_number=line_num,
                        confidence=0.8,
                        remediation="Use COPY for local files or curl/wget in RUN for remote resources"
                    )
                    self.vulnerabilities.append(vuln)
                    issues.append(asdict(vuln))
                
                if '--privileged' in line:
                    vuln = SecurityVulnerability(
                        id=f"docker_{hashlib.md5(f'{dockerfile_path}:{line_num}'.encode()).hexdigest()[:8]}",
                        category=VulnerabilityCategory.CONTAINER,
                        severity=SecurityLevel.CRITICAL,
                        title="Privileged container",
                        description="Container is running in privileged mode",
                        file_path=str(dockerfile_path),
                        line_number=line_num,
                        confidence=1.0,
                        remediation="Remove --privileged flag and use specific capabilities instead"
                    )
                    self.vulnerabilities.append(vuln)
                    issues.append(asdict(vuln))

        except Exception as e:
            self.logger.error(f"Error analyzing Dockerfile {dockerfile_path}: {e}")

        return issues

    async def _analyze_docker_compose(self, compose_path: Path) -> List[Dict]:
        """Analyze docker-compose file for security issues"""
        issues = []
        
        try:
            with open(compose_path, 'r') as f:
                compose_content = yaml.safe_load(f)
            
            if not compose_content or 'services' not in compose_content:
                return issues
            
            for service_name, service_config in compose_content['services'].items():
                if isinstance(service_config, dict):
                    # Check for privileged mode
                    if service_config.get('privileged', False):
                        vuln = SecurityVulnerability(
                            id=f"compose_{hashlib.md5(f'{compose_path}:{service_name}'.encode()).hexdigest()[:8]}",
                            category=VulnerabilityCategory.CONTAINER,
                            severity=SecurityLevel.CRITICAL,
                            title=f"Privileged service: {service_name}",
                            description=f"Service {service_name} is running in privileged mode",
                            file_path=str(compose_path),
                            line_number=1,
                            confidence=1.0,
                            remediation="Remove privileged: true and use specific capabilities"
                        )
                        self.vulnerabilities.append(vuln)
                        issues.append(asdict(vuln))
                    
                    # Check for host network mode
                    if service_config.get('network_mode') == 'host':
                        vuln = SecurityVulnerability(
                            id=f"compose_{hashlib.md5(f'{compose_path}:{service_name}_net'.encode()).hexdigest()[:8]}",
                            category=VulnerabilityCategory.CONTAINER,
                            severity=SecurityLevel.HIGH,
                            title=f"Host network mode: {service_name}",
                            description=f"Service {service_name} uses host network mode",
                            file_path=str(compose_path),
                            line_number=1,
                            confidence=0.9,
                            remediation="Use bridge network mode and expose specific ports"
                        )
                        self.vulnerabilities.append(vuln)
                        issues.append(asdict(vuln))
                    
                    # Check for volume mounts
                    volumes = service_config.get('volumes', [])
                    for volume in volumes:
                        if isinstance(volume, str) and ':' in volume:
                            host_path, container_path = volume.split(':', 1)
                            if host_path.startswith('/'):
                                vuln = SecurityVulnerability(
                                    id=f"compose_{hashlib.md5(f'{compose_path}:{service_name}_vol'.encode()).hexdigest()[:8]}",
                                    category=VulnerabilityCategory.CONTAINER,
                                    severity=SecurityLevel.MEDIUM,
                                    title=f"Host volume mount: {service_name}",
                                    description=f"Service {service_name} mounts host directory {host_path}",
                                    file_path=str(compose_path),
                                    line_number=1,
                                    confidence=0.7,
                                    remediation="Use named volumes or bind mounts with read-only access"
                                )
                                self.vulnerabilities.append(vuln)
                                issues.append(asdict(vuln))

        except Exception as e:
            self.logger.error(f"Error analyzing docker-compose {compose_path}: {e}")

        return issues

    def _aggregate_vulnerabilities(self, results: Dict):
        """Aggregate vulnerabilities from all scans"""
        # Vulnerabilities are already added to self.vulnerabilities during individual scans
        # This method can be used for additional processing or deduplication
        
        # Remove duplicates based on file_path + line_number + title
        seen = set()
        unique_vulns = []
        
        for vuln in self.vulnerabilities:
            key = f"{vuln.file_path}:{vuln.line_number}:{vuln.title}"
            if key not in seen:
                seen.add(key)
                unique_vulns.append(vuln)
        
        self.vulnerabilities = unique_vulns

    def _calculate_metrics(self) -> SecurityMetrics:
        """Calculate security metrics"""
        total = len(self.vulnerabilities)
        critical = sum(1 for v in self.vulnerabilities if v.severity == SecurityLevel.CRITICAL)
        high = sum(1 for v in self.vulnerabilities if v.severity == SecurityLevel.HIGH)
        medium = sum(1 for v in self.vulnerabilities if v.severity == SecurityLevel.MEDIUM)
        low = sum(1 for v in self.vulnerabilities if v.severity == SecurityLevel.LOW)
        info = sum(1 for v in self.vulnerabilities if v.severity == SecurityLevel.INFO)
        
        # Calculate security score (0-1, higher is better)
        if total == 0:
            security_score = 1.0
        else:
            # Weight vulnerabilities by severity
            weighted_score = (critical * 10 + high * 5 + medium * 2 + low * 1 + info * 0.1)
            max_possible_score = total * 10  # If all were critical
            security_score = max(0, 1 - (weighted_score / max_possible_score))
        
        # Simple compliance score based on security score
        compliance_score = security_score * 0.9  # Compliance is typically stricter
        
        self.metrics = SecurityMetrics(
            total_vulnerabilities=total,
            critical_count=critical,
            high_count=high,
            medium_count=medium,
            low_count=low,
            info_count=info,
            security_score=security_score,
            compliance_score=compliance_score,
            last_scan=datetime.now().isoformat()
        )
        
        return self.metrics

    def _generate_recommendations(self) -> List[Dict]:
        """Generate security recommendations"""
        recommendations = []
        
        # Security score recommendations
        if self.metrics.security_score < 0.7:
            recommendations.append({
                "priority": "HIGH",
                "category": "Security Score",
                "title": "Improve Overall Security Score",
                "description": f"Current security score is {self.metrics.security_score:.2f}. Target is 0.9+",
                "actions": [
                    "Address critical and high severity vulnerabilities first",
                    "Implement security testing in CI/CD pipeline",
                    "Regular security code reviews",
                    "Security training for development team"
                ]
            })
        
        # Critical vulnerabilities
        if self.metrics.critical_count > 0:
            recommendations.append({
                "priority": "CRITICAL",
                "category": "Critical Vulnerabilities",
                "title": f"Address {self.metrics.critical_count} Critical Vulnerabilities",
                "description": "Critical vulnerabilities pose immediate security risks",
                "actions": [
                    "Patch or remediate all critical vulnerabilities immediately",
                    "Consider emergency deployment if in production",
                    "Review security policies and procedures"
                ]
            })
        
        # Secrets in code
        secrets_count = sum(1 for v in self.vulnerabilities if v.category == VulnerabilityCategory.SECRETS)
        if secrets_count > 0:
            recommendations.append({
                "priority": "HIGH",
                "category": "Secrets Management",
                "title": f"Remove {secrets_count} Exposed Secrets",
                "description": "Secrets found in source code pose security risks",
                "actions": [
                    "Move secrets to environment variables",
                    "Use secure credential storage (e.g., AWS Secrets Manager, Azure Key Vault)",
                    "Rotate exposed credentials immediately",
                    "Implement pre-commit hooks to prevent secret commits"
                ]
            })
        
        # Container security
        container_issues = sum(1 for v in self.vulnerabilities if v.category == VulnerabilityCategory.CONTAINER)
        if container_issues > 0:
            recommendations.append({
                "priority": "MEDIUM",
                "category": "Container Security",
                "title": f"Fix {container_issues} Container Security Issues",
                "description": "Container configurations have security vulnerabilities",
                "actions": [
                    "Run containers as non-root users",
                    "Use minimal base images (e.g., Alpine, distroless)",
                    "Implement proper network segmentation",
                    "Regular image vulnerability scanning"
                ]
            })
        
        # Dependency vulnerabilities
        dep_issues = sum(1 for v in self.vulnerabilities if v.category == VulnerabilityCategory.DEPENDENCY)
        if dep_issues > 0:
            recommendations.append({
                "priority": "MEDIUM",
                "category": "Dependency Security",
                "title": f"Update {dep_issues} Vulnerable Dependencies",
                "description": "Dependencies have known security vulnerabilities",
                "actions": [
                    "Update vulnerable packages to patched versions",
                    "Implement automated dependency scanning",
                    "Use dependency pinning and lock files",
                    "Regular dependency audits"
                ]
            })
        
        return recommendations

    def _store_results(self):
        """Store results in database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Store vulnerabilities
                for vuln in self.vulnerabilities:
                    conn.execute("""
                        INSERT OR REPLACE INTO vulnerabilities 
                        (id, category, severity, title, description, file_path, line_number, 
                         cve_id, cvss_score, remediation, confidence, timestamp)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        vuln.id, vuln.category.value, vuln.severity.value, vuln.title,
                        vuln.description, vuln.file_path, vuln.line_number, vuln.cve_id,
                        vuln.cvss_score, vuln.remediation, vuln.confidence, vuln.timestamp
                    ))
                
                # Store metrics
                conn.execute("""
                    INSERT INTO security_metrics
                    (total_vulnerabilities, critical_count, high_count, medium_count,
                     low_count, info_count, security_score, compliance_score, scan_timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    self.metrics.total_vulnerabilities, self.metrics.critical_count,
                    self.metrics.high_count, self.metrics.medium_count, self.metrics.low_count,
                    self.metrics.info_count, self.metrics.security_score, self.metrics.compliance_score,
                    self.metrics.last_scan
                ))

        except Exception as e:
            self.logger.error(f"Error storing results: {e}")

    async def generate_security_patches(self, target_path: str) -> List[Dict]:
        """Generate security patches for identified vulnerabilities"""
        self.logger.info("🔧 Generating security patches...")
        
        patches = []
        
        for vuln in self.vulnerabilities:
            if vuln.severity in [SecurityLevel.CRITICAL, SecurityLevel.HIGH]:
                patch = await self._generate_patch_for_vulnerability(vuln, target_path)
                if patch:
                    patches.append(patch)
        
        return patches

    async def _generate_patch_for_vulnerability(self, vuln: SecurityVulnerability, target_path: str) -> Optional[Dict]:
        """Generate a patch for a specific vulnerability"""
        try:
            patch_content = None
            
            if vuln.category == VulnerabilityCategory.SECRETS:
                patch_content = self._generate_secrets_patch(vuln)
            elif vuln.category == VulnerabilityCategory.CODE_INJECTION:
                patch_content = self._generate_injection_patch(vuln)
            elif vuln.category == VulnerabilityCategory.CRYPTOGRAPHY:
                patch_content = self._generate_crypto_patch(vuln)
            elif vuln.category == VulnerabilityCategory.CONTAINER:
                patch_content = self._generate_container_patch(vuln)
            
            if patch_content:
                return {
                    "vulnerability_id": vuln.id,
                    "file_path": vuln.file_path,
                    "patch_content": patch_content,
                    "description": f"Security patch for: {vuln.title}",
                    "severity": vuln.severity.value,
                    "auto_apply": vuln.severity == SecurityLevel.CRITICAL
                }
        
        except Exception as e:
            self.logger.error(f"Error generating patch for {vuln.id}: {e}")
        
        return None

    def _generate_secrets_patch(self, vuln: SecurityVulnerability) -> str:
        """Generate patch for secrets vulnerability"""
        return f"""
# Security Patch: Remove hardcoded secret
# Original issue: {vuln.title} at line {vuln.line_number}
# Recommendation: Use environment variables or secure vault

import os

# Replace hardcoded secret with environment variable
# OLD: {vuln.title}
# NEW: Use os.environ.get() or secure credential storage

# Example:
# password = os.environ.get('DATABASE_PASSWORD')
# api_key = os.environ.get('API_KEY')

# For sensitive data, consider using:
# - AWS Secrets Manager
# - Azure Key Vault
# - HashiCorp Vault
# - Environment variables with proper access controls
"""

    def _generate_injection_patch(self, vuln: SecurityVulnerability) -> str:
        """Generate patch for injection vulnerability"""
        if "eval" in vuln.title.lower():
            return f"""
# Security Patch: Replace eval() with safe alternative
# Original issue: {vuln.title} at line {vuln.line_number}

import ast

# Replace eval() with ast.literal_eval() for safe evaluation
# OLD: result = eval(user_input)
# NEW: result = ast.literal_eval(user_input)  # Only for literals

# For more complex expressions, consider:
# - Using a restricted evaluation environment
# - Parsing and validating input manually
# - Using a safe expression evaluator library
"""
        elif "subprocess" in vuln.title.lower():
            return f"""
# Security Patch: Secure subprocess usage
# Original issue: {vuln.title} at line {vuln.line_number}

import subprocess
import shlex

# Replace shell=True with secure argument passing
# OLD: subprocess.call(command, shell=True)
# NEW: subprocess.run(shlex.split(command), check=True)

# Best practices:
# - Use subprocess.run() instead of subprocess.call()
# - Pass arguments as list, not string
# - Validate and sanitize all inputs
# - Use shell=False (default)
"""
        else:
            return f"""
# Security Patch: Address code injection vulnerability
# Original issue: {vuln.title} at line {vuln.line_number}

# General injection prevention:
# 1. Validate and sanitize all user inputs
# 2. Use parameterized queries for SQL
# 3. Escape output for web content
# 4. Use safe APIs and avoid dynamic code execution
# 5. Implement input validation and output encoding
"""

    def _generate_crypto_patch(self, vuln: SecurityVulnerability) -> str:
        """Generate patch for cryptography vulnerability"""
        return f"""
# Security Patch: Improve cryptographic implementation
# Original issue: {vuln.title} at line {vuln.line_number}

import secrets
import hashlib
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

# Use cryptographically secure random number generation
# OLD: import random; key = random.random()
# NEW: key = secrets.token_bytes(32)

# Use strong hashing algorithms
# OLD: hashlib.md5() or hashlib.sha1()
# NEW: hashlib.sha256() or hashlib.sha3_256()

# Use proper encryption
def secure_encrypt(data: bytes, password: str) -> bytes:
    # Generate a salt
    salt = secrets.token_bytes(16)
    
    # Derive key from password
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    key = kdf.derive(password.encode())
    
    # Encrypt data
    f = Fernet(key)
    encrypted = f.encrypt(data)
    
    return salt + encrypted

# Best practices:
# - Use established cryptographic libraries
# - Generate secure random keys and IVs
# - Use authenticated encryption
# - Implement proper key management
"""

    def _generate_container_patch(self, vuln: SecurityVulnerability) -> str:
        """Generate patch for container vulnerability"""
        if "root" in vuln.title.lower():
            return f"""
# Security Patch: Run container as non-root user
# Original issue: {vuln.title} at line {vuln.line_number}

# Add to Dockerfile:
# Create a non-root user
RUN addgroup -g 1001 -S appgroup && \\
    adduser -u 1001 -S appuser -G appgroup

# Switch to non-root user
USER appuser

# Ensure proper file permissions
COPY --chown=appuser:appgroup . /app
WORKDIR /app
"""
        elif "privileged" in vuln.title.lower():
            return f"""
# Security Patch: Remove privileged mode
# Original issue: {vuln.title} at line {vuln.line_number}

# Remove privileged mode and use specific capabilities instead
# OLD: privileged: true
# NEW: Use specific capabilities only when needed

# Example for docker-compose.yml:
# cap_add:
#   - NET_ADMIN  # Only if network administration is needed
#   - SYS_TIME   # Only if time modification is needed

# security_opt:
#   - no-new-privileges:true

# Best practices:
# - Use principle of least privilege
# - Drop unnecessary capabilities
# - Use read-only file systems when possible
# - Implement proper network segmentation
"""
        else:
            return f"""
# Security Patch: Container security hardening
# Original issue: {vuln.title} at line {vuln.line_number}

# Container security best practices:
# 1. Use minimal base images (Alpine, distroless)
# 2. Run as non-root user
# 3. Use specific versions, not 'latest' tags
# 4. Scan images for vulnerabilities
# 5. Implement proper secrets management
# 6. Use read-only file systems
# 7. Limit resource usage
# 8. Enable security scanning in CI/CD
"""

    def generate_security_report(self) -> str:
        """Generate comprehensive security report"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        report = f"""
================================================================================
                            NEXUS SECURITY ANALYSIS REPORT
================================================================================
Generated: {timestamp}
Security Score: {self.metrics.security_score:.2f}/1.0
Compliance Score: {self.metrics.compliance_score:.2f}/1.0

EXECUTIVE SUMMARY
================================================================================
Total Vulnerabilities: {self.metrics.total_vulnerabilities}
Critical: {self.metrics.critical_count}
High: {self.metrics.high_count}
Medium: {self.metrics.medium_count}
Low: {self.metrics.low_count}
Info: {self.metrics.info_count}

VULNERABILITY BREAKDOWN BY CATEGORY
================================================================================
"""
        
        # Count by category
        category_counts = {}
        for vuln in self.vulnerabilities:
            category = vuln.category.value
            if category not in category_counts:
                category_counts[category] = 0
            category_counts[category] += 1
        
        for category, count in sorted(category_counts.items()):
            report += f"{category.replace('_', ' ').title()}: {count}\n"
        
        report += f"""
CRITICAL AND HIGH SEVERITY VULNERABILITIES
================================================================================
"""
        
        critical_high = [v for v in self.vulnerabilities if v.severity in [SecurityLevel.CRITICAL, SecurityLevel.HIGH]]
        
        for vuln in critical_high[:10]:  # Show top 10
            report += f"""
[{vuln.severity.value.upper()}] {vuln.title}
File: {vuln.file_path}:{vuln.line_number}
Description: {vuln.description}
Remediation: {vuln.remediation or 'Review and remediate'}
CVE: {vuln.cve_id or 'N/A'}
Confidence: {vuln.confidence:.1f}
---
"""
        
        if len(critical_high) > 10:
            report += f"... and {len(critical_high) - 10} more critical/high severity issues\n"
        
        report += f"""
SECURITY RECOMMENDATIONS
================================================================================
"""
        
        recommendations = self._generate_recommendations()
        for i, rec in enumerate(recommendations, 1):
            report += f"""
{i}. [{rec['priority']}] {rec['title']}
   Category: {rec['category']}
   Description: {rec['description']}
   Actions:
"""
            for action in rec['actions']:
                report += f"   - {action}\n"
            report += "\n"
        
        report += f"""
SECURITY METRICS TREND
================================================================================
Current Security Score: {self.metrics.security_score:.2f}
Target Security Score: 0.90+
Compliance Score: {self.metrics.compliance_score:.2f}

NEXT STEPS
================================================================================
1. Address all critical vulnerabilities immediately
2. Fix high-severity issues within 24-48 hours
3. Implement security patches using auto_patcher.py
4. Set up automated security scanning in CI/CD pipeline
5. Conduct regular security reviews and training
6. Monitor security metrics and trends

================================================================================
End of Report
================================================================================
"""
        
        return report


async def main():
    """Main entry point for security analyzer"""
    import argparse
    
    parser = argparse.ArgumentParser(description="NEXUS Security Analyzer")
    parser.add_argument("--path", default=".", help="Path to analyze")
    parser.add_argument("--config", help="Configuration file path")
    parser.add_argument("--output", help="Output report file")
    parser.add_argument("--generate-patches", action="store_true", help="Generate security patches")
    
    args = parser.parse_args()
    
    # Initialize analyzer
    analyzer = SecurityAnalyzer(config_path=args.config)
    
    # Run analysis
    results = await analyzer.analyze_codebase(args.path)
    
    # Generate report
    report = analyzer.generate_security_report()
    
    if args.output:
        with open(args.output, 'w') as f:
            f.write(report)
        print(f"✅ Security report saved to {args.output}")
    else:
        print(report)
    
    # Generate patches if requested
    if args.generate_patches:
        patches = await analyzer.generate_security_patches(args.path)
        print(f"✅ Generated {len(patches)} security patches")
        
        # Save patches
        patches_file = f"security_patches_{datetime.now():%Y%m%d_%H%M%S}.json"
        with open(patches_file, 'w') as f:
            json.dump(patches, f, indent=2)
        print(f"✅ Patches saved to {patches_file}")
    
    # Print summary
    print(f"\n🔒 Security Analysis Complete")
    print(f"Security Score: {analyzer.metrics.security_score:.2f}/1.0")
    print(f"Total Vulnerabilities: {analyzer.metrics.total_vulnerabilities}")
    print(f"Critical: {analyzer.metrics.critical_count}")
    print(f"High: {analyzer.metrics.high_count}")


if __name__ == "__main__":
    asyncio.run(main())