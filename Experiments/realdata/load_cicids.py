"""load_cicids.py - Parcel A1: load + hygiene for the CIC-IDS2017 flow-CSV dataset.

Source (Kaggle): ericanacletoribeiro/cicids2017-cleaned-and-preprocessed
  https://www.kaggle.com/datasets/ericanacletoribeiro/cicids2017-cleaned-and-preprocessed
Underlying dataset: Sharafaldin et al., CIC-IDS2017 (ICISSP 2018),
  https://www.unb.ca/cic/datasets/ids-2017.html

The raw zip is staged OUTSIDE the repo (scratchpad / any local dir) and deleted
after extraction. Point CICIDS_DATA_DIR at the directory holding the extracted
CSV(s); the default below is the acquisition session's scratchpad location.

Hygiene applied (in this order):
  1. read every *.csv in the data dir and concatenate row-wise
  2. strip leading/trailing whitespace from column names (original CIC CSVs
     ship names like " Destination Port")
  3. replace +/-Inf with NaN, then drop any row containing NaN
     (Flow Bytes/s and Flow Packets/s are the historically affected columns)
  4. label column is "Attack Type" (this Kaggle re-release) or "Label"
     (original CIC distribution) - both accepted

Public API:
  get_flows() -> (X: DataFrame [numeric features only], y: Series, feature_names: list[str])

Documented-artifact columns exposed for downstream E4 work: see ARTIFACT_COLUMNS.
"""

from __future__ import annotations

import glob
import os

import numpy as np
import pandas as pd

# Default: where Parcel A1 extracted the CSV. Override with env var CICIDS_DATA_DIR.
_DEFAULT_DATA_DIR = (
    r"C:\Users\nakul\AppData\Local\Temp\claude"
    r"\C--Users-nakul-OneDrive-Desktop-Academics-cn"
    r"\ee30e724-9e44-4268-a3e6-2eabd7e384d0\scratchpad\cicids2017"
)
DATA_DIR = os.environ.get("CICIDS_DATA_DIR", _DEFAULT_DATA_DIR)

# Candidate label-column names across CIC-IDS2017 re-releases.
_LABEL_CANDIDATES = ("Attack Type", "Label")

# Columns tied to the paper's documented natural artifacts (Track B / E4).
# Keys are artifact ids used in phase.md discussion; values are column names
# as they appear AFTER whitespace stripping.
ARTIFACT_COLUMNS = {
    # Destination-port shortcut: attacks in CIC-IDS2017 concentrate on a few
    # ports (e.g. 80, 21, 22), making Destination Port a near-perfect shortcut.
    "dest_port": ["Destination Port"],
    # Engelen et al. (WTMC/SPW 2021) flow-construction critique: CICFlowMeter
    # mis-terminates TCP flows (25.9% spurious "TCP-appendix" flows). The
    # appendix flows are short FIN/ACK-only fragments whose signature shows up
    # in forward-direction header/handshake features:
    "flow_construction": [
        "Fwd Header Length",       # tiny for 1-2 packet appendix fragments
        "min_seg_size_forward",    # forward min segment size; degenerate on fragments
        "Init_Win_bytes_forward",  # -1/0 when no handshake was captured in-flow
        "Init_Win_bytes_backward",
    ],
    # TTL 64/128 artifact (attacker Kali=64 vs victim Windows=128) is a
    # PACKET-level field; CICFlowMeter emits no TTL-derived feature, so it is
    # NOT representable in this flow-CSV. Kept here as an explicit empty entry
    # so downstream code documents rather than silently ignores it.
    "ttl": [],
}


def _find_csvs(data_dir: str) -> list[str]:
    paths = sorted(glob.glob(os.path.join(data_dir, "**", "*.csv"), recursive=True))
    if not paths:
        raise FileNotFoundError(
            f"No CSV files under {data_dir!r}. Set CICIDS_DATA_DIR to the "
            "directory containing the extracted cicids2017 CSV(s)."
        )
    return paths


def load_raw(data_dir: str | None = None) -> pd.DataFrame:
    """Read all CSVs, concatenate, strip column whitespace, drop NaN/Inf rows."""
    data_dir = data_dir or DATA_DIR
    frames = []
    for p in _find_csvs(data_dir):
        df = pd.read_csv(p, low_memory=False)
        df.columns = df.columns.str.strip()
        frames.append(df)
    df = pd.concat(frames, axis=0, ignore_index=True)

    df = df.replace([np.inf, -np.inf], np.nan)
    before = len(df)
    df = df.dropna(axis=0)
    dropped = before - len(df)
    if dropped:
        print(f"[load_cicids] dropped {dropped} rows containing NaN/Inf "
              f"({before} -> {len(df)})")
    return df


def get_flows(data_dir: str | None = None):
    """Return (X, y, feature_names).

    X: DataFrame of numeric flow features (label column removed; any residual
       non-numeric columns removed and reported).
    y: Series of class labels (str).
    feature_names: list of X's column names, in order.
    """
    df = load_raw(data_dir)

    label_col = next((c for c in _LABEL_CANDIDATES if c in df.columns), None)
    if label_col is None:
        raise KeyError(
            f"No label column found; expected one of {_LABEL_CANDIDATES}, "
            f"got columns {list(df.columns)[:5]}..."
        )
    y = df[label_col].astype(str).str.strip()
    X = df.drop(columns=[label_col])

    non_numeric = [c for c in X.columns if not np.issubdtype(X[c].dtype, np.number)]
    if non_numeric:
        print(f"[load_cicids] dropping non-numeric columns: {non_numeric}")
        X = X.drop(columns=non_numeric)

    feature_names = list(X.columns)
    return X, y, feature_names


def artifact_columns_present(feature_names: list[str]) -> dict[str, list[str]]:
    """Which documented-artifact columns actually exist in this release."""
    return {
        k: [c for c in cols if c in feature_names]
        for k, cols in ARTIFACT_COLUMNS.items()
    }


if __name__ == "__main__":
    X, y, feature_names = get_flows()
    print(f"flows:    {len(X)}")
    print(f"features: {len(feature_names)}")
    print(f"classes:  {y.nunique()}")
    print("class distribution:")
    print(y.value_counts().to_string())
    print("artifact columns present:", artifact_columns_present(feature_names))
