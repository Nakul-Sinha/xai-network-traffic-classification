"""
Protocol field registry.

Each Field describes one intervenable protocol field: how to read it from a scapy
packet, how to write it, and (for byte-level models) which byte offsets it occupies in
the on-wire header. This registry is the "protocol grammar" that makes an intervention
well-defined: PacketDO resamples a field's *value* from the pooled empirical marginal,
then lets scapy recompute every field that structurally depends on it.

Offsets are for the canonical Ethernet-less IP/TCP or IP/UDP layout (IHL=5, no IP
options). Callers that feed byte windows to a model must pass the same layout; the
offset map is validated against scapy at import time in tests.
"""
from dataclasses import dataclass, field as dc_field
from typing import Callable, List, Optional
from scapy.all import IP, TCP, UDP, Raw

# Standard header offsets (bytes) for IP(IHL=5) / TCP(dataofs>=5) with no Ethernet.
IP_BASE = 0
TCP_BASE = 20  # only valid when IHL == 5


@dataclass
class Field:
    name: str                       # canonical name, e.g. "ip.ttl"
    layer: type                     # scapy layer class
    attr: str                       # scapy attribute name
    offsets: List[int]              # byte offsets in the standard layout (informational)
    kind: str                       # "categorical" | "numeric" | "address" | "bytes"
    dependent: bool = False         # True if changing OTHER fields forces this to change
    getter: Optional[Callable] = None
    setter: Optional[Callable] = None

    def get(self, pkt):
        if self.getter:
            return self.getter(pkt)
        return getattr(pkt[self.layer], self.attr)

    def set(self, pkt, value):
        if self.setter:
            self.setter(pkt, value)
        else:
            setattr(pkt[self.layer], self.attr, value)


def _get_tcp_ts(pkt):
    """TCP timestamp option value (TSval) or None."""
    if TCP not in pkt:
        return None
    for opt in pkt[TCP].options:
        if opt[0] == "Timestamp":
            return opt[1][0]
    return None


def _set_tcp_ts(pkt, value):
    if TCP not in pkt or value is None:
        return
    opts = []
    found = False
    for opt in pkt[TCP].options:
        if opt[0] == "Timestamp":
            opts.append(("Timestamp", (int(value), opt[1][1])))
            found = True
        else:
            opts.append(opt)
    if not found:
        opts.append(("Timestamp", (int(value), 0)))
    pkt[TCP].options = opts


def _get_payload(pkt):
    return bytes(pkt[Raw].load) if Raw in pkt else b""


def _set_payload(pkt, value):
    if Raw in pkt:
        pkt[Raw].load = bytes(value)


# The registry. Fields the paper intervenes on, grouped by layer.
# "dependent" fields (checksums, lengths, offsets) are NEVER resampled directly;
# they are recomputed by PacketDO. They are listed so validity checks can target them.
REGISTRY = {
    # --- IP header ---
    "ip.ttl":    Field("ip.ttl",    IP, "ttl",   [8],            "numeric"),
    "ip.tos":    Field("ip.tos",    IP, "tos",   [1],            "categorical"),
    "ip.id":     Field("ip.id",     IP, "id",    [4, 5],         "numeric"),
    "ip.flags":  Field("ip.flags",  IP, "flags", [6],            "categorical"),
    "ip.src":    Field("ip.src",    IP, "src",   [12, 13, 14, 15], "address"),
    "ip.dst":    Field("ip.dst",    IP, "dst",   [16, 17, 18, 19], "address"),
    # ip.proto is NOT independently intervenable: its value is determined by the L4
    # header that follows (proto=6 <=> TCP, 17 <=> UDP). Resampling it while keeping the
    # L4 bytes produces a self-inconsistent packet, exactly like a stale checksum. It is
    # therefore a structural/dependent field, not a free degree of freedom.
    "ip.proto":  Field("ip.proto",  IP, "proto", [9],            "categorical", dependent=True),
    # dependent (recomputed, not resampled)
    "ip.len":    Field("ip.len",    IP, "len",   [2, 3],   "numeric", dependent=True),
    "ip.chksum": Field("ip.chksum", IP, "chksum",[10, 11], "numeric", dependent=True),

    # --- TCP header ---
    "tcp.sport":  Field("tcp.sport",  TCP, "sport",  [20, 21],        "numeric"),
    "tcp.dport":  Field("tcp.dport",  TCP, "dport",  [22, 23],        "categorical"),
    "tcp.seq":    Field("tcp.seq",    TCP, "seq",    [24, 25, 26, 27],"numeric"),
    "tcp.ack":    Field("tcp.ack",    TCP, "ack",    [28, 29, 30, 31],"numeric"),
    "tcp.flags":  Field("tcp.flags",  TCP, "flags",  [33],            "categorical"),
    "tcp.window": Field("tcp.window", TCP, "window", [34, 35],        "numeric"),
    "tcp.ts":     Field("tcp.ts",     TCP, "options", [], "numeric",
                        getter=_get_tcp_ts, setter=_set_tcp_ts),
    # dependent
    "tcp.dataofs": Field("tcp.dataofs", TCP, "dataofs", [32], "numeric", dependent=True),
    "tcp.chksum":  Field("tcp.chksum",  TCP, "chksum",  [36, 37], "numeric", dependent=True),

    # --- UDP header ---
    "udp.sport":  Field("udp.sport", UDP, "sport", [20, 21], "numeric"),
    "udp.dport":  Field("udp.dport", UDP, "dport", [22, 23], "categorical"),
    "udp.len":    Field("udp.len",   UDP, "len",   [24, 25], "numeric", dependent=True),
    "udp.chksum": Field("udp.chksum",UDP, "chksum",[26, 27], "numeric", dependent=True),

    # --- payload ---
    "payload": Field("payload", Raw, "load", [], "bytes",
                     getter=_get_payload, setter=_set_payload),
}

# Fields eligible for intervention (exclude dependent/recomputed ones).
INTERVENABLE = [name for name, f in REGISTRY.items() if not f.dependent]

# Fields that PacketDO must recompute after any intervention, in dependency order.
RECOMPUTED = [name for name, f in REGISTRY.items() if f.dependent]


def field_present(pkt, name):
    f = REGISTRY[name]
    if f.layer is Raw:
        return Raw in pkt
    if f.name == "tcp.ts":
        return _get_tcp_ts(pkt) is not None
    return f.layer in pkt
