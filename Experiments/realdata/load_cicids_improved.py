"""load_cicids_improved.py - Parcel A3: load + harmonize the *improved* (corrected)
CICIDS2017 flow CSVs for the E4 corrected-vs-original comparison.

Provenance chain:
  - Engelen, Troia, Joosen, "Troubleshooting an Intrusion Detection Dataset:
    the CICIDS2017 Case Study", SPW (WTMC) 2021 - documents the CICFlowMeter
    TCP-appendix bug (25.9% spurious flows) and releases corrected flows at
    https://intrusion-detection.distrinet-research.be/WTMC2021/
  - Liu, Engelen, Lynar, Essam, Joosen, "Error Prevalence in NIDS Datasets:
    A Case Study on CIC-IDS-2017 and CSE-CIC-IDS-2018", IEEE CNS 2022 -
    the follow-up "improved" regeneration (this file's schema: 91 columns,
    fine-grained labels + 'Attempted Category'), released at
    https://intrusion-detection.distrinet-research.be/CNS2022/
  - Kaggle mirror actually downloaded (DistriNet host unreachable 2026-08-22):
    ernie55ernie/improved-cicids2017-and-csecicids2018, files
    CICIDS2017_improved/{monday..friday}.csv (1,152,270,765 bytes total).

Staged OUTSIDE the repo; override location with env var CICIDS_IMPROVED_DATA_DIR.

Public API mirrors load_cicids.get_flows():
  get_flows(harmonize=True, drop_attempted=True, drop_infiltration=True)
    -> (X: DataFrame, y: Series [7 family labels], feature_names)

harmonize=True renames the improved columns to the ORIGINAL (A1 Kaggle release)
52-column names so the same audit code runs unchanged on both datasets.
"""

from __future__ import annotations

import glob
import os

import numpy as np
import pandas as pd

_DEFAULT_DATA_DIR = (
    r"C:\Users\nakul\AppData\Local\Temp\claude"
    r"\C--Users-nakul-OneDrive-Desktop-Academics-cn"
    r"\ee30e724-9e44-4268-a3e6-2eabd7e384d0\scratchpad\cicids2017_improved"
)
DATA_DIR = os.environ.get("CICIDS_IMPROVED_DATA_DIR", _DEFAULT_DATA_DIR)

# improved-release column name -> original (A1 cleaned release) column name.
# Verified against both actual headers on 2026-08-22. Covers all 52 A1 features.
COLUMN_MAP = {
    "Dst Port": "Destination Port",
    "Flow Duration": "Flow Duration",
    "Total Fwd Packet": "Total Fwd Packets",
    "Total Length of Fwd Packet": "Total Length of Fwd Packets",
    "Fwd Packet Length Max": "Fwd Packet Length Max",
    "Fwd Packet Length Min": "Fwd Packet Length Min",
    "Fwd Packet Length Mean": "Fwd Packet Length Mean",
    "Fwd Packet Length Std": "Fwd Packet Length Std",
    "Bwd Packet Length Max": "Bwd Packet Length Max",
    "Bwd Packet Length Min": "Bwd Packet Length Min",
    "Bwd Packet Length Mean": "Bwd Packet Length Mean",
    "Bwd Packet Length Std": "Bwd Packet Length Std",
    "Flow Bytes/s": "Flow Bytes/s",
    "Flow Packets/s": "Flow Packets/s",
    "Flow IAT Mean": "Flow IAT Mean",
    "Flow IAT Std": "Flow IAT Std",
    "Flow IAT Max": "Flow IAT Max",
    "Flow IAT Min": "Flow IAT Min",
    "Fwd IAT Total": "Fwd IAT Total",
    "Fwd IAT Mean": "Fwd IAT Mean",
    "Fwd IAT Std": "Fwd IAT Std",
    "Fwd IAT Max": "Fwd IAT Max",
    "Fwd IAT Min": "Fwd IAT Min",
    "Bwd IAT Total": "Bwd IAT Total",
    "Bwd IAT Mean": "Bwd IAT Mean",
    "Bwd IAT Std": "Bwd IAT Std",
    "Bwd IAT Max": "Bwd IAT Max",
    "Bwd IAT Min": "Bwd IAT Min",
    "Fwd Header Length": "Fwd Header Length",
    "Bwd Header Length": "Bwd Header Length",
    "Fwd Packets/s": "Fwd Packets/s",
    "Bwd Packets/s": "Bwd Packets/s",
    "Packet Length Min": "Min Packet Length",
    "Packet Length Max": "Max Packet Length",
    "Packet Length Mean": "Packet Length Mean",
    "Packet Length Std": "Packet Length Std",
    "Packet Length Variance": "Packet Length Variance",
    "FIN Flag Count": "FIN Flag Count",
    "PSH Flag Count": "PSH Flag Count",
    "ACK Flag Count": "ACK Flag Count",
    "Average Packet Size": "Average Packet Size",
    "Subflow Fwd Bytes": "Subflow Fwd Bytes",
    "FWD Init Win Bytes": "Init_Win_bytes_forward",
    "Bwd Init Win Bytes": "Init_Win_bytes_backward",
    "Fwd Act Data Pkts": "act_data_pkt_fwd",
    "Fwd Seg Size Min": "min_seg_size_forward",
    "Active Mean": "Active Mean",
    "Active Max": "Active Max",
    "Active Min": "Active Min",
    "Idle Mean": "Idle Mean",
    "Idle Max": "Idle Max",
    "Idle Min": "Idle Min",
}

# fine-grained improved label (base, " - Attempted" suffix stripped) -> the
# 7-family scheme of the A1 original release. Improved labels observed in the
# actual data (27 distinct incl. Attempted variants), all covered here.
FAMILY_MAP = {
    "BENIGN": "Normal Traffic",
    "DoS Hulk": "DoS", "DoS GoldenEye": "DoS", "DoS Slowloris": "DoS",
    "DoS Slowhttptest": "DoS", "Heartbleed": "DoS",
    "DDoS": "DDoS",
    "Portscan": "Port Scanning",
    "FTP-Patator": "Brute Force", "SSH-Patator": "Brute Force",
    "Web Attack - Brute Force": "Web Attacks",
    "Web Attack - XSS": "Web Attacks",
    "Web Attack - SQL Injection": "Web Attacks",
    "Botnet": "Bots",
    # Not present in the A1 original release's 7 classes; dropped by default:
    "Infiltration": "Infiltration",
    "Infiltration - Portscan": "Infiltration",
}

ATTEMPTED_SUFFIX = " - Attempted"


def _find_csvs(data_dir: str) -> list[str]:
    paths = sorted(glob.glob(os.path.join(data_dir, "*.csv")))
    if not paths:
        raise FileNotFoundError(
            f"No CSV files under {data_dir!r}. Set CICIDS_IMPROVED_DATA_DIR to "
            "the directory holding CICIDS2017_improved monday..friday CSVs."
        )
    return paths


def load_raw(data_dir: str | None = None, usecols: list[str] | None = None) -> pd.DataFrame:
    """Read all improved CSVs, concatenate, drop NaN/Inf rows.

    usecols defaults to the 52 mapped feature columns + Label (memory-safe:
    skips id/Flow ID/IP/Timestamp metadata and the extra improved-only columns).
    """
    data_dir = data_dir or DATA_DIR
    if usecols is None:
        usecols = list(COLUMN_MAP) + ["Label"]
    frames = [pd.read_csv(p, usecols=usecols, low_memory=False)
              for p in _find_csvs(data_dir)]
    df = pd.concat(frames, axis=0, ignore_index=True)
    df = df.replace([np.inf, -np.inf], np.nan)
    before = len(df)
    df = df.dropna(axis=0)
    if before - len(df):
        print(f"[load_cicids_improved] dropped {before - len(df)} NaN/Inf rows "
              f"({before} -> {len(df)})")
    return df


def get_flows(data_dir: str | None = None, *, harmonize: bool = True,
              drop_attempted: bool = True, drop_infiltration: bool = True):
    """Return (X, y, feature_names) in the same shape as load_cicids.get_flows().

    drop_attempted: Liu et al. label flows of *failed* attack executions
      "<Attack> - Attempted"; they carry no attack payload behaviour. Default
      drops them (11,979 rows). Set False to keep them under their base family.
    drop_infiltration: the A1 original release has no Infiltration class, so
      the paired E4 comparison drops it (71,848 rows incl. Infiltration -
      Portscan). Set False to keep it as an 8th family.
    """
    df = load_raw(data_dir)

    lab = df["Label"].astype(str).str.strip()
    attempted = lab.str.endswith(ATTEMPTED_SUFFIX)
    base = lab.str.replace(ATTEMPTED_SUFFIX, "", regex=False)
    unknown = sorted(set(base) - set(FAMILY_MAP))
    if unknown:
        raise KeyError(f"Unmapped improved labels: {unknown}")
    fam = base.map(FAMILY_MAP)

    keep = pd.Series(True, index=df.index)
    if drop_attempted:
        keep &= ~attempted
    if drop_infiltration:
        keep &= fam != "Infiltration"
    df, fam = df[keep], fam[keep]

    X = df.drop(columns=["Label"])
    if harmonize:
        X = X.rename(columns=COLUMN_MAP)
    return X, fam.rename("Attack Type"), list(X.columns)


if __name__ == "__main__":
    X, y, feature_names = get_flows()
    print(f"flows:    {len(X)}")
    print(f"features: {len(feature_names)}")
    print(f"classes:  {y.nunique()}")
    print(y.value_counts().to_string())
    tcp_appendix = (X["Init_Win_bytes_forward"] == -1)
    print(f"Init_Win_bytes_forward == -1: {tcp_appendix.sum()} flows "
          f"({tcp_appendix.mean()*100:.2f}%)")
