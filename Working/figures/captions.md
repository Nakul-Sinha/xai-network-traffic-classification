Figure numbering follows the manuscript body (citation order). Image filenames predate the
renumbering and lag it by design; the mapping below is authoritative. Figures are regenerated with
number-matched filenames in the Phase E figure pass.

**Fig 1 -> fig1_operator_validity.png**
Fig 1. Per-field protocol-validity of counterfactuals under zero-masking vs PacketDO. Zero-masking is valid only where it is a no-op; PacketDO is valid by construction.

**Fig 2 -> fig3_necessity.png**
Fig 2. Interventional necessity N(F). Models commit to tcp.window and ignore the redundant ip.ttl; the null field tcp.sport stays at zero.

**Fig 3 -> fig2_false_confidence.png**
Fig 3. False-confidence rate (fraction of confidently-attributed fields with interventional necessity <= 0.05) vs planting strength, mean +/- sd over 5 seeds. Gradient saliency fabricates importance robustly (0.68-0.74); Integrated Gradients and DeepSHAP do so conditionally (nonzero in 3/5 and 2/5 seeds respectively at their worst strength); occlusion is clean (partly by construction, see E5); RF TreeSHAP is bimodal, fabricating confidence exactly when the model commits to one of two redundant shortcuts.
