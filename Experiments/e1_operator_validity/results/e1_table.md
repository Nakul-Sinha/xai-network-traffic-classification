# E1: Operator-validity study

Population: 1500 synthetic IP/TCP+UDP packets (seed 2). Baseline validity of the population: 100.0%.

## Headline

- Zero-masking (the deletion/occlusion default) macro validity: **22.4%**
- PacketDO macro validity: **100.0%**

When zero-masking makes a packet invalid, the predicate it violates:
  - l4_checksum: 10244 violations
  - ip_checksum: 6000 violations

## Per-field validity rate

| field | n | zero-mask valid | PacketDO valid |
|---|---|---|---|
| ip.ttl | 1500 | 0.0% | 100.0% |
| ip.tos | 1500 | 100.0% | 100.0% |
| ip.id | 1500 | 0.0% | 100.0% |
| ip.flags | 1500 | 100.0% | 100.0% |
| ip.src | 1500 | 0.0% | 100.0% |
| ip.dst | 1500 | 0.0% | 100.0% |
| tcp.sport | 1048 | 0.0% | 100.0% |
| tcp.dport | 1048 | 0.0% | 100.0% |
| tcp.seq | 1048 | 0.0% | 100.0% |
| tcp.ack | 1048 | 100.0% | 100.0% |
| tcp.flags | 1048 | 0.0% | 100.0% |
| tcp.window | 1048 | 34.9% | 100.0% |
| udp.sport | 452 | 0.0% | 100.0% |
| udp.dport | 452 | 0.0% | 100.0% |
| payload | 1471 | 0.3% | 100.0% |
