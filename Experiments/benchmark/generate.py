"""
Synthetic traffic generator with planted shortcuts at graded strength (benchmark C2a).

Produces a controlled two-class packet dataset in which we KNOW the ground-truth decision
basis, because we plant it. Each class has:
  - a GENUINE, weak, overlapping signal (payload-length distribution), and
  - one or more PLANTED ARTIFACTS (protocol fields correlated with the label at a tunable
    strength p = P(artifact carries the class-consistent value | class)).

At p=0.5 an artifact is uninformative (pure noise); at p=1.0 it perfectly predicts the label.
Sweeping p yields a spectrum of known reliance so we can plot attribution vs interventional
necessity rather than testing a single point (Bastings et al. use a binary planted shortcut;
graded strength is our extension).

Two planted artifacts are included so redundancy can be studied:
  A: ip.ttl      in {64, 128}
  B: tcp.window  in {8192, 65535}
Both at the same strength p unless --single is passed.

Output: a .npz with raw packet bytes (fixed window), labels, and metadata; plus the scapy
packets pickled for interventional analysis. Everything seeded.

Usage:
  python generate.py --p 1.0 --n 6000 --out data/p100.npz
"""
import warnings; warnings.filterwarnings("ignore")
import argparse, os, pickle, sys
import numpy as np
from scapy.all import IP, TCP, Raw

WIN = 80  # bytes fed to a byte-level model (IP20 + TCP20 + up to 40 payload)


def make_packet(cls, p, rng, single=False):
    # genuine weak signal: payload length, overlapping distributions
    plen = int(rng.normal(120 if cls == 0 else 170, 45))
    plen = max(8, min(plen, 300))

    # planted artifact A: ip.ttl
    if rng.random() < p:
        ttl = 64 if cls == 0 else 128
    else:
        ttl = int(rng.choice([64, 128]))  # class-agnostic noise

    # planted artifact B: tcp.window (redundant with A), unless single-artifact mode
    if single:
        win = int(rng.choice([8192, 65535]))  # pure noise -> B carries no signal
    else:
        if rng.random() < p:
            win = 8192 if cls == 0 else 65535
        else:
            win = int(rng.choice([8192, 65535]))

    pkt = IP(src=f"10.{rng.integers(0,256)}.{rng.integers(0,256)}.{rng.integers(1,255)}",
             dst=f"192.168.{rng.integers(0,256)}.{rng.integers(1,255)}",
             ttl=ttl, id=int(rng.integers(0, 65536))) / \
          TCP(sport=int(rng.integers(1024, 65535)), dport=443,
              window=win, seq=int(rng.integers(0, 2**32 - 1)),
              flags=int(rng.choice([2, 16, 24]))) / \
          Raw(bytes(rng.integers(0, 256, plen, dtype=np.uint8)))
    return IP(bytes(pkt))  # round-trip -> valid, checksums set


def pkt_to_bytes(pkt):
    b = bytes(pkt)[:WIN]
    return np.frombuffer(b + b"\x00" * (WIN - len(b)), dtype=np.uint8).astype(np.float32) / 255.0


def build(n, p, seed, single=False):
    rng = np.random.default_rng(seed)
    pkts, X, y = [], [], []
    for i in range(n):
        cls = i % 2
        pkt = make_packet(cls, p, rng, single)
        pkts.append(pkt); X.append(pkt_to_bytes(pkt)); y.append(cls)
    return pkts, np.stack(X), np.array(y)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--p", type=float, required=True)
    ap.add_argument("--n", type=int, default=6000)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--single", action="store_true", help="only artifact A carries signal")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    pkts, X, y = build(args.n, args.p, args.seed, args.single)
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    np.savez_compressed(args.out, X=X, y=y, p=args.p, seed=args.seed,
                        single=args.single, win=WIN)
    with open(args.out.replace(".npz", "_pkts.pkl"), "wb") as f:
        pickle.dump([bytes(pk) for pk in pkts], f)
    # quick class-separation check on the planted fields
    ttl_by_cls = {0: [], 1: []}
    win_by_cls = {0: [], 1: []}
    for pk, lbl in zip(pkts, y):
        ttl_by_cls[lbl].append(pk[IP].ttl)
        win_by_cls[lbl].append(pk[TCP].window)
    print(f"p={args.p} n={args.n} single={args.single}")
    print(f"  class0 ttl64%={np.mean(np.array(ttl_by_cls[0])==64):.2f}  "
          f"class1 ttl128%={np.mean(np.array(ttl_by_cls[1])==128):.2f}")
    print(f"  saved {args.out} (X {X.shape}) + pkts pickle")


if __name__ == "__main__":
    main()
