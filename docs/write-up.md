# Retrohost — Submission Write-up

## What it does

Retrohost is a **paper-reproduction auditor** built on TrueForge. You give it
the public GitHub repo behind a published scientific paper; it re-runs each
figure's analysis in an isolated sandbox, scores which figures reproduce and
which don't, shows the divergent figure's diff, and pauses for your approval
before publishing a reproduction report as a public GitHub issue.

The job is real and consequential: reproducibility is a genuine crisis in
science, and publicly claiming a paper doesn't reproduce is a one-way door for
reputation. That's exactly the kind of high-stakes, irreversible action an agent
harness should gate behind a human.

## How it uses TrueForge

Every harness feature is load-bearing, not bolted on:

- **MCP tools (GitHub connector)** — reads the paper's repo (structure, code,
  data, claimed results) and creates the public issue.
- **Sandbox** — the paper's **untrusted** code runs isolated in a Daytona
  sandbox where credentials never enter. This is the safety boundary for running
  someone else's code.
- **Code Mode** — each subagent writes a Python script in the sandbox that
  clones the repo, runs the analysis, and computes the reproduction
  classification in code (not guessed from prose).
- **Subagents** — one subagent per figure/table, run in parallel, each with a
  clean context; only the classification + evidence returns to the root agent.
- **Skills** — a git-backed `reproduction-review-playbook` SKILL.md defines what
  "reproduces" means (numeric tolerance, structural equivalence, failure modes).
- **Generative UI** — a scorecard renders per-figure status, counts, and the
  side-by-side diff of any divergent figure.
- **Clarifying questions** — the agent asks "post as a public issue, or hold?"
  before acting.
- **Human approval gate** — creating the issue is a `@write` tool; the harness
  pauses for Allow/Deny before the public, attributed claim is posted.
- **Session persistence** — the review survives a browser refresh / reconnect.

## Honest scope

Retrohost reproduces **Python-based** paper code. R / notebook / shell / MATLAB
papers classify as FAILED with the reason recorded (e.g. `non-Python runtime:
R`). It does not reproduce papers without public code or data.

## What broke along the way

- The GitHub MCP connector's `create_issue` tool must be annotated `@write` for
  the approval gate to fire; we gate by literal tool name as belt-and-suspenders.
- The sandbox must have the paper's runtime installed; we constrain the scope to
  Python and classify non-Python as FAILED-with-reason rather than faking a pass.
- The "irreversible" framing had to be honest: a GitHub issue can be deleted, so
  the stakes are "public + attributed + reputationally consequential," not
  "undeletable."
- The Ox Alpha model on the Zen endpoint failed on tool calls (a documented
  upstream bug), so we switched to `stealth/ox-alpha` on the Nous Research
  endpoint, which handles tools correctly.

## Validated end-to-end

The full flow was run live on TrueForge against the seeded fixtures:

- `examples/reproducible-paper` → **REPRODUCED** (3/3 rows match within
  `rtol=1e-4, atol=1e-6`).
- `examples/divergent-paper` → **FAILED** — the agent produced a side-by-side
  diff (claimed 51/57/63 vs reproduced 8.5/9.5/10.5), diagnosed the stale
  claimed artifact, computed aggregate counts in Python, and rendered a
  Generative UI scorecard.
- The agent asked a clarifying question ("post as a public issue, or hold?"),
  then **paused for human approval** before calling `create_issue`. On approval,
  it created **GitHub issue #1** on the repo — the control-and-safety gate
  working end-to-end on a real write.

### Real-paper validation

Beyond the synthetic fixtures, Retrohost was run against a **real published
paper** — *"Get in Researchers; We're Measuring Reproducibility"* (a
reproducibility study of ML papers in security conferences,
`reproducibility-sec/reproducibility`). The agent:

- Extracted the author-run figure images (Figures 2–9) from the paper's Jupyter
  notebook, since the repo ships no pre-made PDFs.
- Handled real heterogeneity: the repo pins 2021-era dependencies (numpy 1.19.5,
  pandas 1.2.0) that can't install on Python 3.13, so it used the modern stack
  and noted the caveat honestly.
- Spawned **8 parallel subagents** (one per figure), each running `figure.py` in
  the sandbox and classifying with code-computed evidence (aspect ratio,
  pixel-MAD, color-palette diffs).
- Produced the final report: **6 REPRODUCED** (Figs 3, 4, 6, 7, 8, 9), **2
  PARTIAL** (Figs 2, 5), **0 FAILED**.
- When the GitHub MCP backend was transiently down, it **honestly saved the
  ready-to-post issue rather than fabricating success** — exactly the
  "never fabricate a result" rule.

## Repo layout

- `agent.json` — the TrueForge agent definition.
- `skills/reproduction-review-playbook/` — the reproduction checklist skill.
- `examples/reproducible-paper/` and `examples/divergent-paper/` — seeded test
  fixtures (one reproduces, one has a stale committed result).
- `docs/demo-script.md` — the ~3-minute demo.

## Qodo Review Trail

For the Best Code Quality track, all post-scaffold work flowed through
Qodo-reviewed pull requests. Every PR was real, reviewable work; Qodo's
findings were addressed before merge. No review trail was fabricated.

| PR | Work | Qodo findings | Outcome |
|----|------|---------------|---------|
| #2 | CI workflow + requirements.txt | 2 (lockfile/manifest mismatch, MCP session leak) | Fixed, re-reviewed clean, merged |
| #3 | pytest suite (25 tests) | 3 (tolerance-policy bypass, session leak, lockfile) | Fixed, re-reviewed clean, merged |
| #4 | CONTRIBUTING.md | 0 | Merged |
| #5 | README overhaul | 0 | Merged |
| #6 | `--json` output mode | 0 | Merged |
| #7 | Makefile | 2 (clean-checkout test failure, python/python3) | Fixed, re-reviewed clean, merged |

6 PRs merged, 7 Qodo findings, all addressed with follow-up commits and
re-reviewed clean. The trail is visible at
https://github.com/SameerGoyal125/agentic-ai/pulls.
