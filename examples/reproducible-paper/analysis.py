#!/usr/bin/env python3
"""Compute the mean of each numeric column in data/input.csv.

Writes its actual output to results/table.csv and, if matplotlib is available,
results/figure.png. The claimed result lives in results/claimed.csv.
"""
import csv
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
INPUT = os.path.join(HERE, "data", "input.csv")
OUTPUT = os.path.join(HERE, "results", "table.csv")
FIGURE = os.path.join(HERE, "results", "figure.png")


def read_input(path):
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    columns = reader.fieldnames
    return rows, columns


def column_means(rows, columns):
    means = {}
    for col in columns:
        values = [float(r[col]) for r in rows]
        means[col] = sum(values) / len(values)
    return means


def write_table(means, path):
    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["metric", "mean"])
        for col, mean in means.items():
            writer.writerow([f"mean_{col}", f"{mean:.1f}"])


def write_figure(means, path):
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        return  # figure is optional; table is the classification target
    labels = list(means.keys())
    values = list(means.values())
    plt.bar(labels, values)
    plt.title("Column means")
    plt.savefig(path)
    plt.close()


def main():
    rows, columns = read_input(INPUT)
    means = column_means(rows, columns)
    if "--json" in sys.argv:
        out = {f"mean_{col}": means[col] for col in columns}
        print(json.dumps(out))
    else:
        write_table(means, OUTPUT)
        write_figure(means, FIGURE)
        print("wrote", OUTPUT)


if __name__ == "__main__":
    main()
