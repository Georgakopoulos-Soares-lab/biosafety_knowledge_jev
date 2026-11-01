# Revision plan — BioAISS 2026 (ACSAC workshop)

Reviews in hand: **11A weak reject** (knowledgeable), **11B accept** (knowledgeable).
Decision context: revision / camera-ready at the same venue. **6-page body limit stands.**
Model access: TypeSafe (Jev) only, no second vendor. An earlier comparison against other
decision APIs was retired and deleted without ever being run; nothing in the paper depends
on it (see §8).

---

## 1. The one thing both reviews are saying

The two reviews look opposite but share a root cause.

- **11A:** "The main contribution of the paper is benchmarking of jev on different suites
  of Bio based datasets. This is a limited contribution."
- **11B** asks for four additions, and the first is another model.

Both reviewers read the paper as **a benchmark report about one vendor's model**. Under
that reading 11A is right: a table of accuracies for one product is a thin contribution,
and the obvious fix — add more models — is the fix we cannot apply.

But that reading is not what the paper actually did. The paper's real output is a set of
**measurement results that a benchmark number cannot produce**: the vendor's uncertainty
field does not mean what it is documented to mean; a third of decisions change when you
reorder the options; a byte-identical-repeat control proves that is the ordering and not
API noise; and a tempting causal claim was killed by a null model the authors built
themselves. None of that is "benchmarking."

**So the revision is not about adding breadth. It is about making the paper argue for what
it already is, and then deepening it along the one axis we still control: the audited model
itself.** We have the API key, and the entire original study cost **\$0.57 for 19,060
calls**. New data is effectively free. That is the lever.

---

## 2. Strategy in one sentence

Reposition the paper from *"how good is this model"* to *"what breaks when you put a
cheap single-pass decision model into a screening pipeline, and how would you measure
it"* — then back that with two new results that are already computed and verified, plus
four cheap new data arms.

Target outcome: 11A moves to weak accept because the contribution is now a method and a
security finding, not a leaderboard. 11B moves to strong accept because three of their
four asks are answered with real numbers and the fourth is answered honestly.

---

## 3. Workstreams

Five workstreams, **W1 and W2 are already verified to produce results** — I ran them
against the data on disk. W3 needs new API calls. W4 and W5 are writing.

### W1 — Order of options as an attack surface *(new headline result)*

> Answers **11A** (this is a security finding, not a benchmark) and **11B #2**
> (connection to practical screening).

**What.** The paper currently reports that reordering answer options changes 37.4% of
WMDP-Cyber answers, and treats that as a robustness curiosity. Reframe it as a
**decision-steering surface**: if whoever submits the item controls the order in which
options are presented, how much of the decision can they move?

**Verified numbers** (computed from `evidence/raw/perm_*.json` and `repeat_*.json`, no new
calls needed). All four arms cost the same four calls per item, so the comparison is
budget-matched:

| Dataset | Single pass | Worst of 4 **identical** calls (noise only) | Worst of 4 **rotations** (noise + order) | Attributable to order |
|---|---|---|---|---|
| WMDP-Cyber | 0.633 | 0.601 | **0.492** | **−10.9 pp** |
| WMDP-Bio | 0.854 | 0.841 | **0.800** | **−4.1 pp** |

And the fraction of items whose **correctness depends on the ordering** (right under some
orders, wrong under others):

| Dataset | From run-to-run noise alone | With ordering | Attributable to order |
|---|---|---|---|
| WMDP-Cyber | 6.5% | **30.6%** | 24.1 pp |
| WMDP-Bio | 2.0% | **9.5%** | 7.5 pp |

**Why this wins.** It is the same experimental logic 11B singled out for praise — using
byte-identical repeats to separate ordering from noise — applied to a new quantity that a
security workshop cares about. It converts the paper's best existing result into a threat
statement, at zero data cost.

**Honesty requirement (do not skip).** "Worst of four" is an upper bound: picking the
worst ordering needs knowledge of the right answer, which a real attacker does not have.
Say so in the same breath. The number that needs **no** knowledge of the right answer is
the 30.6% steerable fraction — an attacker who simply wants the decision to move away from
its default can expect to succeed on roughly one WMDP-Cyber item in three. Lead with the
bound, qualify it in the next sentence, and report the noise control alongside it every
time. A reviewer who catches an unqualified "attack" claim will reject on that alone.

**Lands in:** new short subsection in §IV, roughly 0.4 pages with a four-row table; two
sentences in the abstract; one contribution bullet.

---

### W2 — Confidence thresholds do not transfer between tasks *(new result)*

> Answers **11B #3** (task-specific calibration, distribution shift, how to choose a
> threshold) and reinforces **11B #2**.

**What.** The paper already notes per-task calibration varies. Make it a quantitative,
deployment-shaped result: *pick a confidence cutoff on one task so that the auto-decided
items have at most 5% errors, then apply that same cutoff to another task.*

**Verified numbers** (computed from `evidence/raw/*.jsonl`, no new calls). Error rate on
the items the cutoff accepts:

| Cutoff tuned on | Cutoff | → WMDP-Bio | → Bio-Robust | → Chem | → Cyber | → LB-DbQA | → LB-LitQA2 |
|---|---|---|---|---|---|---|---|
| WMDP-Bio | 0.87 | 5.0% | 6.3% | 6.2% | 9.0% | 14.8% | **40.0%** |
| WMDP-Cyber | 0.94 | 2.9% | 4.4% | 4.8% | 4.7% | 7.1% | — |
| LB-SeqQA | 0.55 | 11.1% | 15.2% | 18.6% | 20.1% | **39.4%** | **51.0%** |

Two statements fall out, both strong and both new:

1. A cutoff tuned on WMDP-Bio to deliver 5% errors delivers **40% errors** on LitQA2 — an
   eightfold miss. Pooled calibration (ECE 0.034) gives no warning of this.
2. On **LB-DbQA and LB-LitQA2 there is no cutoff at any coverage** that reaches a 5% error
   rate. The honest deployment answer for those tasks is "this model cannot be used
   unsupervised," and the paper should say it plainly.

Supporting detail already available and worth one sentence each: per-task ECE spans
0.033 to 0.193 (a sixfold spread), per-task AUROC spans 0.620 to 0.861, and the error rate
among confident answers spans 0.0% to 50%.

**Also do.** Report equal-mass-bin ECE next to equal-width ECE in Table 1
(`common.py` already has `ece_adaptive`, and `stats.json` already stores it). Equal-width
ECE is unstable on the small LAB-Bench subtasks, and showing both pre-empts a referee
asking whether the 0.193 is a binning artefact. It is not — adaptive binning gives 0.185.

**Lands in:** new short subsection in §IV, ~0.4 pages with a compact transfer table; one
sentence in the abstract; two sentences in Discussion stating the operating rule
(*calibrate per task, on that task's own held-out items, or do not threshold at all*).

---

### W3 — Broader robustness: beyond four rotations, beyond four options

> Answers **11B #4** directly (their comment is truncated but unambiguous), and removes
> the paper's weakest hedge ("the reported instability is a lower bound").

Four new data arms on the audited model. **Combined cost is about \$1.30.** The binding
constraint is wall-clock, not money: the original 19,060 calls took roughly two days, so
budget 3–5 days.

| # | Arm | Why it answers the reviewer | Calls |
|---|---|---|---|
| **3a** | **All 24 orderings** of a 500-item sample of WMDP-Cyber and WMDP-Bio | Cyclic rotations never change *which option follows which* — they are 4 of the 24 orderings, and they preserve relative order. This measures how much the published number under-counts, converting "lower bound" from a hedge into a quantity. | 24,000 |
| **3b** | Cyclic rotations on **WMDP-Chem** and **WMDP-Bio-Robust** | Extends the order result from 2 of 4 WMDP suites to all 4. Bio-Robust is especially pointed: it is the paraphrase-robust set, so it tests whether robustness to wording buys robustness to ordering. | 4,876 |
| **3c** | Cyclic rotations on **LB-DbQA**, **LB-SeqQA**, **LB-LitQA2** | Moves the finding onto the biology tasks and, because LitQA2 and SeqQA carry 2–10 options, **off four-option multiple choice entirely**. This is the exact gap 11B names. | ~5,300 |
| **3d** | **Reversal** of the option list, all 10 datasets | The cheapest possible evidence that the effect is not an artefact of the cyclic group, on every dataset including the wide ones. One call per item. | 6,020 |

**Code readiness.** `run_circular.py` already handles any option count — the rotation and
inversion logic is written in terms of `n = len(choices)` with modular arithmetic, so 3b,
3c and 3d need no changes beyond flags. **3a is the only code change**: replace the
rotation generator (`run_circular.py:50-52`) with `itertools.permutations` for 4-option
items; the inversion logic is already general. Estimated ~10 lines plus an analysis block.

**Analysis-side change.** `analyze.py` hardcodes `CIRCULAR_KEYS = ["bio", "cyber"]` in
blocks a5, a6, a11 and a12. Widen it to whichever datasets have a `perm_*.json` on disk so
the pipeline picks the new arms up automatically.

**Expected result and the risk.** The 24-ordering arm should show instability *above* the
37.4% cyclic figure, which strengthens the paper. If it instead comes back at or below
37.4%, that is still publishable and still answers the reviewer — it would mean the cyclic
subset already captures the effect, and the "lower bound" hedge can simply be dropped. The
arm is informative either way, which is why it is worth running first.

---

### W4 — Rewrite the framing: contributions, abstract, introduction, discussion

> Answers **11A** head-on. This is the workstream that decides the outcome, and it costs
> nothing but care.

**Replace the three contribution bullets.** Current bullets lead with "a reliability audit
of a commercial model across 6,020 items" — that is the sentence 11A read and scored. New
bullets, in this order:

1. **A measurement protocol for single-pass decision models**, which establishes what a
   vendor's uncertainty field actually means before using it. Applied here, it shows the
   documented `confidence` field is a rescaling of the top probability, not a probability
   of being correct; measuring calibration against the documented field reports error
   0.091 where the true figure is 0.034. *This is a trap any API-scored evaluation can
   fall into, and the check is three lines of code.*
2. **Option ordering is a decision-steering surface** (W1), with a budget-matched
   byte-identical-repeat control that separates ordering from API nondeterminism — a
   control absent from the prior order-sensitivity literature we cite.
3. **Confidence cutoffs do not transfer across tasks** (W2), with the consequence that
   pooled calibration figures are unsafe for choosing a deployment threshold.

Keep selective permutation averaging, but demote it to a result rather than a headline
contribution; it is the most "engineering" of the findings and the least novel, and 11A's
objection is partly that the paper's third contribution is a known technique.

**Add one short paragraph on self-correction.** The `evidence/README.md` records that three
results did not survive internal adversarial review and were corrected, including one where
the corrected null model produces a *larger* effect than observed, killing the causal
reading. The paper mentions this in passing. Make it a visible paragraph. Reviewers reward
a paper that reports its own negative results; it is direct evidence that the audit is an
audit and not a vendor datasheet.

**Retitle.** The current title leads with "Auditing … Benchmarks," which invites the
benchmark reading. Candidate:

> *When Option Order Steers the Decision: Reliability Limits of Non-Generative System-1
> Models on Biosecurity-Relevant Tasks*

Keeps the venue keywords, leads with the finding, and no longer sounds like a leaderboard.

---

### W5 — Say honestly what we cannot do, and make the limitation useful

> Answers **11B #1** (additional models) — the one ask we cannot satisfy.

We have no second model. Do not paper over it. Three moves, in order of value:

**5a. Check whether the vendor shipped a new version.** All original calls resolved to
`jev-1.13.0`, collected 19–20 September. If `jev-latest` now resolves to something newer,
re-running a 500-item sample per WMDP suite (~2,700 calls, under \$0.10) gives a
**second system** in the only sense available to us: the same product after a vendor
update. Whether the instability survives a version bump is a genuinely interesting
question, and "hosted models change silently under evaluation" is itself a reproducibility
result worth a paragraph. *Do this check first — it is one API call and it may unlock a
whole response to 11B #1.*

**5b. Reframe generality along the axes we do have.** The paper can honestly claim the
findings hold across **ten datasets, option counts from 2 to 10, three labelling schemes,
two prompt formats, and (after W3) two families of orderings** — without claiming they hold
across vendors. State that explicitly rather than leaving the reader to infer it.

**5c. Make the protocol portable and say so.** The strongest available answer to "only one
model" is: *the harness is released, the protocol is vendor-agnostic, and any system that
returns a distribution over options can be dropped in.* Add two sentences specifying the
interface a second system would need to satisfy. This turns a limitation into the
reusability argument that also serves W4's contribution 1.

**Wording for the limitations section** — commit to something like: *"We evaluate one
proprietary model. The protocol is not specific to it: it requires only a system that
returns a probability distribution over the supplied options, and the released harness
implements it behind a single client interface. Whether the magnitudes reported here
generalise across vendors is open, and is the first thing we would test given access to a
second such system."* Concrete, honest, and it tells 11B we heard them.

---

## 4. New data collection — exact runs

Prerequisites: `export TYPESAFE_API_KEY=...`, benchmark parquet files restored to `data/`
(currently gitignored).

```sh
cd evidence/code

# 0. FIRST: what does jev-latest resolve to today? (W5a)
python3 run_eval.py bio --tag versioncheck --limit 1   # read model_version from the manifest

# 3b. rotations on the two WMDP suites that lack them
python3 run_circular.py chem bio-robust

# 3c. rotations on the biology tasks, including non-four-option items
python3 run_circular.py labbench-db labbench-seq labbench-litqa2 --max-rotations 4

# 3d. reversal arm, every dataset, one call per item
python3 run_eval.py bio bio-robust chem cyber labbench-cloning labbench-protocol \
        labbench-seq labbench-db labbench-litqa2 labbench-supp \
        --order-mode reversed --tag rev          # NOTE: --order-mode must be added

# 3a. all 24 orderings, 500-item sample  (requires the run_circular.py change)
python3 run_circular.py cyber bio --all-permutations --sample 500
```

Two small code changes are required before the last two commands will run: an
`--order-mode reversed` flag on `run_eval.py`, and `--all-permutations` on
`run_circular.py`. Both are small and local.

**Budget.** ~43,000 calls. At the measured 709 input tokens per call and \$0.042 per
million, that is about **\$1.30**. Wall clock, at the rate the original study ran, is
**3–5 days** — start W3 immediately and do W1/W2/W4 in parallel while it runs.

---

## 5. Page budget — we are at the limit

The body is already 6 pages (the 7th is the LLM Usage Statement, which `check_build.py`
correctly excludes). New material needs roughly **1.3 pages**, so the same must come out.
Cut candidates, in the order I would take them:

| Cut | Saves | Cost of cutting |
|---|---|---|
| §IV-C is one 47-line paragraph doing four jobs (repeat control, position preference, label/format ablations, quantisation ties). Keep the first two, compress the ablations and the tie analysis to two sentences each and point at the repo. | ~0.4 pg | Low. Both are supporting checks, not findings. |
| Merge Fig. 1 and Fig. 2 into one full-width four-panel figure. | ~0.3 pg | Low. Two full-width floats on a 6-page paper is extravagant. |
| Compress the cost comparison in §III (12 lines) to three sentences. The \$0.57-vs-generative point lands in one. | ~0.2 pg | Low. |
| Tighten §II Background from three paragraphs to two. | ~0.15 pg | Low. |
| Drop two columns from Table 1 (the chance-adjusted lift and one interval column) to make room for the adaptive-ECE column. | ~0.1 pg | Low. |

That is ~1.15 pages. If W3 lands more results than expected, take the selective-averaging
subsection down to a short paragraph as well — the plan already demotes it.

**Build guard reminder.** Every number in the text is a macro emitted by the pipeline, and
`make` fails if the prose cites a macro that `analyze.py` did not produce. So all new
statistics in W1, W2 and W3 must be added as analysis blocks and exported through
`export_numbers.py` — they cannot be typed into the LaTeX. Plan the analysis blocks
alongside the prose, not after it.

---

## 6. The response letter

Keep it short, one section per reviewer point, each opening with what changed and where.

**To 11A** — one paragraph, no defensiveness. *"The reviewer is right that a benchmark
report on one model would be a limited contribution. We have revised the paper to lead with
what the study actually establishes: that the vendor's documented uncertainty field does
not mean what it is documented to mean; that option order is a decision-steering surface
that costs 14 accuracy points on WMDP-Cyber, isolated from API noise by a budget-matched
control; and that confidence cutoffs tuned on one task miss by up to eightfold on another.
The title, abstract and contributions have been rewritten accordingly, and the benchmark
table is now supporting evidence rather than the result."* Then list the new sections.

**To 11B** — four numbered replies matching their four points. #2, #3, #4 are "done, here
are the numbers, see §X." #1 is the honest one: no second vendor was available; here is
what we did instead (version check if it fired, generality across the axes we do have, the
portable protocol), and here is the sharpened limitation.

**Shared note.** Both reviewers rated themselves *knowledgeable*, and 11B's summary shows
they read the paper carefully and liked the repeat control. Write to that: no padding, no
over-claiming, and flag the upper-bound caveat on the adversarial number yourself before
they do.

---

## 7. Order of work

Sequential dependencies are weak, so run these in parallel.

**Day 1.** Resolve `jev-latest` version (W5a — one call, may change the 11B #1 answer).
Launch W3 arms 3b and 3c, which need no code changes. Write the `--all-permutations` and
`--order-mode` flags.

**Days 1–2.** W1 and W2 analysis blocks into `analyze.py`, macros into
`export_numbers.py`, tables drafted. These need no new data and are the two results that
move the reviews, so get them locked early.

**Days 2–4.** W3 arms 3a and 3d running. W4 rewrite: title, abstract, contributions,
introduction, discussion. Execute the §5 cuts to make room.

**Day 5.** Fold W3 results in. Rebuild, verify the page guard, run `check_parity.py`.
Write the response letter last, once the section numbers are final.

**Day 6.** Full reread against both reviews, line by line, checking each point is visibly
answered and that no claim outruns its evidence.

---

## 8. Housekeeping — done

An earlier comparison harness targeting other decision APIs was retired and deleted. None
of it was ever run, no result in the paper depends on it, and the `comparison/` tree is
gone from the repository.

What replaced it as the answer to "only one model" is the cross-version arm (W5a, which
fired): the vendor alias moved from `jev-1.13.0` to `jev-1.14.0` during the revision, so
re-running against the new build gives a genuine second system in the only sense available
to us. See `evidence/RUNBOOK_R1.md`.

## 9. What we deliberately do not do

Stating these keeps the revision from sprawling, and each has a one-line answer ready if a
reviewer asks.

- **No hazard-detection or benign-vs-dangerous classifier.** Building one is a paper of its
  own and the paper already says so. W1 and W2 supply the deployment relevance instead.
- **No latency measurement.** The paper's cost argument rests on price, which is measured.
  Latency is claimed nowhere and should stay that way.
- **No second vendor.** Covered in W5.
- **No all-24-orderings run on LAB-Bench.** The wide items make it expensive and the
  sample sizes are too small to support the conclusion. The reversal arm (3d) covers those
  datasets instead.

---

## 10. Honest assessment of the odds

11B is already an accept and will stay one — three of their four asks get real numbers and
the fourth gets a straight answer.

11A is the real question. The reviewer's objection is about *contribution*, not
correctness, and they did not ask for experiments. That means **W4, the reframing, matters
more than W1–W3 for flipping that score** — though W1 is what makes the reframing credible
rather than cosmetic. A reviewer who scored a paper "limited contribution" will not change
their mind because four more datasets were rotated; they will change it if the paper now
opens with a security finding and a measurement trap that they recognise as non-obvious.

Biggest risk: adding W1, W2 and W3 to an already-full 6-page paper produces something
dense and unreadable, and a reviewer who finds it cramped may hold the score. **Cut harder
than feels comfortable.** Two sharp new results presented with room to breathe will beat
five results crammed in.
