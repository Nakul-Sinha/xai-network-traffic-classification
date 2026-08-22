# SUBMISSION CHECKLIST — Working/manuscript.md

**Prepared by:** ORG-D lead final pass. **Date:** 2026-08-23.
**Manuscript:** `Working/manuscript.md`, read end to end. Word count **7,552** total / **7,499** excluding the References block (matches Parcel D2's report).
**Verdict: NOT submission-ready as-is.** All load-bearing numbers are correctly cited from the PHASE34-VERIFICATION promoted list and trace to results files; no superseded seed-0 value leaked in; the 8-explainer count is consistent. What blocks submission is (a) four line-level numeric/wording defects found in this pass (Section 1b), and (b) format conversion work (Section 4). Estimated effort: ~1 hour of edits + the LaTeX/table conversion.

---

## 1. Numeric-claim provenance (spot-check)

Sixteen claims spot-checked against raw results files (requirement was 10). Legend: OK = value in manuscript matches file.

| # | Manuscript claim (location) | Backing file | Verdict |
|---|---|---|---|
| 1 | Zero-mask macro validity 22.4% vs PacketDO 100%; population 2,000 packets, baseline 100% (§1, §5.1) | `Experiments/e1_operator_validity/results/e1_results.json` (`summary.zero_mask_macro_valid_rate` = 0.224) | OK |
| 2 | tcp.window zero-mask validity 35.4% / RFC-1071 0xFFFF≡0x0000 subtlety (§5.1) | same file, `per_field["tcp.window"].zero_mask_valid_rate` = 0.3539; subtlety confirmed in `Analysis/E1-VERIFICATION.md` | OK |
| 3 | CNN Saliency FC 0.684 ± 0.037 at p=1.0, 0.68–0.74 across p, nonzero 5/5 seeds (§5.3, Fig 2) | `Experiments/benchmark/results/robustness.md` (aggregating `audit_p10{,_seed1..4}.json`) | OK |
| 4 | IG FC 0.300 ± 0.274 at p=1.0, nonzero 3/5 seeds (§5.3) | same, per-seed [0, 0.5, 0.5, 0.5, 0] | OK |
| 5 | DeepSHAP FC 0.233 ± 0.325 at p=0.5, fails 2/5, clean 5/5 at p≥0.7 (§5.3) | same, per-seed [0, 0, 0, 0.667, 0.5] | OK |
| 6 | TreeSHAP FC at p=1.0 0.200 ± 0.274, bimodal [0.5, 0.5, 0, 0, 0], model-commitment mechanism (§5.3) | same | OK |
| 7 | N(tcp.window) 0.273 ± 0.011 → 0.501 ± 0.020; N(ip.ttl) ≤ 0.004; null control within ±0.006; R(M)=1 (§5.2) | same, ground-truth tables | OK |
| 8 | E5: zero-mask AOPC IG 0.4776 > Sal > DS 0.4724 > Occ 0.4629; spread 0.0147 vs PacketDO 0.0010; per-seed sd ~0.0058; Kendall tau 0.333 (§6) | `Experiments/benchmark/results/e5_operator_sensitivity.{json,md}` | OK **except Saliency last digit — see 1b.2** |
| 9 | Occlusion rho 0.715 / Saliency rho 0.043 (seed-0, p=1.0) (§6) | `Experiments/benchmark/results/audit_p10.json` (`cnn.audit`) | OK |
| 10 | A2 baseline acc 0.99789 / macro-F1 0.91494; N(dst_port) 0.00434 ± 0.00012 acc, 0.04792 ± 0.00134 F1, rank 1/52; Brute-Force −37.8 pp (0.980 → 0.602) (§5.3) | `Experiments/realdata/results/a2_port_results.json` | OK |
| 11 | SHAP rank 5/52 (gini 13); 9/10 acc-only FC (criterion stated); group N 0.201 acc / 0.609 F1 vs max single 0.00064; Fwd IAT Min SHAP rank 36/52 (§5.3) | same file (incl. the machine-readable `audit.false_confidence_acc_only` block, count = 9 — ORG-C fix #4 closed) | OK |
| 12 | Six-run robustness: rank-1 in 6/6; SHAP rank 5–9, mean 6.67 ± 1.63; gini 13–21; FC ≥8/10 every run (8.83 ± 0.41); dual criterion 0–1/10; BF −35.3 ± 8.1 pp (range −20.0 to −44.1); cross-run N 0.00405 ± 0.00140; family fills 7–8 of top-10 every run; Fwd IAT Min in acc-necessity top-3 all 6 runs; seed-0 reproduced float-identically (§4.3, §5.3, §8, §10) | `Experiments/realdata/results/a2_robustness.md` + `a2_robustness_runs.json` (`aggregate.verdicts` all consistent) | OK |
| 13 | KernelSHAP FC 0 at 10.8 s/100; LIME FC 0.667 at 1.0 s/100; StandardScaler zero-variance mechanism (scale_=1.0 on constant bytes) (§5.4) | `Experiments/benchmark/results/extra_explainers.md` (10.78 / 1.04) | OK |
| 14 | Engelen artifact signature: Init_Win_bytes_forward = −1 on benign flows, present on original, vanishes on corrected (§5.3) | `Experiments/realdata/NATURAL_ARTIFACTS.md` (43.5% of Normal Traffic vs exactly 0 flows on corrected) | OK |
| 15 | 2,520,751 × 52 after hygiene; 700k subsample; 490k/210k split; R=10 / R=5-on-50k estimator split; RF configs; TreeSHAP on 1,000 rows; ~200–220 s/run, 1,259 s total (§4.3, §10) | `Experiments/realdata/DATASET.md`; `a2_robustness.md` setup + caveats | OK |
| 16 | Literature numbers: 107 works / 5 metrics; 348 occlusion experiments; TRUSTEE fidelity 1.00 / 3 bytes; ISCX byte-49 (§1) | Traced verbatim to Literature-review claims files by ORG-C (PHASE34-VERIFICATION C5.11); promoted | OK |
| — | `references.bib` "(55 entries)" (§References) | `Working/references.bib`: 55 `@` entries | OK |

## 1b. Flagged (unbacked-as-worded / stale) claims — MUST fix, all line edits

1. **§5.1 (and mirrored in §1 contribution C1): "11 of 15 fields are at exactly 0% validity."** The results file (`e1_results.json`) has **10** fields at exactly 0.0; the 11th, `payload`, is at 0.0056 (0.6%) — and §5.1 itself quotes payload-free "exactly". The promoted-list phrasing "11/15 fields at 0%" (no "exactly") inherited the same rounding. Fix: "10 of 15 fields at exactly 0% (an 11th, the payload, at 0.6%)" or "11 of 15 at or below 0.6%". Also §5.1's "the fields that survive do so only because the generator left them zero" then correctly covers ip.tos / ip.flags / tcp.ack (3 fields) + tcp.window separately.
2. **§6: Saliency zero-mask AOPC "0.4729".** The results file value is **0.473000** (`e5_operator_sensitivity.json`; ORG-C's own recomputation in PHASE34-VERIFICATION check 3.1 also says 0.473000). The promoted-list line "Sal 0.4729" contains a rounding slip. Fix: 0.4730.
3. **§4.1 and §10: "per-field unit-test suite (40 tests)".** "40 passed, 1 skipped" was the count at E1 verification time (`Analysis/E1-VERIFICATION.md`); the current tree collects **43** tests, **42 passed + 1 skipped** (re-run this pass: `pytest packetdo/tests -q`). Fix: say 42 (or drop the count).
4. **§5.3 / §7: "top-k precision … is 1.0" (k = number-of-necessary-fields convention).** Correctly relabelled per ORG-C fix #3 (the stored `precision_at_k` JSON field, 0.5 with hard-coded k=2, is nowhere cited — good), but the 1.0 value under the stated convention is currently backed only by ORG-C's recomputation (PHASE34-VERIFICATION C5.3), not by any stored results file. Fix: emit the convention-consistent value into a results JSON (small script over `audit_p*.json` field scores) so the claim traces to a file, or cite the verification report in the artifact.

Also fix (wording, not numbers): §1 and §5.1 phrase the macro rate as "a protocol-valid counterfactual for only 22.4% of intervenable fields" — 22.4% is the macro-averaged **per-intervention** validity rate (unweighted over 15 fields), not a fraction of fields (that would be 4/15). Reword to "…valid in only 22.4% of field interventions (macro-averaged over 15 fields)". This is exactly the ambiguity ORG-C fix #7 warned about.

## 2. Superseded seed-0 values: CLEAN

Grepped and read for every value on the NOT-promoted list (PHASE34-VERIFICATION):

- "TreeSHAP FC 0.50 at p=1.0" — absent; manuscript states 0.200 ± 0.274 bimodal, as the conditional model-commitment claim. ✔
- "DeepSHAP FC 0.0 everywhere" — absent; manuscript states the p=0.5 failure (2/5 seeds). ✔
- "IG clean at p=1.0" — absent; §5.3 explicitly says the seed-0 clean endpoint "does not generalize". ✔
- "Occlusion/DeepSHAP safest" (refuted item R1) — absent; §7 conditions the claim and §5.3, Fig 2 caption, §7, and §8 all carry the occlusion-circularity caveat. ✔
- Unlabelled "~78%" intro placeholder — resolved to the labelled 22.4% macro + per-field statistic (but see wording item above). ✔
- Stored `precision_at_k` = 0.5 field — never cited. ✔
- A2 numbers presented as seed-robust without the sweep — no; §4.3 defines the six-run robustness protocol and §5.3 pairs every seed-0 point value with its cross-run statistic, exactly per `a2_robustness.md` citation guidance (rank "never better than 5th", FC "at least 8 of 10", dual criterion "empty or a single feature", BF "largest per-class recall drop in every run"). Group-do() numbers and the Fwd IAT Min rank-36 blind spot are correctly labelled seed-0-only. ✔

## 3. Eight-explainer count: CONSISTENT

- Abstract: "eight widely used attribution methods" + full list of 8. ✔
- §1 contribution C3: "eight widely used explainers" + list + the DeepLIFT→{KernelSHAP, LIME} substitution note (ORG-C fix #8). ✔
- §4.4: "Eight attribution methods are audited" (6 on ByteCNN + TreeSHAP + impurity) + substitution note. ✔
- §10: "runs all eight explainers". ✔
- No stray "six explainers" anywhere (phase.md's six is superseded and only referenced via the substitution note). ✔

## 4. IEEE TNSM readiness

**Present and adequate:**
- Structure: Abstract → Intro (contribution list) → Related Work (7 lines of work) → Method → Experimental Setup → Results → E5 → Discussion → Threats to Validity → Limitations/Future Work → Reproducibility → References. Sound TNSM shape.
- Length: 7,499 words excluding references ≈ 9–10 two-column pages with 3 figures — comfortably inside TNSM regular-paper limits.
- Reproducibility statement: §10 is substantive (seeded scripts, provenance-guarded aggregation with exit-code requirement — ORG-C fixes #11 covered, public data, one make target).
- Threats section answers all five planned threats from phase.md §6 plus serializer circularity and seed sensitivity.
- All three figures exist (`Working/figures/fig{1,2,3}*.png`) and are each referenced and captioned.

**TODO for TNSM submission:**
1. **Figure numbering out of citation order:** Fig 3 (necessity) appears in §5.2 before Fig 2 (false confidence) in §5.3. Renumber so figures are cited in order (IEEE style requirement).
2. **No numbered tables.** All results are prose. phase.md promised at minimum the E1 validity table and the E5 "flip table"; reviewers will expect: Table I = E1 per-field validity, Table II = multi-seed FC audit (from `robustness.md`), Table III = E5 AOPC under both operators, Table IV = A2 six-run robustness. All four exist ready-made in the results .md files.
3. **Format conversion:** pandoc-style `[@key]` citations and markdown must be converted to IEEEtran LaTeX (`\cite{}`), with `references.bib` (55 entries) rendered — the References section is currently a pointer, which is not submittable.
4. **IEEE front matter:** Index Terms (keywords), author affiliation/contact, and the required AI-use / funding / conflict declarations per current IEEE policy.
5. **Figure production quality:** PNGs should be checked at column width (300+ dpi) or regenerated as vector (PDF/EPS) for production.
6. **§5.4 scoping:** state that the KernelSHAP/LIME numbers are the p=1.0 ByteCNN cell, seed 0, n=150 explained samples (they are single-cell, unlike the five-seed numbers around them).
7. **§7 criterion tag:** the "nine of TreeSHAP's global top ten" recurrence in §7 should repeat the "(accuracy-only criterion, Section 5.3)" tag — ORG-C fix #4 requires the criterion wherever the 9/10 figure appears.

## 5. Remaining TODOs before submission (beyond line edits)

1. **Deferred byte-level PCAP artifacts (B1/B2/B6):** ISCX Ethernet-header misalignment (byte-49), CIC-IDS2017 TTL 64/128, and sequence-number byte artifacts require packet captures; correctly declared as deferred/future work in §8 ("Synthetic versus real") and §9. No action for this submission; keep the framing.
2. **E7 (ET-BERT flagship table)** — optional per phase.md, not run; correctly in §9 future work.
3. **E8 / G5 diagnosticity study** — reserved; correctly framed in §9 with E5 as first datapoint.
4. **Independent validity checker (tshark)** — named in §8 as a further hardening step; optional, would strengthen the serializer-circularity answer.
5. **Precision@k results file** (item 1b.4) — small script, closes the last traceability gap.
6. **Bookkeeping (ORG-C fix #12):** confirm ORCHESTRATOR.md live-board rows were flipped to DONE (out of manuscript scope; not verified in this pass).
7. **Artifact release packaging:** §10 promises operator + tests + generator + drivers + `make all`; verify the make target actually reproduces all figures/tables from a clean checkout before upload (last done pre-D1/D2).

---

**Bottom line:** content is verified and promotion-compliant; the four Section-1b line edits plus the Section-4 format work (figures renumbered, four tables added, IEEEtran conversion, front matter) are what stand between this file and a TNSM submission.
