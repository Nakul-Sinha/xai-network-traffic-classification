# ORG-E Citation Verification Report

Date: 2026-08-22
Output: `Working/references.bib` (55 unique entries; 64 collected entries deduplicated by key)

## Summary

| Metric | Count |
|---|---|
| Entries written to references.bib | 55 |
| Citations deep-verified by ORG-E this pass | 9 |
| Metadata corrections applied | 2 |
| Bibliographic notes recorded | 2 |
| Flagged items needing attention (full-text access pending) | 5 |

Duplicate keys removed during compilation (identical works, first canonical occurrence kept):
`liu2019fsnet` (x4), `guidotti2021evaluating` (x4), `wang2017malware` (x2), `keshk2023explainable` (x2), `kalakoti2024improving` (x2).

## Corrections applied (fixed in references.bib)

1. **nascita2025survey** — Resource.md metadata was wrong on two counts:
   - Year: listed as 2024, but the canonical journal record is IEEE Communications Surveys & Tutorials, vol. 27, no. 5, pp. 3165-3198, **2025** (the 2024 in the DOI reflects early-access posting in Nov 2024). Cited as 2025.
   - Title: the real title spells out "Explainable Artificial Intelligence", not "XAI".
   - Author order corrected per Crossref: Nascita, Aceto, Ciuonzo, Montieri, Persico, Pescape.
2. **bastings2022shortcuts** — Resource.md gave only the short title; the canonical title carries the subtitle "A Protocol for Evaluating the Faithfulness of Input Salience Methods for Text Classification". Venue/year (EMNLP 2022) were correct. Full title used in the bib.

## Bibliographic notes (no change needed)

3. **yang2019bam** — Confirmed arXiv-only (CoRR 2019): no conference/journal version exists in DBLP, Crossref, or Semantic Scholar. v1 (Jul 2019) was titled "BIM: Towards Quantitative Evaluation of Interpretability Methods with Ground Truth"; renamed to BAM in v2 (Nov 2019). Resource.md's venue-less "2019" is correct; cited as @misc/arXiv with a "not peer-reviewed" note.
4. **adebayo2020debugging** — The arXiv version is the extended paper; the shorter version is the official NeurIPS 2020 proceedings paper (DBLP conf/nips/AdebayoMLK20). Venue/year in Resource.md correct.

## Flagged items — NEED ATTENTION (bibliographic record confirmed; full text still pending)

These five have Crossref-confirmed venue/year/DOI, so the bib entries are safe. However, the deep-read was abstract-only, so **do not cite content claims from these papers until the full text is pulled via institutional access**:

5. **liu2019fsnet** (FS-Net, IEEE INFOCOM 2019, pp. 1171-1179) — abstract-only; IEEE returns 418 on mirrors. Authors confirmed via Crossref: Liu, He, Xiong, Cao, Li.
6. **guidotti2021evaluating** (Artificial Intelligence, vol. 291, art. 103428) — abstract + author code only. Single author Riccardo Guidotti confirmed. The "2020" in the DOI is the acceptance year; the journal issue is Feb 2021 — cited as **2021**. Full text needed before citing its limitations.
7. **wang2017malware** (ICOIN 2017, pp. 712-717) — abstract-only, no OA copy. Authors confirmed via Crossref: Wang, Zhu, Zeng, Ye, Sheng.
8. **keshk2023explainable** (Information Sciences, vol. 639, art. 119000, 2023) — abstract-only. Authors confirmed via Crossref: Keshk, Koroniotis, Pham, Moustafa, Turnbull, Zomaya.
9. **kalakoti2024improving** (IEEE Internet of Things Journal, vol. 11, no. 10, pp. 18237-18254, 2024) — abstract-only. Authors confirmed via Crossref: Kalakoti, Bahsi, Nomm.

## Notes on the remainder of the bib

The other 46 entries were collected and verified by the other org branches and are written verbatim as supplied (dedupe only; no metadata edits by ORG-E). Two of them are preprints and should be tracked for later publication status updates: `alquliti2025evaluating` (arXiv 2505.08006) and `vourganas2026stabilising` (arXiv 2605.22529, submitted to ACM TAISAP); `wang2026biasseeker` (arXiv 2601.10180) is likewise preprint-only.
