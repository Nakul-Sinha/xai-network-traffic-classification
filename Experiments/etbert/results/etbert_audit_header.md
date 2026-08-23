# ET-BERT audit (header input) on real ISCX packets

REAL pretrained ET-BERT (linwhitehat/ET-BERT, WWW 2022), BERT-base, fine-tuned on facebook (TCP/443) vs ftps; test accuracy = **1.0**.
Remap verified vs original UER model (max abs hidden diff = 0.01245).

Input: ET-BERT sees IP+TCP+payload header bytes (apples-to-apples with the Section 5.5 Transformer)

## Interventional necessity N(F) (PacketDO on real packets)
| field | N(F) |
|---|---|
| ip.dst | 0.0675 |
| ip.src | 0.055 |
| ip.ttl | 0.0 |
| ip.id | 0.0 |
| tcp.sport | 0.0 |
| tcp.dport | 0.0 |
| tcp.window | 0.0 |
| tcp.seq | 0.0 |
| tcp.flags | 0.0 |
| payload | 0.0 |

R(M) = 3; sets = [['ip.src'], ['ip.dst'], ['tcp.dport', 'tcp.sport']]

## Explainer audit vs N(F)
| method | rho | precision@k | false-confidence | blind-spot |
|---|---|---|---|---|
| Attention | 0.701 | 1.0 | 0.714 | 0.0 |
| Saliency | 0.701 | 1.0 | 0.8 | 0.0 |
| IntegratedGradients | 0.683 | 1.0 | 0.6 | 0.0 |
