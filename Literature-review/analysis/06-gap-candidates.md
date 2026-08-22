# Candidate gaps (running list) + kill-tests

Every candidate gets an explicit kill-test: the search/read that would prove it already solved.
"KILLED" / "SURVIVES" verdicts get filled as evidence lands. Sources: 105 verified claims
(02-verified-claims.txt), my full-text reads, the corpus sweep.

## G1 - Interventional ground-truth benchmark for attribution faithfulness in NTC  [main candidate]
No one has measured whether SHAP/IG/LIME/attention attributions on traffic classifiers agree with
what packet-level do()-interventions show the model actually uses.
- Kill-test: any paper computing attribution-vs-intervention agreement on traffic models.
  Searched directly; searched TRUSTEE's 44 citers; searched "counterfactual evaluation attribution
  network traffic". Nothing. Surveys state the prerequisite (annotated explanation ground truth)
  "does not exist" [claims 81-82].
- Status: **SURVIVES** (pending final corpus check).

## G2 - Explanation redundancy / Rashomon measurement for traffic models
R(M): how many disjoint sufficient shortcut sets does a trained traffic classifier hold?
TRUSTEE observed the phenomenon once, incidentally (Table 3). Rashomon literature never touched
networking [Rashomon searches returned no networking application].
- Kill-test: "model class reliance network traffic", "predictive multiplicity intrusion detection".
  Nothing found.
- Status: **SURVIVES**. Folded into G1 as RQ2.

## G3 - Plausibility vs faithfulness anti-correlation
Alquliti et al. measure plausibility (FAP/FAR vs ATT&CK-derived sets) and get low scores; they
cannot tell whether the explainer or the reference is wrong. Nobody has measured both plausibility
AND causal faithfulness on the same models.
- Kill-test: any paper jointly measuring the two on security/traffic models. None found.
- Status: **SURVIVES**. Folded into G1 as Track E.

## G4 - Attention validity in traffic transformers
ET-BERT/YaTC attention maps are shown as explanations in the ETC literature; one 2026 RAN paper
[claim 103] finds attention local-R2 < 0.4 (least faithful of tested methods) - but on RAN data,
not traffic classification. The NLP "attention is not explanation" debate was never run for traffic.
- Kill-test: "attention faithfulness ET-BERT / traffic transformer validation". Nothing.
- Status: **SURVIVES**. Folded into G1 as a model family + explainer row.

## G5 - Explanation stability under drift
Formal result exists: additive attributions are invalidated by any boundary change [claim 71,
with CDLEEDS maintenance-cost work 72-74]; CADE-style boundary fidelity collapses on drifted
IDS samples (1.41% boundary-crossing vs 97.64% on malware) [76-77]; SHAP-distribution drift
monitoring proposed [41-44].
- Verdict: real gap space but ALREADY PARTIALLY OCCUPIED (multiple 2024-2026 papers). A pure
  drift-explanations paper would fight existing work. Keep only as a *secondary experiment*
  (does attribution-vs-ground-truth agreement degrade across dataset epochs?).
- Status: **WEAKENED** - do not build the paper on it.

## G6 - Concept-based / self-explaining traffic models
Traffic-CBM exists (2026) [claims 12-15]: unsupervised "concepts", no human validation, authors
defer concept validation to future work. LEXNet prototypes exist. Space is being colonised.
- Status: **WEAKENED** as a primary target (a "better concepts" paper is incremental).
  The G1 harness however can *evaluate* such models fairly - keep as evaluation subject.

## G7 - Real-time / line-rate explanation
- Status: **KILLED**. Actively served (SHAP-pruning 1.29ms p95; INT8+caching 39ms; selective
  triage; LEXNet 102.7us). Multiple 2025-2026 papers. Cost numbers still worth citing.

## G8 - LLM-generated NIDS explanations
MA-IDS, SHAP+LLM description generators, agentic incident reports - crowded, fast-moving, hard to
evaluate rigorously, reviewer-risky.
- Status: **KILLED** for this paper.

## G9 - Ground-truth-known synthetic traffic for XAI benchmarking
OpenXAI/CLEVR-XAI exist for tabular/vision; nothing for traffic. BiasSeeker (dataset-side) and
ConCap (labelled flow generation) are adjacent but neither produces *explanation* ground truth.
- Status: **SURVIVES**; folded into G1 as Track A (controlled artifact injection with tunable p).

## Synthesis
G1 absorbs G2, G3, G4, G9 as tracks and keeps G5 as a secondary experiment. That composition is
the paper: a benchmark + audit with four findings tracks, each independently publishable evidence.
