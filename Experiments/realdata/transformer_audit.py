"""
Transformer audit: does the false-confidence phenomenon hold for an attention-based byte model,
and is attention-as-explanation faithful?

The intro invokes ET-BERT-style transformer classifiers; the reviewer notes our experiments used only
a CNN and an RF, and that attention-as-explanation is contested. This script trains a compact
BERT-style byte-level Transformer encoder (multi-head self-attention over the 80-byte window, a CLS
token, learned positional embeddings) on the SAME real ISCX packets (facebook TCP/443 vs ftps), and
audits four explainers against PacketDO interventional necessity:
  IntegratedGradients, Saliency, Occlusion (reused, model-agnostic), and Attention (CLS->byte weights).

This is not the pretrained ET-BERT (which needs its own fine-tuning pipeline and weights); it is a
transformer of the same architectural family, trained from scratch, sufficient to test whether the
audit findings transfer to self-attention and whether attention weights are a faithful explanation.

Run: python transformer_audit.py    Writes results/transformer_audit.json + .md
"""
import warnings; warnings.filterwarnings("ignore")
import json, os, sys
import numpy as np
import torch, torch.nn as nn

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "results")
sys.path.insert(0, os.path.dirname(HERE))
from benchmark import models as M, groundtruth as GT, explainers as EX
from benchmark.generate import pkt_to_bytes
import pcap_bytelevel as PB

DEVICE = M.DEVICE
SEED = 0


class TFLayer(nn.Module):
    def __init__(self, d, nhead):
        super().__init__()
        self.attn = nn.MultiheadAttention(d, nhead, batch_first=True)
        self.ln1, self.ln2 = nn.LayerNorm(d), nn.LayerNorm(d)
        self.ff = nn.Sequential(nn.Linear(d, 2 * d), nn.ReLU(), nn.Linear(2 * d, d))
        self.last_attn = None

    def forward(self, x):
        a, w = self.attn(x, x, x, need_weights=True, average_attn_weights=True)
        self.last_attn = w
        x = self.ln1(x + a)
        return self.ln2(x + self.ff(x))


class ByteTransformer(nn.Module):
    def __init__(self, seq=80, d=64, nhead=4, nlayers=2):
        super().__init__()
        self.proj = nn.Linear(1, d)
        self.cls = nn.Parameter(torch.randn(1, 1, d) * 0.02)
        self.pos = nn.Parameter(torch.randn(1, seq + 1, d) * 0.02)
        self.layers = nn.ModuleList([TFLayer(d, nhead) for _ in range(nlayers)])
        self.head = nn.Linear(d, 2)

    def forward(self, x):
        h = self.proj(x.unsqueeze(-1))                       # [B, seq, d]
        h = torch.cat([self.cls.expand(x.size(0), -1, -1), h], dim=1) + self.pos
        for l in self.layers:
            h = l(h)
        return self.head(h[:, 0])                            # from CLS

    def attention_importance(self, X):
        """Mean CLS->byte attention of the last layer: attention-as-explanation, per byte."""
        self.eval()
        with torch.no_grad():
            x = torch.tensor(X[:400], dtype=torch.float32, device=DEVICE)
            _ = self.forward(x)
            w = self.layers[-1].last_attn[:, 0, 1:]          # CLS to the 80 byte positions
        return w.mean(0).cpu().numpy()


def train_transformer(X, y, epochs=80, seed=0):
    torch.manual_seed(seed)
    m = ByteTransformer(seq=X.shape[1]).to(DEVICE)
    opt = torch.optim.Adam(m.parameters(), lr=1e-3, weight_decay=1e-4)
    lf = nn.CrossEntropyLoss()
    Xt = torch.tensor(X, dtype=torch.float32, device=DEVICE)
    yt = torch.tensor(y, dtype=torch.long, device=DEVICE)
    n = len(Xt); bs = 512
    m.train()
    g = torch.Generator(device=DEVICE); g.manual_seed(seed)
    for _ in range(epochs):
        perm = torch.randperm(n, generator=g, device=DEVICE)
        for i in range(0, n, bs):
            b = perm[i:i + bs]
            opt.zero_grad(); loss = lf(m(Xt[b]), yt[b]); loss.backward(); opt.step()
    m.eval()
    return m


def main():
    print("loading real ISCX packets (facebook vs ftps)...", flush=True)
    p0 = PB.load_class(PB.CLASSES[0], PB.CAP)
    p1 = PB.load_class(PB.CLASSES[1], PB.CAP)
    pkts = p0 + p1
    y = np.array([0] * len(p0) + [1] * len(p1))
    X = np.stack([pkt_to_bytes(pk) for pk in pkts])
    rng = np.random.default_rng(SEED)
    idx = rng.permutation(len(X))
    X, y, pkts = X[idx], y[idx], [pkts[i] for i in idx]
    ntr = int(0.7 * len(X))
    Xtr, ytr, Xte, yte = X[:ntr], y[:ntr], X[ntr:], y[ntr:]
    pkte = pkts[ntr:][:800]; Xte, yte = Xte[:800], yte[:800]

    print("training byte Transformer (self-attention)...", flush=True)
    tf = train_transformer(Xtr, ytr, epochs=80, seed=SEED)
    acc = round(M.cnn_acc(tf, Xte, yte), 4)
    print(f"  transformer test acc={acc}", flush=True)

    sampler = GT.make_sampler(pkts, seed=SEED + 1)

    def eval_tf(packets, yy):
        return M.cnn_acc(tf, np.stack([pkt_to_bytes(pk) for pk in packets]), yy)

    print("necessity N(F) via PacketDO on the transformer...", flush=True)
    base, N = GT.necessity(pkte, yte, eval_tf, sampler)

    print("explainers (IG, Saliency, Occlusion, Attention)...", flush=True)
    expl = {
        "IntegratedGradients": EX.bytes_to_fields(EX.cnn_integrated_gradients(tf, Xte)),
        "Saliency": EX.bytes_to_fields(EX.cnn_saliency(tf, Xte)),
        "Occlusion": EX.bytes_to_fields(EX.cnn_occlusion(tf, Xte, yte)),
        "Attention": EX.bytes_to_fields(tf.attention_importance(Xte)),
    }
    audit = {name: EX.audit(sc, N) for name, sc in expl.items()}

    out = {"task": "facebook vs ftps (real ISCX), byte Transformer (self-attention)",
           "n_per_class": [len(p0), len(p1)], "test_acc": acc,
           "base_acc_gt": round(base, 4), "N": N, "audit": audit, "attributions_fields": expl}
    os.makedirs(RES, exist_ok=True)
    json.dump(out, open(os.path.join(RES, "transformer_audit.json"), "w"), indent=2)

    Nsorted = sorted(N.items(), key=lambda kv: -kv[1])
    L = ["# Transformer audit on real ISCX packets (attention-based byte model)\n",
         f"Byte Transformer (2 layers, 4 heads, d=64, CLS token) on facebook vs ftps; "
         f"test acc = {acc}.\n",
         "## Interventional necessity N(F)", "| field | N(F) |", "|---|---|"]
    for f, v in Nsorted[:6]:
        L.append(f"| {f} | {v} |")
    L += ["", "## Explainer audit vs N(F) (Attention = CLS->byte attention weights)",
          "| method | rho | precision@k | false-confidence | blind-spot |", "|---|---|---|---|---|"]
    for nm, a in audit.items():
        L.append(f"| {nm} | {a['rho']} | {a['precision_at_k']} | {a['false_confidence']} | {a['blind_spot']} |")
    open(os.path.join(RES, "transformer_audit.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")
    print("N(F) top:", Nsorted[:4], flush=True)
    for nm, a in audit.items():
        print(f"  {nm}: rho={a['rho']} prec={a['precision_at_k']} FC={a['false_confidence']} blind={a['blind_spot']}", flush=True)
    print("saved results/transformer_audit.json + .md", flush=True)


if __name__ == "__main__":
    main()
