#!/usr/bin/env python3
"""
Verilator Coverage Concept Script
Task ID: silicon-arena-6g7.5
Spec Reference: File 2 - "Coverage tracking via Verilator --coverage"

This script demonstrates:
1. Compiling Verilog with coverage instrumentation
2. Running simulation to generate coverage.dat
3. Using verilator_coverage to analyze results
4. Parsing coverage data for reward computation
"""

import subprocess
import sys
from pathlib import Path
import re


def run_command(cmd: list[str], cwd: Path | None = None) -> tuple[int, str, str]:
    """Run a command and return (returncode, stdout, stderr)."""
    result = subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True
    )
    return result.returncode, result.stdout, result.stderr


def parse_coverage_dat(coverage_file: Path) -> dict:
    """
    Parse Verilator coverage.dat file.

    Returns dict with coverage metrics.
    """
    if not coverage_file.exists():
        return {"error": "coverage.dat not found"}

    content = coverage_file.read_text()

    # Count coverage points
    # Format: 'C' <hier> <lineno> <column> <cmt> <count>
    line_points = 0
    line_hits = 0
    toggle_points = 0
    toggle_hits = 0

    for line in content.split('\n'):
        if line.startswith('C '):
            parts = line.split("'")
            if len(parts) >= 2:
                # Extract count (last numeric value)
                count_match = re.search(r"'(\d+)$", line)
                if count_match:
                    count = int(count_match.group(1))

                    if 'line' in line.lower() or 'vlCoverage' in line:
                        line_points += 1
                        if count > 0:
                            line_hits += 1
                    elif 'toggle' in line.lower():
                        toggle_points += 1
                        if count > 0:
                            toggle_hits += 1

    return {
        "line_points": line_points,
        "line_hits": line_hits,
        "line_coverage": (line_hits / line_points * 100) if line_points > 0 else 0,
        "toggle_points": toggle_points,
        "toggle_hits": toggle_hits,
        "toggle_coverage": (toggle_hits / toggle_points * 100) if toggle_points > 0 else 0,
    }


def main():
    script_dir = Path(__file__).parent.resolve()

    print("=" * 60)
    print("Verilator Coverage Concept Script")
    print("=" * 60)
    print()

    # Step 1: Check Verilator is available
    print("[1/5] Checking Verilator installation...")
    rc, stdout, stderr = run_command(["verilator", "--version"])
    if rc != 0:
        print("ERROR: Verilator not found.")
        sys.exit(1)
    print(f"      {stdout.strip()}")
    print()

    # Step 2: Clean previous build
    print("[2/5] Cleaning previous build...")
    run_command(["make", "clean"], cwd=script_dir)
    print("      Done")
    print()

    # Step 3: Compile with coverage
    print("[3/5] Compiling RTL with coverage instrumentation...")
    rc, stdout, stderr = run_command(["make", "all"], cwd=script_dir)
    if rc != 0:
        print("ERROR: Compilation failed")
        print(stderr)
        sys.exit(1)
    print("      Compilation successful (--coverage enabled)")
    print()

    # Step 4: Run simulation
    print("[4/5] Running simulation to generate coverage data...")
    print("-" * 60)
    rc, stdout, stderr = run_command(["make", "run"], cwd=script_dir)
    print(stdout)
    if stderr:
        print(stderr)

    # Step 5: Analyze coverage
    print("[5/5] Analyzing coverage data...")
    print("-" * 60)

    coverage_file = script_dir / "coverage.dat"
    if coverage_file.exists():
        print(f"Coverage file: {coverage_file}")
        print(f"Coverage file size: {coverage_file.stat().st_size} bytes")
        print()

        # Generate annotated sources
        print("Generating annotated sources...")
        rc, stdout, stderr = run_command(["make", "annotate"], cwd=script_dir)

        # Show annotated ALU
        annotated_alu = script_dir / "annotated" / "alu.v"
        if annotated_alu.exists():
            print()
            print("=== Annotated alu.v (showing coverage) ===")
            print(annotated_alu.read_text()[:2000])
            if annotated_alu.stat().st_size > 2000:
                print("... (truncated)")

        # Parse and show summary
        print()
        print("=== Coverage Summary ===")
        metrics = parse_coverage_dat(coverage_file)
        if "error" not in metrics:
            print(f"Line coverage points: {metrics['line_points']}")
            print(f"Line coverage hits: {metrics['line_hits']}")
            print(f"Toggle coverage points: {metrics['toggle_points']}")
            print(f"Toggle coverage hits: {metrics['toggle_hits']}")
        else:
            print(f"Error: {metrics['error']}")
    else:
        print("WARNING: coverage.dat not generated")

    print()
    print("=" * 60)
    print("Coverage concept validation complete!")
    print()
    print("Key observations:")
    print("  - Only ADD, SUB, AND operations were tested")
    print("  - OR, XOR, NOT, SHL, SHR have coverage gaps")
    print("  - This demonstrates how to identify untested code paths")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
