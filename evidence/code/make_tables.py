"""LaTeX tables for the manuscript, generated from derived/stats.json.

Table I is the manuscript's only table: per-dataset size, option range, chance-adjusted
lift, calibration, error detection, high-confidence error rate, and retained accuracy.
"""
import json
import os

from common import DERIVED, FAMILY, KEYS, LABEL

with open(os.path.join(DERIVED, "stats.json")) as _fh:
    S = json.load(_fh)
OUT = os.path.join(DERIVED, "tables")


def fmt(x, nd=3):
    return "--" if x is None or x != x else f"{x:.{nd}f}"


def table1():
    hl = S["headline"]["per_dataset"]
    cb = S["a8_position_bias"]["chance_baselines"]
    cal = S["a2_calibration"]["per_dataset"]
    sel = S["a4_selective_prediction"]["per_dataset"]
    ce = S["a3_conditional_error"]["per_dataset"]

    be = S["a7_breakeven"]
    L = [r"\begin{table*}[t]", r"\centering",
         r"\caption{Per-dataset results. \emph{Lift} is chance-adjusted accuracy, "
         r"$(\mathrm{acc}-c)/(1-c)$, using each item's own $c=1/n$ since option counts "
         r"range from 2 to 10. ECE and AUROC are on $p_{\max}$, not the vendor "
         r"\texttt{confidence} field (Section~\ref{sec:uncertainty}). \emph{Retained} is "
         r"accuracy with the least confident 40\% withheld "
         r"(Section~\ref{sec:selective}). Intervals are Wilson.}",
         r"\label{tab:main}",
         r"\footnotesize",
         r"\setlength{\tabcolsep}{3.3pt}",
         r"\begin{tabular}{@{}llrccccccc@{}}", r"\toprule",
         r"Suite & Dataset & $N$ & opts. & accuracy [95\% CI] & lift & ECE & AUROC & "
         r"$P(\text{err}\mid p_{\max}\!\geq\!0.9)$ & retained \\", r"\midrule"]
    prev_fam = None
    for k in KEYS:
        h, c = hl[k], cb[k]
        fam = FAMILY[k]
        if prev_fam is not None and fam != prev_fam:
            L.append(r"\midrule")
        famcell = fam if fam != prev_fam else ""
        prev_fam = fam
        opts = (f"{c['min_options']}" if c["min_options"] == c["max_options"]
                else f"{c['min_options']}--{c['max_options']}")
        acc = f"{h['accuracy']:.3f} [{h['ci'][0]:.2f}, {h['ci'][1]:.2f}]"
        e = ce[k]
        # n for each high-confidence subset is quoted in the text where it matters;
        # omitted here to keep the table inside \textwidth.
        peh = (f"{e['p_error_given_high_conf']:.3f} "
               f"[{e['p_error_given_high_conf_ci'][0]:.2f}, "
               f"{e['p_error_given_high_conf_ci'][1]:.2f}]")
        d = be[k]["by_deferral"]["0.4"]
        L.append(f"{famcell} & {LABEL[k]} & {h['n']} & {opts} & {acc} & "
                 f"{fmt(c['chance_adjusted_lift'])} & {fmt(cal[k]['on_pmax']['ece_fixed'])} & "
                 f"{fmt(sel[k]['p_max']['auroc'])} & {peh} & "
                 f"{fmt(d['retained_accuracy'])} \\\\")
    tot = S["headline"]["totals"]
    pooled_ece = S["a2_calibration"]["pooled"]["on_pmax"]["ece_fixed"]
    pooled_auroc = S["a4_selective_prediction"]["pooled"]["p_max"]["auroc"]
    L += [r"\midrule",
          f"\\multicolumn{{2}}{{@{{}}l}}{{\\textbf{{pooled}}}} & {tot['n']} & 2--10 & "
          f"{tot['accuracy']:.3f} [{tot['ci'][0]:.3f}, {tot['ci'][1]:.3f}] & -- & "
          f"{pooled_ece:.3f} & {pooled_auroc:.3f} & -- & -- \\\\",
          r"\bottomrule", r"\end{tabular}", r"\end{table*}"]
    return "\n".join(L)


def table2_order():
    """Option order as a steering surface, against the byte-identical control.

    Both arms spend four calls per item, so the rows are directly comparable and the
    difference between them is what re-presentation costs rather than what extra calls buy.
    """
    a13 = S["a13_order_attack"]
    keys = [k for k in ("bio", "cyber") if k in a13]
    L = [r"\begin{table}[t]", r"\centering",
         r"\caption{Option order as a decision-steering surface, at a matched budget of "
         r"four calls per item. \emph{Worst case}: correct under \emph{every} "
         r"presentation. \emph{Steerable}: correct under some and incorrect under others. "
         r"The \emph{identical} rows repeat one prompt byte for byte, isolating "
         r"run-to-run variation, so the difference between the rows is what order "
         r"contributes.}",
         r"\label{tab:order}", r"\footnotesize",
         r"\setlength{\tabcolsep}{4pt}",
         r"\begin{tabular}{@{}llccc@{}}", r"\toprule",
         r"Dataset & presentations & worst case & best case & steerable \\", r"\midrule"]
    for k in keys:
        e = a13[k]
        for arm, name in (("identical", "identical (control)"), ("rotations", "4 rotations")):
            v = e["arms"][arm]
            cell = LABEL[k] if arm == "identical" else ""
            L.append(f"{cell} & {name} & {v['worst_case_accuracy']:.3f} & "
                     f"{v['best_case_accuracy']:.3f} & {v['steerable_fraction']:.3f} \\\\")
        oa = e["order_attributable"]
        L.append(r"\cmidrule(l){2-5}")
        L.append(f" & \\emph{{due to order}} & "
                 f"$-${100 * oa['worst_case_accuracy_drop']:.1f}~pp & -- & "
                 f"$+${100 * oa['steerable_fraction_increase']:.1f}~pp \\\\")
        if k != keys[-1]:
            L.append(r"\midrule")
    L += [r"\bottomrule", r"\end{tabular}", r"\end{table}"]
    return "\n".join(L)


def main():
    os.makedirs(OUT, exist_ok=True)
    for name, body in (("table1_main.tex", table1()), ("table2_order.tex", table2_order())):
        path = os.path.join(OUT, name)
        with open(path, "w") as fh:
            fh.write(body + "\n")
        print(f"  wrote {path}")


if __name__ == "__main__":
    main()
