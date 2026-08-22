# 2. Related work

We position our contribution against seven lines of work. The through-line is that each supplies one
ingredient of interventional, ground-truth explanation evaluation for network traffic, and none
combines them.

**Ground-truth evaluation of attributions in other modalities.** The idea of manufacturing a known
feature importance and checking whether an attribution method recovers it originates outside
networking. BAM/BIM pastes a known object into every image of a class so that its relative importance
is known a priori, and finds that common attribution methods produce false-positive explanations.
Bastings et al. inject a lexical shortcut into text with a controlled probability, verify
behaviourally that the model learned it, and score salience methods on recovering it, concluding that
several popular configurations fail even for simple shortcuts. Debugging Tests constructs
spurious-correlation and mislabelling bugs with known ground-truth masks. Our synthetic benchmark is
this protocol carried, for the first time, to network packets, and extended from a binary
shortcut-recovery test to a graded one: we plant shortcuts at four strengths and measure a continuous
interventional necessity rather than a present/absent flag, which exposes methods that fabricate
importance precisely when the true signal is weak.

**Interventions on traffic classifiers.** Networking research already intervenes on traffic to probe
models. TRUSTEE extracts a high-fidelity decision-tree surrogate and, in one case study, tampers with
the bytes it identifies to reveal redundant shortcuts -- the observation that motivates our
redundancy measure, but which TRUSTEE treats as a validation footnote rather than a method. The 2025
IEEE S&P systematization of encrypted-traffic classifiers runs a large occlusion study to expose
overfitting and dataset leakage, but never connects it to explanation methods. Closest to us,
Traffic-Explainer performs checksum-preserving byte swaps and even notes that the swapped packets
remain valid; however, it swaps only the bytes its own explainer nominated, which is a confirmatory
test that can establish sufficiency of a chosen set but cannot detect a blind spot (a used field the
method missed) or a redundant alternative (a disjoint set that is equally sufficient). We invert the
direction of inference: we build an independent interventional reference over all fields and audit
every explainer against it.

**Removal-operator critiques.** The unreliability of deletion-style faithfulness is known in the
attribution-evaluation literature. ROAR shows that removing-and-retraining changes conclusions; ROAD
shows that fixed-value or zero masking -- the network-traffic default -- is the worst imputation and
that better imputations rely on pixel-neighbourhood structure with no packet analogue; Samek et al.
document that the removal scheme changes the AOPC ranking. None of this work adapts the operator to
protocol-constrained inputs, and the resulting protocol-valid removal operator is precisely what we
supply.

**Shortcut detection that trusts explainers.** A recent strand hunts shortcuts in traffic datasets or
models. BiasSeeker detects dataset-specific shortcut features by statistical correlation on raw
bytes, deliberately avoiding model-specific interpretation. ShortcutCatcher removes features an
explainer flags, in an iterative loop, to improve cross-scenario generalization. Both use explanation
or importance as a trusted instrument; neither validates it. Our work is logically prior: it tests
whether that instrument is right about the model in the first place, and the iterative nature of
ShortcutCatcher's loop is itself indirect evidence of the redundancy our R(M) quantifies.

**Plausibility metrics for security XAI.** Alquliti et al. score SHAP explanations of intrusion
detectors against feature sets derived from MITRE ATT&CK and D3FEND, and find poor alignment. This
measures plausibility -- agreement with what a domain expert expects -- which, following the standard
faithfulness/plausibility distinction, is orthogonal to whether the explanation reflects the model.
On a shortcut-driven classifier the two can even move in opposite directions, because the model's
real basis is a non-semantic artifact; measuring the causal axis they cannot is a direct complement
to their work.

**Evaluation frameworks for explanations in security.** Warnecke et al. propose six criteria for
comparing explanation methods in computer security and, lacking ground-truth relevance, adopt a
deletion-based descriptive-accuracy proxy -- the same proxy whose operator we show to be
protocol-invalid. Their framework covers malware and vulnerability detection and includes no traffic
classifier. We supply the ground truth their proxy stands in for.

**Explainer stability under correlated features.** Vourganas and Michala prove that multicollinearity
inflates the variance of SHAP attributions across resamples, making importances non-identifiable, and
audit this on a NIDS dataset. This is a statement about the *stability* of an explainer; it is
distinct from, and complementary to, our question of *well-posedness* -- whether the model admits a
unique feature basis at all. A perfectly stable attribution can still be causally wrong when the
model holds redundant shortcuts, which their variance-based machinery cannot see and which our
interventional R(M) is designed to measure.

Across all seven, the missing prerequisite named repeatedly -- an interventional, protocol-valid,
ground-truth reference for explanation faithfulness in traffic classification -- is the one this paper
constructs.
