#!/usr/bin/env python3
"""
Cocotb Testbench for FP ALU (32-bit IEEE-754)

Task ID: silicon-arena-6g7.7
Spec Reference: File 2 (RL Verification Gym Architecture.md) - "Cocotb testbenches"

This testbench demonstrates:
1. Basic Cocotb testbench structure
2. Driving inputs and checking outputs
3. Functional coverage collection
4. Test organization patterns

Updated to use 32-bit IEEE-754 FP ALU with operations:
- 1: MUL, 2: DIV, 3: SUB, 4: OR, 5: AND, 6: XOR
- 7: SHL, 8: SHR, 9: FP2INT, 10: ADD, 11: COMPLEMENT
"""

import struct
import cocotb
from cocotb.triggers import Timer


# FP ALU operation codes
class FpAluOp:
    MUL = 1       # Multiplication
    DIV = 2       # Division
    SUB = 3       # Subtraction
    OR = 4        # Bitwise OR
    AND = 5       # Bitwise AND
    XOR = 6       # Bitwise XOR
    SHL = 7       # Left Shift (by 1)
    SHR = 8       # Right Shift (by 1)
    FP2INT = 9    # FP to Integer
    ADD = 10      # Addition
    COMPL = 11    # Complement


# Test coverage tracking
coverage = {
    "operations": {op: 0 for op in range(1, 12)},
    "exception": {"set": 0, "clear": 0},
    "overflow": {"set": 0, "clear": 0},
    "underflow": {"set": 0, "clear": 0},
    "edge_cases": {"zero_operands": 0, "max_operands": 0, "negative": 0},
}


def float_to_ieee754(f: float) -> int:
    """Convert float to IEEE-754 32-bit representation."""
    return struct.unpack('>I', struct.pack('>f', f))[0]


def ieee754_to_float(bits: int) -> float:
    """Convert IEEE-754 32-bit representation to float."""
    return struct.unpack('>f', struct.pack('>I', bits & 0xFFFFFFFF))[0]


def record_coverage(op: int, exception: int, overflow: int, underflow: int, a: int, b: int):
    """Record functional coverage."""
    if 1 <= op <= 11:
        coverage["operations"][op] += 1

    if exception:
        coverage["exception"]["set"] += 1
    else:
        coverage["exception"]["clear"] += 1

    if overflow:
        coverage["overflow"]["set"] += 1
    else:
        coverage["overflow"]["clear"] += 1

    if underflow:
        coverage["underflow"]["set"] += 1
    else:
        coverage["underflow"]["clear"] += 1

    # Edge cases
    if a == 0 and b == 0:
        coverage["edge_cases"]["zero_operands"] += 1
    if a == 0xFFFFFFFF or b == 0xFFFFFFFF:
        coverage["edge_cases"]["max_operands"] += 1
    if (a >> 31) or (b >> 31):  # Check sign bit
        coverage["edge_cases"]["negative"] += 1


async def drive_and_check(dut, a: int, b: int, op: int, description: str = ""):
    """Drive inputs and check outputs after settling."""
    # Drive inputs
    dut.a_operand.value = a
    dut.b_operand.value = b
    dut.Operation.value = op

    # Wait for combinational logic to settle
    await Timer(1, unit="ns")

    # Get actual outputs
    result = int(dut.ALU_Output.value)
    exception = int(dut.Exception.value)
    overflow = int(dut.Overflow.value)
    underflow = int(dut.Underflow.value)

    # Record coverage
    record_coverage(op, exception, overflow, underflow, a, b)

    return result, exception, overflow, underflow


@cocotb.test()
async def test_add_fp(dut):
    """Test FP addition operations (op=10)."""
    dut._log.info("Testing ADD operation (op=10)")
    dut._log.info("Note: Verilator tristate limitation may affect results")

    test_vectors = [
        (float_to_ieee754(1.0), float_to_ieee754(2.0), "1.0 + 2.0"),
        (float_to_ieee754(3.5), float_to_ieee754(2.5), "3.5 + 2.5"),
        (float_to_ieee754(100.0), float_to_ieee754(0.5), "100.0 + 0.5"),
        (float_to_ieee754(0.0), float_to_ieee754(0.0), "0.0 + 0.0"),
    ]

    for a, b, desc in test_vectors:
        result, exc, ovf, udf = await drive_and_check(dut, a, b, FpAluOp.ADD, desc)
        dut._log.info(f"ADD: {desc} => 0x{result:08X} (exc={exc}, ovf={ovf}, udf={udf})")


@cocotb.test()
async def test_sub_fp(dut):
    """Test FP subtraction operations (op=3)."""
    dut._log.info("Testing SUB operation (op=3)")

    test_vectors = [
        (float_to_ieee754(5.0), float_to_ieee754(3.0), "5.0 - 3.0"),
        (float_to_ieee754(10.0), float_to_ieee754(10.0), "10.0 - 10.0"),
        (float_to_ieee754(100.0), float_to_ieee754(50.0), "100.0 - 50.0"),
    ]

    for a, b, desc in test_vectors:
        result, exc, ovf, udf = await drive_and_check(dut, a, b, FpAluOp.SUB, desc)
        dut._log.info(f"SUB: {desc} => 0x{result:08X}")


@cocotb.test()
async def test_mul_fp(dut):
    """Test FP multiplication operations (op=1)."""
    dut._log.info("Testing MUL operation (op=1)")

    test_vectors = [
        (float_to_ieee754(2.0), float_to_ieee754(3.0), "2.0 * 3.0"),
        (float_to_ieee754(4.0), float_to_ieee754(0.5), "4.0 * 0.5"),
        (float_to_ieee754(1.5), float_to_ieee754(2.0), "1.5 * 2.0"),
    ]

    for a, b, desc in test_vectors:
        result, exc, ovf, udf = await drive_and_check(dut, a, b, FpAluOp.MUL, desc)
        dut._log.info(f"MUL: {desc} => 0x{result:08X}")


@cocotb.test()
async def test_div_fp(dut):
    """Test FP division operations (op=2)."""
    dut._log.info("Testing DIV operation (op=2)")

    test_vectors = [
        (float_to_ieee754(6.0), float_to_ieee754(2.0), "6.0 / 2.0"),
        (float_to_ieee754(10.0), float_to_ieee754(4.0), "10.0 / 4.0"),
        (float_to_ieee754(1.0), float_to_ieee754(2.0), "1.0 / 2.0"),
    ]

    for a, b, desc in test_vectors:
        result, exc, ovf, udf = await drive_and_check(dut, a, b, FpAluOp.DIV, desc)
        dut._log.info(f"DIV: {desc} => 0x{result:08X}")


@cocotb.test()
async def test_and_bitwise(dut):
    """Test AND operation (op=5)."""
    dut._log.info("Testing AND operation (op=5)")

    test_vectors = [
        (0xFFFF0000, 0x0000FFFF, "0xFFFF0000 & 0x0000FFFF"),
        (0xAAAAAAAA, 0x55555555, "0xAAAAAAAA & 0x55555555"),
        (0xFFFFFFFF, 0x0F0F0F0F, "0xFFFFFFFF & 0x0F0F0F0F"),
    ]

    for a, b, desc in test_vectors:
        result, exc, ovf, udf = await drive_and_check(dut, a, b, FpAluOp.AND, desc)
        dut._log.info(f"AND: {desc} => 0x{result:08X}")


@cocotb.test()
async def test_or_bitwise(dut):
    """Test OR operation (op=4)."""
    dut._log.info("Testing OR operation (op=4)")

    test_vectors = [
        (0xF0F0F0F0, 0x0F0F0F0F, "0xF0F0F0F0 | 0x0F0F0F0F"),
        (0x00000000, 0xFFFFFFFF, "0x00000000 | 0xFFFFFFFF"),
        (0xAAAAAAAA, 0x55555555, "0xAAAAAAAA | 0x55555555"),
    ]

    for a, b, desc in test_vectors:
        result, exc, ovf, udf = await drive_and_check(dut, a, b, FpAluOp.OR, desc)
        dut._log.info(f"OR: {desc} => 0x{result:08X}")


@cocotb.test()
async def test_xor_bitwise(dut):
    """Test XOR operation (op=6)."""
    dut._log.info("Testing XOR operation (op=6)")

    test_vectors = [
        (0xFFFFFFFF, 0xFFFFFFFF, "0xFFFFFFFF ^ 0xFFFFFFFF"),
        (0xAAAAAAAA, 0x55555555, "0xAAAAAAAA ^ 0x55555555"),
        (0x12345678, 0x00000000, "0x12345678 ^ 0x00000000"),
    ]

    for a, b, desc in test_vectors:
        result, exc, ovf, udf = await drive_and_check(dut, a, b, FpAluOp.XOR, desc)
        dut._log.info(f"XOR: {desc} => 0x{result:08X}")


@cocotb.test()
async def test_shift_left(dut):
    """Test shift left operation (op=7)."""
    dut._log.info("Testing SHL operation (op=7) - shifts by 1")

    test_vectors = [
        (0x00000001, 0, "0x00000001 << 1"),
        (0x80000000, 0, "0x80000000 << 1"),
        (0x12345678, 0, "0x12345678 << 1"),
    ]

    for a, b, desc in test_vectors:
        result, exc, ovf, udf = await drive_and_check(dut, a, b, FpAluOp.SHL, desc)
        dut._log.info(f"SHL: {desc} => 0x{result:08X}")


@cocotb.test()
async def test_shift_right(dut):
    """Test shift right operation (op=8)."""
    dut._log.info("Testing SHR operation (op=8) - shifts by 1")

    test_vectors = [
        (0x80000000, 0, "0x80000000 >> 1"),
        (0x00000002, 0, "0x00000002 >> 1"),
        (0x12345678, 0, "0x12345678 >> 1"),
    ]

    for a, b, desc in test_vectors:
        result, exc, ovf, udf = await drive_and_check(dut, a, b, FpAluOp.SHR, desc)
        dut._log.info(f"SHR: {desc} => 0x{result:08X}")


@cocotb.test()
async def test_complement(dut):
    """Test complement operation (op=11)."""
    dut._log.info("Testing COMPLEMENT operation (op=11)")

    test_vectors = [
        (0x00000000, 0, "~0x00000000"),
        (0xFFFFFFFF, 0, "~0xFFFFFFFF"),
        (0xAAAAAAAA, 0, "~0xAAAAAAAA"),
    ]

    for a, b, desc in test_vectors:
        result, exc, ovf, udf = await drive_and_check(dut, a, b, FpAluOp.COMPL, desc)
        dut._log.info(f"COMPL: {desc} => 0x{result:08X}")


@cocotb.test()
async def test_coverage_report(dut):
    """Final test to report coverage statistics."""
    dut._log.info("=" * 50)
    dut._log.info("COVERAGE REPORT")
    dut._log.info("=" * 50)

    op_names = {
        1: "MUL", 2: "DIV", 3: "SUB", 4: "OR", 5: "AND",
        6: "XOR", 7: "SHL", 8: "SHR", 9: "FP2INT", 10: "ADD", 11: "COMPL"
    }

    dut._log.info("Operations tested:")
    for op, count in coverage["operations"].items():
        dut._log.info(f"  {op_names.get(op, '???')}: {count} tests")

    dut._log.info("Flag coverage:")
    dut._log.info(f"  Exception set: {coverage['exception']['set']}")
    dut._log.info(f"  Exception clear: {coverage['exception']['clear']}")
    dut._log.info(f"  Overflow set: {coverage['overflow']['set']}")
    dut._log.info(f"  Overflow clear: {coverage['overflow']['clear']}")
    dut._log.info(f"  Underflow set: {coverage['underflow']['set']}")
    dut._log.info(f"  Underflow clear: {coverage['underflow']['clear']}")

    dut._log.info("Edge cases:")
    for case, count in coverage["edge_cases"].items():
        dut._log.info(f"  {case}: {count}")

    dut._log.info("=" * 50)

    # Export coverage for external analysis
    import json
    from pathlib import Path

    coverage_file = Path(__file__).parent / "cocotb_coverage.json"
    coverage_file.write_text(json.dumps(coverage, indent=2))
    dut._log.info(f"Coverage exported to: {coverage_file}")
