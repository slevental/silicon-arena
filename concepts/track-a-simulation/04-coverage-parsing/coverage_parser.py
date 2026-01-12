#!/usr/bin/env python3
"""
Verilator Coverage Parser

Task ID: silicon-arena-6g7.6
Spec Reference: File 2 - "CoverageParser utility"

This module provides comprehensive parsing of Verilator coverage.dat files
for use in reward computation and coverage-guided test generation.

Updated for 32-bit IEEE-754 FP ALU with operations:
- 1: MUL, 2: DIV, 3: SUB, 4: OR, 5: AND, 6: XOR
- 7: SHL, 8: SHR, 9: FP2INT, 10: ADD, 11: COMPLEMENT

Coverage.dat format (SystemC::Coverage-3):
  C '<data>' <count>

Where <data> contains encoded information:
  - f<filepath>: Source file path
  - l<num>: Line number
  - n<num>: Column number
  - t<type>: Coverage type (toggle, line, branch)
  - page<type>: Page type (v_toggle, v_line, etc.)
  - Signal/variable name
  - h<hierarchy>: Hierarchy path

Example:
  C 'f../../rtl/fp_alu_32bit/rtl/ALU.vl17n31ttogglepagev_toggle/aluoa[0]:0->1hTOP.ALU' 6
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator


@dataclass
class CoveragePoint:
    """Represents a single coverage point from Verilator."""

    file_path: str
    line_number: int
    column_number: int
    coverage_type: str  # 'toggle', 'line', 'branch'
    signal_name: str
    hierarchy: str
    hit_count: int
    raw_data: str = ""

    @property
    def is_covered(self) -> bool:
        """Return True if this point was hit at least once."""
        return self.hit_count > 0

    @property
    def location(self) -> str:
        """Return formatted location string."""
        return f"{self.file_path}:{self.line_number}"


@dataclass
class FileCoverage:
    """Coverage data aggregated per file."""

    file_path: str
    line_points: list[CoveragePoint] = field(default_factory=list)
    toggle_points: list[CoveragePoint] = field(default_factory=list)
    branch_points: list[CoveragePoint] = field(default_factory=list)

    @property
    def total_points(self) -> int:
        """Total number of coverage points."""
        return len(self.line_points) + len(self.toggle_points) + len(self.branch_points)

    @property
    def covered_points(self) -> int:
        """Number of points that were hit."""
        return sum(
            1 for p in self.line_points + self.toggle_points + self.branch_points if p.is_covered
        )

    @property
    def coverage_percentage(self) -> float:
        """Overall coverage percentage."""
        if self.total_points == 0:
            return 0.0
        return (self.covered_points / self.total_points) * 100.0

    def get_uncovered_lines(self) -> set[int]:
        """Return set of line numbers with uncovered points."""
        uncovered = set()
        for point in self.line_points + self.toggle_points + self.branch_points:
            if not point.is_covered:
                uncovered.add(point.line_number)
        return uncovered


@dataclass
class CoverageReport:
    """Complete coverage report from a coverage.dat file."""

    files: dict[str, FileCoverage] = field(default_factory=dict)
    version: str = ""
    raw_points: list[CoveragePoint] = field(default_factory=list)

    @property
    def total_points(self) -> int:
        """Total coverage points across all files."""
        return sum(f.total_points for f in self.files.values())

    @property
    def covered_points(self) -> int:
        """Total covered points across all files."""
        return sum(f.covered_points for f in self.files.values())

    @property
    def coverage_percentage(self) -> float:
        """Overall coverage percentage."""
        if self.total_points == 0:
            return 0.0
        return (self.covered_points / self.total_points) * 100.0

    def get_line_coverage(self) -> tuple[int, int, float]:
        """Return (covered, total, percentage) for line coverage."""
        total = sum(len(f.line_points) for f in self.files.values())
        covered = sum(sum(1 for p in f.line_points if p.is_covered) for f in self.files.values())
        pct = (covered / total * 100) if total > 0 else 0.0
        return covered, total, pct

    def get_toggle_coverage(self) -> tuple[int, int, float]:
        """Return (covered, total, percentage) for toggle coverage."""
        total = sum(len(f.toggle_points) for f in self.files.values())
        covered = sum(
            sum(1 for p in f.toggle_points if p.is_covered) for f in self.files.values()
        )
        pct = (covered / total * 100) if total > 0 else 0.0
        return covered, total, pct

    def get_branch_coverage(self) -> tuple[int, int, float]:
        """Return (covered, total, percentage) for branch coverage."""
        total = sum(len(f.branch_points) for f in self.files.values())
        covered = sum(
            sum(1 for p in f.branch_points if p.is_covered) for f in self.files.values()
        )
        pct = (covered / total * 100) if total > 0 else 0.0
        return covered, total, pct

    def get_coverage_holes(self) -> list[tuple[str, int, str]]:
        """Return list of (file, line, type) for uncovered points."""
        holes = []
        for file_path, file_cov in self.files.items():
            for point in file_cov.line_points + file_cov.toggle_points + file_cov.branch_points:
                if not point.is_covered:
                    holes.append((file_path, point.line_number, point.coverage_type))
        return sorted(set(holes))


class CoverageParser:
    """Parser for Verilator coverage.dat files."""

    # Verilator coverage.dat uses binary control characters as delimiters:
    # \x01 (SOH) followed by key letter
    # \x02 (STX) followed by value
    # Format: \x01f\x02<file>\x01l\x02<line>\x01n\x02<col>\x01t\x02<type>
    #         \x01page\x02<page>/<path>\x01o\x02<signal>\x01h\x02<hier>
    FIELD_PATTERN = re.compile(r"\x01(\w+)\x02([^\x01]*)")

    # Legacy pattern for non-binary format (older Verilator versions)
    LEGACY_PATTERN = re.compile(
        r"f(?P<file>.+?\.(?:sv|v))"
        r"l(?P<line>\d+)"
        r"n(?P<col>\d+)"
        r"t(?P<type>\w+)"
        r"page(?P<page>\w+)"
        r"/(?P<signal>[^h]+)"
        r"h(?P<hier>.+)"
    )

    def __init__(self, coverage_file: Path | str):
        self.coverage_file = Path(coverage_file)
        self._report: CoverageReport | None = None

    def parse(self) -> CoverageReport:
        """Parse the coverage file and return a CoverageReport."""
        if self._report is not None:
            return self._report

        report = CoverageReport()

        if not self.coverage_file.exists():
            return report

        content = self.coverage_file.read_text()
        lines = content.split("\n")

        for line in lines:
            line = line.strip()

            # Parse header
            if line.startswith("#"):
                report.version = line.lstrip("# ")
                continue

            # Parse coverage point: C '<data>' <count>
            if line.startswith("C "):
                point = self._parse_coverage_line(line)
                if point:
                    report.raw_points.append(point)
                    self._add_point_to_file(report, point)

        self._report = report
        return report

    def _parse_coverage_line(self, line: str) -> CoveragePoint | None:
        """Parse a single coverage line."""
        # Extract quoted data and count
        match = re.match(r"C '([^']+)' (\d+)", line)
        if not match:
            return None

        data = match.group(1)
        count = int(match.group(2))

        # Try binary format first (modern Verilator)
        if "\x01" in data:
            return self._parse_binary_format(data, count)

        # Try legacy text format
        data_match = self.LEGACY_PATTERN.match(data)
        if data_match:
            return CoveragePoint(
                file_path=data_match.group("file"),
                line_number=int(data_match.group("line")),
                column_number=int(data_match.group("col")),
                coverage_type=data_match.group("type"),
                signal_name=data_match.group("signal"),
                hierarchy=data_match.group("hier"),
                hit_count=count,
                raw_data=data,
            )

        # Fallback for non-matching format
        return CoveragePoint(
            file_path="unknown",
            line_number=0,
            column_number=0,
            coverage_type="unknown",
            signal_name=data,
            hierarchy="",
            hit_count=count,
            raw_data=data,
        )

    def _parse_binary_format(self, data: str, count: int) -> CoveragePoint:
        """Parse modern Verilator binary format with control characters."""
        fields: dict[str, str] = {}
        for key, value in self.FIELD_PATTERN.findall(data):
            fields[key] = value

        # Extract file path and page info
        file_path = fields.get("f", "unknown")
        line_number = int(fields.get("l", "0"))
        column_number = int(fields.get("n", "0"))
        coverage_type = fields.get("t", "unknown")
        hierarchy = fields.get("h", "")

        # Signal is in 'o' field (output)
        signal_name = fields.get("o", "")

        # Page field may contain path info like "v_toggle/alu"
        page = fields.get("page", "")

        return CoveragePoint(
            file_path=file_path,
            line_number=line_number,
            column_number=column_number,
            coverage_type=coverage_type,
            signal_name=signal_name,
            hierarchy=hierarchy,
            hit_count=count,
            raw_data=data,
        )

    def _add_point_to_file(self, report: CoverageReport, point: CoveragePoint) -> None:
        """Add a coverage point to the appropriate file in the report."""
        if point.file_path not in report.files:
            report.files[point.file_path] = FileCoverage(file_path=point.file_path)

        file_cov = report.files[point.file_path]

        if point.coverage_type == "toggle":
            file_cov.toggle_points.append(point)
        elif point.coverage_type == "line":
            file_cov.line_points.append(point)
        elif point.coverage_type == "branch":
            file_cov.branch_points.append(point)
        else:
            # Default to toggle for unknown types
            file_cov.toggle_points.append(point)

    def iter_points(self) -> Iterator[CoveragePoint]:
        """Iterate over all coverage points."""
        report = self.parse()
        yield from report.raw_points


def compute_coverage_delta(before: CoverageReport, after: CoverageReport) -> dict:
    """
    Compute the coverage delta between two reports.

    This is the core computation for coverage-based rewards:
        R_coverage = Δcov × (1 + bonus)

    Returns dict with delta metrics.
    """
    delta = {
        "points_before": before.covered_points,
        "points_after": after.covered_points,
        "points_delta": after.covered_points - before.covered_points,
        "total_points": after.total_points,
        "coverage_before": before.coverage_percentage,
        "coverage_after": after.coverage_percentage,
        "coverage_delta": after.coverage_percentage - before.coverage_percentage,
        "new_covered_lines": [],
    }

    # Find newly covered lines
    before_covered = set()
    after_covered = set()

    for point in before.raw_points:
        if point.is_covered:
            before_covered.add((point.file_path, point.line_number))

    for point in after.raw_points:
        if point.is_covered:
            after_covered.add((point.file_path, point.line_number))

    delta["new_covered_lines"] = list(after_covered - before_covered)

    return delta


def compute_reward(
    coverage_delta: dict,
    alpha: float = 1.0,
    small_penalty: float = -0.01,
    bonus_threshold: float = 5.0,
) -> float:
    """
    Compute reward from coverage delta.

    Spec Reference (File 2):
        R_coverage = Δcov × (1 + bonus)

    Args:
        coverage_delta: Output from compute_coverage_delta()
        alpha: Scaling factor for positive rewards
        small_penalty: Penalty for no progress
        bonus_threshold: Percentage gain for bonus multiplier

    Returns:
        Computed reward value
    """
    delta_pct = coverage_delta["coverage_delta"]

    if delta_pct > 0:
        # Positive progress
        bonus = 1.0 if delta_pct >= bonus_threshold else 0.0
        return alpha * delta_pct * (1 + bonus)
    else:
        # No progress or regression
        return small_penalty


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: coverage_parser.py <coverage.dat>")
        sys.exit(1)

    parser = CoverageParser(sys.argv[1])
    report = parser.parse()

    print(f"Coverage Report: {parser.coverage_file}")
    print(f"Version: {report.version}")
    print()
    print("=== Summary ===")
    print(f"Total Points: {report.total_points}")
    print(f"Covered Points: {report.covered_points}")
    print(f"Coverage: {report.coverage_percentage:.2f}%")
    print()

    line_cov, line_total, line_pct = report.get_line_coverage()
    toggle_cov, toggle_total, toggle_pct = report.get_toggle_coverage()
    branch_cov, branch_total, branch_pct = report.get_branch_coverage()

    print("=== By Type ===")
    print(f"Line Coverage: {line_cov}/{line_total} ({line_pct:.2f}%)")
    print(f"Toggle Coverage: {toggle_cov}/{toggle_total} ({toggle_pct:.2f}%)")
    print(f"Branch Coverage: {branch_cov}/{branch_total} ({branch_pct:.2f}%)")
    print()

    print("=== Files ===")
    for file_path, file_cov in sorted(report.files.items()):
        print(f"{file_path}: {file_cov.covered_points}/{file_cov.total_points} ({file_cov.coverage_percentage:.2f}%)")

    print()
    print("=== Coverage Holes (first 20) ===")
    holes = report.get_coverage_holes()[:20]
    for file_path, line, cov_type in holes:
        print(f"  {file_path}:{line} [{cov_type}]")
