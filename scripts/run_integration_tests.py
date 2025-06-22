#!/usr/bin/env python3
"""
Test runner script for WebSocket integration tests
Perfect for local development and CI/CD pipelines
"""
import subprocess
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
os.chdir(project_root)

def run_tests(test_pattern="", verbose=True, markers=""):
    """Run pytest with specified options"""
    cmd = ["uv", "run", "pytest"]
    
    if verbose:
        cmd.append("-v")
    
    if markers:
        cmd.extend(["-m", markers])
    
    # Add coverage if available
    cmd.extend([
        "--tb=short",  # Shorter traceback format
        "--strict-markers",  # Strict marker checking
    ])
    
    if test_pattern:
        cmd.append(f"tests/{test_pattern}")
    else:
        cmd.append("tests/test_websocket_integration.py")
    
    print(f"🧪 Running: {' '.join(cmd)}")
    print("=" * 60)
    
    result = subprocess.run(cmd, cwd=project_root)
    return result.returncode

def main():
    """Main test runner"""
    print("🚀 Mindful Touch - WebSocket Integration Test Runner")
    print("=" * 60)
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "--help":
            print("Usage: python scripts/run_integration_tests.py [OPTIONS]")
            print("\nOptions:")
            print("  --help                Show this help")
            print("  --unit               Run only unit-style WebSocket tests (fast)")
            print("  --integration        Run only full integration tests (slow)")
            print("  --all                Run all tests")
            print("  --quick              Run quick smoke tests only")
            print("\nExamples:")
            print("  python scripts/run_integration_tests.py")
            print("  python scripts/run_integration_tests.py --unit")
            print("  python scripts/run_integration_tests.py --integration")
            return 0
        
        elif sys.argv[1] == "--unit":
            print("🔌 Running WebSocket unit tests (no backend process)...")
            return run_tests(markers="not backend")
        
        elif sys.argv[1] == "--integration":
            print("🔗 Running full integration tests (with backend process)...")
            return run_tests(markers="backend")
        
        elif sys.argv[1] == "--quick":
            print("⚡ Running quick smoke tests...")
            return run_tests("test_websocket_integration.py::TestWebSocketServer::test_server_startup_and_connection")
        
        elif sys.argv[1] == "--all":
            print("🎯 Running all integration tests...")
            return run_tests()
    
    # Default: run all tests
    print("🎯 Running all WebSocket integration tests...")
    return run_tests()

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)