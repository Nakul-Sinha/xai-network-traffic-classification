# E1: Operator-validity study (result)

**Status:** complete. Code: `Experiments/e1_operator_validity/run_e1.py`. Operator:
`Experiments/packetdo/`. Unit tests: 40 passed, 1 skipped.

## What E1 tests

The XAI-NTC literature evaluates explanation faithfulness with deletion / occlusion / AOPC
metrics that "remove" a feature by setting it to zero. E1 asks: when you apply that operator to a
network packet, is the result still a packet a real host could have sent? It contrasts the two
operators the paper defines:

- **zero-mask** (the field's default): overwrite the field's on-wire bytes with `0x00`, recompute
  nothing. This is what deletion/occlusion does to a byte-level input.
- **PacketDO** (ours): set the field to a value resampled from the pooled empirical marginal, then
  recompute every structurally dependent field (IP/TCP/UDP checksums, IP total length, TCP data
  offset). Contribution C1.

Validity is decomposed into checkable predicates (parses, ip_checksum, l4_checksum, ip_len, ihl,
tcp_dataofs, udp_len); a packet is valid iff all applicable predicates hold.

## Headline result (2000 synthetic IP/TCP+UDP packets, baseline validity 100%)

| operator | macro validity rate | seeds 0-1 |
|---|---|---|
| zero-mask (deletion default) | **~22%** | 0.224, 0.223 |
| PacketDO (ours) | **100.0%** | 1.000, 1.000 |

Multi-seed runs (n=1500, seeds 1-3) reproduce both figures; see `results/seed*.txt`.

When zero-masking invalidates a packet, the violated predicate is always a checksum
(`l4_checksum` most often, then `ip_checksum`) - never a parse failure. The invalidity is silent:
the bytes still parse as a packet, so a model consumes them and returns a confident prediction on
an input that could never occur on a network. That is precisely why the resulting "importance"
scores are untrustworthy.

## Per-field structure (the informative part)

Zero-masking's validity rate is **0%** for every field that carries real information
(ip.ttl, ip.id, ip.src/dst, tcp.sport/dport/seq/flags, udp.sport/dport, payload). It is 100% only
for fields that were already zero in the population (ip.tos, ip.flags, tcp.ack) - i.e. where
masking is a no-op that removes nothing.

One field, **tcp.window, is ~34% valid under zero-masking**, and the reason is a genuine and
citable arithmetic subtlety, not noise: a window value of 65535 (`0xFFFF`) masked to `0x0000` is
invisible to the Internet checksum, because `0x0000` and `0xFFFF` are the two representations of
zero in one's-complement arithmetic (RFC 1071). Since ~1/3 of the population had window=0xFFFF,
~1/3 of window zero-masks are checksum-valid by accident. This makes the point sharper: zero-masking
is not merely usually-invalid, its validity depends on the field's *value* in a way no principled
faithfulness operator should.

PacketDO is 100% valid for every independently intervenable field.

## A finding that refines the method

`ip.proto` cannot be intervened on independently: its value (6=TCP, 17=UDP) is determined by the L4
header that follows, so resampling it while keeping the L4 bytes yields a self-inconsistent packet
- exactly like a stale checksum. We therefore classify `ip.proto`, alongside checksums and length
fields, as a *structural/dependent* field that PacketDO recomputes rather than resamples. This is a
small but real contribution to defining what "intervenable" means for packets: the free degrees of
freedom are not all header fields, only those not fixed by the grammar.

## Why this motivates the whole paper

E1 establishes, quantitatively, that the standard faithfulness operator is invalid ~78% of the time
on traffic. Every downstream faithfulness number in the literature that used it was computed partly
on impossible inputs. The rest of the paper measures how much that matters (E4, E5) using PacketDO,
which E1 shows is valid by construction.
