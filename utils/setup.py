"""
Anticipa - Server Deployment Setup and Validation
Installs requirements and validates environment for server deployment
"""

import subprocess
import sys
import os
import socket
import re
from pathlib import Path
from typing import List, Tuple, Dict


class SetupValidator:
    """Validates and sets up the environment for server deployment"""
    
    def __init__(self, project_root: Path = None):
        """Initialize validator with project root path"""
        if project_root is None:
            # Assume this script is in utils/, so go up one level
            self.project_root = Path(__file__).parent.parent
        else:
            self.project_root = Path(project_root)
        
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.checks_passed = 0
        self.checks_failed = 0
    
    def check_python_version(self) -> bool:
        """Check if Python version meets requirements (>= 3.10)"""
        print("Checking Python version...")
        version = sys.version_info
        if version.major >= 3 and version.minor >= 10:
            print(f"  ✓ Python {version.major}.{version.minor}.{version.micro}")
            self.checks_passed += 1
            return True
        else:
            error_msg = f"  ✗ Python {version.major}.{version.minor}.{version.micro} - Requires Python >= 3.10"
            print(error_msg)
            self.errors.append(error_msg)
            self.checks_failed += 1
            return False
    
    def check_package_installed(self, package_name: str) -> bool:
        """Check if a package is already installed"""
        try:
            # Try to import the package
            if package_name == "pyyaml":
                __import__("yaml")
            elif package_name == "python-dotenv":
                __import__("dotenv")
            else:
                __import__(package_name.replace("-", "_"))
            return True
        except ImportError:
            return False
    
    def get_missing_packages(self) -> List[str]:
        """Get list of missing packages from requirements.txt"""
        requirements_file = self.project_root / "requirements.txt"
        
        if not requirements_file.exists():
            return []
        
        missing = []
        try:
            with open(requirements_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    # Skip comments and empty lines
                    if not line or line.startswith('#'):
                        continue
                    
                    # Extract package name (handle version constraints)
                    # e.g., "pandas>=1.5.0,<3.0.0" -> "pandas"
                    # Handle various separators: >=, ==, <=, <, >, ~=, !=
                    # Match package name (word characters, dots, hyphens) before any version specifier
                    match = re.match(r'^([a-zA-Z0-9._-]+)', line)
                    if match:
                        package_name = match.group(1).strip()
                        
                        # Check if installed
                        if not self.check_package_installed(package_name):
                            missing.append(line)
        except Exception as e:
            print(f"  ⚠ Error reading requirements.txt: {e}")
        
        return missing
    
    def install_requirements(self, force: bool = False) -> bool:
        """Install dependencies from requirements.txt (only missing packages)"""
        print("\nChecking requirements...")
        requirements_file = self.project_root / "requirements.txt"
        
        if not requirements_file.exists():
            error_msg = f"  ✗ requirements.txt not found at {requirements_file}"
            print(error_msg)
            self.errors.append(error_msg)
            self.checks_failed += 1
            return False
        
        # Check which packages are missing
        missing_packages = self.get_missing_packages()
        
        if not missing_packages and not force:
            print("  ✓ All required packages are already installed")
            self.checks_passed += 1
            return True
        
        if missing_packages:
            print(f"  → Found {len(missing_packages)} missing package(s)")
        
        try:
            # Only upgrade pip if we need to install packages
            if missing_packages:
                print("  → Upgrading pip...")
                subprocess.run(
                    [sys.executable, "-m", "pip", "install", "--upgrade", "pip", "--quiet"],
                    check=True,
                    capture_output=True
                )
            
            # Install requirements (pip will skip already installed packages)
            if force or missing_packages:
                print("  → Installing/updating packages from requirements.txt...")
                result = subprocess.run(
                    [sys.executable, "-m", "pip", "install", "-r", str(requirements_file), "--quiet"],
                    check=True,
                    capture_output=True,
                    text=True
                )
                print("  ✓ Requirements installed/updated successfully")
            else:
                print("  ✓ All requirements satisfied")
            
            self.checks_passed += 1
            return True
            
        except subprocess.CalledProcessError as e:
            error_msg = f"  ✗ Failed to install requirements: {e}"
            print(error_msg)
            if e.stderr:
                error_output = e.stderr.decode() if isinstance(e.stderr, bytes) else e.stderr
                # Only show error details if not too verbose
                if len(error_output) < 500:
                    print(f"    Error details: {error_output}")
            self.errors.append(error_msg)
            self.checks_failed += 1
            return False
    
    def verify_dependencies(self) -> bool:
        """Verify that all required packages are installed"""
        print("\nVerifying dependencies...")
        
        required_packages = {
            "pandas": "pandas",
            "numpy": "numpy",
            "lightgbm": "lightgbm",
            "scipy": "scipy",
            "streamlit": "streamlit",
            "yaml": "yaml",
            "dotenv": "dotenv",
        }
        
        optional_packages = {
            "supabase": "supabase",
            "bcrypt": "bcrypt",
        }
        
        all_required = True
        
        # Check required packages
        for display_name, import_name in required_packages.items():
            try:
                __import__(import_name)
                print(f"  ✓ {display_name}")
                self.checks_passed += 1
            except ImportError:
                error_msg = f"  ✗ {display_name} - NOT FOUND"
                print(error_msg)
                self.errors.append(error_msg)
                self.checks_failed += 1
                all_required = False
        
        # Check optional packages
        for display_name, import_name in optional_packages.items():
            try:
                __import__(import_name)
                print(f"  ✓ {display_name} (optional)")
                self.checks_passed += 1
            except ImportError:
                warning_msg = f"  ⚠ {display_name} (optional) - NOT FOUND"
                print(warning_msg)
                self.warnings.append(warning_msg)
        
        return all_required
    
    def check_project_structure(self) -> bool:
        """Check if required directories and files exist"""
        print("\nChecking project structure...")
        
        required_dirs = [
            "app",
            "forecaster",
            "optimizer",
            "router",
            "utils",
            "output",
        ]
        
        required_files = [
            "config.yaml",
            "requirements.txt",
            "run_app.py",
            "app/app.py",
        ]
        
        all_present = True
        
        # Check directories
        for dir_name in required_dirs:
            dir_path = self.project_root / dir_name
            if dir_path.exists() and dir_path.is_dir():
                print(f"  ✓ Directory: {dir_name}/")
                self.checks_passed += 1
            else:
                error_msg = f"  ✗ Missing directory: {dir_name}/"
                print(error_msg)
                self.errors.append(error_msg)
                self.checks_failed += 1
                all_present = False
        
        # Check files
        for file_name in required_files:
            file_path = self.project_root / file_name
            if file_path.exists() and file_path.is_file():
                print(f"  ✓ File: {file_name}")
                self.checks_passed += 1
            else:
                error_msg = f"  ✗ Missing file: {file_name}"
                print(error_msg)
                self.errors.append(error_msg)
                self.checks_failed += 1
                all_present = False
        
        return all_present
    
    def check_config_file(self) -> bool:
        """Validate config.yaml exists and is readable"""
        print("\nChecking configuration file...")
        
        config_file = self.project_root / "config.yaml"
        
        if not config_file.exists():
            error_msg = "  ✗ config.yaml not found"
            print(error_msg)
            self.errors.append(error_msg)
            self.checks_failed += 1
            return False
        
        try:
            import yaml
            with open(config_file, 'r') as f:
                config = yaml.safe_load(f)
            
            if config is None or not isinstance(config, dict):
                warning_msg = "  ⚠ config.yaml is empty or invalid"
                print(warning_msg)
                self.warnings.append(warning_msg)
            else:
                print("  ✓ config.yaml is valid")
                self.checks_passed += 1
            
            return True
            
        except yaml.YAMLError as e:
            error_msg = f"  ✗ config.yaml has syntax errors: {e}"
            print(error_msg)
            self.errors.append(error_msg)
            self.checks_failed += 1
            return False
        except Exception as e:
            error_msg = f"  ✗ Error reading config.yaml: {e}"
            print(error_msg)
            self.errors.append(error_msg)
            self.checks_failed += 1
            return False
    
    def check_file_permissions(self) -> bool:
        """Check if output directory is writable"""
        print("\nChecking file permissions...")
        
        output_dir = self.project_root / "output"
        
        # Create output directory if it doesn't exist
        if not output_dir.exists():
            try:
                output_dir.mkdir(parents=True, exist_ok=True)
                print("  ✓ Created output/ directory")
                self.checks_passed += 1
            except Exception as e:
                error_msg = f"  ✗ Cannot create output/ directory: {e}"
                print(error_msg)
                self.errors.append(error_msg)
                self.checks_failed += 1
                return False
        
        # Test write permissions
        try:
            test_file = output_dir / ".write_test"
            test_file.write_text("test")
            test_file.unlink()
            print("  ✓ output/ directory is writable")
            self.checks_passed += 1
            return True
        except Exception as e:
            error_msg = f"  ✗ output/ directory is not writable: {e}"
            print(error_msg)
            self.errors.append(error_msg)
            self.checks_failed += 1
            return False
    
    def check_port_availability(self, port: int = 8501) -> bool:
        """Check if Streamlit default port is available"""
        print(f"\nChecking port availability (port {port})...")
        
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                result = s.connect_ex(('localhost', port))
                if result == 0:
                    warning_msg = f"  ⚠ Port {port} is already in use"
                    print(warning_msg)
                    self.warnings.append(warning_msg)
                    return True  # Not a critical error, just a warning
                else:
                    print(f"  ✓ Port {port} is available")
                    self.checks_passed += 1
                    return True
        except Exception as e:
            warning_msg = f"  ⚠ Could not check port {port}: {e}"
            print(warning_msg)
            self.warnings.append(warning_msg)
            return True  # Not critical
    
    def check_environment_variables(self) -> bool:
        """Check optional environment variables for production"""
        print("\nChecking environment variables...")
        
        env_vars = {
            "SUPABASE_URL": "optional",
            "SUPABASE_KEY": "optional",
        }
        
        found_any = False
        for var_name, status in env_vars.items():
            value = os.getenv(var_name)
            if value:
                print(f"  ✓ {var_name} is set")
                self.checks_passed += 1
                found_any = True
            else:
                if status == "optional":
                    print(f"  ⚠ {var_name} not set (optional for demo mode)")
                else:
                    error_msg = f"  ✗ {var_name} not set (required)"
                    print(error_msg)
                    self.errors.append(error_msg)
                    self.checks_failed += 1
        
        if not found_any:
            print("  ℹ No Supabase credentials found - will use demo mode")
            self.checks_passed += 1
        
        return True  # Environment vars are optional
    
    def run_all_checks(self, install_deps: bool = True, force_install: bool = False) -> bool:
        """Run all validation checks"""
        print("=" * 70)
        print("Anticipa - Server Deployment Setup and Validation")
        print("=" * 70)
        print(f"Project root: {self.project_root}")
        print()
        
        # Step 1: Check Python version
        if not self.check_python_version():
            print("\n✗ Python version check failed. Please upgrade to Python >= 3.10")
            return False
        
        # Step 2: Install requirements (only missing ones)
        if install_deps:
            if not self.install_requirements(force=force_install):
                print("\n✗ Failed to install requirements")
                return False
        
        # Step 3: Verify dependencies
        if not self.verify_dependencies():
            print("\n✗ Dependency verification failed")
            return False
        
        # Step 4: Check project structure
        if not self.check_project_structure():
            print("\n✗ Project structure check failed")
            return False
        
        # Step 5: Check config file
        self.check_config_file()
        
        # Step 6: Check file permissions
        if not self.check_file_permissions():
            print("\n✗ File permissions check failed")
            return False
        
        # Step 7: Check port availability
        self.check_port_availability()
        
        # Step 8: Check environment variables
        self.check_environment_variables()
        
        # Summary
        print("\n" + "=" * 70)
        print("Validation Summary")
        print("=" * 70)
        print(f"✓ Passed: {self.checks_passed}")
        print(f"✗ Failed: {self.checks_failed}")
        print(f"⚠ Warnings: {len(self.warnings)}")
        
        if self.errors:
            print("\nErrors:")
            for error in self.errors:
                print(f"  {error}")
        
        if self.warnings:
            print("\nWarnings:")
            for warning in self.warnings:
                print(f"  {warning}")
        
        if self.checks_failed == 0:
            print("\n" + "=" * 70)
            print("✓ All checks passed! Server is ready for deployment.")
            print("=" * 70)
            print("\nNext steps:")
            print("  1. Run 'python run_app.py' to start the Streamlit app")
            print("  2. Configure Supabase credentials in .env for production")
            print("  3. Review config.yaml for custom settings")
            print()
            return True
        else:
            print("\n" + "=" * 70)
            print("✗ Validation failed. Please fix the errors above.")
            print("=" * 70)
            return False


def main():
    """Main entry point for setup script"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Anticipa server deployment setup and validation"
    )
    parser.add_argument(
        "--no-install",
        action="store_true",
        help="Skip dependency installation (only validate)"
    )
    parser.add_argument(
        "--project-root",
        type=str,
        default=None,
        help="Path to project root directory (default: auto-detect)"
    )
    
    args = parser.parse_args()
    
    project_root = Path(args.project_root) if args.project_root else None
    validator = SetupValidator(project_root)
    
    success = validator.run_all_checks(install_deps=not args.no_install)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

