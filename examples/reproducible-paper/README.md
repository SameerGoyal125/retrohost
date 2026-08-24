# Reproducible Paper

A minimal synthetic "paper" that reproduces cleanly. Used as a test fixture for
the Retrohost reproduction auditor.

## Claim

**Table 1** reports the mean of each numeric column in `data/input.csv`.

The claimed result is committed in `results/claimed.csv`:

| metric | value |
| --- | --- |
| mean_x | 8.5 |
| mean_y | 9.5 |
| mean_z | 10.5 |

## Reproduce

```bash
python3 analysis.py
```

This reads `data/input.csv`, computes the column means, and writes its actual
output to `results/table.csv` (and `results/figure.png` if matplotlib is
available). Compare `results/table.csv` against the claimed result in
`results/claimed.csv`.

## Expected classification

REPRODUCED — re-running `analysis.py` produces `results/table.csv` identical to
the claimed result in `results/claimed.csv`.
