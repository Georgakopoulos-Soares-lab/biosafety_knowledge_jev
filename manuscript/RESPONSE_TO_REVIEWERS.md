# Response to reviewers — BioAISS 2026 (ACSAC workshop)

We thank both reviewers. Every point below is answered with a change in the paper, and
each change is named with the section it landed in. Five new results were added: two
recomputed from the decision records already released with the first submission, and three
from 43,000 further API calls. Every number is produced by the released pipeline, and the
build fails if the text cites a value the pipeline did not emit.

Two of the new results corrected us rather than the reviewers. A matched control refuted
an explanation this paper had itself written into its limitations, and a draft of the
threshold table quoted a 100% error rate that rested on three items. Both are described
below, because a revision that only reports what went well is not worth reading.

Where we could not do what a reviewer asked, we say so plainly rather than substituting
something else and hoping it passes.

---

# Reviewer 11A

> *"The main contribution of the paper is benchmarking of jev on different suites of Bio
> based datasets. This is a limited contribution."*

**We agree with the reviewer, and the criticism landed on a framing problem that was ours
to fix.** A table of accuracy scores for one company's model would be a thin contribution,
and that is what the paper led with. It is not what the study actually produced.

We have rewritten the title, abstract, introduction, contributions and conclusion so the
paper leads with findings that no accuracy score can show. Concretely:

**1. The company's own uncertainty number does not mean what its name says.** The field is
labelled `confidence`, but it is the top probability stretched onto a 0-to-1 scale, not the
chance that the answer is right. Anyone who takes it at face value and measures calibration
against it gets 0.091 when the true figure is 0.034 — wrong by nearly three times. The
check that catches this is three lines of code and works on any model that returns a score
through an interface. This is now contribution 1.

**2. The order the answer options are listed in can be used to steer the decision.** This
is a security result, not a robustness curiosity, and it is new in this revision
(Section 4.5, Table 2). Someone who changes nothing but the order of the options can move
30.6% of WMDP-Cyber decisions. Worst-case accuracy falls from 63.3% to 49.2%. We separate
this from the endpoint simply being noisy by repeating the identical prompt the same number
of times — a control the order-sensitivity papers we cite do not run.

**3. A confidence cut-off chosen on one task does not work on another.** Also new
(Section 4.2). A cut-off tuned on WMDP-Bio to keep errors at 5% produces 40% errors on
LitQA2. On 5 of our 10 tasks, no cut-off reaches 5% errors at any level of coverage.

We also made visible something the first version buried: three of our own early results did
not survive internal checking and were corrected, including one where a null model we built
ourselves produced a *larger* effect than we had observed, which killed the causal reading
we had wanted to make (Section 4.4). We report it as a negative result because that is what
it is.

Benchmark accuracy is still in the paper, but it is now Table 1 supporting the findings
rather than the finding itself.

---

# Reviewer 11B

We are grateful for the careful summary; it described the study more accurately than our
own framing did, which is part of why we rewrote the framing.

### 1. Evaluation across additional models

> *"including another lightweight model or a representative generative baseline would help
> establish whether the observed instability is specific to the evaluated model."*

**We could not obtain a second vendor's model, but the revision period handed us a
partial answer we did not expect.** The alias our runs used, `jev-latest`, has moved from
`jev-1.13.0` to `jev-1.14.0`. We re-ran both arms against the new version, pinned.

The result is the same pattern the paper is about. Accuracy is unchanged on both suites
(WMDP-Cyber *p* = 0.43, WMDP-Bio *p* = 1.0), yet the two versions give different answers
on 13.9% and 4.6% of items, and the steerable fraction is retained (0.306 to 0.260 on
WMDP-Cyber, unchanged at 0.095 on WMDP-Bio). So these properties are not an artefact of
one frozen build. Two builds of one vendor's model remain a weak substitute for a second
vendor, and Section 4.7 says exactly that.

This also surfaced a reproducibility problem worth reporting on its own: a hosted model
moved under a published evaluation within six weeks, with no change to the identifier the
original runs named. Any result collected through a floating alias is not reproducible.
The released harness now pins a concrete version, and the paper says so.

Alongside that, in the limitations section:

- **We state the limit precisely.** Whether these magnitudes hold across vendors is open,
  and it is the first thing we would test given a second system.
- **We make the protocol portable and say what it needs.** It requires only a system that
  returns a probability spread across the options it was given. The released harness puts
  that behind one interface, so a second system is a drop-in, not a rewrite.
- **We are explicit about the generality we do have.** The findings hold across 10
  datasets, option counts from 2 to 10, three option-labelling schemes and two prompt
  formats. That is not generality across vendors and we do not claim it is.

We have also built and released the apparatus for the broader runs described under point 4,
so that the extension is a data-collection step rather than new engineering.

### 2. Stronger connection to biosecurity applications

> *"a more detailed discussion of how calibration and permutation instability might affect
> practical biosecurity screening systems."*

**Added, and this became the paper's strongest section.** Section 5 now works through what
our measurements mean for a model placed in front of a human reviewer, clearing the items
it is sure about and passing on the rest. Three consequences, none visible in an accuracy
score:

- **The threshold cannot come from an overall average.** It has to be fitted on held-out
  items from the task that will actually turn up, and on 5 of our 10 tasks no threshold
  reaches a 5% error rate at any coverage. For those, the right answer is not to automate
  at all.
- **The escalation rate is a real cost.** Holding WMDP-Cyber to 5% errors leaves only 24%
  of items cleared automatically; the other 76% go to a person.
- **Presentation is an attack surface.** Where whoever submits an item has any influence
  over how it is shown, part of the decision is theirs to move — 30.6% of WMDP-Cyber
  decisions in our measurement. Checking whether the answer survives re-presentation is
  cheap, and it both flags shaky decisions and takes that control away.

We still do not claim to evaluate a screening system, and we repeat that doing so needs a
purpose-built safe-versus-dangerous benchmark we do not provide.

### 3. Task-specific calibration analysis

> *"additional discussion of uncertainty estimation under task distribution shifts and how
> confidence thresholds should be selected for practical deployment."*

**Added as a quantitative result rather than a discussion** (Section 4.2). We fit, on each
dataset, the lowest cut-off that holds errors among accepted items at or below 5%, then
apply that cut-off unchanged to every other dataset:

| Cut-off fitted on | Value | Errors on its own task | Worst elsewhere |
|---|---|---|---|
| WMDP-Bio | 0.87 | 5.0% (69% of items accepted) | **40.0% on LB-LitQA2** (8× the target) |
| WMDP-Cyber | 0.94 | 4.7% (24% accepted) | 4.8% on WMDP-Chem |
| LB-SeqQA | 0.55 | 4.5% | 51.0% on LB-LitQA2 |

On the reviewer's specific concern about the small subtasks: we agree the sample sizes
force caution, and we have built that caution into the analysis rather than only mentioning
it. Any cell resting on fewer than 20 accepted items is flagged in the released data and is
never quoted in the paper — an early draft of this table reported a 100% error rate that
turned out to rest on three items, and a check in the build now refuses to let such a
number be quoted.

We also report equal-mass binning alongside equal-width binning, because equal-width ECE is
unstable on small subtasks. The spread survives it (0.033 pooled, 0.185 on the worst
subtask), so the sixfold range across tasks is not an artefact of how the bins were drawn.

The deployment rule we draw is stated plainly: fit the threshold on held-out items from the
task it will run on, or do not use a threshold.

### 4. Broader robustness evaluation

> *"The permutation analysis is primarily restricted to four cyclic rotations of four-option
> multiple-choice questions."*

**The reviewer is right, and we have now run the experiments rather than argue about
them.** Four further arms, 43,000 additional calls:

**The order effect is not confined to four-option questions.** It now covers seven
datasets with the matched control on every one, including two whose option counts run from
2 to 10. Steerable items attributable to order, over the byte-identical control:

| dataset | options | steerable (noise) | steerable (+order) | due to order |
|---|---|---|---|---|
| WMDP-Bio | 4 | 0.020 | 0.095 | +7.5 pp |
| WMDP-Bio-Robust | 4 | 0.030 | 0.104 | +7.4 pp |
| WMDP-Chem | 4 | 0.042 | 0.154 | +11.3 pp |
| WMDP-Cyber | 4 | 0.065 | 0.306 | +24.2 pp |
| LB-SeqQA | **2–5** | 0.083 | 0.295 | +21.2 pp |
| LB-DbQA | 4 | 0.058 | **0.327** | +26.9 pp |
| LB-LitQA2 | **2–10** | 0.020 | 0.206 | +18.6 pp |

The interval excludes zero on all seven. Two consequences we could not state before:
WMDP-Cyber is **not** the worst case (LB-DbQA is), and robustness to paraphrase buys no
robustness to reordering — WMDP-Bio-Robust, a set built for robustness, is no steadier
under reordering than WMDP-Bio.

**A reversed presentation, on all ten datasets.** No dataset's accuracy moves (none
significant after Benjamini–Hochberg, largest shift 9.8 pp) while 6.8% to 34.2% of
individual predictions flip. Reversal is not a rotation for more than two options, so this
covers non-cyclic orderings on every dataset, including the three too small or too wide
for a rotation sweep. It is now a column in Table 1.

**Every one of the 24 orderings, and a correction to ourselves.** We had written into the
limitations that rotations under-count *because* they preserve which option follows which.
We built a matched control to test it — four rotations against four randomly chosen
non-rotations, equal budget — and it refutes the claim: −2.0 pp on WMDP-Cyber (95% CI
[−4.8, +0.8]) and −0.2 pp on WMDP-Bio ([−2.4, +2.0]), both straddling zero. Rotations are
representative of orderings in general. Our figures understate instability only because
four presentations are fewer than 24 (46.8% of WMDP-Cyber items inconsistent across all
24, against 37.2% across the rotations).

We report this because the unmatched comparison alone — 24 orderings find more than 4 —
would have appeared to confirm the explanation we started with. It does not. The adjacency
claim has been removed from the paper.

---

## Summary of changes

| Change | Section | Prompted by |
|---|---|---|
| New title, abstract, contributions, conclusion | throughout | 11A |
| Option order as a decision-steering surface, with control | 4.5, Table 2 | 11A, 11B-2 |
| Confidence cut-offs do not transfer across tasks | 4.2 | 11B-2, 11B-3 |
| Equal-mass binning reported alongside equal-width | 4.2, Table 1 | 11B-3 |
| Small-sample cells flagged and barred from quotation | build check | 11B-3 |
| Screening-pipeline implications | 5 | 11B-2 |
| Why rotations under-count, stated as a reason not a hedge | 5.1 | 11B-4 |
| Portable-protocol statement and sharpened one-model limit | 5.1 | 11B-1 |
| Self-correction of three earlier results made visible | 4.4 | 11A |

The paper remains within the 6-page limit. No result was dropped to make room: the space
came from merging the two figures into one, folding the instability chart into Table 2
(which carries the same comparison plus two more columns), moving the reversal result into
Table 1 as a column, compressing the selective-averaging section to a paragraph, and
tightening prose throughout. All 12 automated consistency checks pass, including five added
for the new results, and the analysis is byte-identical on re-run.
