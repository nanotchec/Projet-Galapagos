"""Load and reconstruct cost-aware signal selection inputs."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from galapagos.research.trade_ledger.intrabar_evaluator import evaluate_trade_candidates_intrabar
from galapagos.research.trade_ledger.ledger_builder import build_trade_candidates
from galapagos.research.trade_ledger.signal_loader import load_ml_signals


def read_optional_json(path: str | Path | None) -> dict[str, Any]:
    if not path:
        return {"status": "not_provided"}
    import json

    p = Path(path)
    if not p.exists():
        return {"status": "missing", "path": str(p)}
    return json.loads(p.read_text(encoding="utf-8"))


def load_selection_inputs(
    *,
    predictions_path: str | Path,
    dataset_path: str | Path,
    intrabar_path: str | Path,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    missing = [
        str(p)
        for p in [Path(predictions_path), Path(dataset_path), Path(intrabar_path)]
        if not p.exists()
    ]
    if missing:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), {
            "status": "missing_required_inputs",
            "missing_files": missing,
        }

    signals_df, signal_audit = load_ml_signals(str(predictions_path))
    dataset = pd.read_parquet(dataset_path)
    intrabar = pd.read_parquet(intrabar_path)
    return signals_df, dataset, intrabar, {"status": "loaded", "signal_audit": signal_audit}


def reconstruct_policy_results(
    *,
    signals_df: pd.DataFrame,
    dataset: pd.DataFrame,
    intrabar: pd.DataFrame,
    policies: list[str],
) -> dict[str, dict[str, Any]]:
    reconstructed: dict[str, dict[str, Any]] = {}
    if signals_df.empty or dataset.empty or intrabar.empty:
        return reconstructed
    for policy in policies:
        candidates = build_trade_candidates(signals_df, dataset, policy)
        results = evaluate_trade_candidates_intrabar(candidates, intrabar)
        reconstructed[policy] = {"candidates": candidates, "results": results}
    return reconstructed
