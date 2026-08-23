# Byte-level PCAP dataset (Phase D)

The byte-level experiment (`pcap_bytelevel.py`, manuscript Section 5.5) runs on real captured packets
from the ISCX VPN-nonVPN 2016 corpus (Draper-Gil et al., ICISSP 2016). We use a 326 MB subset staged
from Kaggle; the full corpus is available from the University of New Brunswick.

## Fetch (Kaggle mirror used here)

    kaggle datasets download -d peyushgedela/vpn-pcaps-iscx --unzip -p Experiments/realdata/pcap/

This yields raw-IP-framed pcaps named `vpn_<app>_<activity>.pcap`. The experiment uses:

- class 0: `vpn_facebook_audio2.pcap`, `vpn_facebook_chat1a.pcap`, `vpn_facebook_chat1b.pcap`
- class 1: `vpn_ftps_A.pcap`, `vpn_ftps_B.pcap`

5,000 TCP/IP packets per class are taken (first-N per file). Packets are re-parsed with scapy so their
captured bytes (and checksums) are preserved. The captures are raw-IP framed (first byte 0x45), and
every packet carries TCP options (data offset 8), which is why they exercise PacketDO on option-laden
headers that the synthetic population did not contain.

## Not committed

The pcap directory (`Experiments/realdata/pcap/`, ~400 MB) is git-ignored. Only the derived results
(`results/pcap_bytelevel.json`, `results/pcap_bytelevel.md`) and the driver are tracked.

## Run

    python pcap_bytelevel.py     # E1-real validity + ByteCNN + audit; writes results/pcap_bytelevel.*
