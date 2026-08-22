# Orchestrator notes - independent grounding (pre-sweep)

Read directly by the lead, not via subagent.

## Observation 1: the XAI-for-NIDS literature is saturated and low-rigour
A Semantic Scholar sweep of "interpretable ML network intrusion detection SHAP" returns ~40 papers,
of which the overwhelming majority follow one template:

    {RandomForest | XGBoost | CNN-LSTM} on {NSL-KDD | CICIDS2017 | UNSW-NB15}
    + SHAP and/or LIME plots
    + reported accuracy 97-99.99%

Representative: 10.1109/CARS61786.2024.10778742 reports "100% accuracy across metrics" on CICIDS2017.
Several 2026 entries report 99.8-99.99%. None of the ones surfaced validate that the SHAP
attributions are *correct* - they are presented as self-evidently meaningful.

This is a saturation signal, NOT a gap by itself. The gap is what nobody in this pile does.

## Observation 2: two recent papers bracket the space I am circling

### BiasSeeker - arXiv 2601.10180 (Wang, Xie, Wang, Cui; 15 Jan 2026)
- Detects *dataset-specific shortcut features* in encrypted NTC.
- Explicitly **model-agnostic and classifier-independent**: statistical correlation directly on raw bytes.
- Motivation quote: "Existing solutions heavily rely on model-specific interpretation techniques,
  which lack adaptability and generality across different model architectures."
- 19 public datasets, 3 NTC tasks.
- KEY: it deliberately *sidesteps* XAI. It answers "which features in this dataset are shortcuts?"
  It does NOT answer "do XAI attributions on a trained traffic classifier actually surface those shortcuts?"

### Traffic-Explainer - arXiv 2509.18007 (Ponraj, Durairajan, Wang; 22 Sep 2025)
- New model-agnostic input-perturbation explainer for traffic DL; mutual-information masking.
- Claims "~42% improvement over existing explanation methods".
- The 42% is measured against a *proxy* fidelity criterion, not against known ground truth.
- Applied to application classification, traffic localisation, network cartography.

### LEXNet - arXiv 2202.05535
- Explainable-by-design prototype-layer CNN for internet traffic classification.

### Others logged
- 2601.04089 - Tutorial on flow-based NTC w/ ML; leakage-resistant design, measurement artifacts, explainability.
- 2310.19568 - DataZoo: standardised NTC datasets + realistic partitioning.
- 2010.06135 - Sharingan: program synthesis for interpretable session-layer attack rules.
- 1910.07266 - Energy-based Flow Classifier (inverse Potts), explainable + cross-dataset.

## Emerging gap hypothesis (to be adversarially tested)
Networking is one of the very few ML domains where **ground-truth explanations are constructible**:
protocol semantics are known, and we can synthesise / inject traffic in which we control exactly which
bytes or fields carry label-predictive signal. Yet the XAI-for-traffic literature evaluates explanations
only with self-referential proxies (deletion/insertion, fidelity-to-surrogate) or by eyeballing plots.

Nobody appears to have asked the falsifiable question:
**when a traffic classifier is provably relying on a known artifact, do standard XAI methods say so?**

Solvable by one person on public data + controlled injection. No capital. Falsifiable either way.
STATUS: hypothesis only. Must survive novelty check against the full corpus.

---

## THE DECISIVE FINDING (read directly from the TRUSTEE PDF, CCS'22, §7.2 + Table 3)

Jacobs, Beltiukov, Willinger, Ferreira, Gupta, Granville.
"AI/ML for Network Security: The Emperor has no Clothes." CCS '22. DOI 10.1145/3548606.3560609

They audited a 1D-CNN encrypted-traffic classifier (ISCX VPN-nonVPN, 784 raw bytes as features,
reported 99.9-100% P/R). TRUSTEE extracted a 3-node decision tree with **fidelity F1 = 1.00** -
a *perfect* surrogate. The tree said the model decides on bytes B49, B43, B47.

Byte forensics showed why: Non-VPN samples always carry Ethernet headers, ~90% of VPN samples do not,
so from k>=40 the byte positions are MISALIGNED between classes. B49 = IPv4 protocol field in VPN
samples but the 4th byte of the Ethernet source address in Non-VPN samples. The model was reading
the capture harness, not the traffic.

### And then the part that matters most

They ran the causal intervention: they *tampered* bytes 43/47/49 in VPN samples to mimic Non-VPN.
If the explanation were causally correct, accuracy should collapse.

    Validation dataset      Avg.Precision  Avg.Recall  Avg.F1
    Untampered              0.959          0.956       0.955
    Tampered-43-47-49       0.959          ...         ...

**Accuracy did not move.** Their own words: "the black-box model succeeds in finding alternative
'shortcuts' that are as easy to identify and explain as the one we described earlier."

### Why this is the paper

A **perfect-fidelity** explanation was **causally wrong**. The model does not depend on the bytes
its explanation named, because it holds a *set of redundant, mutually substitutable shortcuts*.

Two consequences the literature has not absorbed:
1. Fidelity/faithfulness proxies (deletion-insertion, surrogate agreement, the "42% better" of
   Traffic-Explainer, the RRA/RMA of 2506.07882) can all be satisfied by an explanation that names
   features the model does not need.
2. Feature attribution presumes a *unique* explanation. Traffic classifiers appear to hold
   *many equivalent* ones. Attribution is arguably the wrong primitive for this modality.

### Other ground-truth anchors TRUSTEE hands us (Table 2, all artifact-available)
| Problem | Dataset | Model | Fidelity | Established bias |
|---|---|---|---|---|
| VPN detection | ISCX VPN-nonVPN | 1D-CNN | 1.00 | shortcut learning (Ethernet/PCAP metadata) |
| Heartbleed | CIC-IDS-2017 | Random Forest | 0.99 | OOD vulnerability |
| Malicious traffic IDS | CIC-IDS-2017 + campus | nPrintML | 0.99 | spurious correlations (bit-level features) |
| Anomaly detection | Mirai | Kitsune | 0.99 | OOD vulnerability |
| OS fingerprinting | CIC-IDS-2017 | nPrintML | 0.99 | potential OOD |
| IoT device fingerprinting | UNSW-IoT | Iisy | 0.99 | likely shortcut learning |
| Adaptive bitrate | HSDPA Norway | Pensieve | 0.99 | potential OOD |

## Networking is a privileged modality for XAI evaluation
Vision/NLP cannot manufacture ground-truth explanations without synthetic toy data (CLEVR-XAI) or
human annotation (which is *plausibility*, not faithfulness). Networking can:
- protocol field semantics are known exactly, so byte -> field attribution has a defined referent;
- packets are **rewritable**: scapy / tcprewrite let you set a field and regenerate the sample, so a
  do()-intervention on any feature is exact and cheap;
- a rewritten packet is still a valid packet, so the intervention stays ON-MANIFOLD -- which is the
  standard objection to deletion/occlusion metrics in vision.
Nobody has exploited this.

## What is NOT a gap (checked, already served)
- Runtime/latency of SHAP at line rate: actively solved (SHAP-pruning ~1.29ms p95; INT8+caching 39ms;
  LightGBM 4.9-5.9us/sample). Do not build here.
- Dataset shortcut *detection*: BiasSeeker (2601.10180) covers dataset-side diagnosis.
- New explainer methods for traffic: Traffic-Explainer (2509.18007), LEXNet (2202.05535).
- "SHAP on CICIDS2017 + 99% accuracy": saturated beyond redemption.

---

## Downstream consumers of unvalidated attributions (motivation stack)
The cost of unfaithful explanations in this domain is no longer abstract; published systems now make
operational decisions from attributions:
1. **xNIDS** (Wei, Li, Zhao, Hu - USENIX Sec '23): generates *active defense rules* from its
   explanations of DL-NIDS. Evaluated by fidelity/sparsity/completeness/stability - the Warnecke
   proxy suite. No causal validation. Artifact: github.com/CactiLab/code-xNIDS.
2. **ShortcutCatcher** (Zhao, Boffa, Vassio, Mellia - Proc. ACM Netw. 2026): removes features named
   by explainers in a closed loop. Trusts the explainer end-to-end.
3. **EXP-SEC** (arXiv 2607.12203, 2026): maps explanations into analyst-facing language + adds
   group-level metrics; still model-internal proxies, no ground truth.
4. Surveys prescribe XAI as the *audit instrument* for dataset artifacts (NIDS-dataset survey
   claim [64]) - i.e., the field's recommended defence against shortcuts is itself unvalidated.

If attributions have high false-confidence / blind-spot rates against interventional ground truth,
all four break in specific, demonstrable ways. That is the significance argument for the paper.
