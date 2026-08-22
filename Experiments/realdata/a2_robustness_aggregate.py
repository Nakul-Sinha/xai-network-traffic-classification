"""a2_robustness_aggregate.py - summarize a2_robustness_runs.json (ORG-C fix #5).

Reads results/a2_robustness_runs.json (written by a2_robustness.py), verifies
the default_seed0 run reproduces the stored seed-0 a2_port_results.json, and
prints per-run + mean+/-sd tables for the parcel-D1 metrics. Appends an
"aggregate" block back into the runs JSON so every reported mean/sd is
machine-traceable.
"""

from __future__ import annotations

import json
import os

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
RUNS_PATH = os.path.join(HERE, "results", "a2_robustness_runs.json")
SEED0_PATH = os.path.join(HERE, "results", "a2_port_results.json")

ORDER = ["default_seed0", "default_seed1", "default_seed2", "default_seed3",
         "alt_d30l5_seed0", "alt_d30l5_seed1"]


def ms(vals):
    a = np.array(vals, dtype=float)
    return float(a.mean()), float(a.std(ddof=1)) if len(a) > 1 else 0.0


def main() -> None:
    with open(RUNS_PATH) as fh:
        runs = json.load(fh)
    missing = [r for r in ORDER if r not in runs]
    if missing:
        raise SystemExit(f"runs missing: {missing}")

    # ---- exact-reproduction check: default_seed0 vs stored a2_port_results --
    with open(SEED0_PATH) as fh:
        s0 = json.load(fh)
    r0 = runs["default_seed0"]
    checks = [
        ("baseline acc", s0["baseline"]["test_accuracy"],
         r0["baseline"]["test_accuracy"]),
        ("baseline f1", s0["baseline"]["test_macro_f1"],
         r0["baseline"]["test_macro_f1"]),
        ("N(dst) acc drop", s0["N_dst_port_full_test"]["acc_drop_mean"],
         r0["N_dst_port_full_test"]["acc_drop_mean"]),
        ("N(dst) f1 drop", s0["N_dst_port_full_test"]["f1_drop_mean"],
         r0["N_dst_port_full_test"]["f1_drop_mean"]),
        ("shap rank", s0["shap_rank_dst_port"], r0["shap_rank_dst_port"]),
        ("N rank acc", s0["audit"]["N_rank_dst_port_acc"],
         r0["N_rank_dst_port_acc"]),
        ("FC acc-only count", s0["audit"]["false_confidence_acc_only"]["count"],
         r0["audit"]["false_confidence_acc_only"]["count"]),
        ("BF recall drop", s0["dst_port_per_class_recall_drop"]["Brute Force"],
         r0["dst_port_per_class_recall_drop"]["Brute Force"]),
    ]
    print("== exact-reproduction check: default_seed0 vs stored seed-0 JSON ==")
    repro_ok = True
    for name, a, b in checks:
        same = (a == b) if isinstance(a, int) else abs(a - b) < 1e-12
        repro_ok &= same
        print(f"  {name:20s} stored={a!r:<25} rerun={b!r:<25} "
              f"{'MATCH' if same else 'MISMATCH'}")
    print(f"  => {'EXACT REPRODUCTION' if repro_ok else 'MISMATCH (investigate)'}")

    # ---- per-run table ------------------------------------------------------
    cols = []
    print("\n== per-run parcel-D1 metrics ==")
    hdr = (f"{'run':16s} {'acc':>8s} {'N(dst)acc':>10s} {'Nrank':>5s} "
           f"{'NrankF1':>7s} {'SHAPrank':>8s} {'gini':>5s} {'FCacc':>5s} "
           f"{'FCdual':>6s} {'BFdrop':>8s} {'rho':>6s} {'P@10':>5s}")
    print(hdr)
    for rid in ORDER:
        r = runs[rid]
        fc = r["audit"]["false_confidence_acc_only"]["count"]
        fcd = r["audit"]["false_confidence_dual"]["count"]
        bf = r["dst_port_per_class_recall_drop"]["Brute Force"]
        row = dict(
            run=rid,
            acc=r["baseline"]["test_accuracy"],
            f1=r["baseline"]["test_macro_f1"],
            n_dst=r["N_dst_port_full_test"]["acc_drop_mean"],
            n_dst_sd=r["N_dst_port_full_test"]["acc_drop_std"],
            n_dst_f1=r["N_dst_port_full_test"]["f1_drop_mean"],
            n_rank=r["N_rank_dst_port_acc"],
            n_rank_f1=r["N_rank_dst_port_f1"],
            shap_rank=r["shap_rank_dst_port"],
            gini_rank=r["gini_rank_dst_port"],
            fc_acc=fc, fc_dual=fcd, bf_drop=bf,
            rho=r["audit"]["spearman_rho_shap_vs_N_acc"],
            p10=r["audit"]["precision_at_10_Nacc"],
        )
        cols.append(row)
        print(f"{rid:16s} {row['acc']:8.5f} {row['n_dst']:10.6f} "
              f"{row['n_rank']:5d} {row['n_rank_f1']:7d} {row['shap_rank']:8d} "
              f"{row['gini_rank']:5d} {fc:5d} {fcd:6d} {bf:8.4f} "
              f"{row['rho']:6.3f} {row['p10']:5.2f}")

    # ---- aggregate ----------------------------------------------------------
    def agg(key):
        return ms([c[key] for c in cols])

    n_dst_m, n_dst_s = agg("n_dst")
    n_dst_f1_m, n_dst_f1_s = agg("n_dst_f1")
    bf_m, bf_s = agg("bf_drop")
    shap_m, shap_s = agg("shap_rank")
    rho_m, rho_s = agg("rho")
    fc_m, fc_s = agg("fc_acc")
    acc_m, acc_s = agg("acc")
    f1_m, f1_s = agg("f1")

    print("\n== mean +/- sd over all 6 runs (4 seeds x default + 2 seeds x alt) ==")
    print(f"  baseline acc          {acc_m:.5f} +/- {acc_s:.5f}")
    print(f"  baseline macro-F1     {f1_m:.5f} +/- {f1_s:.5f}")
    print(f"  N(dst_port) acc drop  {n_dst_m:.5f} +/- {n_dst_s:.5f}")
    print(f"  N(dst_port) f1 drop   {n_dst_f1_m:.5f} +/- {n_dst_f1_s:.5f}")
    print(f"  BruteForce recall drp {bf_m:.4f} +/- {bf_s:.4f}")
    print(f"  SHAP rank dst_port    {shap_m:.2f} +/- {shap_s:.2f}  "
          f"(values: {[c['shap_rank'] for c in cols]})")
    print(f"  N_acc rank dst_port   values: {[c['n_rank'] for c in cols]}")
    print(f"  N_f1  rank dst_port   values: {[c['n_rank_f1'] for c in cols]}")
    print(f"  FC acc-only count     {fc_m:.2f} +/- {fc_s:.2f}  "
          f"(values: {[c['fc_acc'] for c in cols]})")
    print(f"  FC dual count         values: {[c['fc_dual'] for c in cols]}")
    print(f"  rho(SHAP, N_acc)      {rho_m:.3f} +/- {rho_s:.3f}")

    hold_rank1 = all(c["n_rank"] == 1 for c in cols)
    hold_buried = all(c["shap_rank"] >= 4 for c in cols)
    hold_fc = all(c["fc_acc"] >= 8 for c in cols)
    hold_bf = all(c["bf_drop"] > 0.25 for c in cols)
    print("\n== verdicts ==")
    print(f"  N_acc rank 1/52 in every run:            {hold_rank1}")
    print(f"  SHAP buries dst_port (rank >= 4) always: {hold_buried}")
    print(f"  FC acc-only >= 8/10 in every run:        {hold_fc}")
    print(f"  BruteForce collapse > 25pp in every run: {hold_bf}")

    runs["aggregate"] = {
        "runs_included": ORDER,
        "seed0_exact_reproduction": bool(repro_ok),
        "baseline_acc_mean_sd": [acc_m, acc_s],
        "baseline_f1_mean_sd": [f1_m, f1_s],
        "N_dst_port_acc_drop_mean_sd": [n_dst_m, n_dst_s],
        "N_dst_port_f1_drop_mean_sd": [n_dst_f1_m, n_dst_f1_s],
        "bruteforce_recall_drop_mean_sd": [bf_m, bf_s],
        "shap_rank_mean_sd": [shap_m, shap_s],
        "shap_rank_values": [c["shap_rank"] for c in cols],
        "gini_rank_values": [c["gini_rank"] for c in cols],
        "N_acc_rank_values": [c["n_rank"] for c in cols],
        "N_f1_rank_values": [c["n_rank_f1"] for c in cols],
        "fc_acc_only_count_mean_sd": [fc_m, fc_s],
        "fc_acc_only_count_values": [c["fc_acc"] for c in cols],
        "fc_dual_count_values": [c["fc_dual"] for c in cols],
        "rho_shap_Nacc_mean_sd": [rho_m, rho_s],
        "verdicts": {
            "N_rank1_every_run": hold_rank1,
            "shap_buries_rank_ge4_every_run": hold_buried,
            "fc_acc_only_ge8_every_run": hold_fc,
            "bruteforce_gt25pp_every_run": hold_bf,
        },
    }
    with open(RUNS_PATH, "w") as fh:
        json.dump(runs, fh, indent=2)
    print(f"\nwrote aggregate block into {RUNS_PATH}")


if __name__ == "__main__":
    main()
