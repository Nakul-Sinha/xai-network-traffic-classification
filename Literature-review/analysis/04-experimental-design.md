# Experimental design

## The central instrument: a packet-layer `do()` operator

Every faithfulness metric in use - deletion, insertion, AOPC, occlusion, KernelSHAP's own
marginalisation - perturbs the **feature vector**. In network traffic that is unsound twice over:

1. **Off-manifold.** Zeroing `Flow Duration` while leaving `Flow Bytes/s` and `Total Fwd Packets`
   untouched produces a feature vector no packet capture could ever generate. The model is then
   queried far outside its training distribution and the resulting "importance" is an artifact of
   extrapolation. This is the standard critique of deletion metrics in vision - and it is *worse*
   here, because flow features are deterministic functions of one another.
2. **Wrong layer.** For raw-byte models (ET-BERT, YaTC, 1D-CNN) a "feature" is byte position k,
   whose *meaning changes between samples* when headers are present in one class and absent in
   another. TRUSTEE's ISCX finding is exactly this: byte 49 is the IPv4 protocol field in VPN samples
   and the 4th byte of an Ethernet source MAC in non-VPN samples. Attribution to a byte index is
   attribution to a moving target.

**The fix, available only in this modality.** Intervene on the **packet**, then regenerate everything
downstream. Concretely, `do(F := resample)`:

    for each flow in the test split:
        rewrite protocol field F in every packet of the flow, with a value drawn from the
        POOLED (class-agnostic) empirical distribution of F over the whole dataset
        recompute all dependent fields: IP total length, IP header checksum, TCP/UDP checksum,
                                        TCP data offset, segment lengths
        re-emit a valid PCAP
    then re-run the model's OWN preprocessing:
        raw-byte models  -> re-extract the byte window
        flow-stat models -> re-run CICFlowMeter / NFStream to regenerate the 78-83 features

Properties this buys:
- **On-manifold.** Every counterfactual is a well-formed packet that a real host could have sent.
- **Class-information-destroying but distribution-preserving.** F's marginal is unchanged; only its
  mutual information with the label is destroyed. This is `do()`, not deletion.
- **Consistent.** Downstream flow features are recomputed, so no impossible combinations arise.
- **Architecture-agnostic.** Works identically for a Random Forest and for ET-BERT.

## Ground-truth quantities (these ARE the ground truth - measured, not assumed)

For a trained, frozen model M and protocol field F:

- **Interventional necessity** `N(F) = Acc(M, D) - Acc(M, do(F := resample) D)`
  How much M actually depends on F. Not what an analyst thinks; what the model does.
- **Interventional sufficiency** `S(F) = Acc(M, do(all fields except F := resample) D)`
  How far F alone carries M.
- **Redundancy degree** `R(M)`: greedily extract a minimal sufficient field set `S1`; neutralise it;
  extract `S2` disjoint from `S1`; repeat until accuracy falls to chance. `R = ` number of disjoint
  sufficient sets. **R > 1 means the model has substitutable shortcuts and no unique explanation exists.**

All three are computed by inference only. The model is never retrained, so nothing about M changes.

## Tracks

### Track A - constructed ground truth (exactness)
Inject a controlled artifact into a chosen field with tunable strength `p` = P(artifact present | class):
`p in {0.5 (none), 0.7, 0.9, 1.0}`. Sweeping `p` produces a *spectrum* of known reliance from zero to
total, so we can plot attribution score against `N(F)` rather than testing a single point.
Candidate injected artifacts (each cheap, each realistic): IP TTL, IP ID pattern, TCP window size,
TCP options ordering, TLS cipher-suite ordering, inter-arrival jitter, trailing padding length.

### Track B - natural documented artifacts (ecological validity)
Reproduce artifacts already established in the literature, then measure `N(F)` for each:
| artifact | dataset | established by |
|---|---|---|
| Ethernet-header presence / byte misalignment | ISCX VPN-nonVPN | TRUSTEE §7.2 |
| TTL 64 (Kali) vs 128 (Win8.1) | CIC-IDS-2017 | TRUSTEE / nPrintML case |
| unclosed TCP connections inflating Bwd IAT Total | CIC-IDS-2017 Heartbleed | TRUSTEE §7.3 |
| "TCP appendix" flows from CICFlowMeter | CIC-IDS-2017 | flow-construction critiques |
| RST packets standing in for the Bot class | CIC-IDS-2017 | flow-construction critiques |
| SII: MAC/IP/port | ISCXVPN, USTC-TFC | S&P'25 SoK occlusion grid |
| TCP timestamp options (temporal overfitting) | multiple | BiasSeeker taxonomy |

### Track C - the audit
`{KernelSHAP, TreeSHAP, DeepSHAP, Integrated Gradients, DeepLIFT, LIME, Occlusion, attention}`
x `{1D-CNN raw bytes, RF/XGBoost on flow stats, a traffic transformer (YaTC or ET-BERT)}`
x `{ISCX VPN-nonVPN, CIC-IDS2017, USTC-TFC2016}`

Reported per cell:
- `rho` = Spearman correlation between the attribution ranking and the `N(F)` ranking.
- `P@k` = precision of the attribution's top-k against `{F : N(F) > tau}`.
- **False-confidence rate** = fraction of features ranked top-k by the explainer with `N(F) ~ 0`
  (named but not needed) - the TRUSTEE failure mode, now quantified.
- **Blind-spot rate** = fraction of features with high `N(F)` that the explainer ranks outside top-k.

### Track D - do the proxies work?
Compute the standard in-use metrics on every cell: deletion/insertion AOPC, surrogate fidelity,
monotonicity, Max-Sensitivity, and Alquliti et al.'s FAP/FAR/FAF1. Then ask the only question that
matters: **does a good proxy score predict a good `rho`?** If the correlation is weak or negative,
the field's entire explanation-evaluation practice is unvalidated - measured, not asserted.

### Track E - plausibility vs faithfulness
Reproduce FAP/FAR (MITRE ATT&CK/D3FEND-derived reference) alongside `rho`.
**Prediction: on shortcut-driven models the two anti-correlate** - an explanation looks *more*
domain-meaningful precisely when it is *less* causally faithful, because the model's real basis is
non-semantic. If it holds, this reframes a metric the community is starting to adopt.

## Compute budget (single person, no capital)
- Packet rewriting: scapy, CPU, minutes-to-hours per dataset.
- Flow regeneration: CICFlowMeter / NFStream, CPU.
- 1D-CNN, RF, XGBoost: minutes on CPU/consumer GPU.
- YaTC / ET-BERT fine-tune: hours on one consumer GPU or a free Colab T4. Fallback: a small
  transformer trained from scratch, which preserves the architectural claim at lower cost.
- KernelSHAP is the only expensive explainer; budget it to a stratified sample (the literature
  already reports ~0.63 s/packet, so a few thousand samples is the realistic ceiling - and that
  cost is itself a reportable finding).

## Threats to validity to address in the paper
- **Retraining confound.** Never retrain under intervention; freeze M. Where retraining is needed
  (Track A strength sweep) it happens *before* any intervention and each `p` is a separate model.
- **Resampling still shifts joint distribution.** Mitigate by class-agnostic resampling from real
  values and by reporting a "null intervention" control (resample a field with `N(F) ~ 0`).
- **Field-vs-byte granularity.** Report attributions aggregated to protocol fields, with the
  aggregation rule stated; also report raw-byte results so the aggregation is auditable.
- **Header misalignment across classes.** Handle explicitly - it is the ISCX failure mode; align on
  protocol-parsed offsets, not absolute byte indices, and report both.
