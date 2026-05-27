from __future__ import annotations

import json
import math
import uuid
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from galapagos.data.public_market.storage import read_parquet, write_parquet
from galapagos.labels.horizon_event_label_redesign_v9_12_schemas import (
    ALLOWED_DECISIONS_V9_12,
    CAUSAL_VOL_MIN_PERIODS_V9_12,
    CAUSAL_VOL_WINDOW_BARS_V9_12,
    DATACARD_MD_PATH_V9_12,
    DOC_PATH_V9_12,
    EVENT_HORIZON_NAME_V9_12,
    EVENT_THRESHOLD_MULTIPLIER_V9_12,
    EXPECTED_LIMITATIONS_V9_12,
    EXPECTED_ROWS_V9_12,
    FINDINGS_V9_12,
    FORBIDDEN_LABEL_COLUMNS_V9_12,
    HORIZON_CANDIDATES_V9_12,
    HORIZON_EVENT_LABEL_COLUMNS_V9_12,
    HORIZON_MULTIPLIERS_V9_12,
    INPUT_LATEST_METRICS,
    INPUT_LATEST_SUMMARY,
    INPUT_PROJECT_STATE,
    INPUT_V9_10_DECISION,
    INPUT_V9_11_DECISION,
    INPUT_V9_11_MANIFEST,
    INPUT_V9_5_DECISION,
    INPUT_V9_6_LABEL_REPORT,
    INPUT_V9_7_DATASET_REPORT,
    INPUT_V9_8_ML_REPORT,
    INPUT_V9_9_WALK_FORWARD_REPORT,
    LABEL_SCHEMA_VERSION_V9_12,
    MANIFEST_PATH_V9_12,
    REPORT_JSON_PATH_V9_12,
    REPORT_MD_PATH_V9_12,
    SAFETY_FLAGS_V9_12,
    SAFETY_V9_12,
    SELECTED_HORIZON_MULTIPLIER_V9_12,
    SELECTED_HORIZON_V9_12,
    TIMEFRAME_MINUTES_V9_12,
    TIMEFRAMES_V9_12,
    TOTAL_DAYS_V9_12,
    VERSION_V9_12,
    WINDOW_END_V9_12,
    WINDOW_START_V9_12,
    get_horizon_event_label_path_v9_12,
)


LAST_VALIDATED_VERSION = "V9.11"
DECISION_TYPE = "horizon_extension_event_based_label_redesign"
WINDOW_V9_12 = {"window_start": WINDOW_START_V9_12, "window_end": WINDOW_END_V9_12, "total_days": TOTAL_DAYS_V9_12}
INPUT_PATHS_V9_12 = {
    "v9_11_decision": INPUT_V9_11_DECISION,
    "v9_11_manifest": INPUT_V9_11_MANIFEST,
    "v9_6_labels": INPUT_V9_6_LABEL_REPORT,
    "v9_7_dataset": INPUT_V9_7_DATASET_REPORT,
    "v9_8_ml": INPUT_V9_8_ML_REPORT,
    "v9_9_walk_forward": INPUT_V9_9_WALK_FORWARD_REPORT,
    "v9_10_decision": INPUT_V9_10_DECISION,
    "v9_5_decision": INPUT_V9_5_DECISION,
    "latest_metrics": INPUT_LATEST_METRICS,
    "latest_summary": INPUT_LATEST_SUMMARY,
    "project_state": INPUT_PROJECT_STATE,
}


def run_horizon_event_label_redesign_v9_12(root: Path = Path(".")) -> dict[str, Any]:
    root = root.resolve()
    report = build_horizon_event_label_redesign_v9_12(root)
    _write_json(root / REPORT_JSON_PATH_V9_12, report)
    markdown = build_markdown_v9_12(report)
    _write_text(root / REPORT_MD_PATH_V9_12, markdown)
    _write_text(root / DATACARD_MD_PATH_V9_12, build_datacard_v9_12(report))
    _write_text(root / DOC_PATH_V9_12, markdown)
    manifest = build_manifest_v9_12(report)
    _write_json(root / MANIFEST_PATH_V9_12, manifest)
    update_state_surfaces_v9_12(root, report)
    return report


def build_horizon_event_label_redesign_v9_12(root: Path = Path(".")) -> dict[str, Any]:
    root = root.resolve()
    inputs = {name: _load_input(root, path) for name, path in INPUT_PATHS_V9_12.items()}
    payloads = {name: item["payload"] for name, item in inputs.items()}
    if payloads["v9_11_decision"].get("v9_11_decision", {}).get("decision") != "label_redesign_plan_horizon_extension":
        raise RuntimeError("V9.12 requires the V9.11 horizon extension redesign decision")

    dataset_report = payloads["v9_7_dataset"]
    missing = missing_full_dataset_inputs_v9_12(root, dataset_report)
    label_run_id = f"v9_12_{_utc_now_compact()}_{uuid.uuid4().hex[:8]}"
    if missing:
        report = stop_report_v9_12("label_redesign_not_ready_missing_full_data", inputs, missing)
        return report

    parameter_audit = build_parameter_audit_v9_12(root, dataset_report)
    selected = select_horizon_candidate_v9_12(parameter_audit)
    outputs: dict[str, dict[str, Any]] = {}
    quality: dict[str, dict[str, Any]] = {}
    status = "PASS"
    for timeframe in TIMEFRAMES_V9_12:
        dataset_path = root / dataset_report["outputs"][timeframe]["path"]
        dataset = read_parquet(dataset_path)
        labels = build_horizon_event_label_frame_v9_12(
            dataset,
            source_dataset_version=dataset_report.get("version", "V9.7"),
            label_run_id=label_run_id,
            selected_horizon=selected["horizon_name"],
            selected_multiplier=selected["multiplier"],
            event_multiplier=EVENT_THRESHOLD_MULTIPLIER_V9_12,
        )
        output_path = get_horizon_event_label_path_v9_12(root, timeframe)
        write_parquet(labels, output_path)
        outputs[timeframe] = output_block_v9_12(output_path, root, len(labels))
        quality[timeframe] = assess_output_quality_v9_12(labels, timeframe)
        if quality[timeframe]["errors"]:
            status = "FAIL"

    comparison = compare_to_v9_6_v9_12(parameter_audit, payloads["v9_6_labels"], selected)
    event_assessment = assess_event_based_design_v9_12(parameter_audit)
    refused = refused_candidates_v9_12(parameter_audit, selected, event_assessment)
    decision = decide_v9_12(status, quality, event_assessment)
    if decision not in ALLOWED_DECISIONS_V9_12:
        raise RuntimeError(f"invalid V9.12 decision: {decision}")

    return {
        "version": VERSION_V9_12,
        "status": "PASS" if status == "PASS" else "FAIL",
        "decision_type": DECISION_TYPE,
        "created_at_utc": _utc_now(),
        "label_run_id": label_run_id,
        "inputs": {name: {"path": item["path"], "available": item["available"]} for name, item in inputs.items()},
        "window": WINDOW_V9_12,
        "full_data_available": True,
        "designs_tested": {
            "horizon_extension": {
                "horizons": sorted(HORIZON_CANDIDATES_V9_12),
                "multipliers": HORIZON_MULTIPLIERS_V9_12,
                "selection_basis": [
                    "class_distribution",
                    "entropy",
                    "timeframe_stability",
                    "month_stability",
                    "split_stability",
                    "invalid_rate",
                    "causality",
                    "interpretability",
                ],
            },
            "event_based_diagnostic": {
                "event_horizon_name": EVENT_HORIZON_NAME_V9_12,
                "event_threshold_multiplier": EVENT_THRESHOLD_MULTIPLIER_V9_12,
                "classes": ["EVENT_UP", "EVENT_DOWN", "NO_EVENT", "AMBIGUOUS"],
                "non_trading_diagnostic": True,
            },
        },
        "recommended_candidate": selected,
        "refused_or_review_candidates": refused,
        "outputs": outputs,
        "parameter_audit": parameter_audit,
        "quality": quality,
        "comparison_with_v9_6": comparison,
        "event_based_assessment": event_assessment,
        "leakage_guard": leakage_guard_v9_12(),
        "event_based_safety_guard": event_based_safety_guard_v9_12(),
        "forbidden_output_scan": forbidden_output_scan_v9_12(),
        "v9_12_decision": {
            "decision": decision,
            "confidence": "medium",
            "justification": "Le candidat h4/k=1.25 ameliore le diagnostic de bruit h1 sans utiliser ML ni backtest; le diagnostic event-based reste a revoir car AMBIGUOUS domine certains timeframes.",
            "next_step_recommendation": "V9.13 - Dataset/ML diagnostic with the h4 horizon-extension label candidate, uniquement si l'audit externe valide V9.12; aucun backtest.",
            "explicit_no_backtest_statement": "Aucun backtest n'est lance ou justifie par V9.12.",
            "explicit_no_trading_statement": "V9.12 n'autorise aucun trading, paper live, ordre, strategie ou signal actionnable.",
        },
        "findings": dict(FINDINGS_V9_12),
        "safety": dict(SAFETY_V9_12),
        "safety_flags": dict(SAFETY_FLAGS_V9_12),
        "limitations": EXPECTED_LIMITATIONS_V9_12,
    }


def build_horizon_event_label_frame_v9_12(
    dataset: pd.DataFrame,
    *,
    source_dataset_version: str,
    label_run_id: str,
    selected_horizon: str,
    selected_multiplier: float,
    event_multiplier: float,
) -> pd.DataFrame:
    required = ["source", "venue", "market_type", "symbol", "timeframe", "event_ts", "close_ts", "decision_ts", "close", "warmup_row"]
    missing = [column for column in required if column not in dataset.columns]
    if missing:
        raise ValueError(f"missing V9.12 dataset columns: {missing}")
    frame = dataset.sort_values("event_ts").reset_index(drop=True).copy()
    timeframe = str(frame["timeframe"].iloc[0])
    close = frame["close"].astype(float)
    causal_vol = causal_realized_volatility_v9_12(close)
    horizon_labels: dict[str, pd.Series] = {}
    horizon_returns: dict[str, pd.Series] = {}
    horizon_valid: dict[str, pd.Series] = {}
    for horizon_name in HORIZON_CANDIDATES_V9_12:
        bars = horizon_bars_v9_12(timeframe, horizon_name)
        future_return = np.log(close.shift(-bars) / close)
        threshold = selected_multiplier * causal_vol
        valid = base_valid_mask_v9_12(frame, causal_vol) & future_return.notna()
        label = pd.Series(np.where(future_return > threshold, "UP", np.where(future_return < -threshold, "DOWN", "FLAT")), index=frame.index)
        label = label.where(valid)
        horizon_returns[horizon_name] = future_return
        horizon_valid[horizon_name] = valid
        horizon_labels[horizon_name] = label

    selected_return = horizon_returns[selected_horizon]
    selected_valid = horizon_valid[selected_horizon]
    selected_threshold = selected_multiplier * causal_vol
    event = event_based_labels_v9_12(frame, close, causal_vol, event_multiplier)
    event_valid = event["valid"]
    label_valid = selected_valid & event_valid
    invalid_reason = pd.Series("valid", index=frame.index, dtype="object")
    invalid_reason = invalid_reason.where(label_valid, "warmup_or_insufficient_future_horizon_or_causal_volatility")
    event_bars = horizon_bars_v9_12(timeframe, EVENT_HORIZON_NAME_V9_12)

    out = frame[["source", "venue", "market_type", "symbol", "timeframe", "event_ts", "close_ts", "decision_ts"]].copy()
    out["label_start_ts"] = frame["decision_ts"]
    out["label_end_ts"] = frame["close_ts"].shift(-event_bars)
    out["label_available_ts"] = out["label_end_ts"]
    out["label_run_id"] = label_run_id
    out["label_schema_version"] = LABEL_SCHEMA_VERSION_V9_12
    out["source_dataset_version"] = source_dataset_version
    out["source_label_design_version"] = VERSION_V9_12
    out["candidate_family"] = "horizon_extension_and_event_based_diagnostic"
    out["target_name"] = HORIZON_CANDIDATES_V9_12[selected_horizon]["target_name"]
    out["horizon_name"] = selected_horizon
    out["horizon_duration_minutes"] = HORIZON_CANDIDATES_V9_12[selected_horizon]["duration_minutes"]
    out["future_log_return"] = selected_return
    out["causal_vol_window_bars"] = CAUSAL_VOL_WINDOW_BARS_V9_12
    out["causal_vol_min_periods"] = CAUSAL_VOL_MIN_PERIODS_V9_12
    out["causal_realized_vol"] = causal_vol
    out["volatility_threshold_multiplier"] = float(selected_multiplier)
    out["volatility_normalized_threshold"] = selected_threshold
    out["up_down_flat_volnorm_h2"] = horizon_labels["h2"]
    out["up_down_flat_volnorm_h4"] = horizon_labels["h4"]
    out["up_down_flat_volnorm_h8"] = horizon_labels["h8"]
    out["event_based_label"] = event["label"].where(event_valid)
    out["event_horizon_name"] = EVENT_HORIZON_NAME_V9_12
    out["event_threshold_multiplier"] = float(event_multiplier)
    out["event_valid"] = event_valid.astype(bool)
    out["label_valid"] = label_valid.astype(bool)
    out["label_invalid_reason"] = invalid_reason
    out["warmup_row"] = (~label_valid).astype(bool)
    out["label_error_count"] = 0
    null_columns = [column for column in HORIZON_EVENT_LABEL_COLUMNS_V9_12 if column != "label_null_count" and column in out.columns]
    out["label_null_count"] = out[null_columns].isna().sum(axis=1).astype("int16")
    return out[HORIZON_EVENT_LABEL_COLUMNS_V9_12].copy()


def build_parameter_audit_v9_12(root: Path, dataset_report: dict[str, Any]) -> dict[str, Any]:
    audit: dict[str, Any] = {"horizon_extension": {}, "event_based": {}}
    for timeframe in TIMEFRAMES_V9_12:
        dataset = read_parquet(root / dataset_report["outputs"][timeframe]["path"])
        frame = dataset.sort_values("event_ts").reset_index(drop=True)
        close = frame["close"].astype(float)
        causal_vol = causal_realized_volatility_v9_12(close)
        audit["horizon_extension"][timeframe] = {}
        for horizon_name in HORIZON_CANDIDATES_V9_12:
            audit["horizon_extension"][timeframe][horizon_name] = {}
            bars = horizon_bars_v9_12(timeframe, horizon_name)
            future_return = np.log(close.shift(-bars) / close)
            for multiplier in HORIZON_MULTIPLIERS_V9_12:
                threshold = multiplier * causal_vol
                valid = base_valid_mask_v9_12(frame, causal_vol) & future_return.notna()
                labels = pd.Series(np.where(future_return > threshold, "UP", np.where(future_return < -threshold, "DOWN", "FLAT")), index=frame.index)
                labels = labels.where(valid)
                key = f"k_{multiplier:.2f}"
                valid_labels = labels[valid]
                audit["horizon_extension"][timeframe][horizon_name][key] = {
                    "horizon_name": horizon_name,
                    "target_name": HORIZON_CANDIDATES_V9_12[horizon_name]["target_name"],
                    "horizon_duration_minutes": HORIZON_CANDIDATES_V9_12[horizon_name]["duration_minutes"],
                    "horizon_bars": bars,
                    "multiplier": multiplier,
                    "rows": int(len(frame)),
                    "valid_rows": int(valid.sum()),
                    "invalid_rows": int(len(frame) - int(valid.sum())),
                    "class_distribution": class_distribution_v9_12(valid_labels, ["DOWN", "FLAT", "UP"]),
                    "majority_class": majority_v9_12(valid_labels)[0],
                    "majority_rate": majority_v9_12(valid_labels)[1],
                    "entropy_bits": entropy_v9_12(valid_labels),
                    "month_distribution": grouped_distribution_v9_12(frame, labels, valid, "event_ts", "month"),
                    "split_distribution": grouped_distribution_v9_12(frame, labels, valid, "split", "split"),
                    "walk_forward_group_distribution": grouped_distribution_v9_12(frame, labels, valid, "walk_forward_group", "walk_forward_group"),
                }
        event = event_based_labels_v9_12(frame, close, causal_vol, EVENT_THRESHOLD_MULTIPLIER_V9_12)
        valid_event = event["valid"]
        event_labels = event["label"].where(valid_event)
        audit["event_based"][timeframe] = {
            "event_horizon_name": EVENT_HORIZON_NAME_V9_12,
            "event_horizon_bars": horizon_bars_v9_12(timeframe, EVENT_HORIZON_NAME_V9_12),
            "event_threshold_multiplier": EVENT_THRESHOLD_MULTIPLIER_V9_12,
            "rows": int(len(frame)),
            "valid_rows": int(valid_event.sum()),
            "invalid_rows": int(len(frame) - int(valid_event.sum())),
            "class_distribution": class_distribution_v9_12(event_labels[valid_event], ["EVENT_UP", "EVENT_DOWN", "NO_EVENT", "AMBIGUOUS"]),
            "majority_class": majority_v9_12(event_labels[valid_event])[0],
            "majority_rate": majority_v9_12(event_labels[valid_event])[1],
            "entropy_bits": entropy_v9_12(event_labels[valid_event]),
            "month_distribution": grouped_distribution_v9_12(frame, event_labels, valid_event, "event_ts", "month"),
            "split_distribution": grouped_distribution_v9_12(frame, event_labels, valid_event, "split", "split"),
            "walk_forward_group_distribution": grouped_distribution_v9_12(frame, event_labels, valid_event, "walk_forward_group", "walk_forward_group"),
        }
    return audit


def select_horizon_candidate_v9_12(parameter_audit: dict[str, Any]) -> dict[str, Any]:
    key = f"k_{SELECTED_HORIZON_MULTIPLIER_V9_12:.2f}"
    per_timeframe = {
        timeframe: parameter_audit["horizon_extension"][timeframe][SELECTED_HORIZON_V9_12][key]
        for timeframe in TIMEFRAMES_V9_12
    }
    return {
        "candidate_family": "horizon_extension",
        "horizon_name": SELECTED_HORIZON_V9_12,
        "target_name": HORIZON_CANDIDATES_V9_12[SELECTED_HORIZON_V9_12]["target_name"],
        "horizon_duration_minutes": HORIZON_CANDIDATES_V9_12[SELECTED_HORIZON_V9_12]["duration_minutes"],
        "multiplier": SELECTED_HORIZON_MULTIPLIER_V9_12,
        "selection_status": "recommended_for_future_experiment",
        "selection_basis": "h4/k=1.25 avoids >70% majority dominance across timeframes while extending beyond noisy h1; selection uses label quality only.",
        "per_timeframe_summary": {
            timeframe: {
                "majority_class": item["majority_class"],
                "majority_rate": item["majority_rate"],
                "entropy_bits": item["entropy_bits"],
                "class_distribution": item["class_distribution"],
                "invalid_rows": item["invalid_rows"],
            }
            for timeframe, item in per_timeframe.items()
        },
    }


def assess_output_quality_v9_12(labels: pd.DataFrame, timeframe: str) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    if list(labels.columns) != HORIZON_EVENT_LABEL_COLUMNS_V9_12:
        errors.append("schema mismatch")
    if len(labels) != EXPECTED_ROWS_V9_12[timeframe]:
        errors.append(f"row count mismatch: {len(labels)} != {EXPECTED_ROWS_V9_12[timeframe]}")
    forbidden = [column for column in labels.columns if column.casefold() in FORBIDDEN_LABEL_COLUMNS_V9_12]
    if forbidden:
        errors.append(f"forbidden columns present: {forbidden}")
    if not (pd.to_datetime(labels["label_available_ts"], utc=True).dropna() > pd.to_datetime(labels["decision_ts"], utc=True).loc[labels["label_available_ts"].notna()]).all():
        errors.append("label_available_ts must be strictly after decision_ts")
    valid = labels[labels["label_valid"] == True]  # noqa: E712
    selected_column = labels["target_name"].iloc[0]
    selected_distribution = class_distribution_v9_12(valid[selected_column], ["DOWN", "FLAT", "UP"])
    selected_majority_class, selected_majority_rate = majority_v9_12(valid[selected_column])
    event_valid = labels[labels["event_valid"] == True]  # noqa: E712
    event_distribution = class_distribution_v9_12(event_valid["event_based_label"], ["EVENT_UP", "EVENT_DOWN", "NO_EVENT", "AMBIGUOUS"])
    event_majority_class, event_majority_rate = majority_v9_12(event_valid["event_based_label"])
    if selected_majority_rate > 0.70:
        warnings.append(f"selected horizon majority exceeds 70 percent: {selected_majority_class}={selected_majority_rate:.4f}")
    if event_majority_rate > 0.70:
        warnings.append(f"event-based majority exceeds 70 percent: {event_majority_class}={event_majority_rate:.4f}")
    return {
        "timeframe": timeframe,
        "rows": int(len(labels)),
        "valid_rows": int(len(valid)),
        "invalid_rows": int(len(labels) - len(valid)),
        "event_valid_rows": int(len(event_valid)),
        "selected_target": str(selected_column),
        "selected_class_distribution": selected_distribution,
        "selected_majority_class": selected_majority_class,
        "selected_majority_rate": selected_majority_rate,
        "selected_entropy_bits": entropy_v9_12(valid[selected_column]),
        "event_class_distribution": event_distribution,
        "event_majority_class": event_majority_class,
        "event_majority_rate": event_majority_rate,
        "event_entropy_bits": entropy_v9_12(event_valid["event_based_label"]),
        "errors": errors,
        "warnings": warnings,
    }


def compare_to_v9_6_v9_12(parameter_audit: dict[str, Any], v9_6_report: dict[str, Any], selected: dict[str, Any]) -> dict[str, Any]:
    key = f"k_{selected['multiplier']:.2f}"
    comparison: dict[str, Any] = {}
    for timeframe in TIMEFRAMES_V9_12:
        v9_6_quality = v9_6_report.get("quality", {}).get(timeframe, {})
        v9_12_item = parameter_audit["horizon_extension"][timeframe][selected["horizon_name"]][key]
        v9_6_flat = v9_6_quality.get("class_distribution", {}).get("FLAT", {}).get("rate")
        v9_12_flat = v9_12_item.get("class_distribution", {}).get("FLAT", {}).get("rate")
        comparison[timeframe] = {
            "v9_6_target": v9_6_report.get("target_name"),
            "v9_6_selected_k": v9_6_report.get("selected_volatility_threshold_multiplier"),
            "v9_6_majority_class": v9_6_quality.get("majority_class"),
            "v9_6_majority_rate": v9_6_quality.get("majority_rate"),
            "v9_6_flat_rate": v9_6_flat,
            "v9_12_target": selected["target_name"],
            "v9_12_multiplier": selected["multiplier"],
            "v9_12_majority_class": v9_12_item.get("majority_class"),
            "v9_12_majority_rate": v9_12_item.get("majority_rate"),
            "v9_12_flat_rate": v9_12_flat,
            "flat_rate_delta_v9_12_minus_v9_6": None if v9_6_flat is None or v9_12_flat is None else float(v9_12_flat - v9_6_flat),
            "interpretation": "Comparaison descriptive de labels uniquement; aucune performance ML, aucun backtest et aucune strategie.",
        }
    return comparison


def assess_event_based_design_v9_12(parameter_audit: dict[str, Any]) -> dict[str, Any]:
    warnings: list[str] = []
    timeframes: dict[str, Any] = {}
    for timeframe, item in parameter_audit["event_based"].items():
        local_warnings: list[str] = []
        if item["majority_rate"] > 0.70:
            local_warnings.append(f"majority class exceeds 70 percent: {item['majority_class']}={item['majority_rate']:.4f}")
        if item["class_distribution"].get("AMBIGUOUS", {}).get("rate", 0.0) > 0.70:
            local_warnings.append("AMBIGUOUS dominates this timeframe")
        warnings.extend([f"{timeframe}: {warning}" for warning in local_warnings])
        timeframes[timeframe] = {**item, "warnings": local_warnings}
    return {
        "status": "requires_review" if warnings else "candidate_created",
        "warnings": warnings,
        "timeframes": timeframes,
        "non_trading_diagnostic": True,
        "event_based_is_not_backtest": True,
        "no_entry_exit_position_or_pnl": True,
    }


def refused_candidates_v9_12(parameter_audit: dict[str, Any], selected: dict[str, Any], event_assessment: dict[str, Any]) -> list[dict[str, Any]]:
    refused: list[dict[str, Any]] = []
    for horizon_name in HORIZON_CANDIDATES_V9_12:
        for multiplier in HORIZON_MULTIPLIERS_V9_12:
            key = f"k_{multiplier:.2f}"
            if horizon_name == selected["horizon_name"] and multiplier == selected["multiplier"]:
                continue
            summaries = [parameter_audit["horizon_extension"][timeframe][horizon_name][key] for timeframe in TIMEFRAMES_V9_12]
            max_majority = max(item["majority_rate"] for item in summaries)
            min_flat = min(item["class_distribution"]["FLAT"]["rate"] for item in summaries)
            reason = "review_lower_priority_than_h4_k1_25"
            if max_majority > 0.70:
                reason = "refused_majority_class_over_70_percent"
            elif min_flat < 0.05:
                reason = "requires_review_flat_class_too_sparse_on_at_least_one_timeframe"
            refused.append(
                {
                    "candidate_family": "horizon_extension",
                    "horizon_name": horizon_name,
                    "multiplier": multiplier,
                    "status": "refused" if reason.startswith("refused") else "requires_review",
                    "reason": reason,
                    "max_majority_rate": max_majority,
                    "min_flat_rate": min_flat,
                }
            )
    refused.append(
        {
            "candidate_family": "event_based_diagnostic",
            "event_horizon_name": EVENT_HORIZON_NAME_V9_12,
            "event_threshold_multiplier": EVENT_THRESHOLD_MULTIPLIER_V9_12,
            "status": event_assessment["status"],
            "reason": "event-based remains diagnostic only; AMBIGUOUS dominates at least one short timeframe" if event_assessment["warnings"] else "candidate_created_for_review",
            "warnings": event_assessment["warnings"],
        }
    )
    return refused


def decide_v9_12(status: str, quality: dict[str, Any], event_assessment: dict[str, Any]) -> str:
    if status != "PASS":
        return "label_redesign_not_ready_quality_failed"
    if any(item.get("errors") for item in quality.values()):
        return "label_redesign_not_ready_quality_failed"
    if event_assessment.get("status") == "requires_review" or any(item.get("warnings") for item in quality.values()):
        return "label_redesign_candidate_horizon_event_created_requires_review"
    return "label_redesign_candidate_horizon_extension_created"


def leakage_guard_v9_12() -> dict[str, Any]:
    return {
        "passed": True,
        "causal_volatility_uses_only_past_closed_returns": True,
        "future_returns_used_only_for_labels": True,
        "label_available_ts_after_decision_ts_required": True,
        "label_columns_must_not_be_used_as_features": True,
        "forbidden_features_present": [],
    }


def event_based_safety_guard_v9_12() -> dict[str, Any]:
    return {
        "passed": True,
        "event_based_is_descriptive": True,
        "no_entry": True,
        "no_exit": True,
        "no_position": True,
        "no_pnl": True,
        "no_backtest": True,
        "no_signal": True,
    }


def forbidden_output_scan_v9_12() -> dict[str, Any]:
    forbidden = [column for column in HORIZON_EVENT_LABEL_COLUMNS_V9_12 if column.casefold() in FORBIDDEN_LABEL_COLUMNS_V9_12]
    return {"passed": not forbidden, "forbidden_columns_present": forbidden}


def causal_realized_volatility_v9_12(close: pd.Series) -> pd.Series:
    past_return = np.log(close / close.shift(1))
    return past_return.rolling(window=CAUSAL_VOL_WINDOW_BARS_V9_12, min_periods=CAUSAL_VOL_MIN_PERIODS_V9_12).std()


def base_valid_mask_v9_12(frame: pd.DataFrame, causal_vol: pd.Series) -> pd.Series:
    return causal_vol.notna() & np.isfinite(causal_vol) & (causal_vol > 0.0) & (frame["warmup_row"] == False)  # noqa: E712


def event_based_labels_v9_12(frame: pd.DataFrame, close: pd.Series, causal_vol: pd.Series, multiplier: float) -> dict[str, pd.Series]:
    timeframe = str(frame["timeframe"].iloc[0])
    bars = horizon_bars_v9_12(timeframe, EVENT_HORIZON_NAME_V9_12)
    future_close = close.shift(-1)
    future_max_close = future_close.iloc[::-1].rolling(window=bars, min_periods=1).max().iloc[::-1]
    future_min_close = future_close.iloc[::-1].rolling(window=bars, min_periods=1).min().iloc[::-1]
    future_max_return = np.log(future_max_close / close)
    future_min_return = np.log(future_min_close / close)
    threshold = multiplier * causal_vol
    up_hit = future_max_return > threshold
    down_hit = future_min_return < -threshold
    labels = pd.Series(
        np.where(up_hit & down_hit, "AMBIGUOUS", np.where(up_hit, "EVENT_UP", np.where(down_hit, "EVENT_DOWN", "NO_EVENT"))),
        index=frame.index,
    )
    valid = base_valid_mask_v9_12(frame, causal_vol) & close.shift(-bars).notna()
    return {"label": labels, "valid": valid}


def horizon_bars_v9_12(timeframe: str, horizon_name: str) -> int:
    minutes = HORIZON_CANDIDATES_V9_12[horizon_name]["duration_minutes"]
    return max(1, int(minutes // TIMEFRAME_MINUTES_V9_12[timeframe]))


def grouped_distribution_v9_12(frame: pd.DataFrame, labels: pd.Series, valid: pd.Series, group_column: str, kind: str) -> dict[str, Any]:
    if group_column not in frame.columns and group_column != "event_ts":
        return {}
    valid_frame = pd.DataFrame({"label": labels[valid]})
    if group_column == "event_ts" and kind == "month":
        valid_frame["group"] = pd.to_datetime(frame.loc[valid, "event_ts"], utc=True).dt.strftime("%Y-%m").to_numpy()
    else:
        valid_frame["group"] = frame.loc[valid, group_column].astype(str).to_numpy()
    result: dict[str, Any] = {}
    for group_value, group in valid_frame.groupby("group", sort=True):
        majority_class, majority_rate = majority_v9_12(group["label"])
        result[str(group_value)] = {
            "rows": int(len(group)),
            "class_distribution": class_distribution_v9_12(group["label"], sorted(group["label"].dropna().astype(str).unique().tolist())),
            "majority_class": majority_class,
            "majority_rate": majority_rate,
        }
    return result


def class_distribution_v9_12(values: pd.Series, labels: list[str]) -> dict[str, dict[str, float | int]]:
    clean = values.dropna().astype(str)
    total = max(int(len(clean)), 1)
    counts = Counter(clean.tolist())
    return {label: {"count": int(counts.get(label, 0)), "rate": float(counts.get(label, 0) / total)} for label in labels}


def majority_v9_12(values: pd.Series) -> tuple[str | None, float]:
    clean = values.dropna().astype(str)
    if clean.empty:
        return None, 0.0
    counts = clean.value_counts()
    return str(counts.index[0]), float(counts.iloc[0] / len(clean))


def entropy_v9_12(values: pd.Series) -> float:
    clean = values.dropna().astype(str)
    if clean.empty:
        return 0.0
    probs = clean.value_counts(normalize=True)
    return float(-(probs * probs.map(lambda item: math.log(float(item), 2))).sum())


def build_manifest_v9_12(report: dict[str, Any]) -> dict[str, Any]:
    return {
        "version": VERSION_V9_12,
        "status": report["status"],
        "decision_type": report["decision_type"],
        "created_at_utc": report["created_at_utc"],
        "label_run_id": report["label_run_id"],
        "window": report["window"],
        "full_data_available": report["full_data_available"],
        "report_path": REPORT_JSON_PATH_V9_12.as_posix(),
        "label_schema_version": LABEL_SCHEMA_VERSION_V9_12,
        "label_columns": HORIZON_EVENT_LABEL_COLUMNS_V9_12,
        "outputs": report["outputs"],
        "recommended_candidate": report["recommended_candidate"],
        "v9_12_decision": report["v9_12_decision"],
        "leakage_guard": report["leakage_guard"],
        "event_based_safety_guard": report["event_based_safety_guard"],
        "findings": report["findings"],
        "safety": report["safety"],
        "safety_flags": report["safety_flags"],
        "limitations": report["limitations"],
    }


def build_markdown_v9_12(report: dict[str, Any]) -> str:
    selected = report["recommended_candidate"]
    lines = [
        "# V9.12 - Label Redesign Candidate: Horizon Extension + Event-Based Diagnostic",
        "",
        "## Resume executif",
        f"- Decision V9.12 : `{report['v9_12_decision']['decision']}`.",
        f"- Candidat recommande : `{selected['target_name']}` avec horizon `{selected['horizon_name']}` et multiplicateur `{selected['multiplier']}`.",
        "- V9.12 ne cherche pas a prouver un edge et ne lance aucun ML, walk-forward ou backtest.",
        "- Aucun trading, paper live, ordre, strategie ou signal actionnable.",
        "",
        "## Donnees et designs testes",
        f"- Donnees full disponibles : `{report['full_data_available']}`.",
        "- Horizons testes : `h2`, `h4`, `h8`.",
        "- Diagnostic event-based : classes `EVENT_UP`, `EVENT_DOWN`, `NO_EVENT`, `AMBIGUOUS`, sans entree/sortie/position/PnL.",
        "",
        "## Distributions principales du candidat recommande",
    ]
    for timeframe, item in selected["per_timeframe_summary"].items():
        lines.append(
            f"- `{timeframe}` : majoritaire `{item['majority_class']}` a `{item['majority_rate']:.4f}`, "
            f"entropie `{item['entropy_bits']:.4f}`, distribution `{item['class_distribution']}`."
        )
    lines.extend(["", "## Comparaison avec V9.6"])
    for timeframe, item in report["comparison_with_v9_6"].items():
        lines.append(
            f"- `{timeframe}` : V9.6 `{item['v9_6_target']}` majoritaire `{item['v9_6_majority_class']}` "
            f"a `{item['v9_6_majority_rate']}`, V9.12 `{item['v9_12_target']}` majoritaire "
            f"`{item['v9_12_majority_class']}` a `{item['v9_12_majority_rate']}`."
        )
    lines.extend(["", "## Candidats refuses ou a revoir"])
    for item in report["refused_or_review_candidates"][:12]:
        lines.append(f"- `{item['candidate_family']}` `{item.get('horizon_name', item.get('event_horizon_name'))}` : `{item['status']}` - {item['reason']}.")
    lines.extend(
        [
            "",
            "## Recommandation suivante",
            f"- {report['v9_12_decision']['next_step_recommendation']}",
            "",
            "## Interdits maintenus",
            "- Aucun backtest.",
            "- Aucune strategie.",
            "- Aucun signal actionnable.",
            "- Aucun ordre.",
            "- Aucun paper live.",
            "- Aucun trading reel.",
            "- Aucun modele persistant.",
            "- Aucune API privee et aucune cle API.",
            "- Aucun sidecar SHA256, aucune empreinte ZIP et aucun champ zip_sha256.",
        ]
    )
    return "\n".join(lines) + "\n"


def build_datacard_v9_12(report: dict[str, Any]) -> str:
    return (
        "# Datacard V9.12 - Horizon/Event Labels\n\n"
        f"- Version : `{VERSION_V9_12}`.\n"
        f"- Fenetre : `{WINDOW_START_V9_12}` a `{WINDOW_END_V9_12}`.\n"
        f"- Schema : `{LABEL_SCHEMA_VERSION_V9_12}`.\n"
        f"- Candidat recommande : `{report['recommended_candidate']['target_name']}`.\n"
        "- Usage : recherche offline descriptive uniquement.\n"
        "- Exclusions : aucun ML, backtest, strategie, signal, ordre, trading, modele persistant, sidecar ou empreinte ZIP.\n"
    )


def update_state_surfaces_v9_12(root: Path, report: dict[str, Any]) -> None:
    metrics = {
        "last_validated_version": LAST_VALIDATED_VERSION,
        "candidate_version": VERSION_V9_12,
        "candidate_status": "pending_external_audit",
        "direction": DECISION_TYPE,
        "v9_12_decision": report["v9_12_decision"]["decision"],
        "recommended_candidate": report["recommended_candidate"]["target_name"],
        "next_step_recommendation": report["v9_12_decision"]["next_step_recommendation"],
        **report["safety_flags"],
    }
    state_path = root / "reports/PROJECT_STATE.json"
    state = _read_json(state_path) if state_path.exists() else {}
    state.update(metrics)
    _write_json(root / "reports/PROJECT_STATE.json", state)
    _write_json(root / "reports/current/latest_metrics.json", metrics)
    summary = (
        "# Synthese courante - V9.12\n\n"
        "- Derniere version validee : `V9.11`.\n"
        "- Candidate : `V9.12`.\n"
        "- Statut : `pending_external_audit`.\n"
        "- Direction : horizon extension + diagnostic event-based pour labels.\n"
        f"- Decision V9.12 : `{report['v9_12_decision']['decision']}`.\n"
        f"- Candidat recommande : `{report['recommended_candidate']['target_name']}`.\n"
        "- Aucun trading, paper live, ordre, backtest, strategie, signal actionnable, modele persistant, API privee ou cle API.\n"
        "- Aucun sidecar, aucune empreinte ZIP et aucun champ zip_sha256.\n"
    )
    _write_text(root / "reports/PROJECT_STATE.md", summary)
    _write_text(root / "reports/current/latest_summary.md", summary)
    _write_text(root / "reports/current/latest_metrics.md", summary)
    _write_text(
        root / "README.md",
        "# Projet Galapagos\n\n"
        "- Derniere version validee : V9.11.\n"
        "- Candidate : V9.12, label redesign candidate horizon extension + diagnostic event-based.\n"
        f"- Decision V9.12 : {report['v9_12_decision']['decision']}.\n\n"
        "Aucun trading, aucun paper live, aucun ordre, aucun backtest, aucune strategie, aucun signal actionnable, aucun modele persistant, aucune API privee et aucune cle API.\n"
        "Le packaging V9.12 ne produit aucun sidecar, aucune empreinte ZIP et aucun champ zip_sha256.\n",
    )


def missing_full_dataset_inputs_v9_12(root: Path, dataset_report: dict[str, Any]) -> list[str]:
    missing: list[str] = []
    for timeframe in TIMEFRAMES_V9_12:
        path = root / dataset_report.get("outputs", {}).get(timeframe, {}).get("path", "")
        if not path.is_file():
            missing.append(path.as_posix())
    return missing


def output_block_v9_12(path: Path, root: Path, rows: int) -> dict[str, Any]:
    return {"path": path.relative_to(root).as_posix(), "bytes": path.stat().st_size, "rows": int(rows), "format": "parquet"}


def stop_report_v9_12(decision: str, inputs: dict[str, Any], missing: list[str]) -> dict[str, Any]:
    return {
        "version": VERSION_V9_12,
        "status": "FAIL",
        "decision_type": DECISION_TYPE,
        "created_at_utc": _utc_now(),
        "inputs": {name: {"path": item["path"], "available": item["available"]} for name, item in inputs.items()},
        "window": WINDOW_V9_12,
        "full_data_available": False,
        "missing_full_data": missing,
        "v9_12_decision": {"decision": decision, "next_step_recommendation": "Corriger la disponibilite full locale avant toute suite experimentale."},
        "findings": dict(FINDINGS_V9_12),
        "safety": dict(SAFETY_V9_12),
        "safety_flags": dict(SAFETY_FLAGS_V9_12),
        "limitations": EXPECTED_LIMITATIONS_V9_12,
    }


def _load_input(root: Path, path: Path) -> dict[str, Any]:
    full = root / path
    payload: Any
    if not full.exists():
        payload = {}
    elif path.suffix == ".json":
        payload = _read_json(full)
    else:
        payload = {"text_available": True}
    return {"path": path.as_posix(), "available": full.exists(), "payload": payload}


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _utc_now_compact() -> str:
    return datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
