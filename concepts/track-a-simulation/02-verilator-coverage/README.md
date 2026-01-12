# Concept: Verilator Coverage

**Task ID**: silicon-arena-6g7.5
**Spec Reference**: File 2 (RL Verification Gym Architecture.md) - "Coverage tracking via Verilator --coverage"

## Purpose

Demonstrate generating and analyzing coverage data with Verilator.
This is essential for computing coverage-based rewards in the RL training loop.

## What This Validates

1. **Coverage instrumentation**: `verilator --coverage --coverage-line --coverage-toggle`
2. **Coverage data generation**: `coverage.dat` file format
3. **Coverage analysis**: `verilator_coverage` tool usage
4. **Coverage gaps**: Intentionally incomplete tests to show uncovered code

## Files

| File | Description |
|------|-------------|
| `tb_alu_cov.cpp` | C++ testbench with intentional coverage gaps |
| `Makefile` | Build and coverage analysis targets |
| `run.py` | Python orchestration and analysis script |
| `README.md` | This documentation |

## Quick Start

```bash
# Run the full concept
python run.py

# Or step by step
make all        # Compile with coverage
make run        # Run simulation (generates coverage.dat)
make annotate   # Generate annotated source files
make html       # Generate HTML report (requires genhtml)
make report     # Generate all reports
```

## Coverage Types

| Type | Flag | Description |
|------|------|-------------|
| Line | `--coverage-line` | Which lines were executed |
| Toggle | `--coverage-toggle` | Which signals changed value |
| Branch | `--coverage-branch` | Which branches were taken |

## verilator_coverage Tool

```bash
# Annotate source files with coverage
verilator_coverage --annotate <dir> coverage.dat

# Generate lcov format for HTML
verilator_coverage --write-info coverage.info coverage.dat

# Merge multiple coverage files
verilator_coverage --write merged.dat cov1.dat cov2.dat

# Show test ranking by coverage contribution
verilator_coverage --rank coverage.dat
```

## Coverage Annotation Legend

| Symbol | Meaning |
|--------|---------|
| ` ` (space) | All coverage points hit >= threshold |
| `%` | Below minimum threshold |
| `~` | Mixed (some above, some below) |
| `+` | Above threshold with point details |
| `-` | Below threshold with point details |

## Expected Output

The testbench intentionally only tests ADD, SUB, AND operations.
This creates coverage gaps in:
- OR operation (op=011)
- XOR operation (op=100)
- NOT operation (op=101)
- SHL operation (op=110)
- SHR operation (op=111)

## Key Learnings for Gym Integration

1. **Coverage as reward signal**: `R_coverage = Δcov × scaling_factor`
2. **Coverage holes identify targets**: Parse annotated files for `%` lines
3. **Incremental coverage**: Compare `coverage_t` vs `coverage_{t-1}`
4. **Multiple coverage types**: Line + toggle give complementary views

## Integration with RL Training

```python
# Pseudocode for coverage-based reward
def compute_reward(coverage_before, coverage_after):
    delta = coverage_after - coverage_before
    if delta > 0:
        return ALPHA * delta / TOTAL_POINTS
    else:
        return SMALL_PENALTY  # No progress
```

## Next Steps

- `04-coverage-parsing`: Python parser for coverage.dat
- `05-llm-stimulus`: LLM generates tests targeting coverage holes
- `06-coverage-closure`: Full loop until coverage saturates
