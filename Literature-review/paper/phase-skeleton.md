# phase.md - SKELETON (to be finalized after deep-read distillation)

> Working title (draft): **"Do Explanations Explain? An Interventional Ground-Truth Benchmark for
> Explainable AI in Network Traffic Classification"**
> Target: journal (primary: IEEE TNSM; alternates: Elsevier Computer Networks, Computers & Security,
> IEEE TIFS if findings skew security-critical).

## Phase 0 - Corpus & positioning  [status: in progress]
- [x] 100+ paper sweep across S2/OpenAlex/arXiv/DBLP
- [x] 105+ adversarially verified claims
- [x] Full-text reads: TRUSTEE, S&P'25 SoK, BiasSeeker, Traffic-Explainer, Alquliti, Warnecke, LEXNet
- [ ] Deep-read of 70-80 papers end-to-end (workflow staged)
- [ ] Distilled gap list + final novelty gauntlet
- [ ] Lock research goal; create private GitHub repo

## Phase 1 - Infrastructure (weeks 1-3)
- Packet-rewriting do() operator (scapy): field-level interventions + dependent-field recomputation
  (checksums, lengths, offsets); PCAP in -> PCAP out; unit tests per protocol field.
- Preprocessing harness: raw-byte windows (ET-BERT/YaTC/1D-CNN conventions) + CICFlowMeter/NFStream
  flow-feature regeneration.
- Dataset acquisition + hygiene: ISCX VPN-nonVPN, CIC-IDS2017 (+corrected variants), USTC-TFC2016;
  document known artifacts per dataset from the literature.

## Phase 2 - Models + ground truth (weeks 3-6)
- Train/fine-tune model zoo: 1D-CNN (raw bytes), RF/XGBoost (flow stats), YaTC or ET-BERT (transformer).
- Track A: controlled artifact injection at strengths p ∈ {0.5, 0.7, 0.9, 1.0}; verify injected
  reliance via N(F) curves.
- Track B: reproduce documented natural artifacts (TRUSTEE x3, SoK SII set, TCP-appendix, TTL).
- Compute ground-truth tables: N(F), S(F), R(M) per model x dataset.

## Phase 3 - The audit (weeks 6-9)
- Explainers: KernelSHAP, TreeSHAP/DeepSHAP, IG, DeepLIFT, LIME, occlusion, attention (+TRUSTEE trees).
- Metrics: rho(attribution, N), P@k, false-confidence rate, blind-spot rate.
- Track D: do proxy metrics (deletion/insertion, fidelity, monotonicity, FAP/FAR) predict rho?
- Track E: plausibility (ATT&CK-derived) vs faithfulness (interventional) on same cells.

## Phase 4 - Secondary experiments (weeks 9-11)
- Drift epoch experiment (agreement decay across time-split data).
- Redundancy deep-dive: R(M) distribution; implications for attribution well-posedness.

## Phase 5 - Writing (weeks 11-16)
- Structure: Intro (two-literatures disconnect) -> Related work (6 lineages) -> Ground-truth
  methodology -> Benchmark -> Audit findings -> Proxy-metric meta-evaluation -> Implications
  (xNIDS/ShortcutCatcher-style consumers) -> Limitations -> Release.
- Artifact release: code + injected-artifact datasets + ground-truth tables (the benchmark itself
  is a contribution others can evaluate new explainers against).

## Success criteria
- Every RQ answerable from produced tables regardless of direction of result.
- All numbers reproducible from one `make all` on public data.
- Zero capital spent; consumer GPU or Colab sufficient.
