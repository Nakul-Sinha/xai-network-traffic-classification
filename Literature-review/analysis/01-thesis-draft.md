# Emerging thesis (draft - pending corpus + adversarial novelty check)

## The disconnect, stated as a fact

Two literatures work on the same models and never cite each other.

**Literature A - "XAI for network security."** Hundreds of papers. Template:
`{RF | XGBoost | CNN-LSTM}` on `{NSL-KDD | CICIDS2017 | UNSW-NB15}` + SHAP/LIME plots +
97-99.99% accuracy. The attributions are presented as self-evidently meaningful. None validate them.

**Literature B - "NTC rigour."** TRUSTEE (CCS'22), the S&P'25 SoK, BiasSeeker (2026),
Arp et al., the CIC-IDS label-error papers. These show traffic classifiers routinely learn
capture artifacts, and they diagnose it with *interventions* - occlusion, tampering, feature ablation.

Measured, not asserted: **Wickramasinghe et al., "SoK: Decoding the Enigma of Encrypted Network
Traffic Classifiers," IEEE S&P 2025 (arXiv 2503.20093)** - the flagship systematization of this
field, which runs **348 feature occlusion experiments** - contains:

| term | occurrences |
|---|---|
| explainab* | **0** |
| interpretab* | **0** |
| XAI | **0** |
| SHAP | **0** |
| attribution | **0** |
| saliency | **0** |
| black-box | **0** |

Literature B performs interventions and never calls them explanations.
Literature A produces explanations and never performs interventions.

## The technical claim

Explanation quality in NTC is currently certified by *proxy* criteria:
- deletion/insertion & occlusion curves,
- surrogate fidelity (TRUSTEE's own DT fidelity),
- agreement with what a human expects (RRA/RMA vs a SOC analyst's feature list, arXiv 2506.07882),
- "42% better than existing explainers" on an internal objective (Traffic-Explainer, 2509.18007).

**A causally wrong explanation can pass every one of these.** There is a published proof by example.

TRUSTEE §7.2 + Table 3: a 3-node decision tree with **fidelity F1 = 1.00** - a *perfect* surrogate -
attributed a 1D-CNN's VPN/non-VPN decisions to bytes B49/B43/B47. Tampering those exact three bytes
changed average precision from **0.959 to 0.959**. The model simply used other shortcuts. Quote:
"the black-box model succeeds in finding alternative 'shortcuts' that are as easy to identify and
explain as the one we described earlier."

So in this domain we have a documented case where **perfect fidelity coexists with zero causal necessity**.

## Why networking is the right place to fix this

Ground-truth explanations are the central unsolved problem of XAI evaluation. Vision and NLP work
around it with synthetic toy scenes (CLEVR-XAI), human rationales (plausibility, not faithfulness),
or model-internal proxies (M^4, NeurIPS'23 D&B - images and text only).

Network traffic is a privileged modality, and nobody has used the privilege:

1. **Semantics are known exactly.** Byte k of a packet *is* a named protocol field. A byte-level
   attribution has a defined referent; it can be aggregated to fields and checked against protocol
   knowledge. No annotation needed, no human judgement.
2. **Samples are rewritable.** scapy / tcprewrite let you set any field and re-emit the packet.
   This is a literal `do(X := x)` operator on the input. Exact, cheap, unlimited.
3. **Interventions stay on-manifold.** The standard objection to deletion/occlusion metrics is that
   zeroing a pixel makes an image the model never saw. A rewritten packet with a different TTL is a
   *perfectly ordinary packet*. The counterfactual is real traffic, not an artifact of the metric.
4. **Ground-truth cases already exist, with public artifacts.** TRUSTEE's seven case studies are
   reproducible (github.com/TrusteeML/emperor, /trustee). ET-BERT (670*), YaTC (156*), nPrint (124*)
   are all public. Total capital required: zero.

## Research questions

- **RQ1 (validity).** When a traffic classifier is *known by intervention* to rely on a feature,
  do post-hoc attribution methods say so? Conversely, when they name a feature, is the model
  causally dependent on it?
- **RQ2 (redundancy).** Is TRUSTEE's single observation general? How many *disjoint, mutually
  sufficient* shortcut sets does a typical traffic classifier hold? Feature attribution presumes a
  unique explanation; if traffic models routinely hold many equivalent ones, attribution is the
  wrong primitive for this modality - not merely inaccurate, but ill-posed.
- **RQ3 (metric failure).** Do the faithfulness metrics in current use (deletion/insertion, AOPC,
  RRA/RMA, surrogate fidelity, monotonicity) separate causally-correct from causally-wrong
  explanations? Hypothesis: no, and the redundancy in RQ2 is exactly why.
- **RQ4 (repair).** Does a *set-level, sufficiency-based* notion of explanation - minimal sufficient
  byte/field sets, reported as a set of alternatives rather than one ranking - restore agreement
  with interventional ground truth?

## Why either outcome is publishable
- Attributions fail -> a strong negative result invalidating a large, growing literature.
- Attributions succeed -> the field's first ground-truth validation of its explanations; still novel.
- RQ2's redundancy measurement is a new, previously unmeasured property of traffic classifiers
  regardless of how RQ1 lands.

## Feasibility for one person, no capital
- Datasets: ISCX VPN-nonVPN, CIC-IDS2017 (PCAPs), USTC-TFC2016, CSTNET-TLS1.3 - all free.
- Rewriting: scapy (pure python).
- Models: 1D-CNN (minutes to train), ET-BERT / YaTC fine-tune (single consumer GPU or Colab), RF/XGB (CPU).
- XAI: shap, captum, lime, alibi - all free.
- No physical testbed, no traffic generation hardware, no proprietary data.

## STATUS
Hypothesis. Must survive the corpus sweep and an adversarial novelty check before it becomes the plan.
