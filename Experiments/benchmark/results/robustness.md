# Multi-seed robustness of the synthetic-benchmark audit (seeds [0, 1, 2, 3, 4])

Every cell is mean +/- sample sd (ddof=1) across seeds. Each seed reshuffles the train/test split, the model initialization/training, and the PacketDO resampler stream; the generated datasets (one per p) are fixed. rho uses only finite values (it is NaN when an explainer's field scores have zero variance); when fewer than 5 seeds contribute, (n=...) is shown.

## ByteCNN

### Ground truth (interventional necessity, PacketDO)

| p | test acc | N(ip.ttl) | N(tcp.window) | N(null=tcp.sport) |
|---|---|---|---|---|
| 0.5 | 0.769 +/- 0.007 | 0.001 +/- 0.001 | 0.273 +/- 0.011 | -0.004 +/- 0.007 |
| 0.7 | 0.843 +/- 0.020 | 0.004 +/- 0.002 | 0.341 +/- 0.027 | 0.004 +/- 0.005 |
| 0.9 | 0.946 +/- 0.004 | 0.001 +/- 0.002 | 0.454 +/- 0.016 | 0.001 +/- 0.002 |
| 1.0 | 0.995 +/- 0.005 | 0.002 +/- 0.002 | 0.501 +/- 0.020 | 0.000 +/- 0.002 |

### Explainer audit vs N(F)

**DeepSHAP**

| p | false_confidence | blind_spot | rho |
|---|---|---|---|
| 0.5 | 0.233 +/- 0.325 | 0.000 +/- 0.000 | 0.368 +/- 0.305 |
| 0.7 | 0.000 +/- 0.000 | 0.000 +/- 0.000 | 0.517 +/- 0.098 |
| 0.9 | 0.000 +/- 0.000 | 0.000 +/- 0.000 | 0.273 +/- 0.199 |
| 1.0 | 0.000 +/- 0.000 | 0.000 +/- 0.000 | 0.295 +/- 0.225 |

**IntegratedGradients**

| p | false_confidence | blind_spot | rho |
|---|---|---|---|
| 0.5 | 0.700 +/- 0.045 | 0.000 +/- 0.000 | 0.387 +/- 0.253 |
| 0.7 | 0.567 +/- 0.091 | 0.000 +/- 0.000 | 0.497 +/- 0.198 |
| 0.9 | 0.400 +/- 0.224 | 0.000 +/- 0.000 | 0.287 +/- 0.265 |
| 1.0 | 0.300 +/- 0.274 | 0.000 +/- 0.000 | 0.316 +/- 0.091 |

**Occlusion**

| p | false_confidence | blind_spot | rho |
|---|---|---|---|
| 0.5 | 0.000 +/- 0.000 | 0.000 +/- 0.000 | 0.259 +/- 0.362 |
| 0.7 | 0.000 +/- 0.000 | 0.000 +/- 0.000 | 0.466 +/- 0.351 |
| 0.9 | 0.000 +/- 0.000 | 0.000 +/- 0.000 | 0.293 +/- 0.357 |
| 1.0 | 0.000 +/- 0.000 | 0.000 +/- 0.000 | 0.582 +/- 0.081 |

**Saliency**

| p | false_confidence | blind_spot | rho |
|---|---|---|---|
| 0.5 | 0.743 +/- 0.048 | 0.000 +/- 0.000 | 0.454 +/- 0.298 |
| 0.7 | 0.700 +/- 0.045 | 0.000 +/- 0.000 | 0.166 +/- 0.248 |
| 0.9 | 0.717 +/- 0.045 | 0.000 +/- 0.000 | 0.233 +/- 0.171 |
| 1.0 | 0.684 +/- 0.037 | 0.000 +/- 0.000 | 0.112 +/- 0.065 |

## RFFlow

### Ground truth (interventional necessity, PacketDO)

| p | test acc | N(ip.ttl) | N(tcp.window) | N(null=tcp.sport) |
|---|---|---|---|---|
| 0.5 | 0.834 +/- 0.006 | 0.096 +/- 0.009 | 0.090 +/- 0.009 | -0.003 +/- 0.003 |
| 0.7 | 0.914 +/- 0.010 | 0.137 +/- 0.010 | 0.126 +/- 0.011 | -0.000 +/- 0.001 |
| 0.9 | 0.970 +/- 0.009 | 0.131 +/- 0.022 | 0.167 +/- 0.013 | -0.002 +/- 0.003 |
| 1.0 | 1.000 +/- 0.000 | 0.317 +/- 0.182 | 0.184 +/- 0.180 | 0.000 +/- 0.000 |

### Explainer audit vs N(F)

**Impurity**

| p | false_confidence | blind_spot | rho |
|---|---|---|---|
| 0.5 | 0.625 +/- 0.000 | 0.333 +/- 0.000 | 0.585 +/- 0.140 |
| 0.7 | 0.000 +/- 0.000 | 0.333 +/- 0.000 | 0.678 +/- 0.095 |
| 0.9 | 0.133 +/- 0.182 | 0.000 +/- 0.000 | 0.717 +/- 0.107 |
| 1.0 | 0.200 +/- 0.274 | 0.000 +/- 0.000 | 0.665 +/- 0.080 |

**TreeSHAP**

| p | false_confidence | blind_spot | rho |
|---|---|---|---|
| 0.5 | 0.000 +/- 0.000 | 0.333 +/- 0.000 | 0.572 +/- 0.118 |
| 0.7 | 0.000 +/- 0.000 | 0.333 +/- 0.000 | 0.792 +/- 0.067 |
| 0.9 | 0.333 +/- 0.000 | 0.000 +/- 0.000 | 0.632 +/- 0.065 |
| 1.0 | 0.200 +/- 0.274 | 0.000 +/- 0.000 | 0.665 +/- 0.080 |

## Per-seed diagnostics (headline cells)

Per-seed values in seed order [0, 1, 2, 3, 4].

- CNN Saliency FC @ p=1.0: [0.667, 0.667, 0.75, 0.667, 0.667]
- RF TreeSHAP FC @ p=1.0: [0.5, 0.5, 0.0, 0.0, 0.0]
- RF N(ip.ttl) @ p=1.0:   [0.0, 0.4587, 0.3862, 0.3938, 0.3462]
- RF N(tcp.window) @ p=1.0: [0.49, 0.0125, 0.1175, 0.1325, 0.17]
- CNN IntegratedGradients FC @ p=1.0: [0.0, 0.5, 0.5, 0.5, 0.0]
- CNN DeepSHAP FC @ p=0.5: [0.0, 0.0, 0.0, 0.667, 0.5]

Reading these: the RF TreeSHAP FC at p=1.0 is bimodal, and the mode tracks the model's realized reliance seed by seed -- FC=0.5 exactly in the seeds where the RF commits to a single one of the two perfectly-correlated shortcuts (one field's N large, the other's ~0), FC=0 in the seeds where it spreads reliance across both. The CNN commits to tcp.window in every seed (N(ttl)~0 throughout), so its Saliency FC is stable. Two seed-0 claims are revised by the multi-seed pass: IntegratedGradients FC at p=1.0 is not 0 (nonzero in some seeds), and DeepSHAP FC at p=0.5 is not 0 in every seed (clean at p>=0.7 in all seeds).

