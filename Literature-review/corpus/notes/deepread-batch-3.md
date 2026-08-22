# Deep-Read Notes - Batch 3

Reader focus: (1) how explanation quality is EVALUATED, (2) LIMITATIONS / FUTURE WORK.
All six papers read from full PDF text extractions (tmp-*.txt in this folder).

---

## 1. BiasSeeker - "Bias in the Shadows: Explore Shortcuts in Encrypted Network Traffic Classification"
- **ID:** arXiv:2601.10180 (2026). Wang, Xie, Wang, Cui - Tsinghua.
- **Read depth:** full text.

### Task / setup
- Semi-automated, **model-agnostic, data-centric** framework for detecting dataset-specific shortcut features in encrypted NTC, before any model is trained. Positioned explicitly against model-dependent XAI diagnosis (they cite Trustee as the model-dependent alternative and quote Mink et al. 2023: "explanations provided by interpretable models are often not inherently easier to understand").
- 3 tasks x 19 public datasets: VPN (NordVPN/SuperVPN/Surfshark/TurboVPN/ISCXVPN2016), malware (CIC-AndMal2017 x4, USTC-TFC2016), app classification (CrossPlatform Android/iOS, CrossNet2021, CSTNET-TLS1.3, CipherSpectrum).
- Test models for mitigation: **NetMamba** (pre-trained SSM; first 5 packets/flow, 80 header + 240 payload bytes) and a **decision tree**.

### Method (pipeline)
1. tshark raw field extraction → integer encoding (IP→32-bit ints, SNI→dictionary indices, floats preserved for temporal).
2. **Adjusted Mutual Information (AMI)** between every packet-level field and label; per-packet granularity; constant/low-entropy/trivial fields removed first.
3. Top-k AMI fields = shortcut candidates (they argue high AMI is *necessary but not sufficient*: if a model exploits Xj as shortcut then I(Xj;Y)>0).
4. Domain-knowledge categorization into: **Data-Leakage Identifiers** (src/dst IP, ports = "SII", SNI), **Relative Artifacts** (seq/ack numbers, TCP timestamp options), **Task-Agnostic Fields** (window size, checksum, TTL).
5. Category-specific validation: ΔAMI = AMI(absolute) − AMI(relative transform); class-conditional KL divergence of feature distributions across datasets (e.g., TCP window size KL = 2.36 across CrossNet-A/B vs TCP length 0.06, TCP flags 0.53, IP length 0.05).
6. Model-based validation: 3 occlusion strategies - zero padding, relative transformation, random masking - and re-measure NetMamba/DT accuracy (Table III).

### How explanation/detection quality is evaluated
- **No ground truth.** Validation = accuracy deltas under occlusion, self-described as "an **indirect yet practical measurement** of their influence." Plus ΔAMI and KL-divergence statistics, which quantify dataset properties, not detection correctness.
- Findings from Table III: removing SII/SNI consistently drops accuracy (e.g., ISCXVPN2016 NetMamba 0.8847 → 0.7821 with Random SII; Ransomware 0.3905 → 0.2552); relative artifacts and task-agnostic fields have **inconsistent** effects; **accuracy sometimes IMPROVES after occlusion** (e.g., Ransomware NM 0.3905 → 0.4159 with Random TCP/UDP Checksum; USTC-TFC2016 mostly improves) - "we unexpectedly observe that both NTC models achieve accuracy improvements under several occlusion settings," contradicting prior reports (netFound, AppSniffer, NTC-Enigma).

### Stated limitations / future work (near-verbatim)
- "We acknowledge that the final decision still requires human inspection. However, this is a significant improvement over fully manual processes..."
- "Building an automatic shortcut detector is a challenging open problem. We hope our framework provides a structured first step, and we are actively exploring **causal analysis and representation-based criteria** for more automated shortcut diagnosis in future work."
- "Our findings are not intended to be prescriptive or exhaustive but rather to raise awareness. Shortcut detection must be grounded in the specific goals, data properties, and deployment constraints of each use case."
- Takeaway 2: "Shortcut features are not inherently harmful; their impact is highly dataset- and context-dependent."
- Future directions listed: semantic protocol-invariant representations; systematic shortcut detection/mitigation; realistic diverse benchmarks.

### My gap observations (not stated by authors)
- AMI is univariate/first-order: multivariate or interaction shortcuts (combinations of individually low-AMI fields) are invisible; the "necessary condition" argument only holds for marginal dependence.
- No ground truth that flagged features ARE shortcuts: validation is occlusion accuracy deltas, and their own paradoxical result (accuracy improving after removal) shows occlusion deltas are ambiguous evidence - the same ambiguity undermines the validation logic itself.
- No head-to-head comparison with the model-dependent alternative (Trustee) on the same datasets, despite framing against it.
- Packet-level AMI may miss flow-level/sequential shortcuts (they justify per-packet granularity but never test the flow-level blind spot).
- "Semi-automated" = expert-in-the-loop categorization; the human step is exactly where the claimed objectivity gap re-enters.

---

## 2. "Stabilising Explainability Fragility in Cybersecurity AI: The Impact and Mitigation of Multicollinearity in Public Benchmark Datasets"
- **ID:** arXiv:2605.22529 (2026). Vourganas (Netrity Ltd) & Michala (U. Glasgow). ACM-format preprint.
- **Read depth:** full text.

### Task / setup
- IDS binary classification on **UNSW-NB15** (39 numeric of 49 features; 175,341 train / 82,332 test records). Models: LR, XGBoost, RF, MLP, CNN, LSTM, RBF-SVM.
- Claim: multicollinearity in benchmark datasets makes SHAP/LIME attributions non-identifiable and unstable → prior IDS "top features" claims unreliable.

### Method
- **Theorem 1 (Multicollinearity-Induced Experimental Fragility):** if VIF(x_i)→∞, attribution under any linear explanation method is non-identifiable; for VIF>θ, Var(φ_i) ≥ c·(VIF(x_i)−1). Proof via OLS covariance + Schur complement; Part C extends to Kernel SHAP/LIME local linear surrogates (local weighted VIF); TreeSHAP handled by a remark only.
- **Explainability Fragility Score:** Fragility(x_i) = Var(φ_i) / (E[|φ_i|] + ε) over bootstrap resamples (10 runs × 10,000 records).
- Dataset audit: Pearson clusters (15/39 features = 38% in 3 clusters); VIF: is_ftp_login, ct_ftp_cmd, tcprtt = ∞; ackdat/synack ≈ 9×10^15; dloss 5×10^3...
- Mitigations: (a) VIF pruning (VIF>10, |ρ|>0.85); (b) **CAA-Filter** (post-hoc grouping of SHAP values of correlated clusters, mean/max/sum aggregation); (c) **SHARP** (SHAP Stability Regulariser - adds λ·mean-Fragility penalty to training loss, SHAP computed on batches every k epochs).

### How explanation quality is evaluated
- **Stability-only metrics, no correctness ground truth:**
  - "Fragility Scores for each feature" (variance-to-mean ratio of SHAP values across bootstraps);
  - "**Kendall's τ** calculated for comparison of feature importance stability across the top 20 and top 50 features" across bootstrapped explanations.
- Results: VIF pruning raises τ (top-50): LR 0.37→0.91, XGBoost 0.44→0.68, RF 0.11→0.51, CNN 0.04→0.34, while predictive metrics drop ≤2.2% (CNN 6.8%). CAA-Filter on XGBoost: τ 0.44→0.53 (vs 0.68 pruned). SHARP on LR (λ=0.5): τ 0.50→0.62 AND accuracy 80.7%→89.8%, ROC AUC 0.750→0.976 ("Not only is there no accuracy sacrifice... in fact there is a performance boost"). SHARP on MLP: τ 0.82→0.89, accuracy flat. λ-ablation: monotonic stability gain, performance decays exponentially for λ>1.
- They cite Rawal et al., "Evaluating Model Explanations without Ground Truth" (FAccT 2025) for the differentiable-attribution proxy - an explicit acknowledgment that the field lacks ground truth.

### Stated limitations / future work (near-verbatim)
- CAA-Filter: "The limitation it inherently introduces is the fact that explanations cannot be uniquely attributed to a single feature, but rather a cluster of features. Additionally, it remains possible that some instability is present, especially when the max absolute SHAP filtering approach is selected."
- SEM latent-construct replacement "is beyond the scope of this work, and would be an excellent future direction."
- Future work list: "Replicate the experimental steps of the multicollinearity audit for further IDS benchmarks such as CICIDS2017, Bot-IoT, and TON_IoT, thus evaluating the generalisation claims; Explore other causal inference approaches...; Integrate fragility auditing into open-source benchmarking toolkits...; Assess the broader impact of multicollinearity on proposed fairness metrics and adversarial robustness; Combine CAA-Filtering and SHARP at CAA cluster level...; Extend SHARP to support online monitoring."

### My gap observations
- **Stability ≠ correctness:** a stably *wrong* attribution gets a perfect Fragility Score and τ=1. SHARP explicitly optimizes the evaluation metric (Goodhart risk); nothing checks the stabilized attributions point at causally meaningful features.
- Single dataset (UNSW-NB15) despite "generalisation" framing; engineered tabular flow features only - nothing about raw-bytes/sequence NTC models where multicollinearity is structural (adjacent bytes).
- The LR SHARP result (accuracy +9 points, AUC 0.750→0.976 from a *stability* penalty) is surprising and un-investigated; possible optimization/implementation confound.
- Fragility conflates SHAP estimation noise (KernelExplainer sampling variance) with multicollinearity-induced variance - no ablation to separate them.
- Their secondary metric "Kendall's τ of top-20 fragile features, lower = better stability" is a confusing inversion, and Table 6/7 interpretation looks shaky (LR control fragile-τ 0.90 vs hypothesis 0.30 called an improvement).
- Preprint with many typos; not yet peer-reviewed; theorem's constant c is model/eval-dependent and never estimated empirically.

---

## 3. "One Task to Rule Them All: A Closer Look at Traffic Classification Generalizability"
- **ID:** arXiv:2507.06430 (2025). Akbari, Zhou, Salahuddin, Limam, Boutaba (Waterloo) + Mathieu, Moteau, Tuffin (Orange).
- **Read depth:** full text.
- **NOTE: this is not an XAI paper - no explanation method is applied.** It is in-batch because it motivates XAI from the generalizability side and provides the cross-dataset framework that XAI evaluation in NTC lacks.

### Task / setup
- Revisits DFattack (1D-CNN, packet directions, Undefended Tor 95 classes), Flowpic (2D-CNN, 32x32 time-size histograms, ISCX-Flowpic), UWTransformer (3-channel time series of first 30/32 packets, Orange). Cross-applies each method to the others' datasets.
- Builds a **generalizability test framework**: two independently collected real-world TLS datasets from Oct 2021 (CESNET-25 selection of CESNET-TLS, 1M flows; Orange June/October) aligned by CESNET's SNI labeling function to the **same 25-class ESNI-identification task** - "real-world distribution shift, while excluding concept drift."
- Up to 19 classifiers: 5 transformer architectures (60k-8.2M params), XGBoost, 1-NN, feature-ablated variants.

### Key results
- Each method excels only on its own original dataset: DFattack 0.98 on Undefended vs 0.71 on Orange; Flowpic 0.921 on Aug-ISCX vs 0.65 on Aug-Orange and 0.12-0.63 on Undefended depending on window size; DFattack needs >~200-packet inputs (acc 0.64 at length 50).
- Transferred accuracy CESNET→Orange: best (UWTransformer/Full Model) 0.30-0.35; **1-NN reaches 0.25-0.26** - "a simple 1-Nearest Neighbor classifier's performance is not far behind." XGBoost same-dataset rank 1 (0.9308) but transfer rank 3.
- Higher same-dataset accuracy almost always → higher transferred accuracy; over-parameterized models generalize better; training-process (learning-rate schedule) variance exceeds architecture differences (First Model: constant LR 0.44 val acc vs LR-series 0.85).

### XAI relevance (their words)
- "The models are often unexplainable, so the reasons for their failure are as obscure as the reasons for their success. In the absence of explainability, the only way to assess a model's performance is by performance metrics."
- On netUnicorn/Beltiukov et al.: only after "training a model..., explaining the model using an explainability tool, comparing the learned knowledge with what the model is supposed to learn, and going back three times to recollect data, were they able to pronounce the data shortcut-free. **If what the model should learn is not clear, as is the case in website fingerprinting for example, we believe all datasets should be expected to contain spurious features.**"

### How explanation quality is evaluated
- **None. No XAI method is used.** Evaluation is entirely predictive: same-dataset vs transferred accuracy/F1; a 5-way meaningful-vs-random label-grouping control; reverse-direction transfer check (±0.05).

### Stated limitations (near-verbatim)
- "The necessity for some hyperparameter tuning was clear when applying each method to each new dataset, and the searches could be more exhaustive."
- "tuning some parameters required knowing the labels (i.e., the solution) in advance."
- Results "are indeed the best results seen for each model, and easy to break if different adjustments are made."
- "Some trained models may not have converged, but their training lasted at least 40 epochs."
- Only two datasets exist for the exact same task; representativeness "difficult to verify in practice when p(X,y) is unknown, which includes all practical cases."

### My gap observations
- The paper names lack of explainability as the diagnostic bottleneck yet applies no XAI tooling to its own 19 models - the failure analysis (input-length distributions, class confusion) is manual feature-statistics detective work; an obvious missed opportunity and an implicit indictment of current XAI usability.
- Their framework is, unintentionally, the best available **behavioral testbed for explanation faithfulness in NTC**: if an explanation of a CESNET-trained model identifies transferable (task-related) vs dataset-specific features, that prediction is checkable against Orange transfer results. Nobody has done this.
- "The task-related part of the knowledge learned by models - rather than the dataset-specific part - is not enough for reliable use": this decomposition is exactly what XAI ground-truth evaluation needs to operationalize, and no metric for it exists.

---

## 4. Trustee - "AI/ML for Network Security: The Emperor Has No Clothes"
- **ID:** ACM CCS 2022, DOI 10.1145/3548606.3560609. Jacobs, Beltiukov, Willinger, Ferreira, Gupta, Granville. Best Paper Honorable Mention.
- **Read depth:** full text.

### Task / setup
- **TRUSTEE**: model-agnostic **post-hoc global** explanation - extracts a high-fidelity, low-complexity, stable decision tree from any black-box + training data, plus a "trust report," to detect **underspecification**: (i) shortcut learning, (ii) spurious correlations, (iii) o.o.d. vulnerability.
- Algorithm: imitation-learning teacher-student; inner loop (N=50): uniform subsample (M=30%), CART student, augment dataset with black-box-corrected errors; outer loop (S=10): pick max-fidelity tree, **Top-k pruning** (rank branches by samples classified, keep k), then across S candidates pick the one with **highest mean agreement** (stability).
- Case studies (all reproduced from public artifacts): 1D-CNN VPN/non-VPN (ISCX), RF on CIC-IDS-2017 (Heartbleed), nPrintML AutoML IDS (bit-level features), Kitsune (autoencoder ensemble, Mirai); +3 in tech report (nPrintML OS fingerprinting, Iisy IoT, Pensieve ABR).

### How explanation quality is evaluated
- **Fidelity**: F1 between DT and black-box classifications (R² for regression). Reported 0.99-1.00 on all use cases (Kitsune pruned DT: 0.94).
- **Complexity**: tree size / top-k branches (VPN DT = 3 nodes; unpruned Heartbleed DT = 899 nodes, max 1,491).
- **Stability**: mean pairwise agreement among S candidate DTs; ablation with S=1 over 50 runs shows agreement mostly high but drops to ~80% in some runs - the outer loop exists to filter these.
- **Case-study validation of explanation claims - interventional:**
  - VPN: DT shows 3 bytes (B49/B43/B47) suffice; root cause found by manual dataset inspection - Non-VPN samples keep Ethernet headers, ~90% of VPN don't → byte misalignment; B49 = IP-protocol vs Ethernet-MAC byte. Tampering bytes 43/47/49 → accuracy unchanged (0.955 F1; model finds *alternative* shortcuts); tampering bytes 0-127 → F1 0.398 ("comparable to flipping a fair coin").
  - Heartbleed: DT flags "Bwd Packet Length Max"; generated 1,000 **new realistic o.o.d. attacks** (closing TCP connection between heartbeats) → RF F1 = **0.000** vs 1.000 i.i.d.
  - nPrintML: TTL bits (Kali TTL=64, Win 8.1 TTL=128 collection artifact); iterative feature removal down to tcp_opt alone still gives F1 0.990 (spurious-correlation abundance); **real campus-network deployment** (Suricata-labeled, 12h) → avg F1 0.282, DoS 0.000; port-scan partial success traced to "missing second packet" padding artifact (-1 fill).
  - Kitsune/Mirai: DT shows volume-only features (MAC-IP weights); spacing out ARP floods in the trace drops RMSE into benign range → volume shortcut confirmed, corroborating prior Boxplot criticism.
- Ablations: dataset augmentation reduces tree size ~20% and fidelity +2-3% on complex trees; Top-k ≈ CCP in fidelity/complexity trade-off but with direct user control.

### Stated limitations / future work (near-verbatim)
- "the absence of these instances does not mean that the black-box model can be trusted... proving... that the model does not suffer from the underspecification problem is hard and remains an unsolved problem."
- "rigorously proving that a 'white-box' model extracted from a given black-box model does not provide misleading explanations is an active area of current research."
- "detecting and diagnosing underspecification issues is not a task that is currently automated but requires domain knowledge and great familiarity with the learning problem at hand."
- Re-running yields different DTs due to probabilistic nature: "We leave a careful investigation of this aspect of TRUSTEE and its deeper implications... for future work."
- "our reported findings based on a handful of use cases that are fully reproducible are in no way representative of the existing literature."
- "we need to involve network operators and security experts in **carefully designed user studies** for quantitatively assessing their level of trust."
- Small k "can possibly result in poor fidelity."

### My gap observations
- **High fidelity ≠ complete explanation, demonstrated by their own experiment:** the 3-node VPN DT had perfect F1 fidelity, yet tampering with exactly those 3 bytes left the black-box accuracy unchanged - the black box used *other* shortcuts the DT never showed. Fidelity as an explanation-quality metric is thus provably insufficient, but the paper never elevates this into a critique of its own headline metric.
- Validation is bespoke per use case (manual detective work + custom tampering); there is no reusable quantitative metric of "explanation correctness," and no benchmark with planted/known shortcuts to score Trustee's detection rate or false-negative rate.
- No comparison against alternative global surrogates (Trepan/dtextract fidelity comparison is delegated to the tech report) and no comparison to feature-attribution methods on the same models.
- Agreement/stability threshold and k are user-chosen; explanation quality partly depends on the analyst noticing the right branch - the human is inside the evaluation loop but never measured (they admit user studies are needed).
- All shortcut discoveries are on *broken* models/datasets; nothing shows what Trustee output looks like on a genuinely well-specified NTC model (no negative control).

---

## 5. LEXNet - "A Lightweight, Efficient and Explainable-by-Design CNN for Internet Traffic Classification"
- **ID:** arXiv:2202.05535v4; KDD 2023 (DOI 10.1145/3580305.3599762). Fauvel, Chen, Rossi - Huawei.
- **Read depth:** full text.

### Task / setup
- Encrypted traffic app classification as multivariate time series: input = first 20 packets × (size, direction). Main dataset: **AppClassNet** (commercial-grade, 9.7M flows, 200 classes, labels from a commercial DPI engine); also MIRAGE (100k/40), CESNET-TLS (38M/191), MNIST.
- Architecture: ResNet backbone with new **LERes** blocks (equal-channel-width convs + linear "ghost" feature maps + concatenate shortcut; −19% params, −41% CPU time, 99.3% of accuracy retained) + **LProto** prototype layer (ProtoPNet block minus its 2 conv layers, sigmoid, L2 reg, **variable number of prototypes per class** learned via kurtosis-triggered additions; prototypes size (1,1), projected onto nearest latent training patch of same class).
- Accuracy 89.7% (ResNet 90.4%, ProtoPNet 86.2%); 119k params; CPU 102.7 μs/sample (~10k classifications/s, deployment-driven requirement); learned 1.7±0.1 prototypes/class (340 total vs ProtoPNet's fixed 400).

### How explanation quality is evaluated
- **Illustration:** per-flow prototype regions highlighted on bar charts (e.g., "a small packet of size 44 in position 2 and a descending packet in position 8... characteristic of the class") = application signatures for network experts.
- **"Faithfulness" evaluation (Table 6, computed on the TCP+UDP train set):** treats LEXNet's own prototypes as reference - "the faithful (**by definition**) LEXNet explainability-by-design" - and measures whether post hoc **Grad-CAM** and **SHAP**, applied to the same LEXNet model, recover those (1,1) regions: "**top-protos regions accuracy**" and "**top-10 regions accuracy**". Results: Grad-CAM 8.2% / 38.9%; SHAP 5.9% / 27.4% (LEXNet trivially 100%). Conclusion drawn: post hoc methods are unfaithful; explainability-by-design is necessary.
- **Cost of explainability:** first study quantifying explainability's cost on inference time/size/accuracy - LEXNet 3.6μs GPU / 102.7μs CPU vs plain ResNet+LERes 1.3/20.3 (prototype L2 distances ≈80% of overhead); vs ResNet+Grad-CAM 9.5/278.6; vs ResNet+SHAP 8.3e3/6.8e4.
- Also: negative correlation (−0.24) between #prototypes and class popularity (top-20 apps have 1 prototype → simple explanations).

### Stated limitations / future work (near-verbatim)
- "the explainability-by-design of LEXNet has a cost on the inference time compared to the best performing state-of-the-art CNN ResNet without explainability methods... and **remains an open challenge**." (~80% from L2 distance calculations, "which thus could benefit some optimization").
- Future work: "minimize the impact of the explainability feature on the inference time... by further optimizing the generation of the similarity matrices"; "investigate applications in collaboration with domain experts where LEXNet would be beneficial."
- Production note: explanations proposed as a drift-monitoring signal (consistency of prototype similarity over time) - proposed, not evaluated.

### My gap observations
- **The faithfulness evaluation is circular:** ground truth = the model's own prototype locations, declared faithful "by definition." But the decision also flows through a 340-way FC layer (with negative weights to other classes' prototypes), so a post hoc attribution that spreads relevance beyond the projected prototype patch is not necessarily wrong - the comparison penalizes Grad-CAM/SHAP for disagreeing with an assumption, not for being incorrect. No discussion of this.
- Architectural ground truth is real here (rare in NTC!) but only self-referential: it can only score post hoc methods *on LEXNet*, and the paper never validates that the prototypes themselves align with protocol semantics (no expert scoring, no domain-knowledge check of the 340 prototypes, no comparison to known app signatures).
- Evaluation on the **train** set (Table 6) - prototype projection guarantees train-set patch matches; generalization of explanations to test flows unmeasured.
- Labels come from a commercial DPI engine: label provenance is rule-based, so "explanations" may just recover DPI-rule-adjacent surface features; never discussed.
- "Based on network experts input, we have adopted explanations under the form of class-specific prototypes" - the expert involvement is anecdotal; no user study of interpretability or usefulness.
- No shortcut/artifact audit of AppClassNet (ironic given batch-mates: first-20-packet size/direction may itself carry dataset-specific artifacts).

---

## 6. "Evaluating Explanation Methods for Deep Learning in Security"
- **ID:** IEEE EuroS&P 2020; arXiv:1906.02108. Warnecke, Arp, Wressnegger, Rieck.
- **Read depth:** full text.

### Task / setup
- The canonical security-domain XAI benchmark paper. Six explanation methods - white-box **Gradients, IG, LRP**; black-box **LIME, KernelSHAP, LEMNA** - on four reimplemented DL security systems: **Drebin+** (MLP, Android malware, 129k apps), **Mimicus+** (MLP, PDF malware, 135 features), **DAMD** (CNN on raw Dalvik opcodes, up to 530k features), **VulDeePecker** (LSTM on code-gadget tokens, CWE-119). (No traffic-classification system among them.)
- Motivating check: top-10 feature intersection size (IS) across methods is low (for VulDeePecker "all methods determine different top-10 features") → methods are not interchangeable → criteria needed.

### How explanation quality is evaluated (their six criteria - the field's reference battery)
1. **Descriptive Accuracy (DA):** "As it is difficult to assess the relation between features and a prediction directly, **we follow an indirect strategy** and measure how removing the most relevant features changes the prediction" - deletion curves + AUC. Feature-removal semantics per system: zero-out (Drebin+/Mimicus+), no-op opcode (DAMD), zero embedding (VulDeePecker). Results: IG best (AUC 0.446/0.206/0.499/0.574), LRP close; white-box "up to 48% better on average"; on DAMD only IG/LRP move the classifier at all.
2. **Descriptive Sparsity:** MAZ (mass-around-zero of normalized relevance histogram) + AUC; IG/LRP/Gradients sparsest (LRP: 14 relevant features vs LEMNA: 2,048 on a DAMD sample).
3. **Completeness (security criterion):** can the method produce non-degenerated explanations for ALL inputs? Perturbation-based methods fail when perturbations can't flip the label: on Drebin+ only 31% of benign samples reach even p=5% opposite-class perturbations → ">65% of the whole dataset suffer from degenerated explanations." SHAP returns all-zero explanations on such inputs.
4. **Stability:** average top-k IS across 3 runs. White-box = 1.000 (deterministic); black-box < 0.5 everywhere (SHAP on DAMD: 0.007) - "on average half of the top features do not overlap."
5. **Efficiency:** run-time/sample. LRP on Mimicus+ 1.7×10⁻⁶ s vs LEMNA up to 1 hour for the largest DAMD sample; batch processing gives >16,000× speedups.
6. **Robustness:** **not empirically evaluated** - literature-based assessment only (Zhang et al., Dombrowski et al. white-box attacks; Slack et al. perturbation-distribution attack on LIME/SHAP, "LEMNA... can be attacked likewise"). All methods rated weak.
- Overall recommendation: **IG and LRP** best on all criteria; if black-box access only → LIME, or **model stealing** then white-box (surrogate LRP explanations reach IS≈0.7 on Drebin+, ≈0.55 on Mimicus+ vs original model).
- **Qualitative insights section (no metric):** all four datasets contain artifacts - Mimicus+ count_trailer/count_box_letter "can hardly be related to security"; JavaScript in 88% malicious vs 6% benign docs (evadable single indicator); Drebin+ benign class characterized by touchscreen+launcher+INTERNET artifact triple, while malicious features (SEND_SMS, READ_PHONE_STATE, getSimCountryIso) match FakeInstaller domain knowledge; VulDeePecker highlights semicolons/brackets → "might benefit from... cleansing the training data"; DAMD GoldDream opcode sequence maps to onReceive SMS-interception code, identical across all family members.

### Stated limitations / future work (near-verbatim)
- "the robustness of explanation methods is still not well understood and, similarly to adversarial examples, guarantees and strong defenses have not been established yet."
- "Adapting these attacks seems possible but requires further research on adversarial learning in structured domains"; "the robustness of the methods is difficult to assess and further work is needed to establish a better understanding of this threat."
- DA is admittedly indirect ("it is difficult to assess the relation between features and a prediction directly").
- VulDeePecker insight: "it is still difficult for a human analyst to benefit from the highlighted tokens" (analyst views source code, not tokens; truncation removes essential context).
- "Our study is a first step for integrating explainable learning in security systems."

### My gap observations
- **No ground truth anywhere:** DA is a deletion proxy; deleted-feature inputs are off-manifold (no-op opcodes, zero embeddings), so DA conflates explanation quality with model brittleness to o.o.d. inputs - the paper never controls for this (no retraining-based ROAR-style check).
- The six criteria measure *properties* (sparse, stable, complete, fast) but not *correctness*; a method could win all five measurable criteria while highlighting causally irrelevant features that the model happens to be sensitive to under deletion.
- Qualitative artifact findings (the paper's most influential security payoff) are validated only by informal domain plausibility - no interventional confirmation à la Trustee (e.g., they never retrain Mimicus+ without JavaScript features to confirm the evasion claim).
- The "typical use case: an expert investigates the top-10 features" is asserted, never studied with actual experts; k=10/k=50 are arbitrary.
- No NTC system among the four → the near-universal citation of this paper's IG/LRP recommendation by NTC works is an unverified transfer across input modalities (flow features/raw packets differ from opcodes/tokens).
- Per-system feature-removal semantics differ, so cross-system DA comparisons are not apples-to-apples.

---

## Batch 3 cross-cutting gap synthesis

This batch is the "trust and evaluation" cluster, and it exposes the ground-truth vacuum most clearly:

1. **Ground truth census:** BiasSeeker = none (occlusion deltas); Multicollinearity = none (stability only); One-task = none (no XAI at all); EuroS&P = none (deletion proxy + qualitative plausibility); Trustee = interventional but bespoke, per-case, non-reusable; LEXNet = architectural but circular (its own prototypes "faithful by definition," scored on the train set).
2. **The proxy metrics contradict themselves in-batch:** BiasSeeker finds occlusion sometimes *improves* accuracy; Trustee's perfect-fidelity 3-node DT fails its own tampering test (removing the 3 explained bytes changes nothing). Two of the field's standard proxies (deletion curves, surrogate fidelity) are shown - by their own proponents' data - to be unreliable evidence of explanation correctness.
3. **Stability is the fashionable substitute for correctness** (fragility scores, Kendall's τ, DT agreement, top-k IS across runs) and SHARP even makes it a training objective; none of these can detect a consistently wrong explanation.
4. **The obvious missing benchmark:** no paper plants a *known* shortcut into NTC data and scores whether detectors/explainers find it (interventional ground truth by construction). Trustee's tampering and the netUnicorn loop (cited in One-task) come closest but are one-off diagnostics, not benchmarks. This is the concrete opening for our paper.
5. **Cross-dataset transfer as unexploited faithfulness oracle:** One-task's aligned CESNET/Orange same-task framework could test whether explanation-identified features predict transfer (task-related vs dataset-specific knowledge); nobody connects the two literatures.
6. **Humans are invoked, never measured:** Trustee explicitly defers user studies; LEXNet's expert input is anecdotal; EuroS&P's top-10-analyst use case is assumed; BiasSeeker keeps a human in the loop by design. Zero user studies across the batch.
7. **Modality transfer is assumed:** EuroS&P's IG/LRP recommendation comes from malware/code systems; the multicollinearity theorem from tabular IDS features; both are routinely cited into raw-bytes/sequence NTC without revalidation.
