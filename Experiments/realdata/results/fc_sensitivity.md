# Real-data false-confidence: threshold sensitivity (top-10 SHAP features)

Accuracy-only FC = # of top-10 SHAP features with N_acc < eps_acc.
Dual FC = also requires N_f1 < eps_f1.

## Accuracy-only vs dual (eps_f1 = 0.005), swept over eps_acc
| eps_acc | FC (acc-only) /10 | FC (dual) /10 |
|---|---|---|
| 0.0005 | 8 | 0 |
| 0.001 | 9 | 0 |
| 0.002 | 9 | 0 |
| 0.005 | 10 | 0 |
| 0.01 | 10 | 0 |
| 0.02 | 10 | 0 |
| 0.05 | 10 | 0 |

## Dual FC vs eps_f1 (eps_acc fixed at 0.002)
| eps_f1 | FC (dual) /10 |
|---|---|
| 0.001 | 0 |
| 0.002 | 0 |
| 0.005 | 0 |
| 0.01 | 3 |
| 0.02 | 9 |
| 0.05 | 9 |

## Top-10 SHAP features and their necessity
| feature | N_acc | N_f1 |
|---|---|---|
| Bwd Packet Length Std | 0.00064 | 0.00660 |
| Bwd Packet Length Mean | 0.00036 | 0.00881 |
| Packet Length Variance | 0.00022 | 0.01279 |
| Packet Length Std | 0.00024 | 0.01383 |
| Destination Port | 0.00421 | 0.04841 |
| Packet Length Mean | 0.00021 | 0.01294 |
| Fwd Packet Length Max | 0.00019 | 0.01091 |
| Bwd Packet Length Max | 0.00025 | 0.00542 |
| Average Packet Size | 0.00032 | 0.01956 |
| Total Length of Fwd Packets | 0.00035 | 0.01231 |
