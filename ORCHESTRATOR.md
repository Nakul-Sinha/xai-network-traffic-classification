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

## Standing findings (promoted, verified)

- E1: zero-mask 22% vs PacketDO 100% protocol-valid (seed 0, n=2000; verified, RFC 1071 cross-check).
- E2/E4 synthetic (seed 0): explainers achieve precision@k=1.0 (find the true shortcut) yet Saliency
  FC 0.67-0.80, IntegratedGradients FC up to 0.75 at weak planting, even exact TreeSHAP FC 0.50 at
  p=1.0; DeepSHAP/Occlusion FC 0.0. Multi-seed confirmation pending before promotion to the paper.
