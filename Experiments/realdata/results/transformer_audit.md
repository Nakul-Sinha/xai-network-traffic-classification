# Transformer audit on real ISCX packets (attention-based byte model)

Byte Transformer (2 layers, 4 heads, d=64, CLS token) on facebook vs ftps; test acc = 1.0.

## Interventional necessity N(F)
| field | N(F) |
|---|---|
| ip.src | 0.2137 |
| ip.dst | 0.195 |
| ip.ttl | 0.0 |
| ip.id | 0.0 |
| tcp.sport | 0.0 |
| tcp.dport | 0.0 |

## Explainer audit vs N(F) (Attention = CLS->byte attention weights)
| method | rho | precision@k | false-confidence | blind-spot |
|---|---|---|---|---|
| IntegratedGradients | 0.683 | 1.0 | 0.0 | 0.0 |
| Saliency | 0.701 | 1.0 | 0.333 | 0.0 |
| Occlusion | 0.975 | 1.0 | 0.0 | 0.0 |
| Attention | 0.588 | 0.5 | 0.8 | 0.5 |
