"""
Extra explainers for the C3 matrix: KernelSHAP and LIME on the ByteCNN.

Both are model-agnostic perturbation methods operating on the flat byte window
(WIN=80 features in [0,1]); per-byte attributions are aggregated to protocol
fields with explainers.bytes_to_fields, exactly like the gradient methods, and
audited against the same interventional N(F).

Both are SLOW relative to gradient methods -- the wall-clock cost is itself a
paper datapoint (line-rate argument), so each wrapper returns
(byte_scores, runtime_seconds, n_explained).
"""
import warnings; warnings.filterwarnings("ignore")
import time
import numpy as np
import torch

from benchmark import models as M


def cnn_predict_proba(m, X, batch=4096):
    """Wrapped predict_proba: numpy (n, WIN) float in [0,1] -> (n, 2) softmax probs."""
    out = []
    with torch.no_grad():
        for i in range(0, len(X), batch):
            xb = torch.tensor(np.asarray(X[i:i + batch]), dtype=torch.float32, device=M.DEVICE)
            out.append(torch.softmax(m(xb), dim=1).cpu().numpy())
    return np.concatenate(out, 0)


def cnn_kernelshap(m, X, Xbg, target=1, n_explain=150, bg_k=10, nsamples="auto", seed=0):
    """KernelSHAP over the wrapped predict_proba. Background = k-means summary of Xbg.

    Returns (mean |shap| per byte, wall-clock seconds, n_explained).
    """
    import shap
    rng = np.random.default_rng(seed)
    Xe = X[:n_explain].astype(np.float64)
    bg = shap.kmeans(Xbg[rng.choice(len(Xbg), min(500, len(Xbg)), replace=False)].astype(np.float64),
                     bg_k)
    f = lambda Z: cnn_predict_proba(m, Z.astype(np.float32))
    t0 = time.perf_counter()
    e = shap.KernelExplainer(f, bg)
    sv = e.shap_values(Xe, nsamples=nsamples, silent=True)
    dt = time.perf_counter() - t0
    if isinstance(sv, list):
        sv = sv[target]
    sv = np.array(sv)
    if sv.ndim == 3:           # (n, features, classes)
        sv = sv[..., target]
    return np.abs(sv).mean(0), dt, len(Xe)


def cnn_lime(m, X, Xtr, target=1, n_explain=150, num_samples=1000, seed=0):
    """LIME (lime_tabular, no discretization: bytes stay continuous in [0,1]).

    Per-sample local linear weights for the target class, aggregated as
    mean |weight| per byte over the explained set.
    Returns (mean |weight| per byte, wall-clock seconds, n_explained).
    """
    from lime import lime_tabular
    nb = X.shape[1]
    Xe = X[:n_explain]
    expl = lime_tabular.LimeTabularExplainer(
        Xtr.astype(np.float64),
        feature_names=[f"b{i}" for i in range(nb)],
        class_names=["c0", "c1"],
        discretize_continuous=False,
        mode="classification",
        random_state=seed,
    )
    f = lambda Z: cnn_predict_proba(m, Z.astype(np.float32))
    agg = np.zeros(nb)
    t0 = time.perf_counter()
    for x in Xe:
        exp = expl.explain_instance(x.astype(np.float64), f, labels=(target,),
                                    num_features=nb, num_samples=num_samples)
        for idx, w in exp.as_map()[target]:
            agg[idx] += abs(w)
    dt = time.perf_counter() - t0
    return agg / len(Xe), dt, len(Xe)
