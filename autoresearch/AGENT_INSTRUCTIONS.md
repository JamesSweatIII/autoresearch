# Autoresearch loop — instructions for the AI coding agent (OpenCode)

You are an autonomous ML research agent. Goal: **raise the held-out relevance
accuracy reported by `train_relevance.py` to ≥ 0.90** through many small,
evaluated, version-controlled experiments.

Run from the `autoresearch/` directory.

## One-time setup
```bash
python build_dataset.py        # freezes data/relevance_dataset.jsonl
python train_relevance.py      # baseline ACCURACY:
```

## The loop (repeat until accuracy ≥ 0.90, then stop)
1. **Propose ONE change.** Edit the `CONFIG` block in `train_relevance.py`
   (or the model in `model.py`). One thing at a time.
2. **Train + evaluate.** `python train_relevance.py` → read the `ACCURACY:` line.
   (Each run auto-appends to `experiments.jsonl`; never edit that file.)
3. **Keep or discard.**
   - Improved over the best so far → `git add -A && git commit -m "keep: <change> -> acc <x>"`
   - Did not improve → `git checkout -- train_relevance.py model.py`
4. **Log** one line to `notes.txt`: change, old→new accuracy, KEPT/REVERTED, why.
5. If `python train_relevance.py` errors or prints no `ACCURACY:` line, treat it
   as failed: `git checkout -- train_relevance.py model.py` and try something else.

## Knobs with headroom
- `epochs`, `lr`, `weight_decay`
- add `hidden_dim` (16–128) to make it an MLP; tune `dropout`
- `batch_size`, `threshold`
- `model.py`: deeper/wider net, BatchNorm, different activation

## When done
```bash
python plot.py     # -> results/running_best.png
```
Report: baseline accuracy, final best, total experiments, the 3 changes that
helped most. The app gates user interaction on accuracy ≥ 0.90 (model_meta.json).
```
