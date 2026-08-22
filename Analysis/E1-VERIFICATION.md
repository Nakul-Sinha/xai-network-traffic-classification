# E1 Phase-1 Verification Report (Adjudication)

**Experiment:** E1 — Operator-validity study (Contribution C1: PacketDO vs zero-mask)
**Adjudicated:** 2026-08-22
**Inputs:** 4 independent adversarial verifiers (`unit-tests`, `e1-numbers`, `checksum-claim`, `plan-consistency`)

---

## 1. Overall verdict: **PASS_WITH_ISSUES**

The core scientific finding of E1 is **sound, reproduced, and independently cross-checked**:

- Zero-mask macro validity ~0.22, PacketDO 1.00, baseline 1.00 — reproduced on a never-before-used
  seed (42) and independently recomputed from the per-field table (0.2241867 ≈ 0.2242).
- The validity checker is a **genuine predicate, not a rubber stamp**: 16/16 adversarial corruption
  probes correctly rejected; an independent non-scapy RFC 1071 implementation agrees with `valid()`
  on all sampled cases.
- The RFC 1071 tcp.window subtlety (0xFFFF≡0x0000 under one's-complement) is confirmed by
  micro-tests and matches the population frequency exactly (0.3387).
- Unit tests: 40 passed, 1 skipped; the skip is legitimate (tcp.ts absent), no config tricks inflate
  the count.

**Why not PASS:** the `plan-consistency` verifier **REFUTED two prose claims** in
`Analysis/E1-operator-validity.md`. Per the conservative rule ("if any verifier REFUTED a
load-bearing claim, overall is not PASS"), the overall grade cannot be PASS. Both refutations are
**prose/framing defects, not data or methodology failures** — the underlying experiment and its
numbers survive verification intact — so the grade is PASS_WITH_ISSUES rather than FAIL.

---

## 2. Check-by-check ledger

### verify:unit-tests — PASS
| # | Check | Verdict |
|---|---|---|
| 1 | `pytest packetdo/tests -q` = 40 passed, 1 skipped (41 collected) | CONFIRMED |
| 2 | The single skip is legitimate (tcp.ts option absent), not a disguised trivial pass | CONFIRMED |
| 3 | `test_zero_mask_breaks_validity` asserts a falsifiable condition | CONFIRMED |
| 4 | `test_packet_do_valid_tcp` asserts a falsifiable condition | CONFIRMED |
| 5 | `packet_do_bytes(ip.ttl:=128)` yields a protocol-valid packet | CONFIRMED |
| 6 | `packet_do_bytes(tcp.seq:=999999)` yields a protocol-valid packet | CONFIRMED |
| 7 | `zero_mask_bytes(ip.ttl)` produces an INVALID packet | CONFIRMED |
| 8 | `zero_mask_bytes(tcp.seq)` produces an INVALID packet | CONFIRMED |
| 9 | `validity.valid()` is a genuine predicate (not constant-True) | CONFIRMED |
| 10 | No config-level tricks (conftest/xfail/skipif/assert True) inflate counts | CONFIRMED |

### verify:e1-numbers — PASS_WITH_ISSUES
| # | Check | Verdict |
|---|---|---|
| 1 | Fresh-seed re-run reproduces headline (zero-mask ~0.22, PacketDO 1.00, baseline 1.00) | CONFIRMED |
| 2 | Macro validity = honest unweighted mean; matches independent recompute (0.2242) | CONFIRMED |
| 3 | Baseline 100% is measured; PacketDO 100% is not an artifact of skipping hard cases | CONFIRMED |
| 4 | Validity checker rejects known-invalid, accepts known-valid (not a rubber stamp) | CONFIRMED |

### verify:checksum-claim — PASS
| # | Check | Verdict |
|---|---|---|
| 1 | tcp.window ~34% valid under zero-mask = RFC 1071 one's-complement (0xFFFF→0x0000 invisible) | CONFIRMED |
| 2 | ip.proto is dependent, not independently intervenable; correctly excluded from INTERVENABLE | CONFIRMED |
| 3 | Zero-mask invalidity is always a checksum violation, never a parse failure | CONFIRMED |

### verify:plan-consistency — PASS_WITH_ISSUES
| # | Check | Verdict |
|---|---|---|
| 1 | Implemented E1 matches phase.md's planned E1 (parse-check + checksum-check) | CONFIRMED |
| 2 | Headline zero-mask macro 0.224 / 0.223 at n=2000 (seeds 0-1) reproduces | CONFIRMED |
| 3 | Multi-seed runs (n=1500, seeds 1-3) reproduce both figures byte-for-byte | CONFIRMED |
| 4 | Zero-mask violations are always checksums (l4 > ip), never parses | CONFIRMED |
| 5 | Prose: zero-mask validity is 0% for every info-carrying field incl. payload | **REFUTED** |
| 6 | tcp.window ~34% valid via RFC 1071 one's-complement | CONFIRMED |
| 7 | Unit tests: 40 passed, 1 skipped (no side effects on results/) | CONFIRMED |
| 8 | E1 supports C1 without overclaim; synthetic-vs-real limitation acknowledged | **REFUTED** |
| 9 | Results committed to git and reproducible from requirements.txt | **INCONCLUSIVE** |

**Tally:** 21 CONFIRMED · 2 REFUTED · 1 INCONCLUSIVE.

---

## 3. REFUTED / INCONCLUSIVE — what must be fixed

### R1 (REFUTED, load-bearing on prose) — "0%" payload overstatement
- **Where:** `Analysis/E1-operator-validity.md`, line 39.
- **Claim:** zero-mask validity is "**0%** for every field that carries real information
  (… payload)."
- **Reality:** `e1_results.json` reports payload zero-mask valid rate = **0.0068** (0.68%, 10/1465).
  Root cause verified: exactly 10 packets in the seed-3 population have all-zero payloads, so the
  mask is a no-op there.
- **Fix (one word):** change "0%" to "≈0% (0.7% for payload, where 10/1465 packets had an all-zero
  payload and masking is a no-op)." A reviewer diffing prose against the JSON will otherwise catch it.

### R2 (REFUTED, load-bearing on framing) — synthetic → real-traffic overclaim
- **Where:** `Analysis/E1-operator-validity.md`, line 65 (and headline framing).
- **Claim:** "E1 establishes … that the standard faithfulness operator is **invalid ~78% of the
  time on traffic**."
- **Reality:** the 78% figure is `1 − 0.22`, an **unweighted macro-mean over 15 fields on a
  synthetic population**. Three fields (ip.tos, ip.flags, tcp.ack) are 100% valid *only* because
  the synthetic generator left those bytes zero; on real traffic with nonzero TOS/flags the
  zero-mask rate would likely be **lower** (gap is conservative), but the number is not a measured
  real-traffic rate. The "synthetic" qualifier present in the headline is dropped here, and no
  real-pcap E1 (e.g. CIC-IDS2017) exists yet.
- **Fix:** (a) restore the "synthetic-population" qualifier on the 78% sentence and phrase it as a
  macro-average, not a per-packet real-traffic rate; (b) add one explicit limitation sentence that
  the number is synthetic and that a real-pcap replication is future work. This is a wording +
  disclosure fix; it does **not** require re-running E1.

### I1 (INCONCLUSIVE) — git commit hygiene / artifact traceability
Reproducibility itself is **confirmed** (scapy 2.7.0 == pin; numbers reproduce from a clean copy).
The inconclusive parts are provenance:
- HEAD's committed `e1_results.json` is a seed-2 run while the doc keys its narrative on seed-3.
- Committed `results/seed3.txt` contains only a scapy warning — the data capture missed.
- The n=2000 / seeds 0-1 headline row (0.224, 0.223) has **no saved artifact**; `results/` only
  ever held n=1500 seeds 1-3. The numbers reproduce on rerun, but nothing committed backs the table
  as written.
- **Fix:** commit a seed-3 (or n=2000 seeds 0-1) `e1_results.json` that matches the doc's headline,
  and re-capture `seed3.txt` with actual data. Make the committed artifact and the prose agree.

---

## 4. Operational / carry-forward items (not verdict-changing, but do before Phase 2 leans on this)

1. **`results/` was clobbered during verification.** It now holds an **n=1000 / seed=42** run
   (`zero_mask_macro_valid_rate = 0.2242`) instead of the pre-run seed-3/n-1500 output. A byte-exact
   pre-run backup exists at:
   `…/scratchpad/e1_backup/` (e1_results.json, e1_table.md, seed1-3.txt).
   **To restore:** copy those files back into
   `Experiments/e1_operator_validity/results/`. **Do NOT `git restore`** — seed*.txt and the JSON
   were already modified vs HEAD before the run, so `git restore` would discard the user's own
   uncommitted state.
2. **Latent bug for E4/E5:** `zero_mask_bytes`' `tcp.ts` branch returns `bytes(p)` after a scapy
   rebuild, which silently **recomputes checksums** — i.e. it is not a true zero-mask. Harmless in
   E1 (population has no TCP timestamps; the field is skipped) but **wrong if reused** in later
   phases. Fix before any experiment exercises TCP options.
3. **Robustness gap (non-blocking):** both PacketDO's 100% and the checker rely on scapy's
   serializer, so the figure is quasi-circular. It is currently defended by the 16/16 adversarial
   probes; an independent validator (tshark/tcpdump) would harden it. Worth one disclosure sentence.
4. **Unexplained sample loss:** payload n=1465 of 1500 because scapy re-parses ~35 UDP payloads as
   DNS/NTP layers (Raw absent), silently excluding them from payload intervention. Not wrong, but
   undocumented — note it or filter explicitly.
5. **ip.proto finding is asserted but not tested:** the structural/dependent classification is in
   prose and a `fields.py` comment, but no test/artifact demonstrates proto-resampling yields an
   invalid packet. Add a unit test to make the C1 sub-claim self-evidencing.

---

## 5. Sign-off

**Phase 2 MAY PROCEED.** E1's experimental result and infrastructure are sound and reproducible;
the two REFUTED items are prose/framing fixes (R1, R2) that must be applied to the write-up but do
not invalidate the data — with the conditions that (a) `results/` is restored from the scratchpad
backup, and (b) the `tcp.ts` zero-mask bug (item 2) is fixed before any later phase reuses the
operator on TCP options.
