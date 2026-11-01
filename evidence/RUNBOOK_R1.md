# Runbook — revision data collection

Four new arms on the audited model, answering reviewer 11B's point 4 (robustness beyond
four rotations of four-option items). Everything here is implemented, tested and committed;
what is missing is the data.

**Prerequisites**

```sh
export TYPESAFE_API_KEY=...          # not set in the current shell
cd /Users/kap4722/wmdp_jev/evidence/code
```

The benchmark parquet files must be back in `data/` for arm 4 only (it reads source items).
Arms 1-3 read questions from `evidence/raw/*.jsonl`, so they need no parquet and are
guaranteed to use byte-identical prompts to the original runs.

**Total: about 43,000 calls, roughly $1.30, 3-5 days wall clock.** Cost is not the
constraint; the original 19,060 calls took two days, so start these early and write while
they run.

---

## Order to run them in

### 0. Version check — one call, do this first

```sh
python3 run_eval.py bio --tag versioncheck
```

Then read `model_version` out of `raw/bio_versioncheck_manifest.json`. The original runs all
resolved to `jev-1.13.0`. **If it now resolves to something newer, stop and tell me** — a
re-run on a sample would give a second system to compare against in the only sense available
to us, which is the one thing reviewer 11B asked for that we currently cannot answer. It
also makes "hosted models change under evaluation" a reportable finding in its own right.

Delete the file afterwards if the version is unchanged; it is a probe, not an arm.

### 1. Rotations on the two WMDP suites that lack them — 4,876 calls

```sh
python3 run_circular.py chem bio-robust
```

Writes `raw/perm_chem.json`, `raw/perm_bio-robust.json`. Extends the order result from two
of the four WMDP suites to all four. WMDP-Bio-Robust is the interesting one: it is the
paraphrase-robust set, so this tests whether being robust to reworded questions buys any
robustness to reordered options.

### 2. Rotations on the biology tasks — about 5,300 calls

```sh
python3 run_circular.py labbench-db labbench-seq labbench-litqa2 --max-rotations 4
```

This is the arm that most directly answers the reviewer. LB-LitQA2 and LB-SeqQA carry 2 to
10 options, so it takes the measurement off four-option multiple choice entirely.
`--max-rotations 4` caps the cost on the wide items; without it a 10-option item would get
10 calls.

### 3. Reversed order, every dataset — 6,020 calls

```sh
python3 run_eval.py bio bio-robust chem cyber labbench-cloning labbench-protocol \
        labbench-seq labbench-db labbench-litqa2 labbench-supp \
        --order-mode reversed --tag rev
```

One call per item, the cheapest ordering outside the rotation family, and it covers all ten
datasets including the wide ones. Results are recorded against original option indices, so
each record lines up with its baseline item for item.

### 4. All 24 orderings, seeded sample — 24,000 calls, run last

```sh
python3 run_circular.py cyber bio --all-permutations --sample 500
```

Writes `raw/permall_cyber.json`, `raw/permall_bio.json` — a separate filename, so the
existing `perm_*.json` are untouched and current results cannot shift under us.

This is the one that removes a hedge. Rotations are 4 of the 24 orderings and they never
change which option follows which, so they cannot see adjacency effects. This measures how
much the 37.4% figure under-counts. **Either outcome is publishable:** more instability
strengthens the finding; the same or less means rotations already capture it and the
"lower bound" caveat can simply be dropped.

---

## After the data lands

```sh
cd ../../manuscript && make evidence && make
```

`analyze.py` discovers datasets by looking for `perm_<key>.json` on disk, so arms 1 and 2
are picked up with no code change — the new datasets flow into blocks A5, A6, A11 and A13
automatically. Arms 3 and 4 need a short analysis block each, which I will write once the
files exist; I did not want to write an analysis against data whose shape I had not seen.

`make` will fail if the paper cites a number the pipeline did not produce, so nothing can be
quoted that the data does not support.

---

## What changed in the collection code

| File | Change |
|---|---|
| `run_circular.py` | rotations generalised to arbitrary orderings; `--all-permutations`, `--perm-width`, `--sample` added. Cyclic output shape is unchanged. |
| `run_eval.py` | `--order-mode {original,reversed}`; results mapped back to original option indices so arms stay comparable |
| `analyze.py` | `CIRCULAR_KEYS` discovered from disk instead of hardcoded to bio and cyber |

**Backward compatibility was tested, not assumed.** `cyclic_perms(n)` reproduces the
original rotation formula exactly for n in 2, 4, 5 and 10; the inversion round-trips on
2,000 randomised cases; and re-running the full pipeline after the refactor produced a
byte-identical `stats.json`. Re-collecting the existing arms would reproduce the existing
files.

## Not being done, and why

- **A second vendor's model.** No access. Covered honestly in the limitations rather than
  substituted for.
- **All 24 orderings on LAB-Bench.** The wide items make it expensive and the subtask sample
  sizes are too small to carry the conclusion. Arm 3 covers those datasets instead.
- **Latency.** Never claimed in the paper; leaving it that way.
