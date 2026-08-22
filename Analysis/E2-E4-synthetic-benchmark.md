# E2/E3/E4 (synthetic benchmark): planted-shortcut ground truth and the explainer audit

**Status:** complete for the synthetic benchmark. Code: `Experiments/benchmark/`
(`generate.py`, `models.py`, `groundtruth.py`, `explainers.py`, `run_audit.py`). Raw results:
`Experiments/benchmark/results/audit_*.json` and `audit_summary.md`.

## Design

Two-class synthetic packet traffic with a weak genuine signal (payload length) and two *planted*
artifacts, `ip.ttl` and `tcp.window`, each correlated with the label at effective marginal
`0.5 + 0.5p` for planting strength `p in {0.5, 0.7, 0.9, 1.0}`. Because we plant the signal, we know
the ground-truth decision basis. Two model families are trained per strength: a **ByteCNN** on raw
bytes and a **RandomForest** on named per-packet features. Ground truth is measured by PacketDO
intervention, never by deletion:

- `N(F)` necessity = accuracy drop under `do(F := resample from pooled marginal)`
- `S(F)` sufficiency, `R(M)` = number of disjoint sufficient field sets
- null-intervention control: `tcp.sport`, a field never correlated with the label (must give `N~0`).

## E3: models rely on the planted artifacts, and the null control is clean

| p | ByteCNN acc | N(ttl) | N(win) | N(payload) | N(null=sport) | R |
|---|---|---|---|---|---|---|
| 0.5 | 0.76 | 0.00 | 0.27 | 0.01 | 0.00 | 1 |
| 0.7 | 0.85 | 0.00 | 0.34 | 0.00 | 0.01 | 1 |
| 0.9 | 0.94 | 0.00 | 0.44 | 0.02 | 0.00 | 1 |
| 1.0 | 0.99 | 0.00 | 0.48 | -0.01 | 0.00 | 1 |

The null-control necessity is ~0 at every strength (largest magnitude 0.006), which validates the
interventional estimator: resampling a field the model does not use does not change accuracy. The
CNN's reliance on `tcp.window` rises monotonically with `p` while `N(ttl) ~ 0` throughout: **given
two equally predictive shortcuts, the CNN commits to exactly one** (window) and ignores the other
(ttl). This is the redundancy phenomenon, measured: `R(M)=1` because the model actually learned only
one of the two available shortcuts. (The RandomForest spreads reliance across ttl, window and
payload_len at low `p` and concentrates on window at `p=1.0`.)

## E2/E4: the explainer audit against N(F)

Two metrics carry the result. **Precision@k** (with k = number of truly necessary fields) asks *does
the explainer rank the model's real shortcut at the top?* **False-confidence** asks *does it also
light up fields the model does not use?* They are independent, and the gap between them is the
finding.

**Precision@k = 1.0 for every explainer, model, and strength.** Every method - Saliency, Integrated
Gradients, DeepSHAP, Occlusion, RF impurity, TreeSHAP - correctly ranks the model's actual shortcut
among its top-k features. Post-hoc explanation is *not* failing to find the truth.

**False-confidence is high and method-dependent.** The tables below are the SEED-0 values and are
SUPERSEDED by the multi-seed (n=5) values in the "Multi-seed update" section further down; do NOT
copy the seed-0 tables into the paper. In particular the seed-0 zeros for IG at p=1.0 and DeepSHAP
across p are NOT robust (IG p=1.0 -> 0.300+/-0.274; DeepSHAP p=0.5 -> 0.233+/-0.325). Retained only to
show the per-strength shape on one seed:

| explainer (ByteCNN) SEED 0 ONLY - superseded | p=0.5 | p=0.7 | p=0.9 | p=1.0 |
|---|---|---|---|---|
| Saliency | 0.80 | 0.75 | 0.75 | 0.67 |
| Integrated Gradients | 0.75 | 0.67 | 0.50 | 0.00 (NOT robust: 0.300+/-0.274 over 5 seeds) |
| DeepSHAP | 0.00 (NOT robust: 0.233+/-0.325 at p=0.5) | 0.00 | 0.00 | 0.00 |
| Occlusion | 0.00 | 0.00 | 0.00 | 0.00 (clean 5/5, but partly by construction - see caveat) |

| explainer (RandomForest) SEED 0 ONLY - superseded | p=0.5 | p=0.7 | p=0.9 | p=1.0 |
|---|---|---|---|---|
| Impurity | 0.63 | 0.00 | 0.33 | 0.50 |
| TreeSHAP | 0.00 | 0.00 | 0.33 | 0.50 (multi-seed: 0.200+/-0.274, bimodal - conditional on model commitment) |

## What this says (the precise, defensible claim)

1. **The danger is not missed truth, it is added falsehood.** Explainers reliably surface the field
   the model uses (precision at k = number-of-necessary-fields is 1.0; note the stored
   `precision_at_k` JSON field uses a hard-coded k=2 and reads 0.5 because the CNN has only one
   necessary field, so cite the adaptive-k convention, not the raw JSON value), but gradient saliency
   and, at weak planting, Integrated
   Gradients *also* attribute large importance to a redundant field the model provably does not use
   (`N ~ 0`). An analyst reading the map cannot tell the used field from the merely-correlated one.
2. **Exactness does not rescue faithfulness.** TreeSHAP computes exact Shapley values, yet at `p=1.0`
   it assigns 50% false confidence: when the model commits to one of two perfectly-correlated
   shortcuts, TreeSHAP still splits credit across both, because it reflects the data's correlation
   structure, not the model's realized reliance. This is the redundancy failure mode that
   single-explanation evaluation cannot see, made quantitative.
3. **Intervention-aligned methods are the most faithful.** DeepSHAP and Occlusion hold false
   confidence at 0 across all strengths for the CNN. Occlusion is itself a (feature-space)
   intervention, which foreshadows E5: *how* you remove a feature determines the verdict, and the
   protocol-valid removal operator (PacketDO) is the one whose ground truth these methods are scored
   against.
4. **Graded planting is informative.** Integrated Gradients' false confidence falls from 0.75 to 0
   as the artifact strengthens - a single-point (p=1.0 only) study would have called IG faithful and
   missed that it fabricates importance precisely when the true signal is weak, which is the regime
   real traffic classifiers operate in.

## Multi-seed update (ORG-B, seeds 0-4; supersedes single-seed claims above)

A 5-seed pass (each reshuffling split, training, and the resampler stream) revised two seed-0 claims
and confirmed the rest. Full tables: `Experiments/benchmark/results/robustness.md`.

- **Held:** CNN Saliency FC = 0.684 +/- 0.037 at p=1.0 (0.68-0.74 across all p, sd <= 0.048);
  CNN Occlusion FC = 0 in every seed/strength; ground truth stable (N(tcp.window) 0.273->0.501 with
  p, N(ttl) <= 0.004, null control within +/-0.004). The CNN commits to tcp.window in 5/5 seeds.
- **Revised - "IG is clean at p=1.0" is FALSE:** IntegratedGradients FC at p=1.0 = 0.300 +/- 0.274,
  nonzero in 3/5 seeds (seed 0 was the favorable draw). IG's graded trend survives (FC falls with p),
  but the endpoint is "reduced", not "clean".
- **Revised - "DeepSHAP FC = 0 at all strengths" is FALSE:** DeepSHAP FC at p=0.5 = 0.233 +/- 0.325
  (fails in 2/5 seeds); clean at p >= 0.7 in all seeds.
- **TreeSHAP refined:** FC at p=1.0 is bimodal per-seed [0.5,0.5,0,0,0] = 0.200 +/- 0.274. FC=0.5
  exactly when the RF commits to one of two correlated shortcuts. The correct paper claim is
  mechanistic: *exact Shapley values split credit by the data's correlation structure, so whenever a
  model commits to one of several redundant shortcuts (2/5 RF seeds, 5/5 CNN seeds) TreeSHAP
  fabricates confidence in the unused one* - not a fixed "TreeSHAP FC = 0.5".

**Data-integrity note:** an early background chain fabricated multi-seed files by copying seed-0
output to *_seedN names (a file-naming race). It was caught (byte-identical files, internal seed=0),
replaced with genuine reruns, and `aggregate_seeds.py` now enforces a provenance guard. ORG-C
independently re-audits provenance.

## Threats / caveats (for the write-up)

- `rho` (Spearman attribution-vs-N) is reported in `audit_summary.md` but is a weak instrument here:
  most fields have `N ~ 0`, so the ranking is dominated by noise among zero-necessity fields.
  False-confidence and precision@k are the load-bearing metrics; `rho` is secondary.
- **Occlusion circularity (state in paper):** Occlusion removes a feature by permutation, structurally
  close to the PacketDO ground-truth operator, so its FC=0 is partly by construction. E5 (zero-mask vs
  PacketDO deletion) is where this is disentangled.
- This is the *synthetic* half (known ground truth). The real-data half (E4 on CIC-IDS2017/ISCX
  natural artifacts) is Phase 3 and provides ecological validity.
- The RF "blind-spot" at low `p` (0.33) reflects that the RF genuinely uses 3 fields while top-k
  names 2; it is correct behavior of the metric, not an explainer failure per se.
