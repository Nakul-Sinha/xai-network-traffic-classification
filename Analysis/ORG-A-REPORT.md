# ORG-A REPORT - Real-Data & Natural-Artifacts consolidation (Track B, feeds E4/E6)

**Org:** ORG-A (Real-Data & Natural-Artifacts; CPU/network/disk only, no GPU).
**Date:** 2026-08-22. **Seed policy:** all trained-model numbers below are seed 0, single config
(multi-seed is ORG-B/ORG-C scope). **Status:** parcels A1 (acquisition), A2 (destination-port
ground truth), A3a (corrected dataset), A3b (artifact catalogue) DONE; corrected-vs-original
paired E4 run designed but not yet executed (design in
`Experiments/realdata/CORRECTED_DATASET.md` Sec. 5).

Detailed sources (all real, measured numbers - nothing below is estimated):

- `Experiments/realdata/DATASET.md` - original-copy acquisition + measured artifact columns
- `Experiments/realdata/CORRECTED_DATASET.md` - corrected/improved copy + measured deltas + E4 design
- `Experiments/realdata/NATURAL_ARTIFACTS.md` - the 7-artifact Track-B catalogue (B1-B7)
- `Experiments/realdata/results/a2_port.md` + `a2_port_results.json` - the A2 audit numbers
- Loaders: `Experiments/realdata/load_cicids.py`, `load_cicids_improved.py`

---

## 1. Real data now available

Two CIC-IDS2017 flow-CSV copies are acquired, hygiene-checked, and loadable through a common
harmonized 52-feature / 7-family API. Raw archives were deleted after extraction; CSVs are staged
in the session scratchpad (NOT the repo), locations recorded in the two DATASET files with env-var
overrides (`CICIDS_DATA_DIR`, `CICIDS_IMPROVED_DATA_DIR`).

| copy | source | flows after hygiene | features | on-disk |
|---|---|---|---|---|
| **Original** (uncorrected CICFlowMeter output, publisher pre-cleaned) | Kaggle `ericanacletoribeiro/cicids2017-cleaned-and-preprocessed` | 2,520,751 | 52 numeric, label `Attack Type` (7 classes) | 685 MB |
| **Corrected/improved** (Engelen line: Liu et al. CNS 2022 regeneration, 91 raw columns) | Kaggle mirror `ernie55ernie/improved-cicids2017-and-csecicids2018` (DistriNet host unreachable 2026-08-22) | 2,099,971 raw; **2,016,189 x 52 x 7 families** in the default harmonized E4 view | 91 raw -> 52 harmonized | 1.1 GB |

Key measured deltas that make this the E4 pair (CORRECTED_DATASET.md Sec. 4):

1. **TCP-appendix signature (`Init_Win_bytes_forward == -1`): 43.5% of Normal Traffic on the
   original copy (vs <= 0.01% in every attack class) -> exactly 0 flows on the corrected copy.**
   The Engelen flow-construction artifact is real, class-correlated, and annihilated by the
   correction.
2. **Destination-port concentration survives correction** (DoS/DDoS 100% port 80 on both sides;
   Brute Force 21/22; Bots 8080). It is a testbed-design artifact, not a metering bug - the
   built-in positive control that must stay high-necessity on BOTH sides of the pair.

Class distributions, per-day row counts, fine-label inventory (27 labels incl. `Attempted`),
and the `min_seg_size_forward` / `Fwd Header Length` regime shifts are tabulated in the two
DATASET files.

## 2. Real-data Destination-Port ground-truth result (Parcel A2: N(F) + explainer behavior)

Setup: RF (100 trees, depth <= 20, min_leaf = 20, seed 0) on a stratified 490k/210k train/test
split of the original copy; baseline test accuracy 0.99789, macro-F1 0.91494. Interventional
necessity N(f) = feature-space do(f := resample from pooled empirical marginal) on held-out data
(dst_port: R=10 on full 210k test; all 52 features: R=5 on stratified 50k). TreeSHAP
(`tree_path_dependent`) on 1,000 stratified rows; RF gini as second explainer view.

### The model uses the shortcut (necessity ground truth)

- **N(dst_port) = 0.00434 +/- 0.00012 accuracy drop; 0.04792 +/- 0.00134 macro-F1 drop.
  Rank 1/52 by accuracy-necessity** (rank 2 by F1, behind Fwd IAT Min).
- Recall collapse lands exactly where the port table predicts: **Brute Force -37.8 pp**
  (0.980 -> 0.602), Bots -4.9 pp, DoS -3.1 pp; **~0 for Port Scanning** (port-spread class,
  matching the documented artifact structure).

### Explainer behavior against that ground truth

- **SHAP global rank of dst_port: 5/52** (mean|SHAP| 0.00589); gini rank 13/52. Per-class SHAP is
  qualitatively faithful (rank 1 for Bots and Brute Force, 37 for Port Scanning) - the *global
  aggregation* is what buries the true rank-1 shortcut.
- **rho(SHAP, N_acc) = 0.688** (p = 1.8e-08), rho(SHAP, N_f1) = 0.517; **precision@5 = 0.40,
  precision@10 = 0.60.** Moderately correlated, far from rank-faithful.
- **False confidence:** `Bwd Packet Length Std` is SHAP #1 with N_acc = 0.00064 (15% of
  dst_port's necessity while outranking it). Under the synthetic-track criterion N_acc < 0.002,
  **9 of SHAP's top 10 are false-confidence features** - all from the 14-column packet-length
  redundant family. Mechanism confirmed by group do(): family group N_acc 0.201 / N_f1 0.609 vs
  max single 0.00064 / 0.0196 (collectively load-bearing, individually substitutable ->
  credit-splitting floods the top of the global ranking).
- **Blind spot:** `Fwd IAT Min` - the #1 macro-F1-necessity feature (N_f1 = 0.099, twice
  dst_port's) is SHAP rank 36/52 and gini rank 34/52. Three of the four measured blind-spot
  features (`Fwd Header Length`, `Init_Win_bytes_forward/backward`) are exactly the Engelen
  flow-construction columns: the documented dataset artifact the model exploits is systematically
  under-reported by both explainers (Engelen quartet group N_f1 0.115 vs max single 0.0146).
- **E6 null band:** 24 of 52 features have |N_acc| <= 1e-4 (typ. std ~5e-5) - the built-in
  null-intervention control set for the E4 tables.

**One-line takeaway for the paper:** on real CIC-IDS2017 data the documented destination-port
shortcut is the single most necessary feature, yet global TreeSHAP ranks four interchangeable
packet-length proxies above it and misses the most necessary feature entirely - the E4
false-confidence and blind-spot phenomena occur on natural data, not just planted shortcuts.

## 3. Natural-artifact catalogue status (Track B, 7 artifacts)

Full catalogue with citations and per-artifact intervention recipes: `NATURAL_ARTIFACTS.md`.

| id | artifact | status on acquired data |
|---|---|---|
| B3 | CICFlowMeter TCP-appendix flows (Engelen 25.9%) | **Fully reproducible - flagship.** Signature measured 43.5% benign vs ~0% attack on original; 0 flows on corrected. Paired orig-vs-corrected E4 contrast designed (CORRECTED_DATASET.md Sec. 5), execution pending. |
| B4 | Destination-port bias | **Fully reproducible - DONE (A2).** Numbers in Sec. 2 above; survives correction, so it is the cross-pair positive control. |
| B7 | Heartbleed Bwd-IAT/Bwd-PktLen generation artifact | Partial: fine label only in improved copy, **n = 11 flows** - sidebar cell, not a main E4 row. Original-side isolation would need ungrouped per-day CIC CSVs (not acquired). |
| B5 | SII (MAC/IP/port identifiers in raw bytes) | Partial flow-level rehearsal possible (improved copy exposes Src IP/Dst IP/Src Port metadata, excluded from X by the loader); the real case is byte-level - needs PCAP. |
| B2 | TTL 64/128 (Kali=64 vs Windows=128) | **Not representable in any flow CSV** - verified: neither the 52- nor the 91-column release carries a TTL-derived feature (`ARTIFACT_COLUMNS["ttl"] == []`). Needs PCAP. |
| B1 | ISCX Ethernet-header misalignment (B49/B43/B47) | Needs PCAP (ISCX byte-level parcel). |
| B6 | SeqNo/AckNo/TCP-timestamp flow-ID bytes | Needs PCAP (CICFlowMeter keeps no absolute seq/ack/timestamp features). |

Count: 2 fully reproducible on acquired flow CSVs (B3, B4 - one executed), 2 partial (B7, B5),
4 requiring the PCAP/byte-level parcel (B1, B2, B5-proper, B6).

## 4. Deferred - still needs PCAP / byte-level data (ISCX-USTC parcel, ORG-A next wave)

1. **B2 TTL 64/128** - the headline TRUSTEE artifact; requires CIC-IDS2017 PCAPs + nPrint/byte
   pipeline. PacketDO recipe written (resample TTL over {64,128}+decrements, checksum recompute).
2. **B1 ISCX Ethernet misalignment** - requires ISCX VPN-nonVPN PCAPs; needs protocol-parsed
   offsets (the misalignment is itself why parsing is mandatory - reinforces C1).
3. **B5 SII proper** - byte-level occlusion-grid replication (ET-BERT/YaTC-class models are
   ORG-B GPU scope; ORG-A supplies the data + PacketDO recipes).
4. **B6 SeqNo/AckNo/TS** - byte-level; rebase-preserving-relative-offsets operator specified.
5. **B7 original-side Heartbleed** - would need the ungrouped per-day CIC CSVs (small download,
   optional; improved-copy n=11 cell is possible now but statistically thin).
6. **Corrected-vs-original paired E4 execution** (B3/B4 on both sides, RF+XGBoost, TreeSHAP +
   ORG-B explainer set, E6 rows) - data and design complete, run not yet executed. This is the
   next ORG-A (or ORG-A/ORG-B joint) parcel and needs no new data.

Disk note: both staged copies total ~1.8 GB in scratchpad; scratchpad is session-scoped, so the
acquisition commands in the two DATASET files are the reproducibility record if it is purged.

## 5. Flags for ORG-C (verification org)

1. **Reproduce N(dst_port) = 0.00434 +/- 0.00012 (acc) / 0.04792 (F1) and the Brute-Force
   -37.8 pp recall collapse** from `a2_port_artifact.py` (seed 0, 269 s CPU) - the headline
   real-data number.
2. **Single-seed caveat:** all A2 numbers are seed 0, one RF config. Verify stability across
   seeds and at least one alternative depth/leaf setting before promotion.
3. **50k-subset estimation:** all-features N(f) (hence rho, P@k, blind-spot ranks) used a 50k
   stratified test subset (R=5); dst_port headline used the full 210k (R=10). Check subset-vs-full
   consistency for at least the top-10 necessity features.
4. **Threshold sensitivity:** the "9/10 false confidence" claim depends on the N_acc < 0.002
   threshold carried from the synthetic track; under the stricter dual criterion
   (N_acc AND N_f1) the set is empty (a2_port.md documents both). The paper must state the
   criterion; verify the claim under both.
5. **TreeSHAP mode:** `tree_path_dependent` (field default) - interventional-background TreeSHAP
   is a separate E5 cell, not a correction to these numbers. Confirm mode is reported wherever
   the numbers appear.
6. **Corrected-copy provenance:** we used the Kaggle mirror of the CNS2022 improved release
   because the DistriNet host was TLS-unreachable on 2026-08-22. Verify checksums/schema against
   the DistriNet original when reachable, and confirm the 0-flows `-1` claim independently.
7. **Citation action:** add **Liu et al., IEEE CNS 2022, "Error Prevalence in NIDS Datasets"** to
   `Resource.md` and DOI-verify - the corrected data we actually use follows that paper's schema,
   not the WTMC2021 (Engelen) release named in Resource.md. Cite all three links in the chain
   (Engelen WTMC2021, Liu CNS2022, Kaggle mirror) in the artifact-availability statement.
8. **Label-grouping asymmetry:** the original copy is publisher-grouped into 7 families; the
   harmonized corrected view drops `Attempted` and Infiltration to match. Verify the harmonization
   (COLUMN_MAP, family mapping) does not manufacture or hide artifacts - especially the
   keep-Attempted robustness variant.
