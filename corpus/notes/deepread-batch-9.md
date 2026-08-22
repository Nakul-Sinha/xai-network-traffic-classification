# Deep-Read Notes - Batch 9

Reader focus: (1) how explanation quality is EVALUATED, (2) LIMITATIONS / FUTURE WORK.
All six papers read from full text (PDF extraction). Date: 2026-08-22.

---

## 1. Evaluating the Visualization of What a Deep Neural Network Has Learned
**Samek, Binder, Montavon, Bach, Müller - IEEE TNNLS 2017 (arXiv:1509.06321, read v1)**
Read depth: full text.

### What it is
The founding paper of perturbation-based heatmap evaluation. Not a traffic paper - it is the methodological ancestor of nearly every "deletion/insertion curve" used later in XAI-NTC. Compares three heatmapping methods on image classifiers.

- **Task**: image classification explanation (scene/object recognition).
- **Models**: MIT Places CNN (provided by dataset authors), Caffe reference model (ImageNet), small CNN on CIFAR-10. Classifiers used unmodified.
- **XAI methods compared**: Sensitivity analysis (Simonyan; l2 and l-inf channel pooling), Deconvolution (Zeiler & Fergus, same poolings), LRP (three variants: eps=0.01, eps=100, alpha=2/beta=-1), random-order baseline.
- **Datasets**: SUN397, ILSVRC2012, MIT Places (5040 test images each), CIFAR-10 for the heatmap-quality-vs-accuracy experiment.

### How explanation quality is evaluated (core contribution)
- **Region perturbation framework**: heatmap = ordered set of image locations; **MoRF** (Most Relevant First) process iteratively replaces 9x9 non-overlapping regions (0.157% of image each; 100 steps = 15.7% of image) with values sampled from a uniform distribution, 10 repetitions.
- **Metric: AOPC** - "area over the MoRF perturbation curve": AOPC = (1/(L+1)) * <sum_k f(x0) − f(xk)>_p(x). "An ordering of regions such that the most sensitive regions are ranked first implies a steep decrease of the graph of MoRF, and thus a larger AOPC."
- **Appendix: LeRF + ABPC** - least-relevant-first curve and "area between perturbation curves" (ABPC = gap between LeRF and MoRF curves), used to compare perturbation operators themselves.
- **Auxiliary complexity criteria**: average compressed file size of heatmap images (png/jpeg KB) and MATLAB image entropy ("heatmaps should have low complexity, i.e., be as sparse and non-random as possible").
- Evaluation done for the predicted label, so "our perturbation analysis is a fully unsupervised method during test stage".

### Ground truth
**None.** AOPC is a proxy built on an assumption ("good heatmaps should rank pixels according to relevance wrt to classification"); no human, architectural, or synthetic ground truth anywhere. The authors defend non-circularity ("LRP does not artificially benefit from the way we evaluate heatmaps") but the metric still measures classifier response, not correctness.

### Key numbers
- LRP has largest AOPC on all three datasets; deconvolution is "closest competitor"; sensitivity on SUN397 falls **below the random baseline** (off-manifold effect: SUN397 images lie outside the training manifold of the MIT Places classifier).
- File sizes (png): LRP 154-155 KB < deconv 164-167 < sensitivity 177-183 (lower = less complex).
- Perturbation operator matters enormously: ABPC on SUN397 = Uniform 243.69, Dirichlet 239.8, Constant 193.65, **Blur 113.75** ("blurring fails to remove information").
- CIFAR-10: AOPC tracks accuracy across training iterations (45%→75%) - heatmap quality as unsupervised proxy for model quality.

### Stated limitations / future work (near-verbatim)
- "Note that ... the setup here slightly disfavours LRP" (LRP designed for binary f(x)=0-centered classifiers; used unmodified multiclass nets).
- "a heatmap always represents the classifier's view, i.e., explanations neither need to match human intuition nor focus on the object of interest ... there is no guarantee that human and classifier explanations match."
- "explanations can only be as good as the data provided to the classifier."
- "This paper did not in[t]end to profoundly investigate the relation between network performance and heatmap quality, this is a topic for future research." / "Bringing this idea into practical application will be a topic of future research."
- Appendix acknowledges the manifold problem: ideal perturbation "neither significantly disrupts image statistics nor moves the corrupted image far away from the data manifold."

### My gap observations (not stated by authors)
- The evaluation is **operator-dependent**: their own appendix shows ABPC swinging 113.75→243.69 with the choice of g(). Any AOPC-based method ranking is conditional on an arbitrary information-removal scheme; the paper never quantifies how method *rankings* (not just ABPC) change across operators.
- OOD circularity: score drops conflate "region was relevant" with "perturbed input is off-manifold"; they observe the off-manifold effect for SUN397 sensitivity maps but do not control for it in the main metric.
- The complexity/sparsity criterion is an aesthetic prior, not correctness - a sparse wrong heatmap scores well.
- Transfer to NTC is non-trivial and unaddressed by the descendants: "replace a 9x9 region with uniform noise" has no protocol-valid analog for flow features (e.g., perturbed packet counts/flags can be mutually inconsistent), so AOPC-style curves in traffic papers inherit an even worse validity problem.
- No per-sample ground truth of any kind; no human study despite motivating heatmaps as tools for humans.

---

## 2. LEMNA: Explaining Deep Learning based Security Applications
**Guo, Mu, Xu, Su, Wang, Xing - ACM CCS 2018 (Outstanding Paper)**
Read depth: full text.

### What it is
First explanation method purpose-built for security DL (RNN/MLP), blackbox. Local surrogate = **mixture regression model (K Gaussian components, EM) with fused lasso** penalty to capture feature dependency (adjacent bytes) and locally nonlinear boundaries. Explanation = top features from the best-fitting linear component.

- **Tasks**: (a) binary function-start detection for reverse engineering - bidirectional RNN following Shin et al.; (b) PDF malware classification - MLP.
- **Input representation**: (a) hex byte sequences truncated to length 200, each byte's decimal value = a feature; (b) 135 hand-crafted PDF structural features (Mimicus), binarized.
- **Datasets**: 2,200 binaries (ByteWeight dataset) compiled at O0-O3 (x86, gcc) → 4 classifiers; 4,999 malicious + 5,000 benign PDFs.
- **Classifier accuracy**: 98.57-99.99% precision/recall (Table 2) - explanations are produced for near-saturated models.
- **Baselines**: LIME, random feature selection. SHAP tested but dismissed in a footnote: "SHAP is very slow and its performance is worse than LIME for our applications" (no numbers).
- Hyperparameters N=500, K=6; fused-lasso threshold S=1e-4 (binary) vs S=1e4 (PDF) - set per application based on known feature dependency.

### How explanation quality is evaluated
Two-stage "fidelity" evaluation (Section 5.2):
1. **Local approximation accuracy - RMSE** between classifier prediction probabilities p_i and surrogate estimates p̂_i over test samples.
2. **Three end-to-end fidelity tests**, all measured by **PCR ("positive classification rate")** = fraction of crafted samples still classified as the original label, as a function of number of selected features |Fx|:
   - **Feature Deduction Test**: nullify selected features Fx from x (want low PCR).
   - **Feature Augmentation Test**: transplant Fx values into a random instance of the opposite class (want high PCR).
   - **Synthetic Test**: keep Fx, randomize all other features (want high PCR).
3. Hyperparameter sensitivity table (N, K, S variations; results stable).
Additionally, §6 case studies compare explanations against **well-known domain heuristics / "golden rules"** (ABI prologue `[push ebp; mov ebp,esp]`, gcc `nop` padding, `ret`-before-start), and demonstrate error troubleshooting + targeted patching (augment training data by randomizing the misleading features → retrain).

### Ground truth
**None in the quantitative evaluation** - RMSE and all three PCR tests are perturbation-based proxies (deduction is exactly an occlusion test). The §6 comparison with compiler/ABI golden rules is genuine expert domain knowledge, but it is a qualitative demonstration on 15 hand-picked cases, never turned into a scored benchmark, so I code the paper as ground_truth_used=none with an explicit note. (Honorable mention: the patching experiment is an *interventional use* of explanations - retraining guided by explanations reduces errors - which is indirect evidence of explanation utility, but not an explanation-correctness ground truth.)

### Key numbers
- RMSE: LEMNA 0.0102-0.0264 vs LIME 0.1178-0.1784 ("an order of magnitude smaller"); "the best performing result of LIME has a RMSE of 0.1532, which is still almost 10 times higher than the worse performing result of LEMNA (0.0196)".
- Deduction: nullifying top-5 features (2.5% of the 200) drops function-start PCR to ≤25%; top-35 → PCR ≈ 0.
- Augmentation: top-5 features flip 75% of PDF malware test cases.
- Synthetic: top-5 features → 85-90% take the source label.
- LIME ≈ random on the PDF malware classifier (sparse features hurt boundary smoothness).
- Patching (Table 6): e.g., Binary O2 FN 107→59, FP 129→62; PDF FN 28→10, FP 13→5. ~10s per explanation; 2.5 h for 25,040 sequences with 30 threads.

### Stated limitations / future work (near-verbatim, §7 Discussion)
- Dual use: "it might be used by an attacker to seek the weakness of a deep learning classifier" (they argue this "should not dilute the value" - fuzzing analogy).
- "Manually reading each case's explanation is time-consuming" - suggest clustering identical explanations.
- Other architectures: "sequence-to-sequence networks ... hybrid networks ... Once concrete security applications are built in the future, we plan to test LEMNA on these new architectures."
- "LEMNA is not directly applicable to classifiers trained on obfuscated features."
- "Our work is only the initial step towards improving the model transparency..."

### My gap observations (not stated by authors)
- Motivates with network intrusion detection (cites NIDS DL work in the intro) but **never evaluates on network traffic** - the NTC transfer of the fidelity-test methodology was left to later papers, which imported its OOD problems.
- All three fidelity tests craft out-of-distribution inputs (nullified bytes = invalid code; synthetic instances = random hex) - the same proxy circularity as image occlusion, arguably worse because the input space is discrete/structured.
- No whitebox baselines (gradients, IG, LRP) even where applicable (MLP); the comparison universe is LIME + random; SHAP dismissed without reported numbers.
- Mixture-model EM has stochastic initialization; explanation **stability across runs is never measured** - for a method whose selling point is fidelity, run-to-run variance matters.
- The fused-lasso threshold S must be set according to whether features are dependent (1e-4 vs 1e4 - 8 orders of magnitude apart), i.e., you must already know the dependency structure the method claims to discover.
- The golden-rules validation is the germ of a human_expert ground-truth benchmark (expert-known prologue patterns) but stays anecdotal; nobody quantifies precision/recall of explanations against the rule set.

---

## 3. Outside the Closed World: On Using Machine Learning For Network Intrusion Detection
**Sommer & Paxson - IEEE S&P (Oakland) 2010**
Read depth: full text.

### What it is
Position paper (no experiments, no model, no dataset, no XAI method). Diagnoses why ML-based anomaly detection is "rarely employed in operational 'real world' settings" despite huge academic output. The intellectual root of interpretability requirements in NIDS: the **semantic gap**.

### Challenges identified
(i) ML is better at finding similarity than meaningful outliers - the "closed world assumption" fails; (ii) very high cost of errors (Axelsson base-rate fallacy); (iii) **semantic gap**: "transferring their results into actionable reports for the network operator ... the next step then needs to interpret the results from an operator's point of view - 'What does it mean?'"; (iv) enormous diversity/variability of benign traffic; (v) difficulties with evaluation - data scarcity (DARPA/KDD "now a decade old, and no longer adequate for any current study"; KDD features "exhibit unfortunate artifacts"), simulation lacks realism, anonymization removes exactly the artifacts anomaly detection needs; (vi) adversarial setting (though they argue evasion risk is practically overrated for indiscriminate attackers).

### Evaluation / ground-truth guidance (the part most relevant to my project)
- "If we could give only one recommendation ... it would be: **Understand what the system is doing.**"
- "one can always find a variation that works slightly better than anything else in a particular setting ... we are working in an area where **insight matters much more than just numerical results**."
- Researchers must "manually examine false positives" and - crucially - inspect **true positives too**: "with machine learning, it is often not apparent what the system learned even when it produces correct results" (illustrated by the 1980s Pentagon tank/sky anecdote - the canonical spurious-correlation story).
- On ground truth: "False negatives ... require reliable ground-truth, which can be notoriously hard to obtain ... If one cannot find a sound way to obtain ground-truth for the evaluation, then it becomes questionable to pursue the work at all." - "One must collect ground-truth via a mechanism **orthogonal (unrelated) to how the detector works**." Options given: orthogonal labeling technique; manual labeling ("often however infeasible"); "A final compromise is to **inject a set of attacks deemed representative**."
- ML as means not end: use it "to understand the significance of the different features of benign and malicious activity, which then eventually serve as the basis for a non-machine-learning detector."
- "the most convincing real-world test ... is to solicit feedback from operators who run the system in their network."

### XAI evaluation / ground truth fields
xai_evaluation: none (no explanations exist). ground_truth_used: none.

### Stated limitations (near-verbatim)
- "we are network security researchers, not experts on machine-learning, and thus we argue mostly at an intuitive level rather than attempting to frame our statements in the formalisms employed for machine learning."
- "we view these guidelines as touchstones rather than as firm rules."
- "We stress that we do not consider our discussion as final."

### My gap observations
- The paper demands "insight" and "semantic understanding" but provides **no operationalization or metric** for it - the vacuum that post-2016 XAI methods rushed into without solving.
- Its ground-truth discipline (orthogonal labeling mechanisms, injected representative attacks) was formulated for *detector* evaluation and maps directly onto *explanation* evaluation (inject attacks whose causal features are known by construction → synthetic/interventional explanation ground truth) - a transfer the XAI-NTC literature has essentially never made explicit. This is a strong framing hook for my paper.
- The tank anecdote is precisely the "spurious feature detection" use case that saliency methods now claim to serve; 15 years later there is still no standard test of whether XAI methods actually catch planted spurious features in NIDS models.
- Its recommendation to compare against "simpler, non-machine learning approaches" has an unheeded XAI analog: compare post hoc explanations of DNNs against directly interpretable baselines (rules/trees) at equal detection performance.

---

## 4. The Disagreement Problem in Explainable Machine Learning: A Practitioner's Perspective
**Krishna, Han, Gu, Wu, Jabbari, Lakkaraju - TMLR 06/2024 (arXiv:2202.01602v6)**
Read depth: full text.

### What it is
Formalizes and measures **disagreement between post hoc explanation methods** for the same prediction, grounded in practitioner interviews; then an empirical study and an online user study of how disagreements get resolved.

- **Method inputs**: 25 semi-structured interviews with data scientists (tech + financial services; 84% report encountering disagreement; 88% "almost always use multiple explanation methods").
- **Explainers**: LIME, KernelSHAP, Vanilla Gradient, Gradient x Input, Integrated Gradients, SmoothGrad (+ L2X in appendix). Sample-size hyperparameters run to convergence.
- **Models**: logistic regression, feed-forward NN, random forest, gradient-boosted tree (tabular); vanilla LSTM (text); pretrained ResNet-18 (images).
- **Datasets**: COMPAS (7 features, 4,937 defendants), German Credit (20 features, 1,000), AG_News (127,600 sentences), ImageNet-1k with PASCAL VOC 2012 segmentation maps as superpixels.

### The measurement framework (their "evaluation")
Six practitioner-derived **disagreement metrics** (lower = stronger disagreement):
- Top-k based: **feature agreement** (fraction of shared top-k features), **rank agreement** (shared + same rank), **sign agreement** (shared + same sign), **signed rank agreement** (shared + same sign + same rank).
- Feature-of-interest based: **rank correlation** (Spearman) and **pairwise rank agreement**.
Notable design insight from interviews: 96% of practitioners say raw importance *values* are not comparable across methods, so disagreement is defined over sets/ranks/signs, not values.
Then an online **user study** (25 participants; 12 overlap with interviews; prompts deliberately "selected to ensure high disagreement") on perceived disagreement and resolution.

**Important**: this measures *inter-method agreement* and *human resolution behavior* - it never evaluates which explanation is *correct*. The intro concedes the core obstacle: faithfulness metrics exist (ground-truth feature importances, ROAR) but "challenges arise due to the unavailability of ground truth in real-world applications and the impracticality of retraining models in certain settings."

### Ground truth
**None.**

### Key numbers
- COMPAS NN: 14/15 explanation-method pairs exhibit **negative** rank correlation when explaining multiple data points; agreement drops as k grows; disagreement stronger for NN than logistic regression (complexity trend) and for the 20-feature dataset than the 7-feature one.
- Text (k=11 ≈ 25% of sentence length): "rank agreement and signed rank agreement are the lowest ... values under 0.1 for most cases indicating disagreement in over 90% of the top-k features."
- Images: LIME vs KernelSHAP on superpixels agree strongly (rank corr 0.8977, feature agreement 0.9535, signed rank agreement 0.8193) but gradient methods at pixel level: IG vs SmoothGrad rank correlation **0.001** - "disagreement could potentially vary significantly based on the granularity of image representation."
- User study: 4% completely agree / 28% mostly agree / 50% mostly disagree / 18% completely disagree; when choosing, KernelSHAP picked 66.7% of the time vs Gradient x Input 7.0%; resolution strategies: 33% "inherently better theory/recency", 32% "matches intuition better", 23% "LIME/SHAP for tabular"; day-to-day: 50% ad hoc heuristics, 36% confusion/uncertainty ("no clear answer to me"), 14% suggest fidelity metrics → "86% ... admitted to using ad hoc heuristics or being uncertain."

### Stated limitations / future work (near-verbatim)
- "In this work, we prioritized examining the prevalence of explanation disagreement rather than exploring its underlying causes, given the complexity of this analysis." (Causes analyzed in follow-up Han et al. 2022: all these methods are local linear approximations with different loss/neighborhood choices.)
- "the extent of explanation disagreement would also depend on the specific metric being used ... the extent of disagreement is slightly lower when we consider variants of the proposed metrics" (weighted rank agreement etc., Appendix D.2).
- Resolution "remains an active area of research"; they recommend defining the goal of an explanation first and choosing the method that best satisfies it (e.g., local function approximation per Han et al.).

### My gap observations (not stated by authors)
- Disagreement without ground truth is **undiagnosable**: the framework can show two methods conflict but cannot say whether either is right - the exact missing piece a ground-truth-anchored benchmark would supply; my project can close this loop for NTC.
- No security/networking practitioners and no network datasets anywhere - the disagreement problem is **unquantified for NTC feature spaces** (highly correlated flow statistics, mixed categorical/numeric packet fields), where correlated features plausibly aggravate rank instability. Porting the six metrics to NTC explainers is cheap and novel.
- User-study prompts were intentionally chosen for high disagreement, so the study measures resolution behavior, not in-the-wild prevalence; the interview statistic (84%) is self-report.
- Intuition-based resolution (theme 2, 32%) is exactly the plausibility bias that ground-truth-free evaluation invites - practitioners judge explanations by priors, which cannot detect a model that genuinely relies on unintuitive features (Sommer-Paxson's tank problem, full circle).
- Small samples (25 + 25 with 12 overlap) from two sectors; k=5 of 7 features on COMPAS makes feature agreement nearly saturated by construction.

---

## 5. FlowPrint: Semi-Supervised Mobile-App Fingerprinting on Encrypted Network Traffic
**van Ede, Bortolameotti, Continella, Ren, Dubois, Lindorfer, Choffnes, van Steen, Peter - NDSS 2020**
Read depth: full text.

### What it is
A network-traffic system paper (no deep learning, no post hoc XAI): real-time, semi-supervised **app fingerprinting** from encrypted TLS traffic, able to recognize known apps and detect previously unseen ones without prior app knowledge. Relevant to the XAI-NTC corpus as the archetypal *interpretable-by-construction* alternative: fingerprints are human-readable sets of network destinations.

- **Pipeline**: per-device feature extraction → destination clustering (flows grouped if same (dest IP, dest port) tuple OR same TLS certificate) → browser isolation (random forest on relative changes in active clusters/bytes up/down; isolates ±10 s around detections) → cross-correlation of cluster activity over time → fingerprint = strongly-correlated cluster groups (clique finding) → matching/updating fingerprint database. Batch interval tau_batch = 300 s.
- **Preliminary feature ranking**: Adjusted Mutual Information (AMI) against app label on ReCon; top features: inter-flow timing 0.493, source IP 0.434 (→ per-device processing), TLS cert validity-after 0.369 / validity-before 0.356 / serial 0.342, dest IP 0.246; most packet-size stats ≤0.07 → size features dropped.
- **Datasets** (labeled, public at github.com/Thijsvanede/FlowPrint): ReCon (512 apps, 28.7K flows), ReCon extended (5 apps, 141.2K flows), Cross Platform (215 Android + 196 iOS apps, 102.2K flows, user-generated), Andrubis (1.03M apps, 41.3M flows, incl. potentially harmful), self-collected Browser dataset (4 browsers, 204.5K flows).
- **Threat model**: enterprise monitor, per-device visibility, single-app-at-a-time assumption.

### How explanation quality is evaluated
**None - there are no explanations.** The paper evaluates *detection* (accuracy/precision/recall/F1, homogeneity analysis of shared clusters, confidence of fingerprints, timeliness). The interpretability of destination-based fingerprints is implicit (an operator can read IPs/certificates) but is never framed, measured, or user-tested as such. AMI ranking is dataset-level feature selection, not per-decision explanation.

### Ground truth
For explanations: none/NA (no explanations). App labels provide detection ground truth only.

### Key numbers
- App recognition accuracy **89.2%** (vs supervised AppScanner state of the art; AppScanner covers only 72% of TCP streams at 99% accuracy on its confident subset).
- Unseen-app detection precision **93.5%**; **72.3%** of apps detected within first 5 minutes.
- Browser isolation: accuracy 98.1%, precision 79.8%.
- App-specific clusters vanish with scale: with 100 random apps only 58% have ≥1 app-specific destination cluster; at 1,000 apps → 38% (hence the need for temporal correlation).
- F1 remains ~0.9 under app updates (ReCon extended).

### Stated limitations / future work (near-verbatim, §VI Discussion)
- **Potential for evasion**: VPN/proxy redirection ("our approach would still be able to detect the presence of an unknown app but it will have trouble identifying the specific app"); mimicking a genuine app's destinations/timing.
- **Low-traffic apps**: "apps that only communicate with widely used services, e.g. advertisement networks and CDNs ... may be difficult to fingerprint. ... If the pattern generated by an app is common to many other apps, we cannot discern said specific app."
- **Simultaneously active apps**: "future work needs to investigate the fingerprint generation for multiple simultaneously active apps."
- **Repackaged apps**: "we did not specifically investigate the effect of repackaged apps."
- **Fingerprint coverage**: "it takes some time ... to converge"; multiple fingerprints of one unseen app are counted as separate apps; automatic merging is future work.
- **AppScanner reimplementation** "might still slightly differ from the original tool."
- **Privacy implications**: app identification despite encryption enables censorship/tracking; device-type identification "we leave for future work."

### My gap observations (not stated by authors)
- The paper is routinely cited (in XAI-NTC surveys) as evidence that transparent NTC pipelines exist, yet **no interpretability claim is ever evaluated** - no operator study, no measure of whether destination-cluster fingerprints are actionable, no comparison of analyst effort vs a black-box classifier. "Interpretable-by-design" remains an assertion.
- The semantic units (IP/port/TLS cert clusters) are exactly the kind of human-meaningful vocabulary that post hoc XAI for DL traffic classifiers lacks; contrasting FlowPrint-style semantic features with saliency over packet bytes would make a sharp case study for the semantic-gap argument.
- AMI feature ranking is computed *with labels* on a subset, sitting oddly with the "no prior knowledge" narrative; it is a global, filter-style analysis and cannot explain individual matches (e.g., *why* an unseen app was flagged).
- Detection ground truth is app labels, but fingerprint *semantics* (which cluster corresponds to which app module/library) are never validated - shared-cluster analysis (ads/CDN) is the closest they get.

---

## 6. Lucid: A Practical, Lightweight Deep Learning Solution for DDoS Attack Detection
**Doriguzzi-Corin, Millar, Scott-Hayward, Martínez-del-Rincón, Siracusa - IEEE TNSM 2020 (arXiv:2002.04902)**
Read depth: full text.

### What it is
A canonical DL-NTC system paper with a built-in explainability section. Binary DDoS/benign flow classification designed for online, resource-constrained (edge) deployment; contribution (3) is "an activation analysis to explain LUCID's DDoS classification" - "To the best of our knowledge, this is the first application of a specific activation analysis to a CNN-based DDoS detection method."

- **Input representation**: per-flow 2D matrix n x f = up to 100 packets x 11 packet-level attributes (relative time, packet len, highest layer, IP flags, protocols bag-of-words, TCP len, TCP ack, TCP flags, TCP window size, UDP len, ICMP type), normalized to [0,1], zero-padded, collected in time windows (t up to 100 s). Dataset-agnostic preprocessing (Algorithm 1).
- **Model**: single conv layer (k=64 filters, h=3, full input width), ReLU, global max pooling, single sigmoid output; **2,241 trainable parameters** (vs 1,004,889 for the DeepDefense 3LSTM baseline they reimplement).
- **Datasets**: UNB ISCX2012, CIC2017, CSECIC2018; balanced per dataset (e.g., 37,378 DDoS flows from ISCX2012; 97,718/97,718 CIC2017; 360,832/360,832 CSECIC2018); merged into **UNB201X** for train/val, tested per-dataset (unseen test data).
- **Detection results**: F1 = 0.9889 (ISCX2012), 0.9966 (CIC2017), 0.9987 (CSECIC2018), 0.9946 (UNB201X); FPR 0.0087 on UNB201X; 40x processing-time reduction vs state of the art; 1.9 Mpps CPU-only on NVIDIA Jetson TX2.

### The XAI method: kernel activation analysis (Section VI)
"Inspired by a similar study [Jacovi et al.-style NLP CNN interpretation] ... it is possible to remove the classifier, push the DDoS flows through the convolutional layer and capture the resulting activations per kernel. For each flow, we calculate the total activations per feature, which in the spatial input representation means per column, resulting in 11 values that map to the 11 features. This is then repeated for all kernels, across all DDoS flows, with the final output being the total column-wise activation of each feature." Post-ReLU sums; "the higher a feature's activation when a positive sample i.e. a DDoS flow is seen, the more importance the CNN attaches to that particular feature." Global, class-level ranking on the UNB201X test set (Table X):
Highest Layer 0.69540 > IP Flags 0.30337 > TCP Flags 0.19693 > TCP Len 0.16874 > Protocols 0.14897 > Pkt Len 0.14392 > Time 0.11108 > TCP Win Size 0.09596 > TCP Ack 0.00061 > UDP Len 0.00000 = ICMP Type 0.00000.

### How explanation quality is evaluated
**None (no metric).** The ranking is validated only by **manual plausibility narrative** against dataset statistics: e.g., "99.99% of DDoS packets in the UNB datasets present an IP flags value of 0x4000 ... [vs] about 92% of the [benign] packets. Thus, the pattern of IP flags is slightly different between attack and benign traffic, and **we are confident that LUCID is indeed learning their significance**." And the frank concession: "**even given this activation analysis, there is no definitive list of features that exist for detecting DDoS attacks with which we can directly compare our results**" - citing a 2014 study that "different classes of attack have different properties." Conclusion drawn: "LUCID appears to be learning the importance of relevant features for DDoS detection, which gives us confidence in the prediction performance."

### Ground truth
**None** - explicitly acknowledged as unavailable (the "no definitive list" quote). No expert list, no synthetic construction, no perturbation test even.

### Stated limitations / future work (near-verbatim)
- "there is no definitive list of features that exist for detecting DDoS attacks with which we can directly compare our results."
- Adversarial robustness: "Our activation analysis is a first step in the investigation of the model behaviour in adversarial cases with the feature ranking in Table X highlighting the features for perturbation for evasion attacks. ... The construction of defences robust to adversarial attacks is an open problem ... which we will further explore for LUCID."
- Attack-type prediction "by extending the dataset labeling, which we consider for future work" (Highest Layer links to network/transport/application-layer attacks).
- "as we have not focused on optimising our preprocessing tool ... its evaluation is left as future work."
- Resource/accuracy trade-off study and dynamic model configuration "out of scope of this work."

### My gap observations (not stated by authors)
- **Global-only** explanation: aggregating post-ReLU activations over all DDoS flows and all kernels yields one class-level ranking; no per-flow explanation exists, so the analysis cannot support triage of individual alerts (the operator-facing use case that motivates NIDS explainability).
- The ranking is **confounded by feature sparsity/scaling**: UDP Len and ICMP Type score exactly 0 largely because the flows are overwhelmingly TCP (the features are 0 in the input), so "importance" partially mirrors feature prevalence, not learned weight structure; zero-padding rows dilute column sums; column-wise activation attribution also ignores that a kernel's activation at column j is produced by all 11 columns within its 3-packet window (receptive-field misattribution - activations are not attributions).
- The two "confirmations" are plausibly **dataset artifacts**: "Highest Layer" (numeric encoding of the top recognized protocol layer) acting as the dominant feature smells like a shortcut specific to how UNB traffic was generated, and the 99.99%-vs-92% Don't-Fragment split is a distributional quirk the authors themselves describe; without ground truth, the analysis cannot distinguish "correct domain information" from spurious correlation - it arguably *documents* a shortcut while presenting it as validation.
- No comparison to any standard attribution method (no SHAP/LIME/IG/LRP baseline, no occlusion sanity check), no stability analysis across retrains - despite Samek-style tooling predating it by 4 years.
- With F1 ≈ 0.99 on all UNB sets, near-saturated benchmarks give explanations little to discriminate; explanation analysis on harder/imbalanced settings is absent.

---

## Batch-level synthesis (for the journal paper's gap analysis)

1. **Zero genuine ground truth across the batch.** The two methodological pillars everyone in XAI-NTC cites - Samek's AOPC and LEMNA's deduction/augmentation/synthetic PCR tests - are both perturbation proxies whose scores depend on the perturbation operator (Samek's own appendix: ABPC 113.75-243.69 across operators) and on out-of-distribution artifacts. Lucid is the NTC endpoint of this lineage: a feature ranking validated purely by plausibility narrative, with the authors explicitly conceding "no definitive list of features ... with which we can directly compare our results."
2. **Plausibility-based validation is unfalsifiable given disagreement.** Krishna et al. show that the standard explainers disagree pervasively (negative rank correlations on tabular NNs; <0.1 rank agreement on text; IG-vs-SmoothGrad pixel correlation 0.001) and that 86% of practitioners resolve conflicts with ad hoc heuristics or not at all - with "matches intuition better" as a leading criterion. Combined with (1), the field's dominant validation style (Lucid-style "we are confident the model learned the right thing") cannot detect a wrong explanation of a shortcut-learning model.
3. **The domain already wrote the prescription in 2010 and forgot it.** Sommer & Paxson: obtain ground truth "via a mechanism orthogonal to how the detector works", inject representative attacks if needed, inspect true positives because "it is often not apparent what the system learned even when it produces correct results" (tank anecdote). Mapped to explanations, this is exactly a synthetic/interventional ground-truth benchmark for XAI-NTC - injected traffic whose causal features are known by construction - which none of the experimental papers in this batch (or, largely, the field) implements.
4. **"Interpretable-by-design" NTC exists but its interpretability is never measured.** FlowPrint's destination-cluster fingerprints are semantically meaningful to operators, yet the paper contains no user/utility evaluation of that property; conversely the DL papers (Lucid) have quantitative detection metrics but no explanation metric. The two halves of the evaluation problem never meet.
5. **Concrete openings for our project**: (a) port the six disagreement metrics to NTC explainers on flow features and quantify disagreement under feature correlation; (b) build architectural/synthetic ground truth (models with known decision regions; injected attacks with planted causal features) as the orthogonal mechanism Sommer-Paxson demand; (c) define traffic-valid perturbation operators (protocol-consistent) and measure how operator choice flips AOPC-style rankings in NTC; (d) test whether popular explainers actually recover planted shortcuts (tank-test for NIDS); (e) score explanations against expert "golden rules" quantitatively (LEMNA showed the template but left it anecdotal).

### Temp extraction files (retained)
- tmp-samek-eval.txt, tmp-lemna.txt, tmp-sommer-paxson.txt, tmp-disagreement.txt, tmp-flowprint.txt, tmp-lucid.txt (same directory).
