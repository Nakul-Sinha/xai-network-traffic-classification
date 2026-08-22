"""
Generate paper figures from committed results. Deterministic; re-run any time.
Outputs PNG (300 dpi) + a caption stub into Working/figures/.
"""
import warnings; warnings.filterwarnings("ignore")
import json, os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
E1 = os.path.join(ROOT, "Experiments", "e1_operator_validity", "results", "e1_results.json")
AUD = os.path.join(ROOT, "Experiments", "benchmark", "results")
OUT = os.path.join(ROOT, "Working", "figures")
os.makedirs(OUT, exist_ok=True)

plt.rcParams.update({"font.size": 11, "axes.grid": True, "grid.alpha": 0.3,
                     "figure.dpi": 300, "savefig.bbox": "tight"})


def fig1_operator_validity():
    d = json.load(open(E1))
    pf = d["per_field"]
    fields = [f for f in pf if pf[f]["zero_mask_valid_rate"] is not None]
    zm = [pf[f]["zero_mask_valid_rate"] * 100 for f in fields]
    do = [pf[f]["packet_do_valid_rate"] * 100 for f in fields]
    x = np.arange(len(fields)); w = 0.38
    fig, ax = plt.subplots(figsize=(9, 3.6))
    ax.bar(x - w/2, zm, w, label="zero-mask (deletion default)", color="#d1495b")
    ax.bar(x + w/2, do, w, label="PacketDO (ours)", color="#2e86ab")
    ax.set_xticks(x); ax.set_xticklabels(fields, rotation=45, ha="right", fontsize=8)
    ax.set_ylabel("% protocol-valid counterfactuals")
    ax.set_ylim(0, 105)
    ax.set_title("E1: operator validity per field (2000 synthetic packets, seed 0)")
    ax.legend(loc="center right", fontsize=9)
    s = d["summary"]
    ax.text(0.02, 0.9, f"macro: zero-mask {s['zero_mask_macro_valid_rate']*100:.0f}%  |  "
            f"PacketDO {s['packet_do_macro_valid_rate']*100:.0f}%",
            transform=ax.transAxes, fontsize=9,
            bbox=dict(boxstyle="round", fc="white", alpha=0.8))
    fig.savefig(os.path.join(OUT, "fig1_operator_validity.png"))
    plt.close(fig)
    return "fig1_operator_validity.png"


def _multiseed_fc(fam, exp, tag, seeds=(0, 1, 2, 3, 4)):
    vals = []
    for s in seeds:
        suf = "" if s == 0 else f"_seed{s}"
        fp = os.path.join(AUD, f"audit_{tag}{suf}.json")
        if not os.path.exists(fp):
            continue
        d = json.load(open(fp))
        a = d[fam]["audit"].get(exp)
        if a:
            vals.append(a["false_confidence"])
    if not vals:
        return np.nan, np.nan, 0
    return float(np.mean(vals)), float(np.std(vals, ddof=1) if len(vals) > 1 else 0.0), len(vals)


def fig2_false_confidence():
    ps = [0.5, 0.7, 0.9, 1.0]
    tags = {0.5: "p05", 0.7: "p07", 0.9: "p09", 1.0: "p10"}
    fam_expl = {
        "cnn": ["Saliency", "IntegratedGradients", "DeepSHAP", "Occlusion"],
        "rf": ["Impurity", "TreeSHAP"],
    }
    colors = {"Saliency": "#d1495b", "IntegratedGradients": "#edae49", "DeepSHAP": "#2e86ab",
              "Occlusion": "#66a182", "Impurity": "#d1495b", "TreeSHAP": "#2e86ab"}
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.8), sharey=True)
    nseed = 1
    for ax, (fam, expls) in zip(axes, fam_expl.items()):
        for exp in expls:
            means, sds = [], []
            for p in ps:
                m, sd, n = _multiseed_fc(fam, exp, tags[p])
                means.append(m); sds.append(sd); nseed = max(nseed, n)
            ax.errorbar(ps, means, yerr=sds, fmt="-o", label=exp, color=colors.get(exp),
                        lw=2, ms=6, capsize=3, elinewidth=1.2)
        ax.set_xlabel("planting strength p")
        ax.set_title("ByteCNN" if fam == "cnn" else "RandomForest")
        ax.set_ylim(-0.1, 1.0); ax.set_xticks(ps)
        ax.legend(fontsize=8, loc="upper right")
    axes[0].set_ylabel("false-confidence rate")
    fig.suptitle(f"E4: explainer false-confidence vs planting strength (mean +/- sd, {nseed} seeds)", y=1.02)
    fig.savefig(os.path.join(OUT, "fig2_false_confidence.png"))
    plt.close(fig)
    return "fig2_false_confidence.png"


def fig3_necessity_vs_strength():
    ps = [0.5, 0.7, 0.9, 1.0]
    tags = {0.5: "p05", 0.7: "p07", 0.9: "p09", 1.0: "p10"}
    fig, ax = plt.subplots(figsize=(6, 3.8))
    for fam, style in [("cnn", "-o"), ("rf", "--s")]:
        for fld, col in [("tcp.window", "#2e86ab"), ("ip.ttl", "#d1495b"), ("tcp.sport", "#999999")]:
            ys = []
            for p in ps:
                d = json.load(open(os.path.join(AUD, f"audit_{tags[p]}.json")))
                ys.append(d[fam]["N"].get(fld, np.nan))
            lbl = f"{fam.upper()} N({fld})"
            ax.plot(ps, ys, style, color=col, lw=1.8, ms=5, alpha=0.85, label=lbl)
    ax.axhline(0, color="k", lw=0.6)
    ax.set_xlabel("planting strength p"); ax.set_ylabel("interventional necessity N(F)")
    ax.set_title("Ground truth: model reliance vs planting strength")
    ax.legend(fontsize=7, ncol=2); ax.set_xticks(ps)
    fig.savefig(os.path.join(OUT, "fig3_necessity.png"))
    plt.close(fig)
    return "fig3_necessity.png"


if __name__ == "__main__":
    made = []
    for fn in (fig1_operator_validity, fig2_false_confidence, fig3_necessity_vs_strength):
        try:
            made.append(fn())
            print("wrote", made[-1])
        except Exception as e:
            print("FAILED", fn.__name__, e)
    caps = {
        "fig1_operator_validity.png": "Fig 1. Per-field protocol-validity of counterfactuals under "
        "zero-masking vs PacketDO. Zero-masking is valid only where it is a no-op; PacketDO is valid "
        "by construction.",
        "fig2_false_confidence.png": "Fig 2. False-confidence rate (fraction of confidently-attributed "
        "fields with interventional necessity ~0) vs planting strength. Saliency and Integrated "
        "Gradients fabricate importance; DeepSHAP/Occlusion do not; TreeSHAP fails at p=1.0.",
        "fig3_necessity.png": "Fig 3. Interventional necessity N(F). Models commit to tcp.window and "
        "ignore the redundant ip.ttl; the null field tcp.sport stays at zero.",
    }
    open(os.path.join(OUT, "captions.md"), "w", encoding="utf-8").write(
        "\n\n".join(f"**{k}**\n{v}" for k, v in caps.items() if k in made) + "\n")
    print("captions written")
