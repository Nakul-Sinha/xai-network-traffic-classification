"""a2_port_artifact.py - Parcel A2: Destination-Port artifact as real-data ground truth.

Track B / E4 (phase.md): the documented Destination-Port shortcut in CIC-IDS2017
(DATASET.md: DoS/DDoS/Web Attacks 100% on port 80, Brute Force on 21/22, etc.)
is used as *natural* ground truth to audit explainer faithfulness on real data.

Pipeline
  1. Load flows via load_cicids.get_flows() (Parcel A1 loader + hygiene).
  2. Stratified subsample (SUBSAMPLE_N) -> stratified 70/30 train/test split.
  3. Train RandomForest (CPU only, seeded).
  4. Interventional necessity N(f) for EVERY feature f: feature-space do() =
     permute ONLY column f in the (held-out) evaluation set, i.e. resample from
     the pooled empirical marginal, breaking f's dependence on everything else;
     N(f) = baseline_accuracy - mean permuted accuracy over R repeats.
     This is the real-data analogue of the synthetic N(F).
       - all 52 features: R=R_ALL repeats on a stratified N_EVAL subset of test
       - Destination Port headline: R=R_PORT repeats on the FULL test set,
         with per-class recall drops.
  5. Explainer side: (a) RF impurity importances; (b) TreeSHAP
     (tree_path_dependent, the field's common default) on N_SHAP stratified
     test rows; global importance = mean |SHAP| over samples and classes.
  6. Audit: SHAP rank of dst_port vs its necessity rank; Spearman rho between
     SHAP importance and N(f) across all features; precision@k; false-confidence
     features (SHAP top-K with N(f) ~ 0); blind spots (N top-K unnamed by SHAP).
  7. Redundancy probe (phase.md sec 6, field-set necessity): for each
     false-confidence feature, joint-permute it WITH its most-rank-correlated
     partner(s) (same row permutation -> preserves their joint distribution,
     breaks dependence on the rest) and compare group necessity to the singles.
     Also reports the Engelen flow-construction quartet as a documented group.

Outputs: results/a2_port_results.json (all numbers), console log.
Runtime: ~20-40 min CPU. Everything seeded (SEED).
"""

from __future__ import annotations

import json
import os
import sys
import time

import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, f1_score, recall_score
from sklearn.model_selection import train_test_split

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from load_cicids import ARTIFACT_COLUMNS, get_flows  # noqa: E402

# ----------------------------- configuration --------------------------------
SEED = 0
SUBSAMPLE_N = int(os.environ.get("A2_SUBSAMPLE_N", 700_000))  # of 2,520,751
TEST_FRAC = 0.30
N_EVAL = int(os.environ.get("A2_N_EVAL", 50_000))    # per-feature N(f) subset
R_ALL = int(os.environ.get("A2_R_ALL", 5))           # repeats, all features
R_PORT = int(os.environ.get("A2_R_PORT", 10))        # repeats, dst_port on full test
N_SHAP = int(os.environ.get("A2_N_SHAP", 1_000))     # rows explained by TreeSHAP
TOP_K = 10                                           # audit window
FC_EPS = 0.002   # N(f) below this (=0.2 pp accuracy) counts as ~zero necessity
RESULTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")
DST = "Destination Port"

rng_global = np.random.default_rng(SEED)


def log(msg: str) -> None:
    print(f"[a2 +{time.time() - T0:7.1f}s] {msg}", flush=True)


def stratified_take(X: np.ndarray, y: np.ndarray, n: int, seed: int):
    """Stratified subset of size ~n (all rows of classes too small to split)."""
    if n >= len(y):
        return X, y
    Xs, _, ys, _ = train_test_split(
        X, y, train_size=n, stratify=y, random_state=seed)
    return Xs, ys


def necessity(model, X_eval: np.ndarray, y_eval: np.ndarray, cols: list[int],
              repeats: int, seed: int, base_acc: float, base_f1: float):
    """N(cols): permute the listed columns with ONE shared row permutation per
    repeat (single col -> marginal resample do(); multiple cols -> group do()
    preserving within-group joint dist). Returns dict of drops."""
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
        "acc_perm_mean": float(np.mean(accs)),
        "f1_perm_mean": float(np.mean(f1s)),
    }


T0 = time.time()
os.makedirs(RESULTS_DIR, exist_ok=True)

# ----------------------------- 1. load + split ------------------------------
log("loading CIC-IDS2017 flows (Parcel A1 loader)...")
X_df, y_ser, feature_names = get_flows()
assert DST in feature_names, f"{DST!r} missing from features"
dst_idx = feature_names.index(DST)
log(f"loaded {len(X_df):,} flows x {len(feature_names)} features")

X_all = X_df.to_numpy(dtype=np.float32)
y_all = y_ser.to_numpy()
del X_df, y_ser

X_sub, y_sub = stratified_take(X_all, y_all, SUBSAMPLE_N, SEED)
del X_all, y_all
X_tr, X_te, y_tr, y_te = train_test_split(
    X_sub, y_sub, test_size=TEST_FRAC, stratify=y_sub, random_state=SEED)
log(f"subsample {len(y_sub):,} -> train {len(y_tr):,} / test {len(y_te):,}")
class_counts = pd.Series(y_te).value_counts().to_dict()
log(f"test class counts: {class_counts}")

# ----------------------------- 2. train RF ----------------------------------
log("training RandomForest (100 trees, depth<=20, min_leaf=20, n_jobs=-1)...")
rf = RandomForestClassifier(
    n_estimators=100, max_depth=20, min_samples_leaf=20,
    n_jobs=-1, random_state=SEED)
rf.fit(X_tr, y_tr)
pred_te = rf.predict(X_te)
base_acc = accuracy_score(y_te, pred_te)
base_f1 = f1_score(y_te, pred_te, average="macro")
classes = sorted(np.unique(y_te).tolist())
base_recall = dict(zip(classes, recall_score(
    y_te, pred_te, labels=classes, average=None)))
log(f"baseline test accuracy {base_acc:.6f}  macro-F1 {base_f1:.6f}")

# ---------------------- 3. headline N(dst_port), full test ------------------
log(f"N(dst_port): permuting ONLY {DST!r} on FULL test set, R={R_PORT}...")
port_res = necessity(rf, X_te, y_te, [dst_idx], R_PORT, SEED + 1,
                     base_acc, base_f1)
# per-class recall drop (single representative permutation, seeded)
rng = np.random.default_rng(SEED + 2)
Xp = X_te.copy()
Xp[:, dst_idx] = Xp[rng.permutation(len(Xp)), dst_idx]
pred_p = rf.predict(Xp)
perm_recall = dict(zip(classes, recall_score(
    y_te, pred_p, labels=classes, average=None)))
recall_drop = {c: float(base_recall[c] - perm_recall[c]) for c in classes}
del Xp, pred_p
log(f"N(dst_port) acc drop = {port_res['acc_drop_mean']:.6f} "
    f"+/- {port_res['acc_drop_std']:.6f}; "
    f"macro-F1 drop = {port_res['f1_drop_mean']:.6f}")
log(f"per-class recall drop: { {c: round(v, 4) for c, v in recall_drop.items()} }")

# ---------------------- 4. N(f) for all features (eval subset) --------------
X_ev, y_ev = stratified_take(X_te, y_te, N_EVAL, SEED + 3)
pred_ev = rf.predict(X_ev)
ev_acc = accuracy_score(y_ev, pred_ev)
ev_f1 = f1_score(y_ev, pred_ev, average="macro")
log(f"eval subset {len(y_ev):,}: acc {ev_acc:.6f} macro-F1 {ev_f1:.6f}")
log(f"N(f) for all {len(feature_names)} features, R={R_ALL} on eval subset...")
N_all = {}
for j, fname in enumerate(feature_names):
    N_all[fname] = necessity(rf, X_ev, y_ev, [j], R_ALL, SEED + 10 + j,
                             ev_acc, ev_f1)
    if (j + 1) % 10 == 0:
        log(f"  ...{j + 1}/{len(feature_names)} features done")
N_mean = {f: N_all[f]["acc_drop_mean"] for f in feature_names}
N_f1 = {f: N_all[f]["f1_drop_mean"] for f in feature_names}
N_rank_order = sorted(feature_names, key=lambda f: -N_mean[f])
N_rank = {f: i + 1 for i, f in enumerate(N_rank_order)}
Nf1_rank_order = sorted(feature_names, key=lambda f: -N_f1[f])
Nf1_rank = {f: i + 1 for i, f in enumerate(Nf1_rank_order)}
log("top-10 by necessity N(f) [acc drop]: " + ", ".join(
    f"{f}={N_mean[f]:.4f}" for f in N_rank_order[:10]))
log("top-10 by necessity N(f) [macro-F1 drop]: " + ", ".join(
    f"{f}={N_f1[f]:.4f}" for f in Nf1_rank_order[:10]))

# ---------------------- 5a. RF impurity importances -------------------------
imp = dict(zip(feature_names, rf.feature_importances_.astype(float)))
imp_order = sorted(feature_names, key=lambda f: -imp[f])
imp_rank = {f: i + 1 for i, f in enumerate(imp_order)}
log(f"impurity rank of {DST!r}: {imp_rank[DST]} (importance {imp[DST]:.4f})")

# ---------------------- 5b. TreeSHAP ----------------------------------------
import shap  # deferred import; heavy  # noqa: E402

X_sh, y_sh = stratified_take(X_te, y_te, N_SHAP, SEED + 4)
log(f"TreeSHAP (tree_path_dependent) on {len(y_sh):,} stratified test rows...")
expl = shap.TreeExplainer(rf, feature_perturbation="tree_path_dependent")
sv = expl.shap_values(X_sh, check_additivity=False)
if isinstance(sv, list):                       # old API: list of (n, f) per class
    sv = np.stack(sv, axis=-1)                 # -> (n, f, c)
assert sv.ndim == 3 and sv.shape[1] == len(feature_names), sv.shape
shap_glob = np.abs(sv).mean(axis=(0, 2))       # mean |SHAP| over samples+classes
shap_imp = dict(zip(feature_names, shap_glob.astype(float)))
shap_order = sorted(feature_names, key=lambda f: -shap_imp[f])
shap_rank = {f: i + 1 for i, f in enumerate(shap_order)}
# per-class SHAP rank of dst_port
class_order = list(rf.classes_)
shap_rank_dst_per_class = {}
for ci, cname in enumerate(class_order):
    per_c = np.abs(sv[:, :, ci]).mean(axis=0)
    shap_rank_dst_per_class[str(cname)] = int(
        1 + (per_c > per_c[dst_idx]).sum())
log(f"SHAP global rank of {DST!r}: {shap_rank[DST]} "
    f"(mean|SHAP| {shap_imp[DST]:.5f}); per-class rank: {shap_rank_dst_per_class}")
log("SHAP top-10: " + ", ".join(
    f"{f}={shap_imp[f]:.5f}" for f in shap_order[:10]))

# ---------------------- 6. audit: SHAP vs necessity -------------------------
imp_vec = np.array([shap_imp[f] for f in feature_names])
n_vec = np.array([N_mean[f] for f in feature_names])
n_vec_f1 = np.array([N_f1[f] for f in feature_names])
rho, rho_p = spearmanr(imp_vec, n_vec)
rho_f1, rho_f1_p = spearmanr(imp_vec, n_vec_f1)
imp_vec_g = np.array([imp[f] for f in feature_names])
rho_gini, rho_gini_p = spearmanr(imp_vec_g, n_vec)
rho_gini_f1, _ = spearmanr(imp_vec_g, n_vec_f1)

topk_shap = set(shap_order[:TOP_K])
topk_N = set(N_rank_order[:TOP_K])
topk_Nf1 = set(Nf1_rank_order[:TOP_K])
prec_at_k = len(topk_shap & topk_N) / TOP_K
prec_at_5 = len(set(shap_order[:5]) & set(N_rank_order[:5])) / 5
prec_at_k_f1 = len(topk_shap & topk_Nf1) / TOP_K
prec_at_5_f1 = len(set(shap_order[:5]) & set(Nf1_rank_order[:5])) / 5

# false confidence: high SHAP rank but ~zero necessity under BOTH metrics
FC_EPS_F1 = 0.005
false_conf = [f for f in shap_order[:TOP_K]
              if N_mean[f] < FC_EPS and N_f1[f] < FC_EPS_F1]
blind = [f for f in N_rank_order[:TOP_K] if f not in topk_shap]
blind_f1 = [f for f in Nf1_rank_order[:TOP_K] if f not in topk_shap]
log(f"Spearman rho(SHAP, N_acc) = {rho:.4f} (p={rho_p:.2e}); "
    f"rho(SHAP, N_f1) = {rho_f1:.4f}; rho(gini, N_acc) = {rho_gini:.4f}; "
    f"rho(gini, N_f1) = {rho_gini_f1:.4f}")
log(f"precision@5 {prec_at_5:.2f} / @10 {prec_at_k:.2f} (N_acc); "
    f"@5 {prec_at_5_f1:.2f} / @10 {prec_at_k_f1:.2f} (N_f1)")
log(f"false-confidence features (SHAP top-{TOP_K}, N_acc<{FC_EPS} "
    f"and N_f1<{FC_EPS_F1}): {false_conf}")
log(f"blind spots (N_acc top-{TOP_K} not in SHAP top-{TOP_K}): {blind}")
log(f"blind spots (N_f1  top-{TOP_K} not in SHAP top-{TOP_K}): {blind_f1}")

# ---------------------- 7. redundancy probe ---------------------------------
# rank correlations on a 50k train sample
Xc, _ = stratified_take(X_tr, y_tr, 50_000, SEED + 5)
corr = pd.DataFrame(Xc, columns=feature_names).corr(method="spearman")
del Xc

group_results = {}
for f in false_conf:
    partners = corr[f].drop(index=f).abs().sort_values(ascending=False)
    top_partners = partners.index[:2].tolist()
    cols = [feature_names.index(c) for c in [f] + top_partners]
    res = necessity(rf, X_ev, y_ev, cols, R_ALL, SEED + 100, ev_acc, ev_f1)
    group_results[f] = {
        "partners": top_partners,
        "partner_abs_spearman": [float(partners[c]) for c in top_partners],
        "single_N": N_mean[f],
        "partner_single_N": [N_mean[c] for c in top_partners],
        "group_N_acc_drop": res["acc_drop_mean"],
        "group_N_f1_drop": res["f1_drop_mean"],
    }
    log(f"group do() for FC feature {f!r} + {top_partners}: "
        f"group N = {res['acc_drop_mean']:.4f} "
        f"(singles: {N_mean[f]:.4f}, "
        + ", ".join(f"{N_mean[c]:.4f}" for c in top_partners) + ")")

# packet-length redundant family (dominates SHAP top-k in pilot): group do()
PL_FAMILY = [f for f in feature_names
             if "Packet Length" in f or f in ("Average Packet Size",)]
pl_idx = [feature_names.index(c) for c in PL_FAMILY]
pl_group = necessity(rf, X_ev, y_ev, pl_idx, R_ALL, SEED + 300, ev_acc, ev_f1)
log(f"packet-length family ({len(PL_FAMILY)} cols) group do(): "
    f"group N_acc = {pl_group['acc_drop_mean']:.4f}, "
    f"group N_f1 = {pl_group['f1_drop_mean']:.4f} "
    f"(singles N_acc: " + ", ".join(f"{N_mean[c]:.4f}" for c in PL_FAMILY) + ")")

# documented Engelen flow-construction quartet as a group
fc_cols = [c for c in ARTIFACT_COLUMNS["flow_construction"] if c in feature_names]
fc_idx = [feature_names.index(c) for c in fc_cols]
fc_group = necessity(rf, X_ev, y_ev, fc_idx, R_ALL, SEED + 200, ev_acc, ev_f1)
log(f"Engelen flow-construction group {fc_cols}: "
    f"group N = {fc_group['acc_drop_mean']:.4f} "
    f"(singles: " + ", ".join(f"{N_mean[c]:.4f}" for c in fc_cols) + ")")

# ---------------------- 8. dump ---------------------------------------------
out = {
    "config": {
        "seed": SEED, "subsample_n": int(len(y_sub)), "test_frac": TEST_FRAC,
        "n_train": int(len(y_tr)), "n_test": int(len(y_te)),
        "n_eval_subset": int(len(y_ev)), "r_all": R_ALL, "r_port": R_PORT,
        "n_shap": int(len(y_sh)), "top_k": TOP_K, "fc_eps": FC_EPS,
        "fc_eps_f1": FC_EPS_F1,
        "rf": {"n_estimators": 100, "max_depth": 20, "min_samples_leaf": 20},
        "shap_mode": "tree_path_dependent",
    },
    "baseline": {
        "test_accuracy": base_acc, "test_macro_f1": base_f1,
        "per_class_recall": {c: float(v) for c, v in base_recall.items()},
        "test_class_counts": {str(k): int(v) for k, v in class_counts.items()},
        "eval_subset_accuracy": ev_acc, "eval_subset_macro_f1": ev_f1,
    },
    "N_dst_port_full_test": port_res,
    "dst_port_per_class_recall_drop": recall_drop,
    "N_all_features": N_all,
    "necessity_ranking": N_rank_order,
    "necessity_ranking_macro_f1": Nf1_rank_order,
    "impurity_importance": imp,
    "impurity_rank_dst_port": imp_rank[DST],
    "shap_global_importance": shap_imp,
    "shap_ranking": shap_order,
    "shap_rank_dst_port": shap_rank[DST],
    "shap_rank_dst_port_per_class": shap_rank_dst_per_class,
    "audit": {
        "spearman_rho_shap_vs_N_acc": float(rho), "spearman_p": float(rho_p),
        "spearman_rho_shap_vs_N_f1": float(rho_f1),
        "spearman_rho_shap_vs_N_f1_p": float(rho_f1_p),
        "spearman_rho_gini_vs_N_acc": float(rho_gini),
        "spearman_rho_gini_vs_N_f1": float(rho_gini_f1),
        "precision_at_5_Nacc": prec_at_5, "precision_at_10_Nacc": prec_at_k,
        "precision_at_5_Nf1": prec_at_5_f1, "precision_at_10_Nf1": prec_at_k_f1,
        "false_confidence_features": false_conf,
        "blind_spot_features_Nacc": blind,
        "blind_spot_features_Nf1": blind_f1,
        "N_rank_dst_port_acc": N_rank[DST],
        "N_rank_dst_port_f1": Nf1_rank[DST],
    },
    "redundancy_probe": group_results,
    "packet_length_family_group": {
        "columns": PL_FAMILY,
        "singles_N_acc": {c: N_mean[c] for c in PL_FAMILY},
        "singles_N_f1": {c: N_f1[c] for c in PL_FAMILY},
        "group_N_acc_drop": pl_group["acc_drop_mean"],
        "group_N_f1_drop": pl_group["f1_drop_mean"],
    },
    "engelen_flow_construction_group": {
        "columns": fc_cols,
        "singles_N": {c: N_mean[c] for c in fc_cols},
        "singles_N_f1": {c: N_f1[c] for c in fc_cols},
        "group_N_acc_drop": fc_group["acc_drop_mean"],
        "group_N_f1_drop": fc_group["f1_drop_mean"],
    },
    "runtime_seconds": time.time() - T0,
}
out_path = os.path.join(RESULTS_DIR, "a2_port_results.json")
with open(out_path, "w") as fh:
    json.dump(out, fh, indent=2)
log(f"wrote {out_path}")
log("DONE")
