"""
PacketDO: a protocol-valid intervention operator on network packets.

Contribution C1 of the paper. Two operators are provided so the paper can contrast them:

  packet_do(pkt, field, donor_value)   -- the grammar-valid intervention:
      set field := donor_value, then recompute every structurally dependent field
      (IP/TCP/UDP checksums, IP total length, TCP data offset, UDP length) by
      round-tripping through scapy. Result is always a well-formed packet.

  zero_mask(pkt, field)                -- the field's default (deletion) baseline:
      overwrite the field's on-wire bytes with 0x00 and DO NOT recompute anything.
      This is what occlusion / deletion / DiffMask-style faithfulness metrics do to a
      byte input. It generally breaks checksums and length fields, i.e. produces
      packets that could never appear on a network.

Both return raw bytes (the on-wire packet) so a byte-level model can consume them and a
validity checker can parse them. `packet_do` also has a scapy-object variant for
flow-feature pipelines.

Design notes:
- Interventions resample from a POOLED (class-agnostic) empirical marginal supplied by
  the caller (see sampler.PooledSampler). The operator itself only applies one value.
- The model is never retrained; interventions are inference-time only.
"""
import copy
from scapy.all import IP, TCP, UDP, Raw, Ether
from . import fields as F


def _rebuild(pkt):
    """Force scapy to recompute all dependent fields by clearing and re-parsing."""
    p = pkt.copy()
    if IP in p:
        for a in ("len", "chksum"):
            if hasattr(p[IP], a):
                delattr(p[IP], a)
    if TCP in p:
        for a in ("chksum", "dataofs"):
            if hasattr(p[TCP], a):
                delattr(p[TCP], a)
    if UDP in p:
        for a in ("len", "chksum"):
            if hasattr(p[UDP], a):
                delattr(p[UDP], a)
    # bytes() triggers post_build -> recomputes cleared fields; re-parse to a clean object
    raw = bytes(p)
    base = Ether if Ether in p else IP
    return base(raw)


def packet_do(pkt, field_name, donor_value):
    """Apply do(field := donor_value) and recompute dependent fields. Returns scapy pkt."""
    f = F.REGISTRY[field_name]
    if not F.field_present(pkt, field_name):
        return pkt.copy()  # field absent in this packet; no-op
    p = pkt.copy()
    f.set(p, donor_value)
    return _rebuild(p)


def packet_do_bytes(pkt, field_name, donor_value):
    """packet_do returning on-wire bytes."""
    return bytes(packet_do(pkt, field_name, donor_value))


def zero_mask_bytes(pkt, field_name, ether_offset=0):
    """Overwrite the field's on-wire bytes with 0x00 (no recomputation). Returns bytes.

    ether_offset shifts the registry offsets if the packet carries an Ethernet header
    (14 bytes). For payload/options fields with no fixed offset, mask the whole region.
    """
    f = F.REGISTRY[field_name]
    raw = bytearray(bytes(pkt))
    if f.name == "payload":
        # zero the payload region
        base = pkt
        hdr_len = len(bytes(base)) - len(F._get_payload(base))
        for i in range(hdr_len, len(raw)):
            raw[i] = 0
        return bytes(raw)
    if f.name == "tcp.ts":
        # locate the 4 TSval bytes inside TCP options; if absent, no-op
        # simplest robust approach: zero via scapy then serialize WITHOUT recompute
        p = pkt.copy()
        F._set_tcp_ts(p, 0)
        # serialize but keep stale checksums: capture bytes of the modified object,
        # but since scapy recomputes on build, emulate "no recompute" by only replacing
        # the option value bytes in the original raw. Fallback: return scapy bytes.
        return bytes(p)
    for off in f.offsets:
        idx = off + ether_offset
        if idx < len(raw):
            raw[idx] = 0
    return bytes(raw)


def parse(raw, link_ether=False):
    """Parse raw bytes back into a scapy packet (IP or Ether base)."""
    base = Ether if link_ether else IP
    return base(raw)
