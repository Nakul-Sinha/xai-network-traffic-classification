# Deep-read notes - Batch 12
Reader: Claude (deep-read subagent), 2026-08-22.
Theme of this batch: ground-truth-based and meta-level evaluation of explanations (shortcut/synthetic/interventional/architectural GT), plus the one NIDS paper (INSOMNIA) that *uses* XAI without evaluating it.

---

## 1. "Will You Find These Shortcuts?" A Protocol for Evaluating the Faithfulness of Input Salience Methods for Text Classification
Bastings, Ebert, Zablotskaia, Sandholm, Filippova (Google Research). EMNLP 2022. arXiv:2111.07367v2. **Read: full text (PDF).**

### What it does
Proposes a 6-step protocol to obtain ground-truth token-importance rankings via **partially synthetic data**: (1) define a lexical shortcut type; (2) augment a real dataset with ~20% synthetic examples in which injected out-of-vocabulary shortcut tokens deterministically set the label; (3) train models on original vs. mixed data; (4) **verify** the shortcut is what the model uses; (5) run salience methods; (6) compare top of ranking to shortcut tokens.

Three shortcut types: **single token (st)**, **token-in-context (tic)** (indicator token only predictive when a context token co-occurs), **ordered pair (op)** (#0...#1 -> label 0; #1...#0 -> label 1). Multi-token shortcuts deliberately mimic realistic artifacts ("3 out of 10" in IMDB reviews per Ross et al. 2021).

Verification step (this is what licenses the ground-truth claim, Sec 2.4):
1. model trained on mixed data must get ~100% accuracy on a fully synthetic test set (measured: min 99.7-99.8%, mean 99.91-99.95%);
2. model trained on original data must be at chance (measured: 50%) on the same synthetic test set - "no other tokens but the shortcut are useful to predict the label in that data."

### Evaluation of explanation quality (metric names, quoted)
- **"Precision@k"**: p@k(s) = sum_i |topk(s,m,x_i) ∩ gtk(x_i)| / (k|D|), k = shortcut size (1 or 2).
- **"Mean rank"**: "how deep, on average, we need to go in a salience ranking to cover all the ground truth tokens."
Ground truth = the injected shortcut tokens (synthetic, behaviorally verified). Random baseline (RAND) included.

### Setup
Datasets: SST2, IMDB, Wikipedia Toxicity (imbalanced, 9% toxic) × 3 shortcuts = 9 dataset variants. Models: biLSTM (GloVe) and BERT. Methods (with config axes): GRAD{p|l}×{l1|l2|mean}; GxI{p|l}; IG{p|l}×{zero|unk/mask|pad}×{100|1000 steps}; LIME{unk|mask|erase}×{100|1000|3000 perturbations}.

### Key numbers
- GRAD-L2 (or L1) for **BERT**: precision ≥ 0.99 on 7/9 dataset-shortcut combos (lowest 0.87 on IMDB:tic); rank 1-2 on Toxicity. Same method ~0.5 precision on 6/9 for LSTM.
- **GxI**: precision 1.0 for LSTM on all st variants, drops to 0.35-0.76 on tic; for BERT 0.29-0.59 (fails).
- IG: number of steps barely matters (<3% change); baseline choice matters a lot for BERT ([MASK]+logits best, still worse than GRAD-L2); IG with zero baseline ≈ GxI exactly.
- LIME: 1000 perturbations >> 100; 3000 adds little; UNK masking > [MASK]; erase worst.
- GRAD-mean (the config used by cited prior work, e.g., Pezeshkpour et al. 2021): 0.28-0.46 precision - explains prior "12-13% accuracy" findings as a configuration artifact.
- All results from **a single model checkpoint and a single run** (stated in Sec 4).

### Stated limitations (Sec 7, near-verbatim)
"We limited ourselves to the most popular salience methods, and left others out of scope. In particular, it would be of interest to evaluate the most recent salience methods ... developed to take feature interactions into account. We also limited this work to the task of English (binary) text classification. Furthermore, we focus on a representative set of shortcuts, but different shortcuts might result in different outcomes. Finally, we limited ourselves to LSTM and BERT based models. Results with different neural components or with models of a different size and/or depth may be different. However, the protocol that we proposed can still be used in those cases. We also note that input salience is only one kind of explanation, and a limited one: it does not reveal the logic of the model, nor does it reveal interactions between input features. It is hardly possible to fully understand why a deep non-linear neural model produced a certain prediction by only looking at input salience scores."

### My gap observations (not stated by authors)
- The ground truth is **behavioral-synthetic**, not architectural: the model is still a black box; the GT claim rests on the two accuracy tests, which establish that shortcut tokens are *sufficient and necessary in the synthetic subset*, but only give a partial-order GT (shortcut tokens should outrank all others) - nothing about the ordering of the remaining tokens.
- Single run/checkpoint: no variance estimates over seeds; salience-method rankings could be seed-sensitive.
- Protocol requires control of training data (retraining on augmented data) - cheap in NLP, but nobody has ported this to flow-based network traffic classification. Injecting deterministic "marker" features/flows into CICIDS-style training data and testing whether SHAP/LIME/IG recover them is a direct, unexploited analog for NTC, and it sidesteps the "no ground truth in tabular traffic" objection.
- Findings transfer poorly across architecture (GxI: LSTM yes, BERT no) - warns against NTC papers that validate an explainer on one model family and reuse it on another.

---

## 2. Order in the Court: Explainable AI Methods Prone to Disagreement
Neely, Schouten, Bleeker, Lucic (U. Amsterdam). ICML 2021 XAI workshop. arXiv:2105.03287v3. **Read: full text (PDF).**

### What it does
Empirically tests the "agreement as evaluation" paradigm (post Jain & Wallace 2019): compute Kendall-τ rank correlation between token-importance rankings of LIME, Integrated Gradients, DeepLIFT, Grad-SHAP, Deep-SHAP and attention-based explanations (raw attention for BiLSTM; attention rollout / attention flow for DistilBERT), on 500 test instances per dataset. Datasets: SST-2, IMDb (single-sequence); SNLI, MultiNLI/XNLI, Quora Question Pairs (pair-sequence). Models: BiLSTM with additive attention (+ uniform-attention baseline) and DistilBERT; 3 seeds per model.

### Evaluation of explanation quality
**None** - and that is the point. The paper measures inter-method **"Kendall-τ correlation"** and argues it is *not* a measure of quality: "rank correlation does not measure the quality of feature-additive methods"; "Without an external ground-truth explanation (like those constructed by Yalcin et al., 2021), all rank correlation tells us is whether or not two rankings are similar." Recommends "rigorous diagnostic measures - such as those proposed by Atanasova et al. (2020)."

### Ground truth used
None (explicitly absent; that absence drives the argument).

### Key numbers
- Mean τ between non-attention XAI methods across models/tasks: **0.2684**; with attention-based explanations: **0.1736**.
- DistilBERT inter-method mean 0.1088 vs BiLSTM 0.4281 (agreement collapses on the more complex model).
- Single-sequence mean 0.273 vs pair-sequence 0.1883.
- Even two "Shapley-value" methods disagree: Grad-SHAP vs Deep-SHAP combined mean 0.2839; attention flow vs SHAP approximations 0.1726.

### Stated limitations (no dedicated section; from Method/Discussion, near-verbatim)
- "we limit ourselves to an analysis of the raw attention weights for our LSTM-based model" (no faithful token-level attribution exists for LSTM attention).
- "input rankings may only capture a narrow slice of the model's behavior such that many equally faithful compressions exist. And, since many tasks may be too complex for humans to judge token-level importance, there may also be many plausible rankings ... when agreement is measured in the presence of multiple faithful and plausible rankings, XAI methods will look deceptively problematic."
- Low agreement "does not mean these methods are wrong, merely that we cannot assume they are interchangeable."
- Attention flow computation infeasible for long IMDb sequences.

### My gap observations
- Directly undercuts a common NTC/NIDS practice: validating a new explainer by showing correlation/overlap with SHAP or with another method's top-k features. This paper shows such agreement is neither necessary nor sufficient for faithfulness.
- 500 instances per dataset, workshop scale; no significance testing of τ differences.
- The "many equally faithful compressions" argument implies top-k feature stability metrics (popular in NIDS XAI, e.g., Warnecke et al.-style) inherit the same ambiguity - disagreement may reflect explanation multiplicity, not error. Nobody in NTC has separated these two causes.

---

## 3. A Causal Lens for Evaluating Faithfulness Metrics
Zaman & Srivastava (UNC Chapel Hill). EMNLP 2025 (arXiv:2502.18848v3). **Read: full text (PDF).**

### What it does
A **meta-evaluation**: evaluates faithfulness *metrics* (not explainers) for natural-language explanations. Framework: CAUSAL DIAGNOSTICITY. Uses **knowledge editing** (ICE in-context editing; MEMIT ablation) to create two counterfactually edited models that give the *same answer* for *different internal reasons*; each model's (synthetic) explanation is faithful to itself and unfaithful to the other. A good faithfulness metric should score the faithful member of the pair higher.

### Evaluation metric (quoted)
**"Diagnosticity"** D(F) = P(u ≻_F v | u ≻ v), estimated over explanation pairs with a tie-value of 0.5 (random baseline = 0.5). Metrics evaluated: **Simulatability**, **CC-SHAP** (post-hoc and CoT), and Lanham et al. CoT-corruption metrics: **Early Answering, Adding Mistakes, Paraphrasing, Filler Tokens** (extended from binary to continuous prediction-score-drop variants). Edit validity checked via **perplexity comparison** (faithful explanation should have lower PPL than unfaithful under the edited model).

### Ground truth used
**Interventional** - faithful/unfaithful labels are created by causal intervention on the model (parameter or context edits), not by proxy deletion curves.

### Setup / datasets
Tasks: FactCheck (from COUNTERFACT), Analogy (capitalOf vs cityOf hierarchy, 1,000 pairs), Object Counting (BIG-bench adapted, 1,000 questions), Multi-hop Reasoning (StrategyQA, 200 examples; gpt-4o-generated, manually verified counterfactuals). Models: qwen2.5-7b, gemma-2-9b-it. Synthetic explanations in main results (model-generated ones often fail to reflect edits).

### Key numbers
- **Filler Tokens** best overall (Copeland score 29): diagnosticity 0.828 (Qwen) / 0.893 (Gemma) on FactCheck; significantly > 0.5 across all tasks/models; only metric to do so.
- Simulatability ≈ chance everywhere (0.499-0.512).
- Continuous variants beat binary variants by up to +0.328 (Filler Tokens FactCheck 0.500 -> 0.828); "relative gains of up to 66%".
- Edit reliability: near 1.0 for FactCheck but **<50% for Analogy under ICE** - authors explicitly flag ICE-based Analogy diagnosticity results as "unreliable."
- ICE vs MEMIT: differences not significant except FactCheck.

### Stated limitations (Limitations section, near-verbatim)
"CAUSAL DIAGNOSTICITY is not suitable for evaluating all types of faithfulness metrics. Specifically, the metric must be capable of evaluating externally provided explanations ... we cannot evaluate metrics like Counterfactual Edits (Atanasova et al., 2023) ... Additionally, our approach requires metrics that produce per-instance faithfulness scores. ... Our framework also substantially depends upon the efficacy of the knowledge editing method. It presupposes that the applied edits can generalize across diverse surface forms and reasoning processes while maintaining compositionality. ... we utilize the perplexity relationship between edits and synthetically generated explanations as an indicative measure of model editing success. ... the potential benefits of model-generated explanations and more extensive models employing alternative editing techniques remains unexamined ... our scaling experiments exclude CC-SHAP owing to its slow execution."
Also from Conclusion: "Another key limitation of current metrics is that they do not indicate how or where an explanation is unfaithful."

### My gap observations
- The GT rests on edit success, which is itself only *proxied* (perplexity) - a soft circularity the authors acknowledge but cannot close; diagnosticity numbers inherit unquantified GT noise (Analogy shows how badly this can fail).
- The *concept* - meta-evaluating faithfulness metrics with pairs whose relative faithfulness is known by construction - is portable to NTC feature attributions (e.g., two models trained to rely on disjoint, verified feature subsets à la Bastings), but no NTC work does metric meta-evaluation at all; NIDS papers pick descriptive-accuracy/deletion metrics by convention, never validated.
- Corruption-based metrics suffer OOD artifacts (their Sec 5.2); the same OOD confound afflicts deletion/occlusion evaluations on flow features (zeroing a flow feature creates impossible flows) - an argument my survey can make with this citation.

---

## 4. Shortcut Learning in Deep Neural Networks
Geirhos, Jacobsen, Michaelis, Zemel, Brendel, Bethge, Wichmann. Nature Machine Intelligence 2(11), 2020 (arXiv:2004.07780v5). **Read: full text (perspective paper; intro/taxonomy/Sec 6/conclusion read closely, examples skimmed).**

### What it is
A perspective/position paper (not an XAI paper, no explanation evaluation). Unifies many DNN failure modes as **shortcut learning**: "decision rules that perform well on standard benchmarks but fail to transfer to more challenging testing conditions." Taxonomy of decision rules (Fig 3): all rules ⊃ training solutions ⊃ i.i.d. test solutions (incl. shortcuts) ⊃ intended solutions; shortcuts are exposed only by **o.o.d. generalization tests**. Origins: shortcut opportunities in data (dataset biases, e.g., cow-on-grass, hospital metal token for pneumonia) + discriminative feature combination ("Principle of Least Effort"). Coins "**Morgan's Canon for machine learning**": "Never attribute to high-level abilities that which can be adequately explained by shortcut learning."

### Evaluation of explanation quality
None (no XAI experiments). Its diagnostic prescription is behavioral: "o.o.d. generalisation tests will need to become the rule rather than the exception"; good o.o.d. tests need (1) a clear distribution shift, (2) a well-defined intended solution, (3) current models should struggle. Box I catalogs example benchmarks (adversarial attacks, ARCT-with-removed-shortcuts, cue-conflict stimuli, ImageNet-A/C, ObjectNet, PACS, Shift-MNIST/biased CelebA/unfair dSprites).

### Ground truth used
None.

### Key content for our purposes
- i.i.d. accuracy "can often be misleading, giving a false sense of security"; i.i.d. assumption called "the big lie in machine learning."
- Toy example: fully-connected net classifies stars/moons by *location*, not shape; a CNN "would be prevented from taking this shortcut by design" (inductive bias).
- Adversarial examples framed as counterfactual explanations ("smallest change to an input that produces a certain output").

### Stated limitations / future work (near-verbatim)
"currently a variety of approaches are explored without a commonly accepted strategy"; "o.o.d. tests will likely need to evolve alongside the models they aim to evaluate"; "While overcoming shortcut learning in its entirety may potentially be impossible, any progress towards mitigating it will lead to a better alignment between learned and intended solutions"; understanding what makes a solution easy to learn "requires disentangling the influence of structure (architecture), experience (training data), goal (loss function) and learning (optimisation)."

### My gap observations
- This is the conceptual backbone for grounding XAI evaluation in shortcut discovery (Bastings et al. operationalize it). The paper itself never assesses whether saliency methods *can* find shortcuts - that gap is exactly what Adebayo et al. 2022 and Bastings et al. fill, and it remains 100% open for network traffic.
- NTC datasets are shortcut minefields (CICIDS2017 attacker IPs/subnets, TCP flag artifacts from attack tools, TTL/window-size testbed artifacts, temporal ordering); Geirhos gives the vocabulary to argue that an NTC explanation-evaluation should be scored by whether explainers surface *known dataset shortcuts* - and that i.i.d. detection metrics say nothing about it.
- The recommended remedy (o.o.d. tests) is behavioral, not explanatory: the paper implicitly concedes we lack tools to see *which* shortcut was learned without interventional tests - the role XAI claims but has not earned.

---

## 5. INSOMNIA: Towards Concept-Drift Robustness in Network Intrusion Detection
Andresini, Pendlebury, Pierazzi, Loglisci, Appice, Cavallaro. AISec @ ACM CCS 2021. DOI:10.1145/3474369.3486864. **Read: full text (author PDF, S2Lab mirror).**

### What it does
Semi-supervised NIDS for concept drift: DNN classifier + uncertainty sampling (active learning, top σ% least-confident) + Nearest-Centroid (NC) pseudo-labeling oracle + fine-tuning per count-based window (50k flows). Extends **TESSERACT** to network domain (count-based windows instead of time splits; latency-aware variants F1-D, AUT(F1)-D). Dataset: **revised CICIDS2017** (Engelen et al. revision); init on days 1-2 (m = 693,650 labeled flows), incremental over 28 windows; features = CICFlowMeter flow-level statistics.

### XAI component
**DALEX permutation-based variable-importance** ("for each feature, its effect is removed by resampling or permuting the values of the feature and a loss function compares the performance before and after"), computed globally after initialization and after each window update, to "explain how the black box is changing over time to fit to new attack categories."

### Evaluation of explanation quality
Effectively **none** (qualitative plausibility only). "Utility of the explanations" is listed as an evaluation axis (Sec 4.3), but the actual assessment (Sec 4.3.4 "Drift Explanation") is a narrative check that feature-relevance shifts match domain expectations: e.g., when DoS Slowloris appears, "one would then expect to observe the 'maximum time a flow was idle before becoming active' (Idle Max) to gain importance, as Figures 9a-9c depict"; Bwd Packet Length Min gains relevance with the window-22 port-scan influx. No quantitative explanation metric, no comparison against any ground truth, no baseline explainer.

### Ground truth used (for explanations)
None. (Detection GT labels exist, but explanation quality is never scored against anything.)

### Key numbers
- No-Update baseline: F1 0.0019%, AUT(F1) 0.035; Kitsune: F1 0.0113% - both "identify almost zero attacks" across the 3 test days.
- INSOMNIA σ=50%: **F1 80.88%, AUT(F1) 42.39**, F1-D 80.40%, AUT(F1)-D 42.17, 428 min; vs US+Oracle (human-label upper bound): F1 81.62, AUT(F1) 36.10 (INSOMNIA beats the oracle on the temporal AUT metric).
- σ=70% collapses (F1 64.90) via NC self-poisoning during the port-scan influx (windows 22-25).

### Stated limitations (Sec 5, near-verbatim)
"detection of stealthy, low-prevalence attacks. INSOMNIA struggles to detect the few instances of the Infiltration attack at windows 14-17 ... maintaining sensitivity to attacks with a very low base rate in the presence of high volume attacks such as DoS is very challenging-as is generalizing to attack categories of greatly different character. While generalizing across attack types remains a holy grail, future work may consider ensembles ... INSOMNIA's update mechanism does not have the opportunity to make use of knowledge learned from attacks which occur wholly in a single window ... conceivably the DNN would be susceptible to catastrophic forgetting over long deployments ... As future work, we plan to explore how DALEX's explanations may be used for feature selection, to identify more stable features and improve the accuracy and robustness of the model. Additionally, we plan to investigate the effectiveness of intentional forgetting mechanisms ... and ... online classification algorithms in the role of the oracle."

### My gap observations
- Canonical instance of the pattern my paper targets: XAI in NTC deployed for interpretation of drift with **zero quantitative evaluation of explanation quality** - the plausibility narrative (Idle Max ↔ Slowloris) is confirmation-biased post-hoc storytelling; nothing rules out that the same features would move for unrelated reasons.
- Permutation importance is known to be unreliable under correlated features - flow statistics (IAT means/stds/totals) are heavily correlated; the paper does not acknowledge this.
- Their own future-work plan (use DALEX explanations for feature selection) *presupposes* explanation faithfulness that was never measured - a concrete motivation sentence for my survey.
- Explanations are global-only; per-attack local attribution (which analysts would actually consume) is absent.
- The drift setting adds an unstudied question: is the *explanation delta* between windows itself faithful (does the model actually change the way the importance shift suggests)? Nobody has an evaluation for temporal explanation deltas.

---

## 6. Evaluating Local Explanation Methods on Ground Truth
Riccardo Guidotti. Artificial Intelligence 291:103428 (2021). DOI:10.1016/j.artint.2020.103428. **Read: abstract only** (ScienceDirect/IRIS/RG/D4Science all bot-blocked or unreachable from this session; Wayback rate-limited). Details corroborated from the author's official code release: github.com/riccotti/SyntheticExplanationGenerator (syege/evaluation.py, experiment scripts).

### What it does (abstract, near-verbatim)
"one of the most common ways to assess the performance of an explanation method is to measure the fidelity of the explanation with respect to the classification of a black box ... However, this kind of evaluation only measures the degree of adherence of the local explainer in reproducing the behavior of the black box classifier with respect to the final decision. Therefore, the explanation provided by the local explainer could be different in the content even though it leads to the same decision ... we propose an approach that allows to measure to which extent the explanations returned by local explanation methods are correct with respect to a synthetic ground truth explanation. Indeed, the proposed methodology enables the generation of synthetic transparent classifiers for which the reason for the decision taken, i.e., a synthetic ground truth explanation, is available by design." (SENECA - Synthetic ExplaiNablE ClAssifier generators - for tabular data, images, and text.)

### Evaluation of explanation quality (metric names confirmed from author's evaluation.py)
- `feature_importance_similarity`: **cosine similarity** (1 − cosine distance, clipped to [0,1]) between the explainer's feature-importance vector and the ground-truth importance vector of the transparent classifier.
- `rule_based_similarity` / `_precision` / `_recall`: **F1 / precision / recall** over binary feature masks (which features appear in the explanation rule vs. the ground-truth rule); `rule_based_similarity_complete` additionally compares rule thresholds within eps.
- `word_based_similarity(_text)` and `pixel_based_similarity`: the same two families (cosine on values; F1/precision/recall on binary masks) for text-word and image-pixel explanations.
Explainers exercised in the repo's experiments: LIME, SHAP, LORE, Anchor, MAPLE, SBRL/RuleMatrix, across tabular (linear and rule-based synthetic classifiers), image, and text.

### Ground truth used
**Architectural** - transparent classifiers generated by construction (SENECA), whose true local decision rationale is available by design. This is the strictest GT category in this batch and the closest published analog to what my project needs for NTC.

### Stated limitations
**Not retrievable** (full text inaccessible this session; the abstract states no limitations). Flagged for manual retrieval - do NOT cite limitations of this paper without pulling the PDF via institutional access. Known third-party critiques to check against the primary text: Carmichael & Scheirer (arXiv:2106.08376) argue synthetic transparent classifiers may be off-manifold relative to real black boxes; "The Blame Problem" (arXiv:2310.03466) classifies SENECA-style GT as not solving evaluation for *real* black boxes.

### My gap observations
- Architectural ground truth exists for generic tabular data (SENECA supports tabular!) yet **no NTC/NIDS paper instantiates it** on traffic-like feature spaces (bounded counts, heavy-tailed durations, correlated IAT statistics, protocol categoricals). Building a SENECA-like generator whose transparent classifiers mimic traffic-classifier decision structure is an open, concrete contribution.
- Inherent tension to discuss: explanations validated against transparent surrogates say nothing about behavior on real DNN traffic models - architectural GT trades realism for certainty (mirror image of Bastings' behavioral-synthetic trade).
- Read-depth caveat: my numbers/claims for this paper beyond the abstract and code should be verified against the published text before citation in the journal paper.

---

# Batch-level synthesis (for the gaps section)

1. **A ladder of ground-truth strength emerges from this batch**: architectural (Guidotti: transparent-by-construction classifiers) > interventional (Zaman: model edits with known causal effect) > behavioral-synthetic (Bastings: injected shortcuts verified via accuracy tests) > none (Neely: agreement only; INSOMNIA: plausibility narrative; Geirhos: behavioral o.o.d. tests, no XAI). NTC/NIDS literature sits almost entirely at the bottom rung - INSOMNIA, the only networking paper here, displays importance heatmaps and validates them by story-telling against domain expectations.
2. **Every GT construction has an acknowledged validity dependency**: Bastings needs the two accuracy verification tests (and gets only a partial-order GT); Zaman needs edit success and can only proxy it with perplexity (Analogy task fails, <50%); Guidotti needs the transparent classifier to be a relevant stand-in for real black boxes. A survey table should record "GT validity check" as its own column.
3. **Agreement/correlation between explainers is formally rejected as an evaluation** (Neely: mean Kendall-τ 0.27 among methods, 0.11 for DistilBERT), yet inter-method agreement is still used as validation in NIDS XAI papers - citable ammunition.
4. **Method configuration is a hidden variable**: Bastings show precision swings from ~0.3 to ~1.0 within the *same* method family depending on norm/baseline/masking token, and that conclusions invert across architectures. NTC comparisons that pit "SHAP vs LIME vs IG" with default configs are measuring configurations, not methods.
5. **Meta-evaluation of faithfulness metrics does not exist in NTC**: Zaman's diagnosticity shows popular metrics can be near chance (Simulatability ~0.5). Nobody has asked whether descriptive accuracy / deletion curves - the default NIDS XAI metrics - are themselves diagnostic on traffic models.
6. **Concrete transfer opportunities for the journal paper**: (a) port the Bastings shortcut-injection protocol to flow features on CICIDS/UNSW-style data (shortcut = injected deterministic feature pattern, verified by the two-model accuracy test); (b) build a SENECA-style architectural-GT generator over traffic-feature marginals; (c) evaluate whether explainers detect *known real* dataset shortcuts (Geirhos framing; e.g., documented CICIDS2017 artifacts); (d) define and evaluate faithfulness of *temporal explanation deltas* under drift (gap exposed by INSOMNIA).
