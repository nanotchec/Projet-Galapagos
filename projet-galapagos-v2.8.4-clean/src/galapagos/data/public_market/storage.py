from __future__ import annotations

from pathlib import Path

import pandas as pd


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def write_parquet(frame: pd.DataFrame, path: Path) -> None:
    ensure_parent(path)
    frame.to_parquet(path, index=False, engine="pyarrow")


def read_parquet(path: Path) -> pd.DataFrame:
    return pd.read_parquet(path, engine="pyarrow")
