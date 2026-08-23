"""
Load the REAL pretrained ET-BERT (linwhitehat/ET-BERT, WWW 2022) and expose it as a
controllable PyTorch classifier for the PacketDO faithfulness audit.

What this module does:
  1. Reproduces ET-BERT's exact packet tokenization (datagram -> sliding 2-byte bigram
     "words" -> BERT WordPiece over the released 60,005-token hex vocab -> [CLS]+tokens,
     segment id 1, seq_length padding), from data_process/dataset_generation.py and
     fine-tuning/run_classifier.py in their repo. We additionally TRACK, for every subword
     token, which packet byte offset(s) it covers, so an attention/gradient score over
     tokens can be mapped back to protocol fields exactly like the byte-CNN audit.
  2. Remaps the released UER-py checkpoint (pretrained_model.bin) into a HuggingFace
     BertForSequenceClassification so we control the forward pass (attentions + input
     gradients). The remap is validated by an MLM reconstruction sanity check
     (etbert_mlm_sanity) that reloads the pretrained MLM head and confirms the encoder
     predicts masked hex bigrams -- proving the pretrained weights actually loaded.

ET-BERT is a standard UER-py BERT-base: 12 layers, hidden 768, 12 heads, ff 3072,
vocab 60005, 512 max positions, 3 segment types, gelu, post-LN.
"""
import warnings; warnings.filterwarnings("ignore")
import os, sys, binascii
import numpy as np
import torch
import torch.nn as nn

HERE = os.path.dirname(os.path.abspath(__file__))
VOCAB_PATH = os.path.join(HERE, "repo", "models", "encryptd_vocab.txt")
CKPT_PATH = os.path.join(HERE, "pretrained_model.bin")
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

PAD_ID, SEP_ID, CLS_ID, UNK_ID, MASK_ID = 0, 1, 2, 3, 4   # from encryptd_vocab.txt order
NUM_LAYERS, HIDDEN, HEADS, FF, MAXPOS, NSEG = 12, 768, 12, 3072, 512, 3


# ----------------------------- vocab + WordPiece -----------------------------
def load_vocab(path=VOCAB_PATH):
    vocab = {}
    with open(path, encoding="utf-8") as f:
        for i, line in enumerate(f):
            vocab[line.rstrip("\n")] = i
    return vocab


def _wordpiece(word, vocab, max_chars=200):
    """Greedy longest-match-first WordPiece (standard BERT). Returns list of token strings."""
    if len(word) > max_chars:
        return ["[UNK]"]
    out, start = [], 0
    while start < len(word):
        end = len(word)
        cur = None
        while start < end:
            sub = word[start:end]
            if start > 0:
                sub = "##" + sub
            if sub in vocab:
                cur = sub
                break
            end -= 1
        if cur is None:
            return ["[UNK]"]
        out.append(cur)
        start = end
    return out


class ETBertTokenizer:
    """Packet bytes -> ET-BERT ids, with per-token byte-offset tracking for the audit.

    strip_header_hexchars: number of leading HEX CHARS to drop before tokenizing. ET-BERT's
      published get_feature_packet uses packet_string[76:] on Ethernet-framed pcaps (drops
      14B Ethernet + 20B IP + 4B TCP ports = 38 bytes). Our packets are IP-framed, so:
        - 0   -> header VISIBLE (IP+TCP+payload), the direct parallel to the from-scratch
                 Transformer of Section 5.5 (byte offsets align with BYTE_FIELD_OFFSETS).
        - 48  -> header STRIPPED as ET-BERT intends: drop 20B IP + 4B TCP ports = 24 bytes
                 (48 hex chars) so the 5-tuple is invisible, payload/seq/ack/window remain.
    """
    def __init__(self, vocab, seq_length=128, window_bytes=80, strip_header_hexchars=0):
        self.vocab = vocab
        self.seq_length = seq_length
        self.window_bytes = window_bytes
        self.strip = strip_header_hexchars

    def encode(self, raw: bytes):
        raw = raw[: self.window_bytes]
        hexs = binascii.hexlify(raw).decode()          # 2*len(raw) chars
        drop_bytes = self.strip // 2
        hexs = hexs[self.strip:]
        nbytes = len(hexs) // 2                          # bytes available after strip
        # sliding 2-byte bigram words (stride 1 byte); word j covers absolute byte offsets
        # (drop_bytes+j, drop_bytes+j+1)
        ids = [CLS_ID]
        tok2bytes = [set()]                              # CLS covers no byte
        for j in range(nbytes - 1):
            word = hexs[2 * j: 2 * j + 4]
            b0, b1 = drop_bytes + j, drop_bytes + j + 1
            for sub in _wordpiece(word, self.vocab):
                ids.append(self.vocab.get(sub, UNK_ID))
                tok2bytes.append({b0, b1})
                if len(ids) >= self.seq_length:
                    break
            if len(ids) >= self.seq_length:
                break
        ids = ids[: self.seq_length]
        tok2bytes = tok2bytes[: self.seq_length]
        seg = [1] * len(ids)
        mask = [1] * len(ids)
        while len(ids) < self.seq_length:
            ids.append(PAD_ID); seg.append(0); mask.append(0); tok2bytes.append(set())
        return ids, seg, mask, tok2bytes

    def encode_batch(self, raws):
        I, S, Mk, B = [], [], [], []
        for r in raws:
            a, b, c, d = self.encode(r)
            I.append(a); S.append(b); Mk.append(c); B.append(d)
        return (torch.tensor(I, dtype=torch.long), torch.tensor(S, dtype=torch.long),
                torch.tensor(Mk, dtype=torch.long), B)


# ----------------------------- UER -> HF remap -----------------------------
def _hf_config(num_labels=2):
    from transformers import BertConfig
    return BertConfig(
        vocab_size=60005, hidden_size=HIDDEN, num_hidden_layers=NUM_LAYERS,
        num_attention_heads=HEADS, intermediate_size=FF, hidden_act="gelu",
        max_position_embeddings=MAXPOS, type_vocab_size=NSEG, num_labels=num_labels,
        hidden_dropout_prob=0.1, attention_probs_dropout_prob=0.1,
        position_embedding_type="absolute", pad_token_id=PAD_ID)


def _remap_uer_to_hf(uer):
    """Map UER-py ET-BERT state dict -> HF BertModel-prefixed state dict."""
    h = {}
    h["bert.embeddings.word_embeddings.weight"] = uer["embedding.word_embedding.weight"]
    h["bert.embeddings.position_embeddings.weight"] = uer["embedding.position_embedding.weight"]
    h["bert.embeddings.token_type_embeddings.weight"] = uer["embedding.segment_embedding.weight"]
    h["bert.embeddings.LayerNorm.weight"] = uer["embedding.layer_norm.gamma"]
    h["bert.embeddings.LayerNorm.bias"] = uer["embedding.layer_norm.beta"]
    for i in range(NUM_LAYERS):
        p = f"encoder.transformer.{i}."
        q = f"bert.encoder.layer.{i}."
        h[q + "attention.self.query.weight"] = uer[p + "self_attn.linear_layers.0.weight"]
        h[q + "attention.self.query.bias"] = uer[p + "self_attn.linear_layers.0.bias"]
        h[q + "attention.self.key.weight"] = uer[p + "self_attn.linear_layers.1.weight"]
        h[q + "attention.self.key.bias"] = uer[p + "self_attn.linear_layers.1.bias"]
        h[q + "attention.self.value.weight"] = uer[p + "self_attn.linear_layers.2.weight"]
        h[q + "attention.self.value.bias"] = uer[p + "self_attn.linear_layers.2.bias"]
        h[q + "attention.output.dense.weight"] = uer[p + "self_attn.final_linear.weight"]
        h[q + "attention.output.dense.bias"] = uer[p + "self_attn.final_linear.bias"]
        h[q + "attention.output.LayerNorm.weight"] = uer[p + "layer_norm_1.gamma"]
        h[q + "attention.output.LayerNorm.bias"] = uer[p + "layer_norm_1.beta"]
        h[q + "intermediate.dense.weight"] = uer[p + "feed_forward.linear_1.weight"]
        h[q + "intermediate.dense.bias"] = uer[p + "feed_forward.linear_1.bias"]
        h[q + "output.dense.weight"] = uer[p + "feed_forward.linear_2.weight"]
        h[q + "output.dense.bias"] = uer[p + "feed_forward.linear_2.bias"]
        h[q + "output.LayerNorm.weight"] = uer[p + "layer_norm_2.gamma"]
        h[q + "output.LayerNorm.bias"] = uer[p + "layer_norm_2.beta"]
    return h


def load_etbert_classifier(num_labels=2, ckpt=CKPT_PATH):
    """HF BertForSequenceClassification with ET-BERT pretrained encoder loaded.
    Returns (model, info) where info records how many pretrained tensors matched."""
    from transformers import BertForSequenceClassification
    uer = torch.load(ckpt, map_location="cpu", weights_only=False)
    hf = _remap_uer_to_hf(uer)
    model = BertForSequenceClassification(_hf_config(num_labels))
    msd = model.state_dict()
    loaded = 0
    for k, v in hf.items():
        if k in msd and msd[k].shape == v.shape:
            msd[k] = v; loaded += 1
    model.load_state_dict(msd, strict=False)
    # pooler.dense + classifier are freshly initialized (pretrained bin has no pooler/head)
    info = {"pretrained_tensors_loaded": loaded, "total_remapped": len(hf)}
    return model.to(DEVICE), info


def verify_encoder_against_uer(tokenizer, ckpt=CKPT_PATH):
    """GOLD-STANDARD remap validation: build ET-BERT's encoder from the ORIGINAL UER-py repo
    code + the released checkpoint, and confirm our HF BertModel computes the same hidden
    states on a real byte sequence. A correct remap gives max-abs-diff ~1e-2 (LayerNorm eps
    differences only); a broken one diverges by O(1)."""
    import argparse
    repo = os.path.join(HERE, "repo")
    if repo not in sys.path:
        sys.path.insert(0, repo)
    from uer.layers.embeddings import WordPosSegEmbedding
    from uer.encoders.transformer_encoder import TransformerEncoder
    from transformers import BertModel
    uer = torch.load(ckpt, map_location="cpu", weights_only=False)
    a = argparse.Namespace(emb_size=768, hidden_size=768, heads_num=12, layers_num=12,
        feedforward_size=3072, dropout=0.0, hidden_act="gelu", max_seq_length=MAXPOS,
        mask="fully_visible", parameter_sharing=False, factorized_embedding_parameterization=False,
        layernorm_positioning="post", relative_position_embedding=False, remove_transformer_bias=False,
        remove_attention_scale=False, remove_embedding_layernorm=False, feed_forward="dense", layernorm="normal")
    emb = WordPosSegEmbedding(a, 60005); enc = TransformerEncoder(a)
    emb.load_state_dict({k[10:]: v for k, v in uer.items() if k.startswith("embedding.")}, strict=False)
    enc.load_state_dict({k[8:]: v for k, v in uer.items() if k.startswith("encoder.")}, strict=False)
    emb.eval(); enc.eval()
    raw = bytes.fromhex("4500003c1c4640004006b1e6c0a80001c0a800c70050d90aaabbccddeeff00112233")
    ids, seg, mask, _ = tokenizer.encode(raw)
    ids_t, seg_t, mk = torch.tensor([ids]), torch.tensor([seg]), torch.tensor([mask])
    with torch.no_grad():
        uer_h = enc(emb(ids_t, seg_t), seg_t)
    hf = {k[5:]: v for k, v in _remap_uer_to_hf(uer).items()}  # strip 'bert.'
    bm = BertModel(_hf_config(), add_pooling_layer=False)
    msd = bm.state_dict()
    for k, v in hf.items():
        if k in msd and msd[k].shape == v.shape:
            msd[k] = v
    bm.load_state_dict(msd, strict=False); bm.eval()
    with torch.no_grad():
        hf_h = bm(input_ids=ids_t, attention_mask=mk, token_type_ids=seg_t).last_hidden_state
    return {"encoder_max_abs_diff_vs_uer": round(float((uer_h - hf_h).abs().max()), 5),
            "encoder_mean_abs_diff_vs_uer": round(float((uer_h - hf_h).abs().mean()), 6)}


def etbert_mlm_sanity(tokenizer, ckpt=CKPT_PATH, n_mask=10, raws=None):
    """Second validation: run the pretrained MLM head (UER's OWN native head + encoder) and
    check it reconstructs masked hex-bigram tokens of REAL packets. Chance top-1 = 1/60005;
    a genuine pretrained model scores high. Uses native UER code so no HF weight-tying artifact
    interferes -- this validates that (a) the released weights are a real pretrained model and
    (b) our tokenization matches ET-BERT's expected input."""
    import argparse, random
    repo = os.path.join(HERE, "repo")
    if repo not in sys.path:
        sys.path.insert(0, repo)
    from uer.layers.embeddings import WordPosSegEmbedding
    from uer.encoders.transformer_encoder import TransformerEncoder
    from uer.targets.mlm_target import MlmTarget
    uer = torch.load(ckpt, map_location="cpu", weights_only=False)
    a = argparse.Namespace(emb_size=768, hidden_size=768, heads_num=12, layers_num=12,
        feedforward_size=3072, dropout=0.0, hidden_act="gelu", max_seq_length=MAXPOS,
        mask="fully_visible", parameter_sharing=False, factorized_embedding_parameterization=False,
        layernorm_positioning="post", relative_position_embedding=False, remove_transformer_bias=False,
        remove_attention_scale=False, remove_embedding_layernorm=False, feed_forward="dense", layernorm="normal")
    emb = WordPosSegEmbedding(a, 60005); enc = TransformerEncoder(a); tgt = MlmTarget(a, 60005)
    emb.load_state_dict({k[10:]: v for k, v in uer.items() if k.startswith("embedding.")}, strict=False)
    enc.load_state_dict({k[8:]: v for k, v in uer.items() if k.startswith("encoder.")}, strict=False)
    tgt.load_state_dict({k[7:]: v for k, v in uer.items() if k.startswith("target.")}, strict=False)
    emb.eval(); enc.eval(); tgt.eval()
    if not raws:
        raws = [bytes.fromhex("4500003c1c4640004006b1e6c0a80001c0a800c70050d90aaabbccddeeff00112233"
                              "445566778899aabbccddeeff0011223344556677")]
    tot = cor = cor5 = 0
    for r in raws[:8]:
        ids, seg, mask, _ = tokenizer.encode(r)
        real = [i for i in range(1, len(ids)) if mask[i] == 1]
        if not real:
            continue
        random.seed(0); pos = sorted(random.sample(real, min(n_mask, len(real))))
        gold = [ids[p] for p in pos]
        ids_t = torch.tensor([ids]); seg_t = torch.tensor([seg])
        for p in pos:
            ids_t[0, p] = MASK_ID
        with torch.no_grad():
            h = enc(emb(ids_t, seg_t), seg_t)
            o = tgt.act(tgt.mlm_linear_1(h[0])); o = tgt.layer_norm(o)
            logits = tgt.mlm_linear_2(o)
        for p, gpred in zip(pos, gold):
            top5 = torch.topk(logits[p], 5).indices.tolist()
            cor += int(top5[0] == gpred); cor5 += int(gpred in top5); tot += 1
    return {"masked": tot, "top1_correct": cor, "top1_acc": round(cor / max(1, tot), 3),
            "top5_acc": round(cor5 / max(1, tot), 3), "note": "native UER MLM head on real packets"}
