# E5: operator sensitivity of deletion-based faithfulness (p=1.0 ByteCNN)

Model: ByteCNN, seed 0, test n=800, base acc 0.9862. Ground truth (PacketDO necessity): N(tcp.window)=0.4838, all other fields N~0 (max |N| among others = 0.0063). K=10 fields removed cumulatively in each explainer's own ranking order. PacketDO curves averaged over 5 resampling seeds (sd in parentheses in the JSON).

## Deletion-AUC / AOPC under ZERO-MASK (protocol-invalid removal)

| explainer | AOPC (higher = 'more faithful') | deletion-AUC (lower = 'more faithful') | rank |
|---|---|---|---|
| IntegratedGradients | 0.4776 | 0.5086 | 1 |
| Saliency | 0.4730 | 0.5132 | 2 |
| DeepSHAP | 0.4724 | 0.5139 | 3 |
| Occlusion | 0.4629 | 0.5234 | 4 |

## Deletion-AUC / AOPC under PACKETDO (protocol-valid removal)

| explainer | AOPC | deletion-AUC | rank |
|---|---|---|---|
| IntegratedGradients | 0.4882 (sd 0.0053) | 0.4980 | 1 |
| Occlusion | 0.4881 (sd 0.0065) | 0.4982 | 2 |
| Saliency | 0.4875 (sd 0.0052) | 0.4988 | 3 |
| DeepSHAP | 0.4872 (sd 0.0063) | 0.4990 | 4 |

## Deletion curves (accuracy after removing top-j fields)

**IntegratedGradients** - ranking: tcp.window, ip.ttl, ip.dst, tcp.seq, tcp.sport, payload, ip.src, tcp.dport, ip.id, tcp.flags
| j | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 |
|---|---|---|---|---|---|---|---|---|---|---|
| zero-mask | 0.537 | 0.530 | 0.527 | 0.529 | 0.532 | 0.489 | 0.495 | 0.480 | 0.484 | 0.482 |
| PacketDO | 0.505 | 0.496 | 0.502 | 0.501 | 0.493 | 0.497 | 0.493 | 0.496 | 0.501 | 0.494 |

**Saliency** - ranking: tcp.window, ip.ttl, tcp.flags, ip.dst, tcp.seq, payload, tcp.sport, ip.src, ip.id, tcp.dport
| j | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 |
|---|---|---|---|---|---|---|---|---|---|---|
| zero-mask | 0.537 | 0.530 | 0.530 | 0.527 | 0.529 | 0.511 | 0.489 | 0.495 | 0.501 | 0.482 |
| PacketDO | 0.505 | 0.496 | 0.501 | 0.502 | 0.494 | 0.497 | 0.498 | 0.499 | 0.500 | 0.493 |

**DeepSHAP** - ranking: tcp.window, ip.ttl, tcp.seq, tcp.sport, payload, ip.src, ip.id, ip.dst, tcp.flags, tcp.dport
| j | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 |
|---|---|---|---|---|---|---|---|---|---|---|
| zero-mask | 0.537 | 0.530 | 0.531 | 0.529 | 0.515 | 0.505 | 0.505 | 0.502 | 0.501 | 0.482 |
| PacketDO | 0.505 | 0.496 | 0.502 | 0.504 | 0.494 | 0.498 | 0.496 | 0.501 | 0.502 | 0.491 |

**Occlusion** - ranking: tcp.window, ip.ttl, ip.id, tcp.dport, tcp.flags, ip.dst, tcp.seq, ip.src, tcp.sport, payload
| j | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 |
|---|---|---|---|---|---|---|---|---|---|---|
| zero-mask | 0.537 | 0.530 | 0.530 | 0.530 | 0.530 | 0.530 | 0.529 | 0.525 | 0.510 | 0.482 |
| PacketDO | 0.505 | 0.496 | 0.499 | 0.501 | 0.492 | 0.494 | 0.498 | 0.500 | 0.501 | 0.494 |

## Paired per-seed AOPC under PacketDO (same resampling seeds for every explainer)

| resample seed | IntegratedGradients | Saliency | DeepSHAP | Occlusion |
|---|---|---|---|---|
| 100 | 0.4884 | 0.4900 | 0.4872 | 0.4886 |
| 101 | 0.4897 | 0.4884 | 0.4898 | 0.4921 |
| 102 | 0.4879 | 0.4867 | 0.4874 | 0.4875 |
| 103 | 0.4957 | 0.4940 | 0.4955 | 0.4957 |
| 104 | 0.4792 | 0.4782 | 0.4761 | 0.4764 |

AOPC spread across explainers: zero-mask 0.0147 vs PacketDO 0.0010 (15x); PacketDO per-seed sd ~0.0058, so the PacketDO ordering is within resampling noise (a statistical tie), while the zero-mask ordering is deterministic and operator-manufactured.

## Verdict: does the explainer ranking survive the operator change?

- zero-mask ranking : IntegratedGradients > Saliency > DeepSHAP > Occlusion
- PacketDO ranking  : IntegratedGradients > Occlusion > Saliency > DeepSHAP
- Spearman rho = 0.4 (p=0.6), Kendall tau = 0.3333 (p=0.75)
- **RANKING FLIPS.** Reversed pairs: Saliency vs Occlusion; DeepSHAP vs Occlusion

## Interpretation (what the ground truth licenses us to say)

The p=1.0 CNN provably uses exactly one field: N(tcp.window)=0.4838, every other field |N|<=0.006 (E3). All four explainers rank tcp.window first, so from the interventional standpoint all four top-1 rankings are equally faithful, and removals at j>=2 touch only fields the model does not use. A sound deletion metric must therefore score the four explainers (near-)identically. PacketDO does exactly that: the AOPC spread is within resampling noise. Zero-mask instead differentiates them by a spread an order of magnitude larger, produced entirely on protocol-invalid inputs (stale checksums, window=0, zeroed header bytes; cf. E1: only 22% of zero-mask outputs are valid packets), and it demotes Occlusion - the explainer with zero false-confidence in E2/E4 - to LAST place while promoting Saliency (false-confidence 0.67) above it. The zero-mask curves are also non-monotone (accuracy RISES after some deletions, e.g. IG j=4-5, Saliency j=8-9), confirming the model's response to off-manifold inputs is arbitrary. Conclusion: the deletion verdict depends on the removal operator; zero-mask fabricates an explainer ordering that the protocol-valid operator shows to be an artifact.

