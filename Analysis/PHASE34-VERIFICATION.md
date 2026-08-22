# PHASE 3/4 VERIFICATION — ORG-C ADJUDICATION

**Date:** 2026-08-22
**Adjudicator:** ORG-C (adversarial verification org)
**Inputs:** 5 independent verifier reports (C1 provenance, C2 multi-seed, C3 E5 operator flip, C4 real-data CIC-IDS2017, C5 cross-document consistency). Every verifier recomputed numbers from raw result files with its own scripts; C3 and C4 additionally re-executed pipelines end-to-end.

---

## OVERALL VERDICT: **PASS_WITH_ISSUES**

Every load-bearing experimental number was independently reproduced (CONFIRMED) by at least one adversarial verifier, most from raw JSONs and two by full pipeline re-execution. The single REFUTED item is not an experimental claim but a propagation failure: the Occlusion-circularity caveat marked "state in paper" exists only in the Analysis file and is absent from the paper draft, which instead asserts the opposite ("occlusion, DeepSHAP are safest"). Under the conservative rule this blocks PASS but does not constitute a refuted result, so the phase does not FAIL. The draft must be corrected before ORG-D fills placeholders (see MUST FIX).

**Verifier verdicts:** C1 PASS · C2 PASS · C3 PASS · C4 PASS_WITH_ISSUES · C5 PASS_WITH_ISSUES

---

## PROVENANCE / FABRICATION INCIDENT: **RESOLVED — PROVENANCE CLEAN**

The earlier incident (a seed file that was a byte-copy of the seed-0 file) is fully resolved on the current tree:

1. **Internal seed matches filename in 20/20 files.** All `audit_p{05,07,09,10}_seed{1,2,3,4}.json` files carry an internal `seed` field equal to the filename seed; the 4 suffix-less base files carry `seed=0`. The `p` field also matches in every file. (C1, own loader, 0 mismatches.)
2. **No byte-identical duplicates.** 20 unique MD5s out of 20 files; hardened check re-hashed each file with the `seed` field removed — still 20 unique. A smarter fabrication (copy + edited seed field) would have been caught. (C1.)
3. **Per-seed values genuinely diverge.** `cnn_test_acc` and `N(tcp.window)` are 5-unique vectors at every p (one benign tie: p=0.5 seeds 0 and 2 both at acc 0.7612 = 609/800; all other content differs — confirmed coincidence, not a copy). (C1.)
4. **The guard in `aggregate_seeds.py` demonstrably works.** C1 sandbox-recreated the incident (byte-copied `audit_p10.json` over `audit_p10_seed3.json`): the script printed `SEED MISMATCH ... refusing to use it`, excluded the file, wrote a `**Provenance exclusions:**` section, flagged affected cells `(n=4)`, and exited 1. The clean run reproduced the repo's `robustness.md` byte-identically.
5. **Independent re-audit by C5** reached the same conclusion (20/20 seeds match, no duplicates).

**Residual (accepted) risks, not blockers:**
- The guard trusts the internal `seed` field; a fabricated copy with an edited seed would pass it. Detection of that case relies on cross-file hash/value comparison, which was run and is clean. Recommend keeping the hash check in CI.
- The guard excludes-and-continues (exit 1) rather than hard-aborting; **automation must check the exit code**, not just consume the generated tables.

`provenance_clean: true`

---

## CHECK TABLE — every check, with independently recomputed values

### C1 — Provenance (PASS)

| # | Check | Claimed | Independently computed | Verdict |
|---|-------|---------|------------------------|---------|
| 1.1 | Internal seed = filename seed, all 20 files | 20/20 | 20/20 match (p field also matches) | CONFIRMED |
| 1.2 | No byte-identical cross-seed files | all unique | 20 unique MD5s; also unique with seed field stripped | CONFIRMED |
| 1.3 | Per-seed acc / N(tcp.window) genuinely differ | differ | 5-unique vectors at every p (e.g. p=1.0 acc [0.9862, 0.9988, 0.9938, 0.9975, 0.9962]) | CONFIRMED |
| 1.4 | aggregate_seeds.py guard rejects mismatches | rejects | Sandboxed tamper test: detected, excluded, exit 1; clean run byte-identical to robustness.md | CONFIRMED |

### C2 — Multi-seed robustness (PASS)

| # | Check | Claimed (robustness.md) | Independently computed | Verdict |
|---|-------|-------------------------|------------------------|---------|
| 2.a | CNN Saliency FC @ p=1.0 | 0.684 ± 0.037 | 0.6836 ± 0.0371, per-seed [0.667, 0.667, 0.75, 0.667, 0.667], 5/5 nonzero; high at all p (0.684–0.743) | CONFIRMED |
| 2.b | CNN Occlusion FC everywhere | 0 | exactly 0.0 in 20/20 cells | CONFIRMED |
| 2.c | CNN IG FC @ p=1.0 | 0.300 ± 0.274 | 0.3000 ± 0.2739, per-seed [0, 0.5, 0.5, 0.5, 0] → nonzero 3/5; seed-0 "IG clean at p=1.0" does NOT generalize | CONFIRMED |
| 2.d | CNN DeepSHAP FC @ p=0.5 | 0.233 ± 0.325 | 0.2334 ± 0.3250, per-seed [0, 0, 0, 0.667, 0.5] → fails 2/5 seeds; clean 5/5 at p ≥ 0.7 | CONFIRMED |
| 2.e | RF TreeSHAP FC @ p=1.0 bimodal | 0.200 ± 0.274, [0.5, 0.5, 0, 0, 0] | matches; mechanism verified — FC=0.5 exactly in seeds where the RF commits to a single shortcut field (N of the other ≈ 0) | CONFIRMED |

### C3 — E5 operator-sensitivity flip (PASS)

| # | Check | Claimed | Independently computed | Verdict |
|---|-------|---------|------------------------|---------|
| 3.1 | Zero-mask AOPC order IG > Sal > DS > Occ (Occ last) | yes | 0.477625 > 0.473000 > 0.472375 > 0.462875; Occlusion rank 4/4 | CONFIRMED |
| 3.2 | PacketDO = statistical tie | spread ~0.001 < per-seed sd | spread 0.0010; per-seed sd 0.0052–0.0065 (ratio 0.17); zero-mask spread 0.0147 = 14.7x larger | CONFIRMED |
| 3.3 | Kendall tau between orderings | ~0.33 | tau = 0.3333 (4 concordant / 2 discordant); flipped pairs (Sal, Occ) and (DS, Occ) | CONFIRMED |
| 3.4 | Audit inversion (zero-mask demotes the FC=0 explainer) | yes | Occlusion FC=0.0, rho=0.715 (best) vs Saliency FC=0.667, rho=0.043 (worst) — yet zero-mask ranks Saliency 2nd, Occlusion 4th | CONFIRMED |
| 3.5 | run_e5.py reproduces end-to-end | yes | Fresh retrain from scratch: acc 0.9862, N(tcp.window)=0.4838, IG zero-mask AOPC 0.4776 / PacketDO 0.4882 (sd 0.0053) — exact matches (DeepSHAP/Occlusion curves still computing at report deadline; all stored numbers independently recomputed from raw curves regardless) | CONFIRMED |

### C4 — Real-data CIC-IDS2017 (PASS_WITH_ISSUES)

| # | Check | Claimed | Independently computed (full re-run, identical seed schedule) | Verdict |
|---|-------|---------|---------------------------------------------------------------|---------|
| 4.0 | Baseline RF (2,520,751 x 52, 490k/210k split) | acc 0.99789, macro-F1 0.91494 | acc 0.997890, macro-F1 0.914942 | CONFIRMED |
| 4.a | N(dst_port) | 0.00434 ± 0.00012 acc / 0.04792 ± 0.00134 F1; rank 1/52 acc | 0.004343 ± 0.000124 / 0.047918 ± 0.001338; N_acc rank 1/52, N_f1 rank 2/52 (behind Fwd IAT Min 0.09935) | CONFIRMED |
| 4.b | TreeSHAP global rank of dst_port | 5/52 (0.00589); gini 13/52 | 5/52, mean\|SHAP\| 0.005892; gini 13/52 (0.02654); full top-10 to 5 decimals | CONFIRMED |
| 4.c | Brute-Force recall under do(dst_port) | −37.8 pp (0.980 → 0.602) | −0.37795 (0.9803 → 0.6024); Bots −0.049, DoS −0.031, Port Scanning ≈ 0 | CONFIRMED |
| 4.d | 9 of SHAP top-10 are false-confidence (N_acc < 0.002 only) | 9/10 | 9/10 (all but dst_port; max N_acc 0.00064 = 15% of dst_port's) | CONFIRMED |
| 4.d' | Dual criterion (N_acc < 0.002 AND N_f1 < 0.005) → empty FC set | 0/10 | 0/10 (all nine have N_f1 0.0054–0.0196); JSON `audit.false_confidence_features=[]` matches | CONFIRMED |
| 4.e | Redundancy group do(): packet-length family | N_acc 0.201 / N_f1 0.609 | 0.20090 / 0.60850 vs max single 0.00064 / 0.0196; Engelen quartet N_f1 0.11535 | CONFIRMED |

### C5 — Cross-document consistency (PASS_WITH_ISSUES)

| # | Check | Independently computed | Verdict |
|---|-------|------------------------|---------|
| 5.1 | Draft C1/§5.1: zero-mask macro validity 22% vs PacketDO 100% | 0.224 vs 1.000; tcp.window zero-mask 0.3539; 11/15 fields at 0% | CONFIRMED |
| 5.2 | Draft §5.2: N(win) rises with p, N(ttl)≈0, R(M)=1 | seed-0 0.2687→0.4838; multi-seed 0.273±0.011 → 0.501±0.020; \|N(null)\| ≤ 0.0062; R=1 at all p | CONFIRMED |
| 5.3 | "precision@k = 1.0 everywhere" | 1.0 ONLY under k=#truly-necessary convention; stored `precision_at_k` = 0.5 in all CNN cells and RF p=1.0 (k=2 hard-coded in explainers.py) | CONFIRMED (metric-mismatch issue) |
| 5.4 | LIME FC=0.667 mechanism (StandardScaler scale_=1.0 on zero-variance features) | reproduced FC=0.667; scale_[22]=scale_[23]=1.0; all 17 zero-variance columns at scale_=1.0; mechanism verified in lime source | CONFIRMED |
| 5.5 | Occlusion-circularity caveat in Analysis file | present, E2-E4-synthetic-benchmark.md lines 113–115 ("state in paper") | CONFIRMED |
| 5.6 | Occlusion-circularity caveat in **paper draft** | 0 occurrences in Working/paper-draft.md and Working/sections/*; §7 (line 136) asserts the opposite | **REFUTED** |
| 5.7 | Weakened IG claim propagated to E2-E4 doc + board | present in both | CONFIRMED |
| 5.8 | Weakened DeepSHAP claim propagated to E2-E4 doc + board | present in both; NOT yet in the draft (see MUST FIX #1) | CONFIRMED |
| 5.9 | Multi-seed headline numbers consistent across robustness.md / ORG-B report | all recomputed and matching | CONFIRMED |
| 5.10 | E5 numbers consistent in draft §5.3/§6 | reproduce from raw curves | CONFIRMED |
| 5.11 | Literature prose numbers (107/5; 348; TRUSTEE 0.959; ISCX byte-49) have backing files | all four traced verbatim to Literature-review claims files | CONFIRMED |

---

## REFUTED / INCONCLUSIVE ITEMS AND REQUIRED FIXES

**REFUTED (1):**

- **R1 (C5.6):** *"The Occlusion-circularity caveat is stated in the paper draft."* It is not. It exists only in `Analysis/E2-E4-synthetic-benchmark.md` lines 113–115, explicitly marked "state in paper". Worse, `Working/paper-draft.md` line 136 (§7) asserts "Intervention-aligned methods (occlusion, DeepSHAP) are safest" — an overclaim in the opposite direction (DeepSHAP fails 2/5 seeds at p=0.5, and Occlusion's FC=0 is partly by construction since occlusion is structurally close to PacketDO).
  **Required fix:** Add the circularity caveat to §7 (and anywhere Occlusion FC=0 is cited); weaken the "safest" claim to condition on planting strength and name the E5 disentanglement.

**INCONCLUSIVE (0):** none. Every check reached CONFIRMED or REFUTED.

**Open dependency (not a refutation):** ORG-A flag #2 — multi-seed + alternative RF config (depth/leaf) robustness for the real-data A2 experiment — remains open. C4's re-run is an exact re-execution of the same seeds: it establishes correctness/reproducibility, not seed robustness.

---

## MUST FIX BEFORE ORG-D FILLS PLACEHOLDERS

1. **`Working/paper-draft.md` line 122 (§5.3):** replace seed-0 claims "DeepSHAP/Occlusion FC 0.0, TreeSHAP FC 0.50 at p=1.0" with multi-seed values: DeepSHAP FC 0.233 ± 0.325 at p=0.5 (fails 2/5 seeds; clean at p ≥ 0.7); TreeSHAP FC at p=1.0 = 0.200 ± 0.274, bimodal [0.5, 0.5, 0, 0, 0] — state as the conditional model-commitment claim, not "0.50".
2. **`Working/paper-draft.md` line 136 (§7) + missing circularity caveat** (= REFUTED item R1 above).
3. **precision@k metric mismatch:** do not cite the stored `precision_at_k` JSON field as 1.0 — it is 0.5 in all CNN cells and RF p=1.0 (k=2 hard-coded in `Experiments/benchmark/explainers.py audit()`). Either recompute the field under the k=#truly-necessary convention or relabel the prose metric; make draft §5.3, ORCHESTRATOR standing findings, and the E2-E4 doc agree.
4. **A2 "9 of top-10 SHAP are false-confidence":** state the criterion (acc-only N_acc < 0.002) wherever the 9/10 number appears; under the dual criterion the set is empty and the correct headline is the redundancy/credit-splitting mechanism (group N_acc 0.201 vs max single 0.00064). Add an acc-only FC field to `a2_port_results.json` so the promoted number is machine-traceable.
5. **A2 seed robustness (ORG-A flag #2):** run multi-seed + alternative depth/min_leaf before presenting real-data numbers as robust (they are hereby promoted as *reproducible, seed-0, single-config*).
6. **`Analysis/E2-E4-synthetic-benchmark.md` lines 51–61:** annotate or edit the refuted seed-0 FC tables (IG 0.00 at p=1.0, DeepSHAP 0.00 everywhere) inline — do not rely on the "supersedes" header; ORG-D may copy tables verbatim.
7. **Intro C1 placeholder "~78% of intervenable fields":** pick one statistic and label it — 77.6% of field-packet interventions invalid (macro per-intervention rate) vs 11/15 = 73% of fields at 0% validity.
8. **Abstract vs §4 explainer count:** abstract says "six", §4 lists 8 (IG, Saliency, DeepSHAP, Occlusion, KernelSHAP, LIME, TreeSHAP, impurity); phase.md's six included DeepLIFT, which was never run — reconcile and note the substitution.
9. **E5 wording:** say "spread below resampling noise" rather than "statistical tie" (DS-vs-Occ paired diffs are one-signed, p≈0.12); hang the C4 claim on the Occlusion demotion (robust: 0.0095 below DeepSHAP, ~15x the PacketDO spread) not the full 4-way order (zero-mask ranks 2–3 differ by 0.000625 = half of one test count); "15x" is exactly 14.7x.
10. **A2 table hygiene:** footnote that the FC table's dst_port N_acc (0.00421) is the 50k-subset R=5 estimator while the headline 0.00434 is full-test R=10 (agree within ~5%).
11. **Automation:** any caller of `aggregate_seeds.py` must check the exit code (guard excludes-and-continues with exit 1, it does not hard-abort).
12. **Bookkeeping:** update ORCHESTRATOR.md live-board rows (multi-seed / E5 / extra-explainers show RUNNING/QUEUED but are DONE with outputs on disk).

---

## SIGN-OFF: NUMBERS PROMOTED TO THE PAPER

Promoted (independently reproduced; cite exactly as stated, with any bracketed condition):

**E1 (operator validity):** zero-mask macro validity 22.4% vs PacketDO 100%; 11/15 fields at 0% zero-mask validity; tcp.window zero-mask validity 0.3539 (RFC-1071 subtlety).

**E2–E4 synthetic benchmark (multi-seed, n=5):**
- CNN Saliency FC at p=1.0: **0.684 ± 0.037** (nonzero 5/5 seeds; range 0.684–0.743 across p).
- CNN Occlusion FC: **0.000 ± 0.000** at every p and seed [must carry the circularity caveat — fix #2].
- CNN IG FC at p=1.0: **0.300 ± 0.274** (nonzero 3/5 seeds) — replaces the seed-0 "IG clean at p=1.0" claim.
- CNN DeepSHAP FC at p=0.5: **0.233 ± 0.325** (fails 2/5 seeds); clean 5/5 at p ≥ 0.7.
- RF TreeSHAP FC at p=1.0: **0.200 ± 0.274**, bimodal [0.5, 0.5, 0, 0, 0], as the conditional model-commitment claim.
- Shortcut reliance: N(tcp.window) rises **0.273 ± 0.011 → 0.501 ± 0.020** with p; N(ip.ttl) ≈ 0; R(M)=1.
- LIME FC = **0.667** with the verified StandardScaler zero-variance mechanism.

**E5 (operator sensitivity):** zero-mask AOPC IG 0.4776 > Sal 0.4729 > DS 0.4724 > Occ 0.4629 (spread 0.0147) vs PacketDO spread 0.0010 < per-seed sd ~0.0058; Kendall tau 0.333; headline = Occlusion demotion under zero-mask despite FC=0 / rho=0.715 [wording per fix #9].

**A2 (CIC-IDS2017 real data — promoted as reproducible seed-0 single-config, robustness run pending, fix #5):** baseline RF acc 0.99789 / macro-F1 0.91494; N(dst_port) 0.00434 ± 0.00012 acc / 0.04792 ± 0.00134 F1, rank 1/52 by acc-necessity; SHAP rank of dst_port 5/52 (0.00589), gini 13/52; Brute-Force recall −37.8 pp (0.980 → 0.602) under do(dst_port); 9/10 SHAP-top-10 false-confidence [acc-only criterion; dual criterion → empty, fix #4]; group do() packet-length family N_acc 0.201 / N_f1 0.609 vs max single 0.00064.

**Literature numbers** (107 works / 5 metrics; 348 occlusion experiments; TRUSTEE 0.959 with 3 bytes at fidelity 1.00; ISCX byte-49 misalignment): traced to claims files; citable.

**NOT promoted / blocked until fixed:** the stored `precision_at_k` JSON value (fix #3); "DeepSHAP/Occlusion safest" (§7, fix #2); seed-0 FC values "TreeSHAP 0.50", "DeepSHAP 0.0 everywhere", "IG clean at p=1.0" (fixes #1, #6); the unlabeled "~78%" intro figure (fix #7); any A2 number presented as seed-robust (fix #5).

---

*Adjudicated under the conservative rule: any REFUTED load-bearing claim → not PASS. The one REFUTED item is a draft-propagation defect, not an experimental result; all load-bearing numbers reproduced. Verdict: PASS_WITH_ISSUES.*
