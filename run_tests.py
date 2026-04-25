#!/usr/bin/env python3
"""
Test runner script for the FastAPI application.
Provides convenient commands to run different types of tests.
"""

import subprocess
import sys
import argparse
from pathlib import Path


def run_command(command, description):
    """Run a shell command and print the description."""
    print(f"\n🚀 {description}")
    print("=" * 60)
    
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=False)
        print(f"✅ {description} completed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed with exit code {e.returncode}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Run tests for FastAPI application")
    parser.add_argument(
        "test_type",
        nargs="?",
        choices=["unit", "integration", "all", "coverage", "lint", "security"],
        default="all",
        help="Type of tests to run (default: all)"
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    parser.add_argument("-f", "--file", help="Run specific test file")
    parser.add_argument("--install", action="store_true", help="Install test dependencies")
    
    args = parser.parse_args()
    
    # Install test dependencies if requested
    if args.install:
        if not run_command("pip install -r test_suite/requirements.txt", "Installing test dependencies"):
            sys.exit(1)
        return
    
    # Base pytest command
    pytest_cmd = "pytest"
    if args.verbose:
        pytest_cmd += " -v"
    
    success = True
    
    if args.file:
        # Run specific test file
        success = run_command(f"{pytest_cmd} {args.file}", f"Running tests in {args.file}")
    
    elif args.test_type == "unit":
        success = run_command(f"{pytest_cmd} test_suite/unit/ -m unit", "Running unit tests")
    
    elif args.test_type == "integration":
        success = run_command(f"{pytest_cmd} test_suite/integration/ -m integration", "Running integration tests")
    
    elif args.test_type == "coverage":
        commands = [
            (f"{pytest_cmd} test_suite/ --cov=. --cov-report=html --cov-report=term", "Running tests with coverage"),
            ("echo 'Coverage report generated in htmlcov/index.html'", "Coverage report location")
        ]
        for cmd, desc in commands:
            if not run_command(cmd, desc):
                success = False
                break
    
    elif args.test_type == "lint":
        commands = [
            ("flake8 . --exclude=test_suite/fixtures,htmlcov,__pycache__", "Running code linting"),
            ("black --check .", "Checking code formatting"),
            ("isort --check-only .", "Checking import sorting")
        ]
        for cmd, desc in commands:
            run_command(cmd, desc)  # Don't fail on lint errors
    
    elif args.test_type == "security":
        commands = [
            ("bandit -r . -x test_suite,htmlcov", "Running security checks"),
            ("safety check", "Checking for known security vulnerabilities")
        ]
        for cmd, desc in commands:
            run_command(cmd, desc)  # Don't fail on security warnings
    
    elif args.test_type == "all":
        commands = [
            (f"{pytest_cmd} test_suite/unit/ -m unit", "Running unit tests"),
            (f"{pytest_cmd} test_suite/integration/ -m integration", "Running integration tests"),
            (f"{pytest_cmd} test_suite/ --cov=. --cov-report=term-missing", "Running all tests with coverage")
        ]
        for cmd, desc in commands:
            if not run_command(cmd, desc):
                success = False
                # Continue with other tests even if one fails
    
    if success:
        print("\n🎉 All tests completed successfully!")
        sys.exit(0)
    else:
        print("\n💥 Some tests failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
