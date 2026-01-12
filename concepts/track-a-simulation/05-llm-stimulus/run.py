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

Updated for 32-bit IEEE-754 FP ALU with operations:
- 1: MUL, 2: DIV, 3: SUB, 4: OR, 5: AND, 6: XOR
- 7: SHL, 8: SHR, 9: FP2INT, 10: ADD, 11: COMPLEMENT
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
            Path(__file__).parent.parent.parent / "rtl" / "fp_alu_32bit" / "rtl" / "ALU.v",
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
            CoverageHole("ALU.v", 50, "line", context="FP2INT operation"),
            CoverageHole("ALU.v", 60, "line", context="MUL operation"),
            CoverageHole("ALU.v", 70, "line", context="DIV operation"),
            CoverageHole("ALU.v", 17, "toggle", "a_operand[31]:0->1"),
            CoverageHole("ALU.v", 18, "toggle", "b_operand[31]:0->1"),
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
            test_name="test_fp2int_mul_coverage",
            test_code='''@cocotb.test()
async def test_fp2int_mul_coverage(dut):
    """Test FP2INT and MUL operations to increase coverage.

    Targets coverage holes for FP2INT (op=9) and MUL (op=1) operations.
    Uses 32-bit IEEE-754 FP ALU interface.
    """
    import struct

    def float_to_ieee754(f: float) -> int:
        return struct.unpack('>I', struct.pack('>f', f))[0]

    dut._log.info("Testing FP2INT and MUL operations for coverage")

    # Test MUL operation (op=1)
    test_cases_mul = [
        (1.0, 1.0),   # identity
        (2.0, 3.0),   # 2 * 3 = 6
        (0.5, 4.0),   # 0.5 * 4 = 2
        (-1.0, 2.0),  # negative operand
    ]

    for a, b in test_cases_mul:
        dut.a_operand.value = float_to_ieee754(a)
        dut.b_operand.value = float_to_ieee754(b)
        dut.Operation.value = 1  # MUL
        await Timer(1, unit="ns")
        result = int(dut.ALU_Output.value)
        dut._log.info(f"MUL: {a} * {b} => 0x{result:08X}")

    # Test FP2INT operation (op=9)
    test_cases_fp2int = [
        1.0,    # simple integer
        2.5,    # fractional
        -3.0,   # negative
        100.75, # larger value
    ]

    for a in test_cases_fp2int:
        dut.a_operand.value = float_to_ieee754(a)
        dut.b_operand.value = 0
        dut.Operation.value = 9  # FP2INT
        await Timer(1, unit="ns")
        result = int(dut.ALU_Output.value)
        dut._log.info(f"FP2INT: {a} => {result}")

    dut._log.info("FP2INT and MUL coverage tests passed!")
''',
            target_holes=holes[:5],
            explanation="Targets FP2INT and MUL operation coverage holes",
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
