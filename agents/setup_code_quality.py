"""
Setup script for NEXUS-RSI Code Quality Analyzer Agent
"""

import json
import subprocess
import sys
from pathlib import Path

def install_dependencies():
    """Install required dependencies for code quality analysis"""
    dependencies = [
        "radon",           # Code complexity analysis
        "flake8",          # Style guide enforcement
        "pylint",          # Code analysis
        "black",           # Code formatting
        "mypy",            # Type checking
        "coverage",        # Test coverage
        "bandit",          # Security linting
        "vulture",         # Dead code detection
        "mccabe",          # Complexity checker
        "autopep8",        # Auto-formatting
        "isort",           # Import sorting
    ]
    
    print("📦 Installing code quality dependencies...")
    
    for dep in dependencies:
        try:
            print(f"Installing {dep}...")
            subprocess.run([sys.executable, "-m", "pip", "install", dep], 
                         check=True, capture_output=True)
            print(f"✅ {dep} installed successfully")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install {dep}: {e}")
            print("Continuing with other dependencies...")

def create_config_files():
    """Create configuration files for quality tools"""
    
    # .pylintrc configuration
    pylintrc_content = """
[MASTER]
load-plugins=pylint.extensions.docparams

[MESSAGES CONTROL]
disable=missing-module-docstring,
        missing-class-docstring,
        missing-function-docstring,
        line-too-long,
        too-few-public-methods,
        too-many-arguments,
        too-many-locals,
        import-outside-toplevel

[FORMAT]
max-line-length=88
indent-string='    '

[DESIGN]
max-args=8
max-locals=20
max-returns=6
max-branches=15
max-statements=50

[SIMILARITIES]
min-similarity-lines=4
ignore-comments=yes
ignore-docstrings=yes
ignore-imports=no
"""
    
    # setup.cfg for flake8
    setup_cfg_content = """
[flake8]
max-line-length = 88
extend-ignore = E203, W503
exclude = 
    .git,
    __pycache__,
    docs/source/conf.py,
    old,
    build,
    dist,
    .tox,
    .venv,
    venv,
    migrations

max-complexity = 10
"""
    
    # mypy.ini configuration
    mypy_ini_content = """
[mypy]
python_version = 3.8
warn_return_any = True
warn_unused_configs = True
disallow_untyped_defs = True
disallow_incomplete_defs = True
check_untyped_defs = True
disallow_untyped_decorators = True
no_implicit_optional = True
warn_redundant_casts = True
warn_unused_ignores = True
warn_no_return = True
warn_unreachable = True
strict_equality = True
"""
    
    # .coveragerc for coverage
    coveragerc_content = """
[run]
source = .
omit = 
    */tests/*
    */test_*
    */__pycache__/*
    */migrations/*
    */venv/*
    */.venv/*
    setup.py
    */conftest.py

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    if self.debug:
    if settings.DEBUG
    raise AssertionError
    raise NotImplementedError
    if 0:
    if __name__ == .__main__.:
    class .*\bProtocol\):
    @(abc\.)?abstractmethod

[html]
directory = htmlcov
"""
    
    # pyproject.toml for black
    pyproject_toml_content = """
[tool.black]
line-length = 88
target-version = ['py38', 'py39', 'py310', 'py311']
include = '\.pyi?$'
extend-exclude = '''
/(
  # directories
  \.eggs
  | \.git
  | \.hg
  | \.mypy_cache
  | \.tox
  | \.venv
  | build
  | dist
)/
'''

[tool.isort]
profile = "black"
multi_line_output = 3
line_length = 88
"""
    
    config_files = {
        ".pylintrc": pylintrc_content,
        "setup.cfg": setup_cfg_content,
        "mypy.ini": mypy_ini_content,
        ".coveragerc": coveragerc_content,
        "pyproject.toml": pyproject_toml_content
    }
    
    print("📝 Creating configuration files...")
    
    for filename, content in config_files.items():
        file_path = Path(filename)
        if not file_path.exists():
            with open(file_path, 'w') as f:
                f.write(content.strip())
            print(f"✅ Created {filename}")
        else:
            print(f"ℹ️  {filename} already exists, skipping...")

def setup_quality_gates():
    """Setup pre-commit hooks and quality gates"""
    
    # Pre-commit configuration
    pre_commit_config = """
repos:
  - repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
      - id: black
        language_version: python3.8

  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort
        args: ["--profile", "black"]

  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8

  - repo: https://github.com/pycqa/pylint
    rev: v3.0.0a6
    hooks:
      - id: pylint

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.3.0
    hooks:
      - id: mypy
        additional_dependencies: [types-requests]

  - repo: https://github.com/PyCQA/bandit
    rev: 1.7.5
    hooks:
      - id: bandit
        args: ["-c", "pyproject.toml"]
        additional_dependencies: ["bandit[toml]"]
"""
    
    pre_commit_file = Path(".pre-commit-config.yaml")
    if not pre_commit_file.exists():
        with open(pre_commit_file, 'w') as f:
            f.write(pre_commit_config.strip())
        print("✅ Created .pre-commit-config.yaml")
        
        # Install pre-commit
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "pre-commit"], 
                         check=True, capture_output=True)
            subprocess.run(["pre-commit", "install"], check=True, capture_output=True)
            print("✅ Pre-commit hooks installed")
        except subprocess.CalledProcessError:
            print("⚠️  Failed to install pre-commit hooks")
    else:
        print("ℹ️  Pre-commit config already exists")

def create_quality_scripts():
    """Create quality check scripts"""
    
    # Quality check script
    quality_check_script = """#!/usr/bin/env python3
\"\"\"
Code Quality Check Script for NEXUS-RSI
\"\"\"

import subprocess
import sys
from pathlib import Path

def run_command(cmd, description):
    \"\"\"Run a command and return success status\"\"\"
    print(f"\\n🔍 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description} passed")
            return True
        else:
            print(f"❌ {description} failed:")
            print(result.stdout)
            print(result.stderr)
            return False
    except Exception as e:
        print(f"❌ {description} error: {e}")
        return False

def main():
    \"\"\"Run all quality checks\"\"\"
    print("🚀 Running NEXUS-RSI Code Quality Checks")
    
    checks = [
        ("black --check --diff .", "Black formatting check"),
        ("isort --check-only --diff .", "Import sorting check"),
        ("flake8 .", "Flake8 style check"),
        ("pylint agents/ --score=yes", "Pylint analysis"),
        ("mypy agents/", "Type checking"),
        ("bandit -r agents/", "Security check"),
        ("vulture agents/ --min-confidence 60", "Dead code check"),
        ("radon cc agents/ -a", "Complexity analysis"),
    ]
    
    passed = 0
    total = len(checks)
    
    for cmd, description in checks:
        if run_command(cmd, description):
            passed += 1
    
    print(f"\\n📊 Quality Check Results: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 All quality checks passed!")
        return 0
    else:
        print("⚠️  Some quality checks failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
"""
    
    # Auto-fix script
    auto_fix_script = """#!/usr/bin/env python3
\"\"\"
Auto-fix Code Quality Issues for NEXUS-RSI
\"\"\"

import subprocess
import sys

def run_fix_command(cmd, description):
    \"\"\"Run a fix command\"\"\"
    print(f"\\n🔧 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        print(f"✅ {description} completed")
        if result.stdout:
            print(result.stdout)
        return True
    except Exception as e:
        print(f"❌ {description} error: {e}")
        return False

def main():
    \"\"\"Run auto-fixes for common issues\"\"\"
    print("🔧 Running NEXUS-RSI Code Quality Auto-fixes")
    
    fixes = [
        ("black .", "Black code formatting"),
        ("isort .", "Import sorting"),
        ("autopep8 --in-place --recursive .", "PEP8 auto-fixes"),
        ("vulture agents/ --make-whitelist > vulture_whitelist.py", "Generate dead code whitelist"),
    ]
    
    for cmd, description in fixes:
        run_fix_command(cmd, description)
    
    print("\\n✅ Auto-fixes completed!")
    print("📝 Run quality checks again to verify fixes")

if __name__ == "__main__":
    main()
"""
    
    scripts = {
        "quality_check.py": quality_check_script,
        "auto_fix.py": auto_fix_script
    }
    
    scripts_dir = Path("scripts")
    scripts_dir.mkdir(exist_ok=True)
    
    for filename, content in scripts.items():
        script_path = scripts_dir / filename
        with open(script_path, 'w') as f:
            f.write(content.strip())
        
        # Make executable on Unix systems
        try:
            script_path.chmod(0o755)
        except:
            pass
        
        print(f"✅ Created {script_path}")

def create_github_workflow():
    """Create GitHub Actions workflow for quality checks"""
    
    workflow_content = """
name: Code Quality

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  quality:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.8, 3.9, "3.10", "3.11"]

    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install radon flake8 pylint black mypy coverage bandit vulture
    
    - name: Run Black
      run: black --check --diff .
    
    - name: Run isort
      run: isort --check-only --diff .
    
    - name: Run flake8
      run: flake8 .
    
    - name: Run pylint
      run: pylint agents/ --score=yes
    
    - name: Run mypy
      run: mypy agents/
    
    - name: Run bandit
      run: bandit -r agents/
    
    - name: Run tests with coverage
      run: |
        coverage run -m pytest
        coverage report --show-missing
        coverage html
    
    - name: Run complexity analysis
      run: radon cc agents/ -a
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
        flags: unittests
        name: codecov-umbrella
"""
    
    workflows_dir = Path(".github/workflows")
    workflows_dir.mkdir(parents=True, exist_ok=True)
    
    workflow_path = workflows_dir / "quality.yml"
    with open(workflow_path, 'w') as f:
        f.write(workflow_content.strip())
    
    print(f"✅ Created GitHub workflow: {workflow_path}")

def update_requirements():
    """Update requirements.txt with quality tools"""
    
    quality_requirements = [
        "radon>=6.0.1",
        "flake8>=6.0.0",
        "pylint>=3.0.0",
        "black>=23.0.0",
        "mypy>=1.3.0",
        "coverage>=7.2.0",
        "bandit>=1.7.5",
        "vulture>=2.7",
        "mccabe>=0.7.0",
        "autopep8>=2.0.0",
        "isort>=5.12.0",
        "pre-commit>=3.3.0"
    ]
    
    requirements_file = Path("requirements.txt")
    
    if requirements_file.exists():
        with open(requirements_file, 'r') as f:
            existing_requirements = f.read()
    else:
        existing_requirements = ""
    
    # Add quality requirements if not already present
    new_requirements = []
    for req in quality_requirements:
        package_name = req.split(">=")[0]
        if package_name not in existing_requirements:
            new_requirements.append(req)
    
    if new_requirements:
        with open(requirements_file, 'a') as f:
            f.write("\\n# Code Quality Tools\\n")
            for req in new_requirements:
                f.write(f"{req}\\n")
        
        print(f"✅ Added {len(new_requirements)} quality tools to requirements.txt")
    else:
        print("ℹ️  Quality tools already in requirements.txt")

def verify_installation():
    """Verify that the code quality analyzer is properly installed"""
    
    print("\\n🔍 Verifying Code Quality Analyzer installation...")
    
    # Check if config file exists
    config_file = Path("agents/code_quality.json")
    if config_file.exists():
        print("✅ Configuration file found")
    else:
        print("❌ Configuration file missing")
        return False
    
    # Check if analyzer script exists
    analyzer_file = Path("agents/code_quality.py")
    if analyzer_file.exists():
        print("✅ Analyzer script found")
    else:
        print("❌ Analyzer script missing")
        return False
    
    # Test import
    try:
        sys.path.insert(0, str(Path("agents").absolute()))
        import code_quality
        print("✅ Code quality module imports successfully")
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    
    # Test basic functionality
    try:
        analyzer = code_quality.CodeQualityAnalyzer()
        print("✅ Code quality analyzer initializes successfully")
    except Exception as e:
        print(f"❌ Initialization error: {e}")
        return False
    
    print("🎉 Code Quality Analyzer installation verified!")
    return True

def main():
    \"\"\"Main setup function\"\"\"
    print("🚀 Setting up NEXUS-RSI Code Quality Analyzer")
    print("=" * 50)
    
    try:
        # Install dependencies
        install_dependencies()
        
        # Create configuration files
        create_config_files()
        
        # Setup quality gates
        setup_quality_gates()
        
        # Create utility scripts
        create_quality_scripts()
        
        # Create GitHub workflow
        create_github_workflow()
        
        # Update requirements
        update_requirements()
        
        # Verify installation
        if verify_installation():
            print("\\n" + "=" * 50)
            print("🎉 Code Quality Analyzer setup completed successfully!")
            print("\\n📋 Next steps:")
            print("1. Run: python agents/code_quality.py --project .")
            print("2. Check quality reports in: quality_reports/")
            print("3. Run: python scripts/quality_check.py")
            print("4. Configure your IDE with the quality tools")
        else:
            print("\\n❌ Setup completed with errors. Please check the output above.")
            return 1
            
    except Exception as e:
        print(f"\\n❌ Setup failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
"""