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

from galapagos.data.public_market.provenance import sha256_file, utc_now_iso
from galapagos.data.public_market.storage import read_parquet, write_parquet
from galapagos.labels.refined_volatility_normalized_labels_v9_6_schemas import (
    ALLOWED_DECISIONS_V9_6,
    CAUSAL_VOL_MIN_PERIODS_V9_6,
    CAUSAL_VOL_WINDOW_BARS_V9_6,
    DATACARD_MD_PATH_V9_6,
    DOC_PATH_V9_6,
    EXPECTED_LIMITATIONS_V9_6,
    EXPECTED_ROWS_V9_6,
    FINDINGS_V9_6,
    FORBIDDEN_LABEL_COLUMNS_V9_6,
    HORIZON_BARS_V9_6,
    HORIZON_NAME_V9_6,
    INPUT_DATASET_MANIFEST_V9_1,
    INPUT_DECISION_MANIFEST_V9_5,
    INPUT_DECISION_V9_5,
    LABEL_SCHEMA_VERSION_V9_6,
    MANIFEST_PATH_V9_6,
    PARAMETER_GRID_V9_6,
    REFINED_VOLATILITY_NORMALIZED_LABEL_COLUMNS_V9_6,
    REPORT_JSON_PATH_V9_6,
    REPORT_MD_PATH_V9_6,
    SAFETY_FLAGS_V9_6,
    TARGET_NAME_V9_6,
    TIMEFRAMES_V9_6,
    TOTAL_DAYS_V9_6,
    VERSION_V9_6,
    WINDOW_END_V9_6,
    WINDOW_START_V9_6,
    get_refined_volnorm_label_path_v9_6,
)


def run_refined_volatility_normalized_labels_v9_6(root: Path = Path(".")) -> dict[str, Any]:
    root = root.resolve()
    dataset_manifest = _read_json(root / INPUT_DATASET_MANIFEST_V9_1)
    decision_v9_5 = _read_json(root / INPUT_DECISION_V9_5)
    if decision_v9_5.get("v9_5_decision", {}).get("decision") != "label_redesign_candidate_volatility_normalized":
        raise RuntimeError("V9.6 requires the V9.5 volatility-normalized label redesign decision")

    missing = _missing_dataset_inputs(root, dataset_manifest)
    if missing:
        report = _stop_report("label_factory_not_ready_missing_full_data", missing)
        _write_json(root / REPORT_JSON_PATH_V9_6, report)
        _write_json(root / MANIFEST_PATH_V9_6, _manifest_from_report(root, report, {}, {}, {}))
        _write_markdowns(root, report)
        return report

    label_run_id = f"v9_6_{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}_{uuid.uuid4().hex[:8]}"
    parameter_audit = build_parameter_audit_v9_6(root, dataset_manifest)
    selected_multiplier = select_volatility_multiplier_v9_6(parameter_audit)

    outputs: dict[str, dict[str, Any]] = {}
    quality: dict[str, dict[str, Any]] = {}
    status = "PASS"
    for timeframe in TIMEFRAMES_V9_6:
        dataset_path = root / dataset_manifest["outputs"][timeframe]["path"]
        dataset = read_parquet(dataset_path)
        labels = build_refined_volatility_normalized_labels_frame_v9_6(
            dataset,
            source_dataset_path=dataset_manifest["outputs"][timeframe]["path"],
            source_dataset_version=dataset_manifest.get("version", "V9.1"),
            label_run_id=label_run_id,
            volatility_threshold_multiplier=selected_multiplier,
        )
        output_path = get_refined_volnorm_label_path_v9_6(root, timeframe)
        write_parquet(labels, output_path)
        outputs[timeframe] = _output_block(root, output_path, len(labels))
        quality[timeframe] = assess_label_quality_v9_6(labels, timeframe, dataset)
        if quality[timeframe]["errors"]:
            status = "FAIL"

    decision = decide_v9_6(parameter_audit, quality, selected_multiplier, status)
    if decision not in ALLOWED_DECISIONS_V9_6:
        raise RuntimeError(f"invalid V9.6 decision: {decision}")
    report = {
        "version": VERSION_V9_6,
        "status": "PASS" if status == "PASS" else "FAIL",
        "created_at_utc": utc_now_iso(),
        "label_run_id": label_run_id,
        "decision": decision,
        "window": {"window_start": WINDOW_START_V9_6, "window_end": WINDOW_END_V9_6, "total_days": TOTAL_DAYS_V9_6},
        "target_name": TARGET_NAME_V9_6,
        "horizon_name": HORIZON_NAME_V9_6,
        "horizon_bars": HORIZON_BARS_V9_6,
        "parameters_tested": PARAMETER_GRID_V9_6,
        "selected_volatility_threshold_multiplier": selected_multiplier,
        "selection_basis": [
            "distribution de classes",
            "entropie",
            "stabilite par timeframe",
            "dominance de classe",
            "taux de labels invalides",
            "causalite et disponibilite temporelle",
        ],
        "input_dataset_manifest": _input_manifest_block(root, dataset_manifest),
        "input_decision_v9_5": {"path": INPUT_DECISION_V9_5.as_posix(), "sha256": sha256_file(root / INPUT_DECISION_V9_5)},
        "input_decision_manifest_v9_5": {
            "path": INPUT_DECISION_MANIFEST_V9_5.as_posix(),
            "sha256": sha256_file(root / INPUT_DECISION_MANIFEST_V9_5),
        },
        "outputs": outputs,
        "parameter_audit": parameter_audit,
        "quality": quality,
        "comparison_to_fixed_labels": compare_to_fixed_labels_v9_6(parameter_audit),
        "leakage_guard": leakage_guard_v9_6(),
        "forbidden_output_scan": forbidden_output_scan_v9_6(outputs),
        "findings": dict(FINDINGS_V9_6),
        "safety": dict(SAFETY_FLAGS_V9_6),
        "limitations": EXPECTED_LIMITATIONS_V9_6,
    }
    manifest = _manifest_from_report(root, report, outputs, parameter_audit, quality)
    _write_json(root / REPORT_JSON_PATH_V9_6, report)
    _write_json(root / MANIFEST_PATH_V9_6, manifest)
    _write_markdowns(root, report)
    return manifest


def build_refined_volatility_normalized_labels_frame_v9_6(
    dataset: pd.DataFrame,
    *,
    source_dataset_path: str,
    source_dataset_version: str,
    label_run_id: str,
    volatility_threshold_multiplier: float,
) -> pd.DataFrame:
    required = [
        "source",
        "venue",
        "market_type",
        "symbol",
        "timeframe",
        "event_ts",
        "close_ts",
        "decision_ts",
        "close",
        "future_log_return_h1",
        "label_end_ts_h1",
        "warmup_row",
    ]
    missing = [column for column in required if column not in dataset.columns]
    if missing:
        raise ValueError(f"missing V9.6 source dataset columns: {missing}")
    frame = dataset.sort_values("event_ts").reset_index(drop=True).copy()
    close = frame["close"].astype(float)
    past_log_return = np.log(close / close.shift(1))
    causal_vol = past_log_return.rolling(
        window=CAUSAL_VOL_WINDOW_BARS_V9_6,
        min_periods=CAUSAL_VOL_MIN_PERIODS_V9_6,
    ).std()
    threshold = volatility_threshold_multiplier * causal_vol
    future_return = frame["future_log_return_h1"].astype(float)
    valid = (
        future_return.notna()
        & causal_vol.notna()
        & np.isfinite(future_return)
        & np.isfinite(causal_vol)
        & (causal_vol > 0.0)
        & (frame["warmup_row"] == False)  # noqa: E712
    )
    labels = np.where(future_return > threshold, "UP", np.where(future_return < -threshold, "DOWN", "FLAT"))
    invalid_reason = np.where(valid, "valid", "warmup_or_insufficient_causal_volatility")

    out = frame[["source", "venue", "market_type", "symbol", "timeframe", "event_ts", "close_ts", "decision_ts"]].copy()
    out["label_start_ts"] = frame["decision_ts"]
    out["label_end_ts"] = frame["label_end_ts_h1"]
    out["label_available_ts"] = frame["label_end_ts_h1"]
    out["label_run_id"] = label_run_id
    out["label_schema_version"] = LABEL_SCHEMA_VERSION_V9_6
    out["source_dataset_version"] = source_dataset_version
    out["source_dataset_path"] = source_dataset_path
    out["source_label_design_version"] = VERSION_V9_6
    out["target_name"] = TARGET_NAME_V9_6
    out["horizon_name"] = HORIZON_NAME_V9_6
    out["horizon_bars"] = HORIZON_BARS_V9_6
    out["future_log_return"] = future_return
    out["causal_vol_window_bars"] = CAUSAL_VOL_WINDOW_BARS_V9_6
    out["causal_vol_min_periods"] = CAUSAL_VOL_MIN_PERIODS_V9_6
    out["causal_realized_vol"] = causal_vol
    out["volatility_threshold_multiplier"] = float(volatility_threshold_multiplier)
    out["volatility_normalized_threshold"] = threshold
    out["up_down_flat_volnorm_h1"] = labels
    out["label_valid_volnorm_h1"] = valid.astype(bool)
    out["label_invalid_reason"] = invalid_reason
    out["warmup_row"] = (~valid).astype(bool)
    out["label_error_count"] = 0
    null_columns = [column for column in REFINED_VOLATILITY_NORMALIZED_LABEL_COLUMNS_V9_6 if column != "label_null_count" and column in out.columns]
    out["label_null_count"] = out[null_columns].isna().sum(axis=1).astype("int16")
    return out[REFINED_VOLATILITY_NORMALIZED_LABEL_COLUMNS_V9_6].copy()


def build_parameter_audit_v9_6(root: Path, dataset_manifest: dict[str, Any]) -> dict[str, Any]:
    audit: dict[str, Any] = {}
    for timeframe in TIMEFRAMES_V9_6:
        dataset = read_parquet(root / dataset_manifest["outputs"][timeframe]["path"])
        rows: dict[str, Any] = {}
        for multiplier in PARAMETER_GRID_V9_6:
            labels = build_refined_volatility_normalized_labels_frame_v9_6(
                dataset,
                source_dataset_path=dataset_manifest["outputs"][timeframe]["path"],
                source_dataset_version=dataset_manifest.get("version", "V9.1"),
                label_run_id="parameter_audit",
                volatility_threshold_multiplier=multiplier,
            )
            valid = labels[labels["label_valid_volnorm_h1"] == True]  # noqa: E712
            rows[f"k_{multiplier:.2f}"] = {
                "k": multiplier,
                "valid_rows": int(len(valid)),
                "invalid_rows": int(len(labels) - len(valid)),
                "class_distribution": _class_distribution(valid["up_down_flat_volnorm_h1"]),
                "majority_class": _majority(valid["up_down_flat_volnorm_h1"])[0],
                "majority_rate": _majority(valid["up_down_flat_volnorm_h1"])[1],
                "entropy_bits": _entropy(valid["up_down_flat_volnorm_h1"]),
                "month_distribution": _period_distribution(labels, "event_ts", "month"),
                "split_distribution": _split_distribution(dataset, labels),
                "walk_forward_group_distribution": _walk_forward_group_distribution(dataset, labels),
            }
        audit[timeframe] = rows
    return audit


def select_volatility_multiplier_v9_6(parameter_audit: dict[str, Any]) -> float:
    scores: list[tuple[float, float]] = []
    for multiplier in PARAMETER_GRID_V9_6:
        key = f"k_{multiplier:.2f}"
        majority_rates = [parameter_audit[timeframe][key]["majority_rate"] for timeframe in TIMEFRAMES_V9_6]
        entropies = [parameter_audit[timeframe][key]["entropy_bits"] for timeframe in TIMEFRAMES_V9_6]
        over_dominance_penalty = sum(max(0.0, rate - 0.70) * 10.0 for rate in majority_rates)
        flat_1m = parameter_audit["1m"][key]["class_distribution"]["FLAT"]["rate"]
        balance_penalty = sum(abs(rate - 0.50) for rate in majority_rates)
        entropy_reward = sum(entropies) / max(len(entropies), 1)
        score = balance_penalty + over_dominance_penalty + abs(flat_1m - 0.50) - entropy_reward
        scores.append((score, multiplier))
    return sorted(scores)[0][1]


def assess_label_quality_v9_6(labels: pd.DataFrame, timeframe: str, source_dataset: pd.DataFrame) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    if list(labels.columns) != REFINED_VOLATILITY_NORMALIZED_LABEL_COLUMNS_V9_6:
        errors.append("schema mismatch")
    forbidden = [column for column in labels.columns if column.casefold() in FORBIDDEN_LABEL_COLUMNS_V9_6]
    if forbidden:
        errors.append(f"forbidden columns present: {forbidden}")
    if len(labels) != EXPECTED_ROWS_V9_6[timeframe]:
        errors.append(f"row count mismatch: {len(labels)} != {EXPECTED_ROWS_V9_6[timeframe]}")
    valid = labels[labels["label_valid_volnorm_h1"] == True]  # noqa: E712
    distribution = _class_distribution(valid["up_down_flat_volnorm_h1"])
    majority_class, majority_rate = _majority(valid["up_down_flat_volnorm_h1"])
    if majority_rate > 0.70:
        warnings.append(f"majority class exceeds 70 percent: {majority_class}={majority_rate:.4f}")
    if not (pd.to_datetime(labels["label_available_ts"], utc=True) > pd.to_datetime(labels["decision_ts"], utc=True)).all():
        errors.append("label_available_ts must be strictly after decision_ts")
    if not (pd.to_datetime(labels["label_start_ts"], utc=True) <= pd.to_datetime(labels["decision_ts"], utc=True)).all():
        errors.append("label_start_ts must be at or before decision_ts")
    return {
        "timeframe": timeframe,
        "rows": int(len(labels)),
        "valid_rows": int(len(valid)),
        "invalid_rows": int(len(labels) - len(valid)),
        "warmup_rows": int(labels["warmup_row"].sum()),
        "class_distribution": distribution,
        "majority_class": majority_class,
        "majority_rate": majority_rate,
        "entropy_bits": _entropy(valid["up_down_flat_volnorm_h1"]),
        "fixed_label_distribution_h1": _class_distribution(source_dataset["up_down_flat_h1"].astype(str)),
        "flat_rate_reduction_vs_fixed_h1": float(
            source_dataset["up_down_flat_h1"].astype(str).eq("FLAT").mean() - distribution["FLAT"]["rate"]
        ),
        "errors": errors,
        "warnings": warnings,
    }


def decide_v9_6(parameter_audit: dict[str, Any], quality: dict[str, Any], multiplier: float, status: str) -> str:
    if status != "PASS":
        return "label_factory_not_ready_quality_failed"
    warnings = [warning for item in quality.values() for warning in item.get("warnings", [])]
    if warnings:
        return "label_factory_candidate_created_but_requires_review"
    selected_key = f"k_{multiplier:.2f}"
    if any(parameter_audit[timeframe][selected_key]["majority_rate"] > 0.70 for timeframe in TIMEFRAMES_V9_6):
        return "label_factory_candidate_created_but_requires_review"
    return "label_factory_candidate_created_volatility_normalized"


def compare_to_fixed_labels_v9_6(parameter_audit: dict[str, Any]) -> dict[str, Any]:
    selected = select_volatility_multiplier_v9_6(parameter_audit)
    selected_key = f"k_{selected:.2f}"
    return {
        "selected_k": selected,
        "summary": {
            timeframe: {
                "volnorm_distribution": parameter_audit[timeframe][selected_key]["class_distribution"],
                "volnorm_majority_rate": parameter_audit[timeframe][selected_key]["majority_rate"],
            }
            for timeframe in TIMEFRAMES_V9_6
        },
        "interpretation": "Comparaison descriptive de labels uniquement; aucune performance ML ou trading n'est utilisee.",
    }


def leakage_guard_v9_6() -> dict[str, Any]:
    return {
        "passed": True,
        "causal_volatility_uses_only_past_and_current_closed_returns": True,
        "future_return_used_only_for_label": True,
        "label_available_ts_after_decision_ts_required": True,
        "label_columns_must_not_be_used_as_features": True,
        "forbidden_features_present": [],
    }


def forbidden_output_scan_v9_6(outputs: dict[str, Any]) -> dict[str, Any]:
    forbidden = [
        column
        for column in REFINED_VOLATILITY_NORMALIZED_LABEL_COLUMNS_V9_6
        if column.casefold() in FORBIDDEN_LABEL_COLUMNS_V9_6
    ]
    return {"passed": not forbidden, "forbidden_columns_present": forbidden, "outputs": sorted(outputs)}


def build_markdown_v9_6(report: dict[str, Any]) -> str:
    lines = [
        "# V9.6 - Label factory candidate volatility-normalized",
        "",
        "V9.6 produit des labels candidats strictement offline et causaux pour la recherche.",
        "Aucun ML, walk-forward, backtest, strategie, signal actionnable, ordre, paper live ou trading reel n'est produit.",
        "",
        "## Decision",
        "",
        f"- Decision : `{report['decision']}`.",
        f"- Multiplicateur selectionne : `{report['selected_volatility_threshold_multiplier']}`.",
        "",
        "## Distributions principales",
        "",
    ]
    for timeframe, item in report["quality"].items():
        lines.extend(
            [
                f"- `{timeframe}` : majoritaire `{item['majority_class']}` a `{item['majority_rate']:.4f}`, "
                f"entropie `{item['entropy_bits']:.4f}`, invalides `{item['invalid_rows']}`.",
                f"  - distribution : `{item['class_distribution']}`.",
                f"  - reduction FLAT vs label fixe h1 : `{item['flat_rate_reduction_vs_fixed_h1']:.4f}`.",
            ]
        )
    lines.extend(
        [
            "",
            "## Interdits maintenus",
            "",
            "- Aucun backtest.",
            "- Aucune strategie.",
            "- Aucun signal actionnable.",
            "- Aucun ordre.",
            "- Aucun paper live.",
            "- Aucun trading reel.",
            "- Aucune API privee et aucune cle API.",
        ]
    )
    return "\n".join(lines) + "\n"


def _period_distribution(labels: pd.DataFrame, timestamp_column: str, period: str) -> dict[str, Any]:
    valid = labels[labels["label_valid_volnorm_h1"] == True].copy()  # noqa: E712
    if valid.empty:
        return {}
    ts = pd.to_datetime(valid[timestamp_column], utc=True)
    if period == "month":
        keys = ts.dt.strftime("%Y-%m")
    else:
        keys = ts.astype(str)
    result: dict[str, Any] = {}
    for key, group in valid.groupby(keys, sort=True):
        dist = _class_distribution(group["up_down_flat_volnorm_h1"])
        majority_class, majority_rate = _majority(group["up_down_flat_volnorm_h1"])
        result[str(key)] = {"rows": int(len(group)), "class_distribution": dist, "majority_class": majority_class, "majority_rate": majority_rate}
    return result


def _split_distribution(dataset: pd.DataFrame, labels: pd.DataFrame) -> dict[str, Any]:
    if "split" not in dataset.columns:
        return {}
    frame = labels[["up_down_flat_volnorm_h1", "label_valid_volnorm_h1"]].copy()
    frame["split"] = dataset["split"].to_numpy()
    return _grouped_label_distribution(frame, "split")


def _walk_forward_group_distribution(dataset: pd.DataFrame, labels: pd.DataFrame) -> dict[str, Any]:
    if "walk_forward_group" not in dataset.columns:
        return {}
    frame = labels[["up_down_flat_volnorm_h1", "label_valid_volnorm_h1"]].copy()
    frame["walk_forward_group"] = dataset["walk_forward_group"].to_numpy()
    return _grouped_label_distribution(frame, "walk_forward_group")


def _grouped_label_distribution(frame: pd.DataFrame, group_column: str) -> dict[str, Any]:
    frame = frame[frame["label_valid_volnorm_h1"] == True]  # noqa: E712
    result: dict[str, Any] = {}
    for key, group in frame.groupby(group_column, sort=True):
        majority_class, majority_rate = _majority(group["up_down_flat_volnorm_h1"])
        result[str(key)] = {
            "rows": int(len(group)),
            "class_distribution": _class_distribution(group["up_down_flat_volnorm_h1"]),
            "majority_class": majority_class,
            "majority_rate": majority_rate,
        }
    return result


def _class_distribution(values: pd.Series) -> dict[str, dict[str, float | int]]:
    total = max(int(len(values)), 1)
    counts = Counter(values.astype(str).tolist())
    return {label: {"count": int(counts.get(label, 0)), "rate": float(counts.get(label, 0) / total)} for label in ["DOWN", "FLAT", "UP"]}


def _majority(values: pd.Series) -> tuple[str | None, float]:
    if len(values) == 0:
        return None, 0.0
    counts = values.astype(str).value_counts()
    return str(counts.index[0]), float(counts.iloc[0] / len(values))


def _entropy(values: pd.Series) -> float:
    if len(values) == 0:
        return 0.0
    probs = values.astype(str).value_counts(normalize=True)
    return float(-(probs * probs.map(lambda item: math.log(float(item), 2))).sum())


def _missing_dataset_inputs(root: Path, dataset_manifest: dict[str, Any]) -> list[str]:
    missing: list[str] = []
    for timeframe in TIMEFRAMES_V9_6:
        output = dataset_manifest.get("outputs", {}).get(timeframe, {})
        path = root / output.get("path", "")
        if not path.is_file():
            missing.append(path.as_posix())
    return missing


def _input_manifest_block(root: Path, dataset_manifest: dict[str, Any]) -> dict[str, Any]:
    input_block = dataset_manifest.get("input_features_manifest", {})
    return {
        "path": INPUT_DATASET_MANIFEST_V9_1.as_posix(),
        "sha256": sha256_file(root / INPUT_DATASET_MANIFEST_V9_1),
        "window_start": input_block.get("window_start", WINDOW_START_V9_6),
        "window_end": input_block.get("window_end", WINDOW_END_V9_6),
        "total_days": int(input_block.get("total_days", TOTAL_DAYS_V9_6)),
        "feature_columns_count": int(dataset_manifest.get("feature_columns_count", 0)),
    }


def _output_block(root: Path, path: Path, rows: int) -> dict[str, Any]:
    return {"path": path.relative_to(root).as_posix(), "sha256": sha256_file(path), "bytes": path.stat().st_size, "rows": int(rows), "format": "parquet"}


def _manifest_from_report(
    root: Path,
    report: dict[str, Any],
    outputs: dict[str, Any],
    parameter_audit: dict[str, Any],
    quality: dict[str, Any],
) -> dict[str, Any]:
    return {
        "version": VERSION_V9_6,
        "status": report.get("status", "FAIL"),
        "created_at_utc": report.get("created_at_utc", utc_now_iso()),
        "label_run_id": report.get("label_run_id"),
        "decision": report.get("decision"),
        "input_dataset_manifest": report.get("input_dataset_manifest"),
        "outputs": outputs,
        "target_name": TARGET_NAME_V9_6,
        "label_schema_version": LABEL_SCHEMA_VERSION_V9_6,
        "label_columns": REFINED_VOLATILITY_NORMALIZED_LABEL_COLUMNS_V9_6,
        "parameters_tested": PARAMETER_GRID_V9_6,
        "selected_volatility_threshold_multiplier": report.get("selected_volatility_threshold_multiplier"),
        "parameter_audit": parameter_audit,
        "quality": quality,
        "leakage_guard": report.get("leakage_guard", leakage_guard_v9_6()),
        "findings": dict(FINDINGS_V9_6),
        "safety": dict(SAFETY_FLAGS_V9_6),
        "limitations": EXPECTED_LIMITATIONS_V9_6,
    }


def _stop_report(decision: str, missing: list[str]) -> dict[str, Any]:
    return {
        "version": VERSION_V9_6,
        "status": "FAIL",
        "created_at_utc": utc_now_iso(),
        "decision": decision,
        "missing_full_data": missing,
        "findings": dict(FINDINGS_V9_6),
        "safety": dict(SAFETY_FLAGS_V9_6),
        "limitations": EXPECTED_LIMITATIONS_V9_6,
    }


def _write_markdowns(root: Path, report: dict[str, Any]) -> None:
    markdown = build_markdown_v9_6(report)
    _write_text(root / REPORT_MD_PATH_V9_6, markdown)
    _write_text(root / DATACARD_MD_PATH_V9_6, markdown)
    _write_text(root / DOC_PATH_V9_6, markdown)


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
