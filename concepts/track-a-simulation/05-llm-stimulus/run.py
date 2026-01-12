#!/usr/bin/env python3
"""
LLM Stimulus Generation Concept Script

Task ID: silicon-arena-6g7.8
Spec Reference: File 2 (RL Verification Gym Architecture.md) - "Stimulus Agent task"

This script demonstrates:
1. Reading coverage holes from previous analysis
2. Generating prompts for Claude
3. Generating Cocotb test cases
4. Validating and running generated tests
"""

import json
import os
import subprocess
import sys
from pathlib import Path

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent / "04-coverage-parsing"))
sys.path.insert(0, str(Path(__file__).parent))

from coverage_parser import CoverageParser
from stimulus_generator import (
    CoverageHole,
    GeneratedTest,
    StimulusGenerator,
    create_coverage_prompt,
    get_rtl_context,
    parse_generated_test,
    validate_test_syntax,
)


def load_coverage_holes(coverage_file: Path) -> list[CoverageHole]:
    """Load coverage holes from coverage.dat."""
    if not coverage_file.exists():
        return []

    parser = CoverageParser(coverage_file)
    report = parser.parse()

    holes = []
    for file_path, line, cov_type in report.get_coverage_holes():
        holes.append(CoverageHole(file_path=file_path, line_number=line, coverage_type=cov_type))

    return holes


def demo_prompt_generation(holes: list[CoverageHole]):
    """Demonstrate prompt generation without API call."""
    print("[Demo] Generated prompt for Claude:")
    print("-" * 60)

    prompt = create_coverage_prompt(holes[:5])
    # Show first 1500 chars
    print(prompt[:1500])
    if len(prompt) > 1500:
        print("... (truncated)")
    print("-" * 60)


def generate_with_api(generator: StimulusGenerator, holes: list[CoverageHole]) -> GeneratedTest | None:
    """Generate test using Claude API."""
    print("[API] Generating test with Claude...")

    # Get RTL context for better generation
    rtl_files = {h.file_path for h in holes if h.file_path != "unknown"}
    rtl_context = ""
    for rtl_file in rtl_files:
        # Try to find the file
        possible_paths = [
            Path(__file__).parent.parent.parent / "rtl" / "alu_8bit" / "alu.v",
            Path(rtl_file),
        ]
        for path in possible_paths:
            if path.exists():
                lines = [h.line_number for h in holes if h.file_path == rtl_file]
                rtl_context = get_rtl_context(str(path), lines)
                break

    try:
        test = generator.generate_from_holes(holes[:5], rtl_context)
        if test:
            print(f"[API] Generated test: {test.test_name}")
            return test
        else:
            print("[API] Failed to parse generated test")
            return None
    except Exception as e:
        print(f"[API] Error: {e}")
        return None


def validate_and_save_test(test: GeneratedTest, output_dir: Path) -> bool:
    """Validate generated test and save to file."""
    # Validate syntax
    valid, msg = validate_test_syntax(test.test_code)
    if not valid:
        print(f"[Validation] {msg}")
        return False

    print(f"[Validation] Syntax OK for {test.test_name}")

    # Add required imports
    full_code = f'''#!/usr/bin/env python3
"""
Auto-generated test targeting coverage holes.
{test.explanation}
"""

import cocotb
from cocotb.triggers import Timer

{test.test_code}
'''

    # Save to file
    output_file = output_dir / f"test_{test.test_name}.py"
    output_file.write_text(full_code)
    print(f"[Save] Written to {output_file}")

    return True


def run_generated_test(test_file: Path, cocotb_dir: Path) -> tuple[bool, str]:
    """Run the generated test using cocotb."""
    # Copy test to cocotb directory
    target = cocotb_dir / test_file.name
    target.write_text(test_file.read_text())

    # Run with cocotb
    env = os.environ.copy()
    env["MODULE"] = test_file.stem

    result = subprocess.run(
        ["make", f"MODULE={test_file.stem}"],
        cwd=cocotb_dir,
        capture_output=True,
        text=True,
        env=env,
    )

    success = result.returncode == 0
    output = result.stdout + result.stderr

    # Clean up
    if target.exists():
        target.unlink()

    return success, output


def main():
    script_dir = Path(__file__).parent.resolve()
    coverage_dir = script_dir.parent / "02-verilator-coverage"
    cocotb_dir = script_dir.parent / "03-cocotb-basic"

    print("=" * 60)
    print("LLM Stimulus Generation Concept Script")
    print("=" * 60)
    print()

    # Step 1: Load coverage holes
    print("[1/5] Loading coverage holes...")
    coverage_file = coverage_dir / "coverage.dat"

    if coverage_file.exists():
        holes = load_coverage_holes(coverage_file)
        print(f"      Found {len(holes)} coverage holes")
        if holes:
            print("      First 5 holes:")
            for hole in holes[:5]:
                print(f"        {hole.file_path}:{hole.line_number} [{hole.coverage_type}]")
    else:
        print("      WARNING: coverage.dat not found")
        print("      Using example coverage holes...")
        holes = [
            CoverageHole("alu.v", 69, "line", context="OR operation"),
            CoverageHole("alu.v", 70, "line", context="XOR operation"),
            CoverageHole("alu.v", 71, "line", context="NOT operation"),
            CoverageHole("alu.v", 17, "toggle", "a[7]:0->1"),
            CoverageHole("alu.v", 18, "toggle", "b[7]:0->1"),
        ]
    print()

    # Step 2: Demo prompt generation
    print("[2/5] Demonstrating prompt generation...")
    demo_prompt_generation(holes)
    print()

    # Step 3: Check for API key
    print("[3/5] Checking Claude API access...")
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if api_key:
        print("      API key found, will generate real test")
        use_api = True
    else:
        print("      No ANTHROPIC_API_KEY found, using mock generation")
        use_api = False
    print()

    # Step 4: Generate test
    print("[4/5] Generating test...")

    if use_api:
        generator = StimulusGenerator(api_key)
        test = generate_with_api(generator, holes)
    else:
        # Mock generation for demo
        print("[Mock] Creating example generated test...")
        test = GeneratedTest(
            test_name="test_or_xor_coverage",
            test_code='''@cocotb.test()
async def test_or_xor_coverage(dut):
    """Test OR and XOR operations to increase coverage.

    Targets coverage holes in lines 69-71 (OR, XOR operations).
    """
    dut._log.info("Testing OR and XOR operations for coverage")

    # Test OR operation (op=3)
    test_cases_or = [
        (0x00, 0x00, 0x00),  # 0 | 0 = 0
        (0xFF, 0x00, 0xFF),  # all ones | zero
        (0xAA, 0x55, 0xFF),  # alternating bits
        (0x80, 0x01, 0x81),  # MSB and LSB
    ]

    for a, b, expected in test_cases_or:
        dut.a.value = a
        dut.b.value = b
        dut.op.value = 3  # OR
        await Timer(1, units="ns")
        result = int(dut.result.value)
        assert result == expected, f"OR: {a:#x} | {b:#x} = {result:#x}, expected {expected:#x}"
        dut._log.info(f"OR: {a:#04x} | {b:#04x} = {result:#04x}")

    # Test XOR operation (op=4)
    test_cases_xor = [
        (0xFF, 0xFF, 0x00),  # same values = 0
        (0xAA, 0x55, 0xFF),  # alternating = all ones
        (0x00, 0xFF, 0xFF),  # 0 ^ all = all
        (0x80, 0x80, 0x00),  # MSB toggle
    ]

    for a, b, expected in test_cases_xor:
        dut.a.value = a
        dut.b.value = b
        dut.op.value = 4  # XOR
        await Timer(1, units="ns")
        result = int(dut.result.value)
        assert result == expected, f"XOR: {a:#x} ^ {b:#x} = {result:#x}, expected {expected:#x}"
        dut._log.info(f"XOR: {a:#04x} ^ {b:#04x} = {result:#04x}")

    dut._log.info("OR and XOR coverage tests passed!")
''',
            target_holes=holes[:5],
            explanation="Targets OR and XOR operation coverage holes",
        )

    if test:
        print(f"      Generated test: {test.test_name}")
        print()
        print("      Generated code:")
        print("-" * 60)
        for line in test.test_code.split("\n")[:30]:
            print(f"      {line}")
        if len(test.test_code.split("\n")) > 30:
            print("      ... (truncated)")
        print("-" * 60)
    else:
        print("      ERROR: Failed to generate test")
        return 1
    print()

    # Step 5: Validate and optionally run
    print("[5/5] Validating generated test...")

    output_dir = script_dir / "generated"
    output_dir.mkdir(exist_ok=True)

    if validate_and_save_test(test, output_dir):
        print()
        print("      Would you like to run the generated test?")
        print("      (Set RUN_GENERATED=1 to auto-run)")

        if os.environ.get("RUN_GENERATED") == "1" and cocotb_dir.exists():
            test_file = output_dir / f"test_{test.test_name}.py"
            print()
            print("      Running generated test...")
            success, output = run_generated_test(test_file, cocotb_dir)

            if success:
                print("      Test PASSED!")
            else:
                print("      Test FAILED")
                print(output[:500])

    print()
    print("=" * 60)
    print("LLM stimulus generation concept validation complete!")
    print()
    print("Key observations:")
    print("  - Coverage holes drive prompt generation")
    print("  - Claude generates valid Cocotb test code")
    print("  - Syntax validation catches errors before running")
    print("  - Generated tests can be integrated into test suite")
    print()
    print("Integration with RL training:")
    print("  1. Parse coverage holes from coverage.dat")
    print("  2. Generate prompt targeting specific holes")
    print("  3. LLM generates test code")
    print("  4. Run test and measure coverage delta")
    print("  5. Compute reward: R = Δcov × (1 + bonus)")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
