"""
Interventional ground truth: N(F), S(F), R(M).

Given a frozen model and a set of test packets, we measure what the model ACTUALLY uses
by intervening on packets with PacketDO (protocol-valid do()), never by deleting features.

  N(F) necessity  = Acc(clean) - Acc(do(F := resample))          [how much M needs F]
  S(F) sufficiency = Acc(do(all-other-intervenable := resample))  [how far F alone carries M]
  R(M) redundancy  = number of DISJOINT minimal sufficient field sets (iterative removal)

All interventions resample from the pooled (class-agnostic) empirical marginal, so the
field's marginal is preserved and only its label-correlation is destroyed. The model is
never retrained. Works for both the ByteCNN (re-extract byte window from the intervened
packet) and RFFlow (re-extract features).

This module is representation-agnostic: it takes an `evaluate(packets)->accuracy` closure.
"""
import warnings; warnings.filterwarnings("ignore")
import numpy as np
from scapy.all import IP
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from packetdo import operator as op, fields as F
from packetdo.sampler import PooledSampler

# fields the synthetic benchmark actually varies (keeps R(M)/N(F) focused + fast)
CANDIDATE_FIELDS = ["ip.ttl", "ip.id", "ip.src", "ip.dst", "tcp.sport", "tcp.dport",
                    "tcp.window", "tcp.seq", "tcp.flags", "payload"]


def _apply(packets, field_names, sampler):
    """Return new packet objects with do(field := resample) applied for each field in the set.

    Fast path: set every requested field on a single copy, then do ONE scapy rebuild
    (round-trip), instead of one rebuild per field. Correctness is identical because all
    dependent fields (checksums/lengths/offsets) are recomputed once at the end.
    """
    if not field_names:
        return packets
    out = []
    for pk in packets:
        p = pk.copy()
        changed = False
        for fn in field_names:
            donor = sampler.draw(fn)
            if donor is not None and F.field_present(p, fn):
                F.REGISTRY[fn].set(p, donor)
                changed = True
        out.append(op._rebuild(p) if changed else pk)
    return out


def necessity(packets, y, evaluate, sampler, fields=CANDIDATE_FIELDS):
    base = evaluate(packets, y)
    N = {}
    for fn in fields:
        inter = _apply(packets, [fn], sampler)
        N[fn] = round(base - evaluate(inter, y), 4)
    return base, N


def sufficiency(packets, y, evaluate, sampler, fields=CANDIDATE_FIELDS):
    S = {}
    for fn in fields:
        others = [g for g in fields if g != fn]
        inter = _apply(packets, others, sampler)
        S[fn] = round(evaluate(inter, y), 4)
    return S


def redundancy(packets, y, evaluate, sampler, fields=CANDIDATE_FIELDS, tau=0.10, max_sets=5):
    """Count disjoint minimal sufficient sets.

    Iteratively: on the packets with all previously-found sets already neutralised, find a
    minimal set of remaining fields whose PRESENCE the model can still use to stay above
    chance+tau. Neutralise it, repeat. R = number of such disjoint sets found before the
    model collapses to chance. R>1 => substitutable shortcuts => attribution ill-posed.
    """
    chance = max(np.mean(y == 0), np.mean(y == 1))
    remaining = list(fields)
    neutral = []
    sets = []
    for _ in range(max_sets):
        # accuracy with all found sets neutralised
        base_pk = _apply(packets, neutral, sampler) if neutral else packets
        base_acc = evaluate(base_pk, y)
        if base_acc < chance + tau:
            break  # model already dead; no further disjoint set exists
        # greedily grow a minimal set from `remaining` whose removal drops acc the most
        cur = []
        while True:
            best, best_drop = None, -1
            acc_now = evaluate(_apply(packets, neutral + cur, sampler) if (neutral + cur) else packets, y)
            for fn in remaining:
                if fn in cur:
                    continue
                drop = acc_now - evaluate(_apply(packets, neutral + cur + [fn], sampler), y)
                if drop > best_drop:
                    best, best_drop = fn, drop
            if best is None or best_drop <= 0.01:
                break
            cur.append(best)
            # stop growing once neutralising `cur` brings acc near chance
            if evaluate(_apply(packets, neutral + cur, sampler), y) < chance + tau:
                break
        if not cur:
            break
        sets.append(cur)
        neutral += cur
        remaining = [f for f in remaining if f not in cur]
        if not remaining:
            break
    return sets


def make_sampler(packets, seed=0):
    return PooledSampler(packets, seed=seed)
