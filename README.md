# Retrohost

A paper-reproduction auditor agent on TrueForge.

## Prerequisites

- Node.js 22.14+
- A Daytona API key
- A GitHub Personal Access Token (PAT)

## Setup

1. **Clone this repo** and open a terminal in it.
2. **Start TrueForge** (local mode, SQLite — no other infra):
   ```bash
   npx @truefoundry/trueforge@latest
   ```
   Open http://localhost:8790.
3. **Connect a model** — Settings → Models → pick a provider (OpenAI / Anthropic / Gemini / DeepSeek / any OpenAI-compatible endpoint) and paste your API key. The agent references the model by name; set it in `agent.json` (`model.name`, e.g. `anthropic/claude-sonnet-4-6`).
4. **Connect the sandbox** — Settings → Sandbox providers → Daytona → paste your Daytona API key (permissions: write + delete snapshots, write sandboxes). This is the only sandbox provider TrueForge supports; it runs the paper's untrusted code in isolation.
5. **Connect GitHub** — Settings → Connectors → add the `github` MCP server → authenticate with a fine-grained PAT that has `repo:read` + `issues:write` on the repos you scan and post to.
6. **Register the skill** — Settings → Skills → Import from GitHub → point at this repo, path `skills/reproduction-review-playbook`, ref `main`.
7. **Create the agent** — paste `agent.json` into the agent builder (or `POST /api/v1/agents` with the manifest), then save it as `retrohost`.

**Keys go in TrueForge Settings — never in the repo, never committed.**

## Usage

Open a chat with the `retrohost` agent and give it a paper repo:

```
Reproduce the figures in <owner>/<repo>
```

The agent will:
1. Read the repo via the GitHub MCP connector and enumerate each figure/table.
2. Fan out one subagent per figure; each runs the analysis in the sandbox via Code Mode and classifies REPRODUCED / PARTIAL / FAILED with evidence.
3. Render a Generative UI scorecard with the side-by-side diff of any divergent figure.
4. Ask whether to post the reproduction report as a public GitHub issue.
5. If you choose to post, **pause for your approval** before creating the issue (a public, attributed, reputationally consequential claim).

Try it against the seeded fixtures:
```
Reproduce the figures in <owner>/reproducible-paper
Reproduce the figures in <owner>/divergent-paper
```

## Scope

Retrohost reproduces Python-based paper code only. R / notebook / shell / MATLAB
papers classify as `FAILED` with the reason recorded (e.g. `non-Python runtime: R`).
It does not reproduce papers without public code or data.
