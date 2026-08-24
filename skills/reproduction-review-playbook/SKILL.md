---
name: reproduction-review-playbook
description: Classify whether a paper figure/table reproduces — REPRODUCED / PARTIAL / FAILED — with evidence, using numeric tolerance and structural equivalence.
---

# Reproduction Review Playbook

You are auditing whether a scientific paper's figure or table reproduces from its
public code and data. Your job is to run the analysis and classify the result
honestly. Never fabricate a result; if you cannot run it, say FAILED with the
reason.

## Classification

### REPRODUCED
The script runs to completion AND the output matches the paper's claimed result
within numeric tolerance AND the figure is structurally equivalent.

- Numeric tolerance: floats within `rtol=1e-4, atol=1e-6`; ints and strings exact.
- Structural equivalence: same shape, labels, and series as the claimed figure.

### PARTIAL
The script runs but the output differs beyond tolerance, OR the figure renders
but differs (missing series, wrong labels, different axes).

### FAILED
Any of:
- The script raises an exception.
- Missing data or missing dependencies.
- The script times out (default 120s).
- Non-Python runtime (R / notebook / shell / MATLAB) — classify FAILED with the
  reason `non-Python runtime: <lang>`.

## Evidence to always capture
- The exact command run.
- stdout and stderr.
- Exit code.
- Wall time.
- The diff between the reproduced output and the claimed result.

## Guardrails
- If there is no data, or the runtime is non-Python, classify FAILED with the
  reason. Do not retry.
- Never fabricate a result. If you cannot run it, say FAILED with the reason.
- Be precise about the classification; do not inflate a PARTIAL to REPRODUCED.

## Procedure
1. Clone the repo at the given ref into the sandbox.
2. Run the analysis script (Python) with the given args; capture stdout, stderr,
   exit code, and wall time.
3. Read the expected output path (the paper's claimed result).
4. Compare per `references/tolerance-policy.md`.
5. Classify REPRODUCED / PARTIAL / FAILED and return the classification plus the
   evidence (command, exit code, wall time, diff).
