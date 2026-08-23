"""
Phase D (second real corpus): byte-level PacketDO on REAL captured packets (USTC-TFC2016).

Companion to pcap_bytelevel.py (ISCX VPN). Same audit pipeline, a DIFFERENT real capture
corpus, to show the off-manifold thesis and the false-confidence audit are not single-dataset.

Corpus: USTC-TFC2016 (Wang et al., ICOIN 2017), a malware/benign traffic-classification set of
real packet captures. We form a clean 2-class malware-family task on the two families whose
captures carry INTACT checksums (real, un-anonymised headers): Miuref (class 0) vs Geodo (class 1).
The USTC *benign* application captures are IP-anonymised (rewritten src/dst, stale checksums, 0%
baseline validity), so they are deliberately NOT used here: mixing them would (a) break the
"real packets, real checksums" premise of the byte-level study and (b) plant a first-octet
anonymisation artefact as a fake shortcut. Miuref and Geodo are both raw, valid captures.

Link layer: USTC pcaps are Ethernet-framed (unlike the raw-IP ISCX subset). We normalise every
packet to a clean scapy IP object with bytes(pk[IP]) -> IP(raw), stripping the Ethernet header, so
the byte window and the IP20+TCP20 offset map line up exactly as in the ISCX driver.

  E1-real : zero-mask vs PacketDO protocol-validity on real packets (with options).
  audit   : train a ByteCNN, measure N(F) by PacketDO, audit IG/Saliency/Occlusion against it.

Run: python ustc_bytelevel.py
Writes results/ustc_bytelevel.json and results/ustc_bytelevel.md
"""
import warnings; warnings.filterwarnings("ignore")
import json, os, sys
from collections import defaultdict
import numpy as np
from scapy.all import PcapReader, Ether, IP, TCP

HERE = os.path.dirname(os.path.abspath(__file__))
PCAP = os.path.join(HERE, "ustc")        # git-ignored dataset dir; see ustc_DATASET.md
RES = os.path.join(HERE, "results")
sys.path.insert(0, os.path.dirname(HERE))  # Experiments/
from packetdo import operator as op, validity as vd, fields as F
from packetdo.sampler import PooledSampler
from benchmark import models as M, groundtruth as GT, explainers as EX
from benchmark.generate import pkt_to_bytes

CLASSES = {
    0: ["Miuref.pcap"],   # click-fraud trojan; HTTP/TCP with real payloads
    1: ["Geodo.pcap"],    # Emotet/Geodo banking trojan; TCP C2 beaconing
}
CLASS_NAMES = {0: "Miuref", 1: "Geodo"}
CAP = 5000           # TCP packets per class
SEED = 0


def load_class(files, cap):
    """Stream real TCP/IP packets, normalise link layer, re-parse to clean scapy IP objects.

    Robust to link framing: Ethernet-framed captures (USTC) and raw-IP captures (ISCX) both
    reduce to bytes(pk[IP]) -> IP(raw), which strips any Ethernet header and yields the
    canonical IP20+TCP20 byte layout the offset map and pkt_to_bytes window assume. Captured
    bytes (and checksums) are preserved through the round-trip.
    """
    pkts = []
    for fn in files:
        path = os.path.join(PCAP, fn)
        for pk in PcapReader(path):
            if pk.haslayer(IP) and pk.haslayer(TCP):
                raw = bytes(pk[IP])          # strips Ethernet if present; raw-IP passes through
                if len(raw) >= 40:           # need at least IP+TCP fixed headers
                    pkts.append(IP(raw))
            if len(pkts) >= cap:
                break
        if len(pkts) >= cap:
            break
    return pkts[:cap]


def e1_real(pkts, seed=0):
    """Identical methodology to E1, on real packets."""
    base_valid = sum(vd.valid(bytes(p)) for p in pkts)
    sampler = PooledSampler(pkts, seed=seed + 1)
    per_field = {}
    viol = defaultdict(lambda: defaultdict(int))
    for field in F.INTERVENABLE:
        present = [p for p in pkts if F.field_present(p, field)]
        if not present:
            continue
        zmv = zmt = dov = dot = 0
        for p in present:
            zc = vd.check(op.zero_mask_bytes(p, field)); zmt += 1
            if zc.get("valid"):
                zmv += 1
            else:
                for k, v in zc.items():
                    if k not in ("valid", "pkt") and v is False:
                        viol["zero_mask"][k] += 1
            donor = sampler.draw(field)
            if donor is None:
                continue
            dc = vd.check(op.packet_do_bytes(p, field, donor)); dot += 1
            if dc.get("valid"):
                dov += 1
            else:
                for k, v in dc.items():
                    if k not in ("valid", "pkt") and v is False:
                        viol["packet_do"][k] += 1
        per_field[field] = {"n": zmt,
                            "zero_mask_valid_rate": round(zmv / zmt, 4) if zmt else None,
                            "packet_do_valid_rate": round(dov / dot, 4) if dot else None}
    zm = [v["zero_mask_valid_rate"] for v in per_field.values() if v["zero_mask_valid_rate"] is not None]
    do = [v["packet_do_valid_rate"] for v in per_field.values() if v["packet_do_valid_rate"] is not None]
    return {
        "baseline_valid_rate": round(base_valid / len(pkts), 4),
        "zero_mask_macro_valid_rate": round(float(np.mean(zm)), 4),
        "packet_do_macro_valid_rate": round(float(np.mean(do)), 4),
        "zero_mask_violations": dict(viol["zero_mask"]),
        "packet_do_violations": dict(viol["packet_do"]),
        "per_field": per_field,
    }


def main():
    print("loading real packets...", flush=True)
    p0 = load_class(CLASSES[0], CAP)
    p1 = load_class(CLASSES[1], CAP)
    pkts = p0 + p1
    y = np.array([0] * len(p0) + [1] * len(p1))
    print(f"  {CLASS_NAMES[0]}(TCP)={len(p0)}  {CLASS_NAMES[1]}(TCP)={len(p1)}", flush=True)

    # ---- E1 on real packets ----
    print("E1-real: operator validity on real packets...", flush=True)
    e1 = e1_real(pkts, SEED)
    print(f"  baseline valid={e1['baseline_valid_rate']}  zero-mask={e1['zero_mask_macro_valid_rate']}"
          f"  PacketDO={e1['packet_do_macro_valid_rate']}", flush=True)

    # ---- byte windows + split ----
    X = np.stack([pkt_to_bytes(pk) for pk in pkts])
    rng = np.random.default_rng(SEED)
    idx = rng.permutation(len(X))
    X, y, pkts = X[idx], y[idx], [pkts[i] for i in idx]
    ntr = int(0.7 * len(X))
    Xtr, ytr, Xte, yte = X[:ntr], y[:ntr], X[ntr:], y[ntr:]
    pkte = pkts[ntr:]
    GT_N = min(800, len(pkte))
    pkte, Xte, yte = pkte[:GT_N], Xte[:GT_N], yte[:GT_N]

    print("training ByteCNN on real packets...", flush=True)
    cnn = M.train_cnn(Xtr, ytr, epochs=40, seed=SEED)
    acc = round(M.cnn_acc(cnn, Xte, yte), 4)
    print(f"  test acc={acc}", flush=True)

    sampler = GT.make_sampler(pkts, seed=SEED + 1)

    def eval_cnn(packets, yy):
        return M.cnn_acc(cnn, np.stack([pkt_to_bytes(pk) for pk in packets]), yy)

    print("necessity N(F) via PacketDO on real packets...", flush=True)
    base, N = GT.necessity(pkte, yte, eval_cnn, sampler)
    R = GT.redundancy(pkte, yte, eval_cnn, sampler)

    print("explainer attributions + audit...", flush=True)
    expl = {
        "IntegratedGradients": EX.bytes_to_fields(EX.cnn_integrated_gradients(cnn, Xte)),
        "Saliency": EX.bytes_to_fields(EX.cnn_saliency(cnn, Xte)),
        "Occlusion": EX.bytes_to_fields(EX.cnn_occlusion(cnn, Xte, yte)),
    }
    audit = {name: EX.audit(sc, N) for name, sc in expl.items()}

    out = {
        "dataset": "USTC-TFC2016 (Wang et al., ICOIN 2017)",
        "task": "Miuref vs Geodo (malware-family classification), real USTC-TFC2016 packets",
        "link_layer": "Ethernet-framed, normalised to IP via bytes(pk[IP])",
        "classes": CLASS_NAMES,
        "n_per_class": [len(p0), len(p1)], "n_test_gt": GT_N, "cnn_test_acc": acc,
        "e1_real": e1, "base_acc_gt": round(base, 4), "N": N, "R": len(R), "R_sets": R,
        "audit": audit, "attributions_fields": expl,
    }
    os.makedirs(RES, exist_ok=True)
    json.dump(out, open(os.path.join(RES, "ustc_bytelevel.json"), "w"), indent=2)

    # ranked necessity + audit summary
    Nsorted = sorted(N.items(), key=lambda kv: -kv[1])
    L = ["# Phase D (2nd corpus): byte-level PacketDO on real USTC-TFC2016 packets\n",
         f"Dataset: USTC-TFC2016 (Wang et al., ICOIN 2017). "
         f"Task: {CLASS_NAMES[0]} vs {CLASS_NAMES[1]} (malware-family classification). "
         f"Ethernet-framed captures normalised to IP. "
         f"n/class = {len(p0)}/{len(p1)}; ByteCNN test acc = {acc}.\n",
         "## E1-real: operator validity on REAL packets (with options)",
         f"- baseline valid: {e1['baseline_valid_rate']*100:.1f}%",
         f"- zero-mask macro validity: **{e1['zero_mask_macro_valid_rate']*100:.1f}%**",
         f"- PacketDO macro validity: **{e1['packet_do_macro_valid_rate']*100:.1f}%**",
         f"- zero-mask violations: {e1['zero_mask_violations']}",
         f"- PacketDO violations: {e1['packet_do_violations']}\n",
         "## Interventional necessity N(F) (real packets)",
         "| field | N(F) |", "|---|---|"]
    for f, v in Nsorted:
        L.append(f"| {f} | {v} |")
    L += ["", f"R(M) = {len(R)}; sets = {R}", "", "## Explainer audit vs N(F)",
          "| method | rho | precision@k | false-confidence | blind-spot |", "|---|---|---|---|---|"]
    for nm, a in audit.items():
        L.append(f"| {nm} | {a['rho']} | {a['precision_at_k']} | {a['false_confidence']} | {a['blind_spot']} |")
    open(os.path.join(RES, "ustc_bytelevel.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")
    print("saved results/ustc_bytelevel.json + .md", flush=True)
    print("N(F) top:", Nsorted[:4], flush=True)
    for nm, a in audit.items():
        print(f"  {nm}: rho={a['rho']} FC={a['false_confidence']} blind={a['blind_spot']}", flush=True)


if __name__ == "__main__":
    main()
