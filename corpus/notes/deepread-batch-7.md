# Deep-read notes - Batch 7

Reader focus: (1) how explanation quality is EVALUATED, (2) LIMITATIONS / FUTURE WORK, (3) ground truth used.
Date: 2026-08-22. Batch composition: three XAI-reliability foundations papers, one human-grounded XAI evaluation paper, one canonical raw-bytes NTC classifier, one NIDS benchmark ground-truth critique.

---

## 1. The (Un)reliability of Saliency Methods
Kindermans, Hooker, Adebayo, Alber, Schutt, Dahne, Erhan, Kim - Explainable AI (LNCS 11700) / arXiv:1711.00867 (2017). **Read: full text (PDF).**

### What it does
Introduces the **input invariance** axiom: "a saliency method [should] mirror the sensitivity of the model with respect to transformations of the input." Construction: two networks f1, f2 with *identical weights and predictions by construction* - f2 absorbs a constant input shift m2 into its first-layer bias (b2 = b1 − w^T m2), so f1(x1) = f2(x2) for x2 = x1 + m2 and input gradients are provably equal. Any attribution difference between the two networks is therefore provably an artifact of the method, not the model.

- Model: 3-layer MLP, 1024 ReLU units/layer, MNIST in [0,1] vs [-1,0] encoding; final accuracy 98.3% for both. VGG16/ImageNet used only for reference-point illustration (Fig. 1).
- Methods tested: raw gradients, GuidedBackprop, PatternNet (signal); gradient*input, Integrated Gradients (black-image and zero-vector baselines), Deep Taylor Decomposition (LRP/zero root vs PatternAttribution root); SmoothGrad as a wrapper.

### Results (pass/fail on input invariance)
- Gradients, GuidedBackprop, PatternNet: invariant ("determine attribution entirely as a function of the network/pattern weights").
- gradient*input: fails ("the input shift is carried through to final attribution").
- IG: black-image baseline invariant to mean shift, zero baseline fails; a checkered-box constant shift "causes all IG reference points to fail."
- DTD: LRP/zero root fails; PatternAttribution root invariant by construction (covariance-based root compensates the shift).
- SmoothGrad "inherits the sensitivity of the underlying method."
- "Cat attack": constructed constant shift m2 = s_hat/(df1/dx) − x (clipped to [-0.3, 0.3]) makes gradient*input, IG (both baselines), and DTD-LRP display a hand-drawn cat as the explanation of an MNIST digit - "purposeful misrepresentation" with model weights and outputs untouched.

### xai_evaluation
Binary pass/fail of the **input invariance axiom**, assessed by *visual comparison of saliency heatmaps* across the two by-construction-equivalent networks ("A saliency method that satisfies input invariance will produce identical saliency heatmaps for Network 1 and 2"). No numeric divergence metric is computed; figures carry the evidence.

### ground_truth_used
**Architectural** - the correct target property (identical attributions) is known by construction of the functionally equivalent network pair. This is ground truth about a *required property* of explanations, not about which features are truly important.

### Stated limitations / future work (near-verbatim)
- "Our treatment of input invariance is restricted to demonstrating that there is at least one input transformation (a constant vector shift to the input) that causes numerous saliency methods to attribute incorrectly."
- Normalization "is far from a systematic treatment of the reference point selection as there are input transformations outside of our experiment scope where this would not be sufficient."
- "An urgent research agenda ... is evaluating which methods and/or reference points consistently guarantee reliability for all possible transformations."
- "Guaranteeing the reliability of saliency methods is crucial in tasks where visual inspection of results is not easy... it is unclear how we would catch the same purposeful manipulation or an unintentional misrepresentation in a language or audio model where inspection is not possible or opaque. Paradoxically, these are also the cases where attribution is most needed."

### My gap observations
- Input invariance is a *necessary, not sufficient* condition; a method can pass and still be wrong. The paper never claims otherwise but downstream citations often treat axiom-passing as validation.
- Evaluation is qualitative (heatmap eyeballing) even though a quantitative divergence measure would be trivial to add; MNIST-only quantitative setting; single transformation family.
- Direct NTC relevance nobody exploits: NTC pipelines routinely rescale/shift raw byte values (e.g., /255 normalization, zero-padding, per-feature standardization of flow statistics). Reference-point-dependent methods (IG with zero baseline - the default in most XAI-NTC papers; LRP) are exactly the ones shown fragile, and "zero bytes" is a semantically loaded value in packet data (padding). No XAI-NTC paper I have seen tests input invariance.
- Their closing paradox applies to traffic a fortiori: a human cannot eyeball a byte-heatmap for sanity, so NTC is a domain where axiom-based/construction-based checks are the *only* line of defense - strengthening the case for architectural/synthetic ground truth in our project.

---

## 2. End-to-end encrypted traffic classification with one-dimensional convolution neural networks
Wang, Zhu, Wang, Zeng, Yang - IEEE ISI 2017, pp. 43-48, DOI 10.1109/ISI.2017.8004872. **Read: html_partial.**
(Original PDF is paywalled: IEEE direct PDF, ACM DL, ResearchGate, Scribd, scilit, OUCI all blocked; no arXiv/OA mirror, no Wayback copy, OpenAlex reports oa_status=closed. Content below reconstructed from the verbatim IEEE abstract plus a near-complete third-party section-by-section translation (github.com/SunJackson/PaperDoc), cross-checked against citing surveys; saved to tmp-wang-1dcnn-secondary.txt. Numbers consistent with how the paper is quoted in the literature, but treat fine detail with one grain of salt.)

### What it does
First "end-to-end" (raw-input) method for encrypted traffic classification: a 1D-CNN maps raw traffic bytes directly to class labels, "integrat[ing] feature extraction, feature selection and classifier into a unified end-to-end framework, intending to automatically learn nonlinear relationship between raw input and expected output" (abstract).

- Dataset: public ISCX VPN-nonVPN. Authors relabeled the raw pcaps themselves; Browser vs Streaming ambiguity ("Facebook_video.pcap" etc.) could not be resolved "even after email communication with the authors [of ISCX]," so browser-related files were dropped → final 12 classes (6 regular-encrypted + 6 VPN-encapsulated).
- Input representation: four candidates - {Session, Flow} x {L7 only, All layers}; each unit truncated/padded to first **784 bytes**, converted to IDX via their USTC-TK2016 toolkit (same team's ICOIN 2017 malware paper). Best: **Session + All layers** (session beats flow by avg +1.45% accuracy; All-layers beats L7 by avg +4.85%).
- Model: 1D-CNN vs their prior 2D-CNN; TensorFlow, SGD lr 1e-4, batch 50, ~40 epochs, 10-fold CV, random 1/10 test split; Tesla K40m.
- Four contrastive experiments mirroring Draper-Gil et al. 2016 (the ISCX paper): VPN/non-VPN identification; 6-class non-VPN and 6-class VPN characterization; joint 12-class.

### Key numbers
Both CNNs >80% accuracy; 1D-CNN beats 2D-CNN by up to +2.51% accuracy (precision higher on 11/12 classes, avg +3.75%). Vs the C4.5-with-time-features state of the art: Exp 1 precision +9.4% (non-VPN) / +10.9% (VPN); VPN traffic across Exps 2-4 precision +10.9~13.8%, recall +9.7~13.9%; non-VPN in Exps 2-3 weaker: precision +0.3% but **recall -3.5%**. Headline claim: "11 of 12 evaluation metrics outperform the state-of-the-art method." Class imbalance example: VPN-VoIP 6000 training samples → 99.5% precision; VPN-Email 298 samples → 80%.

### xai_evaluation
**none.** There is no explanation method at all. The only interpretability gesture is visualizing 784-byte units as 28x28 grayscale images and asserting by inspection that "different classes of traffic have obvious distinguishability, and each class of traffic has high consistency" - a subjective eyeball argument, unquantified. Classifier metrics: accuracy, precision, recall only.

### ground_truth_used
**none** (n/a - no explanations to evaluate).

### Stated limitations / future work (from Section V Discussion, via translation)
1. "Regarding traffic representation, we used the first 784 bytes of each session as raw traffic. Since different classes of traffic have different types of packets, a more appropriate number of bytes needs further study."
2. "The current training data is imbalanced, which has a great impact on experimental performance... We plan to study how to improve 1D-CNN performance when training data is imbalanced." (VoIP vs Email example above.)
3. "Experimental results show that the performance on non-VPN traffic is relatively poor. We plan to analyze the detailed reasons and make corresponding improvements." Also: "the recognizability of VPN traffic seems better than non-VPN... detailed reasons will be investigated in future work."

### My gap observations
- The core scientific claim - that the CNN "automatically learns more representative traffic features" - is asserted, never inspected. No attribution, no ablation of header vs payload bytes. This is the archetype of the black-box NTC classifier that the whole XAI-NTC literature then tries to explain post hoc.
- Their own result that **All-layers beats L7-only by 4.85%** is an unexamined red flag: the extra signal lives in unencrypted headers/handshake bytes (they even note TLS negotiation is below L7). Later work (byte-attribution studies, shortcut-learning critiques) shows such models key on ports/addresses/handshake metadata - i.e., the accuracy edge may be exactly the artifact-like features Mahoney & Chan warned about (paper 3 of this batch). Wang et al. had the evidence in hand and drew the opposite (benign) conclusion.
- Label ground truth is itself shaky: manual relabeling with acknowledged unresolvable ambiguity, dropped classes. XAI-NTC papers that "validate" explanations by agreement with ISCX class semantics inherit this label noise.
- Random 1/10 split over preprocessed units (sessions from the same capture on both sides) → likely optimistic; no cross-capture generalization test.

---

## 3. An Analysis of the 1999 DARPA/Lincoln Laboratory Evaluation Data for Network Anomaly Detection
Mahoney & Chan - RAID 2003, LNCS 2820. **Read: full text (PDF via cs.fit.edu mirror).**

### What it does
First data-level analysis of the IDEVAL (DARPA 1999) background network traffic. Shows the simulated background is unrealistically "well behaved," so anomaly detectors get credit for **detections that are simulation artifacts**, and proposes mixing real traffic into IDEVAL to strip the artifacts.

- Comparison corpus: 256 h IDEVAL attack-free inside weeks 1+3 vs 623 h real traffic ("FIT", cs.fit.edu, 50 x 2M-packet weekday traces, Sep-Dec 2002, packets truncated to 200 B, >24,000 remote sources).
- Artifact preconditions: attribute is (1) well behaved in simulated attack-free traffic, (2) NOT well behaved in real traffic, (3) not well behaved in simulated attack traffic.
- Findings (IDEVAL vs FIT): TCP SYN options always exactly 4 bytes MSS=1500 vs 103 first-4-option-byte values; TCP window size 7 values vs 523; remote client source addresses 29 vs 24,924 (power law only in FIT; 45% of FIT addresses appear in a single session vs none in IDEVAL); TTL 9 vs 177 values; TOS 4 vs 44; zero checksum errors in 12M IDEVAL packets vs ~0.02%; no "crud" (nonzero ACK-without-flag, reserved bits, etc.); HTTP 5 user-agents vs 807; SMTP 3/24 distinct HELO/EHLO args vs 1839/1461; SSH 1 client version string vs 32.
- Known artifact examples: TTL values 126/253 appear **only in hostile traffic** ("attacking traffic and background traffic ... were synthesized on different physical machines"); ~half of ALAD/LERAD/NETAD detections come from "anomalous source addresses, including attacks on DNS, web and mail servers, where previously unseen addresses should be the norm."

### Evaluation with mixed traffic
Six detectors - SAD (deliberately trivial: one byte at a fixed packet offset), SPADE, PHAD, ALAD, LERAD, NETAD - on IDEVAL (set S) vs three IDEVAL+FIT mixes (A/B/C), 1999 criteria, 100 false alarms (EVAL tool). **SAD punchline:** watching a single byte (e.g., source-address 3rd byte) detects 79/177 = 45% of attacks on S - "competitive with the top four systems in the 1999 evaluation, which detected 40% to 55%" - and collapses to ~0 on mixed data.
- Detection **legitimacy criteria** (Section 5.3): an author-defined, per-attack-category list of which anomaly features causally relate to which attacks (e.g., source address legitimate only for spoofing DOS or authenticated services; fragmentation legitimate for teardrop/pod; payload anomalies legitimate for server attacks; "No network feature should legitimately detect a U2R or Data attack").
- Result: fraction of legitimate detections rises in every system on mixed traffic - LERAD 56%→83%, ALAD 34%→83%, PHAD 61%→83%, NETAD 48%→67%, SPADE(mode 2) 33%→100%. Residual non-legitimate detections are destination-address anomalies, which mixing cannot remove (FIT adds only one destination host).

### xai_evaluation
Not an XAI paper, but it performs the closest thing 2003 NIDS work has to *explanation* evaluation: each alarm's **triggering anomaly feature** is judged against expert "criteria for legitimate detection," i.e., detections are scored for being *right for the right reason*, and the headline metric is the **fraction of detections judged legitimate**. (Authors concede: "Because this is a subjective judgment, we establish the following criteria.")

### ground_truth_used
**human_expert** - the Section 5.3 legitimacy criteria are an expert-nominated mapping from attack types to causally-appropriate features, used as the reference for judging why-detections. (Additionally, the FIT real-traffic contrast functions as distributional ground truth for realism, but the detection-reason judgment is the expert part.)

### Stated limitations / future work (near-verbatim)
- "We caution that our comparison is based on just one source [of real traffic]... we do not claim that FIT statistics generalize to all sites."
- Mixing "will fail if the IDS is able to model any attribute in the two traffic sources independently or if any attributes modeled by the IDS are missing in the real traffic. We must analyze and possibly modify both the IDS and the real traffic."
- "We also lose the advantage of independent testing and comparison due to privacy issues inherent with real traffic."
- "We do not make any claims about how the six anomaly detection systems we tested would perform on real traffic. Any results we presented on mixed traffic would apply only to the one real source of traffic that we used, are not reproducible..."
- "We analyzed only the inside sniffer traffic... It is likely that simulation artifacts exist in the outside sniffer traffic, and also in the 1998 evaluation (from which the 1999 KDD cup data was generated)."
- "We cannot make any claims with regard to network signature detection or any type of host based detection."

### My gap observations
- This is a 2003 proto-explanation-evaluation: it asks precisely the question modern XAI-NTC rarely operationalizes - *is the feature the model used causally related to the attack, or a dataset artifact?* Its expert legitimacy rubric is never cited by XAI-NTC papers as an evaluation template, though it is directly reusable for judging SHAP/LRP outputs on IDS data.
- Killer implication for the survey: KDD'99/NSL-KDD descend from the 1998 simulation, so **XAI-NTC papers that "validate" explanations because SHAP highlights known-discriminative KDD features (src_bytes, count, service...) may be validating artifact learning**, not model correctness. Feature-importance agreement with an artifact-ridden benchmark is not ground truth.
- The legitimacy criteria are author-defined, single-team, no inter-rater reliability, no statistical testing anywhere in the paper; "legitimate" for debatable cases (single-port attacks) decided by fiat. An honest template would need multiple independent experts.
- The SAD experiment doubles as a model-level sanity check reminiscent of later XAI sanity-check work: if a one-byte detector matches your system, your benchmark (not your model) is doing the work.

---

## 4. Evaluating Explainable AI: Which Algorithmic Explanations Help Users Predict Model Behavior?
Hase & Bansal - ACL 2020, arXiv:2005.01831. **Read: full text (PDF).**

### What it does
Human-subject **simulatability** tests that isolate the causal effect of explanations: forward simulation (predict model output for new inputs after studying explained examples) and counterfactual simulation (predict model output on a perturbed version of an explained input). Five methods: LIME, Anchor, Prototype (case-based, feature-omission importance), Decision Boundary (latent traversal to a counterfactual with evidence-margin path), Composite (all combined).

- Design controls (their contribution over prior tests): (1) explained instances separated from test instances; (2) Pre-phase baseline without explanations ("No prior evaluation includes this control"); (3) data balanced by model correctness (TP/FP/TN/FN equally represented - "users cannot succeed by guessing the true label"); (4) forced predictions on all inputs (no cherry-picking by coverage).
- Tasks/models: movie-review sentiment (Pang et al.), BiLSTM 80.93% test acc; UCI Adult tabular, 2x50 MLP 83.49%; Prototype variants 80.64/81.90.
- Users: 32 trained undergraduates (CS/stats background required), screened; 39 tests, 2166 responses; $15/h.

### xai_evaluation
Metric = **"Change": difference in user simulation accuracy Post minus Pre** ("any improvement in user performance in the Post prediction phase is attributable only to the addition of explanations"), with block-bootstrap two-sided tests over users and items, and a random-effects model for Pre accuracy. Secondary: 7-point Likert **subjective simulatability ratings** ("Does this explanation show me why the system thought what it did?"), and logistic regression of user correctness on ratings.

### Key numbers
- Significant improvements only: **LIME on tabular +11.25 points (p=.014)** (combined tests) and **Prototype on counterfactual simulation +9.53 (p=.032)** across domains. All text-domain effects and all other methods: n.s. (CIs ~±8-13 points). Composite: no overt improvement despite being rated among the best.
- Ratings do NOT predict effectiveness: moving a rating 4→5 associated with between −2.9 and +5.2 pp (text) / −2.6 and +5.3 pp (tabular) change in user correctness - "simply querying humans about explanation quality will not provide a good indication of true explanation effectiveness."

### ground_truth_used
**other** - the gold standard is the *model's actual behavior* on held-out/perturbed inputs (exactly known), used as the target of human prediction. There is no ground truth about explanation content/features; humans are the measurement instrument, not the reference.

### Stated limitations / future work (Section 7, near-verbatim)
- "Forward Tests Stretch User Memory... some users reported that it was difficult to retain insights from the learning phase during later prediction rounds."
- "It may be difficult to algorithmically construct counterfactual inputs that match the true data distribution... Our text counterfactuals are regularly out of the data distribution."
- Fair comparison caveat: "We control for the number of data points between methods, but one could instead control for user exposure time or computation time... It may be that when using such approaches, LIME and Anchor perform better on forward simulation tasks."
- "Given our wide confidence intervals, these results should be considered cautiously. It may also be that other methods do in fact improve simulatability, but we have not precisely estimated this."
- From qualitative analysis: "Better methods will need to distinguish between sufficient and necessary factors in model behavior... Further, they must do so in the appropriate feature space for the problem at hand, especially for models of complex data."

### My gap observations
- The protocol presupposes *human-legible features* (words, census attributes). For NTC's dominant input (raw bytes a la Wang et al., batch paper 2) there is no analogous "read the explanation, predict the model" task a human could perform - the best-controlled evaluation paradigm in XAI is structurally unavailable to byte-level NTC, and nobody in XAI-NTC has adapted it (e.g., to flow-feature level or to analyst-facing artifacts).
- n=32 undergraduates, binary tasks only, wide CIs - the paper honestly reports mostly null results, but the field cites it as "LIME works for tabular"; for NTC flow features (tabular!) the +11.25 result is the single most transferable data point, and untested there.
- The ratings-don't-predict-helpfulness finding indicts the most common XAI-NTC "evaluation": author-judged plausibility of SHAP plots is exactly the subjective rating shown to be uninformative.
- Simulatability measures model-understanding, not feature-truthfulness; a faithful explanation of a shortcut-learning model would score well. Complementary, not substitutive, to ground-truth-based evaluation.

---

## 5. Interpretation of Neural Networks is Fragile
Ghorbani, Abid, Zou - AAAI 2019, arXiv:1710.10547. **Read: full text (PDF).**

### What it does
Defines interpretation fragility: perceptively indistinguishable, **same-prediction** inputs with very different interpretations, and constructs targeted adversarial perturbations against feature-importance methods (simple gradient, DeepLIFT-Rescale, Integrated Gradients; DTD in Appendix E) and exemplar-based influence functions.

- Attacks: random-sign baseline; iterative **top-k attack** (suppress initially most-important k features), **mass-center attack** (max spatial displacement of saliency center of mass), **targeted attack** (concentrate saliency in a chosen region, e.g., a cloud above a truck); single-step gradient-sign attack on influence functions (linearized, targeting top-3 influential training images). L-infinity budget epsilon up to 8/255-scale; P=300 iterations; ReLU→softplus surrogate for gradient computation.
- Setups: 512 correctly-classified ImageNet images / pretrained SqueezeNet; CIFAR-10 / own CNN (73%); roses-vs-sunflowers Inception v3 last-layer (97.5% val) with 1,000 training images for influence functions.

### xai_evaluation
Quantifies interpretation *change* (not correctness) via: **"Spearman's rank order correlation"** between importance vectors before/after perturbation; **"top-k intersection"** (top-1000 pixels ImageNet, top-100 CIFAR, top-5 training images for influence); plus a **center-shift** measure (Appendix E) reported as "the most correlated measure with the subjective perception of change." Constraint checked throughout: predicted label (and roughly confidence) unchanged.

### Key numbers
- Even **random sign perturbation at L-inf=8: <30% overlap** in top-1000 salient pixels on average, all three methods.
- Targeted/center attacks far stronger; integrated gradients "the most difficult one to generate adversarial examples for" (most robust of the three); CIFAR-10 more robust than ImageNet (dimensionality argument via Hessian analysis: relative attribution change scales with the L1 norm of w; fragile directions of interpretation are ~orthogonal to fragile directions of prediction).
- Influence functions: epsilon=8 → only 2 of top-5 influential training images survive; influences before/after "essentially uncorrelated"; random noise alone drops rank correlation to ~0.8 at epsilon≈10.

### ground_truth_used
**none** - all metrics are self-similarity of explanations under perturbation; no reference for what the correct attribution is. (They explicitly frame ground truth as unavailable and measure stability instead.)

### Stated limitations / future work (Discussion, near-verbatim)
- "We do not suggest that interpretations are meaningless, just as adversarial attacks on predictions do not imply that neural networks are useless."
- Crucial epistemic caveat: "the interpretations (e.g. saliency maps) are vulnerable to perturbations, but this does not imply that the interpretation methods are broken... The saliency correctly captures the infinitesimal sensitivity at the two inputs; it's doing what it is supposed to do. The fact that the two resulting saliency maps are very different is fundamentally due to the network itself being fragile."
- "While we focus on the standard image benchmarks..., this fragility issue can be wide-spread in biomedical, economic and other settings where neural networks are increasingly used. Understanding interpretation fragility in these applications and developing more robust methods are important agendas of research."
- Proposed defenses are explicitly tentative: input discretization (thermometer encoding), constraining non-linearity; Appendix J operator-norm regularization is "meant to be suggestive rather than conclusive, since in practice the Lipschitz bounds are rarely tight."

### My gap observations
- The authors' own caveat (fragility of the *model* vs the *method*) undercuts naive use of stability as an explanation-quality metric - yet stability/robustness scores are increasingly reported in XAI-NTC as if they measured explanation goodness. Stability conflates model geometry with method fidelity; only construction-based ground truth can separate them.
- Threat model does not transfer cleanly to traffic: L-infinity pixel perturbations have no analog for protocol-constrained packets (checksums, header semantics, discreteness). Whether *realizable* traffic perturbations (padding, timing jitter, TTL tweaks) can hijack SHAP/IG explanations of an NIDS while preserving the verdict is - to my knowledge - an open, high-value question their framework begs.
- Security framing is ironic for our survey: they attack interpretations of image classifiers and warn of security consequences; in NTC the *attacker actually exists* (evasive malware) and could aim at the analyst's explanation rather than the detector's verdict (alert-triage misdirection). No XAI-NTC work threat-models this.
- "Would not be considered salient by human perception" is asserted, never human-tested; top-1000 intersection thresholds are arbitrary; interestingly their appendix admits the metric best matching perception is center-shift, which has no analog for non-spatial (tabular/flow) inputs.

---

## 6. On the Robustness of Interpretability Methods
Alvarez-Melis & Jaakkola - ICML 2018 WHI workshop, arXiv:1806.08049. **Read: full text (PDF).**

### What it does
Argues **robustness of explanations** - "similar inputs should give rise to similar explanations" - is a key desideratum, and proposes quantifying it with a point-wise **local Lipschitz estimate**:
L_hat(xi) = argmax_{xj in B_eps(xi)} ||f(xi) − f(xj)||_2 / ||xi − xj||_2 (Eq. 1), with a discrete finite-sample variant over test-set neighbors for categorical data (Eq. 2). f is the attribution vector of the interpretability method.

- Estimation: black-box Bayesian optimization (skopt), budget 200 function calls (only 40 for LIME/SHAP "due to higher compute time"), eps=0.1, l-infinity box.
- Methods: LIME, SHAP (black-box); Saliency, Gradient*Input, Integrated Gradients, eps-LRP, Occlusion (DeepExplain implementations).
- Settings: random forests on UCI (glass, wine, ionosphere, leukemia; Boston regression), logistic regression on COMPAS (discrete variant, ~600 test points), CNN/MNIST, ResNet/ImageNet (224x224). Synthetic 2D dataset with linear SVM vs 2-layer NN as motivating illustration (explanations stable for the linear model, erratic for the NN).

### xai_evaluation
The **"Local Lipschitz estimate"** itself is the metric - evaluated relatively across methods ("there is no single 'ideal' value that is universally desirable"). Reported as box-plots over 100 test points (UCI, MNIST); worst-case perturbation pairs displayed. Notable qualitative result: ResNet bull-mastiff example with probabilities 0.7308 vs 0.7307 and "remarkably different" saliency; MNIST Gaussian-noise demo where "the classifier's predicted class probability barely changes ... the interpreter's explanations vary considerably, in some cases dramatically (LIME, Occlusion)."

### Key numbers
- UCI: LIME Lipschitz estimates roughly an order of magnitude above SHAP on several datasets (log-scale Fig. 2; Boston example L=18.17 LIME vs 6.98 SHAP; COMPAS discrete: SHAP 3.63 vs LIME 0.67 - direction varies).
- MNIST (Fig. 6): LIME worst (~6-10), Occlusion next, gradient-based methods lowest (~1-2). Conclusion: "model-agnostic perturbation-based methods are (unsurprisingly) more prone to instability than their gradient-based counterparts."

### ground_truth_used
**none** - robustness is a desideratum measured without any reference explanation. (The linear-SVM synthetic case, where the true explanation is effectively known, is used only as an illustration, not as quantitative ground truth.)

### Stated limitations / future work (Discussion, near-verbatim)
- "A natural question is whether we should expect interpretability methods to be robust when the model being explained is itself not robust... there is probably no absolute answer"; but if the goal is understanding the phenomenon, "it is perhaps necessary to require [the explanation] to be even more [robust than the model]."
- No universal target value: "Although both (1) and (2) are unitless quantities, there is no single 'ideal' value that is universally desirable... what is reasonable will depend on the application and goal of interpretability."
- ImageNet scale: "The size of these images makes it prohibitive to compute (1) repeatedly to estimate dataset-level statistics, so we compute it only for a few images."
- Future: enforce robustness (their self-explaining networks paper), import certified-robustness techniques; "Additional notions of robustness found in that literature would make for interesting complementary evaluation metrics."

### My gap observations
- Same necessary-not-sufficient trap as papers 1 and 5: a constant explanation has L=0 and is useless. The paper says application-dependent; citers rarely do.
- Unequal optimization budgets (200 vs 40 calls) under-attack LIME/SHAP - since they still look *worst*, the ranking survives, but absolute values are incomparable across methods; a point worth making when XAI-NTC papers report single Lipschitz numbers.
- The **discrete, finite-sample variant (Eq. 2) is exactly what tabular flow-feature NTC needs** (categorical ports/protocol fields; meaningless continuous perturbations) - and it is the part of the paper that XAI-NTC robustness papers do not use, defaulting instead to continuous noise on standardized features that generates unrealizable flows.
- eps=0.1 balls in normalized space can cross class-validity or protocol-validity boundaries; no validity constraint on the perturbation - again more severe for traffic than images.

---

## Batch 7 gap synthesis (for the journal paper)

1. **Two-sided ground-truth deficit.** The XAI-methodology papers (1, 4, 5, 6) show the field's evaluation arsenal: construction-based invariance checks (Kindermans - the only one with real, architectural ground truth), stability/fragility proxies with *no* ground truth (Ghorbani, Alvarez-Melis), and human simulatability where the model's own behavior is the reference (Hase & Bansal). Meanwhile the NTC side of the batch shows the *data* has no trustworthy feature-level ground truth either: Mahoney & Chan prove the DARPA/KDD lineage rewards artifact features, and Wang et al. build the canonical raw-byte classifier whose "learned features" are never inspected and whose labels are partly hand-assigned under acknowledged ambiguity. An XAI-NTC paper that explains a Wang-style model on a KDD-descended benchmark and eyeballs the SHAP plot is stacking every weakness in this batch.
2. **Proxy metrics are necessary-condition tests being cited as validation.** Input invariance, rank-correlation-under-attack, and local Lipschitz all detect *failure*; passing them proves nothing about correctness (a constant explanation aces two of three). Ghorbani et al. even state the deeper confound: instability may be a property of the model, not the method. Survey should classify these as falsification tools, not quality metrics.
3. **The best-controlled evaluation paradigm is structurally unavailable to byte-level NTC.** Hase & Bansal's simulatability protocol requires human-legible features; raw-byte inputs (784-byte sessions) defeat it. Kindermans et al. independently note that domains without visual inspection are both where reliability cannot be eyeballed and where attribution is most needed. Network traffic is the extreme case of this paradox - the strongest argument that XAI-NTC needs *constructed* ground truth (synthetic traffic with planted discriminative features, or architecturally transparent reference models) rather than borrowed image-domain proxies.
4. **An unused 2003 template.** Mahoney & Chan's per-attack "legitimacy criteria" - expert mapping from attack type to causally appropriate features, with fraction-legitimate as the metric - is a ready-made, never-adopted template for expert-grounded evaluation of NIDS explanations; it needs only multi-rater validation to be publishable methodology today.
5. **Unstudied threat model.** Ghorbani-style explanation attacks under *realizable traffic perturbations* (protocol-valid, semantics-preserving) against SHAP/IG explanations of deployed NIDS, with the goal of misdirecting analyst triage, appear to be an open problem; none of the batch (or, to my knowledge, the XAI-NTC corpus) addresses it.
6. **Metric transfer failures.** Center-shift (most perceptually valid per Ghorbani) is spatial-only; discrete Lipschitz (Alvarez-Melis Eq. 2) fits flow features but is unused; simulatability "Change" with security analysts instead of undergraduates is unattempted. Each is a concrete, citable methods gap.

### Read-depth ledger
| # | Paper | Depth | Source |
|---|-------|-------|--------|
| 1 | Kindermans 2017/2019 | full_text | arXiv PDF |
| 2 | Wang ISI 2017 | html_partial | IEEE abstract + third-party full translation (GitHub PaperDoc), cross-checked; original PDF paywalled everywhere tried |
| 3 | Mahoney & Chan RAID 2003 | full_text | cs.fit.edu/~pkc/papers/raid03.pdf |
| 4 | Hase & Bansal ACL 2020 | full_text | arXiv PDF |
| 5 | Ghorbani AAAI 2019 | full_text | arXiv PDF (incl. appendices) |
| 6 | Alvarez-Melis & Jaakkola WHI 2018 | full_text | arXiv PDF |
