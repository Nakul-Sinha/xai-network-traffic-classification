# Deep-Read Notes - Batch 1 (XAI for Network Traffic Classification)

Reader: subagent deep-read pass, 2026-08-22.
Focus fields: (1) how explanation quality is EVALUATED, (2) LIMITATIONS / FUTURE WORK.
All six papers read end-to-end from full text (5 via pdftext.py; ShortcutCatcher via CC-BY ACM full text through a reader proxy).

---

## 1. CADE: Detecting and Explaining Concept Drift Samples for Security Applications
**Yang, Guo, Hao, Ciptadi, Ahmadzadeh, Xing, Wang - USENIX Security 2021.** Read: full text (19 pp incl. appendices).

### Task / data / model
- Task: detect individual drifting (out-of-distribution) samples for deployed security classifiers, then explain *why* each one drifted. Two case studies: Android malware family attribution (Drebin, 8 families, 3,317 samples, 1,340 binary features after variance filtering, time-based 80:20 split) and network intrusion detection (IDS2018 / CSE-CIC-IDS2018: Benign, SSH-Bruteforce, DoS-Hulk, Infiltration; 130,702 flows at 10% sampling; 83 flow features - one-hot ports/protocol + 77 MinMax-scaled statistical features). Plus industry test: 20,613 Windows PE malware, 395 families (Blue Hexagon), Ember-style 2,381-dim features.
- Model: contrastive autoencoder (MLP encoder 1340-512-128-32-7 for Drebin; 83-64-32-16-3 for IDS2018); loss = reconstruction MSE + contrastive loss (Eqn. 1, margin m=10, lambda=0.1). Detection by Median Absolute Deviation (MAD, T=3.5) on latent distance to per-class centroids; drifting samples ranked by distance to nearest centroid.

### XAI method
Distance-based perturbation explanation, custom-designed for drift: find a minimal Bernoulli mask m over ORIGINAL features such that replacing masked feature values of the drifting sample x_t with those of the reference training sample x_c (the sample nearest to the centroid of the closest class) minimizes latent distance to the centroid, plus elastic-net sparsity (Eqn. 2); optimized with concrete-distribution relaxation + Adam. Explicitly contrasted with "boundary-based explanation" (supervised perturbation explanation on an MLP approximation of the detector, Fong&Vedaldi-style) and COIN; LIME/SHAP excluded as baselines "because white-box methods usually perform better than black-box methods."

### How explanation quality is EVALUATED (the metric)
1. **Distance-reduction "fidelity" metric** - quote: "We quantify the fidelity of this explanation result by this metric: d'_xt = || f(x_t ⊙ (1−m_t) + x^(c)_yt ⊙ m_t) − c_yt ||_2 ... In this case, a lower distance d'_xt is better." (Table 4: CADE 0.065±0.035 vs original 5.363 on Drebin-FakeDoc, i.e., 98.8% reduction; 2.349±3.238 vs 11.715 on IDS2018-Infiltration, 79.9% reduction; baselines Random 5.422, Boundary-based 3.960, COIN 6.219 on Drebin.)
2. **Boundary-crossing ratio** - "the ratio of perturbed samples that cross the decision boundary. A higher ratio means the perturbed features are more important." (Table 6: CADE 97.64% Drebin, but only 1.41% IDS2018; all baselines ~0%.)
3. **Qualitative case studies** - one randomly picked drifting sample per dataset; features manually checked against external malware analysis reports: "While it is difficult to obtain the 'ground-truth' explanations, we gather external analysis reports about FakeDoc malware and GingerMaster [68,70]." The 42 selected features (of 1000+) include SMS permissions/APIs matching FakeDoc's premium-SMS behavior. Similar informal analysis for Tinba/Smokeloader PE malware.
- Number of selected features: Drebin avg 44.7 (3% of features), IDS2018 avg 16.2 (~20% of features).
- Explanation evaluated on ONE unseen-family setting per dataset ("Results from other settings have the same conclusion and thus are omitted for brevity").

### Ground truth used
**human_expert (qualitative only)** - external analyst reports serve as an informal semantic reference for 1-2 hand-inspected case studies; the *quantitative* evaluation (d', boundary crossing) is a perturbation proxy, NOT ground truth. Authors themselves concede ground-truth explanations are unavailable.

### Key numbers (detection, for context)
Drift-detection F1 0.96±0.03 (Drebin) and 0.96±0.06 (IDS2018) vs Transcend 0.80/0.65 and Vanilla AE 0.72/0.74. PE malware: F1 0.95 (N=10 training families, 160 unseen), 0.87 (N=15). Retraining with 150 CADE-selected samples restores Drebin→Marvin binary F1 from 0.70 to 0.92 (Transcend: 0.74). Runtime: detection 1,422.7s vs Transcend 4,289.3s (IDS2018); explanation 3.2s/sample vs COIN 8.2s.

### Stated limitations / future work (near-verbatim, Sec. 8)
- "First, CADE ranks all the drifting samples in a single list. However, in practice, the drifting samples may contain substructures (e.g., multiple new malware families). A practical strategy could be further grouping drifting samples into clusters."
- "Second, certain hyper-parameters of CADE are determined empirically (e.g., the MAD threshold)... Future work can look into more systematic strategies to configure the hyper-parameters."
- "Third, CADE is designed based on the assumption that the training set does not have mislabeled samples (or poisoning samples). We defer to future work to robustify our system against low-quality or malicious labels."
- "Fourth, our experiments are primarily focused on detecting new families... We defer a more in-depth analysis [of in-class evolution] to future work."
- "Finally, our evaluation in Section 7 is limited to N = 15 training classes... we defer the examination of a larger number of training classes to future work."
- Also: "We leave adversarial attacks against CADE to future work."

### My gap observations (not stated by authors)
- **Self-referential fidelity metric**: d' is literally the objective CADE's explanation optimizes (Eqn. 2 first term), so CADE beating baselines on d' is close to tautological; baselines optimize different objectives. No metric that is neutral w.r.t. the method under test.
- The second metric (boundary crossing) yields 1.41% on IDS2018 - effectively a failure - yet is not treated as a negative result; the asymmetry between Drebin (97.6%) and IDS2018 is left unexplained.
- No human/analyst study despite the system's stated purpose being to save analyst time; no measurement of whether explanations actually speed up triage.
- Qualitative validation covers a single sample per dataset; explanation evaluation covers a single unseen-family configuration per dataset.
- No stability/robustness evaluation of explanations (rerun variance of the stochastic mask optimization is never reported).
- For the NTC case (IDS2018), no domain-semantic check of the 16 selected flow features analogous to the malware case study - the network-traffic explanation is validated only by the proxy metric.

---

## 2. Sanity Checks for Saliency Maps
**Adebayo, Gilmer, Muelly, Goodfellow, Hardt, Kim - NeurIPS 2018 (arXiv:1810.03292v3).** Read: full text (30 pp incl. appendix).

### Task / data / model
Image classification only: Inception v3 on ImageNet, CNN and MLP on MNIST and Fashion-MNIST, Inception v4 on skeletal radiograms. Methods tested: Gradient, SmoothGrad, Gradient⊙Input, Guided Backprop (GBP), GradCAM, Guided GradCAM, Integrated Gradients (IG), IG-SmoothGrad, VarGrad; Sobel edge detector as model-independent baseline.

### XAI evaluation methodology (the paper IS an evaluation methodology)
Two randomization tests ("sanity checks" - necessary conditions, framed as such):
1. **Model parameter randomization test** - cascading (top-down, 17 blocks for Inception v3) and independent per-layer re-initialization; compare saliency for trained vs randomized model. "If the saliency method depends on the learned parameters of the model, we should expect its output to differ substantially between the two cases."
2. **Data randomization test** - permute training labels, retrain to >95% train accuracy (test accuracy at chance), compare saliency. "An insensitivity to the permuted labels... reveals that the method does not depend on the relationship between instances and labels."
Similarity metrics (quoted): "Spearman rank correlation with absolute value", "Spearman rank correlation without absolute value", "the structural similarity index (SSIM)", "the Pearson correlation of the histogram of gradients (HOGs)". Appendix calibrates the metrics against random-mask similarity levels.

### Ground truth used
**interventional** - controlled interventions on the model (weight randomization) and on the data-generating process (label permutation), with a known correct qualitative outcome (explanations MUST change). Not a positive ground truth of correct attributions; a falsification test. Additionally, closed-form analysis of a linear model and a 1-layer sum-pool conv net (where the true gradient is known analytically) supports the empirical findings - an architectural-style auxiliary argument, but the headline evaluation is the randomization intervention.

### Key results
- Gradient and GradCAM pass both tests; "Guided BackProp & Guided GradCAM are invariant to higher layer parameters; hence, fail."
- Gradient⊙Input and IG remain visually similar under randomization because "the input 'structure' dominates the gradient, especially for sparse inputs" (x ⊙ random-vector experiment).
- Rank correlation WITHOUT absolute value drops to ~0 immediately for most methods; ABS correlation and SSIM stay high - "visual perception versus ranking dichotomy," i.e., naive visual inspection cannot distinguish trained from randomized networks.
- Edge-detector comparison: "an edge detector produces outputs that are strikingly similar to the outputs of some saliency methods"; theory for the 1-layer sum-pool conv model shows the local ReLU activation pattern determines the gradient, explaining edge-like maps.

### Stated limitations / future work (near-verbatim, Conclusion + Sec. 5.1)
- "We primarily focused on invariance under model randomization, and label randomization. Many other transformations are worth investigating and can shed light on various methods we did and did not evaluate."
- "...we hope that our paper is a stepping stone towards a more rigorous evaluation of new explanation methods, rather than a verdict on existing methods."
- "Explanations that do not depend on model parameters or training data might still depend on the model architecture and thus provide some useful information about the prior incorporated in the model architecture." (i.e., passing/failing is task-relative)
- "Ultimately, quantifying human visual perception is still an active area of research." (on similarity metrics)

### My gap observations
- The checks are necessary-but-not-sufficient; a method can pass and still be unfaithful - the paper says this, but the field (incl. NTC papers citing it) often treats passing as certification.
- All experiments on natural/sparse IMAGE data; SSIM and HOG similarity are image-specific and have no obvious analogue for byte-matrix or tabular flow-feature inputs used in NTC - porting the sanity checks to NTC requires re-deriving appropriate similarity metrics (an open gap my project can fill).
- No threshold guidance: how much similarity decay counts as "pass" is left to visual reading of curves; no statistical decision procedure.
- Perturbation/occlusion explanation methods are barely covered (one appendix AlexNet figure); LIME/SHAP not tested even though they dominate NTC practice.
- Known post-hoc corrections in the literature (Guided BP partial input recovery, Nie et al.; the v3 erratum that GBP is not *entirely* invariant) show the test outcomes themselves needed sanity-checking.

---

## 3. Yet Another Traffic Classifier (YaTC)
**Zhao, Zhan, Deng, Wang, Wang, Gui, Xue - AAAI 2023.** Read: full text (8 pp).

### Task / data / model
- Task: encrypted traffic classification. Datasets: ISCXVPN2016, ISCXTor2016, USTC-TFC2016, CICIoT2022 (also pooled unlabeled for pre-training), Cross-Platform (transfer learning only).
- Input representation: MFR (multi-level flow representation) matrix - 5 packets/flow, per packet 2 header rows (80 B) + 6 payload rows (240 B), 40x40 bytes total; Ethernet headers removed, ports zeroed, IPs randomized (directions kept).
- Model: Traffic Transformer - ViT-style encoder (D=192, patch 2x2, N=400, 16 heads, 4 layers) with packet-level attention (attention restricted within packets, O(N^2/M)) then row-pooling + flow-level attention + column pooling; parameter sharing between the two encoders. MAE pre-training (mask ratio 0.9, global attention during pre-training), fine-tuning with cross-entropy.

### How explanation quality is EVALUATED
**none - the paper contains no explainability content at all.** No attention visualization, no attribution, no interpretability analysis, no explanation section. (Verified by grep: 'interpret', 'explain', 'visualiz', 'attention map' yield nothing beyond ablation-table caption text.) Evaluation is purely classification Accuracy/F1, ablations (Table 2), masking-ratio sweep, few-shot (10/50/100% labels), and transfer learning.

### Ground truth used
**none** (no explanations to evaluate).

### Key numbers
Accuracy/F1: ISCXVPN2016 98.07/98.04; ISCXTor2016 99.72/99.72; USTC-TFC2016 97.86/97.86; CICIoT2022 96.58/96.58 - vs ET-BERT (87.74/87.47 VPN; 65.38 Tor) and PERT (88.62 VPN; 80.22 Tor). Transfer to Cross-Platform: F1 82.35 with pre-training vs 69.93 without. Best mask ratio 90% (75% for USTC). Ablation: removing pre-training + packet attention drops Tor to 39.84 acc.

### Stated limitations / future work
**none stated.** The paper has no limitations paragraph and no future-work sentence; the conclusion only summarizes results. (The word "limitations" appears once, describing limitations of PRIOR methods in the abstract.)

### My gap observations
- A fully black-box SOTA claim: no analysis whatsoever of WHAT the model learned; given the MFR keeps two full header rows per packet (incl. TCP SeqNo/AckNo, timestamps, checksums), the later ShortcutCatcher/Pcap-Encoder line (same first author surname, different group - note: YaTC is SJTU; the critique papers are PoliTO) shows exactly these fields act as shortcut features. YaTC's near-perfect Tor result (99.72%) is a red flag never probed.
- Per the Pcap-Encoder reassessment (this batch, paper 6): YaTC used the SAME datasets for pre-training and downstream tasks; split policy "Unknown" in their Table 1; with per-flow split + frozen encoder YaTC's TLS-120 macro-F1 collapses to 9.6. YaTC also reports micro-F1 ("misleadingly," per Zhao et al.).
- For my project: YaTC is the canonical example of an NTC model published with zero explanation evaluation and zero stated limitations - useful as the baseline "explanation debt" exhibit, and as the standard subject model that XAI-for-NTC studies now dissect.

---

## 4. Sanity Checks for Saliency Metrics
**Tomsett, Harborne, Chakraborty, Gurram, Preece - AAAI 2020 (arXiv:1912.01451).** Read: full text (9 pp).

### Task / data / model
Meta-evaluation: evaluates the EVALUATION METRICS (saliency/fidelity metrics), not the saliency methods. Single model/task by design: CNN (3 conv blocks, no biases, 86% test acc) on CIFAR-10. Saliency methods scored: sensitivity analysis, gradient⊙input, deep Taylor decomposition, DeepSHAP, + Sobel edge-detection baseline. Metrics under test: AOPC-MoRF, AOPC-LeRF (Samek et al.), "faithfulness" F (Alvarez-Melis & Jaakkola: Pearson correlation between relevance and single-pixel deletion effect). ROAR excluded (cannot score individual maps; compute-prohibitive). Two perturbation variants: dataset-mean and uniform-random-RGB replacement, single pixels.

### How explanation-metric quality is EVALUATED
Psychometric reliability statistics applied to metric scores (the "sanity checks"):
- **Inter-rater reliability**: "The statistic commonly tested to answer this question is Krippendorf's α" over image-wise rankings of saliency methods.
- **Inter-method reliability**: mean pairwise "Spearman's ρ" between saliency-method score vectors across images.
- **Internal consistency reliability**: Spearman correlation between DIFFERENT metrics on the same method.
Explicit framing: "While a reliable metric is not necessarily valid, a valid metric must be reliable."

### Ground truth used
**none** - and stated as impossible: "A true test of saliency metric validity would require knowledge of the ground-truth saliency maps - which we do not have access to, and are what the saliency methods are trying to estimate." Crucial footnote 1: "In early experiments, we attempted to generate ground truth saliency maps by employing rules to generate images... However, we were still constrained to using very simple models... Ultimately the results of these experiments were of limited use as they were not indicative of the results we obtained... with more complex models and datasets." (An attempted-and-abandoned synthetic/architectural ground-truth construction.)

### Key results
- All Krippendorff α values ≪ 0.65 reliability threshold; max 0.48 (AOPC-MoRF, L=100, mean perturbation, edge detector included). "the metrics will not produce consistent rankings of saliency maps when applied to new test images."
- Method rankings REVERSE between AOPC-MoRF and AOPC-LeRF; F vs AOPC-LeRF slightly anti-correlated (−0.09 to −0.22); AOPC-MoRF vs LeRF correlation ranges 0.11-0.77 depending on method.
- Perturbation choice (mean vs random RGB) changes scores, distributions AND method rankings; inter-method ρ from 0.13 (F) to 0.67 (AOPC-MoRF).
- Mechanistic diagnoses: LeRF favors edge-detector-like methods (mean-perturbing along an edge only changes contrast); negative relevance on high-confidence inputs poisons LeRF for signed methods; all metric scores are image-class dependent.

### Stated limitations / future work (near-verbatim)
- "our results and conclusions are not generally applicable statements about the consistency of saliency metrics - they are an illustration that such metrics can produce unreliable and inconsistent results." (single model/task)
- "it is very hard to disentangle the sources of variance and inconsistency in the metric scores, as model, saliency method and metric are tightly coupled."
- Perturbation "ha[s] the potential to move the image off the data manifold learned by the NN, thus reducing the validity of any measurements... it is not currently possible to know what method will adhere to this requirement a priori."
- "We leave a fuller analysis along these lines [per-class metric behavior] as future work."
- Recommendations: compare new metrics to old ones quantitatively; analyze implementation variants; analyze how metrics "might be 'tricked'"; understand variance sources; "developers of saliency methods should not rely on a single metric... they should employ several metrics."

### My gap observations
- Directly undermines the deletion/insertion-style "fidelity" evaluations that dominate XAI-for-NTC papers: if AOPC/faithfulness are unreliable on CIFAR-10, their uncritical transplantation to traffic bytes/flow features (where the off-manifold problem is arguably worse - perturbed packets may be protocol-invalid) is even shakier. Nobody has run these reliability sanity checks on NTC saliency metrics - an immediately actionable gap.
- Footnote-1's failed ground-truth attempt is, to my knowledge, the only recorded attempt in this batch's lineage to construct explanation ground truth by construction - it failed for simple-model reasons; a traffic-domain design (where protocol grammar gives objective feature semantics) could plausibly succeed where rule-generated images failed. Strong motivation for my project's ground-truth angle.
- Single CNN, no ViT/transformer; unknown whether reliability improves with architecture scale; single-pixel perturbation choice is itself one of the implementation choices the paper criticizes.

---

## 5. ShortcutCatcher: Making Traffic Classification Reliable
**Zhao, Boffa, Vassio, Mellia (PoliTO) - Proc. ACM Netw. (CoNEXT), vol. 4, art. 23, June 2026. DOI 10.1145/3808671, CC-BY.** Read: full text (15 pp, ACM published version via reader proxy).

### Task / data / model
- Task: automated detection AND mitigation of shortcut features in encrypted traffic classification, using xAI in a closed loop. Datasets (Table 1): VPN [ISCX-VPN, 6 classes, flow-level, tiny: 840 train flows], App-Time (27 Android apps, flow), App-Ver (25 apps, flow), TLS120 (packet classification, 120 TLS websites, 230k train packets; cleaned traces from their SIGCOMM'25 paper). Features: ALL IP/TCP/UDP header fields via Scapy (Table 3), IP octets as 4 separate features, first 5 packets for flow tasks. Deliberately retains known-bad fields: "We intentionally retain all header fields, including those previously reported as potential shortcuts."
- Models: Random Forest (main text), 2-layer MLP and TabICL tabular foundation model (appendix); AutoGluon v1.4 for training/hyperparameters; k=5 candidate features per iteration; metric optimized = accuracy (reported: macro F1).
- Splits/scenarios: main time split into D (train) / V (verification, ~10x smaller) / C (check); D internally split stratified (S0) or by time (S1); S2 additionally applies forge() to V and C - random consistent IP replacement from 128.66.0.0/16, random TCP-timestamp offsets, checksums recomputed - emulating deployment in a different network at a later time.

### XAI method
Model-coupled global feature-importance explainers used *instrumentally*: "Explainers are typically coupled to the model type (e.g., Feature Impurity [2] for Random Forests; Permutation Methods [4] for Neural Networks). However, any combination that enables the estimation of the model's most important features is suitable at this stage." Loop: Train → Verify → Explain → Select top-k → Mitigate (for each of top-k: remove feature, retrain, evaluate on V; permanently remove the best-gain feature) → repeat; deploy BestModel, final test on C.

### How explanation quality is EVALUATED
**No direct evaluation of explanation quality.** The xAI output is only a candidate-ranking heuristic; validation of "this feature is a shortcut" is exclusively FUNCTIONAL/downstream: leave-one-feature-out retraining and the resulting macro-F1 gain on the verification set ("Features whose removal improves cross-scenario accuracy are flagged as shortcuts"), with final honesty check on C. System-level metrics: F1_0(D), F1_0(C), F1*(C), relative gain. No fidelity, plausibility, stability, or human assessment of the explainer itself; explainer choice is never compared or ablated.

### Ground truth used
**synthetic (partial, by construction) + interventional loop.** The forge() mechanism plants known-invalid features in V/C (forged IPs and TCP timestamps cannot carry class signal), so for the spatio-temporal subset the "shortcut ground truth" is known by construction, and ShortcutCatcher's discoveries can be checked against it (it does remove tcpTS/ipSrc/ipDst first - Fig. 3). The confirmation mechanism for each individual flagged feature is interventional (remove → retrain → measure). Authors flag the circularity themselves (see limitations). One genuinely novel discovery validated by root-cause reasoning rather than construction: TCP-checksum offloading - "authors collected data on clients where TCP checksum offloading was enabled: all packets within a flow share the same checksum. To the model, these checksums act as proxies for flow IDs" - a previously unreported collection artifact in the App-Time/App-Ver datasets.

### Key numbers
- RF Table 2: VPN S0: F1_0(D)=88.0 → F1_0(C)=11.0 (−87.5%) → F1*(C)=43.7 (+297%). S2 drops of 75-85% across all datasets; TLS-120 S2: 9.5 → 20.5 (+115%); App-Time S2: 17.3 → 26.5 (+53.2%); App-Ver S2: 16.6 → 28.5 (+71.7%).
- MLP S2: TLS-120 2.6 → 15.8 (+507.7%); TabICL: VPN 4.9 → 26.5 (+440.8%); "TabICL complexity prevents it from converging on TLS-120, questioning the usage of foundational models."
- Ablations: |V| of 100-250 samples (4-10/class) suffices but with large seed variance (F1* 31.2±6.6 at |V|=100); k=1 fails (forced removal of possibly-good top feature), k∈{3,5,7} good; full run to feature exhaustion: 86 rounds, ≈2.5 h, Mitigate phase ≈5x the Train cost.
- Interpretive claim: post-mitigation F1*(C)=26.5 vs in-distribution 66.5 on App-Time "illustrates the true difficulty of the task"; surviving feature "the IP length of the fourth packet of each flow" is semantically meaningful.

### Stated limitations / future work (near-verbatim, Sec. 6 "Limitations")
- **Dependence on the verification set**: "Its effectiveness depends on how well V reflects the target deployment scenario... A key risk is the potential overfitting to a specific V, yielding performance gains on that dataset without guaranteeing improved generalisation. Furthermore, if V still contains some valid features which may be shortcuts in general, these would not be removed." Proposed extensions: "a nested validation setup," "multiple verification sets, each referring to different possible deployments."
- **Circularity of forge()**: "the verification set is synthetically generated through the forge() mechanism... While this enables controlled experiments, it focuses on well-known artefacts and may introduce some circularity, as it assumes prior knowledge of potential shortcut features... More broadly, the lack of datasets with natural spatio-temporal variation remains a limitation of the field."
- **Greedy feature removal**: "this approach cannot capture interactions between features, where combinations jointly act as shortcuts even if individual features appear benign. Consequently, higher-order dependencies may go undetected. Extending the framework... through group-wise removal or Shapley-based importance methods - is an important direction for future work."
- **Mitigation strategy**: "We experimented with other options: injecting noise and permuting features... Empirically, the feature removal strategy performed the best. Refined strategies based on partial weighting or regularisation could provide a better trade-off and warrant further investigation."

### My gap observations
- The xAI block is replaceable by ANY ranking heuristic; the paper provides no evidence the explainer adds value over, e.g., random top-k candidates or mutual-information ranking - no ablation on explainer choice, so nothing is learned about explainer faithfulness in NTC. (k=1 vs k>1 ablation even shows the top-1 "most important" feature is often NOT the shortcut - indirect evidence the impurity ranking is unreliable, unremarked by authors.)
- Impurity importance is biased toward high-cardinality features (checksums, seq numbers, IP octets) - here the bias happens to align with real shortcuts, which may inflate the apparent usefulness of the explainer; permutation importance for NNs has known correlated-feature pathologies. Never discussed.
- Works only on tabular header-field schemas; the method cannot audit raw-byte/representation-learning models (ET-BERT/YaTC class) where "features" are not enumerable - leaving the models with the worst shortcut record un-auditable by this framework.
- Each removal decision is a single retrain comparison; no significance testing / variance estimate per decision (seed variance shown only for |V| ablation).
- C is in-distribution w.r.t. V, so "generalisation" is demonstrated only for the specific forged shift; no third natural-shift dataset.
- No human validation that flagged features are semantically spurious beyond the authors' own protocol reasoning (which is, in fairness, expert analysis - but n=1 group, not blinded).

---

## 6. The Sweet Danger of Sugar: Debunking Representation Learning for Encrypted Traffic Classification (Pcap-Encoder)
**Zhao, Dettori, Boffa, Vassio, Mellia (PoliTO) - SIGCOMM 2025 (arXiv:2507.16438v1).** Read: full text (15 pp incl. appendices).

### Task / data / model
- Critical reassessment of representation-learning NTC models: ET-BERT, YaTC, NetMamba, TrafficFormer, netFound (pre-trained checkpoints from original repos), vs shallow baselines (RF, XGBoost, LightGBM, MLP on expert-selected Scapy header fields, AutoGluon-tuned) and their own Pcap-Encoder.
- Benchmark: 6 tasks on 3 datasets - ISCX-VPN (VPN-binary/2, VPN-service/6, VPN-app/16), USTC-TFC (binary/2, app/20), CSTNET-TLS1.3 (TLS-120). Standardized cleaning (Tshark filter superset; ISCX/USTC contain 5%/10% spurious packets), NO minimum-size/class-support filters, per-flow vs per-packet split comparison, stratified test sets, balanced training via undersampling, 3-fold CV, accuracy + macro F1.
- Pcap-Encoder: T5-base; Phase 1 packet autoencoder (T5-AE, mean-pooling bottleneck; MAWI + UNSW-NB15 + campus trace, ~1 GB / 500k packets, IPs/TTLs randomized); Phase 2 Q&A fine-tuning on 8 header-semantics question types x 50k instances ("What is the destination IP address of the packet?", "Is the packet's IP checksum correct?"; 98.2% Q&A test accuracy); payload questions avoided by design. 2-layer MLP head; majority vote over first 5 packets for flow tasks.

### XAI usage and how explanations are treated
Not an XAI-methods paper, but interpretability artifacts carry the argument:
1. **RF impurity feature importance** (Fig. 5, per-packet split, TLS-120): with IPs, top features are IP-address octets (acc 98.9%); with IPs removed, TCP AckNo/SeqNo, IP checksum, IP ID dominate (acc still 92.6%) - visualizing explicit and implicit flow-ID shortcuts.
2. **5-NN purity of embeddings** (Fig. 4): frozen ET-BERT on TLS-120 - 71.25% of packets have ZERO same-class 5-NN neighbors; after unfrozen fine-tuning 97.06% have 5/5. "The original embeddings lack meaningful information."
3. **Interventions**: test-time randomization of SeqNo/AckNo/TCP-timestamps collapses unfrozen per-packet ET-BERT from 97.4 → 19.5 acc; removing them from train+test: 52.2; random-initialized (no pre-training) ET-BERT: 97.1 vs 97.4 pretrained - "the ET-BERT pre-training is mostly useless." Pcap-Encoder ablation: w/o IP 13.0 F1 (TLS-120), w/o header 1.5, w/o payload 63.6 vs base 63.7 (payload contributes nothing, by design).

### How explanation quality is EVALUATED
**none, formally.** No explanation-quality metric is ever computed. The RF feature importances are displayed and then their implied claims are corroborated by direct interventions on the named fields (randomize/remove → performance collapse) - i.e., claims derived from explanations are validated interventionally, but the explanation method itself (impurity importance) is never assessed for faithfulness, and no attribution analysis is performed on the deep models at all (their shortcut reliance is inferred purely from input ablations and embedding k-NN purity).

### Ground truth used
**interventional** - the shortcut hypotheses raised by feature importances are confirmed by controlled field randomization/removal experiments with predicted outcomes (huge drops). No ground-truth attributions.

### Key numbers
- Headline (Fig. 1 / Tables 3-5), TLS-120 packet task: per-flow split + frozen encoders: ET-BERT 10.9 AC / 6.7 F1; YaTC 15.5/9.6; NetMamba 8.8/4.5; TrafficFormer 29.7/24.0; netFound 1.9/0.5; Pcap-Encoder 71.0/63.7. Per-flow unfrozen: best non-Pcap is TrafficFormer 43.7 AC. Per-packet + unfrozen (the literature's original setting): ET-BERT 97.4, YaTC 98.2, NetMamba 97.4 - "up to 80% lower [under correct testing] than that reported in their respective papers."
- Flow-level (Table 9, per-flow): frozen all poor (15.6-46.3 AC); unfrozen netFound best on TLS-120 (90.8 AC); Pcap-Encoder frozen majority-vote 71.3 AC.
- Shallow baselines (Table 8, per-flow, macro F1): LightGBM 82.4 (TLS-120) and 82.6 (VPN-app) - beating Pcap-Encoder (63.7/71.0); even without IPs, shallow ≥ Pcap-Encoder on VPN-app.
- Efficiency (Fig. 6): representation models 2-500x RF training time; inference up to 2048x slower (netFound); Pcap-Encoder second slowest.
- Recommended practices (quoted): "Control for shortcut learning… Verify data integrity… Stress representation learning capabilities - i.e., freeze the encoder during downstream training… Consider cost-benefit trade-offs."

### Stated limitations / future work (scattered; no dedicated section)
- On their own model: "Pcap-Encoder appears to be the only model that provides an instrumental representation for traffic classification. Yet, its complexity questions its applicability in practical settings." / "its complexity and performance, on par with shallow models, question its practicality for current problems." / second-slowest at training and inference.
- Scope of splits: "Notice that more advanced splits are possible: per-session, per-client, per-location, per-time split, etc... Here, we limit our analysis to the basic per-packet and per-flow split."
- Label semantics: "we consider all packets and flows to belong to the class the trace belongs to... Even if questionable, this is the same formulation previous works used."
- ET-BERT TLS-120 discrepancy hedged: SNI presence in the private version "the authors do not confirm"; their balanced few-shot training differs from the original.
- "Appendices are supporting material that has not been peer-reviewed."

### My gap observations
- The load-bearing explanation tool (RF impurity importance) is exactly the estimator known to be biased toward high-cardinality features - SeqNo/AckNo/checksums/IP octets are maximal-cardinality, so Fig. 5 would over-rank them even absent shortcut learning; the paper's conclusions survive only because of the interventional follow-ups, yet the XAI step is presented uncritically. A reliability-aware XAI-for-NTC methodology would make this chain explicit.
- The deep models are never explained directly (no attention/attribution analysis of ET-BERT/YaTC), so *which byte positions* the transformers exploit remains unshown - inferred only via input ablations. Post-hoc attribution on these models, validated against the paper's interventional findings, is an open, well-posed benchmark: the interventions provide a rare *known-answer* setting (implicit flow-ID bytes) against which NTC saliency methods could be scored. This is arguably the closest thing to explanation ground truth available in NTC today, and nobody has used it that way.
- 5-NN purity is introduced ad hoc as a representation probe without connection to the (large) representation-evaluation literature; no baseline purity value (chance level for 120 classes) is stated.
- Pcap-Encoder's own decision process is only coarsely ablated (w/o IP / header / payload); no field-level attribution, so its claimed "semantic" superiority is not itself explained.

---

# Batch-level synthesis: the evaluation-gap picture

1. **No paper in this batch evaluates explanation quality against a positive ground truth.** CADE (the only one proposing an NTC-relevant explanation method) evaluates with a self-referential perturbation proxy plus two anecdotal expert-report case studies; ShortcutCatcher and Pcap-Encoder never evaluate their explainers at all - they only use them as heuristics whose *downstream consequences* are checked; YaTC contains zero interpretability content; the two Sanity-Checks papers formalize why this is a problem (randomization tests are necessary-only; the metrics themselves are unreliable; Tomsett et al. even tried and abandoned a constructed ground truth).
2. **The proxy metrics the NTC field imports are exactly the ones shown unreliable.** Deletion/perturbation fidelity (CADE's d', AOPC-style curves) inherits the off-manifold problem, which is worse for traffic (perturbed packets can violate protocol grammar), and Tomsett et al. show such metrics disagree with each other and rank methods inconsistently image-by-image. No one has run reliability sanity checks (Krippendorff-alpha-style) or randomization sanity checks on NTC explainers/metrics.
3. **A latent ground-truth opportunity exists in this exact literature.** The PoliTO shortcut papers create settings where the true "reason" for classification is KNOWN by construction or by intervention (forged IPs/timestamps, implicit flow-ID bytes, checksum-offloading artifacts): a model trained in a leaky per-packet split provably relies on identifiable fields. These constitute ready-made, domain-realistic known-answer tests for NTC attribution methods - but both papers use xAI only instrumentally and never turn the construction around to score explainers. That inversion (planted-shortcut benchmarks as explanation ground truth for traffic models) is the clearest unclaimed contribution surfaced by this batch.
4. **Explainer choice is unexamined in NTC pipelines.** ShortcutCatcher hard-codes impurity/permutation importance; Pcap-Encoder uses impurity importance; both estimators have documented biases (cardinality, feature correlation) that happen to align with traffic shortcut fields - nobody measures whether the explainer, rather than the loop around it, deserves the credit.
5. **Stated-limitations asymmetry**: methodology-critique papers (Sanity x2, ShortcutCatcher, Pcap-Encoder) carry candid limitation sections; SOTA classifier papers (YaTC) state none. CADE's limitations concern detection, not explanation - its explanation-evaluation weaknesses go unstated.

Temp full-text files retained at `corpus\notes\tmp-{cade,sanity-maps,yatc,sanity-metrics,shortcutcatcher,pcap-encoder}.txt`.
