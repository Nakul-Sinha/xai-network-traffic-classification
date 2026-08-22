# Deep-Read Notes - Batch 10

Reader focus: (1) how explanation quality is EVALUATED, (2) LIMITATIONS / FUTURE WORK.
Date: 2026-08-22. Source texts cached as `tmp-*.txt` in this folder.

---

## 1. Robust Network Traffic Classification
Zhang, Chen, Xiang, Zhou, Wu - IEEE/ACM Trans. Networking 23(4):1257-1270 (accepted 2014, issue 2015). DOI:10.1109/TNET.2014.2320577.
**Read depth: full_text** (author PDF, `tmp-robust-ntc.txt`, https://cis.temple.edu/~wu/research/publications/Publication_files/TON_final.pdf).

### What it is
Pre-DL, pre-XAI classic. Proposes **RTC (Robust statistical Traffic Classification)** to handle **zero-day applications** in flow-statistics-based TC. Three modules:
1. **Unknown discovery** (two-step): k-means over labeled+unlabeled flows; clusters containing no labeled samples are "zero-day clusters"; those samples then train a **random forest** with a *generic unknown class*, which re-filters the unlabeled pool to a high-purity zero-day set.
2. **BoF-based classification**: correlated flows (3-tuple heuristic: same dst IP, dst port, protocol in a short window) grouped into "bags of flows"; RF per-flow predictions aggregated by majority vote. Theoretical analysis: BoF error reduced ~1/n under error independence; refined via "sub-bags" (4-tuple) since intra-bag errors are dependent.
3. **System update**: k-means on identified zero-day traffic; **3 randomly selected flows per cluster manually inspected**; consensus creates new classes; two-level classification so known-class performance is untouched.
Parameter k automated via 10-fold CV + binary search targeting FPR closest to 3% (FPR monotone in k).

### Data / features
- Traces: KEIO (2006), WIDE-08, WIDE-09 (MAWI, 40 B payload kept), ISP edge trace (Australia, Nov 2010, full payload). Combined dataset: >638,000 TCP flows, 10 major + 16 small classes. 900 s idle timeout.
- Label ground truth: **custom DPI tool** (l7-filter/Tstat-style regex signatures) + some manual inspection. DPI-unrecognized traffic *excluded* from the combined dataset; in per-trace experiments (ISP, WIDE-09) DPI-unrecognized traffic is instead *defined as* zero-day.
- Features: 20 unidirectional statistics → 9 after feature selection (c2s pkt count, c2s max/min/avg/std pkt bytes, c2s min inter-pkt time, s2c pkt count, s2c max/min pkt bytes).

### Key numbers
- Unknown discovery: step 1 TPR 72% / FPR 6%; after step 2 **TPR 94% / FPR 3%**.
- RTC vs. 4 baselines (RF, BoF-RF, Erman semi-supervised, one-class SVM): accuracy lead over the second best (semi-supervised) ≈ **12-15%** on the combined dataset; stable (±1%) as 1→5 classes are made zero-day, while BoF-RF drops 80%→50%.
- Zero-day traffic F-measure **0.91** before update; after update, new classes new_1(BT)/new_2(DNS)/new_3(SMTP) reach F ≈ **0.94/0.96/0.96**. Manual inspection rate 300/60,000 ≈ **0.5%**.
- ISP dataset: zero-day = 55% of flows / 12% of bytes; RTC flow accuracy ~+10% over second best; byte accuracy +15-25%.

### XAI evaluation
**none** - no explanations of any kind are produced or evaluated. ("Robust" here = robustness to zero-day traffic, not explanation robustness.)

### Ground truth used (for explanations)
**none** (n/a). (Class-label ground truth is DPI+manual, but that is TC ground truth, not explanation ground truth.)

### Stated limitations / future work (near-verbatim)
- "Our work shares a basic assumption with most pattern classification algorithms in that class distribution will not change in the training and testing stages. However, in real-world networks, class distribution may change over a long period of time… a new [cluster] is not added to the training set, i.e., the new characteristic of the application is not tracked."
- "We plan to extend this work in the future and address the problem of changing class distribution by developing new strategies for system updates and classifier retraining."
- Eq. (10) error-reduction "depends on the key assumption that errors due to individual flows in any BoF are independent" - relaxed via sub-bags (Eq. 12).
- Scope: "we focus exclusively on … TCP traffic" (though claimed protocol-independent). System update "Involve[s] a little human effort".

### My gap observations (not stated by authors)
- The **system-update loop is exactly where explanations are missing**: humans must manually inspect raw flows from anonymous clusters with no model-side evidence of *why* the cluster is coherent or what features drove separation. An attribution/prototype explanation would directly reduce this labeling effort - never discussed.
- **Circularity in ground truth**: DPI defines both the known classes and (in per-trace experiments) what counts as "zero-day"; DPI-unrecognized traffic is excluded from the combined benchmark, so evaluation lives inside DPI's recognition envelope.
- Zero-day evaluation is **simulated by class holdout** on 2006-2010 traces; no temporal drift evaluation despite drift being the stated motivation of the update module.
- RF is used throughout but **feature importances are never reported** - even the era-appropriate interpretability freebie is unused. Useful in my survey as the archetype of the "performance-only" era that XAI-for-NTC papers later react to.

---

## 2. MIMETIC: Mobile encrypted traffic classification using multimodal deep learning
Aceto, Ciuonzo, Montieri, Pescapè - Computer Networks 165:106944 (2019). DOI:10.1016/j.comnet.2019.106944.
**Read depth: full_text** (author PDF, `tmp-mimetic.txt`, http://wpage.unina.it/antonio.montieri/pubs/aceto2019mimetic.pdf).

### What it is
First **multimodal (intermediate-fusion) DL** framework for mobile encrypted TC at biflow level. Two modalities:
- **Payload modality**: first **Nb=576 bytes of L4 payload** (normalized [0,1]) → two 1D conv layers (16/32 filters, kernel 25) + max-pooling + dense(256).
- **Protocol-fields modality**: first **Np=12 packets × 4 fields** (transport payload length, TCP window size, inter-arrival time, direction) → bidirectional GRU(64) + dense(256).
- Merge = concatenation → shared dense(128) → softmax. Dropout 20%.
Training: **pre-train each modality branch** (25 epochs each, softmax "stubs") then **fine-tune** whole net (40 epochs) with low layers (conv/GRU) frozen; class-weighted (cost-sensitive) categorical cross-entropy w_m = M/M_ℓ; ADAM, batch 50; early stopping. **Ports and biased inputs deliberately excluded** ("otherwise these may both lead to biased and inflated performance", citing their TMA'18/TNSM'19 dissection).

### Data
Three **human-generated** datasets (labeling by running each app separately; background traffic removed):
- FB/FBM binary: ~31k biflows (13.5k FBM / 17.5k FB), >100 volunteer users, 91% encrypted.
- Android: 49 apps, 607 traces, 55.5k biflows (47% encrypted); iOS: 45 apps, 419 traces, 37.2k biflows (60% encrypted). Provided by a mobile-solutions provider **under NDA - datasets cannot be released** (footnote 2).

### Evaluation of the classifier
Accuracy, macro F-measure, **Top-K accuracy** (K=1,3,5), confusion matrices, Run-Time-Per-Epoch (RTPE), trainable-parameter counts, and **reject option** (censoring threshold γ; Classified Ratio CR vs. performance). Stratified 10-fold CV, mean±std.

### Key numbers
- MIMETIC: accuracy **79.98 / 89.49 / 89.14%** and F-measure **79.63 / 81.51 / 82.99%** on FB-FBM / Android / iOS. Max improvement over best baseline classifier (MIOB-C) up to **+8.58% F** (iOS); over best fusion technique +7.05%.
- Top-5 accuracy 95.82% (Android), 96.74% (iOS).
- RTPE 38.34±0.82 s vs 142.72±1.74 s for 1D-CNN(L7-784) - **>3.5× faster training**; ~3.6× fewer parameters.
- Reject option: F ≥ 90% by censoring ~10% of biflows (multi-class) but ~30% for FB/FBM ("overlapped apps" sharing third-party services).
- Baselines: 1D-CNN [Wang'17], LSTM+2D-CNN [Lopez-Martin'17], MLP-1, AppScanner-style flow RF [Taylor'18], fusion (MV/SOA/TLF).

### XAI evaluation
**none** - no explanation method is applied and no interpretability analysis is performed. The only explanation-adjacent evidence is *modality-level ablation by construction* (single-modality baselines vs. the fused model), which quantifies each input view's standalone value but attributes nothing within a view.

### Ground truth used (for explanations)
**none** (n/a).

### Stated limitations / future work (near-verbatim, §6)
- "the generality of the multimodal-DL TC framework proposed allows the adoption and the use of more sophisticated DL layers, such as inception and residual connections."
- "the training procedure considered, including a pre-training phase, can be used in conjunction with the exploitation of massive unsupervised data for improved transfer learning."
- "it is of clear interest the prototyping of multimodal-DL architectures able to cope with more challenging TC objects (e.g. service burst), especially in the definition of the corresponding multiple modalities."
- "a real-world implementation of multimodal-DL architectures in open-source tools (e.g. TIE) is of relevant interest."
- (Data note: NDA prevents releasing datasets or provider details.)

### My gap observations
- MIMETIC is **the canonical explanandum**: the same UNINA group's later "XAI meets Mobile Traffic Classification" (TNSM 2021, in corpus) applies occlusion/IG-style analysis to *this exact architecture* - evidence that the model paper itself ships with zero transparency and the explanation work is bolted on afterwards, with no ground truth available for either.
- The paper's **bias/shortcut discussion is done entirely by manual input curation** (dropping ports, L7-vs-ALL payload arguments) rather than by any attribution audit; i.e., shortcut detection happens at design time on faith, unverifiable post hoc.
- **Irreproducible data** (NDA) makes any later explanation-faithfulness claims on these datasets untestable by third parties.
- Reject option calibrates *confidence*, not *explanation*; no analysis of whether censored samples are the ones with unstable feature evidence - a natural XAI-meets-reject-option question left open.

---

## 3. An explainable deep learning-enabled intrusion detection framework in IoT networks
Keshk, Koroniotis, Pham, Moustafa, Turnbull, Zomaya - Information Sciences 639:119000 (2023). DOI:10.1016/j.ins.2023.119000.
**Read depth: abstract_only.** ScienceDirect (hybrid OA, CC BY-NC-ND) hard-blocks all non-browser access (direct PDF, /pdfft, /am/ URL, jina proxy → captcha); Unpaywall/OpenAlex list **no repository copy** ("any_repository_has_fulltext": false); no arXiv/CORE/UNSW mirror found. Abstract recovered via OpenAlex; method/evaluation details cross-checked against two corpus papers that describe it (the XAI-for-NTA survey `tmp-xai-survey-nta.txt` and the multicollinearity study `tmp-multicollinearity.txt`).

### What it is (from abstract, verbatim core)
"This paper proposes a novel explainable intrusion detection framework in the Internet of Things (IoT) networks. We have developed an IDS using a Short-Term Long Memory (LSTM) model to identify cyberattacks and explain the model's decisions. This uses a novel set of input features extracted by a novel **SPIP (S: Shapley Additive exPlanations, P: Permutation Feature Importance, I: Individual Conditional Expectation, P: Partial Dependence Plot)** framework to train and evaluate the LSTM model. The framework was validated using the **NSL-KDD, UNSW-NB15 and TON_IoT** datasets. The SPIP framework achieved high detection accuracy, processing time, and high interpretability of data features and model outputs compared with other peer techniques."

### XAI evaluation (as far as retrievable)
Per the abstract plus the survey's description: **downstream-utility evaluation** - "Keshk et al. evaluate the performance achieved when utilizing only the **top-20 features highlighted by SHAP or PFI, or by combining insights from both techniques**. Notably, they also investigate how much **training and detection times are reduced**." I.e., explanation quality is operationalized as detection accuracy + processing time of XAI-selected feature subsets; "high interpretability" is asserted, with global+local explanations (SHAP/PFI global; ICE/PDP per-feature behavior). **No explanation-faithfulness or explanation-ground-truth metric is visible in any retrievable material.** (Caveat: full text unverified.)

### Ground truth used (for explanations)
**none** visible in retrievable sources.

### Key numbers
Not retrievable (paywalled). ~236 citations (S2, 2026-08).

### Stated limitations
**Not retrievable** - full text paywalled; abstract contains no limitations statement.

### My gap observations
- SPIP folds XAI into **feature selection**, so the evaluation (accuracy/time of the reduced model) measures *feature-subset utility*, not whether SHAP/PFI/ICE/PDP faithfully explain the trained LSTM; a random-subset or mutual-information baseline could plausibly match it.
- A citing study in my corpus (multicollinearity paper) reports: Keshk et al. "highlight multicollinearity in the ToN_IoT dataset. However, no analysis or addressing of multicollinearity in UNSW-NB15 is presented. **This omission leads to unstable SHAP and PFI explanations** and reduced overall explainability results for this dataset." - third-party evidence that the explanations are fragile under correlated features, unmeasured in the original.
- All three benchmarks are tabular-feature IDS datasets with documented labeling/redundancy issues (NSL-KDD lineage from KDD'99, etc.); "interpretability of data features" inherits those artifacts.
- Publishing an *explainability* framework behind a captcha-walled hybrid-OA article with no preprint is itself a reproducibility gap; nobody can verify the SPIP plots.

---

## 4. Benchmarking Attribution Methods with Relative Feature Importance (BAM; batch alias "BIM")
Yang & Kim (Google Brain) - arXiv:1907.09701v2 (Nov 2019; v1 was titled "BIM: …", under review AISTATS 2020).
**Read depth: full_text** (`tmp-bim.txt`).

### What it is
A **ground-truth-by-construction benchmark** for feature-attribution methods. Because absolute feature importance is unknowable ("we do not know which input features are in fact important to a model"), they control **relative feature importance**:
- **BAM dataset**: MSCOCO object pixels pasted into MiniPlaces scenes; 10 object × 10 scene classes; 100k images; every object appears in every scene. Each image has object label Lo and scene label Ls.
- **BAM models**: ResNet50s fine-tuned from ImageNet. fo (object labels) vs fs (scene labels): objects are targets for fo, mere **common features (CF)** for fs. Fine-grained: 10 scene classifiers trained with dog-CF at commonality k∈{0.1..1.0} (fraction of classes containing the CF).
- Relative importance **verified empirically**: removing objects drops fo to random but leaves fs intact; accuracy-drop-on-CF-removal decreases as k increases; 86.7% of correctly classified inputs gain confidence when object CF is removed.

### Metrics (the paper's own names)
1. **Model Contrast Score (MCS)** = Gc(f1) − Gc(f2): difference in average region attribution for the same input across two models with known importance ordering. Also correlated (Pearson ρ) against accuracy-drop curves across k.
2. **Input Dependence Rate (IDR)**: % of inputs where CF region is attributed less than the scene pixels it covers (1−IDR = false-positive rate). Baseline 50%.
3. **Input Independence Rate (IIR)**: for optimized functionally-null patch δ (f(x+δ)≈f(x), δ still looks like a dog), % of inputs where region attribution changes < t (t=10%, visually calibrated).

### Findings / key numbers
- Methods: GradCAM, Vanilla Gradient, SmoothGrad, Integrated Gradients, IG-SG, Gradient×Input, Guided Backprop, Guided GradCAM (+ TCAV via MCS).
- **TCAV and GradCAM best on MCS** (highest correlation with accuracy-drop trend); **GC and VG best on IDR**; on IIR "Most of the methods, with the exception of GC and VG, incorrectly assign much higher attributions to δ for over 80% of the examples". GB "evolves minimally with the edges of the dog always being visible" (consistent with Adebayo'18/Nie'18).
- Rankings differ across metrics ("whether a method is good depends on the final task and its metric of choice"); the cheapest method (VG) is near best on IDR/IIR.
- Explicit critique of perturbation tests: they "assume that there exist a unique set of important features whose removal would cause an accuracy drop… the set of important features may not be unique"; and OOD confound: "it is hard to decouple whether the accuracy drop is due to out-of-distribution data or due to good feature attributions."

### XAI evaluation
The paper *is* the evaluation method: **MCS / IDR / IIR against constructed relative feature importance** (see above).

### Ground truth used
**synthetic** - relative importance is known **by dataset+training construction** (semi-natural images, controlled CF commonality), then sanity-verified via removal-based accuracy drops. (Not architectural: models are ordinary ResNet50s. Not absolute: only *relative* importance is controlled.)

### Stated limitations (near-verbatim)
- "Our metrics are by no means exhaustive-they only focus on false positive explanations."
- "While there is no guarantee that methods performing well on the BAM dataset will assign correct attributions to real images, BAM could be seen as a simpler and easier test to more complex scenarios. If an attribution method fails an easier test, it is also likely to fail harder tests."
- "the choice of t can be further calibrated by human subjects… t depends on human subjects and is application specific."
- "Our work is only a starting point; one can also develop other measures of performance using our framework."

### My gap observations
- **Image-only**: the construction primitive is "paste object into scene." There is no published analogue for **sequential/tabular traffic data** - e.g., injecting a protocol-level "common feature" (a header field or handshake token present across k% of app classes) into flows to get controlled relative importance. This is a directly transplantable but unoccupied design for NTC.
- The verification of "known" relative importance itself uses **gray-fill removal** - an occlusion proxy of the same family they criticize; the ground truth is therefore construction+proxy-verified, not axiom-derived.
- Region-average attribution gc assumes spatially contiguous concepts; correlated, non-spatial traffic features break this aggregation.
- Only false positives are measured; false negatives (important features attributed low) remain untested - same asymmetry my project could close.

---

## 5. An Explainable Machine Learning Framework for Intrusion Detection Systems
Wang, Zheng, Yang, Wang - IEEE Access 8:73127-73141 (2020). DOI:10.1109/ACCESS.2020.2988359.
**Read depth: full_text** (`tmp-wang-access.txt`; note: Tables 3 (classifier performance) content is an image and did not extract - numbers unavailable to me).

### What it is
Claimed "**first use of the SHAP method to give explanations for IDSs**". Framework = SHAP local + global explanations over any IDS; demonstrated on **NSL-KDD** (KDDTrain+/KDDTest+; 41→122 features after one-hot; min-max normalized) with two PyTorch fully-connected DNNs (122-100-50-30-out; ReLU; Adam lr 0.01, 500 epochs): a **one-vs-all** bank of 5 binary classifiers and a **multiclass** 5-way classifier - compared for how "explainable" each is.
- Local: KernelSHAP-style Shapley values, force-plot visualization (Lundberg's hypoxaemia style); averaged over 100 randomly selected Neptune flows.
- Global 1: mean |SHAP| top-20 features per attack class (beeswarm summary plots).
- Global 2 (novel): **interval-averaged Shapley values** - feature range divided into intervals, mean SHAP per interval per specific attack type (Eq. 9), broken-line plots (e.g., wrong_fragment=1 → Pod, =3 → Teardrop).

### XAI evaluation (exact mechanisms - no named metric)
1. **Plausibility vs. author-curated domain knowledge**: Table 4 maps each DoS attack to its expected features ("Neptune… always have high SYN error connections"; wrong_fragment↔Teardrop/Pod; service_ecr_i↔Smurf; srv_serror_rate↔Land/Neptune; srv_count↔Back). Explanations judged good because "the interpretation results… are consistent with the characteristics of the specific attacks."
2. **Coincidence rate with a prior feature list**: top-20 SHAP features compared to the features Staudemeyer & Omlin extracted with a **decision tree** (SACJ 2014). "For the DoS attack, the eight features extracted by the one-vs-all classifier are the same as those extracted by Staudemeyer… totally accounting for **73%**" (Table 6 gives per-class coincidence rates).
3. **Cross-classifier comparison**: one-vs-all vs multiclass explanations for the same attacks (13/20 identical top-20 features for DoS/Probe/R2L; 10/20 for U2R); conclusion that one-vs-all explanations are more attack-relevant (multiclass's DoS top-20 contains R2L-ish features like num_failed_logins), hence "security experts can optimize the structures of the IDSs."
**No faithfulness, deletion, stability, or user-study evaluation of any kind.**

### Ground truth used
**human_expert** - strictly: an informal, author-curated expert mapping of attacks→characteristic features (Table 4, drawn from attack semantics) used as the plausibility reference, plus a literature feature list (itself machine-derived via decision tree) used for the quantitative "coincidence rate". No independent expert elicitation, no per-instance annotation.

### Key numbers
- DoS feature coincidence with Staudemeyer: 8/11 features, 73% (both classifiers); one-vs-all more coincident overall (Table 6).
- Local example: one-vs-all 93% vs multiclass 89% confidence that averaged Neptune flows are DoS.
- Classifier accuracy/precision/recall/F1 defined (Eqs. 11-14) and reported in Table 3, but the table did not survive text extraction; text says only "the two classifiers used in the experiment have good classification performances."
- NSL-KDD test has 16 novel attack types not in training (37 vs 21).

### Stated limitations / future work (near-verbatim, §VI)
"The present work has room for improvement. Firstly, more datasets for network intrusion detection systems can be used to demonstrate the feasibility of the framework. Secondly, although SHAP has fast computation for interpreting machine learning models compared with computing Shapley value directly, **it is still not possible to work in real-time**. Thirdly, the SHAP method can be explored on more sophisticated attacks, like Advanced Persistent Attacks (APTs). … Further work can focus on experimenting on more datasets, making the framework work in real-time, and explaining more sophisticated attacks."

### My gap observations
- The two evaluation devices are both **plausibility proxies**: (a) narrative agreement with what the authors already believe about attacks, and (b) agreement with **another model's** (decision tree's) selected features - treating inter-method agreement as correctness. Neither can detect a faithful-but-implausible or plausible-but-unfaithful explanation; Debugging Tests' human-study result (users can't use attributions to catch defective models) directly undermines this style.
- KernelSHAP's absent-feature simulation draws random background values → **off-manifold coalitions** over one-hot + highly correlated NSL-KDD features; never discussed (and the later multicollinearity literature shows SHAP instability exactly here).
- The structural recommendation (one-vs-all "explains better") is drawn from plausibility alone; an equally consistent reading is that the multiclass model genuinely uses cross-class contrast features (absence of R2L indicators *is* evidence for DoS) - i.e., the "worse" explanation may be the more faithful one. The paper cannot distinguish these without ground truth.
- Averaging SHAP over 100 Neptune flows before display can manufacture a clean story from heterogeneous per-flow explanations.
- NSL-KDD (1998-derived) as the sole dataset; novel-attack test split never analyzed through the explanation lens (a missed natural experiment: do explanations degrade on the 16 unseen attack types?).

---

## 6. Debugging Tests for Model Explanations
Adebayo, Muelly, Liccardi, Kim - NeurIPS 2020; arXiv:2011.05429.
**Read depth: full_text** (`tmp-debugging-tests.txt`; appendix figures/refs skimmed).

### What it is
Asks "**which explanation methods are effective for which classes of model bugs?**" Categorizes bugs by pipeline stage - **data contamination** (spurious correlation; mislabeled training examples), **model contamination** (re-initialized weights), **test-time contamination** (OOD inputs) - then injects each bug and tests whether 15 feature-attribution methods reveal it: Grad, SmoothGrad, SmoothGrad², VarGrad, Input⊙Grad, IntGrad, Expected Gradients, LIME, KernelSHAP, Guided BP, DeconvNet, LRP-EPS, LRP-SPAF, PatternNet, PatternAttribution. Testbeds: BVD-CNN (5 conv + 3 FC, birds-vs-dogs from Caltech-UCSD + Cats-v-Dogs, 94% acc), VGG-16/ImageNet, MNIST/FashionMNIST. Plus a **54-person IRB human-subject study** (QA-tester framing; 5-point Likert "recommend model for sale"; motivation selection).

### XAI evaluation (exact mechanisms)
- **Spurious-correlation bug**: birds pasted on sky, dogs on bamboo (Places backgrounds); model verified to have learned the shortcut (97% on background-only test). Attributions compared via **SSIM to two constructed "ground truth" masks**: GT-1 (all relevance on background, none on object) and GT-2 (GT-1 weighted by the attribution of the object-free background). Calibration: random-Gaussian-attribution SSIM ≈ 3e-06.
- **Mislabeled-example bug**: 10% flipped labels (model 93.2/91.7/88% train/val/test acc); compare attribution of an input under correct-label vs wrong-label training via SSIM.
- **Model contamination**: successive top-down re-initialization of VGG-16 (Adebayo'18 cascading randomization); SSIM + Spearman rank correlation vs trained-model attributions.
- **OOD**: attributions of FMNIST digits under in-domain vs out-of-domain models (MNIST, BVD-CNN, VGG-16); SSIM + rank correlation.
- **Human study**: Likert recommendation + selected motivations across 5 model conditions × 3 methods (Grad, SmoothGrad, IntGrad).

### Findings / key numbers
- Spurious: detectable - SSIM-GT2 range **0.78-0.98** across all 15 methods.
- Mislabeled: NOT detectable - SSIM between correct- and wrong-label attributions **0.73-0.99** ("visually similar").
- Model contamination: "**modified back-propagation methods are parameter invariant**" - GBP, DeconvNet, PatternNet, PatternAttribution, LRP-SPAF, DeepTaylor invariant to higher-layer weights (corroborating Sixt et al.'s rank-1 convergence proof).
- OOD: **high visual similarity but essentially zero rank correlation** (e.g., VarGrad SSIM 0.87-0.93 with RK ≤ 0.37; most methods RK ≈ 0) → "debugging solely based on visual inspection might be misleading."
- Human study: normal model median Likert 4/4/3; spurious model 2/2/3 with wide spread - "users are uncertain… do not out-rightly reject the model"; for mislabeled/top-layer/OOD conditions "participants overwhelmingly rely on the model's prediction to make their decision", "rarely" on attributions.

### Ground truth used
**interventional** - bugs are deliberately injected pipeline manipulations whose presence/location is known (label flips, weight re-initialization, domain shift), and explanations are scored on whether they react/detect. The spurious-bug test additionally has **synthetic constructed ground-truth masks** (GT-1/GT-2) from the dataset design - a synthetic sub-component inside the interventional paradigm.

### Stated limitations (near-verbatim, §6)
- "The bug characterization presented only covers the standard supervised learning pipeline and might not neatly capture bugs that result from a combination of factors."
- "We only focused on feature attributions: however, other methods such as approaches based on 'concept' activation (TCAV), model representation dissection, and training point ranking might be more suited to the debugging tasks studied here. Indeed, initial exploration of… TCAV and training point ranking based on influence functions suggests that these approaches are promising."
- "our finding that the participants mostly relied on the labels instead of the feature attributions might be a consequence of the dog breed classification task. **It is unclear whether participants would still rely o[n] model predictions for tasks in which they have no expertise or prior knowledge.**"

### My gap observations
- The last stated caveat is precisely the **NIDS setting**: analysts often *cannot* judge a flow's label from raw features the way study subjects judged dog photos, so whether the "users ignore attributions" result transfers to security operators is an open empirical question - and no NTC equivalent of this human study exists in my corpus.
- The bug taxonomy transplants cleanly to traffic: spurious correlation ↔ dataset artifacts (e.g., CICIDS attacker-IP/TTL shortcuts already documented elsewhere in my corpus), mislabeling ↔ DPI ground-truth errors, OOD ↔ zero-day traffic (cf. RTC paper in this batch). **Nobody has run injected-bug detection tests for NIDS/NTC explainers.**
- Their SSIM-to-mask scoring needs a spatial mask; tabular/flow equivalents would need a feature-subset ground truth - again the missing NTC construction.
- Negative result framing matters for my thesis: this paper shows even *with* known interventional ground truth, most attribution families fail two of four bug classes; applied security papers (e.g., Wang et al., this batch) cite attribution plausibility as validation without any such control.

---

## Batch-level synthesis (for the journal paper)
This batch cleanly stratifies the literature into the three layers my gap analysis needs:
1. **Pure NTC classifiers, zero XAI** (RTC 2015; MIMETIC 2019): define the models, datasets, and operational needs (zero-day triage, mobile app labeling) that explanations should serve. RTC even contains a manual-inspection loop begging for explanations; MIMETIC is the exact architecture later "explained" by the UNINA XAI line. Neither displays nor evaluates any explanation. Both establish TC-label ground truth via DPI/controlled capture - never explanation ground truth.
2. **Applied XAI-for-IDS** (Wang 2020; Keshk 2023): explanation "evaluation" = plausibility narratives against author-curated attack knowledge, agreement with a prior model's feature list (73% "coincidence"), or downstream accuracy/time of XAI-selected top-20 feature subsets. No faithfulness metric, no ground truth, no stability analysis (and third-party evidence of SHAP/PFI instability under multicollinearity for Keshk).
3. **Ground-truth-construction methodology, images only** (BAM 2019; Debugging Tests 2020): the vision community already built the two paradigms the security side lacks - synthetic relative-importance datasets (BAM: MCS/IDR/IIR) and interventional bug injection with constructed masks + human studies (Debugging Tests) - and both papers explicitly warn that plausibility and visual inspection are unreliable, which is exactly the evaluation mode layer-2 papers rely on.
**The unoccupied square**: no work constructs BAM-style controlled relative importance or Debugging-Tests-style injected bugs in *traffic representations* (payload bytes, packet-field sequences, flow statistics) to ground-truth-evaluate the SHAP/attribution pipelines that layer-2 papers deploy on NSL-KDD/UNSW-NB15/TON_IoT. The batch also shows a reproducibility fault line: the methodology papers open-source everything, while the applied security papers sit on paywalled venues (Keshk: no accessible full text at all) and NDA'd datasets (MIMETIC).
