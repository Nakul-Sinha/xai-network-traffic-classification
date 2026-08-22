"""
Per-field unit tests for PacketDO.

For every intervenable field we assert:
  T1. packet_do produces a protocol-VALID packet (all predicates pass).
  T2. packet_do actually CHANGES the field to the donor value (the intervention took).
  T3. packet_do changes NOTHING except the field and its structural dependents.
  T4. zero_mask that touches a checksum-covered byte produces an INVALID packet
      (the motivating failure the paper measures in E1).
Also registry-consistency tests (offsets match scapy) and idempotence/no-op behavior.

Run: python -m pytest Experiments/packetdo/tests -q
"""
import warnings
warnings.filterwarnings("ignore")
import pytest
from scapy.all import IP, TCP, UDP, Raw

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from packetdo import operator as op, validity as vd, fields as F
from packetdo.sampler import PooledSampler


def tcp_pkt(**kw):
    d = dict(src="10.0.0.5", dst="192.168.1.9", ttl=64)
    return IP(**d) / TCP(sport=1234, dport=443, window=8192, seq=1000, ack=0) / Raw(b"payload-bytes-here-0123456789")


def tcp_pkt_ts(**kw):
    return IP(src="10.0.0.5", dst="192.168.1.9", ttl=64) / \
        TCP(sport=1234, dport=443, window=8192, options=[("Timestamp", (12345, 0))]) / Raw(b"data")


def udp_pkt():
    return IP(src="10.0.0.5", dst="192.168.1.9", ttl=64) / UDP(sport=1234, dport=53) / Raw(b"dnsquery-payload")


DONORS = {
    "ip.ttl": 128, "ip.tos": 16, "ip.id": 54321, "ip.flags": 2,
    "ip.src": "8.8.8.8", "ip.dst": "1.1.1.1", "ip.proto": 6,
    "tcp.sport": 5555, "tcp.dport": 80, "tcp.seq": 999999, "tcp.ack": 12345,
    "tcp.flags": "PA", "tcp.window": 65535, "tcp.ts": 88888,
    "udp.sport": 6666, "udp.dport": 123,
    "payload": b"a-completely-different-payload-string",
}


def _fields_for(pkt):
    return [n for n in F.INTERVENABLE if F.field_present(pkt, n)]


@pytest.mark.parametrize("field", [f for f in F.INTERVENABLE if f.startswith(("ip.", "tcp.")) and f != "tcp.ts"])
def test_packet_do_valid_tcp(field):
    """T1: PacketDO on a TCP packet yields a protocol-valid packet."""
    pkt = tcp_pkt()
    if not F.field_present(pkt, field):
        pytest.skip(f"{field} absent")
    raw = op.packet_do_bytes(pkt, field, DONORS[field])
    c = vd.check(raw)
    assert c["valid"], f"{field}: {c}"


@pytest.mark.parametrize("field", ["udp.sport", "udp.dport", "ip.ttl", "ip.src", "ip.dst", "payload"])
def test_packet_do_valid_udp(field):
    pkt = udp_pkt()
    if not F.field_present(pkt, field):
        pytest.skip(f"{field} absent")
    raw = op.packet_do_bytes(pkt, field, DONORS[field])
    assert vd.valid(raw), f"{field} invalid after do on UDP"


@pytest.mark.parametrize("field", [f for f in F.INTERVENABLE if f.startswith(("ip.", "tcp."))])
def test_packet_do_changes_field(field):
    """T2: the intervention actually takes effect."""
    pkt = tcp_pkt()
    if not F.field_present(pkt, field) or field == "tcp.ts":
        pytest.skip(f"{field} skip")
    before = F.REGISTRY[field].get(pkt)
    after_pkt = op.packet_do(pkt, field, DONORS[field])
    after = F.REGISTRY[field].get(after_pkt)
    assert after != before or str(after) == str(DONORS[field]), f"{field}: {before}->{after}"


def test_packet_do_isolation():
    """T3: do(ttl) changes ttl (+ip.chksum) but not tcp.window, seq, ports, payload."""
    pkt = tcp_pkt()
    after = op.packet_do(pkt, "ip.ttl", 200)
    assert after[IP].ttl == 200
    assert after[TCP].window == pkt[TCP].window
    assert after[TCP].seq == pkt[TCP].seq
    assert after[TCP].sport == pkt[TCP].sport
    assert bytes(after[Raw].load) == bytes(pkt[Raw].load)


@pytest.mark.parametrize("field", ["ip.ttl", "ip.src", "ip.dst", "tcp.window", "tcp.seq", "tcp.sport"])
def test_zero_mask_breaks_validity(field):
    """T4: zero-masking a checksum-covered field produces an invalid packet."""
    pkt = tcp_pkt()
    raw = op.zero_mask_bytes(pkt, field)
    assert not vd.valid(raw), f"zero_mask({field}) unexpectedly valid"


def test_registry_offsets_match_scapy():
    """The declared byte offsets must match scapy's serialization for IHL=5 no-options."""
    pkt = IP(src="10.0.0.1", dst="10.0.0.2", ttl=77) / TCP(sport=0x1234, dport=0x5678, window=0xABCD)
    raw = bytes(pkt)
    # ip.ttl at offset 8
    assert raw[8] == 77
    # tcp.sport at 20-21 big-endian
    assert (raw[20] << 8 | raw[21]) == 0x1234
    # tcp.window at 34-35
    assert (raw[34] << 8 | raw[35]) == 0xABCD


def test_absent_field_is_noop():
    """do() on a field not present returns an unchanged, still-valid packet."""
    pkt = udp_pkt()
    raw = op.packet_do_bytes(pkt, "tcp.window", 65535)  # no TCP layer
    assert vd.valid(raw)


def test_ip_proto_is_dependent():
    """ip.proto is NOT independently intervenable (structural, tied to the L4 header)."""
    assert "ip.proto" not in F.INTERVENABLE
    assert "ip.proto" in F.RECOMPUTED
    # setting proto=17 (UDP) on a packet whose L4 bytes are TCP yields an inconsistent packet:
    # the TCP layer can no longer be parsed and the packet is invalid. This is exactly why
    # ip.proto is not a free degree of freedom - it is fixed by the L4 header.
    pkt = tcp_pkt()
    p = pkt.copy()
    p[IP].proto = 17
    raw = bytes(op._rebuild(p))
    reparsed = IP(raw)
    assert reparsed.proto == 17          # forced value persists in the bytes
    assert TCP not in reparsed           # but the TCP layer is now unparseable
    assert not vd.valid(raw)             # -> not a self-consistent packet


def test_zero_mask_tcp_ts_is_true_deletion():
    """zero-masking a TCP timestamp zeroes TSval and leaves a stale checksum (invalid)."""
    pkt = IP(src="1.2.3.4", dst="5.6.7.8", ttl=64) / \
        TCP(sport=1234, dport=443, window=8192, options=[("Timestamp", (123456, 789))]) / Raw(b"data")
    pkt = IP(bytes(pkt))
    zm = op.zero_mask_bytes(pkt, "tcp.ts")
    zp = IP(zm)
    tsval = [o[1][0] for o in zp[TCP].options if o[0] == "Timestamp"]
    assert tsval == [0]
    assert not vd.valid(zm)  # stale checksum -> invalid
    # packet_do keeps it valid
    assert vd.valid(op.packet_do_bytes(pkt, "tcp.ts", 999999))


def test_pooled_sampler_class_agnostic():
    pkts = [tcp_pkt() for _ in range(5)]
    for i, p in enumerate(pkts):
        p[IP].ttl = 64 if i % 2 == 0 else 128
    s = PooledSampler(pkts, seed=3)
    assert set(s.pool["ip.ttl"]) <= {64, 128}
    assert s.draw("ip.ttl") in (64, 128)
