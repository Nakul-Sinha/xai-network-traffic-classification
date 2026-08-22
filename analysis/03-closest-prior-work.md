# Closest prior work, and exactly how the proposed paper differs

The gap survives only if it survives these five. Each is the nearest neighbour along one axis.

---

## 1. Alquliti, Karafili, Kang - "Evaluating Explanation Quality in X-IDS Using Feature Alignment Metrics"
arXiv 2505.08006, Univ. of Southampton, May 2025. **The nearest neighbour overall.**

**What they do.** Define FAP / FAR / FAF1 - precision, recall, F1 of a SHAP top-k feature set against
"domain-informed feature sets" derived by mapping CICIDS2017 attack classes to MITRE ATT&CK detect
tactics and on to D3FEND. Evaluated at instance, class and dataset level, on RF / DNN / CNN-BiLSTM.

**Their result.** Alignment is poor. Precision@5 = 0.09 (RF), 0.30 (DNN), 0.17 (CNN-BiLSTM);
best F1 at k=40 is 0.32. For the infiltration and bot classes the derived feature set is *empty*,
giving structurally zero recall.

**Their own reading of it.** They treat the mismatch as a possible defect of the knowledge base:
"the feature sets might need to be revisited or refined."

**Why that is the opening.** Their reference is *what an expert believes should matter*. That measures
**plausibility**. When SHAP disagrees with it, three explanations are indistinguishable:
  (i) the attribution is wrong, (ii) the ATT&CK-derived set is wrong, (iii) **the model is right about
  itself and is genuinely using something non-semantic - a shortcut.**
They cannot separate these. An *interventional* reference can, because it measures what the model
actually depends on rather than what it ought to depend on.

**Sharper still.** Given that CICIDS2017 models are *known* to ride artifacts (TTL 64 vs 128, TCP
appendices, RST packets for the Bot class), option (iii) is not hypothetical - it is likely the
dominant cause. Which yields a testable and rather provocative prediction:

> On a shortcut-driven traffic classifier, **plausibility and causal faithfulness are anti-correlated**.
> An explanation that scores well on FAP is, precisely for that reason, likely to be causally wrong.

Measuring both on the same models, and showing they diverge, subsumes their contribution rather than
competing with it.

---

## 2. Jacobs et al. - TRUSTEE / "The Emperor has no Clothes" (CCS '22)
**What they do.** Extract a high-fidelity decision tree from a black-box network model; read the tree
to diagnose underspecification. Seven case studies, all artifact-available.
**Overlap.** They perform the one published causal intervention in this space (tamper bytes 43/47/49).
**Gap left.** The intervention is a *validation footnote* on one case, not a method or a benchmark.
They never evaluate SHAP/IG/LIME/attention at all. Their tool *is* an explainer, and they show it can
be causally wrong - they do not follow that thread.

---

## 3. Wickramasinghe, Shaghaghi, Tsudik, Jha - SoK (IEEE S&P '25), arXiv 2503.20093
**What they do.** 348 feature-occlusion experiments over SOTA classifiers; three snags (legacy
datasets, design oversights, unsubstantiated assumptions). Show ISCXVPN2016 is 98.9% *unencrypted*;
ET-BERT decides entirely from headers (header-only occlusion reproduces baseline exactly, payload-only
collapses 0.63 -> 0.12); anonymising SII drops ET-BERT 0.96 -> 0.51 and YaTC 0.90 -> 0.62.
**Overlap.** Occlusion is an intervention, and their occlusion grid is close kin to my ground-truth harness.
**Gap left.** Zero occurrences of explainab*/interpretab*/XAI/SHAP/attribution/saliency in the whole
paper. They build the ground truth and never ask an explainer anything. This is the bridge to build.

---

## 4. Wang, Xie, Wang, Cui - BiasSeeker, arXiv 2601.10180 (Jan 2026)
**What they do.** Model-agnostic statistical detection of shortcut features in raw bytes; 19 datasets.
**Their framing.** They reject XAI on purpose: existing solutions "heavily rely on model-specific
interpretation techniques, which lack adaptability and generality."
**Gap left.** Dataset-side diagnosis, deliberately classifier-independent. Says nothing about whether
a trained model uses a given shortcut, nor whether an explainer would report it. Complementary: their
detector is a good *source of candidate features to intervene on*.

---

## 5. LEXNet - arXiv 2202.05535
**What they do.** Explainable-by-design prototype-layer CNN for traffic. Because the prototype layer
makes the decision regions known by construction, they score Grad-CAM and SHAP against them - and
both post-hoc methods do poorly. Also: ResNet+SHAP costs 6.8e4 us/sample vs LEXNet 102.7 us/sample.
**Overlap.** A genuine ground-truth faithfulness check in traffic classification. Closest on *method*.
**Precision (from my full-text read).** The check is *qualitative and single-sample*: Figure 4b-c shows,
for one flow of one TCP application, that Grad-CAM and SHAP identify "none" of the prototype regions.
No metric, no aggregate, no statistical statement. The claim "post-hoc methods are unfaithful" is
illustrated, not measured.
**Gap left.** The ground truth is *architectural* - it exists only because the model was built to
expose it. It cannot be applied to ET-BERT, YaTC, nPrintML, a 1D-CNN or a Random Forest, which is
what the field actually deploys. An interventional ground truth is architecture-agnostic.

---

## The field says the gap is open, in its own words
- A snowballed survey of **107** XAI-for-network-traffic papers finds only **5** that define any
  explanation-quality evaluation at all, and states plainly that **no dataset with annotated
  explanation ground truth exists for network traffic**.
- Warnecke et al. (the six-criteria framework for security XAI): ground-truth relevance is
  unavailable, so they substitute a deletion-based proxy.
- CADE/drift work: "ground-truth explanations are unavailable in this domain."
- A 2025 X-IDS survey: the literature "does not establish causality or sensitivity of the attributed
  features," and calls for exactly that.

Four independent groups name the same missing prerequisite. Nobody builds it - because in vision and
NLP it genuinely cannot be built cheaply. In networking it can.

---

## 6. Zhao, Boffa, Vassio, Mellia - ShortcutCatcher (Proc. ACM on Networking, 2026, DOI 10.1145/3808671)
**Found via the TRUSTEE citation graph - the newest and most instructive neighbour.**

**What they do.** Automated, model-agnostic shortcut *mitigation*: contrast model behaviour on a
training dataset vs a verification dataset with the same feature schema; use feature explanations to
name critical features; iteratively REMOVE features "that would not be valid in deployment", in a
closed loop, to improve cross-scenario generalisation.

**Relationship to my thesis.** They use XAI as a *trusted instrument*. Nothing in the paper validates
the instrument. My work tests the instrument itself. Two consequences:

1. **Motivation upgrade.** The cost of unfaithful attributions is no longer hypothetical: a published
   pipeline now makes *feature-removal decisions* from attributions. If attributions carry a high
   false-confidence rate (name features with N(F) ~ 0), the loop removes the wrong features;
   if they have blind spots (miss features with high N(F)), the shortcut survives mitigation.
2. **The iterative loop is itself evidence for RQ2.** You need to iterate precisely because removing
   one named shortcut surfaces the next - i.e., redundant substitutable shortcuts (TRUSTEE's Table 3
   phenomenon) are common enough that a one-shot removal does not work. Nobody has *measured* that
   redundancy; my R(M) metric does.

**Differentiation in one line.** ShortcutCatcher asks "how do we use explanations to fix models?";
I ask "are the explanations right about the model in the first place?" - logically prior, unanswered.

---

## 7. Vourganas & Michala - "Stabilising Explainability Fragility in Cybersecurity AI" (arXiv 2605.22529, May 2026)
**The statistical cousin of RQ2.**

**What they do.** Theorem: for feature x_i with VIF > theta, Var(phi_i) >= c*(VIF-1) - multicollinearity
provably inflates SHAP attribution variance across bootstrap resamples; importances become
non-identifiable. First VIF audit of UNSW-NB15; propose VIF-pruning, collinearity-aware aggregation
(CAA), and a fragility-penalty loss (SHARP). Purely statistical machinery: bootstrap variance,
Kendall tau. No interventions, no ground truth, no packets.

**Why it matters to me.**
1. **Mechanism support for RQ2.** Flow features are massively collinear (their audit). Collinear
   features are substitutable; substitutable features produce redundant sufficient sets at the model
   level. Their theorem predicts my R(M) > 1 should be common - but nobody has measured R(M).
2. **Clean differentiation.** They measure *instability of the explainer* (variance across resamples).
   I measure *well-posedness of the explanandum* (does the model admit a unique feature basis at
   all?) plus *correctness* (does the attribution match interventional reliance?). A perfectly
   STABLE attribution can still be causally WRONG - their machinery cannot see that case; TRUSTEE's
   Table 3 shows the case is real.
3. **Their future work names my method space**: "explore causal inference methods." Byte-level
   models also escape their frame entirely (VIF is undefined on raw bytes; my do() operator is not).

**One-line differentiation.** They ask "is the explanation stable?"; I ask "is it true?" - and
instability is only one of the two ways it can fail to be true.
