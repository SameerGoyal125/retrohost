---
name: reproduction-review-playbook
description: Classify whether a paper figure/table reproduces — REPRODUCED / PARTIAL / FAILED — with evidence, using numeric tolerance and structural equivalence. Environment-aware, with stability checks and a verifier pass.
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
- Missing data, or a dependency that still cannot be imported after the environment-preparation install attempt.
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

## Environment preparation (run before first execution)

Before running the analysis script, prepare the sandbox:

1. **Import scan via Python AST.** Parse the target script with Python's `ast`
   module to extract every `import X` and `from X import ...` statement,
   including imports inside functions, classes, and conditional blocks. Then
   follow local module imports transitively: for any name that resolves to a
   `.py` file within the repo, parse that file too and collect its third-party
   imports. Stop recursion at the repo boundary.
2. **Declared dependency check.** If the repo contains `requirements.txt`,
   `environment.yml` (pip section only), or `Pipfile`, read the declared
   dependencies.
3. **Install missing modules.** For any module not already available:
   - If a manifest declares a distribution for it (e.g. `PyYAML==6.0` in
     requirements.txt), install the declared distribution with its version
     constraint. Declared constraints always win over latest-release installs.
   - Otherwise, use the import→distribution name mapping: `cv2` →
     `opencv-python`, `sklearn` → `scikit-learn`, `PIL` → `pillow`. If no
     mapping applies, install the import name as-is.
     Total environment budget: 120 seconds. Use quiet mode (`pip install -q`).
4. **Re-probe every import.** After installation, re-attempt every import from
   step 1. If an import still fails, record it.
5. **Only classify FAILED for a dependency if the import still fails after the
   install attempt.** Reason format:
   `missing dependency: <name> (install attempted, failed: <short error>)`.
6. **Record an environment report:** declared deps found, modules installed
   (with versions), and anything still missing.
7. **Runtime safety net.** If an `ImportError` or `ModuleNotFoundError` escapes
   during the script's execution, parse the missing module name from the error
   message, make ONE bounded pip install attempt for it, and re-run the script
   once. Only after this second attempt may the verdict be
   FAILED-for-dependency.

## Stability check

- If the first run's wall time is ≤ 30 seconds, run the script a second time
  on fresh outputs.
- Compare run1 vs run2 outputs using the same tolerance policy. Label the
  result `stable` (all match) or `varies between runs (nondeterministic)`
  (any mismatch).
- If the second run raises an exception or times out, this does NOT change the
  classification. Record `stability: second run failed (<short reason>)` as
  annotation; the first run remains the sole basis for claimed-vs-reproduced
  classification.
- If the first run took > 30 seconds, label `not checked (runtime > 30s)`.
- Classification is ALWAYS claimed-vs-reproduced; stability is annotation
  only. A REPRODUCED verdict on varying output must carry the variance note.

## Procedure
1. Clone the repo at the given ref into the sandbox.
2. Environment preparation (see above): scan imports, check declared deps,
   install missing modules, re-probe, record environment report.
3. Run the analysis script (Python) with the given args; capture stdout, stderr,
   exit code, and wall time.
4. Stability check (see above): if first run ≤ 30s, run again and compare.
5. Read the expected output path (the paper's claimed result).
6. Compare per `references/tolerance-policy.md`.
7. Classify REPRODUCED / PARTIAL / FAILED and return the classification plus
   the evidence (command, exit code, wall time, diff, environment report,
   stability label).
