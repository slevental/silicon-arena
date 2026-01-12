# Concept: LLM Stimulus Generation

**Task ID**: silicon-arena-6g7.8
**Spec Reference**: File 2 (RL Verification Gym Architecture.md) - "Stimulus Agent task"

## Purpose

Demonstrate using Claude to generate test stimulus targeting coverage holes.
This is the core LLM integration pattern for the RL verification gym.

## What This Validates

1. **Prompt engineering**: Creating effective prompts from coverage data
2. **Code generation**: Claude generating valid Cocotb test code
3. **Syntax validation**: Checking generated code before execution
4. **Integration pattern**: Coverage → Prompt → Generate → Validate → Run

## Files

| File | Description |
|------|-------------|
| `stimulus_generator.py` | Core LLM stimulus generation module |
| `run.py` | Demo script with/without API |
| `generated/` | Output directory for generated tests |
| `README.md` | This documentation |

## Quick Start

```bash
# Run without API (mock generation)
python run.py

# Run with Claude API
export ANTHROPIC_API_KEY="your-key"
python run.py

# Run and execute generated test
export RUN_GENERATED=1
python run.py
```

## Architecture

```
Coverage Holes (from 04-coverage-parsing)
         │
         ▼
┌─────────────────────────────────────┐
│     Prompt Generation               │
│  - ALU specification context        │
│  - Coverage hole descriptions       │
│  - RTL code snippets               │
└─────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│     Claude API Call                 │
│  - model: claude-sonnet-4-20250514  │
│  - max_tokens: 1024                 │
└─────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│     Response Parsing                │
│  - Extract code from markdown       │
│  - Parse test name and docstring    │
│  - Validate syntax                  │
└─────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│     Test Execution                  │
│  - Save to file                     │
│  - Run with Cocotb                  │
│  - Measure coverage delta           │
└─────────────────────────────────────┘
```

## Prompt Structure

The prompt includes:

1. **Module Specification**: Complete ALU interface and operation codes
2. **Coverage Holes**: List of uncovered lines/signals
3. **Cocotb Pattern**: Example test structure
4. **RTL Context**: Relevant code snippets around holes

Example prompt snippet:
```
You are an expert hardware verification engineer...

## Coverage Holes to Target

- alu.v:69 [line] OR operation case
- alu.v:70 [line] XOR operation case
- alu.v:17 [toggle] signal: a[7]:0->1

## Your Task

Generate ONE Cocotb test function that will specifically target
these coverage holes...
```

## API Usage

```python
from stimulus_generator import StimulusGenerator, CoverageHole

# Initialize generator
generator = StimulusGenerator(api_key="your-key")

# Define coverage holes
holes = [
    CoverageHole("alu.v", 69, "line", context="OR operation"),
    CoverageHole("alu.v", 70, "line", context="XOR operation"),
]

# Generate test
test = generator.generate_from_holes(holes)

if test:
    print(f"Generated: {test.test_name}")
    print(test.test_code)
```

## Integration with RL Training

```python
class StimulusAgent:
    """Agent that generates test stimulus."""

    def __init__(self):
        self.generator = StimulusGenerator()
        self.coverage_parser = CoverageParser()

    def step(self, observation: dict) -> str:
        """Generate test code based on coverage observation."""
        # Extract coverage holes from observation
        holes = [
            CoverageHole(h["file"], h["line"], h["type"])
            for h in observation["coverage_holes"]
        ]

        # Generate test
        test = self.generator.generate_from_holes(holes)

        return test.test_code if test else ""

    def compute_reward(self, old_coverage: float, new_coverage: float) -> float:
        """Compute reward from coverage improvement."""
        delta = new_coverage - old_coverage
        if delta > 0:
            bonus = 1.0 if delta > 5.0 else 0.0
            return delta * (1 + bonus)
        return -0.01  # Small penalty for no progress
```

## Generated Test Example

```python
@cocotb.test()
async def test_or_xor_coverage(dut):
    """Target OR and XOR operation coverage holes."""
    dut._log.info("Testing OR and XOR for coverage")

    # Test OR operation (op=3)
    for a, b in [(0xAA, 0x55), (0x80, 0x01), (0xFF, 0x00)]:
        dut.a.value = a
        dut.b.value = b
        dut.op.value = 3  # OR
        await Timer(1, units="ns")
        assert int(dut.result.value) == (a | b) & 0xFF

    # Test XOR operation (op=4)
    for a, b in [(0xFF, 0xFF), (0xAA, 0x55), (0x80, 0x80)]:
        dut.a.value = a
        dut.b.value = b
        dut.op.value = 4  # XOR
        await Timer(1, units="ns")
        assert int(dut.result.value) == (a ^ b) & 0xFF
```

## Key Learnings for Gym Integration

1. **Structured prompts**: Include spec, holes, and examples
2. **RTL context**: Providing relevant code improves generation
3. **Syntax validation**: Check before running to save time
4. **Incremental generation**: Target small sets of holes per iteration
5. **Model selection**: claude-sonnet-4-20250514 balances quality and speed

## Dependencies

- anthropic >= 0.20.0 (for Claude API)
- coverage_parser from 04-coverage-parsing
- cocotb (for running generated tests)

## Next Steps

- `06-coverage-closure`: Full loop until coverage saturates
- Integration with GRPO training loop
- Multi-turn generation for complex coverage targets
