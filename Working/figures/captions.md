**fig1_operator_validity.png**
Fig 1. Per-field protocol-validity of counterfactuals under zero-masking vs PacketDO. Zero-masking is valid only where it is a no-op; PacketDO is valid by construction.

**fig2_false_confidence.png**
Fig 2. False-confidence rate (fraction of confidently-attributed fields with interventional necessity ~0) vs planting strength. Saliency and Integrated Gradients fabricate importance; DeepSHAP/Occlusion do not; TreeSHAP fails at p=1.0.

**fig3_necessity.png**
Fig 3. Interventional necessity N(F). Models commit to tcp.window and ignore the redundant ip.ttl; the null field tcp.sport stays at zero.
