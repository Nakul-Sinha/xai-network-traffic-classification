# USTC-TFC2016 byte-level PCAP dataset (Phase D, second real corpus)

The second byte-level experiment (`ustc_bytelevel.py`, manuscript Section 5.5) runs on real captured
packets from **USTC-TFC2016** (Wang et al., "Malware traffic classification using convolutional neural
network for representation learning", ICOIN 2017). It is an independent corpus from the ISCX VPN set
used by `pcap_bytelevel.py`: real malware/benign captures rather than encrypted VPN application flows.

## Fetch (Kaggle mirror used here)

Kaggle ref: `mdmirazulhasan/ustc-tfc2016` (a mirror of the USTC-TFC2016 corpus). The full corpus is
~2 GB; we stage only the two malware captures used for the task (~45 MB total), downloaded per-file:

    export KAGGLE_CONFIG_DIR=/c/Users/nakul/AppData/Roaming/SPB_Data/.kaggle
    D=Experiments/realdata/ustc
    kaggle datasets download mdmirazulhasan/ustc-tfc2016 -f "Malware/Miuref.pcap" -p $D
    kaggle datasets download mdmirazulhasan/ustc-tfc2016 -f "Malware/Geodo.pcap"  -p $D

(Single-file Kaggle downloads arrive already unzipped as `Miuref.pcap` / `Geodo.pcap`. If a `.zip`
arrives instead, `unzip -o $D/*.zip -d $D && rm $D/*.zip`.)

## Task and packet selection

Two-class malware-family task:

- class 0: `Miuref.pcap`  (Miuref / Boaxxe click-fraud trojan; HTTP/TCP with real payloads)
- class 1: `Geodo.pcap`   (Geodo / Emotet banking trojan; TCP C2 beaconing)

5,000 TCP/IP packets per class are taken (first-N per file). The USTC captures are **Ethernet-framed**;
each packet is normalised to a clean scapy IP object with `IP(bytes(pk[IP]))`, which strips the
Ethernet header and preserves the captured bytes and checksums, yielding the canonical IP20+TCP20
layout the byte-window and field-offset map assume. All selected packets have IHL=5 and carry valid
IP/TCP checksums at baseline (100% baseline validity); TCP options are present (data offset 6-8),
so they exercise PacketDO on option-laden headers just as the ISCX subset does.

## Why these two files (and not the benign apps)

USTC-TFC2016's **benign** application captures (Gmail, Outlook, ...) are IP-anonymised: source/
destination addresses were rewritten (to `1.1.x.x` / `1.2.x.x` prefixes) without recomputing the
checksums, so their baseline protocol validity is 0% and the leading address octet becomes a trivial
anonymisation artefact. Using them would break the "real packets, real checksums" premise of the
byte-level study and plant a fake shortcut. `Miuref` and `Geodo` are raw, un-anonymised captures with
intact checksums, so they give a clean, honest 2-class task.

## Not committed

The pcap directory (`Experiments/realdata/ustc/`) is git-ignored (see repo `.gitignore`; `*.pcap` is
ignored globally as well). Only the derived results (`results/ustc_bytelevel.json`,
`results/ustc_bytelevel.md`), the driver, and this doc are tracked.

## Run

    python ustc_bytelevel.py   # E1-real validity + ByteCNN + audit; writes results/ustc_bytelevel.*
