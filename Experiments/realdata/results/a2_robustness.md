# A2 robustness - seeds + alternative RF config (closes ORG-C MUST-FIX #5 / ORG-A flag #2)

**Scripts:** `Experiments/realdata/a2_robustness.py` (runner, resumable) and
`a2_robustness_aggregate.py` (summary + reproduction check). All numbers in
`results/a2_robustness_runs.json` (per-run records + `aggregate` block).
Data: CIC-IDS2017 flow CSV via `load_cicids.py` (DATASET.md). Date: 2026-08-23.

**Question (Parcel D1):** the promoted A2 numbers - N(dst_port) rank 1/52,
TreeSHAP global rank 5/52, Brute-Force recall -37.8 pp, 9/10 acc-only
false-confidence in SHAP's top-10 - were seed-0 single-config. Do the findings
hold across RNG seeds and an alternative RandomForest configuration?

## Setup

Identical pipeline to `a2_port_artifact.py` (same constants: 700k stratified
subsample, 70/30 split, N(dst_port) at R=10 on the full 210k test set, all-52
N(f) at R=5 on a stratified 50k test subset, TreeSHAP `tree_path_dependent` on
1,000 stratified rows, TOP_K=10, FC eps N_acc<0.002 / N_f1<0.005), wrapped as a
per-run function. The run seed drives the **full pipeline** - subsample, split,
RF `random_state`, every permutation RNG, eval/SHAP subsets - with the same
per-stage seed offsets as the original script.

Six runs:

- **default config** (100 trees, `max_depth=20`, `min_samples_leaf=20`):
  seeds **0, 1, 2, 3**
- **alternative config** (100 trees, `max_depth=30`, `min_samples_leaf=5`):
  seeds **0, 1**

**Exact-reproduction check (internal validity):** the `default_seed0` run
reproduces the stored `a2_port_results.json` **exactly** on all eight checked
values (baseline acc 0.9978904761904762, macro-F1 0.9149417354736281, N(dst)
acc drop 0.004343333333333366, F1 drop 0.04791780221286668, SHAP rank 5, N_acc
rank 1, FC acc-only count 9, Brute-Force recall drop 0.3779527559055118) -
float-identical, see `aggregate.seed0_exact_reproduction`.

## Per-run results (parcel-D1 metrics)

| run | base acc | base F1 | N(dst) acc drop (full test, R=10) | N(dst) F1 drop | N_acc rank /52 | N_f1 rank /52 | SHAP rank /52 | gini rank /52 | FC acc-only /10 | FC dual /10 | Brute-Force recall drop |
|---|---|---|---|---|---|---|---|---|---|---|---|
| default_seed0 | 0.99789 | 0.91494 | 0.004343 +/- 0.000124 | 0.04792 | **1** | 2 | **5** | 13 | **9** | 0 | **-0.3780** |
| default_seed1 | 0.99772 | 0.90984 | 0.003478 +/- 0.000059 | 0.05739 | **1** | 2 | **7** | 15 | **8** | 1 | **-0.4409** |
| default_seed2 | 0.99770 | 0.91309 | 0.002971 +/- 0.000102 | 0.04725 | **1** | 2 | **8** | 14 | **9** | 0 | **-0.3819** |
| default_seed3 | 0.99770 | 0.92077 | 0.002479 +/- 0.000053 | 0.03064 | **1** | 2 | **9** | 21 | **9** | 1 | **-0.1995** |
| alt_d30l5_seed0 | 0.99852 | 0.94883 | 0.006344 +/- 0.000091 | 0.07017 | **1** | 2 | **5** | 13 | **9** | 0 | **-0.3596** |
| alt_d30l5_seed1 | 0.99840 | 0.93820 | 0.004702 +/- 0.000078 | 0.05737 | **1** | 2 | **6** | 14 | **9** | 1 | **-0.3556** |

**Mean +/- sd over the 6 runs** (sd with ddof=1):

| quantity | mean +/- sd | per-run values |
|---|---|---|
| baseline accuracy | 0.99799 +/- 0.00037 | |
| baseline macro-F1 | 0.92428 +/- 0.01568 | |
| N(dst_port) acc drop | **0.00405 +/- 0.00140** | 0.00434, 0.00348, 0.00297, 0.00248, 0.00634, 0.00470 |
| N(dst_port) F1 drop | 0.05179 +/- 0.01329 | |
| N_acc rank of dst_port | **1 in 6/6 runs** | [1, 1, 1, 1, 1, 1] |
| N_f1 rank of dst_port | 2 in 6/6 runs | [2, 2, 2, 2, 2, 2] |
| TreeSHAP global rank | **6.67 +/- 1.63** | [5, 7, 8, 9, 5, 6] |
| gini rank | 15.0 +/- 3.0 | [13, 15, 14, 21, 13, 14] |
| FC acc-only count (of 10) | **8.83 +/- 0.41** | [9, 8, 9, 9, 9, 9] |
| FC dual count (of 10) | 0.5 +/- 0.55 | [0, 1, 0, 1, 0, 1] |
| Brute-Force recall drop | **0.3526 +/- 0.0810** | 0.378, 0.441, 0.382, 0.200, 0.360, 0.356 |
| rho(SHAP, N_acc) | 0.653 +/- 0.104 | 0.688, 0.455, 0.680, 0.669, 0.767, 0.656 |
| precision@10 (N_acc) | 0.53 +/- 0.08 | 0.6, 0.6, 0.5, 0.6, 0.4, 0.5 |

## Do the headline findings hold?

1. **Rank-1 necessity: HOLDS, 6/6 runs.** Destination Port is the N_acc rank-1
   feature of all 52 in every seed and both configs (eval-subset N_acc
   0.00236-0.00601, always ahead of #2). N_f1 rank is 2/52 in every run. The
   *magnitude* varies ~2.6x across runs (full-test acc drop 0.00248-0.00634;
   the promoted 0.00434 +/- 0.00012 is the seed-0 value, its +/- being
   permutation-repeat noise, not seed variance - cite the cross-run
   0.00405 +/- 0.00140 for robustness).
2. **SHAP-buries-it: HOLDS, 6/6 runs, and seed 0 is the most favorable case
   for SHAP.** TreeSHAP global rank of dst_port is 5-9 (never better than 5;
   mean 6.67 +/- 1.63). Gini buries it further (13-21). `Bwd Packet Length
   Std` is SHAP #1 in all six runs, and the packet-length family fills 7-8 of
   the top-10 slots in every run - the credit-splitting mechanism is
   config-independent.
3. **Acc-only false-confidence: HOLDS, >= 8/10 in every run** (9/10 in five
   runs, 8/10 in default_seed1; mean 8.83 +/- 0.41). Machine-readable
   `audit.false_confidence_acc_only` (criterion N_acc < 0.002, list + count)
   is now emitted per run and was added to the seed-0 `a2_port_results.json`
   (ORG-C fix #4). The 8/10 run is itself informative: at seed 1 the RF makes
   `Bwd Packet Length Std` genuinely necessary (N_acc 0.00268, necessity rank
   2), so that feature exits the FC set - which member of the redundant family
   the forest commits to is seed-dependent, exactly the synthetic-benchmark
   TreeSHAP model-commitment phenomenon.
4. **Brute-Force recall collapse: HOLDS qualitatively in 6/6 runs** -
   Brute Force is the largest per-class recall drop under do(dst_port) in
   every run - but the magnitude varies: **-35.3 +/- 8.1 pp, range -20.0 to
   -44.1 pp**. The promoted "-37.8 pp (0.980 -> 0.602)" is the seed-0 value
   and should be cited as such (or replaced by the cross-run mean).
5. **Dual-criterion FC set "empty": seed-0-specific, weaken to "<= 1".** Under
   N_acc < 0.002 AND N_f1 < 0.005 the set is empty in 3/6 runs and contains
   exactly one packet-length feature (`Bwd Packet Length Max` twice,
   `Bwd Packet Length Mean` once) in the other 3. The paper's current wording
   ("under a joint criterion the false-confidence set is empty") should say
   "empty or a single feature (0-1 of 10 across 6 runs)"; the redundancy-
   mechanism framing is unaffected.

**Verdict (machine-readable in `aggregate.verdicts`):** `N_rank1_every_run:
true`, `shap_buries_rank_ge4_every_run: true`, `fc_acc_only_ge8_every_run:
true`, `bruteforce_gt25pp_every_run: false` (seed 3 at -19.95 pp).

## Citation guidance for ORG-D

- Safe as robust claims (6/6 runs, 4 seeds x 2 configs): *dst_port is the
  rank-1 accuracy-necessity feature of 52; global TreeSHAP ranks it 5th-9th;
  at least 8 of SHAP's 10 top-ranked features have N_acc < 0.002; the
  intervention's recall damage concentrates on Brute Force in every run.*
- Keep as seed-0 point values with a robustness reference: 0.00434 acc drop,
  SHAP rank exactly 5, -37.8 pp, exactly 9/10 (this file + `aggregate` block
  are the reference; cross-run: 0.00405 +/- 0.00140, rank 6.67 +/- 1.63,
  -35.3 +/- 8.1 pp, 8.83 +/- 0.41).
- Amend the dual-criterion sentence per point 5 above.
- Not covered by this harness (still seed-0-only): the `Fwd IAT Min` SHAP rank
  36/52 blind-spot value and the group-do() numbers (packet-length family
  0.201/0.609, Engelen quartet 0.115); `Fwd IAT Min` does appear in the
  necessity top-3 by acc in all 6 runs, consistent with the blind-spot
  direction, but per-run full SHAP rankings below the top-10 were not stored.

## Caveats

- 6 runs (4 seeds default, 2 seeds alt config); sd over 6 runs has wide CI.
- The alternative config (depth 30 / min_leaf 5) *strengthens* the findings
  (largest N(dst_port) drops, SHAP rank 5-6, FC 9/10) while raising baseline
  macro-F1 to 0.938-0.949, so the artifact reliance is not an under-fitting
  artifact of the default config.
- Runtime ~200-220 s per run, CPU; total 1,259 s for all six.
