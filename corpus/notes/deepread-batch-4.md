# Deep-Read Notes - Batch 4 (XAI for Network Traffic Classification survey)

Reader: Claude (deep-read subagent) - 2026-08-22
Focus fields: how explanation quality is EVALUATED; what ground truth (if any) is used; authors' stated limitations; gaps I observe that authors do not state.

Papers in this batch:
1. Traffic-Explainer (arXiv:2509.18007, KDD 2025) - full text
2. EXP-SEC (arXiv:2607.12203, 2026) - full text
3. SoK: Explainable ML in Adversarial Environments (IEEE S&P 2024) - full text (PDF via https://oaklandsok.github.io/papers/noppel2024.pdf)
4. Revisiting Sanity Checks for Saliency Maps (arXiv:2110.14297, XAI4Debugging@NeurIPS 2021) - full text
5. A Fresh Look at Sanity Checks for Saliency Maps (arXiv:2405.02383, xAI World Conf 2024) - full text (main body; supplement not deep-read)
6. Dos and Don'ts of Machine Learning in Computer Security (USENIX Security 2022, arXiv:2010.09470v2) - full text incl. appendices

---

## 1. Building Transparency in Deep Learning-Powered Network Traffic Classification: A Traffic-Explainer Framework

**Authors/venue:** Riya Ponraj, Ram Durairajan, Yu Wang (Univ. of Oregon / Link Oregon). arXiv:2509.18007; batch metadata lists KDD 2025 (DOI 10.1145/3770854.3783939).

**Task & datasets:**
- App classification: ISCX-VPN, ISCX-NonVPN, ISCX-Tor, ISCX-NonTor (byte sequences; SplitCap bidirectional flows; Tor flows split into 60s blocks; preprocessing follows TFE-GNN [48]: ≤50 packets, 150 payload + 40 header bytes/packet). Notably, Appendix A calls these "the first four **synthetic** traffic flow datasets."
- Traffic localization (country US/China/India): Cross-Platform iOS (196 apps) and Android (215 apps) datasets [27, 42].
- Network cartography: self-collected 5,000 traceroutes (RIPE Atlas + CAIDA Ark, 3 days, 15 submarine cables / 10 source-destination pairs; collaboration with Link Oregon domain experts). RTT sequences → cable class. Semi-supervised: only 5% labeled.

**Model:** Transformer classifier (byte/RTT tokenization + positional encoding + self-attention + pooling) and MLP; transfer test also on ET-BERT.

**XAI method:** Traffic-Explainer - model-agnostic, input-perturbation, *learned mask* over sequence units optimized by mutual-information maximization (GNNExplainer-style objective adapted to sequences): min conditional entropy H(Y|X̂) (confidence variant), class-label variant (Eq. 3, slightly better), global class-level variant (Eq. 4); mask budget regularization ReLU(||M||1 − B). Byte-byte interaction variant masks self-attention. Explanations are score masks in R^257 (bytes) or R^257×257 (byte pairs); Top-K (1/5/10% budgets) selected.

**How explanation quality is evaluated (xai_evaluation):**
- Four metrics (Sec 5.1.3 / Appendix B): **"Fidelity, Accuracy, Counterfactual Fidelity, and Counterfactual Accuracy"** - keep-only-Top-K bytes vs. remove-Top-K bytes, then re-run the classifier and measure agreement. All are model-behavior deletion/insertion proxies (Fid/Acc = keep-only; C-Fid/C-Acc = remove).
- Baselines: Random, Saliency Map (gradient), SHAP, LIME (byte level); Random, Self-Attention (byte-byte level); NetExplainer at global level. Claim: "improves upon existing explanation methods by approximately 42%" (abstract).
- Byte-swap experiment (localization, Sec 5.3): swap Top-10% explanatory bytes between flows of different countries; measure class "transformation rate" on Transformer, ET-BERT, MLP - transfer across models is argued to show the bytes are "causal features that truly characterize country-level traffic patterns." (Interventional in flavor, but the criterion is still prediction change of models - no task-level truth.)
- Cartography (Sec 5.4): qualitative visual check - identified RTT hops are "cross-validated against the ground-truth RTT sequence: if they align with the hops exhibiting significant RTT spikes, it confirms the reliability of our mapping model." Heatmap-vs-spike alignment in Figure 5; no metric.
- Efficiency: 2.52/2.12/1.90/2.10 s per instance across the four ISCX datasets. Sensitivity to sequence length (Fig 3b): explanation quality decreases slightly with longer sequences.

**Ground truth used:** none (strict reading). All quantitative metrics are deletion/keep proxies; byte-swap validates cross-model causality of prediction change, not correctness vs. an independent truth; RTT-spike alignment is a qualitative domain-expectation check (borderline human_expert, but visual-only, single task, unquantified).

**Key numbers:** Traffic-Explainer @5% budget byte-level: Fid 97.5 (ISCX-VPN), 92.4 (NonVPN), 92.0 (Tor), 96.1 (NonTor) vs LIME 94.9/75.7/68.4/69.0; SHAP degenerate (C-Fid 0.00 everywhere, identical Fid across 1/5/10% budgets). Byte-byte level: slightly below Self-Attention on ISCX-VPN/NonVPN Acc and C-Fid. Cartography classification: mostly 92-100% per class, but class 1 = 0.42% (1/239) in Table 5, unremarked. Localization: Traffic-Explainer beats Saliency Map at 5-10% budgets but loses at 1% on IOS (45.43 vs 72.51 Fid).

**Stated limitations (near-verbatim):** No dedicated limitations section. Closest statements: "We observe a slight decrease in explanation quality as sequence length increases, although the pattern is not strictly monotonic... As the sequence grows, the larger number of interacting byte pairs makes it harder for Traffic-Explainer to recognize the contribution of specific bytes" (5.2.4); "it performs slightly below the Self-Attention Baseline on the ISCX-VPN and ISCX-NonVPN datasets when evaluated using Acc and C-Fid" (5.2.1); Appendix F (ethics): "its capability to automatically uncover fine-grained packet features and traceroute paths may inadvertently expose sensitive user information... could be adversarially exploited to spoof or falsify location information."

**Gap observations (mine):**
- **Metric-definition inconsistency:** Appendix B's printed formulas for Fid and Acc are identical (both compare the keep-only prediction to the ground-truth label Y^{i,*}), and C-Fid/C-Acc as printed ("percentage of updated predictions that equal the original model predictions after removing the Top-K bytes") would make HIGH C-Fid mean the explanation did NOT matter - yet the tables bold high C-Fid as best and Random gets near-zero C-Fid. The reported numbers only make sense if C-Fid is actually a flip/degradation rate. Definitions, text and usage are mutually inconsistent; the actual implemented metric is not recoverable from the paper.
- **Evaluation-objective circularity:** the explainer is trained by optimizing masked-prediction confidence - nearly the same quantity the Fid/Acc metrics measure. Its ~42% "improvement" over LIME/SHAP/Saliency is partly by construction (it optimizes the test).
- **OOD deletion problem unaddressed:** masking bytes (embedding × sigmoid(mask)) produces inputs off the training manifold; no discussion of the deletion-metric OOD critique (ROAR etc.).
- **SHAP baseline is visibly broken** (0.00 C-Fid at every budget, identical values across budgets) and this is never remarked on; comparisons to it inflate the claimed margin.
- **No semantic validation of "important bytes":** e.g., "0th/1st/9th bytes are crucial for identifying Chat" - never mapped to protocol fields; for localization, no check that the model isn't keying on IP-address/header bytes (a classic ISCX/Cross-Platform shortcut, i.e., Arp et al.'s P4 spurious correlations). The privacy narrative ("journalists could obfuscate location-revealing bytes") presumes the bytes are semantically meaningful, which is unverified.
- **Table 5 anomaly:** class 1 accuracy 0.42% while text claims "exceptional classification performance"; also train/val/test for traceroute is 10%/10%/80% (Table 3) contradicting the 70/15/15 split stated in 5.1.4.
- No human/operator study despite operator trust being the paper's core motivation; 2+ s/instance optimization cost makes online use doubtful and is not discussed as a limitation.

---

## 2. Explaining Intrusion Alert Decisions of Deep Learning-based NIDS for Security Analysts (EXP-SEC)

**Authors/venue:** Ayush Kumar, Vrizlynn L.L. Thing (ST Engineering, Singapore). arXiv:2607.12203 (July 2026, journal-style preprint).

**Task & datasets:** Explaining alerts of DL-based NIDS. Targets: Kitsune (autoencoder-ensemble NIDS) with its published (Mirai) dataset; RNN-IDS with NSL-KDD. Black-box assumption (NIDS vendors don't expose models).

**XAI method:** EXP-SEC framework:
1. Forensic module: packet ring buffer + Pkt_ID; on alert, pulls suspect pcap; TRUSTEE-style decision-tree surrogate of the NIDS; binary-search approximation of the relevant windowed inputs (||f'(X_{t,m}) − f'(X_{t,k})||1 < δ).
2. Explanation module: local linear surrogate fitted with **adaptive sparse group lasso with overlapping groups (ASGL-O)** (yaglm package, 5-fold CV) over feature groups (protocol-derived; overlapping features like HpHp_0.1_weight_0 belong to ARP/TCP/UDP groups); subsumes xNIDS's sparse group lasso.
3. Mapping module: de-constructs the AfterImage feature extractor (spatial context keys MAC/MI, H, HH, HpHp, HH_jit; statistics w/µ/σ/magnitude/radius; 5 decay windows L1-L5), correlation engine, semantic reasoning engine → MITRE ATT&CK / Cyber Kill Chain-style analyst narratives. Three worked scenarios: Mirai scanning, data exfiltration, ARP spoofing.

**How explanation quality is evaluated (xai_evaluation):**
- Conventional feature-level metrics from Warnecke et al. EuroS&P 2020 [26]: **"Descriptive Accuracy" (DA)** - "modify(k) nullifies k important features to zero," expect drop in detection output; area under ADA curve. **"Sparsity"** via **"Mass Around Zero (MAZ)"** AUC. **"Stability"** - intersection of top-K features across repeated runs.
- New metrics: **"Group-wise Deletion AUC"** (progressively mask top-ranked groups, track confidence decline; lower better) and **"Group Bloat Factor" GBF = |G_active| / |G_true causal|** (overlap-aware; only RNN-IDS, since Kitsune groups don't overlap).
- Runtime per sample.
- Baseline: xNIDS only (justified because xNIDS beat LIME/SHAP/LEMNA/IG/LRP previously).

**Ground truth used:** none. All deletion/sparsity/stability proxies. GBF's denominator "true causal groups" is never operationally defined (presumably the constructed overlapping group structure). The mapping module's analyst-facing output is never evaluated at all (no user study, no correctness check of tactic mapping).

**Key numbers:** DA-AUC: EXP-SEC 0.19524 (Kitsune) = identical to xNIDS 0.19524; RNN-IDS 0.46947 vs 0.81863 (lower better, EXP-SEC wins). MAZ AUC ≈ 0.494-0.496 for all (tie). Stability: EXP-SEC 0.85/0.42 vs xNIDS 0.9/0.5 (EXP-SEC slightly worse). Group Deletion AUC: 0.19524/0.68806 vs 0.22994/0.77267 (EXP-SEC wins). GBF: 1.00 vs 1.33 (RNN-IDS). Runtime: EXP-SEC 25.34/23.31 s/sample vs xNIDS 0.0217/0.0443 - "~10^3 times slower... EXP-SEC is, therefore, more suited as an offline explanation framework."

**Stated limitations (near-verbatim, Sec 5 Discussion + others):**
- "EXP-SEC is on average ∼10^3 times slower than xNIDS... more suited as an offline explanation framework."
- Stability "depends on the stability of underlying ASGL-O implementation. By controlling the various sources of randomness... stability can be improved further."
- Adaptability requirements framed as open needs: "Network throughput can fluctuate significantly... the framework must automatically pivot to a low-latency mode"; "The structural groups used by the lasso surrogate... cannot be hardcoded... must be determined dynamically"; "if the NIDS is upgraded... the framework should adaptively unlock faster, white-box gradient attribution methods."
- Adversarial evasion: "Sophisticated attackers may figure out how an XAI framework perturbs data... craft malicious traffic wrapped in an adversarial layer... The explanation framework's perturbation and sampling engine must be dynamic and unpredictable."

**Gap observations (mine):**
- **The paper's headline contribution - analyst-understandable explanations - is never evaluated.** No user study with SOC analysts, no measure of correctness/utility of the mapping-module narratives; only three hand-crafted scenario walk-throughs. The quantitative evaluation covers only the feature-attribution core, on the same proxy metrics as prior work.
- **"True causal" groups in GBF undefined** - the one metric that gestures at ground truth has no stated procedure for establishing it.
- **Zero-nullification DA contradicts the paper's own thesis:** they argue traffic features have strict structural dependencies (validity/mutex relations), yet the deletion metric sets features to zero, creating exactly the invalid feature combinations they criticize others for ignoring (OOD evaluation).
- Suspicious table values: EXP-SEC's Kitsune DA-AUC (0.19524) is bit-identical to xNIDS's DA-AUC and to EXP-SEC's own group-deletion AUC - likely copy-paste, undermines confidence in the numbers.
- Datasets are legacy/lab (NSL-KDD, Kitsune-Mirai) despite the enterprise-SOC framing - P1/P9 in Arp et al. terms; ironically Arp et al.'s critique of the Mirai capture (attack trivially separable by packet frequency) applies to the very NIDS they explain.
- Only one baseline (xNIDS) and two NIDS; forensic module (whether the isolated packets are the right ones) not evaluated.

---

## 3. SoK: Explainable Machine Learning in Adversarial Environments

**Authors/venue:** Maximilian Noppel, Christian Wressnegger (KIT/KASTEL). IEEE S&P 2024. PDF: https://oaklandsok.github.io/papers/noppel2024.pdf

**Type:** Systematization of Knowledge - no new experiments, no datasets, no proposed XAI method. Scope: post-hoc feature-attribution explanations for (non-generative) classifiers.

**Content:**
- Threat models: input manipulation (M1: imperceptibility, universality, feature-subspace masks), model manipulation (M2: ε-accurate / ε-agreeing constraints; data poisoning open), system manipulation (M3, e.g., fairwashing with surrogate models).
- Attack taxonomy: explanation-preserving (EP), prediction-preserving (PP), dual (D); scopes untargeted / semi-targeted / targeted (Table 2 categorizes ~30 attack papers).
- **Hierarchy of robustness notions** (their formal core): constraints {LIP (Lipschitz), EXPLSIM_ε (explanation similarity), EXPLEQ (equivalence)} × restrictions {CLSEQ (same class), LOC_δ (vicinity), none}; implication lattice with proofs (some require convex X - explicitly fails for categorical/discrete features). Key finding: "different authors describe different understandings of robustness with the same key phrase" (e.g., 'attributional robustness' = LIP-around-x for Wang et al. but LOC+CLSEQ|EXPLSIM for Ivankay/Sarkar).
- Defense taxonomy: training-time T1-T4 (data validation, model sanitization, robust architectures - Softplus/Bayesian NNs, robust training - Hessian/weight regularization, ATEX, ExpO) and operation-time O1-O3 (input sanitization, model monitoring, I/O validation); certified robustness via linear regions and randomized smoothing (Levine et al. top-k guarantee ≈ LOC|EXPLSIM).

**How explanation quality/robustness is evaluated:** as an SoK, none empirically. The systematized *notions* are the field's evaluation instruments: distances d_E in explanation space, top-k intersection, Kendall rank correlation, SSIM - all similarity/stability measures against a benign reference explanation, never against explanation correctness. Meta-review appendix explicitly flags this: "we would like to see some discussions regarding how the premature nature of this space and its consequential operational issues (e.g., inaccuracy of attribution results) interact with adversarial attempts."

**Ground truth used:** none. (Notably, they discuss explanation-guided training that uses "a ground truth explanation per sample as regularization" and warn: "similarities (a) pose the risk of guidance actually being an unwilling manipulation.")

**Key numbers:** none (systematization; 8 open RQs; ~200 refs; Table 2 covers ~30 attacks incl. 5 fairwashing works).

**Stated limitations / future work (near-verbatim, the 8 Open RQs):**
1. "To which extent do different threat models and attack objectives conflict in their required robustness notions?" (they show defender requirements for PP vs dual adversaries are conflicting).
2. "How to provide guarantees for the robustness around x for explanation methods, other than gradient-based methods?"
3. "How to generalize guarantees from randomized smoothing to other dissimilarity metrics and explanation methods...?"
4. "To what extent can explanations be fooled in a data manipulation setting to bypass sanitization?"
5. "To what extent are recent model sanitizations and validations effective against explanation-preserving, dual, and in particular, prediction-preserving attacks?"
6. "What are effective and efficient regularization techniques for general explanation methods? How can we reduce the required computational efforts...?"
7. "How do the introduced techniques perform in sanitizing and detecting explanation-aware input manipulations...? To what extent can explanation-aware attacks be utilized to bypass recent explanation-based detection techniques?"
8. "To what extent and how can public authorities audit and verify the inner working of an explainable system...?"
Also: "Robustness proofs need to be decoupled from specific explanation methods" via axioms (sensitivity, completeness, implementation invariance, conservation, positivity, continuity) - "many explanation methods have been proposed without pointing out which axioms they satisfy. This drawback hinders research and renders the provided guarantees inaccessible." And: "defenses against explanation-aware attacks are scarce."

**Gap observations (mine):**
- **Robustness ⟂ correctness:** every notion in the hierarchy measures stability relative to the benign explanation; a method could be certifiably robust while being robustly wrong. The SoK never connects its notions to faithfulness/ground-truth quality (the meta-review's "premature XAI" concern makes the same point from outside).
- **Discrete feature spaces break the theory:** two of their results require convex X ("for categorical and discrete features this is not the case and these two results do not necessarily apply"). Network traffic (bytes, protocol fields, flags) is exactly this setting - the certified-robustness toolbox they map out largely does not transfer to NTC, and no traffic-domain attack/defense appears in Table 2. Explanation-aware attacks on NIDS/NTC explainers are an open, uninstantiated threat model.
- All examples/intuitions are vision-centric (heatmaps, patches, SSIM); imperceptibility metrics for traffic perturbations are undefined in the field.
- No benchmark accompanies the SoK; the field lacks standardized evaluation of explanation-aware attacks even in vision.

---

## 4. Revisiting Sanity Checks for Saliency Maps

**Authors/venue:** Gal Yona (Weizmann), Daniel Greenfeld (Jether Energy). XAI4Debugging @ NeurIPS 2021 workshop; arXiv:2110.14297. 7 pp + appendix.

**Task & datasets:** Vision (MNIST; TinyImageNet 10-class subset, 64×64). CNN for MNIST variants; ResNet18 finetuned for ImageNet-pairs task. Methods examined: vanilla backprop (VBP) vs guided backprop (GBP) - chosen because Adebayo et al. 2018's model-randomization sanity checks pass VBP but fail GBP.

**Method:** causal re-framing of the Adebayo et al. model-randomization test. Causal graph T→M, T→X, X→S, M→S; the task T confounds M and S; back-door adjustment yields Λ(x) = Σ_t (S(x;M_t) − S(x;M′))·Pr(T=t|X=x) (Eq. 1) - i.e., the sanity check is distribution/task-dependent. On "natural" tasks (MNIST/ImageNet: single centered object per label), a random model's map can coincide with the trained model's map for reasons unrelated to the saliency method.
**Engineered tasks with known correct maps:** (a) MNIST half-deletion task (classify whether bottom half deleted); (b) MNIST multi-object (digit + random rectangle/circle; two tasks: predict shape vs predict digit; both models 0.99 test acc); (c) TinyImageNet pairs - two images side by side, label = class of the image from group 1 (ResNet18, ~0.77 acc). "We guarantee that the 'correct' saliency map (which in this case we know, having designed the task ourselves) will be visually distinct from that produced by any model that is unaware of the labels."

**How explanation quality is evaluated (xai_evaluation):** modified sanity check = visual comparison of S(x;M) vs S(x;M′) across trained/pretrained/random models on the engineered tasks; accuracy of maps judged by **visual inspection** against the by-construction correct region ("we can indeed verify that both methods produce accurate saliency maps"). **No quantitative similarity metric anywhere** - evaluation is entirely qualitative (Figures 1-7). Result: on engineered tasks both GBP and VBP show non-zero causal effect and highlight the correct object → Adebayo-style rejection of GBP "may be an artifact of the tasks."

**Ground truth used:** synthetic - tasks constructed so that "high accuracy is only possible when the model learns to attend to one type of object and ignore the other," giving known correct saliency regions (footnote 3 concedes: "In general... we have no knowledge of the 'correct' saliency maps.").

**Key numbers:** MNIST variant models trained to 0.99 test accuracy; ResNet18 pairs model ~0.77; no XAI metrics reported.

**Stated limitations (near-verbatim):** "our work challenges the utility of the sanity check methodology, and further highlights that saliency map evaluation beyond ad-hoc visual examination remains a fundamental challenge"; "this does not challenge the basic idea... What it does highlight is that when performed carefully, the necessary condition this perspective proposes may be too weak to provide meaningful distinctions between the existing plethora of saliency methods"; scope restricted to model randomization ("Our focus is on the first" of the two randomization procedures) and to VBP/GBP; future: "explore whether semi-synthetic, engineered tasks... could be used to compare the utility of different methods on a per-task basis."

**Gap observations (mine):**
- Ironically, the paper criticizing evaluation practice performs **no quantitative evaluation itself** - the claimed non-zero causal effects and "accurate maps" are asserted from a handful of visual examples, no map-similarity statistics, no sample counts.
- The "known correct map" argument assumes the trained model uses the intended feature; at 0.77 accuracy (ImageNet pairs) the model may partly rely on other cues, so ground truth is model-conditional, not absolute - the same subtlety that plagues "expected explanation" checks in traffic (e.g., RTT spikes).
- Tiny scale (one architecture per task, two saliency methods) limits the generality of "GBP is fine."
- **Transfer to NTC:** nobody has replicated this confound analysis for traffic models. The direct analogue - semi-synthetic traffic with implanted, by-construction discriminative bytes/fields as explanation ground truth - is essentially absent from the XAI-NTC literature and is exactly what the field needs; this paper is the methodological template.

---

## 5. A Fresh Look at Sanity Checks for Saliency Maps

**Authors/venue:** Anna Hedström, Leander Weber, Sebastian Lapuschkin, Marina Höhne (TU Berlin / Fraunhofer HHI / ATB / BIFOLD). World Conf. on eXplainable AI 2024; arXiv:2405.02383.

**Task & datasets:** XAI-evaluation methodology, vision only: ImageNet (VGG-16, ResNet-18), MNIST + fMNIST (LeNet). 10 attribution methods + random-attribution baseline (Gradient, Saliency, GradCAM, SmoothGrad, IntegratedGradients, LRP-ε, LRP-z+, Guided-Backprop, GradientSHAP, Input×Gradient). Implemented in Quantus.

**Method:** two fixes to the Model Parameter Randomisation Test (MPRT), responding to documented caveats (pre-processing strips sign/scale info; top-down layer order retains lower-layer information; SSIM/Spearman similarity measures "can be minimised by statistically uncorrelated random processes" and thus favour noisy gradient methods):
- **sMPRT:** denoise attributions by averaging over N perturbed inputs (N=50 recommended) before computing similarity; bottom-up randomisation.
- **eMPRT:** drop pairwise similarity entirely; compare **discrete histogram entropy (complexity)** of the explanation before vs after FULL model randomisation: q̂ = (ξ(ê) − ξ(e))/ξ(e).

**How explanation quality is evaluated / how the metric itself is evaluated (xai_evaluation):**
- The paper's object of evaluation is the *metric*: **meta-evaluation with MetaQuantus** - meta-consistency score MC ∈ [0,1] built from intra-consistency (IAC, Wilcoxon-based) and inter-consistency (IEC, ranking changes) under minor noise (Noise Resilience) and disruptive perturbations (Adversary Reactivity), applied in input space (IPT) and model space (MPT); 3 iterations, K=5.
- Explanations themselves are still scored only by MPRT-family randomisation responsiveness (similarity drop or entropy rise) - an axiomatic necessary-condition test, not correctness.

**Ground truth used:** none - the paper's premise is explicit: "generally, ground truth explanation labels do not exist"; MetaQuantus perturbation tests encode *expected metric behaviour*, not correct explanations.

**Key numbers:** sMPRT: max inter-method SSIM gap shrinks ~0.38→~0.34 (VGG-16) and ~0.50→~0.46 (ResNet-18) after denoising (N=50; AUC converges by N=50, tested to 300). eMPRT: no method reaches the theoretical randomness limit; rankings flip strongly vs MPRT - "Contrary to assertions [Adebayo et al.] that claimed Guided Backpropagation to perform worse than gradient-based methods... our eMPRT evaluations advance Guided Backpropagation above its gradient-based counterparts." Random attribution scores lower under eMPRT than MPRT but "does not always receive the lowest rankings; in some settings, LRP-ε, GradCAM, and SmoothGrad are ranked lower." Meta-evaluation: eMPRT/sMPRT ≥ MPRT in most of 16 settings; MC range ≈ 0.52-0.74 (e.g., MNIST-LeNet-M3: eMPRT 0.740±0.036 vs MPRT 0.600±0.048); "neither Figure 6 nor Table 1 indicates perfect reliability, i.e., MC = 1, for any metric variant"; many differences within 1 std.

**Stated limitations (near-verbatim, Sec 5.1/5.2/5.3):**
- sMPRT: "more computationally expensive... (N ≥ 50)"; for SmoothGrad/NoiseGrad-style methods denoising "limit[s] sMPRT's efficacy with these methods and blurring the distinction with their baseline methods"; "the degree of noisiness is an arguable property of attribution methods and removing it before evaluation may yield non-representative or biased results"; "introduces additional hyperparameters σ and N... may not be tunable on any given data domain, e.g., climate data."
- eMPRT: "may... exhibit variability based on different tasks or data-related factors, such as object size in vision datasets"; bin count B "may need adaptation depending on the task or dimensionality."
- General: "no evaluation metric in isolation is sufficient to determine explanation quality"; "the ongoing necessity for careful use of evaluation metrics, particularly in the field of XAI where definitive ground truth explanation labels are often unavailable"; "All evaluated methods scored poorly in absolute term... with small margins between XAI methods."
- Future work: combine sMPRT+eMPRT; "additional empirical studies are necessary to validate the application of bottom-up randomisation."

**Gap observations (mine):**
- **Infinite regress of proxies:** the metric that evaluates explanations is itself evaluated by another proxy (MetaQuantus consistency), with no ground truth anywhere in the tower; "reliability" (MC) is consistency under perturbation, not correctness.
- The improved metric still sometimes ranks real methods **below random attribution** - a failed sanity check of the sanity check, noted but not resolved.
- Ranking volatility between MPRT variants (Fig 5) implies conclusions of any past paper that ranked methods with MPRT (rare in NTC but the checks are cited everywhere) are metric-version-dependent; small margins + overlapping std suggest low discriminative power at realistic budgets.
- Vision-only: histogram-entropy complexity and the "object size" caveat have untested analogues for byte-sequence/flow-feature explanations (flow length, #active features); nothing in the MPRT-variant literature has been applied to traffic classifiers.

---

## 6. Dos and Don'ts of Machine Learning in Computer Security

**Authors/venue:** Daniel Arp, Erwin Quiring, Feargus Pendlebury, Alexander Warnecke, Fabio Pierazzi, Christian Wressnegger, Lorenzo Cavallaro, Konrad Rieck. USENIX Security 2022; arXiv:2010.09470v2.

**Type:** methodology paper. Ten pitfalls across the ML workflow: P1 sampling bias, P2 label inaccuracy, P3 data snooping (test/temporal/selective), P4 spurious correlations, P5 biased parameter selection, P6 inappropriate baseline, P7 inappropriate performance measures, P8 base rate fallacy, P9 lab-only evaluation, P10 inappropriate threat model.

**Evidence:**
- Prevalence analysis: 30 top-tier (CCS/S&P/USENIX/NDSS, 2011-2020) ML-security papers, 2 reviewers + adjudicator, Krippendorff α = 0.832. P1 at least partly present in 90%, P3 in 73%, P10/P9/P7 in >50%; "each paper suffers from at least three pitfalls"; only 22% of pitfall instances discussed in text. Author survey: 49/135 responses (36%); avg agreement with findings 63%; authors self-report 2.77±1.53 pitfalls; 98% say the paper raises awareness.
- Impact case studies:
  - Android malware (P1,P4,P7): AndroZoo/DREBIN origin bias (P(Chinese market | ≥10 AV detections) ≈ 70%); mixing GooglePlay benign + Chinese malware (D1) vs GooglePlay-only (D2): DREBIN recall −12.2%, OPSEQS −16.9%; "the URL play.google.com turns out to be one of the five most discriminative features for the benign class."
  - Vulnerability discovery (P2,P4,P6): VulDeePecker on CWE-119; **LRP explanations (following Warnecke et al.) reveal** top tokens are artifacts (INT1 70.8%, '(' 61.1%, '*', INT2...); buffer size 32 occurs 99.1% in class 0. Linear SVM with 3-grams: AUC 0.986 / TPR 0.963 vs VulDeePecker 0.984 / 0.818 with 18× fewer parameters. Truncation/normalization make some labels undecidable (P2).
  - Code authorship (P1,P4): GCJ template reuse; removing unused code from test set drops accuracy by 48%; after retraining still −6/−7%.
  - **Network intrusion detection (P6,P9): KITSUNE autoencoder ensemble on the Mirai capture vs a boxplot on 10-s packet frequency: baseline AUC 0.998 vs 0.968; TPR@FPR=0.001: 0.996 vs 0.882.** "In the Mirai dataset the infection is overly conspicuous; an attack in the wild would likely be represented by a tiny proportion of network traffic"; benign activity halts when the attack begins.

**How explanation quality is evaluated (xai_evaluation):** none - explanations are not the object of evaluation. XAI (LRP, linear-model weights) is used *diagnostically*: the P4 recommendation reads "we generally recommend applying explanation techniques for machine learning [59, 79, 133]. **Despite some limitations [e.g., 66, 75, 127], these techniques can reveal spurious correlations**" (66=Hooker et al. ROAR benchmark, 75=Kindermans et al. (un)reliability, 127=?). Explanation findings are corroborated indirectly by interventions on data/models (dataset re-composition, artifact removal + retraining, simple baselines), not by any explanation-quality metric.

**Ground truth used:** none (for explanations). The intervention experiments establish ground truth about *model shortcuts* (a causal, remove-and-retrain protocol), but explanation correctness itself is assumed.

**Stated limitations (near-verbatim, §5):** "we cannot cover all ten pitfalls in detail, as our focus is on a comprehensive overview"; "some pitfalls cannot always be prevented, such as sampling bias, label inaccuracy, or lab-only settings... In such cases, simulation is the only option"; "corrective measures may even be an open problem"; paper selection "not entirely free from bias"; "a pitfall is only counted if its presence is clear from the text... we decide in favor of the paper" (undercounting); impact-analysis works chosen "from security areas in which the authors of this paper have also published research. This biased selection, however, should be acceptable, as we intend to empirically demonstrate how pitfalls can affect experimental results."

**Gap observations (mine):**
- **Circularity left open:** the prescribed remedy for spurious correlations is XAI, but the paper gives no protocol for validating the explanations themselves in security settings - unvalidated explainers are used to validate models (they flag "some limitations" only via citation). For my survey this is the canonical statement of the gap: *XAI as auditor with no auditor for XAI.*
- In the one networking case study, the authors did **not** use XAI at all (frequency plot + boxplot sufficed) - a hint that attribution tooling for traffic-anomaly models was too immature to deploy even by the people recommending it.
- Their implicit validation loop - explanation → hypothesized artifact → data intervention → retrain → performance drop - is an unformalized *interventional ground-truth protocol* for explanation claims; no XAI-NTC paper I have read operationalizes it as an explanation-evaluation metric.
- The pitfalls compound in XAI-NTC: explanations of models trained on ISCX/NSL-KDD/Mirai-style data (P1, P9) will faithfully highlight dataset artifacts; "plausible-looking" explanations then *launder* shortcut learning (cf. Traffic-Explainer's unverified "important bytes" in this same batch). P4's "unclear from text... when there is no attempt to explain a model's decisions" also means prevalence of spurious correlations in the literature is a lower bound.

---

## Batch-level synthesis (for the survey's gap analysis)

1. **No paper in this batch evaluates explanation correctness against task-level ground truth in the network domain.** The two NTC/NIDS papers (Traffic-Explainer, EXP-SEC) rely exclusively on deletion/keep-style model-behavior proxies (Fid/Acc/C-Fid/C-Acc; DA/MAZ/stability/deletion-AUC) - precisely the class of measure the batch's methodology papers show to be fragile (OOD deletions, noise-biased similarity, task confounds). The only by-construction ground truth in the batch is in a vision workshop paper (Yona & Greenfeld's engineered tasks).
2. **Circularity appears at three levels:** explainers optimized on the same objective used as the evaluation metric (Traffic-Explainer); sanity-check metrics validated only by further consistency proxies (Hedström et al.); XAI prescribed as the auditor of models with no audit of XAI (Arp et al.).
3. **Human evaluation is absent even where humans are the stated beneficiary.** Both Traffic-Explainer (operators) and EXP-SEC (SOC analysts) motivate everything by practitioner trust and evaluate nothing with practitioners.
4. **The methodology literature has not been ported to traffic.** Model-randomization sanity checks (and their known confounds/fixes), robustness notions and explanation-aware attacks (SoK), and engineered-ground-truth tasks all exist only for vision/text; the SoK's convexity assumptions explicitly break for discrete inputs like bytes - the transfer is not just missing but non-trivial.
5. **Dataset pitfalls and XAI interact:** on lab datasets with conspicuous artifacts (ISCX, Mirai, NSL-KDD), a faithful explanation of a shortcut model looks like a plausible traffic signature. None of the NTC papers checks whether their "important bytes/features" are P4 artifacts, even though Arp et al. (cited by both) demonstrates exactly this failure mode with LRP on VulDeePecker.
6. **Concrete openings for our paper:** (a) formalize the intervention loop (implant/remove known discriminative bytes → retrain → score explainers against the implant) as synthetic ground truth for NTC, in the spirit of Yona & Greenfeld and Arp et al.; (b) port sMPRT/eMPRT-style randomization tests to transformer/AE traffic models and measure their task-confound sensitivity; (c) instantiate the SoK's explanation-aware threat models for NIDS explainers (EXP-SEC itself concedes perturbation-probing evasion); (d) audit published NTC explanation metrics for the definition inconsistencies found here (Traffic-Explainer's C-Fid; EXP-SEC's GBF).

### Sources
- SoK PDF located via web search: [oaklandsok.github.io/papers/noppel2024.pdf](https://oaklandsok.github.io/papers/noppel2024.pdf) (also listed at [IEEE Xplore](https://ieeexplore.ieee.org/document/10646794/))
- All other papers fetched from arXiv PDFs listed in `analysis/deepread-selection.json`; extracted texts cached at `corpus/notes/tmp-*.txt`.
