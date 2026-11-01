# Response to reviewers — BioAISS 2026 (ACSAC workshop)

We thank both reviewers. Every point below is answered with a change in the paper, and
each change is named with the section it landed in. Two new results were added. Both are
computed from the decision records already released with the first submission, so they can
be checked today against the public repository — no new data collection stands behind
them.

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

**This is the one request we could not meet, and we would rather say so than pretend
otherwise.** We did not have access to a second comparable system during the revision
period. We did not want to substitute a loosely comparable model and present it as
settling the question, because it would not.

What we did instead, in the limitations section:

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

**The reviewer is right, and we can now say why the restriction matters rather than only
that it exists.** Four rotations are 4 of the 24 possible orderings, and they all share a
property: they never change which option follows which. So a rotation-only measurement
cannot detect any sensitivity that depends on two options sitting next to each other. The
instability we report is a lower bound for that reason as well as for covering only
four-option items, and the limitations section now says so.

We have implemented and released the apparatus to close this, as four additions to the
collection harness:

- every one of the 24 orderings, on a seeded sample of four-option items;
- rotations on WMDP-Chem and WMDP-Bio-Robust, extending the result from two of the four
  WMDP suites to all four;
- rotations on three LAB-Bench tasks, which carry 2 to 10 options and therefore take the
  measurement **off four-option multiple choice entirely**;
- a reversed-order arm on all 10 datasets, which is the cheapest ordering outside the
  rotation family and runs on the wide items too.

The permutation and inversion logic is covered by tests that confirm every ordering maps
back to the original option indices. We did not want to report numbers from these arms
before the data was collected, so the paper states the limitation honestly and the harness
is in the repository.

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

The paper remains within the 6-page limit. Nothing was dropped to make room: the space came
from merging the two figures into one, folding the instability chart into Table 2 which
carries the same comparison plus two more columns, and tightening prose. All 12 automated
consistency checks pass, including 5 added for the new results.
