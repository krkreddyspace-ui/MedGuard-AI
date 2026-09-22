"""
MedGuard - Automated Test Runner
Runs the full pytest test suite and reports test results.
"""
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def main():
    print("=" * 65)
    print("MedGuard: Running Unit & Integration Tests")
    print("=" * 65)

    cmd = [sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short"]
    result = subprocess.run(cmd, cwd=str(BASE_DIR))

    print("-" * 65)
    if result.returncode == 0:
        print("[SUCCESS] All tests passed cleanly.")
    else:
        print(f"[FAILURE] Tests failed with exit code {result.returncode}")
    print("=" * 65)
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
