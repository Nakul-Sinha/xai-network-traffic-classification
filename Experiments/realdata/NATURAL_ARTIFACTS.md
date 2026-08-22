# NATURAL_ARTIFACTS.md - Track-B documented-artifact catalogue (Parcel A3b)

The paper's Track B uses *documented* dataset artifacts as real-data ground truth (phase.md C2b):
each artifact below is a decision basis that prior work has already shown classifiers exploit, so
an explainer audited on a model verified to use it either recovers it (credit) or does not
(blind spot); naming it where its necessity is ~0 is false confidence. This is the reference
table for the paper. Claim numbers [n] refer to Literature-review/analysis/02-verified-claims.txt
and 02b-claims-update.txt; all cited papers are in Resource.md unless flagged.

Verification-operator legend:
- **PacketDO** - packet-level do(F := resample from pooled empirical marginal) with dependent-field
  recomputation (checksums/lengths/offsets), then re-run the model's own preprocessing (C1).
- **feature permute** - flow-level analogue on CSV features: do(column := resample from
  class-pooled empirical marginal), N(F) = accuracy drop / flip rate. Used when the model consumes
  CICFlowMeter features rather than bytes.

## The catalogue (7 artifacts)

### B1. ISCX Ethernet-header misalignment (3 shortcut bytes B49/B43/B47)

- **Artifact.** Non-VPN captures in ISCX VPN-nonVPN retain Ethernet headers while ~90% of VPN
  captures do not; a published 1D-CNN with ~100% precision/recall decides VPN vs non-VPN from 3
  header-offset bytes (49, 43, 47) of PCAP/Ethernet/IP metadata carrying no VPN semantics.
  Destroying those 3 of 748 bytes leaves accuracy unchanged (0.959 -> 0.959): redundant-shortcut
  family, the surrogate-incompleteness case.
- **Dataset.** ISCX VPN-nonVPN 2016 (Draper-Gil et al., ICISSP 2016), byte-level.
- **Citation.** Jacobs et al. (TRUSTEE), CCS 2022, Sec. 7.2 [36][39][97][158].
- **Interventional verification.** PacketDO with protocol-parsed offsets (misalignment means fixed
  byte indices refer to different header fields per class - the operator must parse first, which
  is exactly why this case is in the paper): re-randomize/strip the L2 header bytes, re-run
  preprocessing; field-SET necessity for {B49,B43,B47} jointly (redundancy - single-byte N(F)
  understates, phase.md Sec. 6).
- **Status.** Needs PCAP (byte-level parcel, ISCX track). Not representable in any flow CSV.

### B2. CIC-IDS2017 TTL 64/128 topology artifact

- **Artifact.** Attack traffic was generated from outside hosts (Kali Linux, default TTL 64),
  benign/victim traffic from inside Windows hosts (TTL 128), so IP TTL alone separates classes.
  nPrintML reproduces 0.999 F1 on CIC-IDS2017 largely from TTL and similar spurious bits;
  iteratively zeroing TTL and other dominant fields still leaves F1 = 0.990 on TCP-options bits
  (redundant-shortcut family).
- **Dataset.** CIC-IDS2017 PCAPs (Sharafaldin et al., ICISSP 2018), byte/bit-level (nPrint
  representation).
- **Citation.** Jacobs et al. (TRUSTEE), CCS 2022 [38][98]; model: Holland et al. (nPrintML),
  CCS 2021. Supporting bound: in-switch models gain only 1.7-3.5% F1 from port/TTL/header bias
  [109].
- **Interventional verification.** PacketDO: do(IP.ttl := resample from pooled marginal over
  {64,128} and observed decrements), recompute IP header checksum, re-extract nPrint/byte input.
  Graded variant: swap TTL class-conditionally at rate p for the E2-style curve.
- **Status.** Needs PCAP. **Verified NOT representable on either acquired flow CSV**: neither the
  original 52-column release nor the improved 91-column release carries any TTL-derived feature
  (both headers checked 2026-08-22; `load_cicids.ARTIFACT_COLUMNS["ttl"] == []`).

### B3. CICFlowMeter TCP-appendix flows (flow-construction artifact)

- **Artifact.** CICFlowMeter mis-terminates TCP flows, emitting 25.9% spurious "appendix" flows
  (post-FIN/RST fragments counted as new flows). Measured signature on our original copy:
  `Init_Win_bytes_forward == -1` (no handshake inside the flow) in **43.5% of Normal Traffic vs
  <=0.01% of every attack class** - a class-correlated shortcut. In the corrected/improved copy the
  signature is annihilated: **exactly 0 flows** with -1 (loader-verified). Correlated column
  family: `Fwd Header Length`, `min_seg_size_forward`, `Init_Win_bytes_backward`.
- **Dataset.** CIC-IDS2017 flow CSVs, original vs Engelen/Liu-corrected pair (both acquired; see
  DATASET.md + CORRECTED_DATASET.md).
- **Citation.** Engelen et al., SPW (WTMC) 2021 [62]; corrected data
  https://intrusion-detection.distrinet-research.be/WTMC2021/; improved regeneration Liu et al.,
  IEEE CNS 2022 (add to Resource.md); packet-duplication corroboration Lanvin et al., CRiSIS 2022
  [116].
- **Interventional verification.** Feature permute on the original-data model:
  do(`Init_Win_bytes_forward` := pooled resample) plus field-set necessity for the 4-column
  family; THEN the corrected-vs-original paired contrast (CORRECTED_DATASET.md Sec. 5): N(F)
  high on original, collapses on corrected; explainer must track the collapse.
- **Status.** **Fully reproducible on acquired flow CSVs** - the flagship Track-B case for E4.

### B4. Destination-port bias

- **Artifact.** Attack classes concentrate on a handful of destination ports, making Dst Port a
  near-perfect shortcut. Measured on our original copy: DoS/DDoS/Web Attacks 100% port 80,
  Brute Force 21 (64.8%)/22 (35.2%), Bots 8080 (64%); measured on the corrected copy: the
  concentration **survives correction** (DoS 100%, DDoS 100%, Bots 100% - it is a testbed-design
  artifact, not a metering bug). Port Scanning is the built-in contrast class (target ports swept:
  top port <0.5%). Documented in the wild: an XAI-for-IDS paper *acknowledges* Destination Port is
  contaminating yet its own SHAP pipeline ranks it #1 on CICIDS-2017 and publishes the ranking -
  false confidence observed in the literature itself.
- **Dataset.** CIC-IDS2017 flow CSVs (both copies); generically ISCX VPN-nonVPN too
  (port -> application leakage, BiasSeeker "data-leakage identifier" category).
- **Citation.** Wang et al. (BiasSeeker), 2026 [22][23]; Neupane et al. (E-XAI) [114]; documented
  quantified shortcut [61]; Arp et al., USENIX Sec 2022 (spurious-correlation pitfall framing).
- **Interventional verification.** Feature permute: do(`Destination Port` := class-pooled
  resample). Expected ground truth: high N(F) on DoS/DDoS/Web/Brute-Force/Bots, ~0 marginal N(F)
  contribution for Port Scanning's port-spread. Positive control in E4 (must stay high-N on BOTH
  original and corrected models). Packet-level twin: PacketDO rewrite of TCP/UDP dport bytes +
  checksum recompute for the byte-level models.
- **Status.** **Fully reproducible on acquired flow CSVs** (both), and later repeatable at byte
  level on PCAP.

### B5. SII: MAC/IP/port strong identifying information in raw bytes

- **Artifact.** Byte-level classifiers read endpoint identifiers instead of behaviour: anonymizing
  Strong Identifying Information (MAC/IP addresses, ports) drops ET-BERT 0.96 -> 0.51 and YaTC
  0.90 -> 0.62 (avg -0.36) in the SoK's 348-experiment occlusion grid; NetMamba on ISCXVPN2016
  drops 0.8847 -> 0.7821 under random SII masking.
- **Dataset.** ISCX VPN-nonVPN, USTC-TFC (byte-level pipelines).
- **Citation.** Wickramasinghe et al. (SoK), IEEE S&P 2025 [8]; corroborating BiasSeeker
  "data-leakage identifiers" [22][128]; first-hand flow-ID leakage admission [108].
- **Interventional verification.** PacketDO field-level resample of src/dst MAC, src/dst IP, and
  port bytes from pooled marginals (NOT zeroing - zero-MAC/IP is protocol-impossible, the E1
  point), recompute IP/TCP checksums, re-run tokenization/byte-window preprocessing. Field-set
  necessity for the SII set jointly (the SoK occludes them as a block).
- **Status.** Needs PCAP (byte-level parcel). *Partial flow-level analogue on acquired CSVs:* the
  improved release exposes `Src IP`/`Dst IP`/`Src Port` metadata columns - they are excluded from
  X by the loader, but a deliberately-leaky variant model can be trained to demonstrate the
  artifact at flow level if ORG-B wants a cheap rehearsal before the PCAP run.

### B6. SeqNo/AckNo/TCP-timestamp flow-ID bytes (relative/temporal artifacts)

- **Artifact.** Raw initial TCP sequence/acknowledgment numbers and TCP timestamp options act as
  per-flow/per-host identifiers: randomizing them collapses ET-BERT from 97.4 to 19.5 (Pcap-Encoder
  / "Sweet Danger of Sugar"); BiasSeeker's "relative artifacts" and "temporal" categories; TCP
  timestamps that uniquely identify mobile apps stop working once randomized [24].
- **Dataset.** ET-BERT-style byte-level corpora (ISCX VPN-nonVPN et al.).
- **Citation.** "The Sweet Danger of Sugar" (Pcap-Encoder), 2025 (arXiv 2507.16438) [G3 evidence,
  analysis/10]; Wang et al. (BiasSeeker), 2026 [22][24].
- **Interventional verification.** PacketDO: rebase SeqNo/AckNo per flow (preserve relative
  offsets - the *relative* structure is legitimate signal; only the absolute values are the
  artifact), resample TCP timestamp option values, fix option lengths and checksums. Field-set
  necessity for {SeqNo, AckNo, TS} jointly - phase.md Sec. 6 names this the documented redundant
  family whose single-field N(F) understates.
- **Status.** Needs PCAP. Not representable in flow CSVs (CICFlowMeter keeps no absolute
  seq/ack/timestamp features).

### B7. Heartbleed Bwd-IAT / Bwd-Packet-Length generation artifact

- **Artifact.** The CIC-IDS2017 generator never closed attack TCP connections between heartbeat
  messages, inflating `Bwd Packet Length Max` and `Bwd IAT Total`; an RF reaches perfect
  Heartbleed detection (P/R/F1 = 1.000) from this artifact, and performance collapses when the
  authors regenerate the attack without it.
- **Dataset.** CIC-IDS2017 flow CSVs (the artifact lives in CICFlowMeter features, unlike B2).
- **Citation.** Jacobs et al. (TRUSTEE), CCS 2022 [37][99].
- **Interventional verification.** Feature permute: do(`Bwd Packet Length Max` := pooled resample)
  and do(`Bwd IAT Total` := pooled resample), single and as a set, on a model trained with
  Heartbleed as its own class.
- **Status.** **Partially reproducible on acquired flow CSVs.** Constraint measured on our copies:
  the original A1 release groups labels into 7 families (Heartbleed folded into DoS, not
  isolable); the improved release retains the fine label - but with **n = 11 Heartbleed flows**
  (matching the known original count). Feasible as a one-vs-rest cell with all 11 flows in test
  on the improved copy (acquired); on the original side it would need the ungrouped per-day CIC
  CSVs, which are NOT acquired. Too small for the headline table - report
  as a documented-artifact sidebar, not a main E4 row.

## Summary counts (parcel report)

| status | artifacts |
|---|---|
| catalogued total | **7** (B1-B7) |
| fully reproducible on acquired flow CSVs (original + corrected in hand) | **2** - B3 TCP-appendix (flagship, incl. corrected-vs-original pair), B4 destination port |
| partially reproducible on flow CSVs | **2** - B7 Heartbleed (fine label only in improved copy, n=11), B5 SII (flow-level rehearsal via metadata columns only; real case is byte-level) |
| require PCAP / byte-level pipeline (ISCX-USTC parcel) | **4** - B1 Ethernet misalignment, B2 TTL 64/128, B5 SII (proper), B6 SeqNo/AckNo/TS |

Cross-references: DATASET.md (original copy, measured artifact columns),
CORRECTED_DATASET.md (corrected copy, measured deltas, E4 design),
load_cicids.py / load_cicids_improved.py (loaders exposing `ARTIFACT_COLUMNS` / harmonized space).

Open citation action: add Liu et al., IEEE CNS 2022 ("Error Prevalence in NIDS Datasets") to
Resource.md and DOI-verify it - the improved release we downloaded follows that paper's schema.
