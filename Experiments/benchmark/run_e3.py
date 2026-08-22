"""
E3: train per-p planted-shortcut models and verify (interventionally + behaviorally)
that they rely on the planted artifacts. Also emits N(F)/S(F)/R(M) ground-truth tables
(the reference the E2/E4 explainer audit will be scored against).

For each strength p in {0.5,0.7,0.9,1.0} and each model family {ByteCNN, RFFlow}:
  - train on a train split, report test accuracy
  - compute N(F), S(F) for candidate fields via PacketDO interventions
  - compute R(M) (disjoint sufficient sets)
  - behavioral check: does N(ip.ttl)+N(tcp.window) dominate N(payload) as p grows?

Output: results/e3_groundtruth.json + results/e3_table.md
Models saved to models/ (gitignored).

Usage: python run_e3.py            (all p, both families)
       python run_e3.py --p 1.0    (single strength)
"""
import warnings; warnings.filterwarnings("ignore")
import argparse, json, os, pickle, sys
import numpy as np
from scapy.all import IP

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from benchmark import models as M
from benchmark import groundtruth as GT
from benchmark.generate import pkt_to_bytes, WIN

RES = os.path.join(HERE, "results"); os.makedirs(RES, exist_ok=True)
MODELS = os.path.join(HERE, "models"); os.makedirs(MODELS, exist_ok=True)
DATA = os.path.join(HERE, "data")

P_TAGS = {0.5: "p05", 0.7: "p07", 0.9: "p09", 1.0: "p10"}


def load(p):
    tag = P_TAGS[p]
    d = np.load(os.path.join(DATA, f"{tag}.npz"))
    with open(os.path.join(DATA, f"{tag}_pkts.pkl"), "rb") as f:
        raws = pickle.load(f)
    pkts = [IP(r) for r in raws]
    return d["X"], d["y"], pkts


def split(n, seed=0, frac=0.7):
    rng = np.random.default_rng(seed)
    idx = rng.permutation(n)
    k = int(frac * n)
    return idx[:k], idx[k:]


def run_p(p, seed=0):
    X, y, pkts = load(p)
    tr, te = split(len(X), seed)
    Xtr, ytr, Xte, yte = X[tr], y[tr], X[te], y[te]
    pkte = [pkts[i] for i in te]
    yte_arr = y[te]
    sampler = GT.make_sampler(pkts, seed=seed + 1)

    out = {"p": p}

    # ---- ByteCNN ----
    cnn = M.train_cnn(Xtr, ytr, epochs=40, seed=seed)
    out["cnn_test_acc"] = round(M.cnn_acc(cnn, Xte, yte), 4)

    def eval_cnn(packets, yy):
        Xb = np.stack([pkt_to_bytes(pk) for pk in packets])
        return M.cnn_acc(cnn, Xb, yy)

    base_c, N_c = GT.necessity(pkte, yte_arr, eval_cnn, sampler)
    S_c = GT.sufficiency(pkte, yte_arr, eval_cnn, sampler)
    R_c = GT.redundancy(pkte, yte_arr, eval_cnn, sampler)
    out["cnn"] = {"base_acc_on_test_pkts": round(base_c, 4), "N": N_c, "S": S_c,
                  "R": len(R_c), "R_sets": R_c}

    # ---- RFFlow ----
    Ftr = np.stack([M.packet_to_features(pkts[i]) for i in tr])
    Fte = np.stack([M.packet_to_features(pkts[i]) for i in te])
    rf = M.train_rf(Ftr, ytr, seed=seed)
    out["rf_test_acc"] = round(M.rf_acc(rf, Fte, yte), 4)

    def eval_rf(packets, yy):
        Ff = np.stack([M.packet_to_features(pk) for pk in packets])
        return M.rf_acc(rf, Ff, yy)

    base_r, N_r = GT.necessity(pkte, yte_arr, eval_rf, sampler)
    S_r = GT.sufficiency(pkte, yte_arr, eval_rf, sampler)
    R_r = GT.redundancy(pkte, yte_arr, eval_rf, sampler)
    out["rf"] = {"base_acc_on_test_pkts": round(base_r, 4), "N": N_r, "S": S_r,
                 "R": len(R_r), "R_sets": R_r}

    return out


def write_table(results):
    lines = ["# E3: planted-shortcut ground truth (N/S/R per strength)\n"]
    lines.append("Planted artifacts: ip.ttl (A) and tcp.window (B), both class-correlated at "
                 "effective marginal 0.5+0.5p. Genuine weak signal: payload length.\n")
    for fam, key in [("ByteCNN (raw bytes)", "cnn"), ("RFFlow (named features)", "rf")]:
        lines.append(f"## {fam}\n")
        lines.append("| p | test acc | N(ip.ttl) | N(tcp.window) | N(payload) | R(M) |")
        lines.append("|---|---|---|---|---|---|")
        for r in results:
            d = r[key]
            lines.append(f"| {r['p']} | {r.get(key.replace('','')+'','')}"
                         f"{r['cnn_test_acc'] if key=='cnn' else r['rf_test_acc']} "
                         f"| {d['N'].get('ip.ttl')} | {d['N'].get('tcp.window')} "
                         f"| {d['N'].get('payload')} | {d['R']} |")
        lines.append("")
    open(os.path.join(RES, "e3_table.md"), "w", encoding="utf-8").write("\n".join(lines) + "\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--p", type=float, default=None)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()
    ps = [args.p] if args.p else [0.5, 0.7, 0.9, 1.0]
    results = []
    for p in ps:
        print(f"=== p={p} ===")
        r = run_p(p, args.seed)
        results.append(r)
        print(f"  CNN acc={r['cnn_test_acc']} N(ttl)={r['cnn']['N'].get('ip.ttl')} "
              f"N(win)={r['cnn']['N'].get('tcp.window')} N(payload)={r['cnn']['N'].get('payload')} R={r['cnn']['R']}")
        print(f"  RF  acc={r['rf_test_acc']} N(ttl)={r['rf']['N'].get('ip.ttl')} "
              f"N(win)={r['rf']['N'].get('tcp.window')} N(payload)={r['rf']['N'].get('payload')} R={r['rf']['R']}")
    json.dump(results, open(os.path.join(RES, "e3_groundtruth.json"), "w"), indent=2)
    write_table(results)
    print("saved e3_groundtruth.json + e3_table.md")


if __name__ == "__main__":
    main()
