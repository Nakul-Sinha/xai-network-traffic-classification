# 1. Introduction

Machine learning now underpins a large fraction of deployed network traffic analysis: encrypted
traffic classification, application identification, and network intrusion detection are all dominated
by deep models that operate on raw packet bytes or on flow-level feature vectors. Because these
models are opaque and because operators are reluctant to act on decisions they cannot interrogate, a
second, rapidly growing literature attaches post-hoc explanation methods -- SHAP, LIME, gradient
saliency, attention maps -- to traffic classifiers, and presents the resulting feature-importance
scores as evidence that the model is trustworthy. This explainability literature is now large enough
to have its own surveys.

What almost none of it does is check whether the explanations are *correct*. In a recent systematic
survey of 107 works on explainable AI for network traffic analysis, only five define any
explanation-quality metric at all, and the survey reports that no public traffic dataset carries
ground-truth feature importance against which an explanation could be scored. In practice,
explanations are displayed as plots and declared meaningful. The few papers that do attempt a
quantitative check substitute a proxy: either agreement with what a human analyst expects (which
measures plausibility, not faithfulness), or a deletion test that removes the features an explainer
called important and measures how much the prediction changes.

This deletion test is the standard notion of faithfulness imported from computer vision and NLP, and
it is the quiet foundation under most quantitative claims in the field. Our starting observation is
that it is not merely unvalidated for network traffic -- it is invalid. Removing a feature by setting
it to zero, the default in every deletion, occlusion, and AOPC-style metric, produces a byte string
that is no longer a well-formed packet: its header checksum no longer matches its contents, or its
length field disagrees with its actual length. Such a packet could never appear on a network, so the
model is being queried far outside the distribution it was trained on, and the resulting "importance"
is partly an artifact of that extrapolation. The problem is strictly worse than the analogous
critique in vision, because a packet's fields are bound to one another by protocol grammar: you
cannot change one field and leave the rest untouched and still have a legal packet.

There is a second, deeper problem that the traffic-classification setting makes unusually visible.
Traffic datasets are riddled with *shortcuts* -- features that predict the label in the dataset
without reflecting any real property of the traffic, such as the fixed time-to-live of the machine
that generated a class of attacks, or an artifact of the flow-metering tool. A model that learns a
shortcut can be perfectly accurate on held-out data and still be wrong about the world. The most
striking published demonstration of the danger for explanations comes from TRUSTEE: a decision-tree
surrogate that reproduced a traffic classifier's decisions with perfect fidelity (an F1 of 1.00)
identified three specific header bytes as the basis of its decisions; yet when the authors tampered
with exactly those three bytes, the model's accuracy did not move, because it had learned several
mutually substitutable shortcuts and simply fell back on another. A perfect-fidelity explanation was
causally wrong. This failure mode -- redundant shortcuts that make the target of an explanation
non-unique -- has never been systematically measured, in traffic classification or anywhere else.

The two literatures that would need to meet in order to address this do not. On one side, the
explainability-for-security literature produces attributions and never intervenes on the model to
check them. On the other, a rigour-focused strand of networking research (TRUSTEE, the 2025 IEEE
S&P systematization of encrypted-traffic classifiers, and recent shortcut-detection frameworks)
routinely intervenes on traffic -- occluding fields, tampering bytes, ablating features -- to expose
what models really use, but never calls these interventions explanations and never evaluates an
explainer with them. As a concrete measure of the gap: the S&P 2025 systematization runs 348 feature
occlusion experiments and contains not a single occurrence of the words explainable, interpretable,
SHAP, attribution, or saliency.

We argue that networking is, in fact, the ideal setting in which to close this gap, for a reason that
does not hold in vision or NLP: interventional ground truth for explanations can be constructed
exactly and on-manifold. Protocol field semantics are known, so an attribution has a defined
referent; and packets are rewritable, so a field can be set to a chosen value and the packet
regenerated as a legal packet. Ground-truth evaluation of feature attribution has been established in
vision (by pasting known objects into images) and in NLP (by injecting known lexical shortcuts into
text), and in both cases it revealed that popular attribution methods produce false-positive
explanations. Neither has ever been done for network traffic -- the one modality where the
intervention that defines the ground truth is exact, protocol-structured, and produces inputs the
model could actually receive.

This paper builds that missing instrument and uses it. Our contributions are:

- **PacketDO (Section 3):** a protocol-valid intervention operator. It sets a chosen protocol field
  to a value resampled from the field's pooled empirical distribution and recomputes every field that
  structurally depends on it -- checksums, lengths, offsets -- so the counterfactual is always a
  well-formed packet. We show experimentally (E1) that the deletion default is protocol-invalid for
  the large majority of intervenable fields, while PacketDO is valid by construction.

- **An interventional ground-truth benchmark (Sections 3-4):** using PacketDO we define and measure,
  for a trained model, the necessity and sufficiency of each protocol field and a redundancy degree
  R(M) -- the number of disjoint, individually-sufficient shortcut sets the model holds. These are
  measured by intervention, not assumed. The benchmark combines synthetic traffic with shortcuts
  planted at graded strength (extending the binary shortcut-injection protocol from NLP to a graded,
  packet-level one) with real datasets carrying documented artifacts.

- **An audit of six widely used explainers against that ground truth (Section 5),** reporting for
  each how well its attribution ranking matches interventional necessity, how often it confidently
  attributes importance to a field the model provably does not use (false-confidence rate), and how
  often it misses a field the model does use (blind-spot rate).

- **The operator-sensitivity result (Section 6):** we show that an explainer's measured faithfulness
  can depend on whether features are removed by zero-masking or by PacketDO, so that faithfulness
  comparisons in the literature that used the zero-masking operator are called into question.

Our findings are not that explanations are useless. They reliably surface a model's true shortcut as
a top-ranked feature. The danger we quantify is subtler and, for an operator staking a decision on an
explanation, more insidious: explainers simultaneously assign high importance to redundant features
the model does not use, and they cannot be told apart from the used feature by inspection; even exact
Shapley values exhibit this when a model commits to one of several equivalent shortcuts. Because
deployed systems now take real actions on these attributions -- generating intrusion-response rules,
deleting features from training pipelines, presenting features to human analysts -- getting the
faithfulness question right is not a matter of tidier figures. We release the operator, the
benchmark, and the ground-truth tables so that new explainers and new classifiers can be scored
against a reference that reflects what a model does, not what a dataset happens to correlate with.
