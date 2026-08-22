# A2 - Destination-Port artifact as real-data ground truth (Track B / E4)

**Script:** `Experiments/realdata/a2_port_artifact.py` (seed 0; all numbers in
`results/a2_port_results.json`). Data: CIC-IDS2017 flow CSV via Parcel A1 loader
(`load_cicids.py`, see `DATASET.md`). Runtime 269 s CPU.

## Setup

- Stratified subsample 700,000 of 2,520,751 flows -> train 490,000 / test 210,000
  (stratified 70/30, 7 classes, 52 numeric flow features).
- Model: RandomForest, 100 trees, `max_depth=20`, `min_samples_leaf=20`, seed 0.
- **Baseline: test accuracy 0.99789, macro-F1 0.91494.** Per-class recall:
  Normal 0.9995, DDoS 0.9982, Port Scanning 0.9964, DoS 0.9903, Brute Force 0.9803,
  Web Attacks 0.8483, Bots 0.3457.
- Interventional necessity N(f) = feature-space do(): permute ONLY column f in the
  held-out set (resample from the pooled empirical marginal, breaking f's dependence
  on all other features and the label), measure the drop. Real-data analogue of the
  synthetic N(F). dst_port: R=10 repeats on the full 210k test set; all 52 features:
  R=5 on a stratified 50k test subset (subset baseline acc 0.99808, macro-F1 0.92656).
- Explainers: TreeSHAP (`tree_path_dependent`, the common default in the audited
  literature) on 1,000 stratified test rows; RF impurity (gini) importances.

## (b) Interventional necessity of Destination Port — the model DOES use the shortcut

**N(dst_port), full test set, R=10:**

| metric | baseline | after do(dst_port) | drop |
|---|---|---|---|
| accuracy | 0.99789 | 0.99355 | **0.00434 +/- 0.00012** |
| macro-F1 | 0.91494 | 0.86702 | **0.04792 +/- 0.00134** |

Destination Port is the **rank-1 necessity feature of all 52 by accuracy drop**
(rank 2 by macro-F1 drop, behind Fwd IAT Min). The drop is concentrated exactly on
the classes the port table in DATASET.md predicts:

| class | recall drop under do(dst_port) |
|---|---|
| Brute Force (ports 21/22) | **-0.3780** (0.9803 -> 0.6024) |
| Bots (port 8080) | -0.0494 |
| DoS (port 80) | -0.0309 |
| DDoS (port 80) | -0.0026 |
| Web Attacks / Port Scanning / Normal | ~0 (0.0000 / 0.0001 / 0.0003) |

Port Scanning's ~0 drop confirms the DATASET.md prediction (scan sweeps spread over
ports; no port signature). DoS/DDoS/Web ride on port 80, which is shared with 10% of
Normal traffic and redundant with volumetric features, so single-feature necessity is
small there; Brute Force's 21/22 signature is genuinely load-bearing.

## (a) Explainer ranking of Destination Port

| explainer view | rank of dst_port (of 52) | value |
|---|---|---|
| TreeSHAP global (mean abs SHAP, samples x classes) | **5** | 0.00589 |
| RF impurity (gini) | **13** | 0.02654 |
| interventional necessity N_acc (ground truth) | **1** | 0.00434 |
| interventional necessity N_f1 | 2 | 0.04792 |

TreeSHAP per-class rank of dst_port: **Bots 1, Brute Force 1, Web Attacks 2, DoS 3**,
Normal 4, DDoS 14, Port Scanning 37. Per-class SHAP is qualitatively faithful: it
puts the port first exactly for the classes whose recall the intervention collapses,
and last for Port Scanning where necessity is ~0. The *global* aggregation is what
buries the shortcut (rank 5), and impurity importance buries it further (rank 13).

## Audit: does SHAP's ranking match interventional necessity?

| statistic | value |
|---|---|
| Spearman rho (SHAP global vs N_acc), 52 features | **0.688** (p = 1.8e-08) |
| Spearman rho (SHAP global vs N_f1) | 0.517 (p = 8.7e-05) |
| Spearman rho (gini vs N_acc / vs N_f1) | 0.670 / 0.508 |
| precision@5 (SHAP top-5 vs N_acc top-5) | **0.40** |
| precision@10 | **0.60** (identical values vs N_f1 ranking) |

Moderate correlation, far from rank-faithful: 3 of SHAP's top-5 and 4 of its top-10
are not in the necessity top-10.

### False confidence (over-attribution to low-necessity features)

SHAP's top-10 vs measured necessity:

| SHAP rank | feature | mean abs SHAP | N_acc | N_f1 |
|---|---|---|---|---|
| 1 | Bwd Packet Length Std | 0.00893 | 0.00064 | 0.0066 |
| 2 | Bwd Packet Length Mean | 0.00799 | 0.00036 | 0.0088 |
| 3 | Packet Length Variance | 0.00723 | 0.00022 | 0.0128 |
| 4 | Packet Length Std | 0.00649 | 0.00024 | 0.0138 |
| 5 | **Destination Port** | 0.00589 | **0.00421** | **0.0484** |
| 6 | Packet Length Mean | 0.00547 | 0.00021 | 0.0129 |
| 7 | Fwd Packet Length Max | 0.00534 | 0.00019 | 0.0109 |
| 8 | Bwd Packet Length Max | 0.00528 | 0.00025 | 0.0054 |
| 9 | Average Packet Size | 0.00514 | 0.00032 | 0.0196 |
| 10 | Total Length of Fwd Packets | 0.00478 | 0.00035 | 0.0123 |

**The false-confidence feature is `Bwd Packet Length Std`** (with its whole family):
SHAP rank 1, yet N_acc = 0.00064 — **15% of dst_port's necessity while outranking
it**. Under the accuracy-necessity criterion used for the synthetic N(F)
(N_acc < 0.002), **9 of SHAP's top 10 are false-confidence features**; every one of
SHAP's top 4 has <= 0.00064 accuracy-necessity and all outrank the true rank-1
shortcut. (Under the stricter dual criterion N_acc < 0.002 AND N_f1 < 0.005 the set
is empty — macro-F1 reveals each has small-but-nonzero minority-class necessity, so
we report the mechanism below rather than calling them inert.)

**Mechanism — redundancy / credit splitting, confirmed by group do():** the 14-column
packet-length family (Fwd/Bwd/overall Packet Length Max/Min/Mean/Std/Variance +
Average Packet Size) fills 9 of SHAP's top-10 slots. Jointly permuting the family
(one shared row permutation: within-family joint distribution preserved, dependence
on everything else broken):

| | max single N_acc | group N_acc | max single N_f1 | group N_f1 |
|---|---|---|---|---|
| packet-length family (14 cols) | 0.00064 | **0.20090** | 0.0196 | **0.60850** |

The family is collectively load-bearing (20 pp accuracy, 61 pp macro-F1) but no
single member is necessary (redundant copies substitute under any single-column
do()). SHAP spreads large credit across all copies, so interchangeable proxies
occupy the top of the global ranking above the irreplaceable shortcut. This is the
real-data false-confidence pattern: single-feature attribution magnitude is read as
single-feature importance, but 9/10 of the top slots have near-zero single-feature
necessity.

### Blind spots (high necessity, unnamed by SHAP)

| feature | N_acc (rank) | N_f1 (rank) | SHAP rank | gini rank |
|---|---|---|---|---|
| **Fwd IAT Min** | 0.00312 (2) | **0.09935 (1)** | **36** | 34 |
| Fwd Header Length | 0.00080 (3) | 0.01463 (4) | 18 | 15 |
| Init_Win_bytes_forward | 0.00048 (5) | 0.00926 | 22 | 26 |
| Init_Win_bytes_backward | 0.00044 (6) | 0.01207 | 14 | 12 |

`Fwd IAT Min` is the strongest failure in the whole audit: the single most necessary
feature by macro-F1 (a 9.9 pp drop, twice dst_port's) is ranked 36/52 by SHAP and
34/52 by impurity. Note three of the four blind spots (`Fwd Header Length`,
`Init_Win_bytes_forward/backward`) are exactly the Engelen flow-construction artifact
columns (DATASET.md sec 2): the documented dataset artifact the model exploits is
systematically under-reported by both explainers. Group do() on the Engelen quartet
(+ `min_seg_size_forward`): group N_acc 0.00358, **group N_f1 0.11535** vs max single
0.00080 / 0.01463 — another collectively-necessary, individually-redundant family.

## Summary numbers (for the E4 table)

- **N(dst_port) = 0.00434 +/- 0.00012 accuracy drop (0.04792 +/- 0.00134 macro-F1),
  rank 1/52 by accuracy-necessity**; recall collapse concentrated on Brute Force
  (-37.8 pp).
- **SHAP rank of dst_port: 5/52 global** (per-class: 1 for Bots and Brute Force);
  impurity rank 13/52.
- **rho(SHAP, N_acc) = 0.688; precision@5 = 0.40, precision@10 = 0.60.**
- **False confidence: `Bwd Packet Length Std` (SHAP #1, 15% of dst_port's N_acc);
  9/10 SHAP-top-10 below the N_acc < 0.002 threshold**, driven by the packet-length
  redundant family (group N_acc 0.201 vs max single 0.00064).
- **Blind spot: `Fwd IAT Min` (N_f1 rank 1 at 0.099, SHAP rank 36)**; Engelen
  flow-construction columns also under-ranked (group N_f1 0.115).

## Caveats

- Single seed (0), single RF config; multi-seed replication is ORG-B/ORG-C scope.
- TreeSHAP run in `tree_path_dependent` mode (the field's common default); the
  interventional-background variant is a separate cell of the E5 operator study.
- All-features N(f) estimated on a 50k stratified test subset (R=5); dst_port
  headline on the full 210k test set (R=10). 24 of 52 features have |N_acc| <= 1e-4,
  serving as the E6-style null band (typ. std ~5e-5).
- Permutation do() is class-agnostic marginal resampling; it breaks the joint
  distribution by design (that is the intervention), so N(f) is single-feature
  necessity, not sufficiency — hence the group do() probes for redundant families
  (phase.md sec 6).
