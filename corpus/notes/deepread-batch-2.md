# Deep-Read Notes - Batch 2 (XAI for Network Traffic Classification)

Read date: 2026-08-22. All six papers read in full text (PDF extraction). Focus per instructions: (1) how explanation quality is evaluated, (2) limitations / future work. Ground-truth taxonomy applied strictly: deletion/occlusion/perturbation curves are proxies, not ground truth.

---

## 1. E-XAI: Evaluating Black-Box Explainable AI Frameworks for Network Intrusion Detection
**Arreche, Guntur, Roberts, Abdallah - IEEE Access 12:23954-23988, 2024. DOI:10.1109/ACCESS.2024.3365140. Read: full text (open-access IEEE PDF).**

### Setup
- Task: multi-class network intrusion detection (attack-type classification per flow).
- Datasets: RoEduNet-SIMARGL2021 (~31M rows, 29 NetFlow-style features), CICIDS-2017 (78 CICFlowMeter features), NSL-KDD (41 features; KDDTrain+/KDDTest+).
- Models: 7 black-box models - RF, DNN, AdaBoost, MLP, KNN, SVM, LightGBM (70/30 split); CNN added in a revision (tabular→1D-array conversion per Zhang et al.).
- XAI methods: SHAP (global summary plot + local) and LIME. LIME is extended to a global scope by the authors: generate local explanation per sample, sum absolute per-feature scores, average over N samples, rank.
- Code released: github.com/ogarreche/XAI_metrics.

### How explanation quality is evaluated (core of the paper)
Six metrics adapted from Warnecke et al. (EuroS&P 2020) [their ref 23], applied per XAI-method x model x dataset:
1. **"Descriptive Accuracy"** - remove top-k features ranked by the explainer (k = 0, 5, 10, 25, 50, 70), re-run the model, plot accuracy vs k; area under the curve tabulated. "If the accuracy drop after the feature is taken out is high, then the XAI explainability power of such a feature is high." Behavior categorized as Perfect / Partially Expected / Not Expected.
2. **"Sparsity"** - fraction of (min-max normalized) importance scores <= threshold tau, tau swept 0→1 in 0.1 steps; AUC of the sparsity curve. Higher AUC = importance concentrated in few features.
3. **"Stability"** - number of top-k features common across N=3 repeated identical runs / k (global and local variants). k=5 (SIMARGL), k=20 (CICIDS, NSL-KDD).
4. **"Efficiency"** - wall-clock time to generate explanations (SHAP: 1-10,000 samples; LIME: 1 and 1,000 samples).
5. **"Robustness"** - adversarial scaffolding attack of Slack et al. [ref 24] ported to NIDS: train an extremely biased single-feature model (e.g., flow duration for a CICIDS DoS) and an adversarial model with an engineered unrelated feature; check whether biased/unrelated features appear in explainer top-3 over 1,000 samples (occurrence bar plots) + sensitivity graph of attack success vs OOD-classifier F1.
6. **"Completeness"** - perturb top-ranked features one at a time (values 0→1, step 0.1); if the predicted class changes, the explanation is deemed "valid". Global completeness % = samples whose class changed / batch (1,000 per class, top-5 features).
- Statistical analysis: Wilcoxon signed-rank tests - but applied to **AI-model accuracy pairs** (k-fold accuracy scores), *not* to the XAI metric comparisons.

### Ground truth used
**None.** All six metrics are functionally-grounded proxies (deletion, perturbation, consistency, runtime, attack demonstration). The robustness experiment does construct a classifier whose reliance on one feature is known by construction, but it is used to demonstrate attack feasibility, not to score explanation correctness against known-true attributions. No expert feature lists, no synthetic/known-truth data, no human study.

### Key numbers
- SHAP > LIME overall (Table 18 summary). Descriptive accuracy behaves as expected for 13/21 (SHAP) vs 8/21 (LIME) model-dataset pairs; sparsity 15/21 vs 7/21 in the top two categories.
- Several models show flat or *increasing* accuracy when top features are removed (esp. DNN/MLP on CICIDS-2017) - attributed to feature redundancy / "curse of dimensionality".
- Completeness: "SHAP and LIME are not complete because they cannot generate complete explanations for most intrusion classes"; incompleteness concentrated in the Normal class (SIMARGL). SHAP > LIME on CICIDS/NSL-KDD completeness.
- Robustness: NSL-KDD most vulnerable for SHAP (biased feature only surfaces 3rd); LIME slightly more robust by OOD-classifier-F1 threshold (deceived only above F1 ~0.8; SHAP degrades from F1 ~0.3).
- Efficiency: SHAP global impractical with KNN/ADA/MLP/SVM; CNN case: SHAP needed >250 GB RAM (kernel kills), LIME 9 min vs SHAP 276 min for 100 samples; LIME-CNN stability 54.54%.

### Stated limitations / future work (Section VII, near-verbatim)
- "The exclusion of other XAI methods like LEMNA presents a limitation in our study." Future work should include LEMNA and similar methods.
- Explore the framework on other benchmark datasets (UNSW-NB15, UMass, vulnerability-based datasets).
- Feature bias: "'Destination Port' has been revealed to be a sign of bias [73]... we may infer that TCP_WIN_SCALE_IN may have the same contaminating effect for the RoEduNet-SIMARGL2021 dataset." Suggest warnings when biased features top an explanation.
- "The findings show that LIME and SHAP cannot be used in their current forms in a production environment."
- "Our work shows that the performance of SHAP and LIME would need to be improved to be used in real-world IDS... enhance SHAP and LIME to be more robust against adversarial attacks... validate the completeness of explanations... before deploying them in reality."
- Time-performance variations: "Future iterations of our proposed E-XAI framework should aim to optimize this aspect."
- CNN experiments "only... a proof of concept" (100 samples, features halved; stability skipped for SHAP; completeness/robustness skipped for CNN).

### My gap observations (not stated by authors)
- No ground-truth comparison anywhere: the entire six-metric battery is model-referenced. A method could score perfectly while highlighting dataset artifacts.
- The completeness metric equates "perturbing top features fails to flip the class" with an *invalid explanation* - this conflates model insensitivity/robustness with explanation incorrectness; a faithful explanation of a redundant-feature model is penalized.
- Perturbations sweep normalized [0,1] values with no protocol/semantic validity constraints - completeness and robustness are computed on out-of-distribution, possibly physically impossible traffic feature vectors.
- The Wilcoxon significance testing validates *classifier accuracy* differences; the paper's actual claims (SHAP vs LIME across six XAI metrics) carry no statistical testing.
- Descriptive accuracy removes globally ranked features and re-evaluates - measuring dataset redundancy and retraining effects as much as explanation fidelity (the authors themselves observe rising accuracy in some cases but keep the metric).
- They acknowledge Destination Port / TCP_WIN_SCALE_IN bias but continue to use the uncorrected datasets; conclusions inherit CICIDS-2017 labeling artifacts documented by Engelen et al. (this batch, paper 3).
- Framing is analyst trust/time savings, but no analyst or user study of any kind.

---

## 2. New Directions in Automated Traffic Analysis (nPrint / nPrintML)
**Holland, Schmitt, Feamster, Mittal - ACM CCS 2021. arXiv:2008.02695. Read: full text.**

### Setup
- Task: 8 traffic-analysis case studies: active device fingerprinting (vs Nmap), passive OS detection (vs p0f), DTLS application/browser identification, netML IoT malware detection, netML traffic-type identification, netML intrusion detection (CICIDS2017), mobile-app country of origin, streaming-video service identification from SYNs.
- Input representation: **nPrint** - per-packet, bit-level, semantically aligned binary map; every header bit is a feature taking {-1, 0, 1} (-1 = header absent), internal padding for alignment, optional payload bytes; multi-packet samples are concatenations. Design requirements: complete, constant-size, inherently normalized, aligned.
- Model: AutoGluon-Tabular AutoML (RF, ExtraTrees, KNN, LightGBM, CatBoost, NN, weighted ensemble); AutoML does model selection + hyperparameter tuning.
- Datasets: Network Device Dataset [Holland et al.], CICIDS2017 PCAPs (OS detection + netML IDS), DTLS handshakes (MacMillan et al., ~7,000), netML challenge sets (recreated raw traffic), Cross Platform (mobile), Streaming Video Providers. All code and data released.

### How explanation quality is evaluated
**None (no metric).** Interpretability is a *design claim* of the representation: "Alignment gives nPrint a distinct advantage... in that it is interpretable at the bit level." Explanations = per-bit feature importance extracted from the best random-forest model, summed across the packets of a sample, and rendered as heatmaps over semantic header fields (Figures 4, 5, 8). Validation is narrative:
- OS detection: "the most important features are in the time-to-live (TTL) field and, to a lesser degree, the IPID field. These results confirm past observations that TTL IPID can be used for OS detection" [refs 7, 33]; window size + TCP options likewise consistent with p0f lore.
- Device fingerprinting: TCP source port importance was traced (manually) to Nmap's port-scan behavior - IoT devices each expose a distinctive open port; also IP TTL and window size.
- DTLS: header lengths and DTLS payload drive performance.
- Control experiments validate the *model* (not the explanation): train on device pairs / test on other devices sharing the OS (perfect separation via initial TTL); initial-TTL-only filtering to exclude network-location memorization.

### Ground truth used
**None.** The correspondence with p0f/Nmap fingerprinting folklore is an informal post-hoc plausibility check, not a scored comparison against an expert-nominated feature set.

### Key numbers
- Passive OS detection on CICIDS2017: 99.5-99.9 balanced accuracy with 1-100 packets; p0f precision ~1.0 but recall 0.00-0.05 with single packets (0.65-0.88 at 100 packets); nPrintML with 1 packet beats p0f with 100.
- Active device fingerprinting: 95.4 balanced accuracy / 99.7 ROC AUC vs AutoML-enhanced Nmap 92.9 macro-F1.
- DTLS (browser, application): 99.8% accuracy, perfect ROC AUC - matches prior hand-engineered features on a *harder* label set; works with UDP headers alone.
- netML: beats leaderboard's hand-tuned models in all tasks but one.
- Streaming video: 98.4 balanced accuracy from 50 SYN packets.
- Systems: ~1.5M packets/min single-thread; ~8 Gbps live with 16 queues/processes; 295-310 KB constant memory.

### Stated limitations / future work (near-verbatim)
- "Many problems, such as capturing temporal relationships across multiple traffic flows, and running nPrintML on longer traffic sequences remain unsolved and unexplored."
- Conclusion: "many open problems exist such as automated timeseries analysis and classification involving multiple flows. nPrint should ultimately be applied to a larger set of classification problems."
- Supervised-only: "there is opportunity for future work in combining the nPrint representation with unsupervised learning techniques."
- netML recreation caveat: "we do not necessarily have the same training and testing split... our results do not reflect a perfect comparison."
- Implementation bottlenecks (CSV output, libpcap) "left... for future work."

### My gap observations
- Bit-level interpretability is a headline design property yet never evaluated: no faithfulness, stability, or cross-method check of the RF impurity/permutation importances; the single best model's importances are implicitly treated as the truth.
- The TCP-source-port finding is a *shortcut discovered by accident*: Nmap's pre-scan chooses an open port per IoT device, so the "important feature" encodes a data-collection artifact, exactly the phenomenon Engelen et al. and the SoK tutorial warn about. The paper reports it as an insight; there is no systematic shortcut audit, and the classifier keeps the shortcut.
- OS-detection ground truth reduces to consistency with p0f/Nmap folklore - the very tools nPrintML claims to beat; circular as validation.
- Summing importance across a 21- or 43-packet concatenation erases which packet/position carried the signal - the heatmaps overstate spatial (header) attribution and hide temporal attribution.
- Relies on CICIDS2017 traffic (flawed per Engelen et al.) for two case studies.
- A complete, aligned representation makes the *explanation* space enormous (thousands of bit features); no discussion of how an analyst consumes per-bit importances beyond the aggregate heatmap.

---

## 3. Troubleshooting an Intrusion Detection Dataset: the CICIDS2017 Case Study
**Engelen, Rimmer, Joosen - IEEE S&P Workshops (WTMC) 2021. Read: full text (DistriNet PDF).**

### Setup
- Task: audit and correction of the CICIDS2017 dataset creation pipeline (attack simulation, flow construction, labelling, feature extraction, ML benchmarking); RF benchmarks on Original vs Intermediate (TCP fixes) vs Final (payload filter) dataset versions; 75/25 split. Regenerated dataset + corrected CICFlowMeter released (downloads.distrinet-research.be/WTMC2021).
- Input representation: bidirectional 5-tuple flows, 80+ CICFlowMeter statistical features.

### Findings (dataset defects)
- **TCP "appendices"**: CICFlowMeter terminates a TCP flow at the *first* FIN (violates RFC 793) → leftover ACK/FIN fragments become separate flows inheriting the attack label. **25.9% of the entire dataset**; up to ~50% for several attack classes. Still present in CSE-CIC-IDS2018.
- Flow-direction swaps after timeouts → attack flows mislabelled benign (labelling relies on direction).
- RST ignored as flow terminator.
- **DoS Hulk misimplemented**: deprecated tool sends `Connection: Close` instead of Keep-Alive, so the server closes connections - "we do not believe this attack class in CICIDS2017 can be used as intended."
- **Labelling by IP pair + time window only**, content never verified → Web Brute Force / XSS flows mostly contain *no forward payload* (attack never executed); Bot: 2/3 of connections rejected; introduced new label "X - Attempted" (447,362 flows) to "decouple intent from effect".
- Attack-tool configuration diversity undocumented.

### How feature importance / explanation-adjacent evaluation is done
Not an XAI paper; RF feature importance is used as a **diagnostic instrument for shortcut learning**, validated by expert semantic judgment plus dataset intervention:
- "We apply extensive feature importance measurements for the RF classifier... in all cases these features do not have any semantic connection with the intended malicious activity, but rather stem from the specifics of the used attack tools."
- Shortcut features for separating appendices between classes: Fwd Header Len, Total Fwd Pkt, Min Seg Size Fwd, Init Win bytes Fwd; appendices vs regular flows: SYN Flag Count, Bwd Pkt Len Mean. "The presence of RST packets was a learned shortcut for Bot traffic."
- After correction: "the model starts to learn actually relevant features, such as Inter-packet arrival time. Given that a DoS Slowhttptest attack sends intermittent fragmented HTTP packets, this feature is a strong indicator of this type of attack, and is something a human operator would look for as well."
- Recommendation: "we recommend analyzing the importance of various features used in prediction as a sanity check for any feature-based classifier"; "Class-based metrics, feature importance analysis and manual investigation of mispredictions are crucial."

### Ground truth used
**human_expert (informal)** - the authors' domain knowledge of attack mechanics is the reference for judging whether important features are semantically connected to each attack, reinforced by knowledge of the data-generation pipeline (artifacts known by construction) and by intervening on the dataset and observing importance shift. No formal nominated-list metric.

### Key numbers
- >20% of traffic traces reconstructed or relabelled; appendices 25.9%.
- Aggregate RF metrics identical across versions (accuracy/weighted P/R/F1 = 0.99) while per-class F1 changes drastically: Web XSS 0.18→0.79, Bot 0.60→0.99, Web Brute Force 0.77→0.95, Heartbleed 0.77→0.93, Infiltration 0.81→0.91, Web SQL 0.11→0.00 (12 traces left), PortScan 0.99→0.97. "Analyzing the imbalanced dataset at the level of aggregated ML metrics is inadequate."

### Stated limitations / future work (near-verbatim)
- Direction-swap phenomenon "out of scope for this work" (see extended docs).
- "Results of the analysis might differ based on the used ML model."
- "Reliable detection of shortcut learning is still an open research problem."
- Attack diversity: "We are not aware whether the attack tools were used with a certain fixed configuration or with varying parameters" - recommend combining tools/configurations.
- "As this dichotomy [intent vs effect] applies to many security datasets, future research should investigate its other possible sources and devise appropriate practices."
- CSE-CIC-IDS2018 "also revealed errors in flow construction. We strongly recommend to further analyze this dataset."

### My gap observations
- This paper performs, informally, exactly the expert-grounded feature-relevance validation missing from XAI-for-NTC papers - but with a single model, no quantitative "semantic connection" metric, and no repeatable protocol.
- Direct blast radius for XAI evaluation: E-XAI, nPrint, DeepAID (this batch) and most of the field evaluate explanations of models trained on the *uncorrected* CICIDS2017/2018; with 25.9% artifact flows and shortcut features dominating importance, "descriptive accuracy"-style proxies will reward explanations that faithfully point at artifacts.
- The Original-vs-Final dataset pair is an unexploited natural benchmark: known-by-construction artifacts (appendix signatures, RST-for-Bot) could serve as ground-truth targets to test whether an XAI method surfaces them; nobody in this batch (or, to my knowledge, the field) uses it that way.
- Demonstrates that aggregate accuracy is blind to 25%+ label noise - undercuts any XAI evaluation that treats the model's accuracy as evidence the model (and hence its explanations) are meaningful.

---

## 4. Evaluating Explainable AI for Deep Learning-Based Network Intrusion Detection System Alert Classification
**Kalakoti, Vaarandi, Bahşi, Nõmm - ICISSP 2025. arXiv:2506.07882. Read: full text.**

### Setup
- Task: binary classification of NIDS **alert groups** (important vs irrelevant) for SOC triage - alert prioritization, not raw traffic classification.
- Dataset: real-world Suricata alert dataset from the TalTech SOC (Estonia), 60 days (Jan-Mar 2022), 45,339 external / 4,401 internal hosts; alert groups produced by the CSCAS stream-clustering algorithm; human-labeled important/irrelevant. Balanced subsample: 10,000 per class, 80/20 split, min-max normalized.
- Input representation: tabular alert-group features - SignatureID, SignatureMatchesPerDay, AlertCount, Proto, ports, Similarity, SCAS inlier/outlier label, and 34 per-attribute similarity features (IPs/SignatureText/Timestamp dropped).
- Model: LSTM (Ray Tune RandomSearch; softmax output), >99.5% accuracy; test confusion 2005+1980 correct of 4,000, 14 FPs.
- XAI methods: LIME, SHAP (DeepExplainer), Integrated Gradients, DeepLIFT (Captum).

### How explanation quality is evaluated (quotes)
Quantitative framework over 2,000 test points, four criteria / six metrics, plus pairwise Wilcoxon signed-rank tests:
- **Faithfulness**: "High Faithfulness Correlation" (Bhatt et al. 2020) - correlation between summed attributions of random feature subsets and the model-output change when those features are replaced by a baseline; "Monotonicity" (Luss et al.).
- **Robustness**: "Max Sensitivity" (Bhatt et al.) - max explanation distance among neighbors within radius r=0.1 (Euclidean).
- **Complexity**: "Low Complexity" - entropy of the fractional attribution distribution.
- **Reliability**: "Relevance Mass Accuracy (RMA)" and "Relevance Rank Accuracy (RRA)" from Arras et al. (CLEVR-XAI), computed against a **ground-truth mask**: "the Ground truth mask ([0,1]) was determined by the features SOC Analysts identified" - five features nominated by TalTech SOC analysts: SignatureMatchesPerDay, Similarity, SCAS, SignatureID, SignatureIDSimilarity (Table 1). "These features act as benchmarking reference features in our research to evaluate how well our XAI algorithms perform."
- Qualitative: SHAP global summary top features "align with those identified by human expert SOC analysts"; "The strong alignment between these analyst-identified features and those obtained by the XAI methods validates their effectiveness."

### Ground truth used
**human_expert** - a formal, pre-specified 5-feature list nominated by SOC analysts, used as the GT mask for RRA/RMA. (The cleanest ground-truth usage in this batch.)

### Key numbers
- DeepLIFT best on nearly everything: faithfulness correlation 0.7559±0.2681 (vs LIME 0.4209±0.1835, SHAP 0.3959±0.2928, IG 0.1761±0.3815); monotonicity 78.35% (IG 73.70, SHAP 64.45, LIME 59.55); max sensitivity 0.0008±0.0004; RMA 0.7812±25.2805; RRA 0.6754±0.0897.
- IG wins complexity (2.1745±0.4134; DeepLIFT 2.2635).
- All pairwise Wilcoxon comparisons significant (p<0.001); DeepLIFT better on faithfulness, sensitivity, RMA, RRA in every pairwise test.

### Stated limitations / future work
**None stated.** Section 5 is titled "Conclusions and Future work" but contains no explicit limitation or future-work sentence - only a summary of contributions. (Notable in itself for an XAI *evaluation* paper.)

### My gap observations
- The reported RMA standard deviations (LIME ±9.70, SHAP ±3.83, DeepLIFT ±25.28) are impossible for a mass-ratio metric bounded in [0,1] - indicates signed/unnormalized attributions in the denominator or a computation bug; unremarked in the paper, and it undermines the headline "reliability" ranking.
- The expert ground truth is a *global, task-level* feature list applied as the mask for every *local* explanation: a faithful local explanation that legitimately relies on other features (for a specific alert) is penalized. The framework therefore measures plausibility-to-experts, not correctness, on the reliability axis - while simultaneously measuring model-faithfulness on another axis, with no way to reconcile disagreement between them.
- Potential circularity/label leakage: the SCAS feature is the output of the stream-clustering algorithm that structured (and plausibly guided) the human labeling; experts nominating SCAS and explanations highlighting SCAS partly re-derive the labeling pipeline.
- LSTM on non-sequential tabular features is unmotivated (no sequence dimension is described); a recurrent model choice mostly matters here because IG/DeepLIFT require differentiability.
- Near-saturated classifier (99.5%+) on a balanced 20k subsample - attribution differences in this regime may not transfer to realistic imbalanced alert streams.
- Single model, single (private) dataset; no cross-model or cross-dataset replication; no analyst-in-the-loop usability evaluation despite SOC framing.

---

## 5. SoK: Explainable Machine Learning for Computer Security Applications
**Nadeem, Vos, Cao, Pajola, Dieck, Baumgartner, Verwer - IEEE EuroS&P 2023. arXiv:2208.10605. Read: full text.**

### Setup
- Systematization of 300+ papers (75 selected for taxonomy) using XAI for cyber security, 2014-2022. Taxonomy: 3 stakeholders (model users, model designers, adversaries) x 4 objectives (XAI-enabled user assistance; XAI-enabled model verification; explanation verification & robustness; offensive use of explanations), plus target domain, model class, explainer class code books.
- Includes an original tutorial: debugging a botnet NetFlow detector (CTU-13; GBM balanced accuracy 86.4%, 9-node decision tree 83.6%) with SHAP/LIME/LEMNA; 140 explained NetFlows (50 TP, 50 TN, 20 FP, 20 FN). Pipeline released (github.com/tudelft-cda-lab/xai-pipeline).

### Field-level findings on explanation evaluation (the paper's core evidence)
- "User studies for explanation evaluation are conducted in only 14% of the cases" - "with a median of 8 participants" (Takeaway 2). 58% of works are user-assistance, yet users are excluded from evaluation.
- Only 22.3% of the literature focuses on model & explanation verification; only 25.9% adopt interpretable models.
- Takeaway 1: "Visualization is not equivalent to effective explanation."
- Takeaway 4: "it is vital for safety-critical applications to establish an equivalence relation between the model and its explainer. However, this is not yet common practice."
- Fidelity evaluation options catalogued: perturbation impact (Wickramasinghe et al.); **synthetic ground truth via injected backdoor triggers** (Lin et al.: "These backdoor triggers serve as ground truth... a faithful explainer must be able to identify them"); Warnecke et al./Ganz et al. criteria (descriptive accuracy, sparsity, completeness, stability, efficiency, robustness) cited as "excellent starting points".
- Explanation disagreement: 25.5% disagreement rate between top-3 SHAP and LIME features (Krishna et al. metric) on their 140 NetFlows; "explanations based on feature importance often disagree on the same model prediction... suggesting a mismatch between the explanations and what the model actually does."
- Post-hoc risks: fairwashing; Adebayo et al. sanity failures; qualitative analyses "only investigate the happy flows (successful explanations)... cherry-picking."

### Tutorial (NTC-relevant demonstration)
- SHAP summary + decision tree reveal reliance on Dport, **Sport, StartTime**. StartTime is Unix time ("the model learns to predict when a Netflow is generated, rather than the Netflow's maliciousness" - perturbing start time 4 weeks earlier flips 65% malicious → 94% benign). Sport: CTU-13 VMs use a small port subset - "a common shortcoming of lab-collected datasets". Removing both drops balanced accuracy 86.4→74.4 (GBM), 83.6→58.1 (DT): "we argue that this is an improvement since the faulty features were making the classifier appear performant."
- Takeaway 7: "Feature importance explanations do not provide the full picture in isolation. Instead, actionable insights can be obtained by combining the input data together with post-hoc explanations." (FP traced to State=54/SrcBytes=186 appearing almost only in malicious training rows; FN traced to RDP port 3389 being benign-dominated in CTU-13 - "sampling and confounding biases in the CTU-13 dataset".)
- Takeaway 8: LIME's near-zero weights mean low local confidence, not unimportance - "an unsuspecting analyst might draw misleading conclusions."

### Ground truth used
**None** (as an SoK it evaluates no explanation-quality metric of its own; the tutorial's spurious-feature calls rest on the authors' domain reasoning - Unix timestamps, OS-assigned ephemeral ports - confirmed via interventions: feature perturbation and retrain-without-feature. It catalogues Lin et al.'s backdoor-injection as the synthetic-GT approach in the literature.)

### Stated limitations / future work (near-verbatim)
- Tutorial scope: "We recognize that the tutorial discusses a simple case study and that the features may have more complex relationships in reality. However, even this simple case occurs frequently in practice."
- Literature coverage: "Since it is impossible to cover all the available literature in the limited space, we chose representative works from each problem area."
- Open problems (§9): "User study crisis" (develop proxy tasks/metrics, artifact-evaluation peer review of usability); "Robustness vs. interpretability" (role of XAI in tamper-resistant feature selection "remains unclear"); "Price of interpretability" (surrogates "must be certifiably equivalent... for the evaluation to be meaningful"); "Privacy-preserving explanations" ("research on limiting these abuses is almost non-existent").

### My gap observations
- Provides the strongest field-level quantification of the evaluation vacuum (14% user studies; 22.3% verification) - directly citable evidence for the ground-truth gap thesis.
- With a measured 25.5% SHAP/LIME top-3 disagreement on NetFlows, there is no arbiter without ground truth; the SoK stops at recommending interpretable-by-design models rather than proposing a ground-truth evaluation protocol.
- Its own tutorial - the most NTC-specific artifact - still validates explanations by expert plausibility plus ad hoc interventions; the interventions (timestamp shift, feature removal + retrain) are a nascent interventional protocol but are not formalized into reusable metrics.
- The catalogued backdoor-trigger idea (synthetic ground truth) is never connected to network traffic; porting it to NTC (injected traffic artifacts with known signatures) is an obvious open niche.
- Their spurious-feature findings (StartTime, Sport in CTU-13; cf. Dport debate) jointly with Engelen et al. imply that *plausibility-based* XAI validation in NTC is systematically confounded: the datasets themselves make wrong features genuinely predictive.

---

## 6. DeepAID: Interpreting and Improving Deep Learning-based Anomaly Detection in Security Applications
**Han et al. (Tsinghua) - ACM CCS 2021. arXiv:2109.11495. Read: full text.**

### Setup
- Task: local interpretation of **unsupervised** DL anomaly detection across three data types, instantiated on: Kitsune (network intrusion; ensemble autoencoders over 100+ per-packet statistics), DeepLog (HDFS log-key sequences; LSTM prediction), GLGV (APT lateral movement; graph embeddings). Plus **Distiller**: an FSM-based extension storing interpretation→feedback rules for human-in-the-loop detection (tabular only).
- Interpretation formulation: interpretation of anomaly x◦ = difference from a searched **reference x\*** - "solving an optimization problem which searches a normal 'reference'", argmin ||x\*−x◦||2 + λ||x\*−x◦||0 s.t. E_R(x\*, f_R(x\*)) < t_R (reference must be classified normal), solved via gradient descent (Adam) with ReLU-bounded loss, tanh change-of-variables, iterative dimension pruning to K dims. White-box (gradients), no surrogate.
- Requirements they posit for security-domain interpreters: "(1) Fidelity... (2) Conciseness... (3) Stability... (4) Robustness... (5) Efficiency."
- Baselines: LIME, LEMNA, COIN, CADE, DeepLIFT, and S.R.T.D. (select reference directly from training data). Supervised baselines run by "approximat[ing] the decision boundary of the anomaly detection with a supervised DNN trained with additionally sampled anomalies."

### How explanation quality is evaluated (quotes)
- **Fidelity(-conciseness)**: "an indicator similar to [LEMNA] called Label Flipping Rate (LFR) as the ratio of abnormal data that becomes normal after being replaced by interpretation results" - LFR vs % dimensions used curves (Kitsune, DeepLog).
- **Stability**: mean Jaccard Similarity of important-dimension index sets across two runs with identical settings.
- **Robustness to noise**: JS before/after Gaussian noise N(0, 0.01²) (tabular only).
- **Robustness to adaptive attacks**: their own "optimization-based attack" (perturb anomaly to maximize change in searched reference, ||perturbation|| < δa) and "distance-based attacks" (Appendix D); measured by JS before/after attack; mitigation by initializing reference from neighborhood (I.R.N.).
- **Efficiency**: runtime to interpret 2,000 anomalies.
- **Use-case validation**: Table 3 case studies on anomalies with known ground-truth causes (Mirai remote command execution; ARP scan) - K=5 features listed with an "Expert's Understanding" column; "Since (a) and (b)... are both interpretable and reasonable for experts, we can draw the conclusion that DL model has learned the expected well-known rules." Similar 2-case DeepLog analysis. Debugging case: interpretations of extreme-RMSE FPs exposed morbidly large covariance/pcc features → real bug (approximation algorithm) in Kitsune's feature extractor.

### Ground truth used
**None** for the quantitative metrics (LFR is a replacement/deletion proxy; JS is consistency; runtime). The case studies use anomalies whose *attack labels* are known and check expert plausibility of the interpretation - informal, unquantified, a handful of examples.

### Key numbers
- "DeepAID with 10% dimensions exceeds others by >50%" on LFR (Kitsune); supervised interpreters show low fidelity in the unsupervised setting; S.R.T.D. poor with few dimensions.
- Stability JS ≈ 1.0 for DeepAID/DeepLIFT; approximation/perturbation methods poor "due to their random sampling/perturbation".
- Adversarial: JS > 0.91 at δa = 0.2 without defense; I.R.N. (σn ≥ 0.02) mitigates most attack effect; I.R.N. stability cost small (JS > 0.95 at σn = 0.04).
- Efficiency: "DeepAID and DeepLIFT are at least two orders of magnitude faster than the other methods."
- Debugging use case: fixing the discovered cov/pcc extraction bug cut Kitsune FPs by 94.92% (TPs −0.17%).
- Distiller (Kitsune data + CIC-IDS2017): rule-match f1 ≈ 0.999; generalization f1-macro* up to 0.9736 (beats RF/MLP by 10-20%); unknown-attack accuracy (UACC) 0.28 (raw Kitsune) → 0.98-1.0; FPR 8%→0% with 10 FP rules; retraining 30% DeepAID-selected samples reduces more FPs than 60% random.

### Stated limitations / future work (Section 7, near-verbatim)
- "First, the adversarial robustness evaluation and claim of DeepAID are mainly against optimization-based and distance-based attacks... There are other target attacks that may fail DeepAID, such as poisoning the original models (as DeepAID is highly faithful to model decisions), hijacking the search process to generate false references, and crafting anomalies extremely or equally far from the decision boundary in many dimensions to force interpretations to use more features (spoiling the conciseness)."
- "Second, hyper-parameters of DeepAID are configured empirically... Future work can develop more systematic strategies."
- "Third, we implement Distiller only for tabular data."
- "Fourth, the practical effectiveness of DeepAID may depend on the expert knowledge of operators, since they do not have prior knowledge of anomalies in the unsupervised setting. Future work can investigate the impact of knowledge level and look into approaches to relax the requirement of expert knowledge."

### My gap observations
- LFR certifies *counterfactual sufficiency with respect to the model*: replacing flagged dimensions with reference values flips the model's label. It says nothing about whether those dimensions correspond to the actual attack mechanism; a reference reached via off-manifold values would score perfectly. (Same proxy family as deletion curves, inverted.)
- Expert validation is 2-3 hand-picked cases per system with a prose "Expert's Understanding" column - precisely the happy-flow/cherry-picking pattern the SoK (paper 5) warns against; no inter-expert agreement, no negative controls.
- The supervised baselines were run through an author-constructed surrogate supervised DNN (trained on artificially sampled anomalies); their measured "low fidelity" partly reflects that surrogate construction, so the headline superiority over LIME/LEMNA/DeepLIFT is not a like-for-like comparison.
- "Human-readable" and operator-centric claims are never tested with humans; Distiller's "expert feedback" experiments explicitly substitute dataset class labels for real feedback ("human feedback is experience-dependent and very subjective. For fairness and simplicity, we select two well-labeled multi-class datasets").
- Robustness evaluated only on tabular Kitsune (time-series discrete), and the noise model (Gaussian on normalized features) again ignores traffic-feature semantics.
- Uses Kitsune's Mirai captures and CIC-IDS2017 - the latter with the defects documented by Engelen et al. (paper 3).

---

## Batch-level synthesis (for the journal paper's gap analysis)

1. **Proxy metrics dominate; ground truth is almost absent.** E-XAI (6 metrics) and DeepAID (LFR/JS/runtime) evaluate explanations only against the model itself (deletion, label-flipping, perturbation sensitivity, run-to-run consistency, speed). nPrint shows importance heatmaps with no evaluation at all. The single formal ground-truth usage in the batch is Kalakoti et al.'s 5-feature SOC-analyst mask (RRA/RMA) - and it applies a *global* expert list to *local* explanations and contains an apparent metric bug (RMA σ up to 25 on a [0,1] metric).
2. **Informal expert plausibility is the de facto standard** (nPrint's fingerprinting-folklore cross-check; DeepAID's case tables; the SoK tutorial) - exactly the cherry-picking-prone practice the SoK criticizes, and never quantified (no agreement rates, no negative controls).
3. **The SoK quantifies the vacuum**: 14% of security-XAI works run user studies (median n=8); 22.3% do model/explanation verification; SHAP-vs-LIME top-3 disagreement measured at 25.5% on NetFlows with no arbiter available.
4. **Dataset integrity contaminates all proxy evaluations.** Engelen et al.: 25.9% of CICIDS2017 flows are TCP-appendix artifacts, labels assigned by IP+time only, shortcut features (RST for Bot, header-length quirks) dominate RF importance, and aggregate metrics (0.99 F1) completely mask it. E-XAI, nPrint, and DeepAID all evaluate on CICIDS2017/NSL-KDD/CTU-13-class data - so "faithful" explanations of these models are faithful to artifacts, and plausibility-based validation is confounded because wrong features are genuinely predictive in-lab.
5. **Unexploited ground-truth opportunities visible from this batch**: (a) the corrected-vs-original CICIDS2017 pair (artifacts known by construction) as a recovery benchmark for XAI methods; (b) backdoor/trigger injection (Lin et al., cited in SoK) never ported to traffic; (c) known-mechanism attacks (Slowhttptest inter-arrival timing, Mirai scan signatures) as expert-verifiable per-class feature sets; (d) E-XAI's biased-single-feature robustness models are architecturally known-truth classifiers that could score explanation correctness but are only used for attack demos.
6. **Statistical practice is thin**: E-XAI's Wilcoxon tests validate classifier accuracies, not XAI-metric differences; Kalakoti et al. do test XAI metrics pairwise (the exception); DeepAID and nPrint report no significance testing for explanation comparisons.
7. **Nobody closes the loop with humans**: across all six papers, zero controlled user studies with security analysts, despite every paper (except Engelen et al.) motivating itself by analyst trust/workload.

### Files
- Notes: `C:\Users\nakul\OneDrive\Desktop\Academics\xai-ntc-research\corpus\notes\deepread-batch-2.md`
- Extracted texts kept for quoting: `tmp-exai.txt`, `tmp-nprint.txt`, `tmp-cicids-troubleshoot.txt`, `tmp-nids-alert-xai.txt`, `tmp-sok-xai-security.txt`, `tmp-deepaid.txt` (same directory).
