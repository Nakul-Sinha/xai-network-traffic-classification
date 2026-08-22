# Orchestrator charter and live board

**Paper:** Protocol-Valid Faithfulness Evaluation for ML-Based Network Traffic Classifiers (see `phase.md`).
**Top orchestrator:** the main session loop (Fable-class). Reads `phase.md`, `README.md`, `Resource.md`,
`Literature-review/analysis/05-distilled-gaps.md`, and this board before every dispatch decision.
**Operating mode:** unconstrained compute (local RTX 4050 + Kaggle) and tokens. Goal: maximal, accurate,
reproducible output. Every organization's output is adversarially verified before it is trusted.

## Office structure

```
Orchestrator (main loop, Fable)
  reads phase.md + plan + this board, sequences orgs, resolves cross-org dependencies
  |
  ├─ ORG-A  Real-Data & Natural-Artifacts   (no GPU: network/disk/CPU)   -> Phase 3
  ├─ ORG-B  Robustness & Operator-Sensitivity (CPU + bounded GPU)         -> Phase 4 (E5, multi-seed, extra explainers)
  ├─ ORG-C  Verification                     (adversarial cross-check)    -> runs after A/B milestones
  └─ ORG-D  Editorial                        (results narrative, figures, paper)  -> Phase 5, after C signs off
```

Each organization is a background Workflow with an internal lead agent (reads phase.md + this board
first) and parallel worker agents. Verification (ORG-C) is never skipped: an org's numbers are not
promoted to the paper until a fresh adversarial team reproduces them.

## Hardware discipline (to avoid contention)

- GPU (6 GB) is a single resource. Only ORG-B trains neural models, and it serializes CNN/ET-BERT
  runs internally. ORG-A (RF/flow only) and ORG-D (text) never touch the GPU.
- Disk: 18 GB free. Large PCAP datasets are staged to scratch, features extracted, raw deleted.
  Prefer flow-CSV datasets (hundreds of MB) over multi-GB PCAP where possible.

## Live board (updated by the orchestrator)

| org | task | status | output | verified |
|---|---|---|---|---|
| - | Phase 0 compute/plan | DONE | Analysis/00-compute-decision.md | n/a |
| - | Phase 1 PacketDO + E1 | DONE | packetdo/, Analysis/E1-*.md | PASS_WITH_ISSUES -> fixed |
| ORG-B | Phase 2 synthetic benchmark (E2/E3/E4) | DONE (seed 0) | benchmark/, Analysis/E2-E4-*.md | pending multi-seed |
| ORG-B | multi-seed robustness (5 seeds) | RUNNING | benchmark/results/audit_*_seed*.json | - |
| ORG-B | E5 operator sensitivity | QUEUED | - | - |
| ORG-B | extra explainers (KernelSHAP, LIME) | QUEUED | - | - |
| ORG-A | CIC-IDS2017 flow data + natural artifacts | LAUNCHING | Experiments/realdata/ | - |
| ORG-A | byte-level dataset (USTC/ISCX) | LAUNCHING | - | - |
| ORG-C | verify Phase 2 + real-data | QUEUED | Analysis/*-VERIFICATION.md | - |
| ORG-D | editorial package | QUEUED | Working/ | - |

## Orchestrator activity log

- Office launched. ORG-A (real data, CPU/net), ORG-B (experiments, GPU), ORG-E (citations, net)
  running in parallel with no hardware contention by design.
- Disk incident resolved: 9 GB "loss" was the pip cache (parallel installs); purged, 23 GB free.
- Paper figures generated (fig1 operator-validity, fig2 false-confidence, fig3 necessity) from
  verified seed-0 results -> Working/figures/.
- Stable manuscript sections drafted as prose: Working/sections/01-introduction, 02-related-work,
  03-method. Results sections (4-10) await verified org outputs.
- Monitor armed for org-report completion; on completion -> ORG-C (verification) -> integrate.

## Standing findings (promoted, verified)

- E1: zero-mask 22% vs PacketDO 100% protocol-valid (seed 0, n=2000; verified, RFC 1071 cross-check).
- E2/E4 synthetic (seeds 0-4, ORG-B): explainers achieve precision@k=1.0 (find the true shortcut) yet
  fabricate importance. Saliency FC 0.684+/-0.037 at p=1.0 (robust); Occlusion FC 0 everywhere;
  TreeSHAP FC bimodal (0.5 when the model commits to one of two redundant shortcuts). CORRECTED vs
  seed-0: IG NOT clean at p=1.0 (0.300+/-0.274), DeepSHAP NOT clean at p=0.5 (0.233+/-0.325).
- E5 operator flip (ORG-B, C4 "so what"): under zero-mask, Occlusion (FC=0, faithful) is ranked LAST
  below Saliency (FC=0.67); under PacketDO all four tie (spread 0.001 < sd). Kendall tau 0.33. The
  removal operator manufactures the ranking. [pending ORG-C]
- E4 real data (ORG-A, CIC-IDS2017): destination-port shortcut is the #1 most-necessary feature
  (N rank 1/52) yet global TreeSHAP ranks it 5/52 and floods the top with packet-length proxies
  (false confidence); the #1 F1-necessity feature Fwd IAT Min is SHAP rank 36/52 (blind spot).
  Engelen TCP-appendix artifact: 43.5% of benign flows on original, 0 on corrected. [pending ORG-C]
- LIME finding (ORG-B): LIME FC=0.667 traced to sklearn StandardScaler scale_=1.0 on zero-variance
  fields -> LIME perturbs constant fields off-manifold: the protocol-invalidity thesis inside an
  explainer's own kernel. [pending ORG-C]
- Data-integrity: a file-naming race fabricated seed copies; caught by provenance guard, replaced with
  genuine reruns. ORG-C auditing.

## Verification status
- ORG-C (Phase 3-4 verification) RUNNING: 5 adversarial verifiers reproducing every number +
  provenance audit. No ORG-A/B number is promoted to the paper until ORG-C signs off.
