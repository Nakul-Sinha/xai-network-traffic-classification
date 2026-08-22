"""
Protocol-validity checks for a packet byte-string.

A counterfactual produced by an intervention is "protocol-valid" iff a real host could
have emitted it. We decompose validity into independent, checkable predicates so E1 can
report WHICH predicate each operator violates, not just a pass/fail rate.

Predicates (IP/TCP or IP/UDP, no Ethernet unless link_ether=True):
  parses          : bytes re-parse into an IP packet without a scapy error layer
  ip_checksum     : IP header checksum equals the checksum of the reparsed header
  l4_checksum     : TCP/UDP checksum equals the recomputed checksum
  ip_len          : IP total-length field equals the actual byte length
  ihl             : IP IHL matches the actual IP header length
  tcp_dataofs     : TCP data offset matches the actual TCP header length (TCP only)
  udp_len         : UDP length field equals actual (UDP only)

valid = AND of all applicable predicates.

Implementation: scapy recomputes checksums/lengths when a packet is rebuilt from its
fields. So to check a field like ip.chksum, we compare the value carried in the raw
bytes against the value scapy computes for the same packet. If they differ, the carried
checksum is wrong -> invalid.
"""
from scapy.all import IP, TCP, UDP, Ether, Raw


def _carried_and_computed(raw, link_ether=False):
    base = Ether if link_ether else IP
    pkt = base(raw)
    ip = pkt[IP] if IP in pkt else None
    out = {"pkt": pkt, "ip": ip}
    return out


def check(raw, link_ether=False):
    """Return dict of predicate -> bool, plus 'valid' = all applicable True."""
    res = {}
    try:
        base = Ether if link_ether else IP
        pkt = base(raw)
        res["parses"] = True
    except Exception:
        return {"parses": False, "valid": False}

    # scapy marks unparseable tails with a Raw/Padding after a malformed header;
    # a hard parse error is rare, so also check there is an IP layer.
    if IP not in pkt:
        res["parses"] = False
        res["valid"] = False
        return res

    ip = pkt[IP]

    # --- IP total length ---
    actual_ip_bytes = len(bytes(ip))
    res["ip_len"] = (ip.len == actual_ip_bytes)

    # --- IHL ---
    res["ihl"] = (ip.ihl == (len(ip) - len(ip.payload)) // 4) if ip.ihl else False

    # --- IP checksum: recompute by clearing and rebuilding ---
    ip_copy = ip.copy()
    carried_ip_ck = ip.chksum
    del ip_copy.chksum
    computed_ip_ck = IP(bytes(ip_copy)).chksum
    res["ip_checksum"] = (carried_ip_ck == computed_ip_ck)

    # --- L4 ---
    if TCP in pkt:
        tcp = pkt[TCP]
        carried = tcp.chksum
        t2 = pkt.copy()
        del t2[TCP].chksum
        computed = IP(bytes(t2[IP])) [TCP].chksum
        res["l4_checksum"] = (carried == computed)
        # data offset
        actual_tcp_hdr = len(bytes(tcp)) - len(bytes(tcp.payload))
        res["tcp_dataofs"] = (tcp.dataofs * 4 == actual_tcp_hdr)
    elif UDP in pkt:
        udp = pkt[UDP]
        carried = udp.chksum
        u2 = pkt.copy()
        del u2[UDP].chksum
        computed = IP(bytes(u2[IP])) [UDP].chksum
        # UDP checksum 0 means "not computed" and is legal
        res["l4_checksum"] = (carried == computed or carried == 0)
        res["udp_len"] = (udp.len == len(bytes(udp)))
    # else: no L4, skip

    applicable = [v for k, v in res.items() if k != "parses"]
    res["valid"] = res["parses"] and all(applicable)
    return res


def valid(raw, link_ether=False):
    return check(raw, link_ether).get("valid", False)
