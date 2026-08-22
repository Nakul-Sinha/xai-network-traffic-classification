"""
Unified benchmark driver: trains models, computes interventional ground truth (E3),
runs all explainers (E2/E4 attributions), and audits each explainer against N(F) with
a null-intervention control (E6). One pass per strength p, both model families.

This is the core results engine for the synthetic-benchmark half of the paper.

Output:
  results/audit_<p>.json    per-strength full record
  results/audit_summary.md  cross-strength audit tables (the paper's Table 2/3)

Usage:
  python run_audit.py --p 1.0
  python run_audit.py            (all strengths; slow, run in background)
"""
import warnings; warnings.filterwarnings("ignore")
import argparse, json, os, pickle, sys
import numpy as np
from scapy.all import IP

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from benchmark import models as M, groundtruth as GT, explainers as EX
from benchmark.generate import pkt_to_bytes

RES = os.path.join(HERE, "results"); os.makedirs(RES, exist_ok=True)
DATA = os.path.join(HERE, "data")
P_TAGS = {0.5: "p05", 0.7: "p07", 0.9: "p09", 1.0: "p10"}
# a field the generator never correlates with the label -> null-intervention control (E6)
NULL_FIELD = "tcp.sport"


def load(p):
    tag = P_TAGS[p]
    d = np.load(os.path.join(DATA, f"{tag}.npz"))
    raws = pickle.load(open(os.path.join(DATA, f"{tag}_pkts.pkl"), "rb"))
    return d["X"], d["y"], [IP(r) for r in raws]


def split(n, seed=0, frac=0.7):
    rng = np.random.default_rng(seed)
    idx = rng.permutation(n); k = int(frac * n)
    return idx[:k], idx[k:]


def run_p(p, seed=0):
    X, y, pkts = load(p)
    tr, te = split(len(X), seed)
    Xtr, ytr, Xte, yte = X[tr], y[tr], X[te], y[te]
    # Intervention-based ground truth is O(packets); 800 is ample for a 2-class accuracy
    # estimate (SE ~ 1.8%). Explainers and reported test accuracy use this same subset so
    # every number in a cell is on the same packets.
    GT_N = min(800, len(te))
    te_gt = te[:GT_N]
    Xte, yte = X[te_gt], y[te_gt]
    pkte = [pkts[i] for i in te_gt]
    sampler = GT.make_sampler(pkts, seed=seed + 1)
    rec = {"p": p, "seed": seed, "n_test": int(GT_N)}

    # ================= ByteCNN =================
    cnn = M.train_cnn(Xtr, ytr, epochs=40, seed=seed)
    rec["cnn_test_acc"] = round(M.cnn_acc(cnn, Xte, yte), 4)

    def eval_cnn(packets, yy):
        return M.cnn_acc(cnn, np.stack([pkt_to_bytes(pk) for pk in packets]), yy)

    base_c, N_c = GT.necessity(pkte, yte, eval_cnn, sampler)
    S_c = GT.sufficiency(pkte, yte, eval_cnn, sampler)
    R_c = GT.redundancy(pkte, yte, eval_cnn, sampler)
    # explainers (byte-level -> fields)
    cnn_expl = {
        "IntegratedGradients": EX.bytes_to_fields(EX.cnn_integrated_gradients(cnn, Xte)),
        "Saliency": EX.bytes_to_fields(EX.cnn_saliency(cnn, Xte)),
        "Occlusion": EX.bytes_to_fields(EX.cnn_occlusion(cnn, Xte, yte)),
    }
    try:
        cnn_expl["DeepSHAP"] = EX.bytes_to_fields(EX.cnn_deepshap(cnn, Xte, Xtr))
    except Exception as e:
        cnn_expl["DeepSHAP"] = {"_error": str(e)[:80]}
    rec["cnn"] = {
        "base_acc": round(base_c, 4), "N": N_c, "S": S_c, "R": len(R_c), "R_sets": R_c,
        "null_N": N_c.get(NULL_FIELD),
        "audit": {name: EX.audit(sc, N_c) for name, sc in cnn_expl.items() if "_error" not in sc},
        "attributions": cnn_expl,
    }

    # ================= RFFlow =================
    Ftr = np.stack([M.packet_to_features(pkts[i]) for i in tr])
    Fte = np.stack([M.packet_to_features(pk) for pk in pkte])
    rf = M.train_rf(Ftr, ytr, seed=seed)
    rec["rf_test_acc"] = round(M.rf_acc(rf, Fte, yte), 4)

    def eval_rf(packets, yy):
        return M.rf_acc(rf, np.stack([M.packet_to_features(pk) for pk in packets]), yy)

    base_r, N_r = GT.necessity(pkte, yte, eval_rf, sampler)
    S_r = GT.sufficiency(pkte, yte, eval_rf, sampler)
    R_r = GT.redundancy(pkte, yte, eval_rf, sampler)
    rf_expl = {"Impurity": EX.rf_scores_to_fields(EX.rf_impurity(rf))}
    try:
        rf_expl["TreeSHAP"] = EX.rf_scores_to_fields(EX.rf_treeshap(rf, Fte))
    except Exception as e:
        rf_expl["TreeSHAP"] = {"_error": str(e)[:80]}
    rec["rf"] = {
        "base_acc": round(base_r, 4), "N": N_r, "S": S_r, "R": len(R_r), "R_sets": R_r,
        "null_N": N_r.get(NULL_FIELD),
        "audit": {name: EX.audit(sc, N_r) for name, sc in rf_expl.items() if "_error" not in sc},
        "attributions": rf_expl,
    }
    return rec


def write_summary(records):
    L = ["# Audit summary: explainers vs interventional ground truth N(F)\n"]
    L.append("Planted artifacts ip.ttl + tcp.window (effective corr 0.5+0.5p); genuine weak "
             "signal payload length. Null-intervention control field: tcp.sport (should have N~0).\n")
    for fam, key in [("ByteCNN", "cnn"), ("RFFlow", "rf")]:
        L.append(f"## {fam}\n")
        L.append(f"### Ground truth")
        L.append("| p | test acc | N(ttl) | N(win) | N(payload) | N(null=sport) | R(M) |")
        L.append("|---|---|---|---|---|---|---|")
        for r in records:
            d = r[key]; acc = r[f"{key}_test_acc"]
            L.append(f"| {r['p']} | {acc} | {d['N'].get('ip.ttl')} | {d['N'].get('tcp.window')} "
                     f"| {d['N'].get('payload')} | {d['null_N']} | {d['R']} |")
        L.append("")
        L.append(f"### Explainer audit (rho / false-confidence / blind-spot)")
        # collect explainer names
        names = set()
        for r in records:
            names.update(r[key]["audit"].keys())
        for nm in sorted(names):
            L.append(f"**{nm}**")
            L.append("| p | rho | precision@2 | false-confidence | blind-spot |")
            L.append("|---|---|---|---|---|")
            for r in records:
                a = r[key]["audit"].get(nm)
                if a:
                    L.append(f"| {r['p']} | {a['rho']} | {a['precision_at_k']} "
                             f"| {a['false_confidence']} | {a['blind_spot']} |")
            L.append("")
    open(os.path.join(RES, "audit_summary.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--p", type=float, default=None)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()
    ps = [args.p] if args.p else [0.5, 0.7, 0.9, 1.0]
    records = []
    for p in ps:
        print(f"=== p={p} ===", flush=True)
        r = run_p(p, args.seed)
        records.append(r)
        suffix = "" if args.seed == 0 else f"_seed{args.seed}"
        json.dump(r, open(os.path.join(RES, f"audit_{P_TAGS[p]}{suffix}.json"), "w"), indent=2)
        c = r["cnn"]; rf = r["rf"]
        print(f"  CNN acc={r['cnn_test_acc']} N(ttl)={c['N'].get('ip.ttl')} "
              f"N(win)={c['N'].get('tcp.window')} N(null)={c['null_N']} R={c['R']}", flush=True)
        for nm, a in c["audit"].items():
            print(f"    CNN {nm}: rho={a['rho']} FC={a['false_confidence']} blind={a['blind_spot']}", flush=True)
        for nm, a in rf["audit"].items():
            print(f"    RF  {nm}: rho={a['rho']} FC={a['false_confidence']} blind={a['blind_spot']}", flush=True)
    write_summary(records)
    print("saved audit_*.json + audit_summary.md", flush=True)


if __name__ == "__main__":
    main()
