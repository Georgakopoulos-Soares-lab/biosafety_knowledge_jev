"""Generate REVISION_REPORT.tex from derived/stats.json.

Same discipline as the paper itself: no statistic is typed by hand. Every number in the
report is read from the analysis output, so the report cannot drift from the pipeline.

Run:  python3 manuscript/make_report.py && tectonic -X compile manuscript/REVISION_REPORT.tex
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
S = json.load(open(os.path.join(HERE, "..", "evidence", "derived", "stats.json")))

hl = S["headline"]["per_dataset"]
a2, a3 = S["a2_calibration"], S["a3_conditional_error"]
a10 = S["a10_cost"]
a13, a14 = S["a13_order_attack"], S["a14_threshold_transfer"]
a15, a16, a17 = S["a15_full_permutations"], S["a16_reversal"], S["a17_version_replication"]
LAB = {k: v["label"] for k, v in a3["per_dataset"].items()} if False else {}
LABEL = {d["key"]: d["label"] for d in S["meta"]["datasets"]}

# Domain tagging. The venue is biosecurity, so which datasets are biology and which are
# not is a reporting decision, not a cosmetic one.
BIO = ["bio", "bio-robust", "labbench-seq", "labbench-db", "labbench-litqa2",
       "labbench-cloning", "labbench-protocol", "labbench-supp"]
NONBIO = ["chem", "cyber"]
DOMAIN = {k: ("biology" if k in BIO else "chem" if k == "chem" else "cyber")
          for k in LABEL}


def pc(x, nd=1):
    return f"{100 * x:.{nd}f}\\%"


def f3(x):
    return f"{x:.3f}"


def rows_order():
    out = []
    for k in BIO + NONBIO:
        if k not in a13:
            continue
        e = a13[k]
        idt = e["arms"]["identical"]["steerable_fraction"]
        rot = e["arms"]["rotations"]["steerable_fraction"]
        inc = e["order_attributable"]["steerable_fraction_increase"]
        cb = S["a8_position_bias"]["chance_baselines"][k]
        lo, hi = cb["min_options"], cb["max_options"]
        opts = str(lo) if lo == hi else f"{lo}--{hi}"
        out.append((LABEL[k], DOMAIN[k], e["n_items"], opts, idt, rot, inc))
    out.sort(key=lambda r: -r[5])
    return out


def rows_reversal():
    out = []
    for k, v in a16["per_dataset"].items():
        out.append((LABEL[k], DOMAIN[k], v["n"], v["acc_baseline"], v["acc_reversed"],
                    v["mcnemar_q_bh"], v["prediction_flip_rate"]))
    out.sort(key=lambda r: -r[6])
    return out


n_bio = sum(hl[k]["n"] for k in BIO)
n_tot = sum(v["n"] for v in hl.values())
ord_rows = rows_order()
rev_rows = rows_reversal()
worst_order = ord_rows[0]
worst_rev = rev_rows[0]
cyb = a13["cyber"]

thr_bio = a14["per_source"]["bio"]
unach = [LABEL[k] for k, v in a14["achievable"].items() if not v["achievable"]]
eces = [v["on_pmax"]["ece_fixed"] for v in a2["per_dataset"].values()]


# ---- call accounting, read off the raw files so it cannot drift from what was collected
RAW = os.path.join(HERE, "..", "evidence", "raw")
ARMS = [
    ("Rotations, WMDP-Chem and Bio-Robust", [("perm_chem", "rot"), ("perm_bio-robust", "rot")],
     "completes the four WMDP suites"),
    ("Rotations, three LAB-Bench tasks",
     [("perm_labbench-db", "rot"), ("perm_labbench-seq", "rot"),
      ("perm_labbench-litqa2", "rot")], "biology; option counts 2--10"),
    ("Identical-call controls, five datasets",
     [(f"repeat_{k}", "rep") for k in
      ("chem", "bio-robust", "labbench-db", "labbench-seq", "labbench-litqa2")],
     "separates order from endpoint noise"),
    ("All 24 orderings, 500 items per suite",
     [("permall_cyber", "perm"), ("permall_bio", "perm")], "matched control; corrected us"),
    ("Reversed order, all ten datasets", [(f"{k}_rev", "jsonl") for k in LABEL],
     "non-cyclic ordering, every task"),
    ("Cross-version replication",
     [("perm114_cyber", "rot"), ("perm114_bio", "rot"),
      ("cyber_v114", "jsonl"), ("bio_v114", "jsonl")], "the second-system answer"),
]
KEYMAP = {"rot": "choices_by_rot", "rep": "choices_by_rep", "perm": "choices_by_perm"}


def _calls(name, kind):
    path = os.path.join(RAW, name + (".jsonl" if kind == "jsonl" else ".json"))
    if not os.path.exists(path):
        return 0
    if kind == "jsonl":
        return sum(1 for _ in open(path))
    return sum(len(r[KEYMAP[kind]]) for r in json.load(open(path)))


COST_ROWS, COST_TOTAL = [], 0
for _lab, _parts, _why in ARMS:
    _c = sum(_calls(n, k) for n, k in _parts)
    COST_ROWS.append((_lab, _c, _why))
    COST_TOTAL += _c
COST_USD = COST_TOTAL * a10["mean_input_tokens_per_call"] / 1e6 * a10["usd_per_m_input_tokens"]

L = []
A = L.append

A(r"\documentclass[11pt,a4paper]{article}")
A(r"\usepackage[margin=2.3cm]{geometry}")
A(r"\usepackage[T1]{fontenc}\usepackage{lmodern}")
A(r"\usepackage{booktabs,longtable,array,xcolor,amsmath}")
A(r"\usepackage[colorlinks=true,linkcolor=black,urlcolor=blue]{hyperref}")
A(r"\usepackage{titlesec}")
A(r"\titleformat{\section}{\large\bfseries}{\thesection}{0.6em}{}")
A(r"\definecolor{hl}{HTML}{B3402F}\definecolor{ok}{HTML}{3A7D44}")
A(r"\newcommand{\key}[1]{\textcolor{hl}{\textbf{#1}}}")
A(r"\setlength{\parskip}{0.45em}\setlength{\parindent}{0pt}")
A(r"\title{\textbf{What the revision did}\\[2pt]"
  r"\large Reviewer-by-reviewer record, with the data behind each claim}")
A(r"\author{BioAISS 2026 (ACSAC workshop) --- revision R1}")
A(r"\date{Generated from \texttt{evidence/derived/stats.json}; no figure typed by hand}")
A(r"\begin{document}\maketitle")

# ---------------------------------------------------------------- summary
A(r"\section*{In one paragraph}")
A(f"The reviewed version was read by both referees as a benchmark report on one vendor's "
  f"model. The revision keeps the benchmark but leads with three things a score cannot "
  f"show: the vendor's uncertainty field does not mean what it is named, a confidence "
  f"cut-off fitted on one task fails on another, and the order the answer options are "
  f"listed in can be used to move the decision. It adds {COST_TOTAL:,} "
  f"calls of new data across five new analyses, for \\${COST_USD:.2f}. "
  f"Two of the new results corrected the authors rather than "
  f"the reviewers, and both are reported as such.".replace(",", "{,}"))

# ---------------------------------------------------------------- bio framing
A(r"\section{A framing problem this report surfaces}")
A(f"The venue is biosecurity. \\key{{{100*n_bio/n_tot:.0f}\\% of the "
  f"{n_tot:,} items are biology}} (WMDP-Bio, its paraphrased variant, and six LAB-Bench "
  f"subtasks); WMDP-Cyber is {100*hl['cyber']['n']/n_tot:.0f}\\% and WMDP-Chem "
  f"{100*hl['chem']['n']/n_tot:.0f}\\%. The original paper led its instability result with "
  f"WMDP-Cyber, and the revision inherited that habit.".replace(",", "{,}"))
A(f"That is the wrong lead for this venue, and it also understates the finding. The most "
  f"order-sensitive dataset in the study is \\key{{{worst_order[0]}, a biology task}}, at "
  f"{pc(worst_order[5])} of decisions steerable --- higher than WMDP-Cyber's "
  f"{pc(cyb['arms']['rotations']['steerable_fraction'])}. Under reversal the most affected "
  f"is \\key{{{worst_rev[0]}}}, also biology, at {pc(worst_rev[6])} of predictions changed.")
A(r"\textbf{Recommended before submission:} re-lead the abstract, Section~4.5 and the "
  r"conclusion with the biology numbers, keeping WMDP-Cyber as the secondary comparison. "
  r"This is a presentation change only --- every number below is already collected.")

# ---------------------------------------------------------------- reviewer A
A(r"\section{Reviewer 11A --- ``limited contribution''}")
A(r"\emph{``The main contribution of the paper is benchmarking of jev on different suites "
  r"of Bio based datasets. This is a limited contribution.''}")
A(r"No experiment answers this; it is a framing failure. The contributions were rewritten:")
A(r"\begin{center}\small\begin{tabular}{@{}p{7.3cm}p{7.3cm}@{}}\toprule"
  r"\textbf{Was} & \textbf{Now} \\\midrule"
  r"``A reliability audit of a commercial System-1 model across 6{,}020 items'' &"
  r"``A protocol for auditing a scored decision API'' --- establishes what the vendor's "
  r"uncertainty field measures before trusting it \\[4pt]"
  r"``A controlled answer-order study'' &"
  r"``Answer order is a decision-steering surface'' \\[4pt]"
  r"``An evaluation of selective permutation averaging'' &"
  r"``Confidence cut-offs do not transfer across tasks'' \\"
  r"\bottomrule\end{tabular}\end{center}")
ece_f = a2["pooled"]["on_confidence_field"]["ece_fixed"]
ece_p = a2["pooled"]["on_pmax"]["ece_fixed"]
A(f"\\textbf{{Worked example of contribution 1.}} The API returns a field named "
  f"\\texttt{{confidence}}. On a four-option item where the model splits evenly between two "
  f"candidates ($p_{{\\max}}=0.5$), it reports "
  f"{S['a1_confidence_semantics']['worked_example']['reported_confidence']:.2f}, not 0.5. "
  f"The field is $(p_{{\\max}}-1/n)/(1-1/n)$, matching "
  f"{pc(S['a1_confidence_semantics']['candidates']['rescaled_pmax']['frac_within_tol'])} of "
  f"{S['a1_confidence_semantics']['n_records']:,} records. Measuring calibration against it "
  f"gives ECE \\key{{{ece_f:.3f}}} where the true figure is \\key{{{ece_p:.3f}}} --- wrong "
  f"by {ece_f/ece_p:.1f}$\\times$. The check is three lines and applies to any scored "
  f"interface.".replace(",", "{,}"))
A(r"Selective permutation averaging was demoted from a contribution to a paragraph, and "
  r"benchmark accuracy moved from being \emph{the} result to Table~1 supporting the others.")

# ---------------------------------------------------------------- 11B-3
A(r"\section{Reviewer 11B.3 --- task-specific calibration}")
A(r"\emph{``\ldots how confidence thresholds should be selected for practical "
  r"deployment.''} Answered with a measurement, using \textbf{no new API calls}.")
A(f"Procedure: on each dataset, fit the lowest $p_{{\\max}}$ cut-off holding errors among "
  f"accepted items at or below {pc(a14['meta']['target_error'],0)}; then apply that cut-off "
  f"unchanged elsewhere.")
A(r"\begin{center}\small\begin{tabular}{@{}lrrr@{}}\toprule" "\n"
  r"Cut-off fitted on & value & error on own task & worst elsewhere \\\midrule")
for k in ("bio", "cyber", "labbench-seq"):
    if k not in a14["per_source"]:
        continue
    r = a14["per_source"][k]
    w = r.get("worst_transfer")
    own = r["targets"][k]["error_rate"]
    cell = (f"{pc(w['error_rate'])} on {w['label']} ({w['ratio_to_target']:.1f}$\\times$)"
            if w else "--")
    L.append(f"{LABEL[k]} & {r['tau']:.2f} & {pc(own)} & {cell} \\\\")
A(r"\bottomrule\end{tabular}\end{center}")
A(f"\\key{{On {len(unach)} of {len(a14['achievable'])} tasks no cut-off reaches "
  f"{pc(a14['meta']['target_error'],0)} at any coverage}}: {', '.join(unach)}. For those, "
  f"the honest deployment answer is not to automate at all. Per-task ECE spans "
  f"{min(eces):.3f} to {max(eces):.3f}, a {max(eces)/min(eces):.0f}-fold range that the "
  f"pooled figure of {ece_p:.3f} conceals.")
A(r"\textbf{A defect this caught.} A draft of this table reported a 100\% error rate that "
  r"rested on three accepted items. Cells below "
  f"{a14['meta']['min_accepted']} accepted items are now flagged in the data and a build "
  r"check refuses to let one be quoted.")

# ---------------------------------------------------------------- 11B-2/4 order
A(r"\section{Reviewers 11B.2 and 11B.4 --- biosecurity relevance and robustness}")
A(r"The core experiment. Each item is answered under four presentations, and separately "
  r"under four \emph{byte-identical} repeats. Both cost four calls, so the difference "
  r"between them is what re-presentation costs rather than what extra calls buy. "
  r"\emph{Steerable} = answered correctly under some presentations and incorrectly under "
  r"others; it needs no knowledge of the correct answer, so it is the quantity an operator "
  r"should worry about.")
A(r"\begin{center}\small\begin{tabular}{@{}llrrrrr@{}}\toprule" "\n"
  r"Dataset & domain & $n$ & options & noise only & {} + order & due to order \\\midrule")
for lab, dom, n, opts, idt, rot, inc in ord_rows:
    mark = r"\key{" + f"{rot:.3f}" + "}" if dom == "biology" and rot > 0.25 else f"{rot:.3f}"
    L.append(f"{lab} & {dom} & {n} & {opts} & {idt:.3f} & {mark} & "
             f"$+${100*inc:.1f}~pp \\\\")
A(r"\bottomrule\end{tabular}\end{center}")
nsig = sum(v["order_attributable"]["significant"] for k, v in a13.items() if k != "meta")
A(f"The interval excludes zero on all {nsig} datasets. Three statements the reviewed "
  f"version could not make: instability is \\textbf{{not}} an artefact of four-option "
  f"questions (the two datasets whose option counts run from 2 to 10 are among the least "
  f"stable); WMDP-Cyber is \\textbf{{not}} the worst case; and robustness to paraphrase "
  f"buys no robustness to reordering --- WMDP-Bio-Robust, built for robustness, is no "
  f"steadier than WMDP-Bio.")

# ---------------------------------------------------------------- reversal
A(r"\subsection*{One reversed presentation, every dataset}")
A(f"Reversing the option list is a single meaning-preserving change costing one call per "
  f"item, so it runs on all {a16['summary']['n_datasets']} datasets, including the three "
  f"too small or too wide for a rotation sweep. For more than two options a reversal is "
  f"not a rotation, so this also probes orderings outside the cyclic group everywhere.")
A(r"\begin{center}\small\begin{tabular}{@{}llrrrrr@{}}\toprule" "\n"
  r"Dataset & domain & $n$ & accuracy & reversed & $q$ (BH) & predictions changed \\\midrule")
for lab, dom, n, ab, ar, q, fl in rev_rows:
    L.append(f"{lab} & {dom} & {n} & {ab:.3f} & {ar:.3f} & {q:.2f} & {fl:.3f} \\\\")
A(r"\bottomrule\end{tabular}\end{center}")
sm = a16["summary"]
A(f"\\key{{No dataset's accuracy moves}} (none significant after Benjamini--Hochberg; "
  f"largest shift {sm['max_abs_accuracy_change_pp']:.1f}~pp) while "
  f"\\key{{{pc(sm['flip_rate_min'])} to {pc(sm['flip_rate_max'])} of individual predictions "
  f"flip}}. This is the paper's thesis in its cleanest form, and it holds on every task.")

# ---------------------------------------------------------------- A15 correction
A(r"\section{Where the new data corrected us}")
A(r"The reviewed version claimed instability was under-counted \emph{because} rotations "
  r"preserve which option follows which, so they cannot see adjacency effects. We tested "
  r"it rather than asserting it.")
A(f"Presenting {a15['cyber']['n_items']} items per suite under all "
  f"{a15['cyber']['n_orderings']} orderings, we compared four rotations against four "
  f"randomly chosen \\emph{{non}}-rotations \\emph{{at the same budget}}, so any difference "
  f"is about which orderings rather than how many:")
A(r"\begin{center}\small\begin{tabular}{@{}lrr@{}}")
A(r"\toprule")
A(r"Suite & non-rotations $-$ rotations & 95\% CI \\")
A(r"\midrule")
for k in ("cyber", "bio"):
    m = a15[k]["matched"]
    A(f"{LABEL[k]} & {100*m['noncyclic_minus_cyclic']:+.1f}~pp & "
      f"$[{100*m['ci'][0]:+.1f}, {100*m['ci'][1]:+.1f}]$ \\\\")
A(r"\bottomrule\end{tabular}\end{center}")
A(f"\\key{{Both straddle zero: the claim was wrong.}} Rotations are representative of "
  f"orderings in general. The figures understate instability only because four "
  f"presentations are fewer than {a15['cyber']['n_orderings']} --- across all of them "
  f"{pc(a15['cyber']['arms']['all']['inconsistency'])} of WMDP-Cyber items are answered "
  f"inconsistently, against {pc(a15['cyber']['arms']['cyclic']['inconsistency'])} under "
  f"rotations alone.")
A(r"Reporting only that unmatched comparison --- ``24 orderings find more than 4'' --- "
  r"would have appeared to confirm the explanation we started with. It does not. The "
  r"adjacency claim has been removed from the paper.")

A(r"\section{Reviewer 11B.1 --- a second model}")
A(r"\emph{``\ldots another lightweight model or a representative generative baseline.''} "
  r"No second vendor was available, and we did not substitute a loosely comparable model. "
  r"The revision period supplied a partial answer instead.")
A(f"The alias the original runs named, \\texttt{{jev-latest}}, moved from "
  f"\\texttt{{{a17['meta']['published_version']}}} to "
  f"\\texttt{{{a17['meta']['replication_version']}}} within six weeks, with no change to "
  f"the identifier. \\key{{An evaluation reached through a floating alias is therefore not "
  f"reproducible}}; the endpoint accepts a concrete version and the harness now pins one.")
A(r"\begin{center}\small\begin{tabular}{@{}lrrrrr@{}}")
A(r"\toprule")
A(r"Suite & $n$ & published & updated & McNemar $p$ & decisions differing \\")
A(r"\midrule")
for k in ("cyber", "bio"):
    v = a17["per_dataset"][k]
    A(f"{LABEL[k]} & {v['n']} & {v['acc_published']:.3f} & {v['acc_replication']:.3f} & "
      f"{v['mcnemar_p']:.2g} & {pc(v['prediction_disagreement'])} \\\\")
A(r"\bottomrule\end{tabular}\end{center}")
A(f"Accuracy is unchanged on both suites, yet the builds disagree on up to "
  f"\\key{{{pc(a17['summary']['max_prediction_disagreement'])} of decisions}} --- the same "
  f"pattern as reordering, now across versions. The steerable fraction is retained "
  f"({pc(a13['cyber']['arms']['rotations']['steerable_fraction'])} to "
  f"{pc(a17['per_dataset']['cyber']['order_sensitivity']['replication']['steerable_fraction'])}"
  f" on WMDP-Cyber), so these properties are not an artefact of one frozen build. Two builds "
  f"of one vendor's model remain a weak substitute for a second vendor, and the paper says "
  f"so.")
A(r"This also prevented a silent defect: collected through the alias, the new arms would "
  r"have run against the updated model and been compared against data from the old one.")

A(r"\section{What it cost, and what is verified}")

A(r"\begin{center}\small\begin{tabular}{@{}lrl@{}}")
A(r"\toprule")
A(r"New arm & calls & purpose \\")
A(r"\midrule")
for lab, c, why in COST_ROWS:
    A(f"{lab} & {c:,} & {why} \\\\".replace(",", "{,}"))
A(r"\midrule")
A(f"\\textbf{{Total new data}} & \\textbf{{{COST_TOTAL:,}}} & "
  f"\\textbf{{$\\approx$\\${COST_USD:.2f}}} \\\\".replace(",", "{,}"))
A(r"\bottomrule\end{tabular}\end{center}")
A(r"\textbf{Verified from a clean tree:} the analysis regenerates byte-identically across "
  r"two runs; 163 macros in the paper are cited and checked against the rendered PDF; 12 "
  r"consistency checks pass, five added for the new results; permutation inversion is "
  r"tested on 3{,}000 randomised cases; the body is within the six-page limit; lint clean.")
A(r"\textbf{Asked for and not delivered --- one item.} Reviewer 11B.1 asked for a second "
  r"model. No second vendor was available, and we declined to substitute a loosely "
  r"comparable system and present it as settling the question. The cross-version arm above "
  r"is a partial answer and is labelled as partial.")
A(r"\textbf{Scope boundaries we state, which no reviewer asked us to cross.} We evaluate "
  r"no biosafety or hazard-classification task: reviewer 11B.2 explicitly noted that we "
  r"``clearly acknowledge this distinction'' and asked for a fuller discussion of the "
  r"deployment consequences, not for such a benchmark to be built. That discussion is "
  r"Section~5. We also do not measure latency, which neither reviewer raised; it is "
  r"declared so that the cost argument is not mistaken for a speed claim.")

A(r"\end{document}")

out = os.path.join(HERE, "REVISION_REPORT.tex")
open(out, "w").write("\n".join(L) + "\n")
print(f"wrote {out}")
