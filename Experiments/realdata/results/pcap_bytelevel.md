# Phase D: byte-level PacketDO on real ISCX VPN packets

Task: facebook (TCP/443) vs ftps (TCP/high-ports). n/class = 5000/5000; ByteCNN test acc = 0.9788.

## E1-real: operator validity on REAL packets (with options)
- baseline valid: 100.0%
- zero-mask macro validity: **6.2%**
- PacketDO macro validity: **100.0%**
- zero-mask violations: {'ip_checksum': 51550, 'l4_checksum': 96118}
- PacketDO violations: {}

## Interventional necessity N(F) (real packets)
| field | N(F) |
|---|---|
| ip.dst | 0.25 |
| ip.src | 0.1625 |
| payload | 0.0175 |
| tcp.sport | 0.005 |
| tcp.seq | 0.0038 |
| tcp.window | 0.0025 |
| ip.ttl | 0.0012 |
| tcp.dport | 0.0012 |
| tcp.flags | 0.0 |
| ip.id | -0.0012 |

R(M) = 1; sets = [['ip.dst', 'ip.src']]

## Explainer audit vs N(F)
| method | rho | precision@k | false-confidence | blind-spot |
|---|---|---|---|---|
| IntegratedGradients | 0.389 | 0.5 | 0.714 | 0.5 |
| Saliency | 0.195 | 0.5 | 0.778 | 0.5 |
| Occlusion | 0.485 | 1.0 | 0.333 | 0.0 |
