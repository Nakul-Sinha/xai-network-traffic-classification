# phase.md - Plan for the specific paper

**Paper:** *Protocol-Valid Faithfulness Evaluation for ML-Based Network Traffic Classifiers*
**Gaps covered:** G4 (protocol-valid faithfulness protocol) validated through G1+G3 (planted and
documented ground truth). Reserve gap for paper 2 or an extension section: G5 (metric
meta-evaluation via diagnosticity). Everything else from analysis/05 is future work, not scope.

**Author:** Nakul Sinha (solo). Software: all free (Python, scapy, PyTorch, scikit-learn, shap,
captum, CICFlowMeter/NFStream). Compute: CPU for tree models and interventions; one cloud GPU
(user-provided) for the 1D-CNN and the optional ET-BERT flagship table.

**Primary venue:** IEEE Transactions on Network and Service Management (TNSM).
**Alternates:** Elsevier Computer Networks; Computers and Security.

---

## 1. The claim (one sentence)

Deletion-style faithfulness evaluation, imported unchanged from vision and NLP, is invalid for
network traffic because it scores explanations on protocol-impossible inputs; we give a
grammar-valid interventional protocol, validate it on classifiers with known ground truth, and show
that standard explainers and the field's current metrics both fail it in measurable ways.

## 2. Contributions (the 4 things reviewers must be able to point at)

- **C1. PacketDO, a protocol-valid intervention operator.** Field-level do(F := resample from
  pooled empirical marginal) on packets: rewrite the field with scapy, recompute dependent fields
  (checksums, lengths, offsets), re-run the model's own preprocessing (byte window or flow-feature
  extraction). Every counterfactual is a valid packet, unlike zero-masking. Operators per
  representation: header-field resampling, payload re-randomization, size/timing jitter within
  protocol bounds.
- **C2. A validation benchmark with known ground truth.** (a) Planted shortcuts at graded strength
  p in {0.5, 0.7, 0.9, 1.0} in controlled traffic (TTL, TCP window, IP ID, options order, padding
  length), with behavioral verification that the model uses them (twin-model test, Bastings-style,
  never done for traffic); (b) documented natural artifacts as real-data ground truth: CIC-IDS2017
  TTL 64/128, ISCX Ethernet-header misalignment (TRUSTEE), CICFlowMeter TCP-appendix flows
  (Engelen corrected-vs-original pair), SII fields (SoK occlusion grid).
- **C3. The audit.** Six explainers (KernelSHAP, TreeSHAP or DeepSHAP, Integrated Gradients,
  DeepLIFT, LIME, occlusion) x two model families (RF/XGBoost on flow features; 1D-CNN on raw
  bytes; optional ET-BERT table) x two datasets (CIC-IDS2017 original+corrected, ISCX VPN-nonVPN).
  Metrics: Spearman rho against interventional necessity N(F), precision@k, false-confidence rate
  (explainer names a field with N ~ 0), blind-spot rate (field with high N unnamed).
- **C4. The operator-sensitivity result.** Recompute standard deletion/AOPC/descriptive-accuracy
  scores under (i) zero-masking (the field's default) and (ii) PacketDO. Show whether explainer
  rankings survive the operator change. If they flip (Samek's appendix and ROAD both predict they
  will), every published NTC explainer comparison that used zero-masking is called into question.
  This is the paper's "so what".

PoC evidence already in hand (poc/FINDINGS.md): IntGrad ranks a zero-necessity field as its number 1
feature at p=0.7 (false-confidence 0.67); DeepSHAP 0.50; occlusion clean. The phenomenon is real and
the full pipeline runs end to end.

## 3. Experiments

| # | Experiment | Output table/figure |
|---|---|---|
| E1 | Operator validity: fraction of protocol-valid counterfactuals under zero-masking vs PacketDO (parse-check + checksum-check) | Table: validity rates; motivates everything |
| E2 | Planted-shortcut recovery, graded p, both model families | Curves: attribution mass on planted field vs p; per-explainer |
| E3 | Behavioral verification of planted reliance (twin-model accuracy) | Sanity table backing E2 |
| E4 | Natural-artifact recovery on CIC-IDS2017 (orig vs corrected) and ISCX | Table: rho, P@k, false-confidence, blind-spot per cell |
| E5 | Operator sensitivity: explainer rankings under zero-mask vs PacketDO deletion curves | The C4 flip table |
| E6 | Null-intervention control (resample known-inert field) reported for every table | Control rows in E2/E4 |
| E7 (optional, GPU) | ET-BERT fine-tune, repeat E4 on one dataset | Flagship deep-model table |
| E8 (reserve, = G5) | Diagnosticity of deletion-AUC / descriptive accuracy / fidelity on planted-truth models | Extension section or paper 2 |

## 4. Datasets and models

- CIC-IDS2017 original + Engelen-corrected (public); ISCX VPN-nonVPN 2016 (public). Both have
  documented artifacts with citations; both are what the audited literature actually uses.
- Synthetic controlled traffic for C2a: scapy-generated, seeded, released with the code.
- Models: RandomForest/XGBoost (CPU), 1D-CNN raw bytes (small GPU), optional ET-BERT (cloud GPU).
- Everything seeded; one `make all` from clean checkout reproduces every number.

## 5. Schedule (14 weeks)

| Weeks | Work |
|---|---|
| 1-2 | PacketDO operator hardening + unit tests per field; E1 validity study |
| 3-4 | Synthetic generator + planted-shortcut training (per-p models); E3 verification |
| 5-6 | Flow-feature pipeline (CICFlowMeter/NFStream); dataset hygiene; natural-artifact reproduction |
| 7-9 | Full audit matrix E2 + E4 + E6; optional E7 on cloud GPU |
| 10 | E5 operator-sensitivity study |
| 11-14 | Writing, internal reproduction pass, submission to TNSM |

## 6. Threats to validity (answered in-paper)

- Resampling shifts the joint distribution: class-agnostic pooled resampling + null-intervention
  controls (E6) reported alongside every result.
- Model never retrained under intervention; per-p models trained before any intervention.
- Byte-vs-field granularity: report both; aggregation rule stated; ISCX header misalignment handled
  via protocol-parsed offsets (it is itself ground-truth case B1).
- KernelSHAP cost: stratified sampling; the measured cost is itself reportable.
- Redundant fields can depress single-field N(F): report field-set necessity for the documented
  redundant families (SeqNo/AckNo/TCP-TS); full Rashomon treatment explicitly deferred (G8).

## 7. What is explicitly out of scope (future work section)

Drift-aware evaluation (G11), plausibility axis and analyst studies (G12, G13), adversarial attacks
on explainers (G14), full redundancy/Rashomon enumeration (G8), attention-as-explanation validation
across the transformer zoo. Each gets one paragraph in future work, citing analysis/05.

## 8. Evidence base

Broad-program documents remain in this repo: analysis/00-10 (corpus, verified claims, prior-work
differentiation incl. the two documented novelty corrections in 08, 17-gap distillation in 05),
poc/ (working demonstration). The broad-program plan this document replaces is preserved at
paper/phase-broad-program.md.
