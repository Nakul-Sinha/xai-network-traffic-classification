# E1: Operator-validity study

Population: 2000 synthetic IP/TCP+UDP packets (seed 0). Baseline validity of the population: 100.0%.

## Headline

- Zero-masking (the deletion/occlusion default) macro validity: **22.4%**
- PacketDO macro validity: **100.0%**

When zero-masking makes a packet invalid, the predicate it violates:
  - l4_checksum: 13691 violations
  - ip_checksum: 8000 violations

## Per-field validity rate

| field | n | zero-mask valid | PacketDO valid |
|---|---|---|---|
| ip.ttl | 2000 | 0.0% | 100.0% |
| ip.tos | 2000 | 100.0% | 100.0% |
| ip.id | 2000 | 0.0% | 100.0% |
| ip.flags | 2000 | 100.0% | 100.0% |
| ip.src | 2000 | 0.0% | 100.0% |
| ip.dst | 2000 | 0.0% | 100.0% |
| tcp.sport | 1413 | 0.0% | 100.0% |
| tcp.dport | 1413 | 0.0% | 100.0% |
| tcp.seq | 1413 | 0.0% | 100.0% |
| tcp.ack | 1413 | 100.0% | 100.0% |
| tcp.flags | 1413 | 0.0% | 100.0% |
| tcp.window | 1413 | 35.4% | 100.0% |
| udp.sport | 587 | 0.0% | 100.0% |
| udp.dport | 587 | 0.0% | 100.0% |
| payload | 1963 | 0.6% | 100.0% |
