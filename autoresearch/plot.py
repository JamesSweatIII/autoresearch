"""Plot the autoresearch progress curve for the relevance model."""

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
EXP_LOG = HERE / "experiments.jsonl"
OUT = HERE / "results" / "running_best.png"
TARGET = 0.85


def main():
    if not EXP_LOG.exists():
        print("No experiments yet. Run train_relevance.py first.")
        return
    accs = []
    with open(EXP_LOG) as f:
        for line in f:
            line = line.strip()
            if line:
                accs.append(json.loads(line)["test_acc"])
    if not accs:
        print("No experiments logged.")
        return

    xs = list(range(len(accs)))
    running, best, best_idx = [], -1.0, []
    for i, a in enumerate(accs):
        if a > best:
            best = a
            best_idx.append(i)
        running.append(best)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    plt.figure(figsize=(10, 6))
    plt.scatter(xs, accs, s=28, c="#9aa0a6", label="Experiment", zorder=2)
    plt.scatter(best_idx, [accs[i] for i in best_idx], s=60, c="#34a853",
                label="New best (kept)", zorder=4)
    plt.plot(xs, running, c="#34a853", lw=2, label="Running best", zorder=3)
    plt.axhline(TARGET, ls="--", c="#ea4335", label=f"Ready gate ({TARGET})", zorder=1)
    plt.xlabel("Experiment #")
    plt.ylabel("Held-out relevance accuracy")
    plt.title(f"Autoresearch: relevance model | {len(accs)} experiments | best={max(accs):.4f}")
    plt.legend(loc="lower right")
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(OUT, dpi=140)
    print(f"Saved {OUT}  (best={max(accs):.4f})")


if __name__ == "__main__":
    main()
