# Contributing to Retrohost

Thanks for looking at this repo. Here's how it works and how to add to it.

## Project layout

```
agent.json                  TrueForge agent manifest (model, MCP servers, skills, config)
skills/
  reproduction-review-playbook/
    SKILL.md                The reproduction audit playbook the agent follows
    references/
      tolerance-policy.md   Numeric tolerance rules for classification
examples/
  reproducible-paper/       Seed fixture: analysis matches claimed.csv → REPRODUCED
  divergent-paper/          Seed fixture: stale claimed sums → DIVERGES
  gate-mcp/                 Approval-gate MCP test fixture (Node 22+)
tests/
  test_fixtures.py          25 pytest tests verifying fixture behavior and tolerance policy
.github/workflows/ci.yml   CI: runs both fixtures, asserts reproducible matches and divergent doesn't
requirements.txt            Runtime deps (numpy, matplotlib) for the sandbox image
requirements-dev.txt        Dev deps (pytest)
```

## Development setup

Requires Python 3.12+ and Node.js 22+ (for the MCP fixture).

```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
python -m pytest tests/ -v
```

CI runs on every push/PR to `main`. Locally, run the same steps above to check your work before pushing.

## Adding a new seed fixture

1. Copy `examples/reproducible-paper` as your starting point.

2. Keep `data/input.csv` in the same shape: 6 data rows, columns `x`, `y`, `z`, all numeric. The existing test suite asserts this structure for every fixture.

3. Write your `analysis.py` to read `data/input.csv`, compute results, and write a two-column CSV (`metric`, `mean`) to `results/table.csv`. Use Python stdlib only (`csv`, `os`, `math`). No numpy, no pandas in the analysis script itself.

4. Create `results/claimed.csv` with the same `metric`/`mean` shape. This file holds the "paper's claim" that the agent will compare against.

5. Decide whether your fixture should be REPRODUCED or DIVERGES:
   - **REPRODUCED**: `results/table.csv` must match `results/claimed.csv` (within tolerance).
   - **DIVERGES**: `results/table.csv` must differ from `results/claimed.csv`. The `divergent-paper` fixture does this by putting stale sums (51/57/63) in claimed.csv while the analysis computes correct means (8.5/9.5/10.5).

6. Add a `README.md` describing what the fixture represents, what the claimed result is, and the expected classification.

7. Update `tests/test_fixtures.py` with tests for your new fixture.

## Test conventions

All numeric comparisons use the project's tolerance policy. Never compare floats with exact equality in new tests.

```python
def within_tolerance(a: float, b: float, rtol: float = 1e-4, atol: float = 1e-6) -> bool:
    """Check whether |a - b| <= atol + rtol * |b|."""
    return abs(a - b) <= atol + rtol * abs(b)
```

`rtol=1e-4` (relative) and `atol=1e-6` (absolute) give floating-point results room to vary across platforms without false failures. The test suite includes `TestTolerancePolicy` which validates boundary behavior. If you add tolerance-sensitive comparisons, follow the same pattern.

The one exception: `pytest.approx` with `abs=1e-9` is used for exact expected values (like 8.5) where the computation is deterministic and platform-independent.

## The gate-mcp fixture

`examples/gate-mcp/` is a Node.js MCP server used to test Retrohost's approval-gate flow. It requires Node 22+ and uses `@modelcontextprotocol/sdk` and `zod`. Run it with:

```bash
cd examples/gate-mcp
npm install
npm start
```

Don't add Python dependencies to this fixture. It's intentionally separate.

## PR workflow

- **Branch naming**: `feat/...` for features, `fix/...` for bug fixes.
- **Qodo bot reviews every PR.** It posts findings automatically. Address them before requesting human review.
- **Keep PRs focused.** One fixture addition per PR, or one behavioral change per PR. Don't bundle unrelated changes.
- **CI must pass.** The `validate-fixtures` job runs both `reproducible-paper` and `divergent-paper` end-to-end. If CI fails, your fixture is wrong.

## Code style

- Python: stdlib in fixture analysis scripts. No type annotations needed, but they're fine.
- JavaScript/Node: ESM (`"type": "module"`), Node 22+ APIs.
- No linter configured. Write clear, straightforward code. Readability beats cleverness.
- Commit messages: short, imperative, descriptive. "Add divergent-paper fixture" not "updates".
