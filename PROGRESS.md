# Progress log

## Phases 0-5: COMPLETE (with adversarial verification after each)

- **Phase 0** compute/plan: local RTX 4050 + Kaggle; GCP billing closed (unneeded). Analysis/00-compute-decision.md
- **Phase 1** PacketDO operator (C1) + E1: zero-mask 22.4% vs PacketDO 100% protocol-valid. 42 tests pass.
  Verified by a 4-agent org (RFC-1071 cross-check); 2 prose overclaims + a tcp.ts bug fixed.
- **Phase 2** synthetic planted-shortcut benchmark (E2/E3/E4), 5 seeds. Explainers find the shortcut
  (precision@k=1.0) yet fabricate importance: Saliency FC 0.68+/-0.04, TreeSHAP bimodal, IG/DeepSHAP
  conditional. Analysis/E2-E4-synthetic-benchmark.md
- **Phase 3** real data CIC-IDS2017 (ORG-A): destination-port shortcut is #1 necessity yet TreeSHAP
  ranks it 5-9th (6/6 runs); Engelen TCP-appendix artifact reproduced. Experiments/realdata/
- **Phase 4** E5 operator flip (ORG-B): under zero-mask the faithful method (occlusion) ranks LAST;
  under PacketDO all tie. KernelSHAP/LIME added; LIME FC traced to off-manifold perturbation bug.
- **Phase 4V** ORG-C verification: every load-bearing number independently reproduced; provenance
  clean (sandboxed guard test); 12-item fix list, all applied. Analysis/PHASE34-VERIFICATION.md
- **Phase 5** editorial (ORG-D): full manuscript Working/manuscript.md (~8k words, 10 sections,
  4 tables, 3 figures) + references.bib (55) + SUBMISSION-CHECKLIST.md.

## Office (5 organizations, Fable orchestrator)
ORG-A real-data | ORG-B experiments | ORG-C verification | ORG-D editorial | ORG-E citations.
All outputs adversarially cross-verified before promotion. ORCHESTRATOR.md is the live board.

## Remaining before actual TNSM submission (mechanics, not research)
- LaTeX/IEEEtran conversion + render references.bib (markdown manuscript is the intellectual deliverable).
- A2 group-do() numbers and Fwd IAT Min blind-spot value are seed-0-only (labelled as such).
- Byte-level PCAP artifacts (TTL 64/128, ISCX misalignment, SeqNo/AckNo) deferred to a PCAP parcel.
