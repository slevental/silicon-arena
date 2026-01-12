"""
Python Bus Functional Model (BFM) for 8-bit ALU.

Task ID: silicon-arena-6g7.1
Spec Reference: File 4 - Pre-RTL Verification Strategy

This model serves as:
1. Golden reference for RTL verification
2. Target for CrossHair symbolic execution
3. Target for icontract Design-by-Contract
"""

from dataclasses import dataclass
from enum import IntEnum
from typing import Tuple


class AluOp(IntEnum):
    """ALU operation codes matching RTL."""
    ADD = 0b000
    SUB = 0b001
    AND = 0b010
    OR  = 0b011
    XOR = 0b100
    NOT = 0b101
    SHL = 0b110
    SHR = 0b111


@dataclass
class AluResult:
    """ALU computation result with all flags."""
    result: int
    zero: bool
    overflow: bool
    carry: bool


def mask(value: int, width: int = 8) -> int:
    """Mask value to specified bit width."""
    return value & ((1 << width) - 1)


def msb(value: int, width: int = 8) -> int:
    """Extract most significant bit."""
    return (value >> (width - 1)) & 1


def alu_compute(a: int, b: int, op: AluOp, width: int = 8) -> AluResult:
    """
    Compute ALU operation matching RTL behavior.

    Args:
        a: First operand (unsigned, width bits)
        b: Second operand (unsigned, width bits)
        op: Operation to perform
        width: Bit width (default 8)

    Returns:
        AluResult with result and flags
    """
    max_val = (1 << width) - 1
    a = mask(a, width)
    b = mask(b, width)

    overflow = False
    carry = False

    if op == AluOp.ADD:
        full_result = a + b
        result = mask(full_result, width)
        carry = full_result > max_val
        # Signed overflow: both operands same sign, result different sign
        overflow = (msb(a, width) == msb(b, width)) and (msb(result, width) != msb(a, width))

    elif op == AluOp.SUB:
        full_result = a - b
        result = mask(full_result, width)
        carry = full_result < 0
        # Signed overflow: operands different signs, result sign differs from a
        overflow = (msb(a, width) != msb(b, width)) and (msb(result, width) != msb(a, width))

    elif op == AluOp.AND:
        result = a & b

    elif op == AluOp.OR:
        result = a | b

    elif op == AluOp.XOR:
        result = a ^ b

    elif op == AluOp.NOT:
        result = mask(~a, width)

    elif op == AluOp.SHL:
        shift_amt = b & 0x7  # Only use lower 3 bits
        result = mask(a << shift_amt, width)

    elif op == AluOp.SHR:
        shift_amt = b & 0x7  # Only use lower 3 bits
        result = a >> shift_amt

    else:
        result = 0

    zero = result == 0

    return AluResult(result=result, zero=zero, overflow=overflow, carry=carry)


def generate_test_vectors(width: int = 8) -> list[Tuple[int, int, AluOp, AluResult]]:
    """
    Generate basic test vectors for ALU verification.

    Returns:
        List of (a, b, op, expected_result) tuples
    """
    vectors = []
    max_val = (1 << width) - 1

    # Test each operation with simple values
    test_cases = [
        # ADD tests
        (0, 0, AluOp.ADD),
        (1, 1, AluOp.ADD),
        (max_val, 1, AluOp.ADD),  # Overflow
        (0x7F, 1, AluOp.ADD),     # Signed overflow (127 + 1)

        # SUB tests
        (5, 3, AluOp.SUB),
        (0, 1, AluOp.SUB),        # Underflow
        (0x80, 1, AluOp.SUB),     # Signed overflow (-128 - 1)

        # Logic tests
        (0xAA, 0x55, AluOp.AND),
        (0xAA, 0x55, AluOp.OR),
        (0xFF, 0x0F, AluOp.XOR),
        (0xAA, 0x00, AluOp.NOT),

        # Shift tests
        (0x01, 4, AluOp.SHL),
        (0x80, 4, AluOp.SHR),
    ]

    for a, b, op in test_cases:
        result = alu_compute(a, b, op, width)
        vectors.append((a, b, op, result))

    return vectors


if __name__ == "__main__":
    # Print test vectors for verification
    print("ALU Test Vectors (8-bit)")
    print("=" * 60)

    for a, b, op, result in generate_test_vectors():
        print(f"a=0x{a:02X}, b=0x{b:02X}, op={op.name:3s} -> "
              f"result=0x{result.result:02X}, "
              f"Z={int(result.zero)}, O={int(result.overflow)}, C={int(result.carry)}")
