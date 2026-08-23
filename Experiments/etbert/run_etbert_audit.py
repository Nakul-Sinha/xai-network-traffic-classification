"""
Task F1: audit the REAL pretrained ET-BERT (linwhitehat/ET-BERT, WWW 2022) against
PacketDO interventional ground truth, mirroring Section 5.5's from-scratch-Transformer study.

Pipeline:
  1. Load real ISCX VPN packets (facebook TCP/443 vs ftps), reusing the exact Section 5.5 loader.
  2. Tokenize each packet with ET-BERT's own datagram bigram + WordPiece scheme over the released
     60,005-token hex vocab, and load the released pretrained encoder (UER-py checkpoint remapped
     into a HuggingFace BertForSequenceClassification; remap verified against the UER model itself).
  3. Fine-tune (head + encoder) a few epochs; report test accuracy.
  4. Measure necessity N(F) by PacketDO on the real packets (same operator, sampler, CANDIDATE_FIELDS
     as every other model in the paper), via an evaluate() closure that runs intervened scapy packets
     through ET-BERT's tokenizer + classifier.
  5. Audit Attention (CLS->token, last layer, mapped back to protocol bytes), gradient Saliency, and
     Integrated Gradients against N(F) with the SAME explainers.audit metrics.

Two input variants (--variant):
  header  : ET-BERT sees IP+TCP+payload bytes (byte offsets align with BYTE_FIELD_OFFSETS). Direct
            apples-to-apples with the Section 5.5 Transformer, which also saw the header.
  payload : ET-BERT's AS-PUBLISHED anonymized input -- get_feature_packet drops the 5-tuple
            (IP addresses + TCP ports) before tokenizing. Tests the model as its authors intended.

Writes results/etbert_audit_<variant>.json + .md and a run log.
"""
import warnings; warnings.filterwarnings("ignore")
import os, sys, json, time, argparse
import numpy as np
import torch
import torch.nn as nn

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "realdata"))
sys.path.insert(0, os.path.join(HERE, ".."))
import etbert_common as EC
from benchmark import groundtruth as GT, explainers as EX
import pcap_bytelevel as PB

DEVICE = EC.DEVICE
SEED = 0
WINDOW = 80  # same 80-byte IP+TCP+payload window as the Section 5.5 byte models


def set_seed(s):
    import random
    random.seed(s); np.random.seed(s); torch.manual_seed(s)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(s)


def pkt_raw(pk):
    """On-wire bytes of the (IP-framed) packet, capped at the audit window."""
    return bytes(pk)[:WINDOW]


class ETBertClf:
    """Fine-tuned ET-BERT classifier + attention/gradient explainers over protocol bytes."""
    def __init__(self, tokenizer, num_labels=2):
        self.tok = tokenizer
        self.model, self.load_info = EC.load_etbert_classifier(num_labels)

    # ---- tokenize a list of raw byte strings into tensors + per-token byte map ----
    def _batch(self, raws):
        return self.tok.encode_batch(raws)

    def fit(self, raws, y, epochs=3, bs=16, lr=2e-5, log=print):
        ids, seg, mask, _ = self._batch(raws)
        y = torch.tensor(np.asarray(y), dtype=torch.long)
        n = len(ids)
        opt = torch.optim.AdamW(self.model.parameters(), lr=lr, weight_decay=1e-2)
        scaler = torch.cuda.amp.GradScaler(enabled=(DEVICE == "cuda"))
        g = torch.Generator().manual_seed(SEED)
        self.model.train()
        for ep in range(epochs):
            perm = torch.randperm(n, generator=g)
            tot, corr, lsum = 0, 0, 0.0
            for i in range(0, n, bs):
                b = perm[i:i + bs]
                ib, sb, mb, yb = ids[b].to(DEVICE), seg[b].to(DEVICE), mask[b].to(DEVICE), y[b].to(DEVICE)
                opt.zero_grad()
                with torch.autocast(device_type="cuda", dtype=torch.float16, enabled=(DEVICE == "cuda")):
                    out = self.model(input_ids=ib, attention_mask=mb, token_type_ids=sb, labels=yb)
                scaler.scale(out.loss).backward()
                scaler.step(opt); scaler.update()
                lsum += float(out.loss) * len(b)
                corr += int((out.logits.argmax(-1) == yb).sum()); tot += len(b)
            log(f"  epoch {ep+1}/{epochs}: loss={lsum/tot:.4f} train_acc={corr/tot:.4f}")
        self.model.eval()

    @torch.no_grad()
    def predict(self, raws, bs=128):
        ids, seg, mask, _ = self._batch(raws)
        self.model.eval(); preds = []
        for i in range(0, len(ids), bs):
            ib, sb, mb = ids[i:i+bs].to(DEVICE), seg[i:i+bs].to(DEVICE), mask[i:i+bs].to(DEVICE)
            with torch.autocast(device_type="cuda", dtype=torch.float16, enabled=(DEVICE == "cuda")):
                lo = self.model(input_ids=ib, attention_mask=mb, token_type_ids=sb).logits
            preds.append(lo.argmax(-1).cpu().numpy())
        return np.concatenate(preds)

    def accuracy(self, raws, y):
        return float((self.predict(raws) == np.asarray(y)).mean())

    # ---- attention-as-explanation: last-layer CLS->token, avg heads, -> per byte ----
    @torch.no_grad()
    def attention_bytes(self, raws, bs=64, limit=400):
        raws = raws[:limit]
        ids, seg, mask, t2b = self._batch(raws)
        self.model.eval()
        per_byte = np.zeros(WINDOW)
        for i in range(0, len(ids), bs):
            ib, sb, mb = ids[i:i+bs].to(DEVICE), seg[i:i+bs].to(DEVICE), mask[i:i+bs].to(DEVICE)
            out = self.model(input_ids=ib, attention_mask=mb, token_type_ids=sb, output_attentions=True)
            att = out.attentions[-1].mean(1)          # [b, L, L] avg over heads
            cls = att[:, 0, :].cpu().numpy()          # [b, L] CLS query -> key tokens
            for r in range(len(ib)):
                bmap = t2b[i + r]
                for p in range(len(bmap)):
                    for byte in bmap[p]:
                        if byte < WINDOW:
                            per_byte[byte] += cls[r, p] / max(1, len(bmap[p]))
        return per_byte

    # ---- gradient attributions on inputs_embeds -> per byte ----
    def _grad_bytes(self, raws, kind="saliency", bs=32, limit=400, ig_steps=20):
        raws = raws[:limit]
        ids, seg, mask, t2b = self._batch(raws)
        self.model.eval()
        per_byte = np.zeros(WINDOW)
        wemb = self.model.bert.embeddings.word_embeddings
        for i in range(0, len(ids), bs):
            ib, sb, mb = ids[i:i+bs].to(DEVICE), seg[i:i+bs].to(DEVICE), mask[i:i+bs].to(DEVICE)
            base_emb = wemb(ib).detach()              # [b, L, H]
            with torch.no_grad():
                pred = self.model(input_ids=ib, attention_mask=mb, token_type_ids=sb).logits.argmax(-1)
            if kind == "saliency":
                emb = base_emb.clone().requires_grad_(True)
                logits = self.model(inputs_embeds=emb, attention_mask=mb, token_type_ids=sb).logits
                sel = logits.gather(1, pred[:, None]).sum()
                grad = torch.autograd.grad(sel, emb)[0]
                tok_imp = grad.norm(dim=-1).detach().cpu().numpy()          # [b, L]
            else:  # integrated gradients from zero-embedding baseline
                total = torch.zeros_like(base_emb)
                for a in np.linspace(1.0 / ig_steps, 1.0, ig_steps):
                    emb = (a * base_emb).clone().requires_grad_(True)
                    logits = self.model(inputs_embeds=emb, attention_mask=mb, token_type_ids=sb).logits
                    sel = logits.gather(1, pred[:, None]).sum()
                    total = total + torch.autograd.grad(sel, emb)[0] / ig_steps
                ig = (base_emb * total).sum(-1)                              # [b, L]
                tok_imp = ig.abs().detach().cpu().numpy()
            for r in range(len(ib)):
                bmap = t2b[i + r]
                for p in range(len(bmap)):
                    for byte in bmap[p]:
                        if byte < WINDOW:
                            per_byte[byte] += tok_imp[r, p] / max(1, len(bmap[p]))
        return per_byte

    def saliency_bytes(self, raws, **kw): return self._grad_bytes(raws, "saliency", **kw)
    def ig_bytes(self, raws, **kw):       return self._grad_bytes(raws, "ig", **kw)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--variant", choices=["header", "payload"], default="header")
    ap.add_argument("--cap", type=int, default=3000, help="packets per class for train/test")
    ap.add_argument("--gt_n", type=int, default=500, help="test packets for N(F)")
    ap.add_argument("--epochs", type=int, default=3)
    ap.add_argument("--bs", type=int, default=16)
    args = ap.parse_args()

    RES = os.path.join(HERE, "results"); os.makedirs(RES, exist_ok=True)
    logf = open(os.path.join(RES, f"etbert_run_{args.variant}.log"), "w", encoding="utf-8")
    def log(*a):
        m = " ".join(str(x) for x in a); print(m, flush=True); logf.write(m + "\n"); logf.flush()

    set_seed(SEED)
    strip = 0 if args.variant == "header" else 48   # 48 hex = drop 20B IP + 4B TCP ports
    log(f"=== ET-BERT audit | variant={args.variant} strip_hexchars={strip} | device={DEVICE} ===")

    log("loading real ISCX packets (facebook TCP/443 vs ftps)...")
    p0 = PB.load_class(PB.CLASSES[0], args.cap)
    p1 = PB.load_class(PB.CLASSES[1], args.cap)
    pkts = p0 + p1
    y = np.array([0] * len(p0) + [1] * len(p1))
    log(f"  facebook={len(p0)} ftps={len(p1)}")

    rng = np.random.default_rng(SEED)
    idx = rng.permutation(len(pkts))
    pkts = [pkts[i] for i in idx]; y = y[idx]
    ntr = int(0.7 * len(pkts))
    tr_pk, tr_y = pkts[:ntr], y[:ntr]
    te_pk, te_y = pkts[ntr:], y[ntr:]

    vocab = EC.load_vocab()
    tokenizer = EC.ETBertTokenizer(vocab, seq_length=128, window_bytes=WINDOW, strip_header_hexchars=strip)

    log("verifying UER->HF remap against the original ET-BERT encoder...")
    ver = EC.verify_encoder_against_uer(tokenizer)
    log(f"  {ver}")
    _mlm_raws = [pkt_raw(p) for p in tr_pk[:8]]
    mlm = EC.etbert_mlm_sanity(tokenizer, n_mask=10, raws=_mlm_raws)
    log(f"  native-UER MLM reconstruction of real hex bigrams: top1_acc={mlm['top1_acc']} "
        f"top5_acc={mlm['top5_acc']} ({mlm['top1_correct']}/{mlm['masked']})")

    log("building + fine-tuning ET-BERT classifier...")
    clf = ETBertClf(tokenizer, num_labels=2)
    log(f"  pretrained encoder tensors loaded: {clf.load_info}")
    tr_raw = [pkt_raw(p) for p in tr_pk]
    t0 = time.time()
    clf.fit(tr_raw, tr_y, epochs=args.epochs, bs=args.bs, log=log)
    log(f"  fine-tune time: {time.time()-t0:.1f}s")

    te_raw = [pkt_raw(p) for p in te_pk]
    acc = round(clf.accuracy(te_raw, te_y), 4)
    log(f"  ET-BERT test accuracy = {acc}")

    # ---- ground truth on a test subset ----
    gt_pk = te_pk[:args.gt_n]; gt_y = te_y[:args.gt_n]
    sampler = GT.make_sampler(pkts, seed=SEED + 1)

    def evaluate(packets, yy):
        return clf.accuracy([pkt_raw(p) for p in packets], yy)

    log(f"necessity N(F) via PacketDO on {len(gt_pk)} real packets...")
    t0 = time.time()
    base, N = GT.necessity(gt_pk, gt_y, evaluate, sampler)
    log(f"  base_acc={base:.4f}  N(F)={ {k: N[k] for k in sorted(N, key=lambda z:-N[z])} }  ({time.time()-t0:.1f}s)")
    try:
        R = GT.redundancy(gt_pk, gt_y, evaluate, sampler)
    except Exception as e:
        R = []; log(f"  redundancy failed: {e}")
    log(f"  R(M)={len(R)} sets={R}")

    log("explainers: Attention (CLS->token), Saliency, IntegratedGradients...")
    att_b = clf.attention_bytes(te_raw)
    sal_b = clf.saliency_bytes(te_raw)
    ig_b = clf.ig_bytes(te_raw)
    expl = {
        "Attention": EX.bytes_to_fields(att_b),
        "Saliency": EX.bytes_to_fields(sal_b),
        "IntegratedGradients": EX.bytes_to_fields(ig_b),
    }
    audit = {name: EX.audit(sc, N) for name, sc in expl.items()}
    for nm, a in audit.items():
        log(f"  {nm}: rho={a['rho']} prec@k={a['precision_at_k']} FC={a['false_confidence']} blind={a['blind_spot']} top_k={a['top_k']}")

    out = {
        "task": "facebook(TCP/443) vs ftps(TCP), real ISCX VPN packets; REAL pretrained ET-BERT (linwhitehat/ET-BERT, WWW2022)",
        "variant": args.variant,
        "input_note": ("ET-BERT sees IP+TCP+payload header bytes (apples-to-apples with the Section 5.5 Transformer)"
                       if args.variant == "header" else
                       "ET-BERT as published: 5-tuple (IP addresses + TCP ports) stripped before tokenizing"),
        "model": "ET-BERT BERT-base (12L/768/12H, vocab 60005), pretrained encoder remapped UER->HF, fine-tuned",
        "remap_verification": ver, "mlm_sanity": mlm, "encoder_load_info": clf.load_info,
        "n_per_class": [len(p0), len(p1)], "n_train": len(tr_pk), "n_test": len(te_pk),
        "n_test_gt": len(gt_pk), "test_acc": acc, "base_acc_gt": round(base, 4),
        "N": N, "R": len(R), "R_sets": R, "audit": audit, "attributions_fields": expl,
        "window_bytes": WINDOW, "seq_length": 128, "epochs": args.epochs, "seed": SEED,
    }
    jpath = os.path.join(RES, f"etbert_audit_{args.variant}.json")
    json.dump(out, open(jpath, "w"), indent=2)
    log(f"saved {jpath}")

    # markdown
    Ns = sorted(N.items(), key=lambda kv: -kv[1])
    L = [f"# ET-BERT audit ({args.variant} input) on real ISCX packets\n",
         f"REAL pretrained ET-BERT (linwhitehat/ET-BERT, WWW 2022), BERT-base, fine-tuned on "
         f"facebook (TCP/443) vs ftps; test accuracy = **{acc}**.",
         f"Remap verified vs original UER model (max abs hidden diff = {ver['encoder_max_abs_diff_vs_uer']}).\n",
         f"Input: {out['input_note']}\n",
         "## Interventional necessity N(F) (PacketDO on real packets)",
         "| field | N(F) |", "|---|---|"]
    for f, v in Ns:
        L.append(f"| {f} | {v} |")
    L += ["", f"R(M) = {len(R)}; sets = {R}", "",
          "## Explainer audit vs N(F)",
          "| method | rho | precision@k | false-confidence | blind-spot |", "|---|---|---|---|---|"]
    for nm, a in audit.items():
        L.append(f"| {nm} | {a['rho']} | {a['precision_at_k']} | {a['false_confidence']} | {a['blind_spot']} |")
    open(os.path.join(RES, f"etbert_audit_{args.variant}.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")
    log(f"saved results/etbert_audit_{args.variant}.md")
    logf.close()


if __name__ == "__main__":
    main()
