# Progress log

## Phase 0 - setup (done)
- Working tree, tooling (pdftext extractor, corpus merger), gh auth verified.

## Phase 1 - corpus discovery (done)
- 12-angle sweep over Semantic Scholar, OpenAlex, arXiv, DBLP plus a parallel verified-claim
  pipeline (fan-out search, fetch, 3-vote adversarial verification per claim).
- Result: 450-paper deduplicated corpus (corpus/corpus.json), ~115 verified claims (analysis/02*).

## Phase 2 - deep read (done)
- 78 papers read end to end across 13 reader batches, 70 in full text; per-paper records of
  how explanation quality was evaluated and what ground truth (if any) was used.
- Ground-truth census: none 50 / synthetic 9 / human-expert 8 / architectural 5 / interventional 5.
- Distillation: 17 gaps across 7 themes with solo-feasibility and risk verdicts (analysis/05).

## Phase 3 - gap selection and novelty gauntlet (done)
- 7 nearest-competitor lineages differentiated (analysis/03).
- Two overclaims caught by full-text reading and corrected (analysis/08): shortcut-injection
  ground truth exists in vision/NLP (BAM, Bastings); on-manifold byte interventions exist
  (Traffic-Explainer, confirmatory direction only).
- Locked goal: interventional ground-truth benchmark + explainer audit + redundancy R(M).

## Phase 4 - proof of concept (done)
- poc/run_poc.py: scapy packet synthesis, packet-layer do() with checksum recompute,
  N(F)/S(F)/R(M), audit of DeepSHAP / IntGrad / occlusion. Three conditions run.
- Key result: IntGrad ranks a zero-necessity field as its number 1 feature at artifact
  strength p=0.7 (false-confidence 0.67); DeepSHAP 0.50; occlusion clean. See poc/FINDINGS.md.

## Phase 5 - paper plan (done)
- phase.md written: venue (IEEE TNSM), 4 RQs, instrument, 5 tracks, 16-week schedule, threats.

## Phase 6 - execution (next)
- Week 1-3 per phase.md: do() operator hardening, preprocessing harness, dataset hygiene.
