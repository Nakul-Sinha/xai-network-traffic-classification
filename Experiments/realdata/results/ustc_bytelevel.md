# Phase D (2nd corpus): byte-level PacketDO on real USTC-TFC2016 packets

Dataset: USTC-TFC2016 (Wang et al., ICOIN 2017). Task: Miuref vs Geodo (malware-family classification). Ethernet-framed captures normalised to IP. n/class = 5000/5000; ByteCNN test acc = 0.8638.

## E1-real: operator validity on REAL packets (with options)
- baseline valid: 100.0%
- zero-mask macro validity: **15.5%**
- PacketDO macro validity: **100.0%**
- zero-mask violations: {'ip_checksum': 48643, 'l4_checksum': 72133}
- PacketDO violations: {}

## Interventional necessity N(F) (real packets)
| field | N(F) |
|---|---|
| ip.dst | 0.13 |
| tcp.window | 0.0938 |
| ip.ttl | 0.0262 |
| ip.id | 0.01 |
| ip.src | 0.01 |
| tcp.dport | 0.0038 |
| tcp.sport | 0.0025 |
| tcp.seq | 0.0025 |
| tcp.flags | 0.0 |
| payload | 0.0 |

R(M) = 2; sets = [['ip.dst'], ['tcp.window']]

## Explainer audit vs N(F)
| method | rho | precision@k | false-confidence | blind-spot |
|---|---|---|---|---|
| IntegratedGradients | 0.734 | 0.5 | 0.667 | 0.5 |
| Saliency | 0.471 | 0.5 | 0.778 | 0.5 |
| Occlusion | 0.423 | 1.0 | 0.0 | 0.0 |
