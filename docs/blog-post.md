# Retrohost: I built an agent that audits whether scientific papers actually reproduce

*Built for the WeMakeDevs Agent Harness Hackathon (Aug 24–30, 2026) on TrueForge.*

## The job I gave the agent

Reproducibility is a real crisis in science. A paper gets published, its code
goes up on GitHub, and nobody ever checks whether the figures actually come from
that code. So I built **Retrohost** — an agent that reads the public repo behind
a paper, re-runs each figure's analysis in an isolated sandbox, scores which
figures reproduce and which don't, and pauses for a human before publishing a
reproduction report as a public GitHub issue.

The job is high-stakes on purpose: publicly claiming a paper doesn't reproduce
is a one-way door for reputation. That's exactly the kind of irreversible action
an agent harness should gate behind a person.

## How I wired it up

Retrohost runs on **TrueForge**, an open-source agent harness. The harness does
the machinery; I wrote the agent definition and the playbook.

- **GitHub MCP connector** — the agent reads the paper's repo (code, data,
  claimed results) and creates the public issue.
- **Sandbox** — the paper's *untrusted* code runs isolated in a Daytona sandbox
  where credentials never enter. That's the safety boundary for running someone
  else's code.
- **Code Mode** — each subagent writes a Python script that clones the repo,
  runs the analysis, and computes the reproduction classification in code, not
  guessed from prose.
- **Subagents** — one per figure, run in parallel, each with a clean context.
- **Skills** — a git-backed `reproduction-review-playbook` SKILL.md defines what
  "reproduces" means (numeric tolerance, structural equivalence, failure modes).
- **Generative UI** — a scorecard renders per-figure status and the side-by-side
  diff of any divergent figure.
- **Clarifying questions** — the agent asks "post as a public issue, or hold?"
  before acting.
- **Human approval gate** — creating the issue is a write tool; the harness
  pauses for Allow/Deny before the public claim is posted.
- **Session persistence** — the review survives a browser refresh.

## What TrueForge handled for me

Everything that makes an agent safe and reliable: the tool routing, the sandbox
provisioning, the approval pause, the subagent fan-out, the session state. I
wrote one `agent.json` and a playbook; the harness did the rest.

## What broke along the way

- The GitHub MCP connector's `create_issue` tool has to be annotated `@write`
  for the approval gate to fire — I gate by literal tool name as belt-and-
  suspenders.
- The sandbox has to have the paper's runtime installed. I scoped Retrohost to
  Python-based code and classify non-Python papers as FAILED-with-reason rather
  than faking a pass.
- The "irreversible" framing had to be honest: a GitHub issue can be deleted, so
  the stakes are "public + attributed + reputationally consequential," not
  "undeletable."

## The demo

Three minutes: the agent reads a divergent paper's repo, fans out a subagent,
shows the scorecard with the divergent figure's diff, asks whether to post, and
pauses for my approval before creating the public issue. Then I refresh the
browser and the session is still there.

## It actually worked

I ran the full flow live on TrueForge. The agent classified the reproducible
fixture as **REPRODUCED** and the divergent one as **FAILED** (with a side-by-side
diff and a correct root-cause diagnosis of the stale claimed artifact). It asked
whether to post, then **paused for my approval** before calling `create_issue` —
and on approval it created **GitHub issue #1** on the repo. The control-and-safety
gate worked end-to-end on a real write.

## Then I pointed it at a real paper

To prove it wasn't just the synthetic fixtures, I ran Retrohost against a **real
published paper** — *"Get in Researchers; We're Measuring Reproducibility"*, a
reproducibility study of ML papers in security conferences. The agent extracted
the author-run figures from the paper's notebook, handled the fact that the repo
pins 2021-era dependencies that can't install on modern Python, spawned **8
parallel subagents** (one per figure), and classified each with code-computed
evidence. Final report: **6 REPRODUCED, 2 PARTIAL, 0 FAILED**. When the GitHub
backend was briefly down, it honestly saved the ready-to-post issue rather than
faking success.

*Retrohost reproduces Python-based paper code. R / notebook / shell papers
classify as FAILED with the reason recorded.*
