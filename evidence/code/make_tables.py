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
    rev = S.get("a16_reversal", {}).get("per_dataset", {})
    L = [r"\begin{table*}[t]", r"\centering",
         r"\caption{Per-dataset results. ECE and AUROC are on $p_{\max}$, not the vendor "
         r"\texttt{confidence} field. \emph{Retained} withholds the least confident 40\%. "
         r"\emph{Flip} is the share of predictions that change when the option list is "
         r"reversed, a single meaning-preserving change: no dataset's accuracy moves "
         r"significantly, yet up to a third of decisions do. Intervals are Wilson.}",
         r"\label{tab:main}",
         r"\footnotesize",
         r"\setlength{\tabcolsep}{3.3pt}",
         r"\begin{tabular}{@{}llrccccccc@{}}", r"\toprule",
         r"Suite & Dataset & $N$ & opts. & accuracy [95\% CI] & ECE & AUROC & "
         r"$P(\text{err}\mid p_{\max}\!\geq\!0.9)$ & retained & flip \\", r"\midrule"]
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
        flip = (f"{rev[k]['prediction_flip_rate']:.3f}" if k in rev else "--")
        L.append(f"{famcell} & {LABEL[k]} & {h['n']} & {opts} & {acc} & "
                 f"{fmt(cal[k]['on_pmax']['ece_fixed'])} & "
                 f"{fmt(sel[k]['p_max']['auroc'])} & {peh} & "
                 f"{fmt(d['retained_accuracy'])} & {flip} \\\\")
    tot = S["headline"]["totals"]
    pooled_ece = S["a2_calibration"]["pooled"]["on_pmax"]["ece_fixed"]
    pooled_auroc = S["a4_selective_prediction"]["pooled"]["p_max"]["auroc"]
    L += [r"\midrule",
          f"\\multicolumn{{2}}{{@{{}}l}}{{\\textbf{{pooled}}}} & {tot['n']} & 2--10 & "
          f"{tot['accuracy']:.3f} [{tot['ci'][0]:.3f}, {tot['ci'][1]:.3f}] & "
          f"{pooled_ece:.3f} & {pooled_auroc:.3f} & -- & -- & -- \\\\",
          r"\bottomrule", r"\end{tabular}", r"\end{table*}"]
    return "\n".join(L)


def table2_order():
    """Option order as a steering surface, against the byte-identical control.

    Both arms spend four calls per item, so the rows are directly comparable and the
    difference between them is what re-presentation costs rather than what extra calls buy.
    """
    a13 = S["a13_order_attack"]
    cb = S["a8_position_bias"]["chance_baselines"]
    keys = [k for k in KEYS if k in a13]
    L = [r"\begin{table}[t]", r"\centering",
         r"\caption{Option order as a decision-steering surface. \emph{ident.} is four "
         r"byte-identical calls, isolating run-to-run variation; \emph{rot.} is four "
         r"cyclic rotations, which add option order. Equal budget, so the difference is "
         r"what re-presentation costs. \emph{Worst}: correct under \emph{every} "
         r"presentation, an upper bound since choosing the worst needs the answer. "
         r"\emph{Steerable}: correct under some and incorrect under others, which does "
         r"not.}",
         r"\label{tab:order}", r"\footnotesize",
         r"\setlength{\tabcolsep}{3pt}",
         r"\begin{tabular}{@{}lrcccccc@{}}", r"\toprule",
         r"& & & \multicolumn{2}{c}{worst case} & \multicolumn{2}{c}{steerable} & due to \\",
         r"\cmidrule(lr){4-5}\cmidrule(lr){6-7}",
         r"Dataset & opts. & single & ident. & rot. & ident. & rot. & order \\",
         r"\midrule"]
    for k in keys:
        e = a13[k]
        idt, rot = e["arms"]["identical"], e["arms"]["rotations"]
        oa = e["order_attributable"]
        c = cb.get(k, {})
        lo, hi = c.get("min_options"), c.get("max_options")
        opts = (str(lo) if lo == hi else f"{lo}--{hi}") if lo else "--"
        L.append(f"{LABEL[k]} & {opts} & {rot['acc_single']:.3f} & "
                 f"{idt['worst_case_accuracy']:.3f} & {rot['worst_case_accuracy']:.3f} & "
                 f"{idt['steerable_fraction']:.3f} & {rot['steerable_fraction']:.3f} & "
                 f"$+${100 * oa['steerable_fraction_increase']:.1f}~pp \\\\")
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
