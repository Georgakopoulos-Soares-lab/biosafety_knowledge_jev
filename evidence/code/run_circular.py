"""Cyclic (circular) evaluation: present every item in all n rotations of its option list.

This is the experiment that supplies the control arm a one-directional reshuffle test
lacks. For every rotation the returned distribution is mapped back to ORIGINAL option
indices, so rotations are directly comparable and can be averaged.

Generalises the original four-option-only script to arbitrary n, which is required for the
LAB-Bench subsets (2 to 10 options). --max-rotations caps the per-item cost for wide items.

--all-permutations presents every one of the n! orderings rather than only the n
rotations. Rotations preserve which option follows which, so they cannot detect any
sensitivity that depends on adjacency; the exhaustive arm measures how much the
rotation-only figure under-counts.

Usage:
  TYPESAFE_API_KEY=... python3 run_circular.py cyber bio
  TYPESAFE_API_KEY=... python3 run_circular.py bio-robust --max-rotations 4
  TYPESAFE_API_KEY=... python3 run_circular.py cyber --all-permutations --sample 500
"""
import argparse
import itertools
import json
import os
import random
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

import jev_client
from common import RAW
from jev_client import (
    build_choice_payload,
    labels_for,
    make_session,
    parse_choice,
    post,
)

MAX_WORKERS = 16


def load_items(subject):
    """Take questions and gold indices from an existing single-pass run."""
    path = os.path.join(RAW, f"{subject}.jsonl")
    items = []
    with open(path) as fh:
        for line in fh:
            r = json.loads(line)
            if r["error"] is not None:
                continue
            items.append({"index": r["index"], "question": r["question"],
                          "choices": r["choices"], "gold": r["gold_idx"]})
    return items


def cyclic_perms(n, max_rot=None):
    """Rotations as explicit permutations: prompt position p shows original (p + rot) % n."""
    n_rot = min(n, max_rot) if max_rot else n
    return [tuple((p + rot) % n for p in range(n)) for rot in range(n_rot)]


def all_perms(n):
    """Every ordering of n options.

    Rotations are only n of the n! orderings, and they share a property the others do
    not: they preserve which option follows which. So a rotation-only measurement cannot
    see any sensitivity that depends on adjacency, which is why the instability it
    reports is a lower bound. Enumerating the full set measures how loose that bound is.
    """
    return list(itertools.permutations(range(n)))


def plan_perms(items, max_rot, use_all, perm_width):
    """Per item, the list of orderings to present it under."""
    plan = []
    for it in items:
        n = len(it["choices"])
        if use_all:
            # Factorial growth makes this affordable only at the width we target.
            plan.append(all_perms(n) if n == perm_width else [])
        else:
            plan.append(cyclic_perms(n, max_rot))
    return plan


def run(subject, max_rot, label_mode, use_all=False, perm_width=4, sample=None,
        seed=20260919, out_prefix=None):
    items = load_items(subject)
    if use_all:
        items = [it for it in items if len(it["choices"]) == perm_width]
    if sample is not None and sample < len(items):
        # Seeded, so the sampled subset is reproducible and reviewable.
        idx = sorted(random.Random(seed).sample(range(len(items)), sample))
        items = [items[j] for j in idx]

    plan = plan_perms(items, max_rot, use_all, perm_width)
    session = make_session()
    tasks = [(i, j) for i, perms in enumerate(plan) for j in range(len(perms))]
    print(f"[{subject}] {len(items)} items, {len(tasks)} calls"
          f"{' (all orderings)' if use_all else ''}", file=sys.stderr)
    out = {}

    def work(i, j):
        ch = items[i]["choices"]
        n = len(ch)
        perm = plan[i][j]
        # Prompt position p shows the option originally at perm[p].
        presented = [ch[perm[p]] for p in range(n)]
        labels = labels_for(n, label_mode)
        data, err = post(session, build_choice_payload(items[i]["question"], presented, labels))
        if err is not None:
            return i, j, None
        p = parse_choice(data, labels)
        if p["chosen_pos"] < 0:
            return i, j, None
        # Invert: map both the choice and the whole vector back to original indices.
        probs_by_orig = [0.0] * n
        for pos in range(n):
            probs_by_orig[perm[pos]] = p["probs_by_position"][pos]
        return i, j, (perm[p["chosen_pos"]], probs_by_orig)

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        futures = [ex.submit(work, i, j) for i, j in tasks]
        done = 0
        for fut in as_completed(futures):
            i, j, val = fut.result()
            out[(i, j)] = val
            done += 1
            if done % 500 == 0:
                print(f"[{subject}] {done}/{len(tasks)}", file=sys.stderr)

    recs, dropped = [], 0
    for i, it in enumerate(items):
        per = [out.get((i, j)) for j in range(len(plan[i]))]
        if not per or any(p is None for p in per):
            dropped += 1
            continue
        rec = {"index": it["index"], "gold": it["gold"],
               "n_options": len(it["choices"])}
        if use_all:
            rec.update({"perms": [list(p) for p in plan[i]],
                        "choices_by_perm": [p[0] for p in per],
                        "probs_by_perm": [p[1] for p in per]})
        else:
            # Unchanged on-disk shape, so every existing analysis block keeps working.
            rec.update({"choices_by_rot": [p[0] for p in per],
                        "probs_by_rot": [p[1] for p in per]})
        recs.append(rec)
    stem = out_prefix or ("permall" if use_all else "perm")
    path = os.path.join(RAW, f"{stem}_{subject}.json")
    with open(path, "w") as fh:
        json.dump(recs, fh)
    print(f"[{subject}] wrote {len(recs)} complete items ({dropped} dropped) -> {path}")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("subjects", nargs="+")
    ap.add_argument("--max-rotations", type=int, default=None,
                    help="cap rotations per item; default is one per option")
    ap.add_argument("--label-mode", default="positional",
                    choices=["positional", "symbolic"])
    ap.add_argument("--all-permutations", action="store_true",
                    help="present every ordering, not only the rotations; writes "
                         "permall_<subject>.json and restricts to --perm-width items")
    ap.add_argument("--perm-width", type=int, default=4,
                    help="option count to enumerate exhaustively (default 4 -> 24 calls "
                         "per item); wider items are skipped because n! explodes")
    ap.add_argument("--sample", type=int, default=None,
                    help="evaluate a seeded random subset of this many items")
    ap.add_argument("--model-version", default=None,
                    help=f"pin a concrete model version (default {jev_client.MODEL}); "
                         "the floating alias no longer reproduces the published runs")
    ap.add_argument("--out-prefix", default=None,
                    help="override the output filename stem, to keep a replication arm "
                         "on a different model version from overwriting the main one")
    args = ap.parse_args()
    if args.model_version:
        jev_client.MODEL = args.model_version
    print(f"model: {jev_client.MODEL}", file=sys.stderr)
    for s in args.subjects:
        run(s, args.max_rotations, args.label_mode,
            use_all=args.all_permutations, perm_width=args.perm_width,
            sample=args.sample, out_prefix=args.out_prefix)


if __name__ == "__main__":
    main()
