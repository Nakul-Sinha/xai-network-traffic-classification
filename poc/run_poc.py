"""
Proof-of-concept for the interventional ground-truth benchmark.

Pipeline (all at the packet layer, the paper's central claim):
 1. Synthesize two "application" classes of real TCP/IP packets with scapy.
    - GENUINE signal:   payload length distribution differs by class (overlapping).
    - ARTIFACT A:       IP TTL   (64 vs 128), class-correlated with strength p.
    - ARTIFACT B:       TCP window (8192 vs 65535), ALSO class-correlated (redundant with A).
 2. Train an MLP on the raw first 64 header+payload bytes (checksums recomputed by scapy,
    so every sample is a valid packet -- interventions stay on-manifold).
 3. Ground truth by intervention:
    - N(F): necessity  = acc drop when field F is resampled from the pooled distribution.
    - S(F): sufficiency = acc when every OTHER candidate field is resampled.
    - R(M): number of disjoint sufficient field-sets (greedy extraction).
 4. Audit explainers (SHAP DeepExplainer + Integrated Gradients + occlusion) against N(F):
    - rank agreement, false-confidence rate, blind-spot rate.

Run: python run_poc.py            (defaults: p=1.0, n=4000 flows)
     python run_poc.py --p 0.7    (weaker artifact strength)
"""
import argparse, random, sys, io
import numpy as np

import warnings
warnings.filterwarnings("ignore")

from scapy.all import IP, TCP, Raw  # noqa: E402
import torch  # noqa: E402
import torch.nn as nn  # noqa: E402

rng = np.random.default_rng(7)
random.seed(7)
torch.manual_seed(7)

WIN = 64  # bytes of each packet fed to the model

# ---------------------------------------------------------------- synthesis
def make_packet(cls: int, p_art: float):
    """One synthetic packet of class `cls` with artifact strength p_art."""
    # genuine (weak, overlapping) signal: payload length
    plen = int(rng.normal(120 if cls == 0 else 180, 40))
    plen = max(8, min(plen, 400))

    # artifact A: TTL  -- class-correlated with prob p_art
    ttl = (64 if cls == 0 else 128) if rng.random() < p_art else (64 if rng.random() < .5 else 128)
    # artifact B: TCP window -- REDUNDANTLY class-correlated with the same strength
    win = (8192 if cls == 0 else 65535) if rng.random() < p_art else (8192 if rng.random() < .5 else 65535)

    pkt = IP(src=f"10.0.{rng.integers(0,255)}.{rng.integers(1,255)}",
             dst=f"192.168.{rng.integers(0,255)}.{rng.integers(1,255)}",
             ttl=int(ttl)) / \
          TCP(sport=int(rng.integers(1024, 65535)), dport=443,
              window=int(win), seq=int(rng.integers(0, 2**32 - 1))) / \
          Raw(bytes(rng.integers(0, 256, plen, dtype=np.uint8)))
    return pkt

def pkt_bytes(pkt) -> np.ndarray:
    b = bytes(pkt)[:WIN]
    b = b + b"\x00" * (WIN - len(b))
    return np.frombuffer(b, dtype=np.uint8).astype(np.float32) / 255.0

# field -> byte offsets inside a 20B-IP + 20B-TCP packet (no options)
FIELDS = {
    "ip.ttl":      [8],
    "ip.src":      [12, 13, 14, 15],
    "ip.dst":      [16, 17, 18, 19],
    "ip.len":      [2, 3],
    "tcp.sport":   [20, 21],
    "tcp.seq":     [24, 25, 26, 27],
    "tcp.window":  [34, 35],
    "payload":     list(range(40, WIN)),
}

def build_dataset(n, p_art):
    pkts, X, y = [], [], []
    for i in range(n):
        cls = i % 2
        pkt = make_packet(cls, p_art)
        pkts.append(pkt); X.append(pkt_bytes(pkt)); y.append(cls)
    return pkts, np.stack(X), np.array(y)

# ---------------------------------------------------------------- model
class MLP(nn.Module):
    def __init__(self):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(WIN, 128), nn.ReLU(),
            nn.Linear(128, 64), nn.ReLU(),
            nn.Linear(64, 2))
    def forward(self, x): return self.net(x)

def train(X, y, epochs=60, mask_bytes=None, mask_p=0.5):
    """mask_bytes: byte offsets randomly zeroed with prob mask_p during training.
    Masking a dominant artifact's bytes forces the model to ALSO learn backups —
    the same mechanism as MAE-style pretraining in YaTC/ET-BERT."""
    m = MLP()
    opt = torch.optim.Adam(m.parameters(), lr=1e-3)
    lf = nn.CrossEntropyLoss()
    Xt, yt = torch.tensor(X), torch.tensor(y)
    for _ in range(epochs):
        Xin = Xt
        if mask_bytes:
            Xin = Xt.clone()
            drop = torch.rand(len(Xt)) < mask_p
            for b in mask_bytes:
                Xin[drop, b] = 0.0
        opt.zero_grad()
        loss = lf(m(Xin), yt)
        loss.backward(); opt.step()
    return m

def acc(m, X, y):
    with torch.no_grad():
        return (m(torch.tensor(X)).argmax(1).numpy() == y).mean()

# ---------------------------------------------------------------- interventions
def intervene(pkts, y, field_names, pool_pkts):
    """do(F := resample from pooled distribution) for every F in field_names.
    Rewrites the field with scapy and lets scapy recompute checksums -> valid packets."""
    out = []
    for pkt in pkts:
        q = pkt.copy()
        donor = pool_pkts[rng.integers(0, len(pool_pkts))]
        for f in field_names:
            if f == "ip.ttl":     q[IP].ttl = donor[IP].ttl
            elif f == "ip.src":   q[IP].src = donor[IP].src
            elif f == "ip.dst":   q[IP].dst = donor[IP].dst
            elif f == "tcp.sport": q[TCP].sport = donor[TCP].sport
            elif f == "tcp.seq":  q[TCP].seq = donor[TCP].seq
            elif f == "tcp.window": q[TCP].window = donor[TCP].window
            elif f == "payload":
                dp = bytes(donor[Raw]) if Raw in donor else b""
                q[Raw].load = dp if dp else q[Raw].load
            elif f == "ip.len":
                pass  # recomputed automatically
        # force checksum/length recompute
        del q[IP].chksum; del q[TCP].chksum; del q[IP].len
        q = IP(bytes(q))
        out.append(pkt_bytes(q))
    return np.stack(out)

def necessity(m, pkts, X, y, pool):
    base = acc(m, X, y)
    N = {}
    for f in FIELDS:
        Xi = intervene(pkts, y, [f], pool)
        N[f] = float(base - acc(m, Xi, y))
    return base, N

def sufficiency(m, pkts, X, y, pool):
    S = {}
    for f in FIELDS:
        others = [g for g in FIELDS if g != f]
        Xi = intervene(pkts, y, others, pool)
        S[f] = float(acc(m, Xi, y))
    return S

def redundancy(m, pkts, X, y, pool, tau=0.10):
    """Greedy: find a minimal sufficient set, neutralise it, look for the next disjoint one."""
    base = acc(m, X, y)
    remaining = list(FIELDS)
    neutralised = []
    sets = []
    for _ in range(4):
        # neutralise already-extracted sets, then rank remaining fields by necessity
        Xn_p = pkts
        cur_neutral = [f for s in sets for f in s]
        best, bestdrop = None, -1
        for f in remaining:
            Xi = intervene(pkts, y, cur_neutral + [f], pool)
            drop = acc(m, intervene(pkts, y, cur_neutral, pool) if cur_neutral else X, y) - acc(m, Xi, y)
            if drop > bestdrop: best, bestdrop = f, drop
        if best is None: break
        # grow set greedily until neutralising it collapses accuracy to ~chance
        s = [best]
        while True:
            Xi = intervene(pkts, y, cur_neutral + s, pool)
            a = acc(m, Xi, y)
            if a < 0.5 + tau: break
            # add next most necessary field
            cand, cd = None, -1
            for f in remaining:
                if f in s: continue
                Xj = intervene(pkts, y, cur_neutral + s + [f], pool)
                d = a - acc(m, Xj, y)
                if d > cd: cand, cd = f, d
            if cand is None or cd <= 0.005: break
            s.append(cand)
        # check: does the rest of the model still work with this set neutralised?
        Xi = intervene(pkts, y, cur_neutral + s, pool)
        a_after = acc(m, Xi, y)
        sets.append(s)
        remaining = [f for f in remaining if f not in s]
        if a_after < 0.5 + tau:   # model is dead once this set is gone -> no further disjoint set
            break
    # R = number of sets the model could FALL BACK on: count sets extracted while acc stayed high
    return sets

# ---------------------------------------------------------------- explainers
def shap_attr(m, X, Xbg):
    import shap
    e = shap.DeepExplainer(m, torch.tensor(Xbg[:100]))
    sv = e.shap_values(torch.tensor(X[:200]), check_additivity=False)
    sv = sv[1] if isinstance(sv, list) else sv  # class-1 attributions
    if sv.ndim == 3: sv = sv[..., 1]
    return np.abs(sv).mean(0)

def ig_attr(m, X):
    x = torch.tensor(X[:200], requires_grad=True)
    base = torch.zeros_like(x)
    steps = 32
    total = torch.zeros_like(x)
    for a in np.linspace(0, 1, steps):
        xi = base + a * (x - base)
        xi.requires_grad_(True)
        out = m(xi)[:, 1].sum()
        g = torch.autograd.grad(out, xi)[0]
        total += g / steps
    ig = ((x - base) * total).detach().numpy()
    return np.abs(ig).mean(0)

def occl_attr(m, X, y):
    base = acc(m, X, y)
    imp = np.zeros(WIN)
    for b in range(WIN):
        Xa = X.copy(); Xa[:, b] = rng.permutation(Xa[:, b])
        imp[b] = base - acc(m, Xa, y)
    return imp

def to_field_scores(byte_scores):
    return {f: float(np.mean([byte_scores[b] for b in off if b < len(byte_scores)]))
            for f, off in FIELDS.items()}

# ---------------------------------------------------------------- audit
def audit(name, field_scores, N, k=2, tau=0.05):
    from scipy.stats import spearmanr
    fields = list(FIELDS)
    a = [field_scores[f] for f in fields]
    n = [N[f] for f in fields]
    rho = spearmanr(a, n).statistic
    smax = max(a) or 1.0
    # "named" = attribution mass at least 20% of the top field's (filters forced-ranking noise)
    named = [f for f in fields if field_scores[f] >= 0.2 * smax]
    needed = {f for f in fields if N[f] > tau}
    false_conf = (len([f for f in named if N[f] <= tau]) / len(named)) if named else 0.0
    blind = (len([f for f in needed if f not in named]) / len(needed)) if needed else 0.0
    scores_str = " ".join(f"{f}={field_scores[f]/smax:.2f}" for f in sorted(fields, key=lambda f: -field_scores[f])[:4])
    print(f"  {name:12s} rho={rho:+.2f}  named={named}  false-confidence={false_conf:.2f}  blind-spot={blind:.2f}")
    print(f"  {'':12s} rel-scores: {scores_str}")
    return rho, named, false_conf, blind

# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--p", type=float, default=1.0, help="artifact strength P(artifact|class)")
    ap.add_argument("--n", type=int, default=4000)
    ap.add_argument("--redundant-model", action="store_true",
                    help="mask tcp.window bytes during training so the model must also learn TTL")
    args = ap.parse_args()

    print(f"=== synthesis: n={args.n}, artifact strength p={args.p}, redundant-model={args.redundant_model} ===")
    pkts, X, y = build_dataset(args.n, args.p)
    idx = rng.permutation(len(X)); ntr = int(0.75 * len(X)); tr, te = idx[:ntr], idx[ntr:]
    Xtr, ytr = X[tr], y[tr]
    Xte, yte = X[te], y[te]
    pkte = [pkts[i] for i in te]

    m = train(Xtr, ytr, mask_bytes=FIELDS["tcp.window"] if args.redundant_model else None)
    print(f"train acc={acc(m,Xtr,ytr):.3f}  test acc={acc(m,Xte,yte):.3f}")

    print("\n=== interventional ground truth (packet-layer do(), checksums recomputed) ===")
    base, N = necessity(m, pkte, Xte, yte, pkts)
    S = sufficiency(m, pkte, Xte, yte, pkts)
    print(f"{'field':12s} {'N(F) necessity':>15s} {'S(F) sufficiency':>17s}")
    for f in FIELDS:
        print(f"{f:12s} {N[f]:15.3f} {S[f]:17.3f}")

    print("\n=== redundancy R(M): disjoint sufficient sets (greedy) ===")
    sets = redundancy(m, pkte, Xte, yte, pkts)
    for i, s in enumerate(sets): print(f"  S{i+1}: {s}")
    print(f"  R(M) = {len(sets)}")

    print("\n=== explainer audit vs N(F) ===")
    try:
        sa = to_field_scores(shap_attr(m, Xte, Xtr)); audit("DeepSHAP", sa, N)
    except Exception as e:
        print(f"  DeepSHAP failed: {e}")
    ia = to_field_scores(ig_attr(m, Xte)); audit("IntGrad", ia, N)
    oa = to_field_scores(occl_attr(m, Xte, yte)); audit("Occlusion", oa, N)

    print("\nInterpretation: if the model leans on ONE of two redundant artifacts, a good rho for")
    print("one explainer does not guarantee the other artifact is visible to any of them; a field")
    print("with N~0 in the top-k is the TRUSTEE false-confidence failure mode, measured.")

if __name__ == "__main__":
    main()
