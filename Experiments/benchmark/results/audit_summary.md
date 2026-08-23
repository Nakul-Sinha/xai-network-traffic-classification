# Audit summary: explainers vs interventional ground truth N(F)

Planted artifacts ip.ttl + tcp.window (effective corr 0.5+0.5p); genuine weak signal payload length. Null-intervention control field: tcp.sport (should have N~0).

## ByteCNN

### Ground truth
| p | test acc | N(ttl) | N(win) | N(payload) | N(null=sport) | R(M) |
|---|---|---|---|---|---|---|
| 0.5 | 0.7612 | 0.0 | 0.2687 | 0.0062 | 0.0025 | 1 |
| 0.7 | 0.8462 | 0.0025 | 0.3438 | 0.0037 | 0.0062 | 1 |
| 0.9 | 0.9437 | 0.0025 | 0.4363 | 0.0175 | 0.0025 | 1 |
| 1.0 | 0.9862 | 0.0025 | 0.4838 | -0.005 | -0.0013 | 1 |

### Explainer audit (rho / false-confidence / blind-spot)
**DeepSHAP**
| p | rho | precision@2 | false-confidence | blind-spot |
|---|---|---|---|---|
| 0.5 | 0.596 | 0.5 | 0.0 | 0.0 |
| 0.7 | 0.439 | 0.5 | 0.0 | 0.0 |
| 0.9 | 0.415 | 0.5 | 0.0 | 0.0 |
| 1.0 | 0.445 | 0.5 | 0.0 | 0.0 |

**IntegratedGradients**
| p | rho | precision@2 | false-confidence | blind-spot |
|---|---|---|---|---|
| 0.5 | 0.238 | 0.5 | 0.75 | 0.0 |
| 0.7 | 0.561 | 0.5 | 0.667 | 0.0 |
| 0.9 | 0.616 | 0.5 | 0.5 | 0.0 |
| 1.0 | 0.226 | 0.5 | 0.0 | 0.0 |

**Occlusion**
| p | rho | precision@2 | false-confidence | blind-spot |
|---|---|---|---|---|
| 0.5 | 0.688 | 0.5 | 0.0 | 0.0 |
| 0.7 | 0.178 | 0.5 | 0.0 | 0.0 |
| 0.9 | 0.195 | 0.5 | 0.0 | 0.0 |
| 1.0 | 0.715 | 0.5 | 0.0 | 0.0 |

**Saliency**
| p | rho | precision@2 | false-confidence | blind-spot |
|---|---|---|---|---|
| 0.5 | 0.082 | 0.5 | 0.8 | 0.0 |
| 0.7 | 0.11 | 0.5 | 0.75 | 0.0 |
| 0.9 | 0.36 | 0.5 | 0.75 | 0.0 |
| 1.0 | 0.043 | 0.5 | 0.667 | 0.0 |

## RFFlow

### Ground truth
| p | test acc | N(ttl) | N(win) | N(payload) | N(null=sport) | R(M) |
|---|---|---|---|---|---|---|
| 0.5 | 0.8237 | 0.0837 | 0.0762 | 0.1075 | -0.0025 | 1 |
| 0.7 | 0.915 | 0.1225 | 0.1275 | 0.0625 | -0.0012 | 1 |
| 0.9 | 0.97 | 0.1212 | 0.1713 | 0.0262 | 0.0 | 1 |
| 1.0 | 1.0 | 0.0 | 0.49 | 0.0 | 0.0 | 1 |

### Explainer audit (rho / false-confidence / blind-spot)
**Impurity**
| p | rho | precision@2 | false-confidence | blind-spot |
|---|---|---|---|---|
| 0.5 | 0.45 | 1.0 | 0.625 | 0.333 |
| 0.7 | 0.77 | 1.0 | 0.0 | 0.333 |
| 0.9 | 0.61 | 1.0 | 0.333 | 0.0 |
| 1.0 | 0.522 | 0.5 | 0.5 | 0.0 |

**TreeSHAP**
| p | rho | precision@2 | false-confidence | blind-spot |
|---|---|---|---|---|
| 0.5 | 0.444 | 1.0 | 0.0 | 0.333 |
| 0.7 | 0.879 | 1.0 | 0.0 | 0.333 |
| 0.9 | 0.61 | 1.0 | 0.333 | 0.0 |
| 1.0 | 0.522 | 0.5 | 0.5 | 0.0 |

