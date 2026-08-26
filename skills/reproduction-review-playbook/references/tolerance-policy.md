# Tolerance Policy

This file defines exactly how to compare a reproduced output against a paper's
claimed result. It is the numeric and structural ground truth for the
REPRODUCED / PARTIAL / FAILED classification.

## Numeric comparison

### Floats
Compare with `numpy.isclose` semantics:
- `rtol = 1e-4` (relative tolerance)
- `atol = 1e-6` (absolute tolerance)

Two floats `a` and `b` match when:

```
abs(a - b) <= atol + rtol * abs(b)
```

### Integers
Exact equality. No tolerance.

### Strings
Exact equality (byte-for-byte after stripping trailing whitespace).

### Arrays / tables
Element-wise comparison using the rules above. A table reproduces when every
cell matches within tolerance and the shape (rows × columns) is identical.

## Structural figure comparison

A figure is structurally equivalent when all of the following match:

- **Dimensions**: same width × height (in pixels or inches).
- **Labels**: same axis labels, title, and legend entries.
- **Series**: same number of plotted series/lines/bars, in the same order.
- **Axes**: same scale (linear/log) and same axis ranges within tolerance.

A figure that renders but differs in any of these is PARTIAL (not REPRODUCED).

## Reporting a diff

When a result does not reproduce, report:

- The expected value and the actual value.
- The absolute and relative error.
- For figures: which structural property differs (shape / labels / series / axes).
- The exact command that produced the actual result.

## Timeout

The default per-script timeout is 120 seconds. A script that exceeds it is
FAILED with reason `timeout`.

## Stability comparison (v2)

Run-to-run comparison uses the identical numeric and structural rules as
claimed-vs-reproduced (same rtol/atol, same structural checks). Outcomes:

- **stable**: all run1 vs run2 comparisons match within tolerance.
- **varies between runs (nondeterministic)**: any run1 vs run2 comparison
  mismatches.
- **not checked**: first-run wall time exceeded 30 seconds, so no second
  run was attempted.

Instability never upgrades or downgrades a classification by itself. It is
recorded as evidence alongside the claimed-vs-reproduced verdict.
