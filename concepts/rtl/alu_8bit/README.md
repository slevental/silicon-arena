# 8-bit ALU Test Design

**Task ID**: silicon-arena-6g7.1
**Spec Reference**: File 2 (RL Verification Gym Architecture.md) - 'ALU.v module'

## Interface

| Port | Direction | Width | Description |
|------|-----------|-------|-------------|
| `a` | input | WIDTH | First operand |
| `b` | input | WIDTH | Second operand |
| `op` | input | 3 | Operation select |
| `result` | output | WIDTH | Operation result |
| `zero` | output | 1 | Zero flag (result == 0) |
| `overflow` | output | 1 | Signed overflow (ADD/SUB only) |
| `carry` | output | 1 | Carry/borrow out |

## Operations

| Op Code | Operation | Description |
|---------|-----------|-------------|
| `000` | ADD | `result = a + b` |
| `001` | SUB | `result = a - b` |
| `010` | AND | `result = a & b` |
| `011` | OR | `result = a \| b` |
| `100` | XOR | `result = a ^ b` |
| `101` | NOT | `result = ~a` |
| `110` | SHL | `result = a << b[2:0]` |
| `111` | SHR | `result = a >> b[2:0]` |

## Parameters

- `WIDTH`: Bit width of operands and result (default: 8)

## Flags

- **Zero**: Asserted when result equals zero
- **Overflow**: Signed overflow detection for ADD/SUB operations
  - ADD: `(a[MSB] == b[MSB]) && (result[MSB] != a[MSB])`
  - SUB: `(a[MSB] != b[MSB]) && (result[MSB] != a[MSB])`
- **Carry**: Unsigned carry/borrow from MSB position

## Example Usage

```verilog
alu #(.WIDTH(8)) dut (
    .a(operand_a),
    .b(operand_b),
    .op(operation),
    .result(alu_result),
    .zero(zero_flag),
    .overflow(overflow_flag),
    .carry(carry_flag)
);
```

## Verification Points

Coverage targets for concept scripts:
1. All 8 operations exercised
2. Zero flag transitions (0→1, 1→0)
3. Overflow conditions for ADD/SUB
4. Carry conditions for ADD/SUB
5. Shift amount coverage (0-7 for 8-bit)
6. Edge cases: max values, min values, all zeros, all ones
