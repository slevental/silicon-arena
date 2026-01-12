#!/usr/bin/env python3
"""
LLM Stimulus Generator

Task ID: silicon-arena-6g7.8
Spec Reference: File 2 (RL Verification Gym Architecture.md) - "Stimulus Agent task"

This module generates test stimulus using Claude to target coverage holes.
It demonstrates the core LLM integration pattern for the RL verification gym.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


@dataclass
class CoverageHole:
    """Represents an uncovered code location."""

    file_path: str
    line_number: int
    coverage_type: str
    signal_name: str = ""
    context: str = ""


@dataclass
class GeneratedTest:
    """Represents a generated test case."""

    test_name: str
    test_code: str
    target_holes: list[CoverageHole]
    explanation: str = ""


# ALU module context for prompts
ALU_CONTEXT = """
## ALU Module Specification

The ALU is an 8-bit arithmetic logic unit with the following interface:

### Inputs
- a[7:0]: First operand (8 bits)
- b[7:0]: Second operand (8 bits)
- op[2:0]: Operation selector (3 bits)

### Outputs
- result[7:0]: Operation result (8 bits)
- zero: Set when result is 0
- overflow: Set on arithmetic overflow
- carry: Carry out from addition/subtraction

### Operation Codes
- 000 (0): ADD - result = a + b
- 001 (1): SUB - result = a - b
- 010 (2): AND - result = a & b
- 011 (3): OR  - result = a | b
- 100 (4): XOR - result = a ^ b
- 101 (5): NOT - result = ~a
- 110 (6): SHL - result = a << b[2:0]
- 111 (7): SHR - result = a >> b[2:0]

### Cocotb Test Pattern
```python
@cocotb.test()
async def test_name(dut):
    # Drive inputs
    dut.a.value = <value>
    dut.b.value = <value>
    dut.op.value = <op_code>

    # Wait for combinational logic
    await Timer(1, units="ns")

    # Check outputs
    assert int(dut.result.value) == <expected>
```
"""


def create_coverage_prompt(holes: list[CoverageHole], rtl_snippet: str = "") -> str:
    """Create a prompt for Claude to generate tests targeting coverage holes."""
    holes_desc = []
    for hole in holes:
        desc = f"- {hole.file_path}:{hole.line_number} [{hole.coverage_type}]"
        if hole.signal_name:
            desc += f" signal: {hole.signal_name}"
        if hole.context:
            desc += f"\n  Context: {hole.context}"
        holes_desc.append(desc)

    holes_text = "\n".join(holes_desc)

    prompt = f"""You are an expert hardware verification engineer. Your task is to generate
Cocotb test cases that will exercise uncovered code paths in an ALU design.

{ALU_CONTEXT}

## Coverage Holes to Target

The following lines/signals have not been fully exercised:

{holes_text}

## Your Task

Generate ONE Cocotb test function that will specifically target these coverage holes.
The test should:
1. Exercise the specific operations or signals that are uncovered
2. Include edge cases that will toggle the uncovered signals
3. Use assertions to verify correct behavior
4. Include a docstring explaining what coverage it targets

Return ONLY the Python code for the test function, nothing else.
Start with @cocotb.test() decorator.
"""

    if rtl_snippet:
        prompt += f"\n\n## Relevant RTL Code\n```verilog\n{rtl_snippet}\n```"

    return prompt


def create_edge_case_prompt(operation: str, current_coverage: dict) -> str:
    """Create a prompt for generating edge case tests."""
    prompt = f"""You are an expert hardware verification engineer.

{ALU_CONTEXT}

## Current Coverage Status

```json
{json.dumps(current_coverage, indent=2)}
```

## Your Task

Generate a Cocotb test function that finds edge cases for the {operation} operation.
Focus on:
1. Boundary values (0x00, 0x7F, 0x80, 0xFF)
2. Sign bit transitions
3. Overflow conditions
4. Zero result conditions

Return ONLY the Python code for the test function, nothing else.
Start with @cocotb.test() decorator.
"""
    return prompt


def parse_generated_test(response: str) -> GeneratedTest | None:
    """Parse LLM response to extract test code."""
    # Extract code block if present
    code_match = re.search(r"```python\n?(.*?)```", response, re.DOTALL)
    if code_match:
        code = code_match.group(1).strip()
    else:
        # Assume the whole response is code
        code = response.strip()

    # Validate it looks like a cocotb test
    if "@cocotb.test()" not in code:
        return None

    # Extract test name
    name_match = re.search(r"async def (\w+)\(", code)
    if not name_match:
        return None

    test_name = name_match.group(1)

    # Extract docstring for explanation
    doc_match = re.search(r'"""(.*?)"""', code, re.DOTALL)
    explanation = doc_match.group(1).strip() if doc_match else ""

    return GeneratedTest(
        test_name=test_name, test_code=code, target_holes=[], explanation=explanation
    )


def validate_test_syntax(test_code: str) -> tuple[bool, str]:
    """Validate that generated test code has correct Python syntax."""
    try:
        compile(test_code, "<generated>", "exec")
        return True, "Syntax OK"
    except SyntaxError as e:
        return False, f"Syntax error: {e}"


class StimulusGenerator:
    """Generates test stimulus using LLM."""

    def __init__(self, api_key: str | None = None):
        """Initialize with optional API key."""
        self.api_key = api_key
        self._client = None

    @property
    def client(self):
        """Lazy load Anthropic client."""
        if self._client is None:
            try:
                import anthropic

                self._client = anthropic.Anthropic(api_key=self.api_key)
            except ImportError:
                raise ImportError("anthropic package not installed. Run: uv add anthropic")
        return self._client

    def generate_from_holes(
        self, holes: list[CoverageHole], rtl_snippet: str = "", max_tokens: int = 1024
    ) -> GeneratedTest | None:
        """Generate test targeting specific coverage holes."""
        prompt = create_coverage_prompt(holes, rtl_snippet)

        message = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )

        response = message.content[0].text
        test = parse_generated_test(response)

        if test:
            test.target_holes = holes

        return test

    def generate_edge_cases(
        self, operation: str, current_coverage: dict, max_tokens: int = 1024
    ) -> GeneratedTest | None:
        """Generate edge case tests for an operation."""
        prompt = create_edge_case_prompt(operation, current_coverage)

        message = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )

        response = message.content[0].text
        return parse_generated_test(response)


def get_rtl_context(file_path: str, line_numbers: list[int], context_lines: int = 5) -> str:
    """Get RTL code context around specific lines."""
    path = Path(file_path)
    if not path.exists():
        return ""

    lines = path.read_text().split("\n")

    # Collect unique line ranges
    ranges = set()
    for line_num in line_numbers:
        start = max(0, line_num - context_lines - 1)
        end = min(len(lines), line_num + context_lines)
        ranges.add((start, end))

    # Merge overlapping ranges
    sorted_ranges = sorted(ranges)
    merged = []
    for start, end in sorted_ranges:
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))

    # Extract code
    snippets = []
    for start, end in merged:
        snippet = "\n".join(f"{i + 1}: {lines[i]}" for i in range(start, end))
        snippets.append(snippet)

    return "\n...\n".join(snippets)


if __name__ == "__main__":
    # Demo usage
    print("LLM Stimulus Generator")
    print("=" * 50)

    # Example coverage holes
    holes = [
        CoverageHole("alu.v", 69, "line", context="OR operation case"),
        CoverageHole("alu.v", 70, "line", context="XOR operation case"),
        CoverageHole("alu.v", 17, "toggle", "a[7]:0->1", "MSB of operand a"),
    ]

    print("\nTarget coverage holes:")
    for hole in holes:
        print(f"  {hole.file_path}:{hole.line_number} [{hole.coverage_type}]")

    print("\nGenerated prompt preview:")
    prompt = create_coverage_prompt(holes[:2])
    print(prompt[:500] + "...")
