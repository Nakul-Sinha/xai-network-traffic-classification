"""
Complete the C3 explainer matrix: KernelSHAP + LIME on the p=1.0 ByteCNN,
audited against the SAME interventional ground truth N(F) as run_audit.py
(same split seed, same sampler seed, same 800-packet test subset), so the new
rows are directly comparable with the existing audit_p10.json numbers.

Also reports wall-clock seconds per 100 explained samples for each method --
the line-rate-cost datapoint.

Output: results/extra_explainers.json + results/extra_explainers.md

Usage:  python run_extra.py [--p 1.0] [--n-explain 150]
"""
import warnings; warnings.filterwarnings("ignore")
import argparse, json, os, pickle, sys
import numpy as np
from scapy.all import IP

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from benchmark import models as M, groundtruth as GT, explainers as EX
from benchmark import explainers_extra as EXX
from benchmark.generate import pkt_to_bytes
from benchmark.run_audit import load, split, P_TAGS, NULL_FIELD

RES = os.path.join(HERE, "results"); os.makedirs(RES, exist_ok=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--p", type=float, default=1.0)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--n-explain", type=int, default=150)
    args = ap.parse_args()
    p, seed = args.p, args.seed

    X, y, pkts = load(p)
    tr, te = split(len(X), seed)
    Xtr, ytr = X[tr], y[tr]
    GT_N = min(800, len(te))
    te_gt = te[:GT_N]
    Xte, yte = X[te_gt], y[te_gt]
    pkte = [pkts[i] for i in te_gt]
    sampler = GT.make_sampler(pkts, seed=seed + 1)

    print(f"=== extra explainers, p={p}, seed={seed}, n_explain={args.n_explain} ===", flush=True)
    cnn = M.train_cnn(Xtr, ytr, epochs=40, seed=seed)
    acc = M.cnn_acc(cnn, Xte, yte)
    print(f"CNN test acc = {acc:.4f}", flush=True)

    def eval_cnn(packets, yy):
        return M.cnn_acc(cnn, np.stack([pkt_to_bytes(pk) for pk in packets]), yy)

    base_c, N_c = GT.necessity(pkte, yte, eval_cnn, sampler)
    print(f"base acc = {base_c:.4f}")
    print("N(F):", {k: v for k, v in N_c.items()}, flush=True)

    rec = {"p": p, "seed": seed, "n_test": int(GT_N), "cnn_test_acc": round(acc, 4),
           "base_acc": round(base_c, 4), "N": N_c, "null_N": N_c.get(NULL_FIELD),
           "n_explain": args.n_explain, "explainers": {}}

    # ---- KernelSHAP ----
    print("running KernelSHAP ...", flush=True)
    ks_bytes, ks_dt, ks_n = EXX.cnn_kernelshap(cnn, Xte, Xtr, n_explain=args.n_explain, seed=seed)
    ks_fields = EX.bytes_to_fields(ks_bytes)
    ks_audit = EX.audit(ks_fields, N_c)
    ks_per100 = ks_dt / ks_n * 100
    rec["explainers"]["KernelSHAP"] = {
        "fields": ks_fields, "audit": ks_audit,
        "runtime_s": round(ks_dt, 2), "n_explained": ks_n,
        "s_per_100_samples": round(ks_per100, 2)}
    print(f"KernelSHAP: {ks_dt:.1f}s for {ks_n} samples ({ks_per100:.1f}s/100) "
          f"rho={ks_audit['rho']} FC={ks_audit['false_confidence']} "
          f"blind={ks_audit['blind_spot']}", flush=True)

    # ---- LIME ----
    print("running LIME ...", flush=True)
    lm_bytes, lm_dt, lm_n = EXX.cnn_lime(cnn, Xte, Xtr, n_explain=args.n_explain, seed=seed)
    lm_fields = EX.bytes_to_fields(lm_bytes)
    lm_audit = EX.audit(lm_fields, N_c)
    lm_per100 = lm_dt / lm_n * 100
    rec["explainers"]["LIME"] = {
        "fields": lm_fields, "audit": lm_audit,
        "runtime_s": round(lm_dt, 2), "n_explained": lm_n,
        "s_per_100_samples": round(lm_per100, 2)}
    print(f"LIME: {lm_dt:.1f}s for {lm_n} samples ({lm_per100:.1f}s/100) "
          f"rho={lm_audit['rho']} FC={lm_audit['false_confidence']} "
          f"blind={lm_audit['blind_spot']}", flush=True)

    json.dump(rec, open(os.path.join(RES, "extra_explainers.json"), "w"), indent=2)

    # ---- markdown report ----
    L = ["# Extra explainers (C3 completion): KernelSHAP + LIME on the p=%.1f ByteCNN\n" % p]
    L.append(f"Same protocol as `run_audit.py`: split seed {seed}, sampler seed {seed+1}, "
             f"test subset n={GT_N}. CNN test acc {acc:.4f}. Ground truth N(F) recomputed "
             f"on this run (PacketDO resampling); null control N({NULL_FIELD}) = "
             f"{N_c.get(NULL_FIELD)}.\n")
    L.append("## Ground truth N(F) for this cell\n")
    L.append("| field | N(F) |")
    L.append("|---|---|")
    for f, v in sorted(N_c.items(), key=lambda kv: -kv[1]):
        L.append(f"| {f} | {v} |")
    L.append("")
    L.append("## Audit vs N(F)\n")
    L.append("| explainer | rho | precision@2 | false-confidence | blind-spot | "
             "n explained | runtime (s) | s / 100 samples |")
    L.append("|---|---|---|---|---|---|---|---|")
    for nm in ["KernelSHAP", "LIME"]:
        d = rec["explainers"][nm]; a = d["audit"]
        L.append(f"| {nm} | {a['rho']} | {a['precision_at_k']} | {a['false_confidence']} "
                 f"| {a['blind_spot']} | {d['n_explained']} | {d['runtime_s']} "
                 f"| {d['s_per_100_samples']} |")
    L.append("")
    L.append("## Field attributions (aggregated from per-byte scores)\n")
    for nm in ["KernelSHAP", "LIME"]:
        d = rec["explainers"][nm]
        L.append(f"**{nm}** (named = >= 0.2 * max): {d['audit']['named']}")
        L.append("")
        L.append("| field | score |")
        L.append("|---|---|")
        for f, v in sorted(d["fields"].items(), key=lambda kv: -kv[1]):
            L.append(f"| {f} | {v:.6g} |")
        L.append("")
    L.append("## Runtime note (line-rate-cost angle)\n")
    ks, lm = rec["explainers"]["KernelSHAP"], rec["explainers"]["LIME"]
    L.append(f"KernelSHAP: {ks['s_per_100_samples']} s / 100 packets; "
             f"LIME: {lm['s_per_100_samples']} s / 100 packets, on an RTX 4050 laptop GPU "
             f"with a batched predict_proba. For comparison, gradient methods in "
             f"`run_audit.py` explain 400 samples in well under a second. Perturbation "
             f"explainers are orders of magnitude away from line rate even on an 80-byte "
             f"toy window.\n")
    open(os.path.join(RES, "extra_explainers.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")
    print("saved results/extra_explainers.json + extra_explainers.md", flush=True)


if __name__ == "__main__":
    main()
