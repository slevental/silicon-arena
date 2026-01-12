#!/usr/bin/env python3
"""
Verilator Compile Concept Script
Task ID: silicon-arena-6g7.4
Spec Reference: File 2 - "verilator --cc" and "RTLEnv wrapper"

This script demonstrates:
1. Compiling Verilog RTL with Verilator
2. Running C++ testbench simulation
3. Generating VCD waveforms
"""

import subprocess
import sys
from pathlib import Path


def run_command(cmd: list[str], cwd: Path | None = None) -> tuple[int, str, str]:
    """Run a command and return (returncode, stdout, stderr)."""
    result = subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True
    )
    return result.returncode, result.stdout, result.stderr


def main():
    script_dir = Path(__file__).parent.resolve()

    print("=" * 60)
    print("Verilator Compile Concept Script")
    print("=" * 60)
    print()

    # Step 1: Check Verilator is available
    print("[1/4] Checking Verilator installation...")
    rc, stdout, stderr = run_command(["verilator", "--version"])
    if rc != 0:
        print("ERROR: Verilator not found. Please install Verilator.")
        sys.exit(1)
    print(f"      {stdout.strip()}")
    print()

    # Step 2: Clean previous build
    print("[2/4] Cleaning previous build...")
    run_command(["make", "clean"], cwd=script_dir)
    print("      Done")
    print()

    # Step 3: Compile with Verilator
    print("[3/4] Compiling RTL with Verilator...")
    rc, stdout, stderr = run_command(["make", "all"], cwd=script_dir)
    if rc != 0:
        print("ERROR: Compilation failed")
        print(stderr)
        sys.exit(1)
    print("      Compilation successful")
    print()

    # Step 4: Run simulation
    print("[4/4] Running simulation...")
    print("-" * 60)
    rc, stdout, stderr = run_command(["make", "run"], cwd=script_dir)
    print(stdout)
    if stderr:
        print(stderr)

    # Check for VCD output
    vcd_file = script_dir / "alu_waveform.vcd"
    if vcd_file.exists():
        print(f"VCD waveform: {vcd_file}")
        print(f"VCD size: {vcd_file.stat().st_size} bytes")
    else:
        print("WARNING: VCD file not generated")

    print()
    print("=" * 60)
    print("Concept validation complete!")
    print("=" * 60)

    return rc


if __name__ == "__main__":
    sys.exit(main())
