# Verilator Simulation for FP ALU

## Overview

This directory contains Verilator-based simulation infrastructure for the 32-bit IEEE-754 floating-point ALU.

## Quick Start

```bash
# Build with Verilator
make -f Makefile.verilator all

# Run simulation
make -f Makefile.verilator run

# Generate coverage report
make -f Makefile.verilator coverage

# View waveforms
make -f Makefile.verilator trace
make -f Makefile.verilator waves
```

## Known Limitation: Tristate Logic

**Important**: The FP ALU design uses tristate (high-Z) logic for output multiplexing:

```verilog
assign ALU_Output = (Operation == 4'd10) ? Add_Sub_Output : 32'dz;
assign ALU_Output = (Operation == 4'd1)  ? Mul_Output     : 32'dz;
// ... etc
```

Verilator does not fully support tristate simulation. It treats 'z' values as '0', causing incorrect functional results. However:

1. **Coverage still works**: Toggle and line coverage is collected correctly
2. **Compilation succeeds**: The design compiles and links
3. **Submodules work**: Individual submodules (Addition_Subtraction, Multiplication, Division) function correctly

## Workaround Options

For accurate functional simulation, consider:

1. **Use Icarus Verilog**: `iverilog` supports tristates
2. **Refactor RTL**: Replace tristate muxing with proper case/mux statements
3. **Use Cocotb with Icarus**: Python testbench with full tristate support

Example refactored output (not applied):
```verilog
always @(*) begin
    case (Operation)
        4'd1:  ALU_Output = Mul_Output;
        4'd2:  ALU_Output = Div_Output;
        4'd3:  ALU_Output = Add_Sub_Output;
        // ...
        default: ALU_Output = 32'b0;
    endcase
end
```

## Files

| File | Description |
|------|-------------|
| `Makefile.verilator` | Verilator build system |
| `tb_fp_alu.cpp` | C++ testbench |
| `coverage.dat` | Generated coverage data |

## Coverage Analysis

Despite the tristate limitation, coverage data is valid for:
- Identifying untested operations
- Measuring toggle coverage on internal signals
- Computing coverage-based rewards in RL training

```bash
# Parse coverage
verilator_coverage --annotate annotated coverage.dat

# View annotated source
cat annotated/ALU.v
```
