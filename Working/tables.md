**Table I. Per-field protocol-validity of counterfactuals: zero-mask vs PacketDO (2000 synthetic packets, seed 0).**

| field | zero-mask valid | PacketDO valid |
|---|---|---|
| ip.ttl | 0.0% | 100.0% |
| ip.tos | 100.0% | 100.0% |
| ip.id | 0.0% | 100.0% |
| ip.flags | 100.0% | 100.0% |
| ip.src | 0.0% | 100.0% |
| ip.dst | 0.0% | 100.0% |
| tcp.sport | 0.0% | 100.0% |
| tcp.dport | 0.0% | 100.0% |
| tcp.seq | 0.0% | 100.0% |
| tcp.ack | 100.0% | 100.0% |
| tcp.flags | 0.0% | 100.0% |
| tcp.window | 35.4% | 100.0% |
| udp.sport | 0.0% | 100.0% |
| udp.dport | 0.0% | 100.0% |
| payload | 0.6% | 100.0% |
| **macro** | **22.4%** | **100.0%** |

**Table II. Explainer false-confidence rate (mean +/- sd over 5 seeds) vs planting strength.**

| method | model | p=0.5 | p=0.7 | p=0.9 | p=1.0 |
|---|---|---|---|---|---|
| Saliency | ByteCNN | 0.74+/-0.05 | 0.70+/-0.05 | 0.72+/-0.05 | 0.68+/-0.04 |
| IntegratedGradients | ByteCNN | 0.70+/-0.05 | 0.57+/-0.09 | 0.40+/-0.22 | 0.30+/-0.27 |
| DeepSHAP | ByteCNN | 0.23+/-0.33 | 0.00+/-0.00 | 0.00+/-0.00 | 0.00+/-0.00 |
| Occlusion | ByteCNN | 0.00+/-0.00 | 0.00+/-0.00 | 0.00+/-0.00 | 0.00+/-0.00 |
| Impurity | RF | 0.62+/-0.00 | 0.00+/-0.00 | 0.13+/-0.18 | 0.20+/-0.27 |
| TreeSHAP | RF | 0.00+/-0.00 | 0.00+/-0.00 | 0.33+/-0.00 | 0.20+/-0.27 |

**Table III. E5: deletion AOPC of each explainer under zero-mask vs PacketDO removal (p=1.0 ByteCNN; PacketDO mean over 5 resampling seeds). Higher AOPC = steeper deletion = nominally more faithful.**

| explainer | zero-mask AOPC | PacketDO AOPC | false-conf (seed 0) |
|---|---|---|---|
| IntegratedGradients | 0.4776 | 0.4882 | 0.0 |
| Saliency | 0.4730 | 0.4875 | 0.667 |
| DeepSHAP | 0.4724 | 0.4872 | 0.0 |
| Occlusion | 0.4629 | 0.4881 | 0.0 |
*Under zero-mask, Occlusion (false-confidence 0) is ranked last; under PacketDO the four are within 0.001 (below resampling noise ~0.006).*

**Table IV. A2 real-data (CIC-IDS2017) destination-port robustness: 4 seeds x default RF (d20/l20) + 2 alt-config runs (d30/l5).**

| run | N(dst) acc-rank /52 | TreeSHAP rank /52 | acc-only FC /10 | Brute-Force recall drop |
|---|---|---|---|---|
| default_seed0 | 1 | 5 | 9 | 0.378 |
| default_seed1 | 1 | 7 | 8 | 0.441 |
| default_seed2 | 1 | 8 | 9 | 0.382 |
| default_seed3 | 1 | 9 | 9 | 0.199 |
| alt_d30l5_seed0 | 1 | 5 | 9 | 0.360 |
| alt_d30l5_seed1 | 1 | 6 | 9 | 0.356 |
*Necessity rank 1/52 in all six runs; TreeSHAP never ranks it better than 5th.*

