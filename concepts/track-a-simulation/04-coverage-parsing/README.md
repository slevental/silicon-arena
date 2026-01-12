# Concept: Coverage Parsing

**Task ID**: silicon-arena-6g7.6
**Spec Reference**: File 2 (RL Verification Gym Architecture.md) - "CoverageParser utility"

## Purpose

Provide a robust Python parser for Verilator coverage.dat files.
This enables coverage-based reward computation in the RL training loop.

## What This Validates

1. **Coverage.dat parsing**: Handle SystemC::Coverage-3 format
2. **Coverage metrics**: Line, toggle, and branch coverage extraction
3. **Coverage holes**: Identify uncovered code for stimulus targeting
4. **Delta computation**: Compare coverage between runs for reward

## Files

| File | Description |
|------|-------------|
| `coverage_parser.py` | Main parser module with dataclasses |
| `run.py` | Demo script exercising the parser |
| `README.md` | This documentation |

## Quick Start

```bash
# Generate coverage data first
cd ../02-verilator-coverage
make run

# Run the parser
cd ../04-coverage-parsing
python run.py

# Or use the module directly
python coverage_parser.py ../02-verilator-coverage/coverage.dat
```

## API Overview

### Data Classes

```python
@dataclass
class CoveragePoint:
    file_path: str
    line_number: int
    column_number: int
    coverage_type: str  # 'toggle', 'line', 'branch'
    signal_name: str
    hierarchy: str
    hit_count: int

@dataclass
class FileCoverage:
    file_path: str
    line_points: list[CoveragePoint]
    toggle_points: list[CoveragePoint]
    branch_points: list[CoveragePoint]

@dataclass
class CoverageReport:
    files: dict[str, FileCoverage]
    version: str
    raw_points: list[CoveragePoint]
```

### Parser Usage

```python
from coverage_parser import CoverageParser

parser = CoverageParser("coverage.dat")
report = parser.parse()

# Access metrics
print(f"Coverage: {report.coverage_percentage:.2f}%")

# Get coverage by type
line_cov, line_total, line_pct = report.get_line_coverage()
toggle_cov, toggle_total, toggle_pct = report.get_toggle_coverage()

# Find coverage holes
holes = report.get_coverage_holes()
for file_path, line, cov_type in holes:
    print(f"Uncovered: {file_path}:{line} [{cov_type}]")
```

### Reward Computation

```python
from coverage_parser import compute_coverage_delta, compute_reward

# Compare two coverage reports
delta = compute_coverage_delta(before_report, after_report)
print(f"Coverage improved by {delta['coverage_delta']:.2f}%")

# Compute reward (Spec: R_coverage = Δcov × (1 + bonus))
reward = compute_reward(delta, alpha=1.0, small_penalty=-0.01)
print(f"Reward: {reward:.4f}")
```

## Coverage.dat Format

Verilator's coverage.dat uses SystemC::Coverage format:

```
# SystemC::Coverage-3
C '<data>' <count>
```

Where `<data>` encodes:
- `f<filepath>`: Source file path
- `l<line>`: Line number
- `n<col>`: Column number
- `t<type>`: Coverage type (toggle, line, branch)
- `page<page>`: Page type
- `/<signal>`: Signal name
- `h<hier>`: Hierarchy path

Example:
```
C 'f../../rtl/alu.vl17n31ttogglepagev_toggle/aluoa[0]:0->1hTOP.alu' 6
```

## Integration with RL Training

```python
# In the training loop
def step(action):
    # Apply action (run new stimulus)
    run_simulation()

    # Parse new coverage
    parser = CoverageParser("coverage.dat")
    new_report = parser.parse()

    # Compute reward
    delta = compute_coverage_delta(old_report, new_report)
    reward = compute_reward(delta)

    # Get coverage holes for observation
    holes = new_report.get_coverage_holes()

    return observation, reward, done, info
```

## Key Learnings for Gym Integration

1. **Coverage as observation**: Include coverage holes in agent observation
2. **Delta reward**: Reward proportional to coverage improvement
3. **Bonus for big gains**: Extra reward for large coverage jumps
4. **Penalty for stagnation**: Small penalty when no progress made

## Next Steps

- `05-llm-stimulus`: Use coverage holes to prompt LLM for targeted tests
- `06-coverage-closure`: Full loop until coverage saturates
