#!/usr/bin/env python3
"""
Cocotb Testbench for ALU

Task ID: silicon-arena-6g7.7
Spec Reference: File 2 (RL Verification Gym Architecture.md) - "Cocotb testbenches"

This testbench demonstrates:
1. Basic Cocotb testbench structure
2. Driving inputs and checking outputs
3. Functional coverage collection
4. Test organization patterns
"""

import cocotb
from cocotb.triggers import Timer
from cocotb.result import TestSuccess


# ALU operation codes
class AluOp:
    ADD = 0b000
    SUB = 0b001
    AND = 0b010
    OR = 0b011
    XOR = 0b100
    NOT = 0b101
    SHL = 0b110
    SHR = 0b111


# Test coverage tracking
coverage = {
    "operations": {op: 0 for op in range(8)},
    "zero_flag": {"set": 0, "clear": 0},
    "overflow": {"set": 0, "clear": 0},
    "edge_cases": {"all_zeros": 0, "all_ones": 0, "alternating": 0},
}


def record_coverage(op: int, result: int, zero: int, overflow: int, a: int, b: int):
    """Record functional coverage."""
    coverage["operations"][op] += 1

    if zero:
        coverage["zero_flag"]["set"] += 1
    else:
        coverage["zero_flag"]["clear"] += 1

    if overflow:
        coverage["overflow"]["set"] += 1
    else:
        coverage["overflow"]["clear"] += 1

    # Edge cases
    if a == 0 and b == 0:
        coverage["edge_cases"]["all_zeros"] += 1
    if a == 0xFF and b == 0xFF:
        coverage["edge_cases"]["all_ones"] += 1
    if a == 0xAA or b == 0x55:
        coverage["edge_cases"]["alternating"] += 1


def compute_expected(a: int, b: int, op: int, width: int = 8) -> tuple[int, int, int]:
    """Compute expected ALU result (golden model)."""
    mask = (1 << width) - 1

    if op == AluOp.ADD:
        full_result = a + b
        result = full_result & mask
        overflow = 1 if full_result > mask else 0
    elif op == AluOp.SUB:
        full_result = a - b
        result = full_result & mask
        overflow = 1 if full_result < 0 else 0
    elif op == AluOp.AND:
        result = (a & b) & mask
        overflow = 0
    elif op == AluOp.OR:
        result = (a | b) & mask
        overflow = 0
    elif op == AluOp.XOR:
        result = (a ^ b) & mask
        overflow = 0
    elif op == AluOp.NOT:
        result = (~a) & mask
        overflow = 0
    elif op == AluOp.SHL:
        result = (a << (b & 0x7)) & mask
        overflow = 0
    elif op == AluOp.SHR:
        result = (a >> (b & 0x7)) & mask
        overflow = 0
    else:
        result = 0
        overflow = 0

    zero = 1 if result == 0 else 0
    return result, zero, overflow


async def drive_and_check(dut, a: int, b: int, op: int, description: str = ""):
    """Drive inputs and check outputs after settling."""
    # Drive inputs
    dut.a.value = a
    dut.b.value = b
    dut.op.value = op

    # Wait for combinational logic to settle
    await Timer(1, units="ns")

    # Get actual outputs
    result = int(dut.result.value)
    zero = int(dut.zero.value)
    overflow = int(dut.overflow.value)

    # Compute expected
    exp_result, exp_zero, exp_overflow = compute_expected(a, b, op)

    # Record coverage
    record_coverage(op, result, zero, overflow, a, b)

    # Check results
    assert result == exp_result, f"{description}: result mismatch: got {result:#x}, expected {exp_result:#x}"
    assert zero == exp_zero, f"{description}: zero flag mismatch: got {zero}, expected {exp_zero}"

    return result, zero, overflow


@cocotb.test()
async def test_add_basic(dut):
    """Test basic addition operations."""
    dut._log.info("Testing ADD operation")

    test_vectors = [
        (0, 0, "0 + 0"),
        (1, 1, "1 + 1"),
        (10, 20, "10 + 20"),
        (100, 50, "100 + 50"),
        (255, 0, "255 + 0"),
        (128, 127, "128 + 127"),
    ]

    for a, b, desc in test_vectors:
        result, zero, overflow = await drive_and_check(dut, a, b, AluOp.ADD, desc)
        dut._log.info(f"ADD: {a} + {b} = {result} (zero={zero}, overflow={overflow})")


@cocotb.test()
async def test_sub_basic(dut):
    """Test basic subtraction operations."""
    dut._log.info("Testing SUB operation")

    test_vectors = [
        (10, 5, "10 - 5"),
        (100, 100, "100 - 100 = 0"),
        (50, 20, "50 - 20"),
        (255, 1, "255 - 1"),
        (0, 0, "0 - 0"),
    ]

    for a, b, desc in test_vectors:
        result, zero, overflow = await drive_and_check(dut, a, b, AluOp.SUB, desc)
        dut._log.info(f"SUB: {a} - {b} = {result} (zero={zero})")


@cocotb.test()
async def test_and_basic(dut):
    """Test AND operation."""
    dut._log.info("Testing AND operation")

    test_vectors = [
        (0xFF, 0x0F, "0xFF & 0x0F"),
        (0xAA, 0x55, "0xAA & 0x55"),
        (0xFF, 0xFF, "0xFF & 0xFF"),
        (0x00, 0xFF, "0x00 & 0xFF"),
    ]

    for a, b, desc in test_vectors:
        result, zero, _ = await drive_and_check(dut, a, b, AluOp.AND, desc)
        dut._log.info(f"AND: {a:#04x} & {b:#04x} = {result:#04x} (zero={zero})")


@cocotb.test()
async def test_or_basic(dut):
    """Test OR operation."""
    dut._log.info("Testing OR operation")

    test_vectors = [
        (0xF0, 0x0F, "0xF0 | 0x0F"),
        (0x00, 0x00, "0x00 | 0x00"),
        (0xAA, 0x55, "0xAA | 0x55"),
    ]

    for a, b, desc in test_vectors:
        result, zero, _ = await drive_and_check(dut, a, b, AluOp.OR, desc)
        dut._log.info(f"OR: {a:#04x} | {b:#04x} = {result:#04x} (zero={zero})")


@cocotb.test()
async def test_xor_basic(dut):
    """Test XOR operation."""
    dut._log.info("Testing XOR operation")

    test_vectors = [
        (0xFF, 0xFF, "0xFF ^ 0xFF = 0"),
        (0xAA, 0x55, "0xAA ^ 0x55"),
        (0x00, 0xFF, "0x00 ^ 0xFF"),
    ]

    for a, b, desc in test_vectors:
        result, zero, _ = await drive_and_check(dut, a, b, AluOp.XOR, desc)
        dut._log.info(f"XOR: {a:#04x} ^ {b:#04x} = {result:#04x} (zero={zero})")


@cocotb.test()
async def test_not_basic(dut):
    """Test NOT (complement) operation."""
    dut._log.info("Testing NOT operation")

    test_vectors = [
        (0x00, "~0x00"),
        (0xFF, "~0xFF"),
        (0xAA, "~0xAA"),
        (0x55, "~0x55"),
    ]

    for a, desc in test_vectors:
        result, zero, _ = await drive_and_check(dut, a, 0, AluOp.NOT, desc)
        dut._log.info(f"NOT: ~{a:#04x} = {result:#04x} (zero={zero})")


@cocotb.test()
async def test_shift_left(dut):
    """Test shift left operation."""
    dut._log.info("Testing SHL operation")

    test_vectors = [
        (0x01, 1, "1 << 1"),
        (0x01, 4, "1 << 4"),
        (0x0F, 4, "0x0F << 4"),
        (0x80, 1, "0x80 << 1 (overflow)"),
    ]

    for a, b, desc in test_vectors:
        result, zero, _ = await drive_and_check(dut, a, b, AluOp.SHL, desc)
        dut._log.info(f"SHL: {a:#04x} << {b} = {result:#04x}")


@cocotb.test()
async def test_shift_right(dut):
    """Test shift right operation."""
    dut._log.info("Testing SHR operation")

    test_vectors = [
        (0x80, 1, "0x80 >> 1"),
        (0xFF, 4, "0xFF >> 4"),
        (0x01, 1, "0x01 >> 1"),
    ]

    for a, b, desc in test_vectors:
        result, zero, _ = await drive_and_check(dut, a, b, AluOp.SHR, desc)
        dut._log.info(f"SHR: {a:#04x} >> {b} = {result:#04x}")


@cocotb.test()
async def test_coverage_report(dut):
    """Final test to report coverage statistics."""
    dut._log.info("=" * 50)
    dut._log.info("COVERAGE REPORT")
    dut._log.info("=" * 50)

    op_names = ["ADD", "SUB", "AND", "OR", "XOR", "NOT", "SHL", "SHR"]

    dut._log.info("Operations tested:")
    for op, count in coverage["operations"].items():
        dut._log.info(f"  {op_names[op]}: {count} tests")

    dut._log.info("")
    dut._log.info("Flag coverage:")
    dut._log.info(f"  Zero set: {coverage['zero_flag']['set']}")
    dut._log.info(f"  Zero clear: {coverage['zero_flag']['clear']}")
    dut._log.info(f"  Overflow set: {coverage['overflow']['set']}")
    dut._log.info(f"  Overflow clear: {coverage['overflow']['clear']}")

    dut._log.info("")
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
