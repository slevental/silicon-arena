# Silicon Arena EDA Base Docker Image

**Task ID**: silicon-arena-6g7.3
**Spec Reference**: File 2 (RL Verification Gym Architecture.md) - "VeriGym Dockerfile Specification"

## Overview

Docker image containing EDA tools for hardware verification concept testing:
- **Verilator 5.x**: Fast simulation and coverage
- **Yosys**: Open-source synthesis
- **SymbiYosys (SBY)**: Formal verification frontend
- **Cocotb**: Python-based verification framework
- **Formal Solvers**: Z3, Yices2, Boolector

## Quick Start

```bash
# Build the image
./build.sh

# Or with docker-compose
docker-compose build

# Run interactively
docker-compose run --rm eda-base

# Or directly
docker run -it --rm -v $(pwd):/workspace silicon-arena/eda-base:latest
```

## Tool Versions

| Tool | Version | Purpose |
|------|---------|---------|
| Verilator | thomasnormal/combined-features | Simulation, coverage (enhanced SV/UVM) |
| Yosys | 0.40 | Synthesis |
| SymbiYosys | latest | Formal verification |
| Python | 3.11 | Scripting |
| Cocotb | 1.8+ | Python testbenches |
| Z3 | system | SMT solver |
| Yices2 | system | SMT solver |
| Boolector | latest | SMT solver |

### Special Verilator Fork

Uses [thomasnormal/verilator](https://github.com/thomasnormal/verilator) `local/combined-features` branch with:
- Stream expressions with `[]` selection syntax
- `$past` with explicit clock argument
- Bind with instance list syntax parsing
- Modport empty expression syntax `.name()`
- Soft constraints and UVM feature support

## Python Packages

```
cocotb>=1.8.0           # Python testbench framework
cocotb-test>=0.2.4      # Pytest integration
cocotb-coverage>=1.1.0  # Functional coverage
pyvcd>=0.3.0            # VCD parsing
vcdvcd>=2.2.0           # VCD analysis
numpy>=1.24.0           # Numerical computing
scipy>=1.11.0           # Scientific computing
xmltodict>=0.13.0       # XML/coverage parsing
pytest>=7.4.0           # Testing
```

## Example Usage

### Compile with Verilator

```bash
# Inside container
cd /workspace/rtl/alu_8bit
verilator --cc alu.v --exe tb_alu.cpp
make -C obj_dir -f Valu.mk
./obj_dir/Valu
```

### Generate Coverage

```bash
verilator --cc --coverage alu.v --exe tb_alu.cpp
make -C obj_dir -f Valu.mk
./obj_dir/Valu
verilator_coverage --annotate coverage_report coverage.dat
```

### Run Cocotb Test

```bash
cd /workspace/concepts/track-a-simulation/03-cocotb-basic
make SIM=verilator
```

### Formal Verification with SBY

```bash
cd /workspace/concepts/track-b-formal/02-sby-bounded
sby -f alu.sby
```

### Synthesize with Yosys

```bash
yosys -p "read_verilog alu.v; synth; stat"
```

## Volume Mounts

The docker-compose.yaml mounts:
- `concepts/` → `/workspace/concepts` (read-write)
- `concepts/rtl/` → `/workspace/rtl` (read-only)

## Environment Variables

| Variable | Value | Description |
|----------|-------|-------------|
| `PYTHONPATH` | `/workspace` | Python module path |
| `VERILATOR_ROOT` | `/usr/local/share/verilator` | Verilator installation |

## Image Size

Approximate size: ~2-3 GB (includes all tools compiled from source)

For a smaller image, consider:
1. Using pre-built tool packages where available
2. Multi-stage builds
3. Removing build dependencies after compilation
