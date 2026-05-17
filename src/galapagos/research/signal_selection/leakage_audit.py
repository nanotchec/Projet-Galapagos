"""Leakage audit helpers for signal selection rules and features."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from .selection_rules import SelectionRule, build_default_rules

FORBIDDEN_PREFIXES = (
    "forward_return_",
    "max_favorable_excursion_",
    "max_adverse_excursion_",
)
REALIZED_OUTCOME_COLUMNS = {
    "gross_pnl_pct",
    "net_pnl_pct",
    "mfe_pct",
    "mae_pct",
    "exit_reason",
    "simulation_status",
    "bars_held_intrabar",
}
DIAGNOSTIC_ONLY_COLUMNS = {
    "diagnostic_forward_move_pct",
}
CAUSAL_ALLOWED_COLUMNS = {
    "timestamp",
    "policy",
    "side",
    "predicted_probability",
    "model_name",
    "target",
    "feature_set",
    "split_name",
    "cost_pct",
    "realized_volatility",
    "volatility_regime",
    "trend_regime",
    "macro_regime",
    "derivatives_risk_regime",
    "combined_alpha_score",
    "alpha_score_v1_14",
    "ohlcv_only_alpha_score",
    "derivatives_regime_score",
    "mfe_proxy_pct",
    "causal_expected_move_pct",
    "gross_expected_move_pct",
    "expected_move_model_pct",
    "cost_to_expected_move_ratio",
    "gross_edge_after_cost",
    "is_cost_viable",
    "is_high_confidence",
    "is_high_volatility",
    "is_top_decile_by_probability",
    "is_top_decile_by_mfe_proxy",
    "confidence_bucket",
}


def classify_column(column: str) -> str:
    if column in REALIZED_OUTCOME_COLUMNS:
        return "realized_outcome"
    if column in DIAGNOSTIC_ONLY_COLUMNS:
        return "diagnostic_only"
    if any(column.startswith(prefix) for prefix in FORBIDDEN_PREFIXES):
        return "forbidden_future"
    if column in CAUSAL_ALLOWED_COLUMNS:
        return "causal_allowed"
    return "unknown"


def audit_signal_selection_leakage(
    *,
    features: pd.DataFrame | None = None,
    rules: list[SelectionRule] | None = None,
    source_paths: list[str | Path] | None = None,
) -> dict[str, Any]:
    rules = rules or build_default_rules()
    columns = list(features.columns) if features is not None else []
    column_classes = {column: classify_column(column) for column in columns}
    forbidden_future_columns = sorted(
        column for column, status in column_classes.items() if status == "forbidden_future"
    )
    realized_outcome_columns = sorted(
        column for column, status in column_classes.items() if status == "realized_outcome"
    )
    diagnostic_only_columns = sorted(
        column for column, status in column_classes.items() if status == "diagnostic_only"
    )
    rule_rows = [_audit_rule(rule) for rule in rules]
    non_causal_rules = [row for row in rule_rows if not row["causal"]]
    causal_rules_with_forbidden = [
        row for row in rule_rows if row["causal"] and row["forbidden_used_columns"]
    ]
    source_scan = _scan_sources(source_paths or [])
    leakage_risk = bool(
        forbidden_future_columns
        or causal_rules_with_forbidden
        or source_scan["dangerous_assignments"]
    )
    causal_subset_available = bool(
        [row for row in rule_rows if row["causal"] and not row["forbidden_used_columns"]]
    )
    if leakage_risk and causal_subset_available:
        status = "SIGNAL_SELECTION_CAUSAL_SUBSET_AVAILABLE"
        verdicts = [
            "SIGNAL_SELECTION_LEAKAGE_RISK_DETECTED",
            "SIGNAL_SELECTION_CAUSAL_SUBSET_AVAILABLE",
        ]
    elif leakage_risk:
        status = "SIGNAL_SELECTION_LEAKAGE_RISK_DETECTED"
        verdicts = [status]
    else:
        status = "SIGNAL_SELECTION_LEAKAGE_AUDIT_PASSED"
        verdicts = [status]
    return {
        "status": status,
        "verdicts": verdicts,
        "column_classes": column_classes,
        "forbidden_future_columns": forbidden_future_columns,
        "realized_outcome_columns": realized_outcome_columns,
        "diagnostic_only_columns": diagnostic_only_columns,
        "causal_allowed_columns": sorted(
            column for column, status in column_classes.items() if status == "causal_allowed"
        ),
        "rules": rule_rows,
        "causal_rules_count": sum(1 for row in rule_rows if row["causal"]),
        "diagnostic_rules_count": len(non_causal_rules),
        "causal_rules_with_forbidden_columns": causal_rules_with_forbidden,
        "source_scan": source_scan,
        "leakage_risk_resolved_for_causal_rules": not causal_rules_with_forbidden
        and not source_scan["dangerous_assignments"],
        "causal_subset_available": causal_subset_available,
    }


def _audit_rule(rule: SelectionRule) -> dict[str, Any]:
    used_columns = list(rule.used_columns)
    forbidden = [
        column
        for column in used_columns
        if classify_column(column) in {"forbidden_future", "realized_outcome", "diagnostic_only"}
    ]
    return {
        "name": rule.name,
        "family": rule.family,
        "description": rule.description,
        "causal": rule.causal and not forbidden,
        "declared_causal": rule.causal,
        "used_columns": used_columns,
        "forbidden_used_columns": forbidden,
    }


def _scan_sources(source_paths: list[str | Path]) -> dict[str, Any]:
    findings: list[dict[str, Any]] = []
    dangerous_assignments: list[dict[str, Any]] = []
    for source_path in source_paths:
        path = Path(source_path)
        if not path.exists():
            findings.append({"path": str(path), "status": "missing"})
            continue
        text = path.read_text(encoding="utf-8")
        forward_mentions = [
            token for token in ["forward_return_6bar", "forward_return_12bar"] if token in text
        ]
        if forward_mentions and "diagnostic_forward_move_pct" not in text:
            dangerous_assignments.append(
                {"path": str(path), "reason": "forward_return_used_without_diagnostic_field"}
            )
        if "gross_expected_move_pct" in text and "diagnostic_forward_move_pct" in text:
            findings.append(
                {
                    "path": str(path),
                    "status": "inspected",
                    "forward_mentions": forward_mentions,
                    "gross_expected_move_is_separated_from_diagnostic": True,
                }
            )
        else:
            findings.append(
                {
                    "path": str(path),
                    "status": "inspected",
                    "forward_mentions": forward_mentions,
                }
            )
    return {"files": findings, "dangerous_assignments": dangerous_assignments}
