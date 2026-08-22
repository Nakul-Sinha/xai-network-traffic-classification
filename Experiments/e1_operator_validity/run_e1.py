"""
E1: Operator-validity study.

Claim under test (paper C1/C4 motivation): the deletion/occlusion operator the XAI-NTC
literature imports from vision (set the "removed" feature to zero) produces
PROTOCOL-INVALID packets, whereas PacketDO produces valid ones. We quantify the gap.

Method:
  - Build a diverse population of valid packets (synthetic TCP + UDP, varied fields).
  - For each intervenable field, apply BOTH operators to every packet:
        zero_mask(pkt, field)          -- the field's default
        packet_do(pkt, field, donor)   -- ours, donor from pooled sampler
  - Score each resulting byte-string with the validity predicates.
  - Report per-field and overall validity rate for each operator, and WHICH predicate
    zero-masking most often violates.

Output: results/e1_results.json + results/e1_table.md
"""
import warnings; warnings.filterwarnings("ignore")
import json, os, sys, argparse
from collections import defaultdict
import numpy as np
from scapy.all import IP, TCP, UDP, Raw

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from packetdo import operator as op, validity as vd, fields as F
from packetdo.sampler import PooledSampler

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "results")
os.makedirs(RES, exist_ok=True)


def build_population(n, seed=0):
    rng = np.random.default_rng(seed)
    pkts = []
    for i in range(n):
        proto_tcp = rng.random() < 0.7
        ttl = int(rng.choice([32, 64, 128, 255]))
        src = f"{rng.integers(1,223)}.{rng.integers(0,255)}.{rng.integers(0,255)}.{rng.integers(1,254)}"
        dst = f"{rng.integers(1,223)}.{rng.integers(0,255)}.{rng.integers(0,255)}.{rng.integers(1,254)}"
        plen = int(rng.integers(0, 200))
        payload = bytes(rng.integers(0, 256, plen, dtype=np.uint8))
        if proto_tcp:
            pkt = IP(src=src, dst=dst, ttl=ttl, id=int(rng.integers(0, 65536))) / \
                  TCP(sport=int(rng.integers(1024, 65535)), dport=int(rng.choice([80, 443, 22, 8080])),
                      window=int(rng.choice([8192, 16384, 65535])), seq=int(rng.integers(0, 2**32-1)),
                      flags=int(rng.choice([2, 16, 24, 18]))) / Raw(payload if plen else b"\x00")
        else:
            pkt = IP(src=src, dst=dst, ttl=ttl, id=int(rng.integers(0, 65536))) / \
                  UDP(sport=int(rng.integers(1024, 65535)), dport=int(rng.choice([53, 123, 443]))) / \
                  Raw(payload if plen else b"\x00")
        # round-trip through scapy so baseline is guaranteed valid
        pkts.append(IP(bytes(pkt)))
    return pkts


def run(n=2000, seed=0):
    pkts = build_population(n, seed)
    # baseline sanity: every synthesized packet must be valid
    base_valid = sum(vd.valid(bytes(p)) for p in pkts)
    sampler = PooledSampler(pkts, seed=seed + 1)

    per_field = {}
    violation_counts = defaultdict(lambda: defaultdict(int))  # operator -> predicate -> count

    for field in F.INTERVENABLE:
        present = [p for p in pkts if F.field_present(p, field)]
        if not present:
            continue
        zm_valid = do_valid = 0
        zm_total = do_total = 0
        for p in present:
            # zero-mask
            zraw = op.zero_mask_bytes(p, field)
            zc = vd.check(zraw)
            zm_total += 1
            if zc.get("valid"):
                zm_valid += 1
            else:
                for k, v in zc.items():
                    if k not in ("valid", "pkt") and v is False:
                        violation_counts["zero_mask"][k] += 1
            # packet_do
            donor = sampler.draw(field)
            if donor is None:
                continue
            draw = op.packet_do_bytes(p, field, donor)
            dc = vd.check(draw)
            do_total += 1
            if dc.get("valid"):
                do_valid += 1
            else:
                for k, v in dc.items():
                    if k not in ("valid", "pkt") and v is False:
                        violation_counts["packet_do"][k] += 1
        per_field[field] = {
            "n": zm_total,
            "zero_mask_valid_rate": round(zm_valid / zm_total, 4) if zm_total else None,
            "packet_do_valid_rate": round(do_valid / do_total, 4) if do_total else None,
        }

    # overall (macro over fields)
    zm_rates = [v["zero_mask_valid_rate"] for v in per_field.values() if v["zero_mask_valid_rate"] is not None]
    do_rates = [v["packet_do_valid_rate"] for v in per_field.values() if v["packet_do_valid_rate"] is not None]
    summary = {
        "n_packets": n,
        "seed": seed,
        "baseline_valid_rate": round(base_valid / len(pkts), 4),
        "zero_mask_macro_valid_rate": round(float(np.mean(zm_rates)), 4),
        "packet_do_macro_valid_rate": round(float(np.mean(do_rates)), 4),
        "zero_mask_violations": dict(violation_counts["zero_mask"]),
        "packet_do_violations": dict(violation_counts["packet_do"]),
    }
    out = {"summary": summary, "per_field": per_field}
    json.dump(out, open(os.path.join(RES, "e1_results.json"), "w"), indent=2)
    write_table(out)
    return out


def write_table(out):
    s = out["summary"]; pf = out["per_field"]
    lines = []
    lines.append("# E1: Operator-validity study\n")
    lines.append(f"Population: {s['n_packets']} synthetic IP/TCP+UDP packets (seed {s['seed']}). "
                 f"Baseline validity of the population: {s['baseline_valid_rate']*100:.1f}%.\n")
    lines.append("## Headline\n")
    lines.append(f"- Zero-masking (the deletion/occlusion default) macro validity: "
                 f"**{s['zero_mask_macro_valid_rate']*100:.1f}%**")
    lines.append(f"- PacketDO macro validity: **{s['packet_do_macro_valid_rate']*100:.1f}%**\n")
    lines.append("When zero-masking makes a packet invalid, the predicate it violates:")
    for k, v in sorted(s["zero_mask_violations"].items(), key=lambda x: -x[1]):
        lines.append(f"  - {k}: {v} violations")
    lines.append("")
    lines.append("## Per-field validity rate\n")
    lines.append("| field | n | zero-mask valid | PacketDO valid |")
    lines.append("|---|---|---|---|")
    for f, v in pf.items():
        zm = f"{v['zero_mask_valid_rate']*100:.1f}%" if v['zero_mask_valid_rate'] is not None else "-"
        do = f"{v['packet_do_valid_rate']*100:.1f}%" if v['packet_do_valid_rate'] is not None else "-"
        lines.append(f"| {f} | {v['n']} | {zm} | {do} |")
    open(os.path.join(RES, "e1_table.md"), "w", encoding="utf-8").write("\n".join(lines) + "\n")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=2000)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()
    out = run(args.n, args.seed)
    print(json.dumps(out["summary"], indent=2))
