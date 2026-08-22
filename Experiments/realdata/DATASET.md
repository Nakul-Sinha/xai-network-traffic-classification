# DATASET.md - CIC-IDS2017 flow-CSV acquisition (Parcel A1)

## Source

- **Kaggle dataset:** `ericanacletoribeiro/cicids2017-cleaned-and-preprocessed`
  https://www.kaggle.com/datasets/ericanacletoribeiro/cicids2017-cleaned-and-preprocessed
  (zip 210,143,955 bytes -> single file `cicids2017_cleaned.csv`, 717 MB extracted;
  raw zip deleted after extraction per disk discipline)
- **Underlying dataset:** Sharafaldin et al., "Toward Generating a New Intrusion Detection
  Dataset and Intrusion Traffic Characterization" (CIC-IDS2017), ICISSP 2018.
  https://www.unb.ca/cic/datasets/ids-2017.html
- **Staging location (NOT in repo):** session scratchpad
  `C:\Users\nakul\AppData\Local\Temp\claude\C--Users-nakul-OneDrive-Desktop-Academics-cn\ee30e724-9e44-4268-a3e6-2eabd7e384d0\scratchpad\cicids2017\cicids2017_cleaned.csv`
  Loader: `load_cicids.py` (override location with env var `CICIDS_DATA_DIR`).

This Kaggle re-release is the *original* (uncorrected) CICFlowMeter output with publisher
pre-cleaning: duplicate rows and NaN/Inf rows already removed, the 8 original CIC-IDS2017
attack labels grouped into 6 attack families + Normal Traffic, and 52 of the original ~78
CICFlowMeter columns retained. Our own hygiene pass (`load_cicids.py`: strip column
whitespace, replace +/-Inf with NaN, drop NaN rows) dropped **0 additional rows**,
confirming the publisher's cleaning. For E4 (orig-vs-corrected comparison) the
Engelen-corrected counterpart is downloaded separately from
https://intrusion-detection.distrinet-research.be/WTMC2021/ (not part of this parcel).

## Size and schema

| quantity | value |
|---|---|
| flows (rows after hygiene) | **2,520,751** |
| features (numeric, label excluded) | **52** |
| classes | **7** |
| label column | `Attack Type` |

## Class distribution

| class | flows | share |
|---|---|---|
| Normal Traffic | 2,095,057 | 83.11% |
| DoS | 193,745 | 7.69% |
| DDoS | 128,014 | 5.08% |
| Port Scanning | 90,694 | 3.60% |
| Brute Force | 9,150 | 0.36% |
| Web Attacks | 2,143 | 0.09% |
| Bots | 1,948 | 0.08% |

## Documented-artifact columns (Track B ground truth, feeds E4)

Measured on the loaded data (real numbers, this release):

### 1. `Destination Port` - destination-port shortcut (present)

Attack classes are almost perfectly separable by port alone:

| class | top ports (share of class) |
|---|---|
| DoS | 80 (100.0%) |
| DDoS | 80 (100.0%) |
| Web Attacks | 80 (100.0%) |
| Brute Force | 21 (64.8%), 22 (35.2%) |
| Bots | 8080 (64.0%) |
| Normal Traffic | 53 (41.9%), 443 (22.4%), 80 (10.4%) |
| Port Scanning | spread (scan sweeps many ports; top port <0.5%) |

A classifier can shortcut most attack classes on this single column; an explainer that
fails to surface it on those classes has a blind spot, and one that names it for
Port Scanning-style spread classes may show false confidence. This is the primary
documented artifact for E4.

### 2. Flow-construction artifacts (Engelen et al., SPW/WTMC 2021) - present

Engelen et al. showed CICFlowMeter mis-terminates TCP flows, producing 25.9% spurious
"TCP-appendix" flows (post-FIN/RST fragments counted as new flows). The appendix-flow
signature lands in these columns, all present in this release:

- **`Init_Win_bytes_forward` / `Init_Win_bytes_backward`** - value `-1` means no
  handshake was captured inside the flow (mid-stream fragment). Measured:
  `Init_Win_bytes_forward == -1` in **43.5% of Normal Traffic** flows vs **~0.0% of every
  attack class** (max 0.01%, Port Scanning). The artifact is therefore strongly
  class-correlated: "-1 => benign" is a flow-construction shortcut, not traffic semantics.
- **`Fwd Header Length`** - degenerate on 1-2-packet fragments. Median per class:
  Port Scanning 40 (two bare 20-byte TCP headers), Normal 64, DDoS 80, Bots 92,
  Web Attacks 104, DoS 200, Brute Force 296.
- **`min_seg_size_forward`** - bimodal: 20 (bare TCP header, no options) x 1,296,937
  flows vs 32 (header + timestamp option) x 1,028,633; TTL-adjacent OS fingerprint of
  the attacker/victim stacks rather than behaviour.

### 3. TTL 64/128 (attacker Kali=64 vs victim Windows=128) - NOT representable here

CICFlowMeter emits no TTL-derived feature; the TTL artifact is packet-level only and
requires the PCAPs / byte-level pipeline (ORG-A byte-level parcel, ISCX/USTC track).
`load_cicids.py` records this as an explicit empty entry in `ARTIFACT_COLUMNS["ttl"]`
so downstream audit code documents rather than silently skips it.

## API

```python
from load_cicids import get_flows, artifact_columns_present
X, y, feature_names = get_flows()   # X: 2,520,751 x 52 DataFrame; y: str labels
artifact_columns_present(feature_names)
# {'dest_port': ['Destination Port'],
#  'flow_construction': ['Fwd Header Length', 'min_seg_size_forward',
#                        'Init_Win_bytes_forward', 'Init_Win_bytes_backward'],
#  'ttl': []}
```

Hygiene order inside `get_flows()`: read all `*.csv` in the data dir -> concat ->
`str.strip()` column names -> `+/-Inf -> NaN` -> `dropna(axis=0)` -> split label ->
drop non-numeric residuals (none in this release).
