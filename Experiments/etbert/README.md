# Pretrained ET-BERT audit (Phase F1, manuscript Section 5.5)

Audits the REAL pretrained ET-BERT (linwhitehat/ET-BERT, WWW 2022) against PacketDO interventional
necessity, on the same real ISCX task as the from-scratch Transformer (facebook TCP/443 vs ftps).

## What is here (tracked)
- `etbert_common.py`  loads ET-BERT: clones the upstream repo, remaps the UER pretrained encoder to a
  HuggingFace BERT (remap verified against the original UER model to max hidden-state diff 0.012), and
  exposes attention + gradient hooks.
- `run_etbert_audit.py`  fine-tunes the classifier, computes N(F) via PacketDO on the real packets, and
  runs the attention/saliency/integrated-gradients audit. `--variant header` feeds the 80-byte
  IP+TCP+payload header window (used in the paper, apples-to-apples with the Transformer);
  `--variant payload` strips the 5-tuple (ET-BERT's native regime; future work).
- `results/etbert_audit_header.json` / `.md`  the audited result.

## Not tracked (git-ignored)
- `pretrained_model.bin` (~683 MB ET-BERT weights) and `repo/` (the cloned upstream). Fetch with the
  upstream instructions: clone https://github.com/linwhitehat/ET-BERT and download its released
  pretrained model (Google Drive link in their README) to `pretrained_model.bin`.

## Result (header input, 3 epochs, seed 0, N(F) on 800 real packets)
- Test accuracy 1.0; model commits to the server identity (N(ip.dst)=0.068, N(ip.src)=0.055).
- R(M)=3: three disjoint sufficient sets {ip.src}, {ip.dst}, {tcp.sport, tcp.dport}.
- Audit false-confidence: Attention 0.714, Saliency 0.800, Integrated Gradients 0.600 (all precision@k
  1.0, blind-spot 0.0): the explainers rank the address shortcut at the top yet fabricate importance on
  fields the model provably does not use.

## Run
    python run_etbert_audit.py --variant header
