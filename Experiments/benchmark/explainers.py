"""
Explainer wrappers + the audit metrics that score attributions against interventional
ground truth N(F).

Explainers produce per-feature importance in the model's OWN representation:
  ByteCNN -> per-byte importance (WIN scores) -> aggregated to fields via the offset map
  RFFlow  -> per-feature importance (len(RF_FEATURES)) -> mapped to field names

Audit metrics (per model x dataset cell), comparing an explainer's field ranking to the
N(F) ranking:
  rho              : Spearman correlation(attribution_field_score, N(field))
  precision_at_k   : |top-k attribution ∩ {F: N(F)>tau}| / k
  false_confidence : fraction of top-k attributed fields whose N(F) ~ 0 (named-but-unused)
  blind_spot       : fraction of {F: N(F)>tau} not in the explainer's top-k (used-but-unnamed)
"""
import warnings; warnings.filterwarnings("ignore")
import numpy as np
import torch
from scipy.stats import spearmanr

from benchmark import models as M
from benchmark.groundtruth import CANDIDATE_FIELDS

# byte-offset map for aggregating per-byte CNN attributions to fields (IP20+TCP20 layout)
BYTE_FIELD_OFFSETS = {
    "ip.ttl": [8], "ip.id": [4, 5], "ip.src": [12, 13, 14, 15], "ip.dst": [16, 17, 18, 19],
    "tcp.sport": [20, 21], "tcp.dport": [22, 23], "tcp.seq": [24, 25, 26, 27],
    "tcp.window": [34, 35], "tcp.flags": [33], "payload": list(range(40, 80)),
}


# ----------------------------- CNN explainers (byte-level) -----------------------------
def cnn_integrated_gradients(m, X, target=1, steps=32):
    x = torch.tensor(X[:400], dtype=torch.float32, device=M.DEVICE, requires_grad=True)
    base = torch.zeros_like(x)
    total = torch.zeros_like(x)
    for a in np.linspace(0, 1, steps):
        xi = (base + a * (x - base)).clone().detach().requires_grad_(True)
        out = m(xi)[:, target].sum()
        g = torch.autograd.grad(out, xi)[0]
        total = total + g / steps
    ig = ((x - base) * total).detach().cpu().numpy()
    return np.abs(ig).mean(0)


def cnn_saliency(m, X, target=1):
    x = torch.tensor(X[:400], dtype=torch.float32, device=M.DEVICE, requires_grad=True)
    out = m(x)[:, target].sum()
    g = torch.autograd.grad(out, x)[0]
    return np.abs(g.detach().cpu().numpy()).mean(0)


def cnn_occlusion(m, X, y, target=1):
    base = M.cnn_acc(m, X, y)
    imp = np.zeros(X.shape[1])
    rng = np.random.default_rng(0)
    for b in range(X.shape[1]):
        Xa = X.copy()
        Xa[:, b] = rng.permutation(Xa[:, b])
        imp[b] = base - M.cnn_acc(m, Xa, y)
    return imp


def cnn_deepshap(m, X, Xbg, target=1):
    import shap
    e = shap.DeepExplainer(m, torch.tensor(Xbg[:100], dtype=torch.float32, device=M.DEVICE))
    sv = e.shap_values(torch.tensor(X[:200], dtype=torch.float32, device=M.DEVICE),
                       check_additivity=False)
    if isinstance(sv, list):
        sv = sv[target]
    sv = np.array(sv)
    if sv.ndim == 3:
        sv = sv[..., target]
    return np.abs(sv).mean(0)


def bytes_to_fields(byte_scores):
    return {f: float(np.mean([byte_scores[b] for b in offs if b < len(byte_scores)]))
            for f, offs in BYTE_FIELD_OFFSETS.items()}


# ----------------------------- RF explainers (field-level) -----------------------------
def rf_impurity(rf):
    return {M.RF_FEATURES[i]: float(rf.feature_importances_[i]) for i in range(len(M.RF_FEATURES))}


def rf_treeshap(rf, F):
    import shap
    e = shap.TreeExplainer(rf)
    sv = e.shap_values(F[:400])
    if isinstance(sv, list):
        sv = sv[1]
    sv = np.array(sv)
    if sv.ndim == 3:
        sv = sv[..., 1]
    imp = np.abs(sv).mean(0)
    return {M.RF_FEATURES[i]: float(imp[i]) for i in range(len(M.RF_FEATURES))}


# map RF feature names -> canonical field names used by N(F)
RF_TO_FIELD = {
    "ip.ttl": "ip.ttl", "ip.id": "ip.id", "ip.src_b3": "ip.src", "ip.dst_b3": "ip.dst",
    "tcp.sport": "tcp.sport", "tcp.dport": "tcp.dport", "tcp.window": "tcp.window",
    "tcp.seq_hi": "tcp.seq", "tcp.flags": "tcp.flags", "payload_len": "payload",
}


def rf_scores_to_fields(rf_scores):
    out = {}
    for k, v in rf_scores.items():
        fld = RF_TO_FIELD.get(k, k)
        out[fld] = out.get(fld, 0.0) + v
    return out


# ----------------------------- audit metrics -----------------------------
def audit(field_scores, N, k=2, tau=0.05):
    """Score an explainer's field attributions against interventional necessity N."""
    fields = [f for f in N.keys() if f in field_scores]
    a = np.array([field_scores[f] for f in fields])
    n = np.array([N[f] for f in fields])
    rho = float(spearmanr(a, n).statistic) if len(fields) > 2 and a.std() > 0 else float("nan")
    order = sorted(fields, key=lambda f: -field_scores[f])
    topk = order[:k]
    needed = [f for f in fields if N[f] > tau]
    smax = a.max() if a.max() > 0 else 1.0
    named = [f for f in fields if field_scores[f] >= 0.2 * smax]
    p_at_k = len([f for f in topk if N[f] > tau]) / k
    false_conf = (len([f for f in named if N[f] <= tau]) / len(named)) if named else 0.0
    blind = (len([f for f in needed if f not in topk]) / len(needed)) if needed else 0.0
    return {"rho": round(rho, 3), "precision_at_k": round(p_at_k, 3),
            "false_confidence": round(false_conf, 3), "blind_spot": round(blind, 3),
            "top_k": topk, "named": named}
