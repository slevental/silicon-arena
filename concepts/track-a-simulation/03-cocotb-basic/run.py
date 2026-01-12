#!/usr/bin/env python3
"""
Cocotb Basic Testbench Concept Script

Task ID: silicon-arena-6g7.7
Spec Reference: File 2 (RL Verification Gym Architecture.md) - "Cocotb testbenches"

This script demonstrates:
1. Running Cocotb tests with Verilator
2. Collecting functional coverage
3. Generating test reports
"""

import json
import subprocess
import sys
from pathlib import Path


def run_command(cmd: list[str], cwd: Path | None = None) -> tuple[int, str, str]:
    """Run a command and return (returncode, stdout, stderr)."""
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    return result.returncode, result.stdout, result.stderr


def check_cocotb_installed() -> bool:
    """Check if cocotb is installed."""
    rc, stdout, _ = run_command(["python", "-c", "import cocotb; print(cocotb.__version__)"])
    return rc == 0


def main():
    script_dir = Path(__file__).parent.resolve()

    print("=" * 60)
    print("Cocotb Basic Testbench Concept Script")
    print("=" * 60)
    print()

    # Step 1: Check prerequisites
    print("[1/4] Checking prerequisites...")

    # Check Verilator
    rc, stdout, _ = run_command(["verilator", "--version"])
    if rc != 0:
        print("ERROR: Verilator not found")
        sys.exit(1)
    print(f"      Verilator: {stdout.strip().split()[1]}")

    # Check Cocotb
    if not check_cocotb_installed():
        print("ERROR: Cocotb not installed")
        print("      Install with: pip install cocotb")
        sys.exit(1)

    rc, stdout, _ = run_command(["python", "-c", "import cocotb; print(cocotb.__version__)"])
    print(f"      Cocotb: {stdout.strip()}")
    print()

    # Step 2: Clean previous runs
    print("[2/4] Cleaning previous build...")
    run_command(["make", "clean-all"], cwd=script_dir)
    print("      Done")
    print()

    # Step 3: Run Cocotb tests
    print("[3/4] Running Cocotb testbench...")
    print("-" * 60)
    rc, stdout, stderr = run_command(["make"], cwd=script_dir)

    # Print output
    if stdout:
        for line in stdout.split("\n"):
            if "PASS" in line or "FAIL" in line or "INFO" in line:
                print(f"      {line}")

    if rc != 0:
        print()
        print("ERROR: Cocotb tests failed")
        if stderr:
            print(stderr)
        sys.exit(1)

    print()
    print("      All tests passed!")
    print()

    # Step 4: Show coverage results
    print("[4/4] Coverage analysis...")
    print("-" * 60)

    coverage_file = script_dir / "cocotb_coverage.json"
    if coverage_file.exists():
        coverage = json.loads(coverage_file.read_text())

        op_names = ["ADD", "SUB", "AND", "OR", "XOR", "NOT", "SHL", "SHR"]

        print("      Operation Coverage:")
        ops_tested = 0
        for op, count in coverage["operations"].items():
            if count > 0:
                ops_tested += 1
            print(f"        {op_names[int(op)]}: {count} tests")
        print(f"      Coverage: {ops_tested}/8 operations ({ops_tested / 8 * 100:.1f}%)")
        print()

        print("      Flag Coverage:")
        print(f"        Zero flag set: {coverage['zero_flag']['set']}")
        print(f"        Zero flag clear: {coverage['zero_flag']['clear']}")
        print(f"        Overflow set: {coverage['overflow']['set']}")
        print(f"        Overflow clear: {coverage['overflow']['clear']}")
        print()

        print("      Edge Cases:")
        for case, count in coverage["edge_cases"].items():
            status = "✓" if count > 0 else "✗"
            print(f"        {status} {case}: {count}")
    else:
        print("      WARNING: Coverage file not generated")

    print()
    print("=" * 60)
    print("Cocotb concept validation complete!")
    print()
    print("Key observations:")
    print("  - Cocotb enables Python-based verification")
    print("  - Testbenches are coroutines with async/await")
    print("  - Functional coverage can be collected in Python")
    print("  - Easy integration with LLM-generated tests")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
