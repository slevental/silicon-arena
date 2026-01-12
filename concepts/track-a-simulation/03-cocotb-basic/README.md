# Concept: Cocotb Basic Testbench

**Task ID**: silicon-arena-6g7.7
**Spec Reference**: File 2 (RL Verification Gym Architecture.md) - "Cocotb testbenches"

## Purpose

Demonstrate Python-based hardware verification using Cocotb.
This enables LLM-generated testbenches without SystemVerilog knowledge.

## What This Validates

1. **Cocotb testbench structure**: Tests as async Python functions
2. **Stimulus generation**: Driving DUT inputs with Python
3. **Response checking**: Comparing DUT outputs to golden model
4. **Functional coverage**: Python-based coverage collection

## Files

| File | Description |
|------|-------------|
| `test_alu.py` | Cocotb testbench for ALU |
| `Makefile` | Cocotb/Verilator build system |
| `run.py` | Python orchestration script |
| `README.md` | This documentation |

## Quick Start

```bash
# Install cocotb (if not already installed)
pip install cocotb

# Run the concept
python run.py

# Or run directly with make
make

# View waveforms
make waves
```

## Testbench Structure

Cocotb tests are Python coroutines decorated with `@cocotb.test()`:

```python
@cocotb.test()
async def test_add_basic(dut):
    """Test basic addition operations."""
    # Drive inputs
    dut.a.value = 10
    dut.b.value = 20
    dut.op.value = AluOp.ADD

    # Wait for combinational logic
    await Timer(1, units="ns")

    # Check outputs
    assert int(dut.result.value) == 30
```

## Functional Coverage

Coverage is collected in Python dictionaries:

```python
coverage = {
    "operations": {op: 0 for op in range(8)},
    "zero_flag": {"set": 0, "clear": 0},
    "edge_cases": {"all_zeros": 0, "all_ones": 0},
}

def record_coverage(op, result, zero, a, b):
    coverage["operations"][op] += 1
    if zero:
        coverage["zero_flag"]["set"] += 1
```

## Test Organization

| Test | Operations Covered |
|------|-------------------|
| `test_add_basic` | ADD with various operands |
| `test_sub_basic` | SUB with various operands |
| `test_and_basic` | AND operation |
| `test_or_basic` | OR operation |
| `test_xor_basic` | XOR operation |
| `test_not_basic` | NOT (complement) |
| `test_shift_left` | SHL operation |
| `test_shift_right` | SHR operation |
| `test_coverage_report` | Coverage summary |

## LLM Integration Potential

Cocotb testbenches are ideal for LLM generation because:

1. **Python syntax**: LLMs are well-trained on Python
2. **Simple patterns**: Drive inputs → wait → check outputs
3. **No timing complexity**: Combinational logic just needs Timer()
4. **Self-documenting**: Python docstrings and assertions

Example LLM prompt:
```
Generate a Cocotb test for the ALU that:
- Tests XOR operation with all combinations of MSB
- Checks the zero flag when result is 0
- Records coverage for edge cases
```

## Integration with RL Training

```python
# In RTLEnv.step()
def step(action):
    # LLM generates test code
    test_code = self.llm.generate(action)

    # Write to test file
    Path("test_generated.py").write_text(test_code)

    # Run cocotb
    result = subprocess.run(["make", "MODULE=test_generated"])

    # Parse coverage
    coverage = json.loads("cocotb_coverage.json")

    # Compute reward
    reward = compute_coverage_reward(old_coverage, coverage)

    return observation, reward, done, info
```

## Key Learnings for Gym Integration

1. **Python-native**: No SystemVerilog compilation in test loop
2. **Fast iteration**: Cocotb handles DUT communication
3. **Coverage export**: JSON format for reward computation
4. **Assertion-based**: Clear pass/fail for sparse reward

## Dependencies

- Verilator >= 4.0
- Cocotb >= 1.8.0
- Python >= 3.8

## Next Steps

- `05-llm-stimulus`: LLM generates Cocotb tests from coverage holes
- `06-coverage-closure`: Full loop until coverage saturates
