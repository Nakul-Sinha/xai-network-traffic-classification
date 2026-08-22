"""
Multi-seed aggregation for the synthetic-benchmark audit (parcel B1).

Loads results/audit_<ptag>[_seed<N>].json for seeds 0..4 (seed 0 has no suffix) and
emits results/robustness.md with, for each (model family, explainer, p):
  mean +/- sd of false_confidence, blind_spot, rho across seeds
and, per (family, p), the ground-truth mean +/- sd of N(ip.ttl), N(tcp.window),
N(null=tcp.sport), plus test accuracy.

Provenance guard: every loaded file's internal "seed" field must match the seed implied
by its filename; mismatches are refused (never silently averaged). rho may be NaN when
an explainer's attributions have zero variance -> aggregated with nanmean/nanstd and the
number of finite values reported.

sd is the sample standard deviation (ddof=1) across seeds.

Usage:  python benchmark/aggregate_seeds.py [--seeds 0 1 2 3 4]
"""
import argparse, json, math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "results")
P_TAGS = {0.5: "p05", 0.7: "p07", 0.9: "p09", 1.0: "p10"}
FAMS = [("ByteCNN", "cnn"), ("RFFlow", "rf")]


def _mean_sd(vals):
    """Return (mean, sample sd, n_finite) ignoring NaNs; sd is NaN if n<2."""
    v = [x for x in vals if x is not None and not (isinstance(x, float) and math.isnan(x))]
    n = len(v)
    if n == 0:
        return float("nan"), float("nan"), 0
    m = sum(v) / n
    sd = math.sqrt(sum((x - m) ** 2 for x in v) / (n - 1)) if n > 1 else float("nan")
    return m, sd, n


def fmt(m, sd, n, total, dec=3):
    if n == 0:
        return "nan"
    s = f"{m:.{dec}f} +/- {sd:.{dec}f}" if not math.isnan(sd) else f"{m:.{dec}f} +/- n/a"
    if n < total:
        s += f" (n={n})"
    return s


def load_records(seeds):
    """records[p][seed] = json record; hard-fails on filename/internal seed mismatch."""
    records, problems = {}, []
    for p, tag in P_TAGS.items():
        records[p] = {}
        for s in seeds:
            suffix = "" if s == 0 else f"_seed{s}"
            path = os.path.join(RES, f"audit_{tag}{suffix}.json")
            if not os.path.exists(path):
                problems.append(f"MISSING: {os.path.basename(path)}")
                continue
            rec = json.load(open(path))
            if rec.get("seed") != s:
                problems.append(f"SEED MISMATCH: {os.path.basename(path)} has internal "
                                f"seed={rec.get('seed')} (expected {s}) -- refusing to use it")
                continue
            if rec.get("p") != p:
                problems.append(f"P MISMATCH: {os.path.basename(path)} has p={rec.get('p')}")
                continue
            records[p][s] = rec
    return records, problems


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, nargs="+", default=[0, 1, 2, 3, 4])
    args = ap.parse_args()
    seeds = args.seeds
    records, problems = load_records(seeds)
    if problems:
        print("PROVENANCE PROBLEMS:")
        for pr in problems:
            print("  " + pr)
        # missing/mismatched files are excluded, aggregation proceeds on what is clean;
        # exit nonzero so a caller cannot miss it
    total = len(seeds)

    L = [f"# Multi-seed robustness of the synthetic-benchmark audit (seeds {seeds})\n"]
    L.append("Every cell is mean +/- sample sd (ddof=1) across seeds. Each seed reshuffles the "
             "train/test split, the model initialization/training, and the PacketDO resampler "
             "stream; the generated datasets (one per p) are fixed. rho uses only finite values "
             "(it is NaN when an explainer's field scores have zero variance); when fewer than "
             f"{total} seeds contribute, (n=...) is shown.\n")
    if problems:
        L.append("**Provenance exclusions:**\n")
        L += [f"- {pr}" for pr in problems]
        L.append("")

    for fam_name, key in FAMS:
        L.append(f"## {fam_name}\n")
        L.append("### Ground truth (interventional necessity, PacketDO)\n")
        L.append("| p | test acc | N(ip.ttl) | N(tcp.window) | N(null=tcp.sport) |")
        L.append("|---|---|---|---|---|")
        for p in sorted(records):
            rs = [records[p][s] for s in seeds if s in records[p]]
            acc = _mean_sd([r[f"{key}_test_acc"] for r in rs])
            nttl = _mean_sd([r[key]["N"].get("ip.ttl") for r in rs])
            nwin = _mean_sd([r[key]["N"].get("tcp.window") for r in rs])
            nnull = _mean_sd([r[key]["null_N"] for r in rs])
            L.append(f"| {p} | {fmt(*acc, total)} | {fmt(*nttl, total)} "
                     f"| {fmt(*nwin, total)} | {fmt(*nnull, total)} |")
        L.append("")
        # explainer names present anywhere for this family
        names = sorted({nm for p in records for r in records[p].values()
                        for nm in r[key]["audit"].keys()})
        L.append("### Explainer audit vs N(F)\n")
        for nm in names:
            L.append(f"**{nm}**\n")
            L.append("| p | false_confidence | blind_spot | rho |")
            L.append("|---|---|---|---|")
            for p in sorted(records):
                audits = [records[p][s][key]["audit"][nm] for s in seeds
                          if s in records[p] and nm in records[p][s][key]["audit"]]
                fc = _mean_sd([a["false_confidence"] for a in audits])
                bs = _mean_sd([a["blind_spot"] for a in audits])
                rho = _mean_sd([a["rho"] for a in audits])
                L.append(f"| {p} | {fmt(*fc, total)} | {fmt(*bs, total)} | {fmt(*rho, total)} |")
            L.append("")

    # ---- per-seed diagnostics for the cells whose seed-0 value is revised ----
    def vec(p, key, nm, metric):
        return [records[p][s][key]["audit"][nm][metric] for s in seeds if s in records[p]]

    def nvec(p, key, fld):
        return [records[p][s][key]["N"].get(fld) for s in seeds if s in records[p]]

    L.append("## Per-seed diagnostics (headline cells)\n")
    L.append(f"Per-seed values in seed order {seeds}.\n")
    L.append(f"- CNN Saliency FC @ p=1.0: {vec(1.0, 'cnn', 'Saliency', 'false_confidence')}")
    L.append(f"- RF TreeSHAP FC @ p=1.0: {vec(1.0, 'rf', 'TreeSHAP', 'false_confidence')}")
    L.append(f"- RF N(ip.ttl) @ p=1.0:   {nvec(1.0, 'rf', 'ip.ttl')}")
    L.append(f"- RF N(tcp.window) @ p=1.0: {nvec(1.0, 'rf', 'tcp.window')}")
    L.append(f"- CNN IntegratedGradients FC @ p=1.0: "
             f"{vec(1.0, 'cnn', 'IntegratedGradients', 'false_confidence')}")
    L.append(f"- CNN DeepSHAP FC @ p=0.5: {vec(0.5, 'cnn', 'DeepSHAP', 'false_confidence')}")
    L.append("")
    L.append("Reading these: the RF TreeSHAP FC at p=1.0 is bimodal, and the mode tracks the "
             "model's realized reliance seed by seed -- FC=0.5 exactly in the seeds where the RF "
             "commits to a single one of the two perfectly-correlated shortcuts (one field's N "
             "large, the other's ~0), FC=0 in the seeds where it spreads reliance across both. "
             "The CNN commits to tcp.window in every seed (N(ttl)~0 throughout), so its Saliency "
             "FC is stable. Two seed-0 claims are revised by the multi-seed pass: "
             "IntegratedGradients FC at p=1.0 is not 0 (nonzero in some seeds), and DeepSHAP FC "
             "at p=0.5 is not 0 in every seed (clean at p>=0.7 in all seeds).\n")

    out = os.path.join(RES, "robustness.md")
    open(out, "w", encoding="utf-8").write("\n".join(L) + "\n")
    print(f"wrote {out}")

    # headline numbers for the board
    for fam_name, key, nm in [("ByteCNN", "cnn", "Saliency"), ("RFFlow", "rf", "TreeSHAP")]:
        audits = [records[1.0][s][key]["audit"][nm] for s in seeds
                  if s in records.get(1.0, {}) and nm in records[1.0][s][key]["audit"]]
        fc = _mean_sd([a["false_confidence"] for a in audits])
        print(f"HEADLINE p=1.0 {fam_name} {nm} FC = {fmt(*fc, total)}")

    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
