# Deep-Read Notes - Batch 6

Reader focus: (1) how explanation quality is EVALUATED, (2) LIMITATIONS / FUTURE WORK, for the journal paper on XAI for network traffic classification (NTC).
All six papers read full-text (5 arXiv PDFs + 1 author-copy PDF from wpage.unina.it). Extracted texts: `tmp-cfgnnexplainer.txt`, `tmp-aceto2019mobile.txt`, `tmp-faithfulness-jacovi.txt`, `tmp-eraser.txt`, `tmp-rise.txt`, `tmp-quantus.txt` (same folder).

Batch character: 5 of 6 are XAI-evaluation methodology papers from *other domains* (graphs, NLP, vision, general toolkit) that the NTC literature imports; 1 (Aceto et al.) is a pure DL-NTC benchmark paper with no XAI, included as the domain anchor that motivates why NTC needs explanation auditing.

---

## 1. CF-GNNExplainer: Counterfactual Explanations for Graph Neural Networks
Lucic, ter Hoeve, Tolomei, de Rijke, Silvestri - AISTATS 2022 (arXiv:2102.03322v4). Read: full text incl. supplement.

**Task / model.** Node classification with a 3-layer GCN (hidden size 20, ≥87% test accuracy), same setup as Ying et al. (2019). Not traffic - relevant because GNN-based NTC exists and counterfactuals are an alternative to attribution.

**Method.** First CF explainer for GNNs: find the *minimal edge-deletion* perturbation of the node's subgraph adjacency matrix Av such that the prediction flips. Learns a binary perturbation matrix P (sigmoid + 0.5 threshold on a real-valued P̂, gradient taken w.r.t. P̂), loss L = Lpred + β·Ldist where Lpred = −1[f(v)=f(v̄)]·L_NLL and Ldist = number of edges removed (Wachter-style). O(KN²); ~375 GPU-hours total. Explanation size is found automatically (subgraph methods like GNNExplainer need user-specified size S).

**Datasets.** tree-cycles, tree-grid, ba-shapes (Ying et al. 2019): synthetic base graph + planted motifs (6-cycle / 3×3 grid / house) + random edges; classes = motif membership. "The purpose of these datasets is to have a ground-truth for the 'correctness' of an explanation: for nodes in the motifs, the explanation is the motif itself."

**XAI evaluation (quotes).** Four metrics:
- **Fidelity**: "proportion of nodes where the original predictions match the prediction for the explanations… Since we generate CF examples… we want a low value for fidelity." (Here fidelity = CF non-validity rate, inverted vs. usual usage.)
- **Explanation Size**: number of removed edges (want small).
- **Sparsity**: "proportion of edges in Av that are removed" (want ≈1).
- **Accuracy**: "mean proportion of explanations that are 'correct'… only compute accuracy for nodes that are originally predicted as being part of the motifs, since accuracy can only be computed on instances for which we know the ground truth explanations… an explanation [is] correct if it exclusively involves edges that are inside the motifs."
Baselines: random perturbation, 1hop (keep ego graph), rm-1hop (remove ego graph), GNNExplainer with removed subgraph for S ∈ {1..5, GT}. t-tests at α=0.01 (supplement).

**Ground truth used: synthetic** (planted motifs known by dataset construction; used only for the Accuracy metric and only on motif nodes).

**Key numbers.** ≥94% accuracy on all 3 datasets; mean explanation size 2.09/1.47/2.39 edges; sparsity 0.90/0.94/0.99; fidelity 0.21/0.07/0.39. random has fidelity 0 (always finds CFs) but size up to 503 edges and 0.17 accuracy on ba-shapes. GNNExplainer-as-CF: fidelity 0.35-0.90, accuracy 0.24-0.79 (worse than CF-GNNExplainer everywhere).

**Stated limitations (near-verbatim).** "In its current form, CF-GNNExplainer is limited to performing edge deletions in the context of node classification tasks. For future work, we plan to incorporate node feature perturbations… extend CF-GNNExplainer to accommodate graph classification tasks… investigate adapting graph attack methods for generating CF explanations, as well as conduct a user study to determine if humans find CF-GNNExplainer useful in practice." Also: "there do not exist any real node classification datasets with ground-truth explanations… Building such a dataset would be an excellent contribution, but is outside the scope of this paper." And (societal impact): "We believe it is crucial for the ML community to invest in developing more rigorous evaluation protocols for XAI methods."

**My gap observations (not stated by authors).**
- The Accuracy metric grades explanations against *data-generation* ground truth, silently assuming the trained GCN actually uses the motif. The model has only ≥87% accuracy, so for a nontrivial fraction of nodes the model's real reasoning provably deviates from the motif; motif-based "correctness" then measures plausibility w.r.t. the generator, not faithfulness to the model.
- Accuracy is computed only on motif nodes and only for methods that find CFs there - rm-1hop's accuracy is undefined on 2/3 datasets, making cross-method comparison on that column selective.
- Hyperparameters were selected "to produce the most CF examples", i.e., tuned on one of the reported evaluation quantities.
- Evaluation is synthetic-only; no real dataset, no runtime-vs-graph-size study beyond complexity claim.
- NTC transfer: graph-based traffic classifiers (flow graphs, host communication graphs) have no analogue of planted-motif ground truth; a "minimal edge deletion that flips the app label" is also an *evasion attack* in traffic - the paper's CF/adversarial distinction ("intent") dissolves in security settings, which no NTC paper I have read confronts.

---

## 2. Mobile Encrypted Traffic Classification Using Deep Learning: Experimental Evaluation, Lessons Learned, and Challenges
Aceto, Ciuonzo, Montieri, Pescapé - IEEE TNSM 2019 (author copy: wpage.unina.it/giuseppe.aceto/pub/aceto2019mobile_TNSM.pdf). Read: full text.

**Task / models.** Mobile encrypted app classification at biflow level. Reproduces and systematically compares state-of-the-art DL classifiers: SAE (Lotfollahi), 1D-CNN (Wang et al. '17), 2D-CNN (Wang et al. '17), LSTM, hybrid LSTM+2D-CNN (Lopez-Martin), MLP-2/2D-CNN on packet directions (Oh); baselines: 1-hidden-layer MLP and the AppScanner RF (40 handcrafted flow features).

**Input representations.** Type I "L7-N": first N app-layer payload bytes (256-2304, normalized to [0,1]); Type II "ALL-N": first N raw PCAP bytes - shown to be **biased** (PCAP global/per-packet headers incl. µs timestamps and size metadata leak label information); Type III "MAT": 6 fields × first Np packets (ports, payload size, TCP window, IAT, direction) - port fields shown to inflate performance ("statistical port-based architectures"); "DIR-Np": packet directions only.

**Datasets.** Three human-generated (not bot-generated) datasets: Android 49 apps (77.3k biflows) and iOS 45 apps (44.1k biflows) from a global mobile solutions provider, Apr'15-Jan'17, under NDA ("we can not report its name… nor release the data set"); FB/FBM binary dataset (>34k biflows, >100 volunteer users, single Xiaomi Mi5 device, May'17-Mar'18) collected at ARCLAB Napoli (precursor of MIRAGE).

**Evaluation workbench (classification, not XAI).** Accuracy, macro F-measure, G-mean (√(rec·spec)), Top-K accuracy (K∈{1,3,5}), confusion matrices, reject option (censoring threshold γ vs. Classified Ratio), Run-Time-Per-Epoch; stratified 10-fold CV, mean ± std, ±3σ intervals.

**XAI evaluation: none.** No explanation method is applied anywhere. Interpretability appears only as a challenge: "this issue is worsened by the black-box nature of most algorithms, as the performance impact of specific inputs is barely or not-at-all predictable."

**Ground truth used: none** (for explanations; classification labels are per-app trace-level capture labels).

**Key numbers.** Best unbiased DL: 1D-CNN (L7-784) 85.70% acc / 78.68 F1 Android; 2D-CNN (L7-784) 82.72% acc iOS; DL beats RF (84.78% Android) on multi-class but **loses to RF on FB/FBM** (76.37% vs 79.56%). Biased ALL-784 inflates a *shallow* MLP-1 to 96.53% (Android) / 97.24% (iOS) - the single clearest quantitative demonstration of input bias in the DL-NTC literature. Removing ports from MAT costs up to −19.68 F1. DIR input collapses to 40.11%/32.95% acc (directions suffice for website fingerprinting but not mobile TC). 16-20 packets suffice for MAT; N=784 best for payload. With 10% rejection, 1D-CNN reaches ≥90% acc (Android).

**Stated limitations / challenges (near-verbatim, from Sec. V).** "TC… is affected by the lack of up-to-date human-generated public datasets… difficulty of anonymizing traffic traces in ways that both do not significantly affect the information useful for classification, and preserve users privacy." "An elaborated input selection process contrasts one of the main promises of DL approaches, i.e. the reduced need of domain expertise… worsened by the black-box nature of most algorithms." "There is no 'killer' DL architecture for mobile TC… the tuning of hyper-parameters of DL algorithms is substantially overlooked (just tentative values are provided, if at all)." "The aspect of the purity of labeled samples used for training (i.e. the ground-truth quality) is equally important, with (coarse) trace-level labeling probably not representing the 'purest' strategy." "Whether the fields of the first 16 to 20 packets are usually sufficient… a clear trend is not evident for payload input… this motivates a deeper investigation, also in terms of a more effective representation of payload." Service-burst TC objects "deserve further attention." "DL algorithms applied to mobile TC… has yet to reach the maturity level of DL in other fields."

**My gap observations.**
- This paper is the strongest *motivating case* for XAI-in-NTC in the whole batch: the ALL-784 bias (models exploiting PCAP metadata) and the port shortcut were discovered by **manual domain reasoning and ablation**, exactly the shortcut-detection job that attribution methods claim to automate. No attribution method was used; the 2019 authors had to guess where the leakage was and re-run. A faithful explainer would have localized the leak to the 24-byte global header / 16-byte per-packet headers directly - this is a concrete, checkable use-case where "architectural" knowledge of the bias exists and could serve as ground truth for evaluating XAI methods (nobody has done this).
- The NDA on the two multi-class datasets makes headline results unreproducible; only FB/FBM descends to the public MIRAGE lineage.
- Single-device, volunteer-session FB/FBM collection risks device/session artifacts; no cross-dataset or temporal-drift evaluation despite citing fingerprint aging as key.
- The paper's own "biased vs unbiased input" framing is a proto-sanity-check for NTC: reporting both is effectively a leakage audit protocol, but it never became standard in later DL-NTC papers.

---

## 3. Towards Faithfully Interpretable NLP Systems: How Should We Define and Evaluate Faithfulness?
Jacovi & Goldberg - ACL 2020 (arXiv:2004.03685v3). Read: full text. Opinion/position paper; no experiments, no datasets, no models.

**Core distinction.** "'Plausibility' refers to how convincing the interpretation is to humans, while 'faithfulness' refers to how accurately it reflects the true reasoning process of the model." Conflation is "dangerous" (recidivism example: "a plausible but unfaithful interpretation may be the worst-case scenario").

**Guidelines (their Sec. 5, near-verbatim).**
1. "Be explicit in what you evaluate… Conflating plausibility and faithfulness is harmful."
2. "Faithfulness evaluation should not involve human-judgement on the quality of interpretation" - "humans cannot judge if an interpretation is faithful… if they understood the model, interpretation would be unnecessary."
3. "Faithfulness evaluation should not involve human-provided gold labels… Evaluation methods that rely on gold labels are influenced by human priors on what should the model do, and again push the evaluation in the direction of plausibility."
4. "Do not trust 'inherent interpretability' claims."
5. "Faithfulness evaluation of IUI systems should not rely on user performance" (utility ≈ plausibility × model performance, not faithfulness; fictional heat-map counterexample given).

**Three assumptions organizing all existing faithfulness evaluations.**
- **Model Assumption**: same predictions ⟺ same reasoning. Underlies fidelity of surrogate models ("the degree to which the explanation model can mimic the original model's decisions") and adversarial counter-examples (Wiegreffe & Pinter) and forward simulation (Doshi-Velez & Kim).
- **Prediction Assumption**: similar inputs + similar decisions ⟺ similar reasoning. Underlies interpretability robustness (Alvarez-Melis & Jaakkola), input-shift invariance (Kindermans). "Robustness measures are difficult to apply in NLP settings due to the discrete input" (same holds for packets).
- **Linearity Assumption**: parts of input contribute independently. Underlies **erasure**: "the 'most relevant' parts of the input-according to the explanation-are erased… in expectation that the model's decision will change"; comprehensiveness/sufficiency (Yu et al.; DeYoung et al.) are "a formal generalization of erasure."

**Binary → graded.** "There is a clear trend of proof via counter-example… that they are not globally faithful. We claim that this is unproductive… By the pigeonhole principle, there will be inputs with deviation between interpretation and reasoning." "Strictly faithful interpretation is a 'unicorn' which will likely never be found." Proposal: graded ("grayscale") faithfulness (i) across models and tasks, (ii) across input subspaces.

**XAI evaluation performed: none** (prescriptive meta-paper). **Ground truth used: none** - and it argues human gold labels must *not* serve as faithfulness ground truth.

**Stated limitations (near-verbatim).** "We pose the exact formalization of these criteria, and concrete evaluations methods for them, as a central challenge to the community for the coming future." "Exposing the underlying assumptions enables an informed discussion regarding their validity and merit (we leave such a discussion for future work, by us or others)."

**My gap observations.**
- No operationalization: the paper forbids most practical evaluation routes (human judgement, gold labels, utility studies) yet supplies no concrete metric, leaving erasure-style proxies - which live under the Linearity Assumption the authors themselves flag as under "justified scrutiny" - as the only sanctioned tools.
- The claim that the three assumptions "encapsulate the current working definitions" is asserted from a literature survey, not demonstrated; interventional/retraining approaches (ROAR) and known-model architectural ground truth don't cleanly fit any of the three.
- Direct consequence for NTC that no NTC paper draws: the standard NTC validation move - checking SHAP/IG attributions against expert networking knowledge (ports, TLS handshake fields, packet-length signatures) - is, under this framework, a **plausibility** evaluation, not faithfulness. Most "our explanations are correct because experts agree" claims in the NTC corpus are thereby recategorized.
- Their graded-faithfulness proposal (per-task, per-input-subspace) has never been instantiated in NTC (e.g., per-app or per-protocol faithfulness scores).

---

## 4. ERASER: A Benchmark to Evaluate Rationalized NLP Models
DeYoung, Jain, Rajani, Lehman, Xiong, Socher, Wallace - ACL 2020 (arXiv:1911.03429v2). Read: full text (appendices skimmed: dataset processing/hyperparams only).

**What it is.** GLUE-style benchmark of 7 NLP datasets repurposed/augmented with **human-annotated rationales** (supporting text snippets): Evidence Inference (RCT articles), BoolQ, Movie Reviews, FEVER, MultiRC, CoS-E, e-SNLI (sizes 1.6k-912k train; avg doc length 16-4761 tokens). Comprehensive (all-evidence) rationales collected for subsets; Evidence Inference comprehensive rationales annotated by **Medical Doctors**. Human agreement: Cohen κ 0.618-0.854; token F1 0.617-0.871.

**XAI evaluation metrics (quotes).** Two families, explicitly separated:
1. **Agreement with human rationales (= plausibility)**: IOU-F1 (token-level Intersection-Over-Union, match if overlap >0.5), token-level precision/recall/F1; for soft scores, **AUPRC** by sweeping a threshold. "Measuring agreement between extracted and human rationales… assesses the plausibility of rationales, but such approaches do not establish whether the model actually relied on these particular rationales."
2. **Faithfulness**: **comprehensiveness** = m(xi)_j − m(xi∖ri)_j ("were all features needed to make a prediction selected?" - contrast examples per Zaidan et al.) and **sufficiency** = m(xi)_j − m(ri)_j ("do the extracted rationales contain enough signal…?"). Soft scores discretized via top-k_d where k_d = average human rationale length per dataset. Aggregate **AOPC** variant: average over bins of top 1/5/10/20/50% tokens ("Area Over the Perturbation Curve"), with a **random-ordering reference** (10 runs). Footnote: "Our AOPC metrics are similar in concept to ROAR (Hooker et al., 2019) except that we re-use an existing model as opposed to retraining for each fraction."
Hard-selection (extract-then-predict) models are declared "inherently faithful, because by construction we know which snippets the decoder used" (footnote: "This assumes independent encoders and decoders."), so only plausibility is reported for them.

**Models.** Hard: Lei et al. 2016 (BERT/GloVe+LSTM encoder-decoder, REINFORCE; with and without rationale supervision), Lehman et al. pipeline, BERT-to-BERT pipeline. Soft: BERT+LSTM (GloVe+LSTM for long docs) scored by attention, simple gradients, LIME.

**Ground truth used: human_expert** (human-annotated rationales, incl. domain experts for Evidence Inference) - used for the plausibility half; the faithfulness half is deliberately proxy-based (erasure).

**Key numbers.** BERT-to-BERT best IOU-F1 on FEVER 0.835; Lei et al. degenerates (0.000 F1) on several datasets without rationale supervision. Soft-score results: attention wins AUPRC (plausibility) but "both simple gradient and LIME-based scoring yield more comprehensive rationales than attention weights… LIME does particularly well across these tasks in terms of faithfulness" (e.g., e-SNLI comprehensiveness: LIME 0.437 vs attention 0.105; random 0.081). Rationale supervision improves agreement "though not always," and "this does not seem strongly correlated with predictive performance."

**Stated limitations (near-verbatim).** "We do not claim that these are necessarily the best metrics for evaluating rationales… How best to measure rationale faithfulness is an open question… a topic ripe for additional research." "The necessity of discretizing continuous scores forces us to pick a particular threshold k." "No single 'off-the-shelf' architecture is readily adaptable to datasets with very different instance lengths and associated rationale snippets." Test sets released publicly "because we do not view the 'correct' metrics to use as settled." Future: "better evaluation metrics for interpretability, causal analysis of NLP models and datasets of rationales in other languages."

**My gap observations.**
- Comprehensiveness/sufficiency feed the model deliberately mutilated inputs; the footnote-7 admission (no retraining, unlike ROAR) means OOD artifacts are baked into the benchmark's faithfulness scores - a random-token baseline mitigates but does not remove this.
- k_d anchored to *human* rationale length imports a human prior into the "faithfulness" metric, partially recoupling the two axes the benchmark tries to separate (tension with Jacovi & Goldberg guideline 3, which the paper itself cites approvingly).
- "Inherently faithful by construction" for pipelines quietly assumes the extractor didn't leak label information through snippet *selection* statistics.
- NTC transfer: nothing like ERASER exists for traffic - there is no corpus of flows with expert-marked byte-/packet-level rationales ("which header fields/packets justify labeling this flow as FBM"). Building even a small one (feasible for protocol-structured, non-encrypted fields) is an obvious missing resource; until then NTC papers can compute comprehensiveness/sufficiency but have no plausibility axis with which to triangulate.

---

## 5. RISE: Randomized Input Sampling for Explanation of Black-box Models
Petsiuk, Das, Saenko - BMVC 2018 (arXiv:1806.07421v3). Read: full text incl. appendices.

**Method.** Black-box saliency for image classifiers: importance of pixel λ = E_M[f(I⊙M) | M(λ)=1], Monte-Carlo-estimated as score-weighted average of N random masks. Masks: low-res 7×7 Bernoulli(p=0.5) grids, bilinearly upsampled to 224×224 (values in [0,1], avoids adversarial sharp edges and shrinks mask space), randomly shifted. N=4000 (VGG16) / 8000 (ResNet50). Only input/output access needed; extended to captioning (per-word saliency).

**Datasets / models.** PASCAL VOC07 (test), MSCOCO2014 (val), ImageNet (val); ResNet50 and VGG16.

**XAI evaluation (quotes).** Proposes the now-canonical **deletion** and **insertion** "causal metrics":
- Deletion: "measures the drop in the probability of a class as important pixels… are gradually removed… A sharp drop, and thus a small area under the probability curve, are indicative of a good explanation." Pixels set to constant values ("blurring small regions… does not help. This is because a good classifier is usually able to fill in the missing details").
- Insertion: "measures the increase in probability as more and more pixels are introduced, with higher AUC indicative of a better explanation," starting from a blurred canvas ("less severe" spurious-evidence issue; "This strategy gives higher scores for all methods, so we adopt it").
- Rationale for automatic metrics: "human-dependent metric cannot evaluate the correctness of an explanation that aims to extract the underlying decision process from the network… an AI system could behave differently from a human and learn to use cues from the background (e.g., using grass to detect cows)." "Localization is merely a proxy for human explanation."
- Secondary human-centric metric: **pointing game** - "If the highest saliency point lies inside the human-annotated bounding box of an object, it is counted as a hit"; accuracy = #Hits/(#Hits+#Misses), averaged over categories. Caveat repeated: "good pointing accuracy may not correlate with actual causal processes in a network."
3 independent runs with std reported.

**Ground truth used: human_expert** - only in the *secondary* pointing game (human-annotated object bounding boxes); the headline deletion/insertion metrics are proxies, not ground truth (and on ImageNet "no ground truth segmentation or localization mask is provided and thus explainability performance can only be measured via automatic metrics").

**Key numbers.** ImageNet ResNet50: deletion 0.1076, insertion 0.7267 (RISE) vs Grad-CAM 0.1232/0.6766, LIME 0.1217/0.6940, sliding window 0.1421/0.6618 - a black-box method beating white-box Grad-CAM. Pointing game: VGG16 VOC 87.33% (best, vs c-MWP 80.00); ResNet50 VOC 88.94 (CAM 90.60 wins).

**Stated limitations (near-verbatim).** "Due to increased number of forward passes, RISE is heavy in computation. This can potentially be addressed by intelligently sampling fewer number of random masks which is kept as a future work. RISE, sometimes, provides noisy importance maps due to sampling approximation especially in presence of objects with varying sizes." Appendix failure cases: "cannot get rid of the background noise (in part due to MC approximation with only a subset)." Future work: "exploit the generality of the approach for explaining decisions made by complex networks in video and other domains."

**My gap observations.**
- The word "causal" is doing unearned work: deletion/insertion are occlusion proxies whose fill values (constant gray / blur) create off-manifold inputs; the paper *acknowledges* the spurious-evidence problem and then selects the fill strategy partly because "this strategy gives higher scores for all methods" - a metric-design choice justified by score magnitude, not validity. No experiment verifies that metric rankings survive a change of baseline value (Quantus later shows exactly this parameter flips rankings).
- Evaluation-method circularity risk: RISE computes importance by random masking, and is evaluated by masking-based deletion/insertion - the method and the metric share the same perturbation family, plausibly favoring RISE over gradient methods. Not discussed.
- No statistical comparison beyond std over 3 runs of its own method; competitor numbers partly copied from prior papers on possibly different pipelines.
- NTC transfer (widely done, rarely questioned): deletion/insertion AUC has been imported into traffic XAI papers wholesale, but (i) "blur" has no analogue for packet bytes, (ii) zero is a *meaningful, common* byte value in headers/payloads so zero-masking creates valid-looking but semantically different packets rather than "information removal," (iii) RISE's smooth upsampled masks encode a spatial-smoothness prior that is wrong for byte sequences where adjacent bytes belong to unrelated fields. Any NTC use of RISE-style masking needs field-aware masks; I have not seen this addressed.

---

## 6. Quantus: An Explainable AI Toolkit for Responsible Evaluation of Neural Network Explanations and Beyond
Hedström, Weber, Bareeva, Krakowczyk, Motzkus, Samek, Lapuschkin, Höhne - JMLR 24(34), 2023 (arXiv:2202.06861v3). Read: full text (short MLOSS paper, 11 pp incl. refs).

**What it is.** Open-source Python toolkit (PyTorch + TensorFlow) with "30+ reference metrics" (27 at time of Table 1 vs Captum 2, AIX360 2, TorchRay 1) for evaluating attribution-based explanations, plus warnings/checks/guidelines. One-liner API (e.g., `quantus.PixelFlipping(perturb_baseline="black")`); `perturb_baseline` and other components user-replaceable.

**Six metric categories (Appendix, quotes).**
- "(a) Faithfulness (↑) quantifies to what extent explanations follow the predictive behaviour of the model, asserting that more important features affect model decisions more strongly" (9 metrics; Bach '15 pixel-flipping, Samek '17, Bhatt '20, Yeh '19, Rong '22 …).
- "(b) Robustness (↓) measures to what extent explanations are stable when subject to slight perturbations in the input, assuming that the model output approximately stayed the same" (4).
- "(c) Localisation (↑) tests if the explainable evidence is centred around a region of interest, which may be defined around an object by a bounding box, a segmentation mask or a cell within a grid" (6).
- "(d) Complexity (↓) captures to what extent explanations are concise" (3).
- "(e) Randomisation (↑) tests to what extent explanations deteriorate as the data labels or the model… are increasingly randomised" (2; Adebayo sanity checks, Sixt).
- "(f) Axiomatic (↑) measures if explanations fulfil certain axiomatic properties" (3).

**Motivating claims (quotes).** "The task of explaining generally lacks 'ground-truth' data. There exists no universally accepted definition of what a 'correct' explanation is." "It is common for XAI papers to base their conclusions on one-sided, sometimes methodologically questionable evaluation procedures." "It is practically well-known but not yet publicly recognised that evaluation outcomes of explanations can be highly sensitive to the parameterisation of metrics" - Fig. 1c demonstrates that the *pixel replacement strategy* of a faithfulness test "influences the ranking of explanation methods" (ImageNet demo comparing Saliency, Integrated Gradients, GradientShap, FusionGrad).

**XAI evaluation performed in the paper: demonstration only** - spider-plot "holistic quantification" across categories plus a parameterisation sensitivity analysis on ImageNet; no claim about which method is best, no validation of the metrics themselves.

**Ground truth used: none** (toolkit supports localisation against masks/boxes, but the paper performs no ground-truth evaluation).

**Stated limitations (near-verbatim).** "XAI evaluation is intrinsically difficult and there is no one-size-fits-all metric for all tasks. Evaluation of explanations must, therefore, be understood and calibrated from its context: the application, data, model, and intended stakeholders." "The first iterations of the library mainly focus on attribution-based explanation techniques for (but not limited to) image classification. In planned future releases, we are working towards extending the applicability of the library further, e.g., by developing additional metrics and functionality that will enable users to perform checks, verifications and sensitivity analyses on top of the metrics."

**My gap observations.**
- Quantus aggregates proxy metrics but offers no principle for resolving *disagreement between categories* (a method can win faithfulness and lose robustness; the spider plot displays, it does not decide) and no meta-evaluation of which metric is trustworthy when parameterisations flip rankings - the problem its own Fig. 1c exposes. (The authors' later MetaQuantus work exists precisely because this paper leaves it open.)
- Category (a)'s definition quietly embeds the linearity/erasure assumption criticized by Jacovi & Goldberg; the toolkit standardizes the proxies without standardizing their validity conditions.
- Image-idiomatic defaults (`perturb_baseline="black"`, bounding-box localisation) require domain redefinition for traffic inputs; nothing prevents use on flow vectors, but no tutorial/guidance existed for non-image tabular/sequence domains at publication.
- For the journal paper: no NTC study I have catalogued runs a Quantus-style multi-category battery; NTC XAI evaluation is typically a single proxy (deletion curve or expert agreement). Porting the six-category battery to NTC - with traffic-appropriate perturbation baselines (e.g., protocol-valid resampling instead of zeroing) - is a concrete, publishable methodological contribution.

---

## Cross-batch synthesis (for the gap analysis chapter)

1. **The imported evaluation canon was built elsewhere and carries domain assumptions.** Deletion/insertion (RISE), comprehensiveness/sufficiency/AOPC (ERASER), planted-motif accuracy (CF-GNNExplainer), and the Quantus metric battery were all designed for images, text, or synthetic graphs. Each embeds assumptions that fail for packets/flows: meaningful "removal" baselines (zero bytes are valid data, blur is undefined), spatially smooth masks, token-aligned human rationales, motifs known by construction. NTC papers import these metrics verbatim; none of the six papers (nor, so far, the NTC corpus) re-derives their validity conditions for traffic.
2. **The field disagrees about whether humans can supply ground truth.** ERASER's plausibility half and RISE's pointing game treat human annotations as reference; Jacovi & Goldberg explicitly forbid human judgement and gold labels for faithfulness. Consequence for NTC: the dominant NTC validation pattern - "SHAP highlighted ports/TLS fields, which matches expert knowledge" - is a plausibility check, not a faithfulness check. A rigorous NTC evaluation needs both axes reported separately (ERASER's structure) or a non-human ground truth.
3. **Nobody in this batch uses architectural or interventional ground truth.** The strictest available strategies - models with decision regions known by construction, or retraining-based interventions (ROAR is mentioned only in an ERASER footnote as the road not taken) - are absent. CF-GNNExplainer's synthetic motifs are dataset-level, not model-level, ground truth (the trained model may not use the motif). This is the opening for our project's ground-truth taxonomy: synthetic-known-model traffic classifiers would give NTC what none of these fields has cleanly.
4. **Proxy metrics are themselves unvalidated and unstable.** Quantus demonstrates that a single parameter (pixel replacement strategy) flips method rankings; RISE chose its fill strategies partly because they yield higher scores; ERASER admits its threshold k is arbitrary. Evaluation-of-the-evaluation (meta-evaluation) is missing everywhere.
5. **The NTC anchor paper shows the concrete payoff.** Aceto et al. found dataset/input bias (PCAP metadata, ports) by hand; a trustworthy attribution method would have localized it automatically - and, conversely, the *known* location of that bias is a ready-made, real-data ground truth for benchmarking XAI methods on traffic (does the method's attribution concentrate on the 24-byte PCAP global header / port fields of a biased model?). None of the methodology papers' benchmarks offers anything this ecologically valid.
6. **Method-metric circularity.** Perturbation-based explainers (RISE; occlusion) evaluated by perturbation-based metrics (deletion/insertion; pixel-flipping) share a perturbation family; rankings may reflect this affinity rather than faithfulness. Never controlled for in this batch; worth testing in NTC where both are commonly borrowed together.
