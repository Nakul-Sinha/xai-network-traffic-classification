# ORG-B consolidated report: robustness and operator-sensitivity

**Org:** ORG-B (Robustness & Operator-Sensitivity). **Parcels:** B1 multi-seed robustness,
B2 E5 operator sensitivity, B3 extra explainers (KernelSHAP, LIME).
**Status:** all three parcels DONE with real, executed numbers. Ready for ORG-C verification;
nothing below is promoted to the paper until ORG-C reproduces it.

**Raw outputs:**
- B1: `Experiments/benchmark/aggregate_seeds.py`, `Experiments/benchmark/results/robustness.md`,
  `results/audit_p{05,07,09,10}_seed{1..4}.json` (+ seed-0 `audit_p*.json`), `results/run_seed{3,4}.log`
- B2: `Experiments/benchmark/run_e5.py`, `results/e5_operator_sensitivity.{md,json}`
- B3: `Experiments/benchmark/explainers_extra.py`, `run_extra.py`, `results/extra_explainers.{md,json}`

---

## 1. Multi-seed robustness (B1): did the seed-0 FC values hold?

Five seeds (0-4), each reshuffling train/test split, model training, and the PacketDO resampler
stream; datasets fixed. All cells mean +/- sample sd (ddof=1). Full tables in
`results/robustness.md`.

**Verdict: the headline holds; two secondary seed-0 claims must be weakened.**

Held robustly (paper-ready pending ORG-C):

- **CNN Saliency false-confidence is stable across every seed and strength**: FC at
  p = 0.5/0.7/0.9/1.0 = 0.743/0.700/0.717/**0.684**, sd <= 0.048 (per-seed at p=1.0:
  [0.667, 0.667, 0.75, 0.667, 0.667]). This is the robust headline number.
- **Occlusion FC = 0 in every seed and strength** (CNN). Its clean record survives.
- **Ground truth is stable**: CNN N(tcp.window) 0.273 +/- 0.011 (p=0.5) rising to
  0.501 +/- 0.020 (p=1.0); CNN N(ip.ttl) <= 0.004 at all p; the CNN commits to tcp.window in
  5/5 seeds. Null control N(tcp.sport) within +/- 0.004 of 0 in every cell — the interventional
  estimator itself is seed-robust.
- **TreeSHAP's redundancy failure is real but conditional, and now mechanistically explained**:
  RF TreeSHAP FC at p=1.0 = 0.200 +/- 0.274, bimodal per-seed [0.5, 0.5, 0, 0, 0]. FC = 0.5
  exactly in the seeds where the RF commits to a single one of the two perfectly-correlated
  shortcuts (the other field's N ~ 0), FC = 0 when it spreads reliance across both. The per-seed
  N diagnostics in robustness.md show the mode tracking realized reliance seed by seed. The
  correct paper claim: *exact Shapley values split credit by the data's correlation structure,
  so whenever the model commits to one of two redundant shortcuts (2/5 RF seeds; 5/5 CNN seeds),
  TreeSHAP fabricates confidence in the unused one.* Not "TreeSHAP FC = 0.5", which is
  seed-contingent.

Revised (the E2-E4 analysis doc and the board's standing-findings row must be edited before
promotion):

- **"IG clean at p=1.0" is FALSE**: IntegratedGradients FC at p=1.0 = 0.300 +/- 0.274, nonzero
  in 3/5 seeds (per-seed [0, 0.5, 0.5, 0.5, 0]). Seed 0 was the favorable draw. IG's graded
  story (FC falls with p: 0.700 -> 0.567 -> 0.400 -> 0.300) survives, but the endpoint is
  "reduced", not "clean".
- **"DeepSHAP FC = 0 at all strengths" is FALSE**: DeepSHAP FC at p=0.5 = 0.233 +/- 0.325
  (per-seed [0, 0, 0, 0.667, 0.5]). DeepSHAP is clean at p >= 0.7 in all 5 seeds; at weak
  planting it fails in 2/5 seeds.

**Data-integrity incident (must be disclosed to ORG-C).** A concurrent background chain
initially *fabricated* multi-seed files by copying seed-0 output to `*_seedN.json` names
(caught: byte-identical files with internal `seed=0`). The corrupt files were replaced by
genuine reruns (seeds 1-2 by a corrected chain, seeds 3-4 run directly, GPU serialized). All 20
files now pass provenance checks: internal seed field matches filename, no byte-identical
cross-seed duplicates, seed-0 unchanged vs a snapshot kept in the B1 session scratchpad
(`seed_snapshot/`). `aggregate_seeds.py` enforces the same guard and exits nonzero on any
mismatch. **Lead's independent re-check (this session): confirmed** — all 16 seed-1..4 JSONs
have matching internal seeds and unique MD5s, and the per-seed headline values re-extracted
from the JSONs match robustness.md exactly.

## 2. E5 operator sensitivity (B2): the ranking flip — the paper's "so what"

Setup: p=1.0 ByteCNN (seed 0, acc 0.9862, test n=800). Cumulative deletion over each
explainer's own top-j field ranking (j=1..10) under (i) zero-mask and (ii) PacketDO (5 shared
resampling seeds). Ground truth: N(tcp.window) = 0.4838, all other |N| <= 0.0063; all four
explainers rank tcp.window #1.

**The explainer ranking does not survive the operator change.**

| operator | AOPC ranking | AOPC spread |
|---|---|---|
| zero-mask | IG 0.4776 > Saliency 0.4730 > DeepSHAP 0.4724 > Occlusion 0.4629 | 0.0147 |
| PacketDO | IG 0.4882 ~ Occlusion 0.4881 ~ Saliency 0.4875 ~ DeepSHAP 0.4872 | 0.0010 |

Spearman rho = 0.40 (p=0.60), Kendall tau = 0.333 (p=0.75). Reversed pairs:
Saliency-vs-Occlusion and DeepSHAP-vs-Occlusion.

Why this is C4, the paper's "so what":

1. **The interventional ground truth dictates what a sound deletion metric must do here.** The
   model provably uses exactly one field, and all four explainers put it first — so all four
   top-1 rankings are equally faithful, removals at j >= 2 touch only N ~ 0 fields, and a valid
   metric must score the four (near-)identically. **PacketDO does exactly that**: spread 0.0010,
   within resampling noise (per-seed sd ~0.0058; paired per-seed table in the md). The nominal
   PacketDO order (IG > Occ > Sal > DS) must be quoted as a **statistical tie**, never as a
   real ordering.
2. **Zero-mask fabricates a deterministic ordering 15x larger, entirely on protocol-invalid
   inputs** (cf. E1: only 22% of zero-mask outputs parse as valid packets). Its curves are
   non-monotone — accuracy *rises* after some deletions — confirming the model's off-manifold
   response is arbitrary.
3. **The fabricated ordering is anti-correlated with the audit's faithfulness evidence**:
   zero-mask demotes Occlusion (FC = 0 in every seed of E2/E4) to last while placing Saliency
   (FC = 0.67, the robust headline failure) above it. A practitioner choosing explainers by
   zero-mask deletion-AUC would pick the *less* faithful method.

Consequence for the field: every published NTC explainer comparison scored by zero-mask
deletion inherits an operator artifact, exactly as C4 conjectured. This is the sentence the
paper leads with.

## 3. Extra explainers (B3): KernelSHAP + LIME complete the C3 matrix

Protocol identical to the seed-0 `run_audit.py` cell on the p=1.0 ByteCNN (split seed 0,
sampler seed 1, n_test = 800; ground truth byte-identical to `audit_p10.json`); 150 explained
samples each.

| explainer | rho | precision@2 | false-confidence | blind-spot | s / 100 samples |
|---|---|---|---|---|---|
| KernelSHAP (150 samples, k-means-10 background) | 0.183 | 0.5 | **0.0** | 0.0 | 10.78 |
| LIME (lime_tabular, 1000 perturbations/sample) | 0.311 | 0.5 | **0.667** | 0.0 | 1.04 |

- precision@2 = 0.5 is the *ceiling* at p=1.0 (only one truly necessary field), matching all
  four existing CNN explainers in that cell — not an underperformance.
- **LIME's FC = 0.667 has a verified mechanism that is itself paper-grade evidence**: it falsely
  names `tcp.dport` (constant 443) and the `ip.dst` prefix (constant 192.168). sklearn's
  `StandardScaler` inside `LimeTabularExplainer` sets `scale_ = 1.0` for zero-variance features
  (verified on this data), so LIME perturbs constant header fields with unit-variance noise —
  protocol-impossible inputs — and reads the CNN's off-manifold response as importance. The
  protocol-invalidity thesis occurring *inside an explainer's own perturbation kernel*, not just
  inside a faithfulness metric. KernelSHAP is clean because coalition replacement uses real
  background byte values, which keep constant fields constant.
- **Line-rate cost angle**: KernelSHAP ~10.8 s and LIME ~1.0 s per 100 packets (80-byte toy
  window, GPU-batched predict) vs sub-second-for-400 for gradient methods — perturbation
  explainers are orders of magnitude from line rate even in the toy setting.

## 4. Consolidated picture for the paper

- **Precision vs false-confidence gap survives 5 seeds**: explainers find the true shortcut
  (precision at ceiling everywhere) but Saliency (0.68-0.74) and LIME (0.67) confidently name
  fields with N ~ 0; IG does so at all strengths in expectation; TreeSHAP and DeepSHAP fail
  conditionally (model-commitment / weak-planting regimes); Occlusion and KernelSHAP are clean.
- **The failure axis lines up with the operator thesis**: the clean methods (Occlusion,
  KernelSHAP) perturb with realized/observed values; the dirty ones inject gradients or
  off-manifold noise. LIME's mechanism and E5's zero-mask artifact are the same defect at two
  different layers of the stack.
- **E5 is the C4 deliverable**: deletion verdicts are operator-dependent; the zero-mask ordering
  is manufactured; PacketDO returns the tie that the known ground truth demands.

## 5. What a verifier (ORG-C) must double-check

1. **Seed-file provenance** (highest priority, given the fabrication incident): re-run
   `aggregate_seeds.py` (it exits nonzero on mismatch); independently confirm internal
   `seed` fields, absence of byte-identical cross-seed duplicates, and that regenerating one
   seed (e.g. `run_audit.py --seed 3` on one p) reproduces the stored JSON. Note the driver
   overwrites `audit_summary.md` as a side effect (it was restored to seed-0 content).
2. **The two revised claims**: confirm IG FC at p=1.0 is nonzero in 3/5 seeds and DeepSHAP FC
   at p=0.5 nonzero in 2/5 seeds, then ensure `Analysis/E2-E4-synthetic-benchmark.md` (points
   3-4 and the FC tables) and the ORCHESTRATOR.md standing-findings row are edited accordingly
   — both currently state the seed-0 versions ("IG 0.00 at p=1.0", "DeepSHAP 0.00 all
   strengths").
3. **E5 tie claim**: verify from `e5_operator_sensitivity.json` that the PacketDO AOPC spread
   (0.0010) is smaller than the per-seed sd (~0.0058) using the paired per-seed table; the
   paper must quote PacketDO as a tie, and any text quoting "IG > Occ > Sal > DS" as a real
   ordering is an error. Also note Spearman/Kendall p-values (0.60/0.75) are meaningless at
   n=4 — flag if the paper text leans on them rather than on the reversed-pairs + spread
   argument.
4. **E5 scope caveat**: single model seed (seed 0), single strength (p=1.0), matching the
   Phase-2 protocol. Multi-seed E5 and weaker-p variants (where rankings could diverge at j=1)
   are a queued extension (`run_e5.py` needs only a `--p` flag generalization); the paper's C4
   claim should be scoped to what was run.
5. **LIME mechanism**: reproduce the `scale_[22] = scale_[23] = 1.0` StandardScaler check and
   confirm the named fields (`ip.dst`, `tcp.dport`) are the constant ones; also confirm the
   0.2*max naming threshold matches `run_audit.py`'s convention so FC is comparable across
   B3 and the main audit.
6. **rho remains a weak instrument** in single-field cells (ranking dominated by noise among
   N ~ 0 fields, and NaN-handling in aggregation when scores have zero variance); FC and
   precision@k are load-bearing. Check no paper text ranks explainers by rho.
7. **RF ground truth at p=1.0 is seed-bimodal by design** (N(ttl)/N(win) trade places per
   seed): mean +/- sd there (0.317 +/- 0.182 / 0.184 +/- 0.180) describes a mixture, not a
   central tendency — the paper should show per-seed values or the commitment fraction
   instead of the mean.

## 6. Board updates for the orchestrator

- `multi-seed robustness (5 seeds)` RUNNING -> **DONE** (pending ORG-C), output
  `results/robustness.md` + 20 audit JSONs.
- `E5 operator sensitivity` QUEUED -> **DONE** (pending ORG-C), output
  `results/e5_operator_sensitivity.{md,json}`.
- `extra explainers (KernelSHAP, LIME)` QUEUED -> **DONE** (pending ORG-C), output
  `results/extra_explainers.{md,json}`.
- Standing-findings row for E2/E4 needs the two weakened claims (IG at p=1.0, DeepSHAP at
  p=0.5) before any promotion to Working/.
