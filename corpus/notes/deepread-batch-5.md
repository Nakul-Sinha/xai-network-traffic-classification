# Deep-Read Notes - Batch 5

Reader focus: (1) how explanation quality is EVALUATED, (2) LIMITATIONS / FUTURE WORK, with strict ground-truth typing for the journal paper on XAI for network traffic classification.
Date: 2026-08-22. All six papers read at full-text depth.

---

## 1. GNNExplainer: Generating Explanations for Graph Neural Networks (Ying, Bourgeois, You, Zitnik, Leskovec - NeurIPS 2019, arXiv:1903.03894v4)

**Read depth:** full text (main paper + appendices A-C).

**What it is.** First general, model-agnostic explainer for any message-passing GNN (MSG/AGG/UPDATE formulation). Given a trained GNN and a prediction, it learns (a) a continuous edge mask over the node's computation graph (mean-field variational approximation of a subgraph distribution) and (b) a binary node-feature mask, jointly optimized to maximize mutual information MI(Y,(G_S, X_S)) = H(Y) − H(Y | G_S, X_S), with entropy/size regularizers to force discrete, compact masks. Multi-instance explanations via graph alignment (relaxed alignment matrix, Eq. 8) + median-based prototype.

**Tasks / datasets.** Node classification on 4 synthetic datasets with planted motifs: BA-SHAPES (BA graph + 80 5-node "house" motifs, 4 structural-role classes), BA-COMMUNITY (2 BA-SHAPES + Gaussian node features, 8 classes), TREE-CYCLES (binary tree + 80 6-node cycles), TREE-GRID (3×3 grids). Graph classification on MUTAG (4,337 molecules, mutagenicity) and REDDIT-BINARY (2,000 thread graphs, QA vs discussion). GNNs trained to ≥85% (graph) / ≥95% (node) accuracy; 80/10/10 splits.

**XAI evaluation (exact).** "Explanation accuracy": on the synthetic datasets, "we have ground-truth explanations ... we formalize the explanation problem as a binary classification task, where edges in the ground-truth explanation are treated as labels and importance weights given by explainability method are viewed as prediction scores." Baselines: GRAD (saliency w.r.t. adjacency + features) and ATT (GAT attention weights averaged over layers). Real-world datasets are evaluated only qualitatively, by visual agreement with domain knowledge (NO2/NH2 groups and carbon rings known mutagenic from Debnath et al. 1991; QA-thread star patterns).

**Key numbers.** Explanation accuracy - BA-Shapes: GNNExplainer 0.925 / Grad 0.882 / Att 0.815; BA-Community: 0.836 / 0.750 / 0.739; Tree-Cycles: 0.948 / 0.905 / 0.824; Tree-Grid: 0.875 / 0.667 / 0.612. "Outperforms alternative approaches by 17.1% on average," "up to 43.0% higher accuracy on the hardest TREE-GRID dataset."

**Ground truth used:** SYNTHETIC - datasets constructed so labels are determined by planted motifs known by construction; GT edge sets derive from the construction. (Real-world part: informal appeal to expert chemistry knowledge, qualitative only, no quantitative human_expert protocol.)

**Stated limitations / future work (near-verbatim).**
- Optimization: "due to the complexity of neural networks, the convexity assumption does not hold. However, experimentally, we found that minimizing this objective with regularization often leads to a local minimum corresponding to high-quality explanations."
- Multi-instance (App. A): "The problem of multi-instance explanations ... is challenging ... More research in this area is necessary to design efficient Multi-instance explanation methods. The main challenges in practice is mainly due to the difficulty to perform graph alignment under noise and variances of node neighborhood structures ... closely related to finding the maximum common subgraphs ... which is an NP-hard problem."
- No dedicated limitations section in the conclusion.

**My gap observations (not stated by authors).**
- KM (subgraph size budget) is "set ... to be the size of ground truth" on synthetic data - the evaluated method receives the GT explanation size as a hyperparameter, and all methods are thresholded to at least K_M edges; this leaks GT into the benchmark and flatters precision-style accuracy.
- The protocol assumes the trained GNN actually uses the planted motif; the model's true reasoning is never verified independently (label-generating process ≠ model process). Later critiques (e.g., Faber et al. 2021) formalize this "GT-alignment" pitfall.
- Real-world evaluation is anecdotal (curated figures); no quantitative faithfulness metric (no deletion/insertion, no stability) is reported anywhere.
- No runtime/stability analysis; per-instance gradient-descent optimization (100-300 epochs each) is a real cost when explaining per-flow GNN NTC/NIDS decisions at scale.
- NTC relevance: GNNExplainer is the default explainer reused by graph-based traffic/IDS papers, but its validation regime (planted motifs on BA/tree graphs) has no analogue in traffic graphs; nobody has built the traffic-graph equivalent of BA-SHAPES - an opportunity my project can exploit (synthetic traffic with motif-defined ground truth).

---

## 2. Attention is not Explanation (Jain & Wallace - NAACL-HLT 2019, arXiv:1902.10186v3)

**Read depth:** full text (main + appendices).

**What it is.** Empirical study of whether attention weights in BiLSTM-with-attention models are faithful explanations. Two properties tested: (i) attention should correlate with feature-importance measures; (ii) counterfactual attention configurations should change predictions.

**Models / tasks / datasets.** BiLSTM encoder + additive (tanh) or scaled dot-product attention; contrast encoders: feed-forward "average" (projected embeddings) and CNN. Binary text classification (SST, IMDB, ADR Tweets, 20 Newsgroups hockey/baseball, AG News world/business, MIMIC-III Diabetes, MIMIC-III Anemia), QA (CNN news cloze, bAbI 1/2/3), NLI (SNLI).

**XAI evaluation (exact metrics).**
- Kendall-τ correlation between attention and (a) gradient-based importance τ_g (gradients detached at the attention module) and (b) leave-one-out output change τ_loo (TVD of outputs on token removal).
- Counterfactual: random permutation of attention weights → median output change ∆ŷ_med (TVD over 100 permutations).
- Adversarial attention: optimize k attention distributions maximizing JSD from the observed α (and from each other) subject to TVD[ŷ(x,α_adv), ŷ(x,α̂)] ≤ ε (ε=0.01 classification, 0.05 QA); metric "ε-max JSD" (upper bound 0.69).
- No ground truth anywhere; explicitly: "We do not intend to imply that such alternative measures are necessarily ideal or that they should be considered 'ground truth'."

**Key numbers.** BiLSTM τ_g typically 0.33-0.47 (20News as low as 0.08-0.13); "average" encoder τ_g 0.65-0.81; LOO-vs-gradient correlations exceed attention-vs-either by ~0.2-0.25 τ on average. Adversarial ε-max JSD masses near the 0.69 bound on most datasets; intro example: prediction 0.01 unchanged under a disjoint attention heatmap, τ_g = 0.29, permutation median output diff 0.006. Diabetes-positive class is the standing exception (few high-precision tokens; perturbing attention does change output).

**Ground truth used:** NONE. All evaluations are proxy-consistency (correlation with other importance estimators) and model-internal interventions; the paper itself disclaims GT status for the reference measures.

**Stated limitations (Section 6, near-verbatim).**
- "We do not intend to imply that such alternative measures are necessarily ideal or that they should be considered 'ground truth'. ... exactly how strong such correlations 'should' be in order to establish reliability as explanation is an admittedly subjective question."
- "irrelevant features may be contributing noise to the Kendall τ measure, thus depressing this metric artificially. ... it remains a possibility that agreement is strong between attention weights and feature importance scores for the top-k features only (the trouble would be defining this k...)."
- "we have only considered a handful of attention variants ... particularly focused on RNNs (here, BiLSTMs) ... Alternative attention specifications may yield different conclusions."
- "the counterfactual attention experiments demonstrate the existence of alternative heatmaps that yield equivalent predictions ... However, the adversarial weights themselves may be scored as unlikely under the attention module parameters. Furthermore, it may be that multiple plausible explanations for a particular disposition exist."
- "we have limited our evaluation to tasks with unstructured output spaces, i.e., we have not considered seq2seq tasks, which we leave for future work."

**My gap observations.**
- The adversarial search freezes every parameter except attention (per-instance, non-learned adversary); Wiegreffe & Pinter (2019) later show model-consistent (trained) adversaries have far less room - the existence-vs-learnability distinction the paper only half-acknowledges.
- Detaching the gradient at the attention layer is a nonstandard design choice that changes what τ_g measures; correlations are proxy-vs-proxy with no independent referent - the study demonstrates disagreement, not which signal (if any) is right.
- All conclusions come from single-sequence NLP classification; transformer-era NTC models (ET-BERT-style, packet-sequence attention classifiers) routinely display attention heatmaps over bytes/packets as explanations without running any of these consistency tests - the paper's protocol transfers to NTC almost verbatim and nobody has run it there.
- Positive control insight for my project: Diabetes shows attention behaves when few high-precision features exist - traffic tasks with signature-like fields (e.g., TLS SNI) may sit in this regime, making "attention is/isn't explanation" task-dependent in NTC too.

---

## 3. Kitsune: An Ensemble of Autoencoders for Online Network Intrusion Detection (Mirsky, Doitshman, Elovici, Shabtai - NDSS 2018, arXiv:1802.09089v2)

**Read depth:** full text.

**What it is.** Plug-and-play online, unsupervised NIDS for resource-constrained devices. Pipeline: Packet Capturer/Parser → Feature Extractor (damped incremental statistics) → Feature Mapper (incremental agglomerative hierarchical clustering of the feature space by correlation distance; clusters capped at m features) → Anomaly Detector KitNET = ensemble of k three-layer autoencoders (one per feature cluster; compression ratio β=3/4) whose per-AE RMSEs feed an output autoencoder acting as a "non-linear voting mechanism"; final anomaly score is the output AE's RMSE; alert if s ≥ φβ. Single-pass SGD (max_iter=1), ≤1 instance in memory; execution complexity O(km² + k²).

**Input representation.** 115 features per packet: 23 damped incremental statistics (bandwidth µ/σ of outbound traffic; 2D magnitude/radius/approx-covariance/correlation of in+out; packet rate w; jitter stats) over aggregations SrcMAC-IP, SrcIP, Channel (src↔dst IP), Socket, each in 5 damped time windows (100 ms, 500 ms, 1.5 s, 10 s, 1 min; λ = 5,3,1,0.1,0.01). Runtime benchmarks used n=198.

**Datasets.** Self-collected: IP-camera video-surveillance network (2×4 HD cameras, PoE, site-to-site VPN) with 8 attacks - OS Scan (Nmap), Fuzzing (SFuzz), Video Injection, ARP MitM (Ettercap), Active Wiretap (RPi bridge), SSDP Flood, SYN DoS (Hping3), SSL Renegotiation (THC); plus a 9-IoT-device Wi-Fi network with a real Mirai infection. 0.76M-6.08M packets per trace; train on first 1M packets, execute on the rest. (These captures became the widely reused "Kitsune/Mirai datasets".)

**Evaluation (of detection, not explanation).** TPR/FNR at FPR=0 and FPR=0.001, AUC, EER vs Suricata (13,465 ET rules), Isolation Forest, GMM (offline "upper bounds"), incremental GMM, pcStream2. Kitsune ≈ offline detectors, better EER than GMM on ARP/Fuzzing/Mirai/SSL-R/SYN/wiretap; e.g., AUC ≈ 0.99997 (OS Scan, m=1), wiretap detected where GMM fails. Runtime: Raspberry PI 3B single core ~1,000 pps (single AE) → ~5,400 pps at k=35 (×5); PC 7,500 → 37,300 pps.

**XAI evaluation:** NONE. No explanations are produced, displayed, or evaluated; interpretability is never mentioned as a goal. (The word "explain" appears only as "we will now explain how...".)

**Ground truth used (for explanations):** none - not applicable.

**Stated limitations / future work (Section VI, near-verbatim).**
- Poisoning/evasion: "When first installed, Kitsune assumes that all traffic is benign while in train-mode. Therefore, a preexisting adversary may be able to evade Kitsune's detection. ... a user should be aware of this risk when installing Kitsune on a potentially compromised network. As a future work, it would be interesting to find a mechanism which can safely filter out potentially contaminated instances during the training process."
- FE memory-DoS: "an attacker sends many packets with random IP addresses ... the FE will creates many incremental statistics which eventually consume the device's memory ... it is highly recommended that the user limit the number of incremental statistics which can be stored in memory."
- Threshold choice φ left to the user ("select φ probabilistically ... A user of KitNET should decide"); parallelization over cores left as future work.

**My gap observations.**
- Alerts are bare RMSE scores: an analyst gets no indication of which channel/feature/subspace fired. Yet the architecture is latently self-explaining - the FM's correlation clusters give each ensemble AE a semantically coherent feature subspace, and per-AE RMSEs are a ready-made attribution vector; neither the paper nor most follow-ons exploit or evaluate this (instead, later XAI-NIDS work bolts SHAP onto Kitsune post hoc).
- The Kitsune/Mirai captures became a de facto benchmark for XAI-NIDS papers, but ship with no expert feature-relevance annotation, so explanation claims on them are unverifiable; ironically the attacks are simple enough (SYN flood → packet-rate/jitter stats) that a defensible expert GT could be constructed - a concrete dataset-building opportunity.
- ROC/EER evaluation sidesteps the deployed threshold procedure (φβ from train max), so operational FPR is unknown; single network per attack, temporal split on the same capture - cross-network generalization untested.
- The 115 features are correlated by construction (same statistic, 5 decay windows), which is exactly the regime where SHAP/LIME independence assumptions misbehave - relevant caveat for every later paper explaining Kitsune-featurized models.

---

## 4. Investigating Sanity Checks for Saliency Maps with Image and Text Classification (Kokhlikyan, Miglani, Alsallakh, Martin, Reblitz-Richardson - Facebook AI / Captum team; ICLR 2021 Workshop on Responsible AI, arXiv:2106.07475)

**Read depth:** full text (main + appendices A/B).

**What it is.** Extends Adebayo et al. (2018) sanity checks (cascading parameter randomization; data/label randomization) from images to text, and dissects the role of the input multiplier (x − x0) in "global" variants of gradient methods, plus the effect of NN smoothness on evaluation metrics.

**Models / tasks.** Inception (image classification; MNIST for label-randomization test) and BERT fine-tuned on SST2 (sentiment). Methods analyzed: Integrated Gradients (local = no multiplier vs global = with (x−x0) multiplier), IG+SmoothGrad, InputXGradient, DeepLift, DeepLift SHAP, Gradient SHAP, Guided BackProp, Guided GradCAM.

**XAI evaluation (exact metrics).**
- Sanity checks: cascading layer-wise (Xavier) parameter randomization top→bottom; data (label) randomization.
- Similarity of explanations pre/post randomization: SSIM (image), Cosine Similarity (text, L2-normalized token attributions), Spearman rank correlation, Euclidean distance; boxplots over 10 randomization trials per layer.
- Infidelity (Yeh et al. 2019; generalization of the completeness axiom) and max-sensitivity; perturbations ~ N(0, 0.03) for infidelity/local IG, L∞ ball radius 0.02 with 5 samples for max-sensitivity. "Lower scores for both metrics indicate more trustworthy explanations."
- Metrics averaged across only ten input samples.

**Key findings / numbers.** Global IG on images fails parameter randomization (input multiplier "carries input's structural patterns"; SSIM for global ≈ 2× local); on text both variants ARE sensitive (attributions summed over embedding dims → multipliers cancel; CosSim medians ≈ 0 after randomizing even one layer). Inception infidelity explodes under randomization (global: 2.84 → 1.27e7 at Mixed 6); BERT infidelity stays ~1e-17 across randomization. Replacing ReLU→Softplus and MaxPool→LogSumExp "drops infidelity significantly" - smoothness improves explanation reliability under the infidelity metric.

**Ground truth used:** NONE. Sanity checks are necessary-condition falsification tests; infidelity/max-sensitivity are perturbation proxies. No human, synthetic, or architectural GT.

**Stated limitations / future work (near-verbatim).** Sparse (workshop paper, no limitations section): "Note that this behaviour depends on the randomization technique. In this experiment, we used Xavier random initialization"; "As a future direction it would be interesting to explore feature pruning tasks and the effects of feature and neuron correlations and interactions on saliency maps."

**My gap observations.**
- n=10 samples, no statistical tests - the quantitative claims are fragile; the paper itself only argues distributions "are similar" to the single-sample case.
- Perturbation scales (σ=0.03, r=0.02) are unjustified; infidelity is known to be sensitive to the perturbation distribution and baseline choice, so the ReLU→Softplus "more trustworthy" conclusion is metric-relative.
- Passing sanity checks remains only necessary, never sufficient - the paper never connects any metric to explanation correctness.
- Central message for my project: sanity-check conclusions DO NOT transfer across modalities ("the conclusions made for image do not directly transfer to text") because of representation structure (2D spatial patterns vs summed embedding dims). NTC sits in a third regime - byte "images", packet-sequence time series, tabular flow features - and the analogous sanity-check suite has never been run on traffic models; NTC papers that convert traffic to 28×28 byte images inherit the CV-style input-multiplier pathology unexamined.

---

## 5. A Survey on Explainable Artificial Intelligence for Internet Traffic Classification and Prediction, and Intrusion Detection (Nascita, Aceto, Ciuonzo, Montieri, Persico, Pescapé - IEEE Communications Surveys & Tutorials, vol. 27 no. 5, pp. 3165-3198; DOI 10.1109/COMST.2024.3504955; CC-BY)

**Read depth:** full text (IEEE stampPDF, 34 pp).

**What it is.** Systematic survey (Wohlin snowballing from 28 seed papers found via Google Scholar query `("explainable AI" OR "interpretable AI") AND ("network traffic analysis")` → 107 papers) of XAI for NTA tasks: legit Traffic Classification (TC), Intrusion Detection (ID; split Misuse Detection vs Anomaly Detection), Attack Classification (AC), fine-grained Traffic Prediction (TP), + other (QoE/SLA/SDN). Adopts Nauta et al. (2022) definition of explanation and its 12-property quality framework.

**Structure highlights.**
- Taxonomy (III-A): scope local/global; stage pre-model / post-hoc / intrinsic; model-specific vs agnostic; explanation types visualization / input importance / example-based (incl. counterfactual CEM, ProtoDash, CADE, COIN).
- Metrics (III-B): 12 Nauta properties in 3 dimensions (content, presentation, user); "the most considered explanation-quality properties are Coherence ..., Compactness ..., Completeness, and Correctness" in general XAI, but "in NTA it is later shown that instead Continuity ... is the most considered property." Coherence is defined as "the alignment of the explanation with domain knowledge (if a ground truth is available), or with other established XAI methods (used as gold standard)."
- Reliability (III-C): calibration (ECE/MCE/class-wise, reliability diagrams; Focal Loss, Label Smoothing, Dirichlet methods) treated as complementary to explanation; for TP, conformal prediction et al.
- Usage stats (VI): SHAP is by far the most used technique (~46 of 107 works; DeepSHAP/TreeSHAP/KernelSHAP variants), LIME second (~22), often both together (~16); LRP, IG, saliency, Grad-CAM, LEMNA rare; distillation approaches (TRUSTEE DT-extraction, Markovian distillation, Metis) for global explanations; intrinsic: DTs, LEXNet prototypes, I2RNN, additive trees, SOM-based IDS; attention used as explanation in ID [95,150,153,176] and TC [80,89] "while ongoing debates in the literature question the suitability of attention mechanisms as a measure of feature importance."
- Inputs (VII): raw bytes (mostly TC; byte→image reshaping "typically is not soundly motivated and represents an obstacle to the practical interpretation ... by itself"), packet sequences (PL/DIR/IAT/TCP-WS/flags/TTL; lightweight, encryption-robust), pre-extracted tabular features (the large majority; NetFlow, CICFlowMeter ~80+ features), heterogeneous/multimodal (rare; only [74] uses all three). "The weaker semantic content in networking data limits the effectiveness of XAI, indicating the need for specialized approaches tailored to the unique demands of NTA."
- Datasets (VIII-A): 51 public datasets tabulated; 30/51 security-domain; only 14 human-generated (fully or partially); XAI studies concentrated on TC datasets, then ID/AC.
- Tools (VIII-B): only 3 of the listed libraries implement explanation-quality metrics; "there is no agreement on the nomenclature of metrics nor on their definition."

**XAI evaluation (what the survey reports about the field - the core finding).**
- "Only a few works in NTA defines and/or utilizes metrics for evaluating explanations [75], [96], [115], [143], [150]." (5 of 107.)
- Table V harmonizes "17 definitions for explanation-quality metrics being considered in NTA," with a "translation" to the Nauta categories; "the most common being Robustness and Stability. More important, the lack of consensus and clarity in metric definitions can be noted. In fact, different papers utilize identical names while referring to different metrics, or even distinct explanation aspects altogether (as in the case of Stability)."
- "a significant portion of these metrics pertain to the Continuity property (7 out of 17 definitions). The second most considered property is Correctness (4 out of 17 definitions), and both belong to the content viewpoint. ... in NTA many explanation-quality properties are currently neglected."
- Common indirect validation pattern: retrain on XAI-selected top-k features and compare accuracy/latency (e.g., Roshan & Zafar top-40/78 SHAP features; Garcia et al. headers-vs-payload; Keshk et al. top-20 SHAP/PFI; Nascita et al. ≈60% training-time cut).
- Bottom line stated: "while the insights gained from explainability analyses can provide valuable guidance ..., they do not (at their current stage of maturity) directly and automatically contribute to enhancing traffic detection or prediction accuracy."

**Ground truth used:** NONE (survey; performs no experiment). Crucially it documents that GT-annotated explanation datasets do not exist in NTA.

**Stated limitations / open challenges (Section IX, near-verbatim).**
- IX-A Inadequate methods for XAI in the loop: "XAI methods should not only elucidate the reasons behind predictions but also explicitly indicate the necessary steps to enhance the quality of these predictions"; "XAI methods encounter challenges due to the lack of methodologies tailored for incremental training. Indeed, the dynamic nature of incremental updates surpasses conventional XAI tools' capabilities."
- IX-B Cost: "the accuracy-interpretability trade-off"; "Achieving interpretability through XAI also entails associated computational cost"; "difficulty in integrating into networking systems for on-the-fly model interpretation"; need for "standard application programming interfaces and software development kits."
- IX-C Lack of specialized XAI methods: existing studies "commonly utilize XAI methods introduced in other application domains like SHAP and LIME. Such methods are not inherently crafted to harness the distinctive features of contemporary networking systems and data ... this approach may result in inconsistent or misleading outcomes"; calls out "the integration of causal explanation methods" as a relevant example.
- IX-D Non-standardized metrics & interfaces: "there is an urgent need for shared (and possibly rigorous) metrics to evaluate the explanations obtained. Different techniques may return different results, and it is difficult to know which technique is to be preferred"; "Current evaluations are often not well-suited for evaluating the complex and multifaceted nature of explanations. While some metrics used in NTA focus on properties like Correctness and Continuity, these represent only two of twelve key properties"; "an exhaustive assessment of explanation quality would be impractical"; **"the sharing of datasets including annotated ground truth for explanations is crucial for evaluating new methods and selecting the most effective one. Networking poses even greater challenges compared to more established fields like computer vision, as even just assessing the plausibility of results-although straightforward for an image-becomes more complex in the case of network traffic."** Plus privacy issues in trace sharing.
- IX-E Absence of XAI-driven foundation models for NTA; "a lack of metrics for resilience evaluation in the literature can be also observed."

**My gap observations.**
- The survey's own Coherence definition presumes "a ground truth is available" - and its own dataset table shows none of the 51 datasets carries explanation annotations; the field's flagship survey thus certifies that the Correctness/Coherence axis is currently unmeasurable in NTA. This is the single strongest citation for my project's motivation.
- The survey catalogs metrics but never audits their validity: deletion/occlusion-style Correctness proxies are accepted at face value; sanity checks (Adebayo-style), the attention-faithfulness debate (cited only in passing as [41],[179]), and synthetic/architectural ground-truth construction (GNNExplainer-style planted GT, weight-transparent models) are absent from the metric discussion - there is no NTA analogue of "planted-motif" benchmarks anywhere in the 107 papers.
- Feature-subset retraining, the field's favorite validation (top-k SHAP features → retrain), conflates feature predictivity with explanation fidelity: a wrong attribution over redundant, correlated flow features (CICFlowMeter is heavily redundant) can still pass it.
- Reliability/calibration (III-C) and explanation quality are surveyed as parallel tracks; no reviewed work connects them (e.g., is explanation quality worse on miscalibrated/low-confidence predictions?) - open empirical question.
- The 5-of-107 statistic makes the quantitative case: ~95% of XAI-NTA papers display explanations without evaluating them (my project's "plots-only" phenomenon), and even the 5 that evaluate mostly measure Continuity (stability), not truth.

---

## 6. Why Attention is Not Explanation: Surgical Intervention and Causal Reasoning about Neural Models (Grimsley, Mayfield, Bursten - LREC 2020, pp. 1780-1790)

**Read depth:** full text.

**What it is.** A philosophy-of-science analysis (no new experiments) of the attention-faithfulness debate: Jain & Wallace (2019) and Serrano & Smith (2019) (plus the Wiegreffe & Pinter response), re-read through Woodward's interventionist account of causal explanation. Taxonomy of theories of explanation (deductive-nomological, unification, transmission-causal, interventionist, pragmatic, psychological).

**Argument (3 research questions).**
- Q1: Do the attention-manipulation studies fit the interventionist account? A1: "Yes, these studies are attempting to make arguments that fit the interventionist account" (empirical data, counterfactual reasoning, causal claims).
- Q2: Are the manipulations SURGICAL (all non-target variables held invariant)? A2: "No, manipulating attention weights fails to meet the conditions of surgical intervention." "The relevant system in this case is not attention alone, but attention in addition to and in connection with the neural model's prior layers. ... the scope of the changes to network output ... may not match the scope of attempted interventions." Wiegreffe & Pinter's critique "can be strengthened with philosophical vocabulary."
- Q3: Consequences? A3: "Attention weights alone cannot be used as causal explanations for model behavior." "by definition, attention is not explanation"; "the 'deep' structure of contemporary NLP is exactly what prevents causal explanation from manipulation of their parts." Apparently-causal explanations from such systems are "causal fake news" - successful only under psychological (sense-of-understanding) accounts. Recommends grounding XAI success criteria in non-causal accounts: mathematical explanation, structural-model explanation, minimal-model explanation.

**XAI evaluation:** none empirically - the paper is a conceptual meta-evaluation; its contribution is a principled success-criterion (surgical interventionist causality) against which it argues attention-based explanation necessarily fails.

**Ground truth used:** NONE (no experiments).

**Stated limitations (Section 6.1, near-verbatim).** "While our study of explanation is based in philosophy, our contributions are based in epistemology, not in ethics. ... We have examined whether researchers or users are being given a true explanation. But a good explanation does not mean that an algorithm has made a good decision. ... Our work does not absolve researchers from a broader social responsibility ... our work must be a component piece, incorporated into a broader foundation that accounts not only for explanation but also for ethical software development."

**My gap observations.**
- The impossibility claim is asserted without an operational test: no measurable criterion is offered by which a practitioner could certify a given method as achieving (or verifiably approximating) surgical intervention, and the recommended non-causal accounts (minimal-model etc.) are left entirely unoperationalized - the paper names the destination but provides no metric.
- Taken seriously, the argument indicts far more than attention: LIME/SHAP perturbations, deletion/occlusion curves, and permutation importance are all non-surgical interventions on entangled systems; the paper never extends the analysis to input-space perturbation methods, though it applies a fortiori.
- Domain nuance the paper misses (useful for NTC): in networking one can sometimes intervene on the REAL data-generating process - craft/replay modified packets and observe the classifier in situ - a physically realizable intervention unavailable in NLP; and synthetic/architectural ground truth (models or datasets whose causal structure is known by construction) is precisely a way to restore surgical intervention, which motivates my project's GT-based evaluation design.
- Bridges to batch papers: gives the vocabulary for why proxy metrics (deletion curves, attention correlations) are not GT - they are non-surgical interventions delivering at best psychological-account satisfaction.

---

## Cross-batch synthesis (batch 5)

This batch pairs the NTC field's flagship survey with the methodological canon it should be (but mostly is not) built on. The survey (Nascita et al.) quantifies the field's evaluation vacuum: 5/107 papers use any explanation-quality metric, 17 mutually inconsistent metric definitions dominated by Continuity/stability (7/17) over Correctness (4/17), zero NTA datasets with annotated explanation ground truth, and an explicit open challenge calling for exactly such datasets. The canon shows what rigorous evaluation looks like and where each style breaks: GNNExplainer is the lone GT-based protocol (synthetic planted motifs → explanation accuracy as edge-level binary classification) but leaks GT size into the method and never verifies model-process alignment; Jain & Wallace and the Captum sanity-check study supply transferable falsification batteries (adversarial/permuted attention, parameter/data randomization, infidelity/max-sensitivity) that are proxy-only, modality-sensitive, and - per the Captum result that image conclusions don't transfer to text - cannot be assumed valid on traffic representations without re-running them there; Grimsley et al. give the theoretical verdict that all such non-surgical interventions can never certify causal explanation. Kitsune sits at the other end: the de facto XAI-NIDS benchmark generator that itself contains zero interpretability, whose correlated damped-window features and unannotated attacks are what most downstream SHAP-on-NIDS papers "explain" unverifiably. Net gap this batch nails down: NTC has imported explainers and (rarely) proxy metrics, but has imported neither the GT-construction idea (no traffic BA-SHAPES exists), nor the sanity-check/adversarial batteries, nor any interventional protocol that networking uniquely could support (packet-level real-world intervention) - the precise opening for a ground-truth-based evaluation framework.
