# Retrohost

A paper-reproduction auditor agent on TrueForge.

## What it does

Retrohost takes a public GitHub repo linked to a published paper and checks
whether its figures actually reproduce. It runs each figure's analysis in an
isolated Daytona sandbox, classifies results as REPRODUCED, PARTIAL, or
FAILED, shows a side-by-side diff for anything that diverges, and pauses for
your approval before publishing a public GitHub issue with the report.

**Agent flow:**

1. Read the repo via the GitHub MCP connector. Enumerate each figure or table.
2. Fan out one subagent per figure. Each runs the analysis in the sandbox,
   computes a classification with evidence, and returns only the result.
3. Render a Generative UI scorecard with per-figure status and aggregate counts.
4. Ask whether to post the report as a public GitHub issue.
5. Pause for your approval before calling `create_issue`. No public,
   attributed claim goes out without a human saying yes.

## Quickstart

**Prerequisites:** Node.js 22.14+, a Daytona API key, a GitHub PAT with
`repo:read` + `issues:write`.

**Setup:**

1. Clone this repo and open a terminal in it.
2. Start TrueForge (local mode, SQLite, no other infra):
   ```bash
   npx @truefoundry/trueforge@latest
   ```
   Open http://localhost:8790.
3. Connect a model. Settings → Models, pick a provider (OpenAI, Anthropic,
   Gemini, DeepSeek, or any OpenAI-compatible endpoint), paste your key.
   Set the model name in `agent.json` (`model.name`).
4. Connect the sandbox. Settings → Sandbox providers → Daytona, paste your
   key. Permissions needed: write + delete snapshots, write sandboxes.
5. Connect GitHub. Settings → Connectors → add `github` MCP, authenticate
   with your PAT.
6. Register the skill. Settings → Skills → Import from GitHub, point at
   this repo, path `skills/reproduction-review-playbook`, ref `main`.
7. Create the agent. Paste `agent.json` into the agent builder (or
   `POST /api/v1/agents`), save as `retrohost`.

Keys go in TrueForge Settings. Never in the repo.

## Usage

Open a chat with the `retrohost` agent:

```
Reproduce the figures in <owner>/<repo>
```

Try it against the seeded fixtures:

```
Reproduce the figures in <owner>/reproducible-paper
Reproduce the figures in <owner>/divergent-paper
```

## Validated results

**Seed fixtures** (CI-validated):

| Fixture | Result | Why |
|---------|--------|-----|
| `reproducible-paper` | REPRODUCED | Analysis output matches claimed (8.5, 9.5, 10.5) |
| `divergent-paper` | FAILED | Claimed has stale sums (51, 57, 63); script computes means |

**Real-paper demo** (`reproducibility-sec/reproducibility`, a published
reproducibility study of ML papers in security conferences):

- 8 parallel subagents, one per figure (Figs 2-9).
- Ran `figure.py` in the sandbox with code-computed evidence (aspect ratio,
  pixel-MAD, color-palette diffs).
- **6 REPRODUCED** (Figs 3, 4, 6, 7, 8, 9), **2 PARTIAL** (Figs 2, 5),
  **0 FAILED**.
- Handled real heterogeneity: 2021-era pinned deps that don't install on
  Python 3.13; used the modern stack and noted the caveat honestly.
- Approval gate fired. Issue creation attempted; GitHub MCP backend was
  transiently down, so the agent saved the ready-to-post issue rather than
  fabricating success.

## Development

```bash
pip install -r requirements-dev.txt
python -m pytest tests/ -v
```

The test suite (`tests/test_fixtures.py`) validates both seed fixtures,
the numeric tolerance policy (rtol=1e-4, atol=1e-6), and input data
structure.

CI runs on every push and PR to `main` (`.github/workflows/ci.yml`). It
installs Python 3.12, runs each fixture's `analysis.py`, and asserts the
reproducible one matches its claimed output while the divergent one doesn't.

## Repository layout

| Path | What it is |
|------|-----------|
| `agent.json` | TrueForge agent manifest (model, instructions, MCP, config) |
| `skills/reproduction-review-playbook/` | Reproduction checklist skill (SKILL.md + tolerance policy) |
| `examples/reproducible-paper/` | Seed fixture that reproduces cleanly |
| `examples/divergent-paper/` | Seed fixture with a stale claimed artifact |
| `examples/gate-mcp/` | Minimal MCP server for approval-gate testing |
| `tests/test_fixtures.py` | Pytest suite for fixtures, tolerance, and input validation |
| `.github/workflows/ci.yml` | CI: validates both fixtures against their expected outcomes |
| `docs/` | Write-up and demo script |

## Scope

Retrohost reproduces **Python-based** paper code. Non-Python runtimes
(R, notebooks, shell, MATLAB) classify as FAILED with the reason recorded
(e.g. `non-Python runtime: R`). Papers without public code or data are
out of scope.

## Acknowledgements

Built during the WeMakeDevs Agent Harness Hackathon (August 24-30, 2026).
See `AGENTS.md` for the AI coding assistance disclosure.
