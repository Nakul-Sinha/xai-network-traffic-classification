# Protocol-Valid Faithfulness Evaluation for ML-Based Network Traffic Classifiers

*Draft manuscript. Stable sections (Intro, Related Work, Method, E1) are written; results sections
carry [VERIFIED-RESULT] placeholders filled from adversarially-verified organization outputs.
Target: IEEE TNSM.*

---

## Abstract

Deep learning has become the default tool for network traffic classification and intrusion
detection, and with it a large literature that attaches post-hoc explanation methods (SHAP, LIME,
saliency) to these models to make them trustworthy. That literature almost never checks whether the
explanations are *correct*: in a survey of 107 works, only five define any explanation-quality
metric, and none has a dataset with ground-truth feature importance. We show that the standard way
faithfulness *is* measured elsewhere - deletion/occlusion of "important" features - is not merely
unvalidated for network traffic but formally invalid: setting a feature to zero produces a packet
that violates protocol grammar (a broken checksum, an impossible length) and could never appear on a
network, so the model is queried off-manifold. We introduce **PacketDO**, a protocol-valid
intervention operator that resamples a protocol field from its pooled empirical marginal and
recomputes every dependent field, yielding a counterfactual that is always a well-formed packet.
Using PacketDO we build the first interventional ground truth for traffic classifiers - necessity,
sufficiency, and a redundancy degree R(M) measured by intervention, not assumed - and audit six
widely used explainers against it, on models with planted shortcuts of graded strength and on real
datasets with documented artifacts. We find that explainers reliably rank a model's true shortcut at
the top yet simultaneously attribute high importance to redundant features the model provably does
not use; that even exact Shapley values (TreeSHAP) exhibit this false confidence when a model commits
to one of several equivalent shortcuts; and that an explainer's faithfulness ranking can flip
depending on whether features are removed by zero-masking or by PacketDO. We release the operator,
the benchmark, and the ground-truth tables.

## 1. Introduction

[Two-literatures framing. Literature A (XAI-for-security): hundreds of papers,
RF/CNN + SHAP/LIME on CICIDS2017/NSL-KDD, explanations displayed, never validated. Literature B
(NTC rigour: TRUSTEE CCS'22, S&P'25 SoK, BiasSeeker): traffic classifiers routinely learn capture
artifacts, diagnosed with interventions, never called "explanations". The two never cite each other:
the S&P'25 SoK runs 348 occlusion experiments and contains zero occurrences of
explainab*/SHAP/attribution.]

[Opening anecdote: TRUSTEE Table 3 - a perfect-fidelity (F1=1.00) surrogate named 3 bytes; tampering
those exact bytes left accuracy at 0.959->0.959 because the model held substitutable shortcuts. A
perfect explanation was causally wrong. Nobody has systematised this.]

[The opportunity: networking is the one modality where interventional explanation ground truth is
exact and on-manifold, because packets are rewritable and protocol semantics are known. Ground-truth
attribution evaluation exists in vision (BAM 2019) and NLP (Bastings 2022) but never for traffic.]

**Contributions.**
- **C1.** PacketDO, a protocol-valid intervention operator (Section 3). We show (E1) that the
  deletion default is invalid for [VERIFIED-RESULT: ~78% of intervenable fields on synthetic
  packets; zero-mask 22% vs PacketDO 100% protocol-valid], because zeroing a field breaks checksums.
- **C2.** An interventional ground-truth benchmark: planted shortcuts at graded strength plus
  documented natural artifacts, with necessity/sufficiency/redundancy measured by intervention.
- **C3.** An audit of six explainers against that ground truth (Section 5), quantifying
  false-confidence and blind-spot rates.
- **C4.** The operator-sensitivity result (Section 6): an explainer's faithfulness verdict depends
  on the removal operator, so prior zero-mask-based comparisons are called into question.

## 2. Related work

[Seven lineages, from Literature-review/analysis/03-closest-prior-work.md, differentiated:]
- **Ground-truth XAI evaluation in other modalities.** BAM/BIM (Yang & Kim 2019, paste objects);
  Bastings et al. (EMNLP 2022, inject lexical shortcuts); Debugging Tests (Adebayo 2020). Our Track A
  is Bastings' protocol ported to packets and extended from binary recovery to graded necessity.
- **Interventions on traffic.** Traffic-Explainer (2025) does checksum-valid byte-swapping but only
  *confirmatorily* - it swaps bytes its own explainer chose, so it cannot see blind spots or
  redundant alternatives; we invert the direction and audit all explainers against an independent
  reference. TRUSTEE (CCS'22) performs one tampering intervention as a validation footnote; the
  S&P'25 SoK runs occlusion but never asks an explainer anything.
- **Removal-operator critiques.** ROAR (Hooker 2019), ROAD (Rong 2022, zero-masking provably worst;
  imputation image-specific), Samek (2017, operator dependence). None adapted to packets; the
  protocol-valid removal operator is the gap.
- **Shortcut detection.** BiasSeeker (2026), ShortcutCatcher (2026) - dataset/model-side shortcut
  hunting that *uses* explainers as trusted heuristics; we validate the heuristic.
- **Plausibility metrics.** Alquliti et al. (2025) score SHAP against ATT&CK-derived expert feature
  sets - plausibility, not faithfulness; we measure the causal axis they cannot.
- **Security-XAI evaluation frameworks.** Warnecke et al. (2020) six criteria, deletion-based
  descriptive accuracy as an admitted proxy for absent ground truth.
- **Explainer-stability.** Vourganas & Michala (2026) prove multicollinearity inflates attribution
  variance - explainer instability, distinct from the well-posedness question our R(M) addresses.

## 3. Method: PacketDO and interventional ground truth

### 3.1 The operator

[do(F := resample from pooled class-agnostic marginal), recompute dependent fields (IP/TCP/UDP
checksums, IP total length, TCP data offset) via scapy round-trip. Every counterfactual is a valid
packet. Contrast with zero-mask (overwrite field bytes with 0x00, recompute nothing). Structural
fields (checksums, lengths, ip.proto) are recomputed, not resampled - ip.proto is not a free degree
of freedom because it is fixed by the L4 header.]

### 3.2 Ground-truth quantities

- Necessity N(F) = Acc(clean) - Acc(do(F:=resample)).
- Sufficiency S(F) = Acc(do(all fields except F := resample)).
- Redundancy R(M) = number of disjoint minimal sufficient field sets. R>1 means the model holds
  substitutable shortcuts and no unique explanation target exists.
- Null-intervention control: a field never correlated with the label must give N ~ 0.

## 4. Experimental setup

[Datasets: synthetic planted-shortcut traffic (graded p in {0.5,0.7,0.9,1.0}); CIC-IDS2017 flow
features with documented artifacts; [VERIFIED-RESULT: real-data specifics from ORG-A].
Models: ByteCNN (raw bytes), RandomForest (flow features), [optional ET-BERT].
Explainers: Integrated Gradients, Saliency, DeepSHAP, Occlusion, KernelSHAP, LIME, TreeSHAP,
impurity. Metrics: Spearman rho(attribution, N), precision@k, false-confidence rate, blind-spot rate.
All seeded; multi-seed mean+/-sd.]

## 5. Results

### 5.1 E1: the deletion operator is protocol-invalid
[VERIFIED-RESULT: zero-mask macro validity 22% (per-field 0% for information-carrying fields, 100%
only where masking is a no-op), PacketDO 100%; the RFC 1071 tcp.window subtlety; Figure 1.]

### 5.2 E3: models rely on the planted artifacts; the null control is clean
[VERIFIED-RESULT: N(win) rises 0.27->0.48 with p, N(ttl)~0 (model commits to one of two redundant
shortcuts), N(null)~0; R(M)=1; Figure 3.]

### 5.3 E4: explainers find the shortcut but fabricate importance
[VERIFIED-RESULT: precision@k=1.0 everywhere; Saliency FC 0.67-0.80, IntegratedGradients FC up to
0.75 at weak planting, DeepSHAP/Occlusion FC 0.0, TreeSHAP FC 0.50 at p=1.0; multi-seed mean+/-sd
from ORG-B; Figure 2. Real-data Destination-Port result from ORG-A.]

### 5.4 KernelSHAP / LIME and runtime
[VERIFIED-RESULT: FC + wall-clock per 100 samples, from ORG-B.]

## 6. E5: faithfulness verdicts depend on the removal operator
[VERIFIED-RESULT: deletion-AUC ranking of explainers under zero-mask vs PacketDO; which pairs flip;
from ORG-B. This is C4 - prior zero-mask comparisons are unsafe.]

## 7. Discussion and implications
[Downstream consumers of unvalidated attributions: xNIDS emits defence rules, ShortcutCatcher deletes
features, EXP-SEC pipes to analysts. False confidence changes a firewall rule, not just a figure.
Redundancy makes single-explanation evaluation ill-posed. Intervention-aligned methods (occlusion,
DeepSHAP) are safest; the operator must be protocol-valid.]

## 8. Threats to validity
[Resampling shifts joint distribution -> class-agnostic pooled resampling + null controls. Model
never retrained under intervention. Byte-vs-field granularity reported both ways. KernelSHAP cost.
Redundant fields depress single-field N -> field-set necessity reported. Synthetic vs real: E1/E4
replicated on real data (ORG-A). scapy-serializer circularity -> RFC 1071 cross-check + tshark.]

## 9. Limitations and future work
[Out of scope, cited to analysis/05: drift-aware evaluation (G11), plausibility axis + analyst
studies (G12/G13), adversarial attacks on explainers (G14), full Rashomon enumeration (G8),
attention-as-explanation across the transformer zoo. Metric meta-evaluation (G5) is the natural
sequel.]

## 10. Reproducibility
[Public code + benchmark + ground-truth tables; one `make all` on public data reproduces every
number; no capital, single consumer GPU.]
