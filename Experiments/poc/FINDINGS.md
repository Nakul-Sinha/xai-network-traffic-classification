# PoC findings (run_poc.py, three conditions, ~3 min CPU total)

Setup: scapy-synthesized TCP/IP packets, two classes; weak genuine signal (payload length);
TWO injected class-correlated artifacts - ip.ttl (64/128) and tcp.window (8192/65535) - each
predictive with strength p. MLP on raw first 64 bytes. All interventions are packet-layer
do() operations: field rewritten, checksums/lengths recomputed by scapy, sample re-extracted -
every counterfactual is a valid packet.

## Condition 1 - p=1.0, plain training
Model: 100% test acc. Ground truth: relies ONLY on tcp.window (N=0.513, S=1.000 alone);
ip.ttl has N=0.000 despite being a perfect predictor in the data.
- The model *chose one of two equally valid shortcuts* - measured, not assumed.
- DeepSHAP: names only tcp.window -> false-confidence 0.00. Correct here.
- **IntGrad: assigns ip.ttl 41% relative mass (N=0.000) -> false-confidence 0.50.**
- Occlusion: rho=+1.00, clean (expected: occlusion is itself an intervention).

## Condition 2 - p=1.0, redundant-model (tcp.window bytes randomly masked in training)
Masking forces the model to also learn the backup artifact - the same mechanism as MAE-style
pretraining in YaTC/ET-BERT. Result: reliance spreads (window N=0.340, ttl N=0.133; S=0.823/0.583).
All three explainers correctly name both. FC=0.00 across the board.
- **Testable prediction generated for the real study: MAE-pretrained traffic transformers
  (YaTC, ET-BERT, NetMamba) should exhibit HIGHER redundancy R(M) than plain CNNs - attribution
  becomes structurally harder for exactly the current SOTA model family.**

## Condition 3 - p=0.7 (graded artifact)
Model still single-shortcut (window N=0.370, ttl N=0.003).
- DeepSHAP: false-confidence 0.50 (names ttl at 0.41 rel-mass).
- **IntGrad: false-confidence 0.67 - its #1 ranked feature (ip.ttl, rel-mass 1.00) has
  necessity ~0.** The most confident attribution in the whole run is causally inert.
- Occlusion: still clean.

## What the PoC establishes
1. The full instrument runs end-to-end on consumer CPU in minutes: synthesis -> packet-layer
   do() -> N(F)/S(F)/R(M) -> explainer audit with rho / false-confidence / blind-spot.
2. **False-confidence is real, explainer-dependent, and worsens as artifacts weaken** -
   gradient methods attribute to class-correlated-but-unused fields; the phenomenon TRUSTEE
   observed once is systematic and now measurable on demand.
3. The graded-p design exposes differences invisible at p=1.0 (DeepSHAP clean at 1.0, FC=0.50
   at 0.7).
4. Dataset redundancy != model redundancy: the data had two perfect artifacts; the plain model
   used one; the masking-trained model used both. R(M) must be measured on the MODEL - which is
   exactly why BiasSeeker-style dataset-side detection cannot answer this question.

## Known PoC limitations (to fix in the real implementation)
- Greedy R(M) grows one set until collapse (finds the union, not minimal disjoint sets);
  real implementation needs proper minimal-sufficient-set extraction (e.g., iterative pruning).
- Necessity via single-field resampling underestimates fields with in-model backups; report
  N over field *sets* as well (the sufficiency table already exposes this).
- KernelSHAP/LIME/attention rows not yet included; DeepSHAP/IG/occlusion only.
