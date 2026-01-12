# IEEE-754 32-bit Floating-Point ALU

**Source**: [UVM_Machine Project](https://anonymous.4open.science/r/UVM_Machine-7806)
**Task ID**: silicon-arena-6g7.1

## Overview

A complex 32-bit IEEE-754 floating-point ALU with multiple operations and complete UVM testbench.
This serves as a realistic verification target for concept scripts.

## Operations

| Op Code | Operation | Description |
|---------|-----------|-------------|
| `4'd1` | MUL | IEEE-754 multiplication |
| `4'd2` | DIV | IEEE-754 division (Newton-Raphson) |
| `4'd3` | SUB | IEEE-754 subtraction |
| `4'd4` | OR | Bitwise OR |
| `4'd5` | AND | Bitwise AND |
| `4'd6` | XOR | Bitwise XOR |
| `4'd7` | SHL | Left shift by 1 |
| `4'd8` | SHR | Right shift by 1 |
| `4'd9` | F2I | Float to integer conversion |
| `4'd10` | ADD | IEEE-754 addition |
| `4'd11` | COMP | Bitwise complement |

## Interface

| Port | Direction | Width | Description |
|------|-----------|-------|-------------|
| `a_operand` | input | 32 | First operand (IEEE-754) |
| `b_operand` | input | 32 | Second operand (IEEE-754) |
| `Operation` | input | 4 | Operation select |
| `ALU_Output` | output | 32 | Result (IEEE-754 or integer) |
| `Exception` | output | 1 | Invalid operation/overflow in intermediate |
| `Overflow` | output | 1 | Result exceeds max representable value |
| `Underflow` | output | 1 | Result below min representable value |

## Submodules

1. **Addition_Subtraction** - IEEE-754 add/sub with exponent alignment
2. **Multiplication** - IEEE-754 multiply with normalization and rounding
3. **Division** - Newton-Raphson iterative division
4. **Floating_Point_to_Integer** - Conversion based on exponent
5. **priority_encoder** - For normalization in subtraction

## Directory Structure

```
fp_alu_32bit/
├── rtl/
│   ├── ALU.v              # Main ALU with all submodules
│   └── ALU_spec.md        # Specification document
├── testbench/
│   ├── ALU_Top.sv         # Top-level testbench
│   ├── ALU_if.sv          # Interface definition
│   ├── ALU_seq_item.sv    # Transaction class
│   ├── ALU_driver.sv      # Drive stimulus
│   ├── ALU_monitor.sv     # Capture transactions
│   ├── ALU_agent.sv       # Agent container
│   ├── ALU_env.sv         # Environment
│   ├── ALU_scoreboard.sv  # Check results
│   ├── ALU_subscriber.sv  # Coverage collection
│   ├── ALU_reference_model.sv  # Golden model
│   ├── ALU_seq.sv         # Sequences
│   └── ALU_test.sv        # Test classes
└── sim/                   # Simulation scripts
```

## Coverage Points (from ALU_subscriber.sv)

```systemverilog
covergroup cg;
    command : coverpoint item.Operation {
        bins add = {CMD_ADD};
        bins sub = {CMD_SUB};
        bins mul = {CMD_MUL};
        bins div = {CMD_DIV};
        bins or_bin = {CMD_OR};
        bins and_bin = {CMD_AND};
        bins xor_bin = {CMD_XOR};
        bins ls = {CMD_LS};
        bins rs = {CMD_RS};
        bins float_to_int = {CMD_FLOAT_TO_INT};
        bins complement = {CMD_COMPLEMENT};
    }
    a_cg: coverpoint item.a_operand { ... }
    b_cg: coverpoint item.b_operand { ... }
endgroup
```

## Use in Concept Scripts

### Track A: Simulation
- Compile with Verilator (combinational, no clock)
- Use cocotb for Python-based testbench
- Parse UVM coverage reports

### Track B: Formal
- Complex enough for meaningful formal verification
- IEEE-754 properties (NaN handling, overflow, underflow)
- Newton-Raphson convergence properties

### Track C: Mutation
- Rich mutation space in arithmetic logic
- Submodule boundaries for targeted mutations

## Key Verification Challenges

1. **IEEE-754 Compliance**: Sign, exponent, mantissa handling
2. **Edge Cases**: NaN, Inf, denormalized numbers, zero
3. **Division Convergence**: Newton-Raphson iterations
4. **Rounding**: Truncation vs round-to-nearest
5. **Exception Detection**: When to flag overflow/underflow

## Reference Model

The `ALU_reference_model.sv` provides a golden model implementation:
- `ALU_RefModel::Operate()` - Main entry point
- `Ref_Addition_Subtraction` - Add/sub reference
- `Ref_Multiplication` - Multiply reference
- `Ref_Division` - Division reference
- `Ref_Floating_Point_to_Integer` - Conversion reference
