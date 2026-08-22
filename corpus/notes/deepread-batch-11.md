# Deep-Read Notes - Batch 11
Reader: subagent, 2026-08-22. Focus fields: how explanation quality is EVALUATED; LIMITATIONS / FUTURE WORK.
Full extracted texts: `tmp-attr-correct.txt`, `tmp-tfe-gnn.txt`, `tmp-flowpic.txt`, `tmp-pert.txt`, `tmp-road.txt` (+ `tmp-kalakoti-icissp.txt` as secondary context) in this directory.

---

## 1. Do Feature Attribution Methods Correctly Attribute Features? (Zhou, Booth, Ribeiro, Shah - AAAI 2022, arXiv:2104.14403)
**Read depth:** full_text (main body; appendix skimmed).

**What it is.** Methodology paper (not NTC). Proposes a *dataset modification procedure to induce ground truth* for feature attribution: (a) **label reassignment** - labels kept w.p. r, flipped otherwise, so no original feature can yield accuracy above p* = max(r, 1−r); (b) **input manipulation** - a local artifact (watermark, blur, hue, noise, brightness; article-word substitution in text) applied as a function of the reassigned label, confined to a known "effective region" (ER). Any model with accuracy > p* is *guaranteed* to rely on features inside the **joint effective region** φ∪ (union over all classes' manipulations - crucial, because a model may legitimately use the *absence* of a manipulation).

**XAI evaluation (exact metrics).**
- Continuous attributions: **"attribution percentage Attr%(F) = (Σ_{i∈F} |s_i|) / (Σ_{i=1..D} |s_i|)"** on the joint ER; expectation Attr%(φ∪) ≈ 1 for near-perfect models trained at r = 0.5.
- Top-k / rationales: **precision Pr(F) = |F∩F_C|/|F| and recall Re(F) = |F∩F_C|/|F_C|**.
- For r > 0.5, attribution is only *bounded* via normalized Shapley values on accuracy: v(F_M) ≥ 1.5 − r for p ≈ 1; checks whether saliency maps fall in the Shapley-consistent range.

**Ground truth:** SYNTHETIC (semi-natural dataset construction; guarantee comes from an accuracy argument, with binomial tail bound for finite test sets). Explicitly contrasts itself against proxy metrics (Samek deletion curves fail on OR-interactions; ROAR retraining fails under underspecification) and against plausibility/human-agreement evaluation ("positive results from alignment evaluation only support plausibility, not faithfulness").

**Setup.** ResNet-34 from scratch on a custom 8-class bird dataset (1,200 Flickr images/class; confusing pairs mined from CUB-200-2011); Bi-LSTM+attention and rationale models (RL: Lei et al.; CR: Bastings et al.) on modified BeerAdvocate (12k reviews).

**Key numbers.** 70% of 100 runs reach >95% test accuracy; **none of Gradient/SmoothGrad/GradCAM/LIME/SHAP consistently gets Attr% ≈ 1**; SHAP best ("%Attr = 69% at %ER = 40% on average"), strongly manipulation-type dependent; watermark *presence* detected far better than *absence*. Attention: articles receive 8.6% attribution vs 7.9% frequency baseline ("better than random, albeit barely") despite >97% accuracy. Rationale models: near-optimal precision/recall on obvious manipulations; but RL rationales select misleading non-correlating articles.

**Stated limitations / future work (near-verbatim).** "Current evaluations fall short-primarily due to a lack of clearly defined ground truth." "The mostly negative conclusions cast doubt on this use case of interpretability methods [spurious-correlation detection]." Future: "move beyond 'artifact' features … [with] image inpainting and masked language prediction, more realistic features could be generated, perhaps also conditioned on or guided by semantic concepts." Recommendations: developers "should first train models that are guaranteed to use certain known features, and 'dry run' the planned interpretability methods on them"; future proxy metrics should "be first calibrated with ground truth in a controlled setting."

**My gap observations.**
- The procedure is claimed domain-general but instantiated only on images/text; **no one (including later NTC literature) has built the traffic analogue** - e.g., injecting a byte watermark or forced packet-size signature into flows with label reassignment. This is the most directly transplantable ground-truth recipe for NTC XAI.
- The hard guarantee only bites at r = 0.5 (all natural signal destroyed); for realistic r > 0.5 the "correct" attribution is a *range*, not a point - the paper under-emphasizes how weak the test becomes there.
- The guarantee is about *feature sets*, not attribution magnitudes; localized artifacts (watermark) are the favorable case - spatially distributed manipulations (blur/hue) map poorly to traffic features that are inherently non-local (statistics over a flow).
- Evaluation is of methods-on-modified-data; transfer of conclusions to natural-data behavior of the same methods is assumed, not shown.

---

## 2. TFE-GNN: A Temporal Fusion Encoder Using Graph Neural Networks for Fine-grained Encrypted Traffic Classification (Zhang et al. - WWW 2023, arXiv:2307.16713)
**Read depth:** full_text.

**What it is.** Pure classification paper, **zero XAI content**. Byte-level traffic graphs: each distinct byte value (≤256 nodes) is a node; undirected edge iff PMI(i,j) > 0 within a window (default 5). Header and payload get separate graphs, separate embeddings ("dual embedding"), each encoded by 4-layer GraphSAGE + PReLU + BatchNorm with JKN-style concat and mean pooling; header/payload vectors fused via **cross-gated feature fusion** (sigmoid gates crosswise filter the other part); per-packet vectors fed to 2-layer Bi-LSTM + classifier. Preprocessing removes Ethernet header, IPs, ports; max 50 packets, 150 payload / 40 header bytes per packet.

**XAI evaluation:** none. Explanations never produced; only classification metrics (AC/PR/RC/macro-F1) and component ablations.

**Ground truth (attribution):** none.

**Datasets.** ISCX VPN-nonVPN (6 behaviours), ISCX Tor-nonTor (8; flows split into 60-s blocks citing FlowPic), self-collected WWT (WeChat 9, WhatsApp 12, Telegram 6 user-behaviour classes). 9:1 stratified split; 10 runs averaged.

**Key numbers.** F1: ISCX-VPN 0.9536, ISCX-nonVPN 0.9240, ISCX-Tor 0.9855 (+4.58% over ET-BERT 0.9397), ISCX-nonTor 0.8507, Telegram 0.9649 (+10.82%). Ablation: header-only ≫ payload-only on Tor (F1 0.9806 vs 0.7700 - a 21.06% gap); w/o activation+BN collapses (F1 0.0548 on Tor). FLOPs 2.2e3 M vs ET-BERT 1.1e4 M ("approximately five times" fewer).

**Stated limitations (near-verbatim, Sec. 6).** "(1) **Limited graph construction approach.** The graph topology of the proposed model is determined before the training procedure, which may result in non-optimal performance. Moreover, the TFE-GNN can not cope with the byte-level noise implied in the raw bytes of each packet. (2) **Unused temporal information implied in byte sequences.** The byte-level traffic graphs are constructed without introducing the explicit temporal characteristics of byte sequences."

**My gap observations.**
- The architecture contains attention-like machinery the authors themselves describe in interpretive terms (PReLU "plays a role similar to that of the attention mechanism"; gates "filter out unimportant information") yet **nothing is ever inspected or visualized** - interpretability language used as design rhetoric only.
- The representation is *structurally hostile to attribution*: "all the bytes with the identical value share the same nodes," so per-position/per-packet byte attribution is impossible by construction; any future GNN explainer (GNNExplainer etc.) could only say "byte value 0x16 mattered," which is nearly meaningless for analysts.
- The header/payload ablation is a *global explanation-by-ablation* (headers dominate, dataset-dependent) that begs a shortcut question the paper never asks: with headers dominating on Tor, is the model reading protocol metadata rather than behaviour? No leakage analysis despite removing IPs/ports "to eliminate interference with sensitive information."
- 60-s block splitting of scarce Tor flows (train/test partitioned "sequentially" after stratified sampling) risks same-flow correlation between train and test; not discussed.

---

## 3. FlowPic: A Generic Representation for Encrypted Traffic Classification and Applications Identification (Shapira & Shavitt - IEEE TNSM 18(2):1218-1232, 2021)
**Read depth:** full_text (author mirror, eng.tau.ac.il).

**What it is.** Classification paper, **no XAI**. FlowPic = 1500×1500 2D histogram of {packet size (1-1500 B)} × {normalized arrival time (60-s window → 1500 bins)} per *unidirectional* flow; single LeNet-5-style CNN (CONV1 10@10×10 s5, maxpool, CONV2 20@10×10 s5, maxpool, FC-64, softmax; ~309k params) reused unchanged for every task. Data augmentation: 60-s blocks with 45-s overlap (split into train/test *before* augmenting).

**XAI evaluation:** none. The closest thing is qualitative human reading of FlowPic images (Sec. IV-B "FlowPics Exploration": VoIP = many high-frequency small packets; Tor = discrete packet sizes from block cipher; chat vs browsing hard "even by a human eye") used as motivation, and confusion-matrix error analysis. No saliency/CAM, no verification that the CNN uses the human-visible patterns.

**Ground truth (attribution):** none.

**Datasets.** ISCX VPN-nonVPN + ISCX Tor-nonTor + own TAU captures (added chats: WhatsApp web, Facebook, Hangouts); 5 categories × {non-VPN, VPN, Tor}; manual cleaning of mislabeled sessions ("we keep only the flows that belong to the correct category by manually removing sessions"). Dataset released.

**Key numbers.** Balanced accuracy: non-VPN categorization 85.0, VPN 98.4, Tor 67.8, merged 83.0; class-vs-all averages 97.0 (non-VPN) / 99.7 (VPN) / 85.7 (Tor); encryption-technique classification 88.4 (Tor recall 97.7, precision 100); application ID 99.7 (10 apps non-VPN), 100.0 (5 apps VPN), 44.3 (Tor apps - fails); unknown-application generalization: video-vs-all excluding Vimeo+YouTube from training → 83.1; excluding Facebook → 99.9; VoIP excluding Facebook → 96.3. Imbalanced 5-fold comparison: FlowPic beats DT/kNN/SVM/NB/MLP on 3 of 4 tasks (e.g., Tor Acc 0.8694 vs DT 0.7755). Cross-encryption transfer is poor (e.g., VoIP trained non-VPN → tested Tor: 48.2).

**Stated limitations / future work (near-verbatim, Sec. VIII).** "We made no effort to optimize the CNN architecture… Examining other known architectures may improve results." Input reduction: "the input size to the system can be reduced to a coarser matrix of 300x300… we can also reduce the number of bits per pixel by using binning… at the extreme… binary images." "While our 15 seconds classification time is certainly not problematic in most cases, it may still be a limiting factor for some applications. Thus, an interesting research direction would be to look for methods that would produce a faster classification."

**My gap observations.**
- The FlowPic idea is *sold* on interpretability ("an intuitive picture") and the paper even articulates human-legible class signatures - the perfect setup for a saliency ground-truth check - but **no attribution method is ever run**; the human-stated signatures are never validated as what the CNN uses. Later XAI-for-NTC papers adopt FlowPic + Grad-CAM, inheriting a representation whose "expected" salient regions were only ever informal prose here.
- Manual label cleaning by the authors means class labels partially embed author judgment; combined with per-category merging of all applications into one histogram set, artifacts of specific capture sessions can act as shortcuts (their own cross-encryption transfer collapse, e.g. 35.8% VoIP VPN→Tor, hints the model keys on encryption-specific texture, not category semantics).
- Aggressive 45-s overlap augmentation (37 blocks from a 10-min call) creates highly correlated training samples; the session-level split mitigates train/test leakage but effective sample size is much smaller than block counts suggest.

---

## 4. Improving IoT Security With Explainable AI: Quantitative Evaluation of Explainability for IoT Botnet Detection (Kalakoti, Bahşi, Nõmm - IEEE IoT Journal 11(10):18237-18254, 2024)
**Read depth:** abstract_only. Closed access (OpenAlex: `oa_status: closed`, no repository full text; no arXiv preprint; ResearchGate "Request PDF"; TalTech portal lists only metadata; IEEE page blocks fetch). Record built from the full official abstract (Semantic Scholar), venue metadata, and secondary descriptions in citing/companion papers by the same group.

**What it is (per abstract).** "Our aim is to improve the transparency and interpretability of high-performance ML models for IoT botnet detection by selecting higher quality explanations using XAI techniques. We used three data sets to induce binary and multiclass classification models…, with sequential backward selection (SBS) employed as the feature selection technique. We then use two post hoc XAI techniques such as LIME and SHAP…"

**XAI evaluation (exact, quoted from abstract).** "To evaluate the quality of explanations generated by XAI methods, we employed **faithfulness, monotonicity, complexity, and sensitivity metrics**." Result: "explanations generated by applying LIME and SHAP to the extreme gradient boosting model yield high faithfulness, high consistency, low complexity, and low sensitivity. Furthermore, **SHAP outperforms LIME** by achieving better results in these metrics." Secondary sources (2026 Frontiers survey-style article) report datasets **N-BaIoT, MedBIoT, BoT-IoT**, F1 > 99% for XGBoost, and SHAP faithfulness ≈ 0.907 - plausible but unverified against the paywalled text.

**Ground truth:** none - all four metrics are functional/proxy metrics computed against the model itself (faithfulness correlation, monotonicity under feature addition, attribution entropy, perturbation sensitivity). No human-expert or constructed ground truth appears in the abstract. (Contrast: the same group's later ICISSP 2025 NIDS-alert paper adds a SOC-analyst "ground truth mask" with Relevance Mass/Rank Accuracy - i.e., their human_expert ground truth postdates this JIOT paper.)

**Key numbers (from abstract only).** "ML models employed in this work achieve very high detection rates with a limited number of features."

**Stated limitations:** not retrievable (full text paywalled; abstract contains none).

**My gap observations.**
- This is one of the very few NTC/IoT-security papers whose *headline contribution* is quantitative XAI evaluation - and it is built entirely on the proxy-metric family that the two methodology papers in this batch (Zhou AAAI'22; ROAD ICML'22) show to be uncalibrated or confounded. Nobody closes that loop for traffic data.
- Metric suite (faithfulness/monotonicity/complexity/sensitivity) is imported unchanged from image/tabular XAI literature; no traffic-specific validity argument (e.g., whether feature perturbations used by faithfulness correspond to *realizable* traffic).
- Closed access with no preprint is itself a reproducibility gap for a paper about transparency.

---

## 5. PERT: Payload Encoding Representation from Transformer for Encrypted Traffic Classification (He, Yang, Chen - ITU Kaleidoscope 2020; read via ZTE Communications 19(4):90-97, 2021)
**Read depth:** full_text (ZTE Communications version; same paper presented at Kaleidoscope 2020 per the copyright note).

**What it is.** Classification paper, **no XAI**. First BERT-style pre-training for traffic: payload bytes tokenized as **bigrams** (vocab 0-65535), ALBERT encoder (768 hidden, 12 layers, 12 heads, input length 128) pre-trained with masked LM on unlabeled self-captured traffic; downstream flow classification takes the first M packets (5 by default), encodes each packet, concatenates the 'cls' embeddings, softmax on top; fine-tuning end-to-end. Predecessor of ET-BERT.

**XAI evaluation:** none. Self-attention is purely architectural; no attention visualization, no attribution, no error analysis beyond aggregate metrics.

**Ground truth (attribution):** none.

**Datasets.** (1) unlabeled captured traffic for pre-training ("no special requirement… cover the mainstream protocols"); (2) ISCX2016 VPN-nonVPN, labeled into 12 classes following Wang et al.'s open-source DeepTraffic processing; (3) 100 Android apps' HTTPS flows (top Chinese app-market apps). 90/10 split; precision/recall/F1.

**Key numbers.** ISCX: PERT P 0.9327 / R 0.9322 / F1 0.9323 vs CNN-1D 0.8610, HAST-I 0.8742, ML-2 (DT + time-series features) 0.8898. Android 100-class: PERT F1 0.9007 vs HAST-I 0.8167; ML-1 fails entirely. Packet-count ablation: 5→20 packets buys only +1.28% F1 on Android; "using 5-10 packets… will be sufficient." Concatenation merging converges faster than LSTM merging with equal accuracy.

**Stated limitations (near-verbatim; no explicit limitations section).** "Even if properly optimized, current BERT pre-training is very costly when we use 4 Nvidia Tesla P100 GPU cards." "The encoding costs on a long string are not affordable for complex dynamic word embedding. At the current stage, the 'packet-level encoding + flow-level merging' is the best option." Also notes on data: "We find the ISCX data set is not entirely encrypted as it also contains data of some unencrypted protocols like Domain Name System (DNS)."

**My gap observations.**
- The paper itself flags that ISCX contains unencrypted protocols, then reports +7-point gains over CNNs there - the obvious follow-up (is the masked-LM/classifier exploiting plaintext handshake/DNS fields, i.e., a shortcut?) is never asked; attribution on tokens would answer it and the transformer makes it trivially available. This unexamined-shortcut pattern propagates to the whole BERT-for-traffic lineage.
- What a masked LM can legitimately learn from *ciphertext* bytes (which should be near-uniform) is left completely untheorized - a semantic-validity question that XAI could probe.
- Bigram tokenization doubles vocabulary "to extend the vocab size" with no linguistic justification for byte data; interpretation of any future token attribution would be confounded by overlapping bigrams.

---

## 6. A Consistent and Efficient Evaluation Strategy for Attribution Methods (ROAD) (Rong*, Leemann*, Borisov, G. Kasneci, E. Kasneci - ICML 2022, arXiv:2202.00449)
**Read depth:** full_text (main body; appendices B-D not read in detail).

**What it is.** Methodology paper (image domain). Information-theoretic analysis of pixel-perturbation evaluation (MoRF/LeRF removal, with/without ROAR retraining). Central identity: Eval outcome I(x'_l;C) = Feature Info I(C;x'_l|M) + Mask Info I(C;M) − Mitigator I(C;M|x'_l). With invertible imputation (fixed-value filling), the Mitigator vanishes and **"Class Information Leakage"** occurs - the *shape of the removal mask* leaks the label. Fix: **Noisy Linear Imputation** (each removed pixel = weighted mean of neighbors, w_d = 1/6 direct, w_i = 1/12 diagonal, sparse linear system, + noise σ = 0.1), approximating the "Minimally Revealing Imputation" condition I(x'_l;M) ≈ 0. ROAD = removal + debiased imputation + **no retraining**.

**XAI evaluation (how the paper evaluates evaluation).** No ground truth: quality of the strategy is operationalized as (a) **consistency** - "Spearman Rank correlation" between attribution-method rankings under MoRF vs LeRF and under retrain vs no-retrain; (b) **efficiency** - runtime. Explicitly positions itself among "functional-grounded metrics [that] do not require a human-generated ground truth that can be hard or even impossible to obtain" (citing Doshi-Velez & Kim). Fidelity itself = accuracy-drop curves on imputed inputs.

**Ground truth:** none (consistency proxy; leakage demonstration uses a mask-only classifier, an architectural argument about the *evaluator*, not attribution ground truth).

**Setup / key numbers.** CIFAR-10 (+Food-101 in appendix, >1000 retrained models); 8 attribution methods (IG, GB × {plain, SG, SQ, Var}); ResNet-18. Mask-only classifier reaches **~80% accuracy (vs 85% on full images)** for IG-SG masks - "the feature values do not play an important role in the evaluation." Spearman MoRF-vs-LeRF: fixed imputation **−0.01 (retrain) / 0.01 (no-retrain)** → Noisy Linear **0.61 / 0.58**. Retrain-vs-no-retrain: fixed 0.15 (MoRF) / 0.09 (LeRF) → lin **0.84 / 0.94**. Runtime per method: ROAD 33.3 s vs ROAR 3903 s - "0.9%", "saves up to 99% in computational costs". Under ROAD, IG-SG flips from worst (fixed, MoRF) to best - rankings in prior ROAR-based work are cast in doubt.

**Stated limitations / future work (near-verbatim).** "We see that some inconsistencies still remain, which cannot be compensated by the current imputation. However, the evaluation strategies might also consider different characteristics of an attribution method (e.g., one might be particularly good at identifying irrelevant pixels), which is why perfect agreement might not even be desirable." "Going forward, we plan to investigate more sophisticated imputation models in ROAD as well as other evaluation metrics besides fidelity."

**My gap observations.**
- Consistency is necessary but not sufficient: a *consistently biased* evaluator scores perfectly on their criterion; without ground truth (cf. Zhou et al., same batch) one cannot tell debiasing from re-biasing. The two papers are complementary and neither cites a network-traffic instantiation.
- Noisy Linear Imputation is intrinsically image-specific - it rests on measured neighbor correlations (ρ = 0.89/0.82 on CIFAR-10). For NTC inputs (byte sequences, packet-size/IAT series, FlowPic histograms) no analogue exists; naive interpolation would produce protocol-invalid, out-of-manifold "flows," so every deletion/insertion-style metric currently used in NTC XAI papers inherits *both* the leakage confounder and an unsolved imputation problem. Designing a protocol-consistent traffic imputation operator is an open, publishable gap.
- The leakage result retroactively undermines occlusion/deletion evaluations copied into security/NTC papers (masking bytes with zeros is exactly the invertible "reserved value" imputation they prove worst).
- Residual hyperparameters (σ = 0.1, neighbor weights) contradict the stated goal of a hyperparameter-free evaluator; sensitivity to them is not reported in the main body.

---

## Batch-level synthesis for the journal paper
Three NTC representation papers (TFE-GNN, FlowPic, PERT) span the field's three dominant input encodings - byte-PMI graphs, 2D time×size histograms, payload-token transformers - and contain **zero explanation evaluation**, while using interpretability rhetoric in motivation or architecture naming. The one applied XAI paper (Kalakoti JIOT'24) evaluates LIME/SHAP *quantitatively* but exclusively with model-referential proxy metrics (faithfulness, monotonicity, complexity, sensitivity). The two methodology papers show precisely why that is insufficient: Zhou et al. demonstrate that popular attribution methods fail against constructed ground truth even in favorable conditions and urge that "proxy metrics … be first calibrated with ground truth in a controlled setting"; ROAD proves the deletion-style metrics underlying "faithfulness" leak class information through the removal mask and depend critically on a domain-appropriate imputation operator that does not exist for traffic data. Concrete openings: (1) port Zhou-style semi-natural ground-truth construction to flows (injected byte/size/timing artifacts + label reassignment on ISCX-class datasets); (2) define protocol-valid, minimally revealing imputation for packet sequences to enable a "traffic-ROAD"; (3) audit the representations themselves for attribution-hostility (TFE-GNN's byte-value node collapse being the extreme case).
