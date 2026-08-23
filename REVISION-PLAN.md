# Submission-grade revision plan (post-audit)

Triggered by a five-organization adversarial audit of `Working/manuscript.md` (2026-08-23).
Auditors were blind to authorship and verified against code + result files, not prose.

## Audit outcome (what is TRUE)

- **Data integrity: CLEAN.** 0 fabricated numbers; every headline figure re-derived from the raw
  JSONs and reproduces; the 5 seeds are genuinely distinct (distinct hashes AND distinct values).
- **Citations: CLEAN.** 0 fabricated / 0 mis-attributed across 22 load-bearing refs; all nine
  2025/2026 entries resolve to real DOIs/arXiv IDs. Two source-internal numbers (nascita 107/5;
  TRUSTEE Table-3 case study) could not be fetched in-env; papers are real and on-topic. TODO: spot
  check those two against the source PDFs.
- **Internal consistency: MOSTLY CLEAN.** 0 reverted overclaims; abstract<->body<->tables agree.
  `42 passed, 1 skipped` verified by re-running pytest.

## Findings to fix, by severity

### CRITICAL
- **R(M) is broken in code.** `benchmark/groundtruth.py:redundancy()` grows sets by single-field
  removal and stops each set at chance, so it returns R=1 for a committed model and R=0 for a
  genuinely redundant one (inverted). No stored result is ever R>1. The redundancy narrative is
  actually carried by TreeSHAP bimodality + packet-length group necessity, not by R(M).

### MAJOR (need experiments / reshape claims)
- Byte-level thesis (broken checksum -> off-manifold) never tested on a real packet; the one real
  dataset is flow-level. On flow features PacketDO reduces to permutation importance.
- Occlusion (removal-based) crowned winner against a removal-based ground truth = circularity.
- Real-data 9/10 false-confidence collapses to 0-1/10 under an equally-defensible cutoff; no
  sensitivity curve shown.
- False universals: "could never appear on a network" (NIC checksum offload; malformed packets are
  exactly what a NIDS classifies), "always well-formed", "formally invalid", unqualified "first".
- Scope mismatch: intro invokes transformers (ET-BERT); experiments use ByteCNN + RF.

### MINOR (mechanical)
- runtime 1,259 s -> 1,232 s; Impurity 0.62 -> 0.625; "nine packet-length" -> "nine false-confident
  (8 in family)"; null-control "every cell" -> "cell means"; disclose tau=0.05.
- captions.md figure numbering stale/swapped vs the (correct) manuscript body.
- SS5.1 "22.4% of intervenable fields" -> "field interventions".
- "eight explainers" promised but Table II tabulates six (KernelSHAP/LIME prose-only).
- precision@k=1.0 trivial for committed models; E2 referenced but never shown; "C4" cited but
  contributions unnumbered; S(F) defined as "every field" but code uses candidate set, never reported.

## Phases (each closes with an adversarial verification pass)

- **A. Mechanical fixes** — numbers, captions, wording, C1-C4, E2, explainer table, soften false
  universals. No new experiments.
- **B. R(M) repair** — rewrite `redundancy()` as sufficiency-based disjoint-set search; validate on a
  constructed oracle with known R=2 and R=1 (old algo returns 0/1, new returns 2/1); report R(M) for
  trained models; tie false-confidence to attribution on the non-committed substitute.
- **C. Circularity + thresholds** — stop adjudicating occlusion as winner; add an operator-independent
  ground-truth check; threshold-sensitivity curves for false-confidence / blind-spot (esp. real data).
- **D. Byte-level PCAP** — real captures -> byte model -> PacketDO on real packets with real
  checksums/lengths; replicate audit + documented artifacts (TTL 64/128, ISCX misalignment).
- **E. Integrate + re-verify** — fold results in, re-run verification org, regenerate PDF.

## Status
- Em-dash removal: DONE (64 -> 0, verified; backup Working/build/manuscript.pre-emdash.bak).
- Phase A (mechanical + false-universal softening): DONE. C1-C4 numbered, E2/E6 labelled,
  captions synced, numbers corrected, tau=0.05 disclosed, Section 8 distributional caveat added.
- Phase B (R(M) repair): DONE. `redundancy()` rewritten (sufficiency-based disjoint-set search),
  `redundancy_legacy` retained for the ablation. Validated (benchmark/validate_rm.py, rm_validation.*):
  legacy R<=1 always; corrected recovers R=2 on a redundant oracle (f<=0.4), R=1 on committed oracle
  and both trained models {tcp.window}. Manuscript SS3.3 def + SS5.2 Table II added; tables renumbered.
  Finding: on-manifold resampling makes single-classifier R(M) threshold-sensitive (disclosed).
- Phase C (threshold sensitivity): DONE for real data (realdata/fc_sensitivity.py, Fig 4). Accuracy-only
  FC robust at 8-10 across cutoffs; dual criterion criterion-dependent (minority-class F1). SS5.3 updated.
  TODO C: circularity reframe already largely present (occlusion not crowned); confirm in Phase E.
- Phase D (byte-level PCAP): DONE. realdata/pcap_bytelevel.py on ISCX VPN (facebook vs ftps, 5k/class
  real TCP packets w/ options). E1-real: zero-mask 6.2% vs PacketDO 100% (baseline 100%); ByteCNN acc
  0.979; model shortcut = server IP (N(ip.dst)=0.25, N(ip.src)=0.16), R(M)=1 {ip.dst,ip.src}; gradient
  explainers FC 0.71-0.78, precision@k 0.50, blind 0.50; occlusion FC 0.33. Manuscript SS5.5 + Table IV
  + abstract + SS8 updated. Dataset git-ignored; PCAP_DATASET.md documents fetch. reproduce.py updated.
- Phase E: DONE. Verification org (2 agents): data-integrity 0 mismatches (all Phase B/C/D numbers trace
  to files); consistency 1 fail -> fixed ("always a well-formed packet" in C1 bullet + one unqualified
  "for the first time" softened). PDF regenerated (19 pp, 4 figures embedded, IEEE cites, 39-entry bib).
  Manuscript 9.36k words, 0 em dashes, Tables I-VI, Figs 1-4.

## ALL PHASES COMPLETE. Committed a44f1f8 + pushed to main.

## Follow-up: ET-BERT-style transformer test (user-requested)
- realdata/transformer_audit.py: compact byte-level self-attention Transformer (2 layers, 4 heads,
  d=64, CLS) on the same real ISCX facebook-vs-ftps task. Test acc 1.0; same server-IP shortcut
  (N(ip.src)=0.214, N(ip.dst)=0.195). Audit incl. attention-as-explanation: IG/Occlusion faithful
  (FC 0.0), but ATTENTION is least faithful (FC 0.80, precision@k 0.5, blind 0.5). Which explainer
  fails is model-dependent (IG dirty on CNN, clean on transformer). Integrated into SS5.5 (Table IV
  extended with Transformer block), abstract, SS9 future-work. Not the pretrained ET-BERT (labelled).
  PDF regenerated (23 pp, 9.72k words).

## Phase F: post-review completion (2026-08-24) - IN PROGRESS
Goal: complete the 3 remaining tasks end to end (see phase.md section 9).
- F1 pretrained ET-BERT audit: RUNNING (Opus agent, Kaggle GPU). Deliverable Experiments/etbert/ + DRAFT.md.
- F2 second byte-level dataset: RUNNING (Opus agent, local GPU). Deliverable Experiments/realdata/<ds>_* + DRAFT.md.
- F3 LaTeX/IEEEtran camera-ready: QUEUED (after F1+F2 integrated). Deliverable Working/paper-tex/.
Execution: F1 || F2 (independent, separate GPUs); orchestrator integrates DRAFTs serially; F3 last.
