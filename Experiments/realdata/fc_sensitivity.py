"""
Phase C: threshold sensitivity of the real-data false-confidence result.

Reviewer concern: the headline "9 of TreeSHAP's top 10 are false-confident" uses a single
necessity cutoff (FC_EPS = 0.002 accuracy) and collapses to 0-1/10 under a dual accuracy+F1
criterion. This script sweeps the cutoff and reports the false-confidence count among the top-10
SHAP features as a function of it, so the reader sees the full curve instead of one hand-picked
point. It reads the committed a2_port_results.json (no retraining).

Writes results/fc_sensitivity.json, results/fc_sensitivity.md, and figure fc_sensitivity.png.
"""
import json, os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "results")
d = json.load(open(os.path.join(RES, "a2_port_results.json")))

shap = d["shap_global_importance"]
Nall = d["N_all_features"]
top10 = [f for f, _ in sorted(shap.items(), key=lambda kv: -kv[1])[:10]]

# per-feature necessity for the top-10 SHAP features
def n_acc(f): return Nall[f]["acc_drop_mean"]
def n_f1(f):  return Nall[f]["f1_drop_mean"]

print("Top-10 SHAP features (real data), with interventional necessity:")
for f in top10:
    print(f"  {f:32s}  N_acc={n_acc(f):.5f}  N_f1={n_f1(f):.5f}")

# --- sweep accuracy cutoff (accuracy-only false confidence) ---
eps_acc_list = [0.0005, 0.001, 0.002, 0.005, 0.01, 0.02, 0.05]
eps_f1_fixed = 0.005
acc_only = []
dual = []
for eps in eps_acc_list:
    fc_a = sum(1 for f in top10 if n_acc(f) < eps)
    fc_d = sum(1 for f in top10 if n_acc(f) < eps and n_f1(f) < eps_f1_fixed)
    acc_only.append(fc_a)
    dual.append(fc_d)

# --- sweep F1 cutoff at fixed accuracy cutoff 0.002 ---
eps_f1_list = [0.001, 0.002, 0.005, 0.01, 0.02, 0.05]
dual_vs_f1 = []
for eps_f1 in eps_f1_list:
    fc = sum(1 for f in top10 if n_acc(f) < 0.002 and n_f1(f) < eps_f1)
    dual_vs_f1.append(fc)

out = {
    "top10_shap": top10,
    "top10_necessity": {f: {"N_acc": n_acc(f), "N_f1": n_f1(f)} for f in top10},
    "eps_acc_list": eps_acc_list,
    "fc_accuracy_only": acc_only,
    "fc_dual_at_f1_0.005": dual,
    "eps_f1_list": eps_f1_list,
    "fc_dual_vs_f1_at_acc_0.002": dual_vs_f1,
    "paper_point_acc_only_at_0.002": acc_only[eps_acc_list.index(0.002)],
    "paper_point_dual_at_0.002_0.005": dual[eps_acc_list.index(0.002)],
}
json.dump(out, open(os.path.join(RES, "fc_sensitivity.json"), "w"), indent=2)

# --- markdown ---
L = ["# Real-data false-confidence: threshold sensitivity (top-10 SHAP features)\n",
     "Accuracy-only FC = # of top-10 SHAP features with N_acc < eps_acc.",
     "Dual FC = also requires N_f1 < eps_f1.\n",
     "## Accuracy-only vs dual (eps_f1 = 0.005), swept over eps_acc",
     "| eps_acc | FC (acc-only) /10 | FC (dual) /10 |", "|---|---|---|"]
for e, a, dd in zip(eps_acc_list, acc_only, dual):
    L.append(f"| {e} | {a} | {dd} |")
L += ["", "## Dual FC vs eps_f1 (eps_acc fixed at 0.002)",
      "| eps_f1 | FC (dual) /10 |", "|---|---|"]
for e, v in zip(eps_f1_list, dual_vs_f1):
    L.append(f"| {e} | {v} |")
L += ["", "## Top-10 SHAP features and their necessity",
      "| feature | N_acc | N_f1 |", "|---|---|---|"]
for f in top10:
    L.append(f"| {f} | {n_acc(f):.5f} | {n_f1(f):.5f} |")
open(os.path.join(RES, "fc_sensitivity.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")

# --- figure ---
fig, ax = plt.subplots(1, 2, figsize=(9, 3.4))
ax[0].plot(eps_acc_list, acc_only, "o-", label="accuracy-only")
ax[0].plot(eps_acc_list, dual, "s--", label="dual (F1<0.005)")
ax[0].axvline(0.002, color="grey", ls=":", lw=1)
ax[0].set_xscale("log"); ax[0].set_xlabel("necessity cutoff eps_acc")
ax[0].set_ylabel("false-confident features (of top-10)")
ax[0].set_title("FC vs accuracy cutoff"); ax[0].legend(); ax[0].set_ylim(-0.3, 10.3)
ax[1].plot(eps_f1_list, dual_vs_f1, "d-", color="C3")
ax[1].set_xscale("log"); ax[1].set_xlabel("F1 cutoff eps_f1 (acc cutoff=0.002)")
ax[1].set_ylabel("dual false-confident features")
ax[1].set_title("dual FC vs F1 cutoff"); ax[1].set_ylim(-0.3, 10.3)
fig.tight_layout()
fig.savefig(os.path.join(HERE, "..", "figures", "fc_sensitivity.png"), dpi=150)

print("\nAccuracy-only FC by eps_acc:", dict(zip(eps_acc_list, acc_only)))
print("Dual FC (f1<0.005) by eps_acc:", dict(zip(eps_acc_list, dual)))
print("Dual FC vs eps_f1 (acc<0.002):", dict(zip(eps_f1_list, dual_vs_f1)))
print("saved fc_sensitivity.json/.md and figures/fc_sensitivity.png")
