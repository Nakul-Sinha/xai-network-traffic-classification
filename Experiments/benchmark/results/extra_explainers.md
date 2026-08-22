# Extra explainers (C3 completion): KernelSHAP + LIME on the p=1.0 ByteCNN

Same protocol as `run_audit.py`: split seed 0, sampler seed 1, test subset n=800. CNN test acc 0.9862. Ground truth N(F) recomputed on this run (PacketDO resampling); null control N(tcp.sport) = -0.0013.

## Ground truth N(F) for this cell

| field | N(F) |
|---|---|
| tcp.window | 0.4838 |
| ip.ttl | 0.0025 |
| ip.id | 0.0025 |
| tcp.dport | 0.0 |
| tcp.sport | -0.0013 |
| ip.src | -0.0025 |
| tcp.seq | -0.0025 |
| tcp.flags | -0.0038 |
| payload | -0.005 |
| ip.dst | -0.0063 |

## Audit vs N(F)

| explainer | rho | precision@2 | false-confidence | blind-spot | n explained | runtime (s) | s / 100 samples |
|---|---|---|---|---|---|---|---|
| KernelSHAP | 0.183 | 0.5 | 0.0 | 0.0 | 150 | 16.18 | 10.78 |
| LIME | 0.311 | 0.5 | 0.667 | 0.0 | 150 | 1.56 | 1.04 |

## Field attributions (aggregated from per-byte scores)

**KernelSHAP** (named = >= 0.2 * max): ['tcp.window']

| field | score |
|---|---|
| tcp.window | 0.194589 |
| ip.ttl | 0.00877583 |
| tcp.seq | 0.00443444 |
| payload | 0.00188488 |
| ip.dst | 0.00165552 |
| ip.src | 0.00163443 |
| tcp.sport | 0.00125813 |
| ip.id | 0.000398834 |
| tcp.flags | 0.000228832 |
| tcp.dport | 0 |

**LIME** (named = >= 0.2 * max): ['ip.dst', 'tcp.dport', 'tcp.window']

| field | score |
|---|---|
| tcp.window | 0.0910501 |
| ip.dst | 0.0323901 |
| tcp.dport | 0.0184343 |
| ip.src | 0.00964934 |
| ip.ttl | 0.00960824 |
| tcp.sport | 0.00795285 |
| tcp.seq | 0.00726171 |
| ip.id | 0.00722766 |
| payload | 0.00708233 |
| tcp.flags | 0.00616601 |

## Why LIME's false confidence is 0.667 (verified mechanism)

LIME falsely names `ip.dst` and `tcp.dport` (both N ~ 0). Both fields are (partly or fully)
CONSTANT in the dataset: `tcp.dport` = 443 (bytes 22-23 = 0x01BB, std 0) and the first two
`ip.dst` bytes = 192.168 (std 0). `LimeTabularExplainer` samples perturbations as
`N(0,1) * scaler.scale_ + mean`, and sklearn's `StandardScaler` maps zero-variance features to
`scale_ = 1.0` (verified on this data: `scale_[22] = scale_[23] = 1.0`), i.e. unit-variance
noise in normalized byte space (+/- 255 in raw byte units) on fields that never vary in real
traffic. LIME therefore probes the model with protocol-impossible dport/dst values, the CNN's
arbitrary out-of-manifold response correlates with that noise, and the local surrogate reads it
as importance. This is the paper's core claim -- scoring explanations on protocol-invalid
inputs fabricates evidence -- occurring *inside* an explainer's own perturbation kernel, not
just inside a faithfulness metric. KernelSHAP avoids it here because its perturbation replaces
coalitions with background-data values (real observed bytes), which keeps constant fields
constant.

## Runtime note (line-rate-cost angle)

KernelSHAP: 10.78 s / 100 packets; LIME: 1.04 s / 100 packets, on an RTX 4050 laptop GPU with a batched predict_proba. For comparison, gradient methods in `run_audit.py` explain 400 samples in well under a second. Perturbation explainers are orders of magnitude away from line rate even on an 80-byte toy window.

