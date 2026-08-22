"""a2_robustness.py - ORG-C fix #5: seed + RF-config robustness for Parcel A2.

The promoted A2 numbers (N(dst_port) rank 1/52, SHAP global rank 5/52,
Brute-Force recall -37.8pp, 9/10 acc-only false-confidence in SHAP's top-10)
were seed-0 single-config. This harness re-runs the *identical* pipeline of
a2_port_artifact.py (same constants, same per-stage seed offsets) as a slim
per-run function, across:

  - default RF config (100 trees, depth<=20, min_leaf=20): seeds 0, 1, 2, 3
    (seed 0 mirrors a2_port_artifact.py exactly and must reproduce
     results/a2_port_results.json -> built-in exact-reproduction check)
  - alternative RF config (100 trees, depth<=30, min_leaf=5): seeds 0, 1

Seed semantics: the run seed drives the FULL pipeline - stratified subsample,
train/test split, RF random_state, every permutation RNG (necessity), the
eval/SHAP subsets - via the same offsets as a2_port_artifact.py:
  subsample seed=S, split random_state=S, RF random_state=S,
  N(dst_port) full-test seed=S+1, recall permutation seed=S+2,
  eval subset seed=S+3, per-feature N(f) seed=S+10+j, SHAP subset seed=S+4.

Per run this records exactly the parcel-D1 metrics (plus context):
  N(dst_port) full-test acc/F1 drop, its rank among 52 features (acc and F1
  necessity, eval subset R=5), TreeSHAP global rank of dst_port, gini rank,
  acc-only false-confidence count+list in SHAP top-10 (N_acc < 0.002),
  dual-criterion FC set, Brute-Force (and all-class) recall drop,
  Spearman rho(SHAP, N_acc), precision@5/@10.

Skipped vs a2_port_artifact.py (not needed for fix #5): redundancy group
probes, packet-length family do(), Engelen quartet do().

Output: results/a2_robustness_runs.json, written incrementally after each run
(already-present run_ids are skipped on restart, so the script is resumable).
Usage: python a2_robustness.py [run_id ...]   (no args = all runs)
"""

from __future__ import annotations

import json
import os
import sys
import time

import numpy as np
from scipy.stats import spearmanr
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, f1_score, recall_score
from sklearn.model_selection import train_test_split

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from load_cicids import get_flows  # noqa: E402

# ---- constants: IDENTICAL to a2_port_artifact.py ----------------------------
SUBSAMPLE_N = 700_000
TEST_FRAC = 0.30
N_EVAL = 50_000
R_ALL = 5
R_PORT = 10
N_SHAP = 1_000
TOP_K = 10
FC_EPS = 0.002
FC_EPS_F1 = 0.005
DST = "Destination Port"
RESULTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")
OUT_PATH = os.path.join(RESULTS_DIR, "a2_robustness_runs.json")

DEFAULT_RF = {"n_estimators": 100, "max_depth": 20, "min_samples_leaf": 20}
ALT_RF = {"n_estimators": 100, "max_depth": 30, "min_samples_leaf": 5}

RUNS = [
    {"run_id": "default_seed0", "seed": 0, "rf": DEFAULT_RF},
    {"run_id": "default_seed1", "seed": 1, "rf": DEFAULT_RF},
    {"run_id": "default_seed2", "seed": 2, "rf": DEFAULT_RF},
    {"run_id": "default_seed3", "seed": 3, "rf": DEFAULT_RF},
    {"run_id": "alt_d30l5_seed0", "seed": 0, "rf": ALT_RF},
    {"run_id": "alt_d30l5_seed1", "seed": 1, "rf": ALT_RF},
]

T0 = time.time()


def log(msg: str) -> None:
    print(f"[a2rob +{time.time() - T0:7.1f}s] {msg}", flush=True)


def stratified_take(X, y, n, seed):
    if n >= len(y):
        return X, y
    Xs, _, ys, _ = train_test_split(X, y, train_size=n, stratify=y,
                                    random_state=seed)
    return Xs, ys


def necessity(model, X_eval, y_eval, cols, repeats, seed, base_acc, base_f1):
    accs, f1s = [], []
    rng = np.random.default_rng(seed)
    for _ in range(repeats):
        Xp = X_eval.copy()
        perm = rng.permutation(len(Xp))
        Xp[:, cols] = Xp[perm][:, cols]
        pred = model.predict(Xp)
        accs.append(accuracy_score(y_eval, pred))
        f1s.append(f1_score(y_eval, pred, average="macro"))
    return {
        "acc_drop_mean": float(base_acc - np.mean(accs)),
        "acc_drop_std": float(np.std(accs)),
        "f1_drop_mean": float(base_f1 - np.mean(f1s)),
        "f1_drop_std": float(np.std(f1s)),
    }


def one_run(X_all, y_all, feature_names, seed: int, rf_cfg: dict) -> dict:
    t_run = time.time()
    dst_idx = feature_names.index(DST)

    X_sub, y_sub = stratified_take(X_all, y_all, SUBSAMPLE_N, seed)
    X_tr, X_te, y_tr, y_te = train_test_split(
        X_sub, y_sub, test_size=TEST_FRAC, stratify=y_sub, random_state=seed)
    del X_sub, y_sub

    log(f"  train RF {rf_cfg} seed={seed} on {len(y_tr):,} rows...")
    rf = RandomForestClassifier(n_jobs=-1, random_state=seed, **rf_cfg)
    rf.fit(X_tr, y_tr)
    pred_te = rf.predict(X_te)
    base_acc = accuracy_score(y_te, pred_te)
    base_f1 = f1_score(y_te, pred_te, average="macro")
    classes = sorted(np.unique(y_te).tolist())
    base_recall = dict(zip(classes, recall_score(
        y_te, pred_te, labels=classes, average=None)))
    log(f"  baseline acc {base_acc:.6f} macro-F1 {base_f1:.6f}")

    # headline N(dst_port), full test, R=R_PORT (seed offset +1, as original)
    port_res = necessity(rf, X_te, y_te, [dst_idx], R_PORT, seed + 1,
                         base_acc, base_f1)
    # per-class recall drop, single representative permutation (offset +2)
    rng = np.random.default_rng(seed + 2)
    Xp = X_te.copy()
    Xp[:, dst_idx] = Xp[rng.permutation(len(Xp)), dst_idx]
    pred_p = rf.predict(Xp)
    perm_recall = dict(zip(classes, recall_score(
        y_te, pred_p, labels=classes, average=None)))
    recall_drop = {c: float(base_recall[c] - perm_recall[c]) for c in classes}
    del Xp, pred_p
    log(f"  N(dst_port) acc drop {port_res['acc_drop_mean']:.6f} "
        f"+/- {port_res['acc_drop_std']:.6f}; "
        f"BruteForce recall drop {recall_drop.get('Brute Force', float('nan')):.4f}")

    # N(f) for all features on stratified eval subset (offsets +3, +10+j)
    X_ev, y_ev = stratified_take(X_te, y_te, N_EVAL, seed + 3)
    pred_ev = rf.predict(X_ev)
    ev_acc = accuracy_score(y_ev, pred_ev)
    ev_f1 = f1_score(y_ev, pred_ev, average="macro")
    N_all = {}
    for j, fname in enumerate(feature_names):
        N_all[fname] = necessity(rf, X_ev, y_ev, [j], R_ALL, seed + 10 + j,
                                 ev_acc, ev_f1)
        if (j + 1) % 13 == 0:
            log(f"    ...N(f) {j + 1}/{len(feature_names)}")
    N_mean = {f: N_all[f]["acc_drop_mean"] for f in feature_names}
    N_f1 = {f: N_all[f]["f1_drop_mean"] for f in feature_names}
    N_rank_order = sorted(feature_names, key=lambda f: -N_mean[f])
    Nf1_rank_order = sorted(feature_names, key=lambda f: -N_f1[f])
    N_rank = {f: i + 1 for i, f in enumerate(N_rank_order)}
    Nf1_rank = {f: i + 1 for i, f in enumerate(Nf1_rank_order)}

    # gini
    imp = dict(zip(feature_names, rf.feature_importances_.astype(float)))
    imp_order = sorted(feature_names, key=lambda f: -imp[f])
    imp_rank = {f: i + 1 for i, f in enumerate(imp_order)}

    # TreeSHAP (offset +4)
    import shap  # deferred, heavy
    X_sh, y_sh = stratified_take(X_te, y_te, N_SHAP, seed + 4)
    t_sh = time.time()
    log(f"  TreeSHAP (tree_path_dependent) on {len(y_sh):,} rows...")
    expl = shap.TreeExplainer(rf, feature_perturbation="tree_path_dependent")
    sv = expl.shap_values(X_sh, check_additivity=False)
    if isinstance(sv, list):
        sv = np.stack(sv, axis=-1)
    assert sv.ndim == 3 and sv.shape[1] == len(feature_names), sv.shape
    shap_glob = np.abs(sv).mean(axis=(0, 2))
    shap_imp = dict(zip(feature_names, shap_glob.astype(float)))
    shap_order = sorted(feature_names, key=lambda f: -shap_imp[f])
    shap_rank = {f: i + 1 for i, f in enumerate(shap_order)}
    shap_secs = time.time() - t_sh
    log(f"  SHAP done in {shap_secs:.0f}s; global rank of dst_port: "
        f"{shap_rank[DST]}")

    # audit metrics
    imp_vec = np.array([shap_imp[f] for f in feature_names])
    n_vec = np.array([N_mean[f] for f in feature_names])
    n_vec_f1 = np.array([N_f1[f] for f in feature_names])
    rho, rho_p = spearmanr(imp_vec, n_vec)
    rho_f1, _ = spearmanr(imp_vec, n_vec_f1)
    topk_shap = shap_order[:TOP_K]
    prec_at_5 = len(set(shap_order[:5]) & set(N_rank_order[:5])) / 5
    prec_at_10 = len(set(topk_shap) & set(N_rank_order[:TOP_K])) / TOP_K
    false_conf_acc_only = [f for f in topk_shap if N_mean[f] < FC_EPS]
    false_conf_dual = [f for f in topk_shap
                       if N_mean[f] < FC_EPS and N_f1[f] < FC_EPS_F1]

    return {
        "seed": seed,
        "rf": rf_cfg,
        "n_train": int(len(y_tr)), "n_test": int(len(y_te)),
        "n_eval_subset": int(len(y_ev)), "n_shap": int(len(y_sh)),
        "baseline": {
            "test_accuracy": float(base_acc), "test_macro_f1": float(base_f1),
            "eval_subset_accuracy": float(ev_acc),
            "eval_subset_macro_f1": float(ev_f1),
            "per_class_recall": {c: float(v) for c, v in base_recall.items()},
        },
        "N_dst_port_full_test": port_res,
        "dst_port_per_class_recall_drop": recall_drop,
        "N_dst_port_eval_subset": {
            "acc_drop_mean": N_mean[DST], "f1_drop_mean": N_f1[DST]},
        "N_rank_dst_port_acc": N_rank[DST],
        "N_rank_dst_port_f1": Nf1_rank[DST],
        "necessity_top10_acc": [
            [f, N_mean[f]] for f in N_rank_order[:TOP_K]],
        "shap_rank_dst_port": shap_rank[DST],
        "shap_dst_port_mean_abs": shap_imp[DST],
        "shap_top10": [[f, shap_imp[f]] for f in topk_shap],
        "gini_rank_dst_port": imp_rank[DST],
        "audit": {
            "spearman_rho_shap_vs_N_acc": float(rho),
            "spearman_p": float(rho_p),
            "spearman_rho_shap_vs_N_f1": float(rho_f1),
            "precision_at_5_Nacc": prec_at_5,
            "precision_at_10_Nacc": prec_at_10,
            "false_confidence_acc_only": {
                "criterion": f"N_acc < {FC_EPS}",
                "features": false_conf_acc_only,
                "count": len(false_conf_acc_only),
            },
            "false_confidence_dual": {
                "criterion": f"N_acc < {FC_EPS} and N_f1 < {FC_EPS_F1}",
                "features": false_conf_dual,
                "count": len(false_conf_dual),
            },
        },
        "N_acc_of_shap_top10": {f: N_mean[f] for f in topk_shap},
        "N_f1_of_shap_top10": {f: N_f1[f] for f in topk_shap},
        "runtime_seconds": time.time() - t_run,
        "shap_seconds": shap_secs,
    }


def main() -> None:
    os.makedirs(RESULTS_DIR, exist_ok=True)
    wanted = set(sys.argv[1:]) or {r["run_id"] for r in RUNS}
    store = {}
    if os.path.exists(OUT_PATH):
        with open(OUT_PATH) as fh:
            store = json.load(fh)
        log(f"resuming: {sorted(store)} already on disk")

    todo = [r for r in RUNS if r["run_id"] in wanted
            and r["run_id"] not in store]
    if not todo:
        log("nothing to do")
        return

    log("loading CIC-IDS2017 flows once for all runs...")
    X_df, y_ser, feature_names = get_flows()
    X_all = X_df.to_numpy(dtype=np.float32)
    y_all = y_ser.to_numpy()
    del X_df, y_ser
    log(f"loaded {len(y_all):,} x {len(feature_names)}")

    for spec in todo:
        log(f"=== RUN {spec['run_id']} (seed {spec['seed']}, rf {spec['rf']}) ===")
        rec = one_run(X_all, y_all, feature_names, spec["seed"], spec["rf"])
        store[spec["run_id"]] = rec
        with open(OUT_PATH, "w") as fh:
            json.dump(store, fh, indent=2)
        log(f"=== {spec['run_id']} done in {rec['runtime_seconds']:.0f}s; "
            f"N_rank_acc={rec['N_rank_dst_port_acc']} "
            f"shap_rank={rec['shap_rank_dst_port']} "
            f"FC_acc_only={rec['audit']['false_confidence_acc_only']['count']}"
            f"/10; wrote {OUT_PATH} ===")
    log("ALL DONE")


if __name__ == "__main__":
    main()
