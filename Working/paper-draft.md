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
sufficiency, and a redundancy degree R(M) measured by intervention, not assumed - and audit eight
widely used attribution methods (integrated gradients, gradient saliency, DeepSHAP, occlusion,
KernelSHAP, LIME, TreeSHAP, and impurity) against it, on models with planted shortcuts of graded
strength and on real datasets with documented artifacts. We find that explainers reliably rank a model's true shortcut at
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
- **C1.** PacketDO, a protocol-valid intervention operator (Section 3). We show (E1) that on
  synthetic packets the deletion default produces a protocol-valid counterfactual for only 22.4% of
  intervenable fields (11 of 15 fields are at exactly 0% validity), versus 100% for PacketDO, because
  zeroing a field breaks its checksum.
- **C2.** An interventional ground-truth benchmark: planted shortcuts at graded strength plus
  documented natural artifacts, with necessity/sufficiency/redundancy measured by intervention.
- **C3.** An audit of eight attribution methods against that ground truth (Section 5), quantifying
  false-confidence and blind-spot rates. (The plan's DeepLIFT was replaced by KernelSHAP and LIME;
  the eight are integrated gradients, gradient saliency, DeepSHAP, occlusion, KernelSHAP, LIME,
  TreeSHAP, and random-forest impurity.)
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

*All numbers below are ORG-C-promoted (independently reproduced). Synthetic-benchmark false-confidence
(FC) figures are mean +/- sd over five seeds; real-data figures are reproducible seed-0 single-config
(seed-robustness run pending).*

### 5.1 E1: the deletion operator is protocol-invalid
Over a synthetic population of 2000 IP/TCP+UDP packets (baseline validity 100%), zero-masking -- the
deletion default -- yields a protocol-valid packet for only 22.4% of intervenable fields, while
PacketDO yields one for 100%. The macro figure is an unweighted mean over 15 fields; the per-field
picture is sharper: 11 of 15 fields are at exactly 0% zero-mask validity, and the fields that survive
do so only because the generator left them zero (masking is a no-op). One field, tcp.window, is 35.4%
valid because a window value of 0xFFFF masked to 0x0000 is invisible to the Internet checksum (0x0000
and 0xFFFF both represent zero in one's-complement arithmetic, RFC 1071) -- an arithmetic accident,
not a principled validity. When zero-masking invalidates a packet the violated predicate is always a
checksum, never a parse failure: the bytes still parse, so a model consumes them and returns a
confident prediction on an impossible input. Figure 1.

### 5.2 E3: models rely on the planted artifacts; the null control is clean
The ByteCNN's interventional necessity for the planted tcp.window shortcut rises from 0.273 +/- 0.011
at planting strength p=0.5 to 0.501 +/- 0.020 at p=1.0, while its necessity for the equally-predictive
ip.ttl shortcut stays at or below 0.004: given two perfectly-correlated shortcuts the model commits to
one and ignores the other, so its redundancy degree R(M)=1 even though the data offers two. The
null-intervention control (tcp.sport, never correlated with the label) stays within +/-0.006 of zero
in every cell, calibrating the estimator's noise floor. Figure 3.

### 5.3 E4: explainers find the shortcut but fabricate importance
Every explainer ranks the model's true shortcut at the top (top-k precision under the
number-of-necessary-features convention is 1.0), so the failure is not a missed truth. It is added
falsehood, and it is method- and strength-dependent:
- **Gradient saliency fabricates importance robustly:** CNN Saliency false-confidence is 0.684 +/- 0.037
  at p=1.0 and 0.68-0.74 across all strengths, nonzero in all five seeds.
- **Integrated Gradients and DeepSHAP fabricate importance conditionally:** IG false-confidence at
  p=1.0 is 0.300 +/- 0.274 (nonzero in three of five seeds) -- the appealing seed-0 result of a clean
  endpoint does not generalize; DeepSHAP is clean at p>=0.7 in all seeds but reaches 0.233 +/- 0.325
  at p=0.5 (fails in two of five seeds).
- **Occlusion has zero false-confidence in every seed and strength**, but this is partly by
  construction: occlusion removes a feature by permutation, structurally close to the PacketDO
  ground-truth operator, so its clean record is not independent evidence and is disentangled in E5.
- **Exactness does not confer faithfulness:** RF TreeSHAP false-confidence at p=1.0 is 0.200 +/- 0.274,
  bimodal across seeds ([0.5, 0.5, 0, 0, 0]); it is 0.5 precisely in the seeds where the forest
  commits to one of the two correlated shortcuts and 0 when it spreads reliance. Exact Shapley values
  split credit by the data's correlation structure, so whenever a model commits to one of several
  redundant shortcuts they fabricate confidence in the unused one. Figure 2.

On real CIC-IDS2017 flow data the same phenomena appear on a documented natural artifact. A random
forest (test accuracy 0.99789, macro-F1 0.91494) depends on the destination-port shortcut more than
on any other feature: its interventional necessity is 0.00434 +/- 0.00012 in accuracy (rank 1 of 52)
and 0.04792 +/- 0.00134 in macro-F1, and intervening on it collapses Brute-Force recall by 37.8 points
(0.980 -> 0.602) while leaving the port-spread Port-Scanning class unaffected. Yet global TreeSHAP
ranks destination port only 5th of 52; nine of its top ten features are packet-length statistics whose
individual accuracy-necessity is below 0.002 (false confidence under the accuracy criterion -- these
same features have small but nonzero F1-necessity, so under a joint accuracy-and-F1 criterion the
false-confidence set is empty, and the honest headline is the redundancy mechanism: the packet-length
family has group necessity 0.201 in accuracy / 0.609 in F1 versus at most 0.00064 individually, so
credit-splitting floods the top of the global ranking). The single most F1-necessary feature (Fwd IAT
Min) is TreeSHAP rank 36 of 52 -- a blind spot. The Engelen TCP-appendix flow-construction artifact
is present as expected: the signature Init_Win_bytes_forward = -1 covers 43.5% of benign flows on the
original dataset and exactly 0 on the corrected one.

### 5.4 KernelSHAP, LIME, and cost
Adding the two perturbation-based methods the audit lacked: KernelSHAP has zero false-confidence but
costs 10.8 s per 100 samples; LIME has false-confidence 0.667 at 1.0 s per 100 samples, and the cause
is instructive -- LIME's tabular perturbation standardizes features, and scikit-learn's StandardScaler
assigns unit scale to zero-variance columns, so LIME perturbs constant protocol fields (a fixed
destination port, an address prefix) with unit-variance noise and reads the model's response to those
protocol-impossible inputs as importance. The off-manifold problem this paper identifies reappears
inside LIME's own perturbation kernel.

## 6. E5: faithfulness verdicts depend on the removal operator
For the p=1.0 ByteCNN, we score each explainer with a standard deletion-AOPC curve under two removal
operators. Under zero-masking the four methods order IG (0.4776) > Saliency (0.4729) > DeepSHAP
(0.4724) > Occlusion (0.4629), a spread of 0.0147; under PacketDO they collapse to within 0.0010,
below the per-seed resampling noise (~0.0058). The Kendall tau between the two orderings is 0.333. The
robust and load-bearing effect is not the full four-way reordering (the middle ranks differ by less
than one test-sample count) but a specific demotion: under zero-masking, occlusion -- the method with
zero false-confidence and the best necessity-rank correlation (0.715) -- is ranked last, below
saliency, whose false-confidence is 0.667 and whose necessity correlation is 0.043. The protocol-
invalid operator manufactures an ordering that inverts the audit evidence, and it does so on
non-monotone deletion curves computed on impossible packets. Any comparison of traffic-classifier
explainers that used the zero-masking operator -- the field default -- therefore inherits an ordering
that is an artifact of the operator, not a property of the explanations (contribution C4).

## 7. Discussion and implications
See Working/sections/07-discussion.md for the full discussion. In brief: the failure mode is added
falsehood rather than missed truth; redundancy makes single-vector explanation ill-posed and exact
Shapley values do not escape it; the removal operator is not a detail (E5); and because deployed
systems act on these attributions -- xNIDS generates intrusion-response rules, ShortcutCatcher deletes
features, analyst tools present them as justification -- a false-confidence feature is an operational
error, not a cosmetic one. We do not claim any single method is uniformly safest: occlusion and
DeepSHAP are the most faithful in our study, but occlusion's advantage is partly structural and
DeepSHAP fails at weak signal strength, so the constructive claim is conditional -- faithfulness is
achievable only with a protocol-valid intervention and an explicit accounting of redundancy.

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
