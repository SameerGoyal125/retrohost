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

## Repo layout

- `agent.json` — the TrueForge agent definition.
- `skills/reproduction-review-playbook/` — the reproduction checklist skill.
- `examples/reproducible-paper/` and `examples/divergent-paper/` — seeded test
  fixtures (one reproduces, one has a stale committed result).
- `docs/demo-script.md` — the ~3-minute demo.
