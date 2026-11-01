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

### 0. Version check — DONE, and it changed the plan

Run on 2026-11-01: the alias `jev-latest` now resolves to **`jev-1.14.0`**. Every number in
the paper was collected against **`jev-1.13.0`**.

This matters more than it looks. Had the arms below been collected through the alias, they
would have run against 1.14.0 and been compared against 1.13.0 data already on disk —
silently confounding dataset with model version. The rotation result on WMDP-Chem would not
have been comparable to the one on WMDP-Cyber.

The endpoint accepts a concrete version in the same `model` field, verified both ways:

```
request jev-1.13.0 -> served jev-1.13.0    PINNED OK
request jev-1.14.0 -> served jev-1.14.0    PINNED OK
```

So `jev_client.MODEL` now defaults to `jev-1.13.0`, the published version, instead of the
floating alias. `run_eval.py` and `run_circular.py` take `--model-version`, and both print
the version they are using before the first call. Every arm below is therefore collected
against the same model as the existing data.

**This is also a finding for the paper.** A hosted model moved under a published
evaluation inside six weeks, with no change to the identifier the original runs used. Any
result collected through a floating alias is not reproducible, and the paper's
reproducibility limitation should say so and name the fix: pin the version.

**And it is a partial answer to reviewer 11B's point 1.** Re-running a sample against
1.14.0 gives a genuine second system — the same product after a vendor update — and tests
whether the order-instability finding survives it. See arm 5.

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

### 5. Cross-version replication on jev-1.14.0 — about 13,000 calls

New, and only possible because the version moved. Repeats the two arms the order finding
rests on, against the updated model, writing to separate files so nothing already collected
is touched:

```sh
python3 run_circular.py cyber bio --model-version jev-1.14.0 --out-prefix perm114
python3 run_eval.py cyber bio --model-version jev-1.14.0 --tag v114
```

This answers a question we could not otherwise ask: is the 30.6% steerable fraction a
property of one frozen snapshot, or does it survive a vendor update? Either answer is worth
reporting. If the instability persists, the finding is about the architecture rather than
one build; if it disappears, that is a concrete demonstration that these properties move
under the user's feet without notice, which is itself the reproducibility argument.

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
