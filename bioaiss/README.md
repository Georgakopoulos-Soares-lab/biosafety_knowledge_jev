# Camera-ready package

*Auditing System-1 Models on Biosecurity-Relevant Benchmarks: Calibration, Selective
Prediction, and Permutation Instability in a Non-Generative Model*

BioAISS 2026 (ACSAC workshop) — revision R1. Submission deadline 06 November 2026.
Production editor: Martha Nunez, martha.nunez@contractor.ieee.org.

Title unchanged from the reviewed version; neither reviewer asked for a change to it.

## Contents

```
paper.pdf                           the camera-ready paper (6 pages, US Letter, PDF 1.4)
source/                             LaTeX source, compiles standalone
  main.tex                          manuscript, \documentclass[conference]{IEEEtran}
  numbers.tex                       every statistic, as \stat* macros (generated)
  refs.bib                          bibliography
  main.bbl                          pre-built bibliography, so no BibTeX pass is needed
  IEEEtran.cls                      venue class file
  figs/                             figure PDF and the two generated tables
response/
  response-to-reviewers.{md,pdf}    point-by-point reply to 11A and 11B
  revision-report.pdf               longer record of what changed, with the data
```

## IEEE submission checklist

Verified against the production instructions, by inspecting the file rather than assuming:

| Requirement | Status |
|---|---|
| Page size 612 x 792 pt (8.5 x 11 in) | US Letter, enforced by a build guard |
| Conference mode | `\documentclass[conference]{IEEEtran}`, matching the linked template |
| All fonts embedded and subset | 17 of 17 fonts, verified with `pdffonts` |
| Graphics at 300 dpi or better | the only figure is vector PDF, so resolution-independent |
| Acrobat 5.0 compatibility | PDF 1.4, set via `\special{pdf:minorversion 4}` |
| Bibliography style | `IEEEtran.bst`, as supplied in IEEEtranBST2 |
| Unresolved references | none |
| Optimized (linearized) | **not applied** --- see below |

**On linearization.** The instructions list "Optimized" among the distiller settings. No
linearizer (`qpdf`, Ghostscript) is installed here, so `paper.pdf` is not linearized.
This is a web-delivery optimisation rather than a rendering property, and PDF eXpress
produces the Xplore-compatible file in any case. If production asks for it:
`qpdf --linearize paper.pdf paper-linearized.pdf`.

**If submitting source instead of PDF.** PDF eXpress needs all support files for LaTeX.
Send the whole `source/` directory; `main.bbl` is included so no BibTeX pass is required.

## Building

```sh
cd source && tectonic -X compile main.tex --outfmt pdf
```

No other dependency, and no network access needed. Produces 6 pages; verified by building
from a clean copy of `source/` with zero errors.

## A note on the numbers

No statistic in the paper or in `response/` is typed by hand. Every one is computed by the
analysis pipeline, written to `evidence/derived/stats.json`, and exported as a LaTeX macro
into `numbers.tex`. In the full repository the build fails if the text cites a macro the
pipeline did not emit, and a parity check confirms each cited value appears in the rendered
PDF. That machinery needs the `evidence/` tree and so is not reproduced here; it lives at
the repository linked in the paper.

Figures for the record: the revision added **66,578** API calls across four new data arms,
at a measured cost of about **$2.07**. The analysis is deterministic — two runs produce a
byte-identical `stats.json`.

## What changed since review

Summarised in `response/response-to-reviewers.pdf`, in full in
`response/revision-report.pdf`. In brief:

- Contributions rewritten to lead with findings rather than with the audit itself (11A).
- New: option order as a decision-steering surface, on seven datasets with a matched
  byte-identical control (11A, 11B-2, 11B-4).
- New: confidence cut-offs do not transfer across tasks; on five of ten tasks no cut-off
  reaches a 5% error rate at any coverage (11B-3).
- New: reversal arm on all ten datasets, and all 24 orderings on a sample (11B-4).
- New: replication against the updated model version, after the vendor alias moved
  mid-revision (11B-1, partially).
- Two self-corrections are reported as such: a matched control refuted an explanation the
  paper had itself advanced, and a draft table quoted an error rate resting on three items.

## Known open items

- **No second vendor.** 11B-1 asked for another model; none was available, and we declined
  to substitute a loosely comparable one. The cross-version arm is a partial answer and is
  labelled partial in the paper.
- **The paper leads its instability result with WMDP-Cyber.** For a biosecurity venue the
  biology datasets are the better lead, and they are also the stronger numbers — LB-DbQA is
  steerable on 32.7% of decisions against WMDP-Cyber's 30.6%. This is a presentation
  change, not a data change; see §1 of `revision-report.pdf`. Not applied here.
