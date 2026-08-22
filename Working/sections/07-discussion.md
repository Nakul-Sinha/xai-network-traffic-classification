# 7. Discussion

**The failure is added falsehood, not missed truth.** Across every model, dataset, and planting
strength, the explainers we tested rank a model's genuinely-used feature at or near the top: on the
synthetic benchmark precision-at-k is 1.0, and on real CIC-IDS2017 the destination-port shortcut that
the model most depends on is surfaced by per-class SHAP. What the explainers add is confident,
high-magnitude importance for features the model provably does not use. On the synthetic benchmark
this shows up as gradient-saliency false-confidence around 0.7; on real data it is starker, because
the redundant features are numerous: nine of TreeSHAP's global top ten are packet-length statistics
that are collectively load-bearing but individually near-zero in interventional necessity, and they
outrank the single most necessary feature. An operator reading the explanation cannot separate the
feature the model uses from the many it merely could have used. This is a more dangerous failure than
a low-quality but honest ranking, because the false positives are exactly the plausible-looking
features that invite a wrong intervention.

**Redundancy makes single-explanation evaluation ill-posed, and exactness does not help.** The
reason the false positives appear is structural: traffic data encodes the same discriminative signal
many times over -- two headers that both leak the class, a family of correlated flow statistics -- so
a model is free to commit to one encoding and ignore the rest, and different models (or the same
architecture under a different seed) commit differently. An attribution method that returns a single
importance vector is answering a question with no unique answer. TreeSHAP makes this precise: it
computes exact Shapley values, and it still fabricates confidence in an unused shortcut, because
Shapley values distribute credit according to the correlation structure of the data rather than the
realized reliance of the model. Exactness of the attribution is orthogonal to its faithfulness when
the explanandum is not unique. Our redundancy degree R(M) is the property that has to be measured
before a single-vector explanation can even be interpreted, and it is measurable only by intervention.

**The removal operator is not a detail.** E5 shows that the ranking of explainers by a standard
deletion-style faithfulness score can inverts depending on whether features are removed by
zero-masking or by PacketDO: under the protocol-invalid zero-mask operator the method with zero
false-confidence (occlusion) is ranked worst, below a method with high false-confidence, because the
zero-masked inputs are off-manifold and the resulting deletion curves are not even monotone. Under
the protocol-valid operator the methods that all correctly identify the model's single true shortcut
are, correctly, a statistical tie. Any comparison of explainers for traffic classifiers that used the
zero-masking operator -- the field default -- therefore inherits an ordering that is an artifact of
the operator, not a property of the explanations. The same off-manifold mechanism reappears inside an
explainer: LIME's false-confidence traces to its perturbation kernel sampling constant protocol
fields with unit variance (an artifact of standardizing zero-variance features), i.e. LIME evaluates
the model on impossible packets as part of its own definition.

**Why this matters operationally.** The traffic-classification literature does not stop at displaying
attributions. Deployed and published systems act on them: xNIDS generates active intrusion-response
rules from its explanations, ShortcutCatcher deletes features from the training pipeline based on what
an explainer flags, and analyst-facing tools present attributed features as the justification for an
alert. A false-confidence feature in that setting is not a mislabeled figure; it is a firewall rule
keyed on a coincidence, a genuinely-predictive feature wrongly pruned, or an analyst's trust spent on
the wrong evidence. The interventional reference we provide is the check these pipelines currently
lack: before an attribution is allowed to drive an action, it can be scored against what the model
actually depends on.

**What we do not claim.** We do not claim explanations are worthless, nor that any single method is
uniformly best. Intervention-aligned methods (occlusion, and DeepSHAP at sufficient signal strength)
are the most faithful in our study, but occlusion's advantage is partly structural -- it removes
features much as our ground-truth operator does -- and even it is only as good as the removal
operator it uses. The constructive reading of our results is that faithfulness for traffic
classifiers is achievable, but only with a protocol-valid intervention and an explicit accounting of
redundancy; neither is present in current practice.
