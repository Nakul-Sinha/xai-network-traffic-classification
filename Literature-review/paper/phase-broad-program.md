# phase-broad-program.md - The original broad research program plan (superseded by the scoped phase.md)


**Title (working):** *Do Explanations Explain? An Interventional Ground-Truth Benchmark for
Explainable AI in Network Traffic Classification*

**Author:** Nakul Sinha (solo, no capital, public data, consumer GPU / Colab)

**Primary venue:** IEEE Transactions on Network and Service Management (TNSM).
**Alternates:** Elsevier Computer Networks; Computers & Security; IEEE TIFS if the findings skew
security-critical. All are journals; TNSM is the best scope match (AI/ML for network management,
explainability, benchmark papers welcome).

---

## 1. Thesis and research questions

Two disconnected literatures: "XAI-for-security" papers attach SHAP/LIME to traffic classifiers and
never validate the explanations (64% of our 78-paper deep-read corpus uses NO ground truth); the
"NTC rigour" literature (TRUSTEE CCS'22, S&P'25 SoK, BiasSeeker) diagnoses shortcut learning with
interventions and never mentions XAI (0 occurrences of explainab*/SHAP/attribution across the S&P'25
SoK's 348 occlusion experiments). Networking is the one modality where interventional explanation
ground truth is exact and on-manifold (rewrite field → recompute checksums → valid packet), yet
ground-truth attribution evaluation exists only in vision (BAM 2019, Debugging Tests 2020) and NLP
(Bastings EMNLP'22).

- **RQ1 (validity).** When a traffic classifier is known by intervention to rely on a protocol
  field, do SHAP / IG / DeepLIFT / LIME / occlusion / attention say so? When they name a field, is
  the model causally dependent on it?
- **RQ2 (well-posedness).** How many *disjoint sufficient* field sets does a classifier hold
  (redundancy degree **R(M)**)? If R(M) > 1 is common, attribution presumes a uniqueness the
  modality lacks. New in any modality.
- **RQ3 (metric failure).** Do the proxy metrics in current use (deletion/insertion AOPC, surrogate
  fidelity, monotonicity, max-sensitivity) predict agreement with interventional ground truth?
- **RQ4 (plausibility vs faithfulness).** Reproduce ATT&CK-derived plausibility scoring (Alquliti
  2025) alongside causal faithfulness on the same cells. Prediction: on shortcut-driven models they
  anti-correlate.

Either outcome of RQ1 is publishable: failure → negative result invalidating a large literature;
success → the field's first ground-truth validation. R(M) is novel regardless.

## 2. Ground-truth instrument

Packet-layer `do(F := resample-from-pooled-distribution)`: rewrite protocol field F in every packet
of a flow (scapy), recompute dependent fields (checksums, lengths, offsets), re-run the model's own
preprocessing (byte window or CICFlowMeter/NFStream). Measured quantities, inference-only, model
frozen:
- **N(F)** necessity = accuracy drop under do(F)
- **S(F)** sufficiency = accuracy when all fields except F are resampled
- **R(M)** = number of disjoint minimal sufficient field sets (iterative-pruning extraction - NOT
  the greedy union-growth of the PoC; that is a known PoC bug)
- Null-intervention control (resample a known-inert field) for every table.

## 3. Experimental tracks

- **Track A - constructed ground truth.** Inject artifacts (TTL, IP ID, TCP window, TCP options
  order, TLS cipher order, timing jitter, padding length) at strengths p ∈ {0.5, 0.7, 0.9, 1.0};
  separate model per p. Include the mandatory **Bastings-style binary recovery baseline** so graded
  N(F) is shown to add information over the established protocol.
- **Track B - natural documented artifacts** (ecological validity, cannot be dismissed as toy):
  ISCX Ethernet-header misalignment (TRUSTEE §7.2); CIC-IDS2017 TTL 64/128 and Heartbleed
  Bwd-IAT artifacts; CICFlowMeter TCP-appendix flows (Engelen); SII (MAC/IP/port - SoK: ET-BERT
  0.96→0.51 under D1 occlusion); SeqNo/AckNo/TCP-timestamp flow-ID bytes (Pcap-Encoder:
  ET-BERT 97.4→19.5).
- **Track C - the audit.** Explainers {KernelSHAP, TreeSHAP/DeepSHAP, IG, DeepLIFT, LIME,
  occlusion, attention, TRUSTEE trees} × models {1D-CNN raw bytes, RF/XGBoost flow stats, YaTC or
  ET-BERT} × datasets {ISCX VPN-nonVPN, CIC-IDS2017(+corrected), USTC-TFC2016}. Metrics: Spearman
  ρ(attribution, N), precision@k, **false-confidence rate** (named but N≈0), **blind-spot rate**
  (needed but unnamed).
- **Track D - proxy-metric meta-evaluation** (G5): does a good AOPC/fidelity score predict good ρ?
- **Track E - plausibility vs faithfulness** (G12): FAP/FAR vs ρ on the same cells.
- **Secondary:** drift epochs (agreement decay over time-split data); MAE-pretraining hypothesis
  from the PoC (masking-trained models have higher R(M) → SOTA transformers are the worst case).

## 4. Paper structure

1. Introduction - the two-literatures disconnect; TRUSTEE Table 3 as the opening anecdote
2. Related work - 7 lineages (analysis/03): TRUSTEE, SoK, BiasSeeker, Traffic-Explainer
   (cite as the direct intervention precedent, confirmatory direction), Alquliti, Warnecke,
   Vourganas; plus BAM/Bastings as cross-modal ancestors
3. Ground-truth methodology (Section 2 above) + threats to validity
4. Benchmark description + release
5. Audit results (RQ1, RQ2)
6. Meta-evaluation (RQ3, RQ4)
7. Implications - xNIDS, ShortcutCatcher, EXP-SEC consume unvalidated attributions
8. Limitations & release (code + injected datasets + ground-truth tables; the benchmark is itself
   a contribution others evaluate new explainers against)

## 5. Schedule (16 weeks)

| Weeks | Work |
|---|---|
| 1-3 | do() operator + preprocessing harness + dataset hygiene; unit tests per field |
| 3-6 | Model zoo; Track A injection + verification; N/S/R tables |
| 6-9 | Track B artifacts; full audit matrix (Track C) |
| 9-11 | Tracks D & E; drift + MAE secondary experiments |
| 11-16 | Writing; internal reproduction pass (`make all` from clean checkout); submission |

## 6. Threats to validity (address in-paper)

- Resampling shifts joint distribution → class-agnostic pooled resampling + null-intervention
  controls reported everywhere.
- Never retrain under intervention (freeze M); Track A trains per-p *before* interventions.
- Byte-vs-field granularity → report both; state aggregation rule; handle ISCX header
  misalignment via protocol-parsed offsets.
- KernelSHAP cost → stratified sample; the cost itself is a reportable finding (lit: 0.63 s/packet).
- Retrieval caveats from the deep-read (analysis/05 tail): pull Guidotti 2021, FS-Net full texts
  via institutional access before citing.

## 7. Evidence base (all in this repo)

`analysis/00-10`: orchestrator notes, thesis, 115 verified claims, closest-prior-work, experimental
design, distilled 17-gap analysis, gap candidates with kill-tests, novelty corrections (2 overclaims
caught and documented - read 08 before writing the intro), deep-read final result.
`poc/`: working demonstration - IG assigns its #1 rank to a field with zero causal necessity at
p=0.7; DeepSHAP false-confidence 0.50; occlusion clean. `poc/FINDINGS.md` has the numbers.
