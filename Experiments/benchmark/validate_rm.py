"""
Validation of the corrected redundancy degree R(M) (paper contribution C2).

The removal-based `redundancy_legacy` cannot return R>1 and returns R=0 for a genuinely redundant
model (it reports LESS redundancy than a committed one). This script validates the corrected
sufficiency-based `redundancy()` on models with KNOWN redundancy structure, the way BAM/Bastings
validate attribution on known ground truth:

  * commit-oracle   uses only tcp.window                      -> true R = 1
  * redundant-oracle either ip.ttl OR tcp.window alone carries it (an ensemble whose two shortcuts
                    each clear the sufficiency threshold)      -> true R = 2
  * ttl-oracle      uses only ip.ttl                           -> true R = 1

and reports R(M) for the actually-trained ByteCNN / RandomForest at p=1.0.

Run: python validate_rm.py
Writes results/rm_validation.json and results/rm_validation.md
"""
import warnings; warnings.filterwarnings("ignore")
import json, os, sys
import numpy as np
from scapy.all import IP, TCP, Raw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from benchmark import models as M, groundtruth as GT
from benchmark.generate import pkt_to_bytes
from benchmark.run_audit import load, split

RES = os.path.join(HERE, "results")
PL_THRESH = 145  # midpoint of the class-conditional payload-length signal (120 vs 170)


def _feat(pk):
    ttl = pk[IP].ttl
    win = pk[TCP].window if pk.haslayer(TCP) else 0
    pl = len(pk[Raw].load) if pk.haslayer(Raw) else 0
    return ttl, win, pl


def commit_oracle(packets, y):
    pred = np.array([1 if _feat(pk)[1] == 65535 else 0 for pk in packets])
    return float(np.mean(pred == np.asarray(y)))


def ttl_oracle(packets, y):
    pred = np.array([1 if _feat(pk)[0] == 128 else 0 for pk in packets])
    return float(np.mean(pred == np.asarray(y)))


def redundant_oracle(packets, y):
    # Two NON-interfering shortcuts: trust the two markers when they agree; when a resampled marker
    # makes them disagree, fall back to the weak genuine payload signal. Either shortcut alone then
    # recovers ~85% (well above the 50%-skill threshold), so {ttl} and {window} are each sufficient.
    preds = []
    for pk in packets:
        ttl, win, pl = _feat(pk)
        a = 1 if ttl == 128 else 0
        b = 1 if win == 65535 else 0
        preds.append(a if a == b else (1 if pl > PL_THRESH else 0))
    return float(np.mean(np.array(preds) == np.asarray(y)))


def rm(evaluate, pkts, y, sampler):
    legacy = GT.redundancy_legacy(pkts, y, evaluate, sampler)
    new = GT.redundancy(pkts, y, evaluate, sampler)
    return {"base_acc": round(evaluate(pkts, y), 4),
            "legacy_R": len(legacy), "legacy_sets": legacy,
            "new_R": len(new), "new_sets": new}


def main():
    X, y, pkts = load(1.0)
    tr, te = split(len(X), seed=0)
    te = te[:800]
    pkte = [pkts[i] for i in te]
    yte = y[te]
    sampler = GT.make_sampler(pkts, seed=1)

    out = {"p": 1.0, "n_test": len(te), "suff_frac": 0.5, "pl_thresh": PL_THRESH, "cases": {}}

    print("=== oracle validation (known ground-truth R) ===", flush=True)
    for name, ev, true_R in [("commit_oracle(window only)", commit_oracle, 1),
                             ("ttl_oracle(ttl only)", ttl_oracle, 1),
                             ("redundant_oracle(ttl OR window)", redundant_oracle, 2)]:
        r = rm(ev, pkte, yte, sampler)
        r["true_R"] = true_R
        out["cases"][name] = r
        print(f"{name:36s} true R={true_R}  legacy_R={r['legacy_R']}  new_R={r['new_R']}  "
              f"sets={r['new_sets']}  acc={r['base_acc']}", flush=True)

    print("\n=== R(M) vs sufficiency threshold (corrected algorithm) ===", flush=True)
    sweep = {}
    fracs = [0.3, 0.4, 0.5, 0.6, 0.7]
    for name, ev in [("commit_oracle", commit_oracle), ("redundant_oracle", redundant_oracle)]:
        row = {str(sf): len(GT.redundancy(pkte, yte, ev, sampler, suff_frac=sf)) for sf in fracs}
        sweep[name] = row
        print(f"{name:20s} " + "  ".join(f"sf={sf}:R={row[str(sf)]}" for sf in fracs), flush=True)
    out["threshold_sweep"] = sweep

    print("\n=== trained models at p=1.0 ===", flush=True)
    Xtr, ytr = X[tr], y[tr]
    cnn = M.train_cnn(Xtr, ytr, epochs=40, seed=0)

    def eval_cnn(packets, yy):
        return M.cnn_acc(cnn, np.stack([pkt_to_bytes(pk) for pk in packets]), yy)

    Ftr = np.stack([M.packet_to_features(pkts[i]) for i in tr])
    rf = M.train_rf(Ftr, ytr, seed=0)

    def eval_rf(packets, yy):
        return M.rf_acc(rf, np.stack([M.packet_to_features(pk) for pk in packets]), yy)

    for name, ev in [("trained_ByteCNN", eval_cnn), ("trained_RandomForest", eval_rf)]:
        r = rm(ev, pkte, yte, sampler)
        out["cases"][name] = r
        print(f"{name:36s} legacy_R={r['legacy_R']}  new_R={r['new_R']}  sets={r['new_sets']}  "
              f"acc={r['base_acc']}", flush=True)

    os.makedirs(RES, exist_ok=True)
    json.dump(out, open(os.path.join(RES, "rm_validation.json"), "w"), indent=2)

    L = ["# R(M) validation: legacy (removal) vs corrected (sufficiency)\n",
         f"p=1.0, n_test={len(te)}, sufficiency fraction={out['suff_frac']} "
         f"(a set must recover >= 50% of above-chance skill).\n",
         "| model | true R | legacy R | corrected R | corrected sets |",
         "|---|---|---|---|---|"]
    for name, r in out["cases"].items():
        L.append(f"| {name} | {r.get('true_R','?')} | {r['legacy_R']} | {r['new_R']} | "
                 f"{r['new_sets']} |")
    open(os.path.join(RES, "rm_validation.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")
    print("\nsaved results/rm_validation.json + rm_validation.md", flush=True)


if __name__ == "__main__":
    main()
