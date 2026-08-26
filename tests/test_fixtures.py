"""Tests for the Retrohost seed fixtures.

Verifies that:
  - reproducible-paper's analysis produces results matching claimed.csv (REPRODUCED)
  - divergent-paper's analysis produces results NOT matching claimed.csv (DIVERGES)
  - the numeric tolerance policy works correctly
  - input data files have the expected structure
"""
import csv
import os
import subprocess
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPRODUCIBLE_DIR = os.path.join(ROOT, "examples", "reproducible-paper")
DIVERGENT_DIR = os.path.join(ROOT, "examples", "divergent-paper")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def within_tolerance(a: float, b: float, rtol: float = 1e-4, atol: float = 1e-6) -> bool:
    """Check whether |a - b| <= atol + rtol * |b|."""
    return abs(a - b) <= atol + rtol * abs(b)


def run_analysis(paper_dir: str) -> subprocess.CompletedProcess:
    """Run analysis.py in *paper_dir* and return the CompletedProcess."""
    return subprocess.run(
        [sys.executable, "analysis.py"],
        cwd=paper_dir,
        capture_output=True,
        text=True,
        check=True,
    )


def parse_table(path: str) -> dict[str, float]:
    """Read a two-column CSV (metric, mean) and return {metric: float}."""
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        return {row["metric"]: float(row["mean"]) for row in reader}


def parse_input_csv(path: str) -> tuple[list[str], int]:
    """Return (column_names, num_data_rows) from an input CSV."""
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        return list(reader.fieldnames), len(rows)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def reproducible_result():
    """Run reproducible-paper/analysis.py once and return the parsed output table."""
    run_analysis(REPRODUCIBLE_DIR)
    return parse_table(os.path.join(REPRODUCIBLE_DIR, "results", "table.csv"))


@pytest.fixture(scope="module")
def divergent_result():
    """Run divergent-paper/analysis.py once and return the parsed output table."""
    run_analysis(DIVERGENT_DIR)
    return parse_table(os.path.join(DIVERGENT_DIR, "results", "table.csv"))


def _load_claimed(paper_dir: str) -> dict[str, float]:
    return parse_table(os.path.join(paper_dir, "results", "claimed.csv"))


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestReproduciblePaper:
    """Reproducible-paper must produce 8.5 / 9.5 / 10.5, matching its claimed.csv."""

    EXPECTED_VALUES = {"mean_x": 8.5, "mean_y": 9.5, "mean_z": 10.5}

    def test_reproduces_claimed(self, reproducible_result):
        claimed = _load_claimed(REPRODUCIBLE_DIR)
        for metric in claimed:
            actual = reproducible_result[metric]
            exp = claimed[metric]
            assert within_tolerance(actual, exp), (
                f"{metric}: actual {actual} not within tolerance of claimed {exp}"
            )

    def test_exact_expected_values(self, reproducible_result):
        for metric, expected in self.EXPECTED_VALUES.items():
            actual = reproducible_result[metric]
            assert actual == pytest.approx(expected, abs=1e-9), (
                f"{metric}: got {actual}, expected {expected}"
            )

    def test_has_all_three_metrics(self, reproducible_result):
        assert set(reproducible_result.keys()) == {"mean_x", "mean_y", "mean_z"}

    def test_result_is_mean_not_sum(self, reproducible_result):
        """8.5 is the mean of [1,4,7,10,13,16], not the sum (51)."""
        assert reproducible_result["mean_x"] == 8.5
        assert reproducible_result["mean_x"] != 51.0


class TestDivergentPaper:
    """Divergent-paper's analysis produces 8.5/9.5/10.5 but claimed.csv
    has stale sums 51/57/63 → must NOT match."""

    STALE_CLAIMED_VALUES = {"mean_x": 51.0, "mean_y": 57.0, "mean_z": 63.0}

    def test_diverges_from_claimed(self, divergent_result):
        claimed = _load_claimed(DIVERGENT_DIR)
        any_outside = False
        for metric in claimed:
            actual = divergent_result[metric]
            exp = claimed[metric]
            if not within_tolerance(actual, exp):
                any_outside = True
                break
        assert any_outside, (
            f"All metrics within tolerance of claimed {claimed} — expected divergence"
        )

    def test_stale_values_not_reproduced(self, divergent_result):
        """The output must NOT equal the stale sums 51/57/63."""
        for metric, stale_val in self.STALE_CLAIMED_VALUES.items():
            assert divergent_result[metric] != stale_val, (
                f"{metric} unexpectedly equals stale value {stale_val}"
            )

    def test_analysis_still_computes_means(self, divergent_result):
        """Despite diverging from claimed, the analysis still produces correct means."""
        assert divergent_result["mean_x"] == pytest.approx(8.5, abs=1e-9)
        assert divergent_result["mean_y"] == pytest.approx(9.5, abs=1e-9)
        assert divergent_result["mean_z"] == pytest.approx(10.5, abs=1e-9)


class TestTolerancePolicy:
    """The tolerance policy (rtol=1e-4, atol=1e-6) must behave correctly."""

    def test_identical_values_match(self):
        assert within_tolerance(8.5, 8.5)

    def test_within_relative_tolerance(self):
        # 8.5 * (1 + 5e-5) = 8.500425 — within rtol=1e-4
        assert within_tolerance(8.500425, 8.5)

    def test_outside_relative_tolerance(self):
        # 8.5 * (1 + 2e-4) = 8.5017 — outside rtol=1e-4
        assert not within_tolerance(8.5017, 8.5)

    def test_within_absolute_tolerance(self):
        # tiny values: diff = 5e-7, within atol=1e-6
        assert within_tolerance(1e-10, 1e-10 + 5e-7)

    def test_outside_absolute_tolerance(self):
        # diff = 2e-6, outside atol=1e-6 and both values near zero
        assert not within_tolerance(0.0, 2e-6)

    def test_symmetry(self):
        """Tolerance check must be symmetric: within_tolerance(a, b) == within_tolerance(b, a)."""
        assert within_tolerance(8.5, 8.5001) == within_tolerance(8.5001, 8.5)

    def test_zero_vs_zero(self):
        assert within_tolerance(0.0, 0.0)

    def test_negative_values(self):
        assert within_tolerance(-8.5, -8.50005)
        assert not within_tolerance(-8.5, -8.51)

    def test_tolerance_applies_to_reproduction_comparison(self):
        """Simulate the actual Retrohost comparison: reproduced vs claimed."""
        reproduced = 8.50005
        claimed = 8.5
        assert within_tolerance(reproduced, claimed)
        # A stale sum should never be within tolerance of the correct mean
        assert not within_tolerance(51.0, 8.5)


# ---------------------------------------------------------------------------
# Classification helper (connects tolerance policy to REPRODUCED / DIVERGES)
# ---------------------------------------------------------------------------

def classify(actual: dict[str, float], claimed: dict[str, float],
             rtol: float = 1e-4, atol: float = 1e-6) -> str:
    """Classify *actual* against *claimed* using the declared tolerance policy.

    Returns REPRODUCED if every metric is within tolerance, DIVERGES otherwise.
    """
    for metric in claimed:
        if not within_tolerance(actual[metric], claimed[metric], rtol=rtol, atol=atol):
            return "DIVERGES"
    return "REPRODUCED"


class TestClassificationPolicy:
    """Prove the tolerance policy is CONNECTED to fixture classification."""

    def test_within_tolerance_classifies_reproduced(self):
        """A value within rtol of claimed must classify as REPRODUCED."""
        claimed = {"mean_x": 8.5, "mean_y": 9.5, "mean_z": 10.5}
        # 5e-5 relative offset: 8.5 * (1 + 5e-5) = 8.500425 — within rtol=1e-4
        actual = {k: v * (1 + 5e-5) for k, v in claimed.items()}
        assert classify(actual, claimed) == "REPRODUCED"

    def test_outside_tolerance_classifies_diverges(self):
        """A value outside rtol of claimed must classify as DIVERGES."""
        claimed = {"mean_x": 8.5, "mean_y": 9.5, "mean_z": 10.5}
        # 2e-4 relative offset: 8.5 * (1 + 2e-4) = 8.5017 — outside rtol=1e-4
        actual = {k: v * (1 + 2e-4) for k, v in claimed.items()}
        assert classify(actual, claimed) == "DIVERGES"


class TestInputData:
    """Both fixture input CSVs must have 6 data rows and 3 columns (x, y, z)."""

    @pytest.mark.parametrize("paper_dir,label", [
        (REPRODUCIBLE_DIR, "reproducible"),
        (DIVERGENT_DIR, "divergent"),
    ])
    def test_column_names(self, paper_dir, label):
        cols, _ = parse_input_csv(os.path.join(paper_dir, "data", "input.csv"))
        assert cols == ["x", "y", "z"], f"{label}: unexpected columns {cols}"

    @pytest.mark.parametrize("paper_dir,label", [
        (REPRODUCIBLE_DIR, "reproducible"),
        (DIVERGENT_DIR, "divergent"),
    ])
    def test_row_count(self, paper_dir, label):
        _, nrows = parse_input_csv(os.path.join(paper_dir, "data", "input.csv"))
        assert nrows == 6, f"{label}: expected 6 rows, got {nrows}"

    @pytest.mark.parametrize("paper_dir,label", [
        (REPRODUCIBLE_DIR, "reproducible"),
        (DIVERGENT_DIR, "divergent"),
    ])
    def test_data_is_numeric(self, paper_dir, label):
        """Every cell must be convertible to float (no stray text)."""
        path = os.path.join(paper_dir, "data", "input.csv")
        with open(path, newline="") as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader, 1):
                for col in ["x", "y", "z"]:
                    try:
                        float(row[col])
                    except (ValueError, KeyError) as exc:
                        pytest.fail(f"{label} row {i} col {col}: {exc}")

    def test_both_inputs_are_identical(self):
        """Both fixtures use the same input data."""
        def _read(path):
            with open(path, newline="") as f:
                return f.read()
        repro = _read(os.path.join(REPRODUCIBLE_DIR, "data", "input.csv"))
        div = _read(os.path.join(DIVERGENT_DIR, "data", "input.csv"))
        assert repro == div
