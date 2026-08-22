# CORRECTED_DATASET.md - Engelen/Liu "improved" CICIDS2017 acquisition + E4 design (Parcel A3a)

## 1. Reachability investigation (2026-08-22)

| source | status | size |
|---|---|---|
| DistriNet WTMC2021 page (Engelen corrected), https://intrusion-detection.distrinet-research.be/WTMC2021/ | **UNREACHABLE** - TLS connection reset (curl exit 35/56, WebFetch ECONNRESET) from this network on 2026-08-22 | n/a |
| DistriNet CNS2022 page (Liu improved), https://intrusion-detection.distrinet-research.be/CNS2022/ | **UNREACHABLE** - same failure | n/a |
| Kaggle `ernie55ernie/improved-cicids2017-and-csecicids2018` (mirror of the CNS2022 improved release) | **REACHABLE, per-file download** | full dataset 10,985,642,855 B (~11 GB, over cap); CICIDS2017_improved portion alone: 5 CSVs, 1,152,270,765 B (~1.15 GB) - **under the 3 GB cap** |
| Kaggle `ernie55ernie/cleaned-cicids2017` (single pre-cleaned CSV of the same improved data) | reachable | 914,702,992 B (291 MB zipped); not used - we do our own hygiene |

**Decision: downloaded.** The five `CICIDS2017_improved/*.csv` files were fetched individually
(`kaggle datasets download -f CICIDS2017_improved/<day>.csv`), unzipped to the scratchpad, archives
deleted. CSE-CIC-IDS2018_improved (10 files, 2.99-4.2 GB *each*) was NOT downloaded and is out of
scope.

Staging location (NOT in repo):
`C:\Users\nakul\AppData\Local\Temp\claude\C--Users-nakul-OneDrive-Desktop-Academics-cn\ee30e724-9e44-4268-a3e6-2eabd7e384d0\scratchpad\cicids2017_improved\{monday,tuesday,wednesday,thursday,friday}.csv`
Loader: `load_cicids_improved.py` (env override `CICIDS_IMPROVED_DATA_DIR`).

## 2. Provenance chain (cite all three in the paper)

1. **Engelen et al., SPW (WTMC) 2021** - "Troubleshooting an Intrusion Detection Dataset: the
   CICIDS2017 Case Study" - documents the CICFlowMeter TCP-appendix bug (25.9% spurious flows),
   releases the first corrected flows. https://doi.org/10.1109/SPW53761.2021.00009 |
   https://intrusion-detection.distrinet-research.be/WTMC2021/ (in Resource.md)
2. **Liu et al., IEEE CNS 2022** - "Error Prevalence in NIDS Datasets: A Case Study on
   CIC-IDS-2017 and CSE-CIC-IDS-2018" - the follow-up **improved** regeneration (fixed
   CICFlowMeter, relabelling, `Attempted Category`, payload-aware labels). Dataset page:
   https://intrusion-detection.distrinet-research.be/CNS2022/
   **NOT yet in Resource.md - must be added and DOI-verified before manuscript** (the data we
   actually use follows this paper's schema, not the WTMC2021 one).
3. **Kaggle mirror** ernie55ernie/improved-cicids2017-and-csecicids2018 (the copy actually
   downloaded; DistriNet host was down). Record the mirror in the artifact-availability statement.

Schema fingerprint confirming this is the CNS2022 improved release: 91 columns including
`Attempted Category`, `Fwd RST Flags`/`Bwd RST Flags`, `ICMP Code`/`ICMP Type`,
`Total TCP Flow Time`, and flow metadata (`id`, `Flow ID`, `Src IP`, `Src Port`, `Dst IP`,
`Timestamp`).

## 3. Measured characterization (real numbers, this copy)

Rows per day: monday 371,624; tuesday 322,078; wednesday 496,641; thursday 362,076;
friday 547,557 -> **2,099,976 total** (hygiene drops 5 NaN/Inf rows -> 2,099,971).

Fine labels: 27 (incl. 11,979 `* - Attempted` rows and the CNS2022 relabelling
`Infiltration - Portscan` = 71,767 rows). Family view (base label, Attempted kept):

| family | flows | | family | flows |
|---|---|---|---|---|
| Normal Traffic | 1,582,566 | | Infiltration | 71,848 |
| DoS (incl. Heartbleed 11) | 177,521 | | Brute Force | 6,972 |
| Port Scanning | 159,066 | | Bots | 4,803 |
| DDoS | 95,144 | | Web Attacks | 2,056 |

Default E4 view from `load_cicids_improved.get_flows()` (drop Attempted, drop Infiltration,
harmonize to the original 52-column space): **2,016,189 flows x 52 features, 7 families**
(Normal 1,582,561 / DoS 171,645 / Port Scanning 159,066 / DDoS 95,144 / Brute Force 6,933 /
Bots 736 / Web Attacks 104).

## 4. Corrected-vs-original measured deltas (the E4 levers)

Original = Parcel A1 Kaggle cleaned release (see DATASET.md); corrected = this improved release.

| quantity | original | corrected (improved) |
|---|---|---|
| flows after hygiene | 2,520,751 | 2,099,971 |
| `Init_Win_bytes_forward == -1` (TCP-appendix signature) | **43.5% of Normal Traffic** (vs <=0.01% of every attack class) | **0 flows, 0.00%** - in every family, TCP-only subset and overall (loader-verified) |
| Destination-port concentration | DoS/DDoS/Web Attacks 100% port 80; Brute Force 21/22; Bots 8080 (64%) | **survives correction**: DoS 100% port 80 (n=167,786), DDoS 100% (n=95,144), Web 100% (n=104), Slowloris 100%, Brute Force 21 (57.3%)/22 (42.7%), Bots 8080 (100%, n=736); Normal top = 53 (60.5%), 443 (24.6%), 80 (10.5%) |
| `min_seg_size_forward` | bimodal 20 (1,296,937) / 32 (1,028,633) | mode is now **8** (999,092), then 20 (551,841), 32 (300,894), 24 (148,029), 40 (86,718) - fixed CICFlowMeter computes it differently (UDP/ICMP get 8) |
| `Fwd Header Length` median (family) | Normal 64, Port Scan 40, DoS 200 | Normal 16, Port Scan 40, DoS 232 |
| labels | 7 grouped families | 27 fine labels + `Attempted Category` |

The two headline facts for the paper:
1. **The Engelen flow-construction artifact is a real, class-correlated feature in the original
   data (43.5% benign vs ~0% attack) and is annihilated by the correction (exactly 0 flows).**
2. **The destination-port shortcut is untouched by the correction** - it is a testbed-design
   artifact, not a flow-metering bug. Correction removes metering artifacts, not design artifacts.

## 5. E4 corrected-vs-original experiment design (Phase 3+ execution)

1. **Harmonize** with `load_cicids_improved.get_flows(harmonize=True)`: identical 52-feature
   space and 7-family labels on both sides (COLUMN_MAP verified against both actual headers;
   metadata columns id/Flow ID/IPs/Src Port/Timestamp never enter X). Two label variants:
   (i) default drop-Attempted, (ii) keep-Attempted robustness check.
2. **Train the identical model pair**: RF and XGBoost, same hyperparameters, same seed set as the
   Phase 2 benchmark, stratified train/test within each dataset. Report both models' accuracy so
   any headline-accuracy delta (Engelen: performance claims survive; Lanvin: they can move) is a
   by-product table.
3. **Interventional ground truth per side**: flow-feature permute operator (the flow-level
   PacketDO analogue): do(F := resample from class-pooled empirical marginal), N(F) = accuracy
   drop / prediction-flip rate; field-set necessity for the correlated family
   {`Init_Win_bytes_forward`, `Init_Win_bytes_backward`, `Fwd Header Length`,
   `min_seg_size_forward`}.
4. **Audit** (TreeSHAP exact, plus KernelSHAP/LIME per ORG-B's explainer set): Spearman rho vs
   N(F), precision@k, false-confidence rate, blind-spot rate - per model x dataset cell.
5. **The paired contrast that only this dataset pair enables**: on the original model the
   appendix-signature features have high N(F) (real shortcut); on the corrected model their N(F)
   should collapse toward 0 (signature no longer exists). An explainer that keeps assigning them
   mass on the corrected model exhibits false confidence with a *natural-data* cause; one that
   missed them on the original model has a blind spot on a documented artifact.
   Destination Port is the positive control that must stay high-N on BOTH sides.
6. **Null-intervention control (E6)**: permute a measured-inert feature on both sides; report in
   every table row.
