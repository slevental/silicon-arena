# Concept: Verilator Compile

**Task ID**: silicon-arena-6g7.4
**Spec Reference**: File 2 (RL Verification Gym Architecture.md) - "verilator --cc"

## Purpose

Demonstrate compiling Verilog RTL with Verilator and running a C++ testbench.
This is the foundation for all simulation-based verification concepts.

## What This Validates

1. **Verilator compilation**: `verilator --cc --exe` converts Verilog to C++
2. **C++ testbench**: Drive inputs and check outputs from C++
3. **VCD generation**: Waveform output for debugging
4. **Build system**: Makefile for reproducible builds

## Files

| File | Description |
|------|-------------|
| `tb_alu.cpp` | C++ testbench driving the ALU |
| `Makefile` | Build system for Verilator |
| `run.py` | Python orchestration script |
| `README.md` | This documentation |

## Quick Start

```bash
# Run the concept script
python run.py

# Or use Make directly
make run

# View waveforms (if gtkwave installed)
make trace
```

## Expected Output

```
=== ALU Verilator Testbench ===
Running 19 test vectors...

=== Test Summary ===
Passed: 19/19
Failed: 0/19
VCD written to: alu_waveform.vcd
```

## Verilator Flags Used

| Flag | Purpose |
|------|---------|
| `--cc` | Generate C++ output |
| `--exe` | Build executable |
| `--build` | Compile after generation |
| `--trace` | Enable VCD tracing |
| `-Wall` | Enable all warnings |

## Key Learnings for Gym Integration

1. **Compilation is deterministic**: Same RTL → same executable
2. **No clock needed**: For combinational ALU, just `eval()` after input change
3. **VCD for debugging**: Essential for understanding failures
4. **Exit code**: 0 = pass, 1 = fail (useful for reward)

## Next Steps

- `02-verilator-coverage`: Add `--coverage` flag for coverage metrics
- `03-cocotb-basic`: Replace C++ testbench with Python/Cocotb
