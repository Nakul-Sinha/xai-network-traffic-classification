# Protocol-Valid Faithfulness Evaluation for ML-Based Network Traffic Classifiers

Private research repository for a journal paper (target: IEEE TNSM).

## The paper in one sentence

Deletion-style faithfulness evaluation, imported unchanged from vision and NLP, is invalid for
network traffic because it scores explanations on protocol-impossible inputs; this paper gives a
grammar-valid interventional protocol, validates it on classifiers with known ground truth, and
shows that standard explainers and the field's current metrics both fail it in measurable ways.

## Contributions

1. **PacketDO** - a protocol-valid intervention operator: rewrite a header field, recompute
   checksums/lengths/offsets, re-run the model's own preprocessing. Every counterfactual is a
   valid packet, unlike zero-masking.
2. **A validation benchmark with known ground truth** - planted shortcuts at graded strength
   (never done for traffic) plus documented natural artifacts (CIC-IDS2017 TTL, ISCX header
   misalignment, TCP-appendix flows, SII fields).
3. **The audit** - six explainers (SHAP, IG, DeepLIFT, LIME, occlusion, TreeSHAP) x two model
   families x two datasets, scored on necessity-rank agreement, false-confidence rate and
   blind-spot rate.
4. **The operator-sensitivity result** - whether published explainer rankings survive replacing
   zero-masking with protocol-valid removal.

Evidence the pipeline works: `Experiments/poc/` - Integrated Gradients ranks a field with zero
causal necessity as its number 1 feature at artifact strength p=0.7 (details in
`Experiments/poc/FINDINGS.md`).

## What is to be done (from phase.md)

| Weeks | Work |
|---|---|
| 1-2 | Harden PacketDO + per-field unit tests; E1 operator-validity study |
| 3-4 | Synthetic generator, planted-shortcut models per strength p; behavioral verification |
| 5-6 | Flow-feature pipeline, dataset hygiene, natural-artifact reproduction |
| 7-9 | Full audit matrix (E2, E4, E6); optional ET-BERT table on cloud GPU |
| 10 | Operator-sensitivity study (E5) |
| 11-14 | Writing, reproduction pass, TNSM submission |

Full experiment definitions (E1-E8), threats to validity and scope cuts: see `phase.md`.

## Repository layout

- `phase.md` - the paper plan: claim, contributions, experiment matrix, schedule
- `Resource.md` - citations (as links) for every paper used in this paper
- `Analysis/` - analysis artifacts for the new paper (ground-truth tables, audit results)
- `Experiments/` - experiment code and outputs; `poc/` is the working proof of concept
- `Gaps/` - running log of gaps and obstacles hit while executing the plan
- `Working/` - the manuscript: outline, drafts, figures, bibliography
- `Literature-review/` - the completed literature phase: 450-paper corpus, 78-paper deep read,
  verified claims, 17-gap distillation, prior-work differentiation, novelty corrections

## Status

Literature phase complete (see `Literature-review/PROGRESS.md`). Current: Week 1-2 of the
schedule - PacketDO hardening and the E1 validity study.
