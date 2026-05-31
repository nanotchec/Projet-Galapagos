from __future__ import annotations

from pathlib import Path
from typing import Any


FORBIDDEN_FEATURE_TERMS_V9_62 = [
    "future_",
    "label_",
    "direction_",
    "up_down_flat_",
    "target",
    "split",
    "walk_forward_group",
    "prediction",
    "model_score",
    "signal",
    "trading_signal",
    "order",
    "pnl",
    "backtest",
    "strategy",
    "entry",
    "exit",
    "position",
    "profit",
    "sharpe",
    "drawdown",
    "equity",
]

FORBIDDEN_METRIC_TERMS_V9_62 = {
    "pnl",
    "sharpe",
    "drawdown",
    "equity_curve",
    "equity",
    "profit_factor",
    "return_strategy",
    "hit_ratio_trading",
    "trade_count",
    "position_sizing",
}

FORBIDDEN_MODEL_SUFFIXES_V9_62 = (".pkl", ".pickle", ".joblib", ".onnx", ".pt", ".pth", ".ckpt")


def scan_forbidden_features_v9_62(feature_columns: list[str]) -> dict[str, Any]:
    forbidden = [
        column
        for column in feature_columns
        if any(term in column.casefold() for term in FORBIDDEN_FEATURE_TERMS_V9_62)
    ]
    return {
        "status": "PASS" if not forbidden else "FAIL",
        "forbidden_feature_columns": forbidden,
        "features_checked": len(feature_columns),
    }


def scan_forbidden_metrics_v9_62(payload: Any) -> dict[str, Any]:
    found: list[str] = []

    def walk(value: Any) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                lowered = str(key).casefold()
                if lowered in FORBIDDEN_METRIC_TERMS_V9_62:
                    found.append(str(key))
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)

    walk(payload)
    return {
        "status": "PASS" if not found else "FAIL",
        "forbidden_terms_present": sorted(set(found)),
    }


def no_persistent_model_check_v9_62(root: Path = Path(".")) -> dict[str, Any]:
    scan_roots = [root / "reports", root / "docs", root / "scripts", root / "src"]
    forbidden: list[str] = []
    for base in scan_roots:
        if not base.exists():
            continue
        forbidden.extend(
            path.relative_to(root).as_posix()
            for path in base.rglob("*")
            if path.is_file()
            and path.name.endswith(FORBIDDEN_MODEL_SUFFIXES_V9_62)
            and "__pycache__" not in path.parts
        )
    return {
        "status": "PASS" if not forbidden else "FAIL",
        "model_persisted": False,
        "forbidden_model_artifacts_created": forbidden,
        "checked_suffixes": list(FORBIDDEN_MODEL_SUFFIXES_V9_62),
    }
