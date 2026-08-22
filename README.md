# Do Explanations Explain? An Interventional Ground-Truth Benchmark for XAI in Network Traffic Classification

Private research repository - literature corpus, gap analysis, proof-of-concept, and paper plan.

## The question
When a network traffic classifier is *known by intervention* to rely on a protocol field, do the
explanation methods the field deploys (SHAP, IG, DeepLIFT, LIME, occlusion, attention) say so -
and when they name a field, does the model actually depend on it?

## Why it is open
- A snowballed survey of 107 XAI-for-traffic papers finds only 5 with any explanation-quality
  evaluation; our own 78-paper deep read measures ~60% using *no* ground truth of any kind.
- Ground-truth attribution evaluation exists in vision (BAM 2019, Debugging Tests 2020) and NLP
  (Bastings et al., EMNLP 2022) - never in network traffic, the modality where interventions are
  exact, on-manifold (checksums recomputed -> valid packets) and protocol-structured.
- TRUSTEE (CCS'22 §7.2, Table 3): a perfect-fidelity surrogate named 3 bytes; tampering them left
  accuracy unchanged (0.959 -> 0.959) - models hold substitutable shortcuts, so explanations can
  pass every proxy metric while being causally wrong. Nobody has systematised this.

## Layout
- `PROGRESS.md` - running log
- `phase.md` - the paper-writing plan (the main planning deliverable)
- `corpus/` - 450-paper deduplicated corpus (raw angle sweeps + merged JSON)
- `analysis/` - verified claims, closest-prior-work, experimental design, gap analysis, novelty corrections
- `poc/` - runnable proof of concept (scapy packet-layer do() -> N/S/R -> explainer audit)
- `scripts/` - corpus tooling (merge, PDF text extraction, deep-read workflow)
