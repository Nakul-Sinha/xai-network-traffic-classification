# Audit summary: explainers vs interventional ground truth N(F)

Planted artifacts ip.ttl + tcp.window (effective corr 0.5+0.5p); genuine weak signal payload length. Null-intervention control field: tcp.sport (should have N~0).

## ByteCNN

### Ground truth
| p | test acc | N(ttl) | N(win) | N(payload) | N(null=sport) | R(M) |
|---|---|---|---|---|---|---|
| 0.5 | 0.7762 | 0.0025 | 0.2575 | 0.0 | 0.0 | 1 |
| 0.7 | 0.8413 | 0.005 | 0.34 | 0.0063 | 0.0063 | 1 |
| 0.9 | 0.9513 | -0.0012 | 0.4463 | 0.0013 | 0.0 | 1 |
| 1.0 | 0.9988 | 0.005 | 0.49 | 0.0025 | 0.0025 | 1 |

### Explainer audit (rho / false-confidence / blind-spot)
**DeepSHAP**
| p | rho | precision@2 | false-confidence | blind-spot |
|---|---|---|---|---|
| 0.5 | 0.679 | 0.5 | 0.0 | 0.0 |
| 0.7 | 0.58 | 0.5 | 0.0 | 0.0 |
| 0.9 | 0.293 | 0.5 | 0.0 | 0.0 |
| 1.0 | 0.42 | 0.5 | 0.0 | 0.0 |

**IntegratedGradients**
| p | rho | precision@2 | false-confidence | blind-spot |
|---|---|---|---|---|
| 0.5 | 0.562 | 0.5 | 0.667 | 0.0 |
| 0.7 | 0.333 | 0.5 | 0.5 | 0.0 |
| 0.9 | 0.206 | 0.5 | 0.5 | 0.0 |
| 1.0 | 0.383 | 0.5 | 0.5 | 0.0 |

**Occlusion**
| p | rho | precision@2 | false-confidence | blind-spot |
|---|---|---|---|---|
| 0.5 | 0.281 | 0.5 | 0.0 | 0.0 |
| 0.7 | 0.669 | 0.5 | 0.0 | 0.0 |
| 0.9 | -0.278 | 0.5 | 0.0 | 0.0 |
| 1.0 | 0.518 | 0.5 | 0.0 | 0.0 |

**Saliency**
| p | rho | precision@2 | false-confidence | blind-spot |
|---|---|---|---|---|
| 0.5 | 0.601 | 0.5 | 0.75 | 0.0 |
| 0.7 | -0.049 | 0.5 | 0.667 | 0.0 |
| 0.9 | 0.056 | 0.5 | 0.667 | 0.0 |
| 1.0 | 0.191 | 0.5 | 0.667 | 0.0 |

## RFFlow

### Ground truth
| p | test acc | N(ttl) | N(win) | N(payload) | N(null=sport) | R(M) |
|---|---|---|---|---|---|---|
| 0.5 | 0.835 | 0.1075 | 0.1 | 0.1262 | -0.0025 | 1 |
| 0.7 | 0.91 | 0.13 | 0.1113 | 0.065 | 0.0 | 1 |
| 0.9 | 0.9712 | 0.105 | 0.1537 | 0.025 | -0.0013 | 1 |
| 1.0 | 1.0 | 0.4587 | 0.0125 | 0.0 | 0.0 | 1 |

### Explainer audit (rho / false-confidence / blind-spot)
**Impurity**
| p | rho | precision@2 | false-confidence | blind-spot |
|---|---|---|---|---|
| 0.5 | 0.72 | 1.0 | 0.625 | 0.333 |
| 0.7 | 0.529 | 1.0 | 0.0 | 0.333 |
| 0.9 | 0.865 | 1.0 | 0.0 | 0.0 |
| 1.0 | 0.701 | 0.5 | 0.5 | 0.0 |

**TreeSHAP**
| p | rho | precision@2 | false-confidence | blind-spot |
|---|---|---|---|---|
| 0.5 | 0.713 | 1.0 | 0.0 | 0.333 |
| 0.7 | 0.705 | 1.0 | 0.0 | 0.333 |
| 0.9 | 0.656 | 1.0 | 0.333 | 0.0 |
| 1.0 | 0.701 | 0.5 | 0.5 | 0.0 |

