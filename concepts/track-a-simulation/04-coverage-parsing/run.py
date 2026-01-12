#!/usr/bin/env python3
"""
Coverage Parser Concept Script

Task ID: silicon-arena-6g7.6
Spec Reference: File 2 - "CoverageParser utility"

This script demonstrates:
1. Parsing Verilator coverage.dat files
2. Computing coverage metrics
3. Identifying coverage holes
4. Computing rewards from coverage deltas
"""

import sys
from pathlib import Path

# Add parent directory to path for importing coverage_parser
sys.path.insert(0, str(Path(__file__).parent))

from coverage_parser import CoverageParser, CoverageReport, compute_coverage_delta, compute_reward


def create_mock_before_report() -> CoverageReport:
    """Create a mock 'before' report with partial coverage."""
    from coverage_parser import CoveragePoint, FileCoverage

    report = CoverageReport()
    report.version = "SystemC::Coverage-3 (mock before)"

    # Simulate partial coverage
    file_cov = FileCoverage(file_path="alu.v")
    file_cov.toggle_points = [
        CoveragePoint("alu.v", 17, 31, "toggle", "a[0]:0->1", "TOP.alu", 5, ""),
        CoveragePoint("alu.v", 17, 31, "toggle", "a[0]:1->0", "TOP.alu", 4, ""),
        CoveragePoint("alu.v", 18, 31, "toggle", "b[0]:0->1", "TOP.alu", 0, ""),  # uncovered
        CoveragePoint("alu.v", 18, 31, "toggle", "b[0]:1->0", "TOP.alu", 0, ""),  # uncovered
    ]
    report.files["alu.v"] = file_cov
    report.raw_points = file_cov.toggle_points.copy()

    return report


def create_mock_after_report() -> CoverageReport:
    """Create a mock 'after' report with improved coverage."""
    from coverage_parser import CoveragePoint, FileCoverage

    report = CoverageReport()
    report.version = "SystemC::Coverage-3 (mock after)"

    # Simulate improved coverage
    file_cov = FileCoverage(file_path="alu.v")
    file_cov.toggle_points = [
        CoveragePoint("alu.v", 17, 31, "toggle", "a[0]:0->1", "TOP.alu", 8, ""),
        CoveragePoint("alu.v", 17, 31, "toggle", "a[0]:1->0", "TOP.alu", 7, ""),
        CoveragePoint("alu.v", 18, 31, "toggle", "b[0]:0->1", "TOP.alu", 3, ""),  # now covered
        CoveragePoint("alu.v", 18, 31, "toggle", "b[0]:1->0", "TOP.alu", 2, ""),  # now covered
    ]
    report.files["alu.v"] = file_cov
    report.raw_points = file_cov.toggle_points.copy()

    return report


def main():
    script_dir = Path(__file__).parent.resolve()
    coverage_concept_dir = script_dir.parent / "02-verilator-coverage"
    coverage_file = coverage_concept_dir / "coverage.dat"

    print("=" * 60)
    print("Coverage Parser Concept Script")
    print("=" * 60)
    print()

    # Step 1: Check if coverage.dat exists
    print("[1/4] Checking for coverage.dat...")
    if not coverage_file.exists():
        print(f"      WARNING: {coverage_file} not found")
        print("      Run 02-verilator-coverage first to generate coverage.dat")
        print("      Using mock data for demonstration...")
        print()
        use_mock = True
    else:
        print(f"      Found: {coverage_file}")
        print(f"      Size: {coverage_file.stat().st_size} bytes")
        print()
        use_mock = False

    # Step 2: Parse coverage data
    print("[2/4] Parsing coverage data...")
    print("-" * 60)

    if use_mock:
        report = create_mock_before_report()
        print("      Using mock coverage data")
    else:
        parser = CoverageParser(coverage_file)
        report = parser.parse()

    print(f"      Version: {report.version}")
    print(f"      Total Points: {report.total_points}")
    print(f"      Covered Points: {report.covered_points}")
    print(f"      Coverage: {report.coverage_percentage:.2f}%")
    print()

    # Step 3: Show coverage by type
    print("[3/4] Coverage breakdown by type...")
    print("-" * 60)

    line_cov, line_total, line_pct = report.get_line_coverage()
    toggle_cov, toggle_total, toggle_pct = report.get_toggle_coverage()
    branch_cov, branch_total, branch_pct = report.get_branch_coverage()

    print(f"      Line Coverage:   {line_cov:4d}/{line_total:4d} ({line_pct:6.2f}%)")
    print(f"      Toggle Coverage: {toggle_cov:4d}/{toggle_total:4d} ({toggle_pct:6.2f}%)")
    print(f"      Branch Coverage: {branch_cov:4d}/{branch_total:4d} ({branch_pct:6.2f}%)")
    print()

    # Show files
    print("      Files:")
    for file_path, file_cov in sorted(report.files.items()):
        print(f"        {file_path}: {file_cov.covered_points}/{file_cov.total_points} ({file_cov.coverage_percentage:.2f}%)")
    print()

    # Step 4: Demonstrate reward computation
    print("[4/4] Coverage delta and reward computation...")
    print("-" * 60)

    if use_mock:
        before = create_mock_before_report()
        after = create_mock_after_report()
    else:
        # For real data, simulate a "before" with fewer hits
        before = CoverageReport()
        before.version = "mock-before"
        # Create artificial before state with 50% of coverage
        from coverage_parser import CoveragePoint, FileCoverage

        for file_path, file_cov in report.files.items():
            before_file = FileCoverage(file_path=file_path)
            for i, point in enumerate(file_cov.toggle_points):
                # Only count first half as covered in "before"
                hit_count = point.hit_count if i < len(file_cov.toggle_points) // 2 else 0
                before_file.toggle_points.append(
                    CoveragePoint(
                        point.file_path,
                        point.line_number,
                        point.column_number,
                        point.coverage_type,
                        point.signal_name,
                        point.hierarchy,
                        hit_count,
                        point.raw_data,
                    )
                )
            before.files[file_path] = before_file
            before.raw_points.extend(before_file.toggle_points)

        after = report

    # Compute delta
    delta = compute_coverage_delta(before, after)

    print(f"      Coverage Before: {delta['coverage_before']:.2f}%")
    print(f"      Coverage After:  {delta['coverage_after']:.2f}%")
    print(f"      Coverage Delta:  {delta['coverage_delta']:+.2f}%")
    print(f"      Points Delta:    {delta['points_delta']:+d}")
    print()

    # Compute reward
    reward = compute_reward(delta, alpha=1.0, small_penalty=-0.01, bonus_threshold=5.0)
    print(f"      Computed Reward: {reward:.4f}")
    print()

    # Show coverage holes
    print("      Coverage Holes (first 10):")
    holes = after.get_coverage_holes()[:10]
    if holes:
        for file_path, line, cov_type in holes:
            print(f"        {file_path}:{line} [{cov_type}]")
    else:
        print("        None (100% coverage)")
    print()

    print("=" * 60)
    print("Coverage parsing concept validation complete!")
    print()
    print("Key observations:")
    print("  - Parser handles SystemC::Coverage-3 format")
    print("  - Coverage types: line, toggle, branch")
    print("  - Delta computation enables reward calculation")
    print("  - Coverage holes identify targets for LLM stimulus")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
