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


def redundancy_legacy(packets, y, evaluate, sampler, fields=CANDIDATE_FIELDS, tau=0.10, max_sets=5):
    """DEPRECATED removal-based counter. Kept only for the ablation in validate_rm.py.

    Grows a set by single-field removal and stops each set once its removal drops accuracy below
    chance+tau. This is structurally unable to return R>1: the inner loop drives accuracy to chance
    before the outer loop can look for a second disjoint set, and for two mutually substitutable
    shortcuts single-field removal shows no drop, so it returns R=0 (reports LESS redundancy than a
    committed model). Superseded by the sufficiency-based `redundancy()` below.
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


def _keep_only_acc(packets, y, evaluate, sampler, keep, allfields):
    """Accuracy when ONLY `keep` is intact and every other candidate field is resampled.

    This is set-level sufficiency: it measures whether `keep` alone carries the model while the
    rest of the candidate fields are randomised from their pooled marginal.
    """
    others = [f for f in allfields if f not in keep]
    return evaluate(_apply(packets, others, sampler), y)


def _minimal_sufficient_set(packets, y, evaluate, sampler, pool, allfields, thresh, max_size=4):
    """Forward-select fields from `pool` until keeping-only-them is sufficient, then prune to minimal.
    Returns None if no sufficient subset of `pool` exists."""
    keep = []
    while len(keep) < max_size:
        acc = (_keep_only_acc(packets, y, evaluate, sampler, keep, allfields) if keep
               else evaluate(_apply(packets, allfields, sampler), y))
        if acc >= thresh:
            break
        best, best_acc = None, acc
        for f in pool:
            if f in keep:
                continue
            a = _keep_only_acc(packets, y, evaluate, sampler, keep + [f], allfields)
            if a > best_acc + 1e-9:
                best, best_acc = f, a
        if best is None:
            return None
        keep.append(best)
    if not keep or _keep_only_acc(packets, y, evaluate, sampler, keep, allfields) < thresh:
        return None
    changed = True
    while changed and len(keep) > 1:
        changed = False
        for f in list(keep):
            trial = [g for g in keep if g != f]
            if _keep_only_acc(packets, y, evaluate, sampler, trial, allfields) >= thresh:
                keep = trial
                changed = True
                break
    return keep


def redundancy(packets, y, evaluate, sampler, fields=CANDIDATE_FIELDS, suff_frac=0.5, max_sets=5):
    """Count DISJOINT minimal sufficient field sets (sufficiency-based, corrected).

    A set S is SUFFICIENT if keeping S and resampling every other candidate field retains at least
    `suff_frac` of the model's above-chance skill:  acc(keep=S) >= chance + suff_frac*(base-chance).
    We greedily extract a minimal sufficient set, remove its fields from the pool, and search for
    another DISJOINT one, until none remains. R(M) = number of such sets. R>1 means the model holds
    substitutable shortcuts, so the target of attribution is non-unique.

    The removal-based `redundancy_legacy` above cannot return R>1; this replaces it. The sufficiency
    fraction is a disclosed parameter (default 0.5, i.e. a set must recover half the model's skill).
    """
    base = evaluate(packets, y)
    chance = max(np.mean(y == 0), np.mean(y == 1))
    thresh = chance + suff_frac * (base - chance)
    pool = list(fields)
    sets = []
    for _ in range(max_sets):
        S = _minimal_sufficient_set(packets, y, evaluate, sampler, pool, fields, thresh)
        if not S:
            break
        sets.append(S)
        pool = [f for f in pool if f not in S]
        if not pool:
            break
    return sets


def make_sampler(packets, seed=0):
    return PooledSampler(packets, seed=seed)
