from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, balanced_accuracy_score, f1_score

from galapagos.data.public_market.provenance import sha256_file, utc_now_iso
from galapagos.data.public_market.storage import read_parquet, write_parquet
from galapagos.datasets.ohlcv_trades_1y_window_validation import validate_ohlcv_trades_1y_offline_supervised_dataset_v8_4
from galapagos.datasets.schemas import MANIFEST_PATH_V8_4
from galapagos.ml.offline_baselines import fit_predict_model
from galapagos.ml.schemas import (
    ALLOWED_FEATURE_COLUMNS_V8_7,
    DOC_PATH_V8_7,
    EXPECTED_LIMITATIONS_V8_7,
    FORBIDDEN_FEATURE_EXACT_V8_7,
    FORBIDDEN_FEATURE_PREFIXES_V8_7,
    FORBIDDEN_METRIC_TERMS_V8_7,
    LABEL_SHUFFLE_RANDOM_SEED_V8_7,
    MANIFEST_PATH_V8_5,
    MANIFEST_PATH_V8_7,
    ML_SCHEMA_VERSION_V8_7,
    ML_SCORE_COLUMNS_V8_7,
    MODEL_NAMES_V8_7,
    REPORT_JSON_PATH_V8_7,
    REPORT_MD_PATH_V8_7,
    SAFETY_FLAGS_V8_7,
    SCORES_JSON_PATH_V8_7,
    SCORES_MD_PATH_V8_7,
    TARGET_NAME_V8_7,
    TIMEFRAMES_V8_7,
    VERSION_V8_7,
    WALK_FORWARD_FOLD_COLUMNS_V8_7,
    get_feature_columns_sha256_v8_7,
    get_strict_walk_forward_folds_path_v8_7,
    get_strict_walk_forward_score_path_v8_7,
)
from galapagos.ml.strict_walk_forward_metrics import (
    compute_strict_walk_forward_aggregate_metrics_v8_7,
    compute_strict_walk_forward_metrics_v8_7,
)
from galapagos.ml.strict_walk_forward_quality import assess_strict_walk_forward_quality_v8_7


WALK_FORWARD_POLICY_VERSION_V8_7 = "strict_walk_forward_v8_7_calendar_month_v1"
WALK_FORWARD_POLICY_V8_7 = {
    "grouping": "calendar_month",
    "initial_train_months": 6,
    "validation_months": 1,
    "test_months": 1,
    "step_months": 1,
    "purge_bars": 5,
    "embargo_bars": 5,
    "expanding_train": True,
    "shuffle": False,
}
ROBUSTNESS_MODELS_V8_7 = ["logistic_regression", "decision_tree_depth_2"]
EVALUATION_ROLES_V8_7 = ["validation", "test"]


def run_strict_walk_forward_validation_v8_7(
    root: Path = Path("."),
    *,
    validate_dataset: bool = True,
) -> dict[str, Any]:
    root = root.resolve()
    if validate_dataset:
        _validate_dataset_layer(root)

    dataset_manifest = load_v8_4_dataset_manifest(root)
    window = _input_window(dataset_manifest)
    window_start = window["window_start"]
    window_end = window["window_end"]
    created_at = utc_now_iso()
    run_id = f"v8_7_{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}_{uuid.uuid4().hex[:8]}"

    outputs: dict[str, dict[str, Any]] = {"scores": {}, "folds": {}}
    input_datasets: dict[str, dict[str, Any]] = {}
    folds_manifest: dict[str, list[dict[str, Any]]] = {}
    metrics: dict[str, Any] = {}
    aggregate_metrics: dict[str, Any] = {}
    label_shuffle: dict[str, Any] = {}
    quality: dict[str, Any] = {}
    status = "PASS"

    for timeframe in TIMEFRAMES_V8_7:
        dataset_path = input_dataset_path(root, timeframe, dataset_manifest)
        dataset_sha = sha256_file(dataset_path)
        dataset = read_parquet(dataset_path)
        dataset = dataset.sort_values("event_ts").reset_index(drop=True)
        folds = build_strict_walk_forward_folds_v8_7(dataset, window_start, window_end)
        scores = build_strict_walk_forward_scores_v8_7(
            dataset,
            folds,
            dataset_sha256=dataset_sha,
            ml_run_id=run_id,
        )
        fold_metrics = compute_strict_walk_forward_metrics_v8_7(scores)
        metrics.update(fold_metrics)
        aggregate_metrics.update(compute_strict_walk_forward_aggregate_metrics_v8_7(fold_metrics))
        label_shuffle.update(compute_label_shuffle_falsification_v8_7(dataset, folds, fold_metrics))

        score_path = score_output_path(root, timeframe, window_start, window_end)
        folds_path = folds_output_path(root, timeframe, window_start, window_end)
        write_parquet(scores, score_path)
        write_parquet(folds, folds_path)

        input_datasets[timeframe] = _input_block(root, dataset_path, dataset_sha, len(dataset))
        outputs["scores"][timeframe] = _output_block(root, score_path, len(scores))
        outputs["folds"][timeframe] = _output_block(root, folds_path, len(folds))
        folds_manifest[timeframe] = summarize_folds_v8_7(folds)
        quality[timeframe] = assess_strict_walk_forward_quality_v8_7(dataset, folds, scores, timeframe)
        if quality[timeframe]["errors"]:
            status = "FAIL"

    comparison_to_static_split = compare_to_static_split_v8_5(root, aggregate_metrics)
    feature_leakage_scan = scan_strict_walk_forward_feature_leakage_v8_7(ALLOWED_FEATURE_COLUMNS_V8_7)
    metric_forbidden_scan = scan_strict_walk_forward_metric_forbidden_terms_v8_7(
        {
            "metrics": metrics,
            "aggregate_metrics": aggregate_metrics,
            "label_shuffle_falsification": label_shuffle,
            "comparison_to_static_split_v8_5": comparison_to_static_split,
        }
    )
    if feature_leakage_scan["forbidden_feature_columns_present"] or metric_forbidden_scan["forbidden_terms_present"]:
        status = "FAIL"

    manifest = {
        "version": VERSION_V8_7,
        "status": status,
        "created_at_utc": created_at,
        "walk_forward_run_id": run_id,
        "input_dataset_manifest": {
            "path": MANIFEST_PATH_V8_4.as_posix(),
            "sha256": sha256_file(root / MANIFEST_PATH_V8_4),
            "window_start": window_start,
            "window_end": window_end,
            "total_days": int(window["total_days"]),
            "feature_columns_count": int(dataset_manifest["feature_columns_count"]),
        },
        "input_datasets": input_datasets,
        "walk_forward_policy": WALK_FORWARD_POLICY_V8_7,
        "folds": folds_manifest,
        "outputs": outputs,
        "target_name": TARGET_NAME_V8_7,
        "feature_columns": ALLOWED_FEATURE_COLUMNS_V8_7,
        "feature_columns_count": len(ALLOWED_FEATURE_COLUMNS_V8_7),
        "models": MODEL_NAMES_V8_7,
        "metrics": metrics,
        "aggregate_metrics": aggregate_metrics,
        "label_shuffle_falsification": label_shuffle,
        "comparison_to_static_split_v8_5": comparison_to_static_split,
        "feature_leakage_scan": feature_leakage_scan,
        "metric_forbidden_scan": metric_forbidden_scan,
        "findings": {
            "robust_edge_claimed": False,
            "strategy_validated": False,
            "backtest_performed": False,
            "actionable_signal_produced": False,
            "walk_forward_validated_for_trading": False,
            "warnings": _collect_warnings(aggregate_metrics, label_shuffle, comparison_to_static_split),
        },
        "quality": quality,
        "safety": SAFETY_FLAGS_V8_7,
        "limitations": EXPECTED_LIMITATIONS_V8_7,
    }
    _write_json(root / MANIFEST_PATH_V8_7, manifest)
    _write_json(root / REPORT_JSON_PATH_V8_7, manifest)
    _write_json(root / SCORES_JSON_PATH_V8_7, _scores_report(manifest))
    markdown = build_strict_walk_forward_markdown_v8_7(manifest)
    _write_text(root / REPORT_MD_PATH_V8_7, markdown)
    _write_text(root / SCORES_MD_PATH_V8_7, markdown)
    _write_text(root / DOC_PATH_V8_7, markdown)
    _update_project_state(root, manifest)
    return manifest


def load_v8_4_dataset_manifest(root: Path = Path(".")) -> dict[str, Any]:
    return json.loads((root.resolve() / MANIFEST_PATH_V8_4).read_text(encoding="utf-8"))


def input_dataset_path(root: Path, timeframe: str, manifest: dict[str, Any] | None = None) -> Path:
    manifest = manifest or load_v8_4_dataset_manifest(root)
    return root.resolve() / manifest["outputs"][timeframe]["path"]


def score_output_path(root: Path, timeframe: str, window_start: str | None = None, window_end: str | None = None) -> Path:
    if window_start is None or window_end is None:
        window = _input_window(load_v8_4_dataset_manifest(root))
        window_start = window["window_start"]
        window_end = window["window_end"]
    return get_strict_walk_forward_score_path_v8_7(root.resolve(), timeframe, window_start, window_end)


def folds_output_path(root: Path, timeframe: str, window_start: str | None = None, window_end: str | None = None) -> Path:
    if window_start is None or window_end is None:
        window = _input_window(load_v8_4_dataset_manifest(root))
        window_start = window["window_start"]
        window_end = window["window_end"]
    return get_strict_walk_forward_folds_path_v8_7(root.resolve(), timeframe, window_start, window_end)


def build_strict_walk_forward_folds_v8_7(dataset: pd.DataFrame, window_start: str, window_end: str) -> pd.DataFrame:
    event_ts = pd.to_datetime(dataset["event_ts"], utc=True)
    start = pd.Timestamp(f"{window_start}T00:00:00Z")
    end_exclusive = pd.Timestamp(f"{window_end}T00:00:00Z") + pd.Timedelta(days=1)
    fold_frames: list[pd.DataFrame] = []
    fold_order = 1
    offset = 0
    while True:
        train_start = start
        validation_start = start + pd.DateOffset(months=WALK_FORWARD_POLICY_V8_7["initial_train_months"] + offset)
        test_start = validation_start + pd.DateOffset(months=WALK_FORWARD_POLICY_V8_7["validation_months"])
        test_end = test_start + pd.DateOffset(months=WALK_FORWARD_POLICY_V8_7["test_months"])
        if test_end > end_exclusive:
            break
        fold_id = f"fold_{fold_order:02d}"
        fold = _fold_assignments(dataset, event_ts, fold_id, fold_order, train_start, validation_start, test_start, test_end)
        fold_frames.append(_apply_purge_embargo(fold))
        fold_order += 1
        offset += WALK_FORWARD_POLICY_V8_7["step_months"]
    if not fold_frames:
        return pd.DataFrame(columns=WALK_FORWARD_FOLD_COLUMNS_V8_7)
    return pd.concat(fold_frames, ignore_index=True)[WALK_FORWARD_FOLD_COLUMNS_V8_7]


def build_strict_walk_forward_scores_v8_7(
    dataset: pd.DataFrame,
    folds: pd.DataFrame,
    *,
    dataset_sha256: str,
    ml_run_id: str,
) -> pd.DataFrame:
    score_frames: list[pd.DataFrame] = []
    feature_columns_sha256 = get_feature_columns_sha256_v8_7()
    if folds.empty:
        return pd.DataFrame(columns=ML_SCORE_COLUMNS_V8_7)
    merged = folds.merge(
        dataset,
        on=["source", "venue", "market_type", "symbol", "timeframe", "event_ts"],
        how="left",
        validate="many_to_one",
    )
    merged = prepare_walk_forward_ml_frame_v8_7(merged)
    for fold_id, fold_frame in merged.groupby("fold_id", sort=True):
        train = fold_frame[fold_frame["fold_role"] == "train"]
        if train.empty:
            continue
        train_features = train[ALLOWED_FEATURE_COLUMNS_V8_7]
        train_target = train[TARGET_NAME_V8_7].astype(str)
        predict_features = fold_frame[ALLOWED_FEATURE_COLUMNS_V8_7]
        for model_name in MODEL_NAMES_V8_7:
            result = fit_predict_model(model_name, train_features, train_target, predict_features)
            scores = fold_frame[
                [
                    "source",
                    "venue",
                    "market_type",
                    "symbol",
                    "timeframe",
                    "event_ts",
                    "close_ts",
                    "decision_ts",
                    "fold_id",
                    "fold_role",
                    "fold_order",
                ]
            ].copy()
            scores["ml_run_id"] = ml_run_id
            scores["model_name"] = model_name
            scores["target_name"] = TARGET_NAME_V8_7
            scores["dataset_sha256"] = dataset_sha256
            scores["feature_columns_sha256"] = feature_columns_sha256
            scores["ml_schema_version"] = ML_SCHEMA_VERSION_V8_7
            scores["target_value"] = fold_frame[TARGET_NAME_V8_7].astype(str).to_numpy()
            scores["research_predicted_class"] = result.predicted_class.to_numpy()
            scores["research_probability_down"] = result.probabilities["DOWN"].to_numpy()
            scores["research_probability_flat"] = result.probabilities["FLAT"].to_numpy()
            scores["research_probability_up"] = result.probabilities["UP"].to_numpy()
            scores["prediction_available_ts"] = fold_frame["decision_ts"].to_numpy()
            scores["row_valid_for_ml"] = True
            scores["ml_null_count"] = scores.isna().sum(axis=1).astype(int)
            scores["ml_error_count"] = 0
            score_frames.append(scores[ML_SCORE_COLUMNS_V8_7])
    if not score_frames:
        return pd.DataFrame(columns=ML_SCORE_COLUMNS_V8_7)
    return pd.concat(score_frames, ignore_index=True)


def prepare_walk_forward_ml_frame_v8_7(frame: pd.DataFrame) -> pd.DataFrame:
    filtered = frame[
        (frame["label_valid_h1"] == True)  # noqa: E712
        & (frame["warmup_row"] == False)  # noqa: E712
        & (frame["is_embargoed"] == False)  # noqa: E712
        & (frame["is_purged"] == False)  # noqa: E712
    ].copy()
    return filtered.sort_values(["fold_order", "fold_role", "event_ts"]).reset_index(drop=True)


def summarize_folds_v8_7(folds: pd.DataFrame) -> list[dict[str, Any]]:
    summaries: list[dict[str, Any]] = []
    for (fold_id, fold_order), group in folds.groupby(["fold_id", "fold_order"], sort=True):
        role_bounds: dict[str, tuple[str, str, int]] = {}
        for role in ["train", "validation", "test"]:
            role_group = group[group["fold_role"] == role]
            timestamps = pd.to_datetime(role_group["event_ts"], utc=True)
            role_bounds[role] = (
                timestamps.min().date().isoformat(),
                timestamps.max().date().isoformat(),
                int(len(role_group[(role_group["is_purged"] == False) & (role_group["is_embargoed"] == False)])),  # noqa: E712
            )
        summaries.append(
            {
                "fold_id": fold_id,
                "fold_order": int(fold_order),
                "train_start": role_bounds["train"][0],
                "train_end": role_bounds["train"][1],
                "validation_start": role_bounds["validation"][0],
                "validation_end": role_bounds["validation"][1],
                "test_start": role_bounds["test"][0],
                "test_end": role_bounds["test"][1],
                "train_rows": role_bounds["train"][2],
                "validation_rows": role_bounds["validation"][2],
                "test_rows": role_bounds["test"][2],
                "purged_rows": int(group["is_purged"].eq(True).sum()),
                "embargoed_rows": int(group["is_embargoed"].eq(True).sum()),
            }
        )
    return summaries


def compute_label_shuffle_falsification_v8_7(
    dataset: pd.DataFrame,
    folds: pd.DataFrame,
    original_metrics: dict[str, Any],
) -> dict[str, Any]:
    falsification: dict[str, Any] = {}
    merged = folds.merge(
        dataset,
        on=["source", "venue", "market_type", "symbol", "timeframe", "event_ts"],
        how="left",
        validate="many_to_one",
    )
    merged = prepare_walk_forward_ml_frame_v8_7(merged)
    for (fold_id, fold_order), fold_frame in merged.groupby(["fold_id", "fold_order"], sort=True):
        train = fold_frame[fold_frame["fold_role"] == "train"]
        if train.empty:
            continue
        rng = np.random.default_rng(LABEL_SHUFFLE_RANDOM_SEED_V8_7 + int(fold_order))
        shuffled_train_target = pd.Series(rng.permutation(train[TARGET_NAME_V8_7].astype(str).to_numpy()), index=train.index)
        predict_frame = fold_frame[fold_frame["fold_role"].isin(EVALUATION_ROLES_V8_7)]
        for model_name in ROBUSTNESS_MODELS_V8_7:
            result = fit_predict_model(
                model_name,
                train[ALLOWED_FEATURE_COLUMNS_V8_7],
                shuffled_train_target,
                predict_frame[ALLOWED_FEATURE_COLUMNS_V8_7],
            )
            for role in EVALUATION_ROLES_V8_7:
                role_frame = predict_frame[predict_frame["fold_role"] == role]
                y_true = role_frame[TARGET_NAME_V8_7].astype(str)
                y_pred = result.predicted_class.loc[role_frame.index].astype(str)
                shuffled = _classification_summary(y_true, y_pred)
                timeframe = str(role_frame["timeframe"].iloc[0]) if not role_frame.empty else str(fold_frame["timeframe"].iloc[0])
                original = original_metrics[f"{timeframe}.{model_name}.{fold_id}.{role}"]
                no_clear_edge = original["accuracy"] <= shuffled["accuracy"] or original["macro_f1"] <= shuffled["macro_f1"]
                falsification[f"{timeframe}.{model_name}.{fold_id}.{role}"] = {
                    "timeframe": timeframe,
                    "model_name": model_name,
                    "fold_id": fold_id,
                    "fold_role": role,
                    "random_seed": LABEL_SHUFFLE_RANDOM_SEED_V8_7 + int(fold_order),
                    "shuffle_scope": "train_labels_only",
                    "validation_test_contaminated": False,
                    "original_accuracy": float(original["accuracy"]),
                    "original_macro_f1": float(original["macro_f1"]),
                    "shuffled_accuracy": shuffled["accuracy"],
                    "shuffled_macro_f1": shuffled["macro_f1"],
                    "accuracy_delta_original_minus_shuffled": _round_metric(original["accuracy"] - shuffled["accuracy"]),
                    "macro_f1_delta_original_minus_shuffled": _round_metric(original["macro_f1"] - shuffled["macro_f1"]),
                    "no_clear_edge_vs_shuffled_labels": bool(no_clear_edge),
                }
    return falsification


def compare_to_static_split_v8_5(root: Path, aggregate_metrics: dict[str, Any]) -> dict[str, Any]:
    manifest_path = root / MANIFEST_PATH_V8_5
    if not manifest_path.exists():
        return {
            "status": "SKIPPED",
            "source_manifest_path": MANIFEST_PATH_V8_5.as_posix(),
            "descriptive_only": True,
            "not_same_validation_design": True,
            "comparisons": {},
            "warnings": ["V8.5 static split manifest absent; comparison skipped."],
        }
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    comparisons: dict[str, Any] = {}
    for key, aggregate in sorted(aggregate_metrics.items()):
        timeframe = aggregate["timeframe"]
        model_name = aggregate["model_name"]
        static_key = f"{timeframe}.{model_name}.test"
        static = manifest.get("metrics", {}).get(static_key)
        if not isinstance(static, dict):
            continue
        comparisons[key] = {
            "timeframe": timeframe,
            "model_name": model_name,
            "v8_7_mean_test_accuracy": aggregate["mean_test_accuracy"],
            "v8_5_static_test_accuracy": static.get("accuracy"),
            "accuracy_delta_v8_7_minus_v8_5_static": _nullable_delta(aggregate["mean_test_accuracy"], static.get("accuracy")),
            "v8_7_mean_test_macro_f1": aggregate["mean_test_macro_f1"],
            "v8_5_static_test_macro_f1": static.get("macro_f1"),
            "macro_f1_delta_v8_7_minus_v8_5_static": _nullable_delta(aggregate["mean_test_macro_f1"], static.get("macro_f1")),
            "descriptive_only": True,
            "not_same_validation_design": True,
        }
    return {
        "status": "PASS",
        "source_manifest_path": MANIFEST_PATH_V8_5.as_posix(),
        "source_manifest_sha256": sha256_file(manifest_path),
        "descriptive_only": True,
        "not_same_validation_design": True,
        "compared_metrics": ["accuracy", "macro_f1"],
        "comparisons": comparisons,
        "warnings": ["V8.5 static split and V8.7 strict walk-forward are not identical validation designs."],
    }


def scan_strict_walk_forward_feature_leakage_v8_7(feature_columns: list[str]) -> dict[str, Any]:
    exact = {term.casefold() for term in FORBIDDEN_FEATURE_EXACT_V8_7}
    prefixes = tuple(term.casefold() for term in FORBIDDEN_FEATURE_PREFIXES_V8_7)
    forbidden = []
    for column in feature_columns:
        folded = str(column).casefold()
        if folded in exact or folded.startswith(prefixes):
            forbidden.append(str(column))
    return {
        "feature_columns_checked": list(feature_columns),
        "forbidden_feature_columns_present": forbidden,
        "feature_leakage_detected": bool(forbidden),
    }


def scan_strict_walk_forward_metric_forbidden_terms_v8_7(payload: Any) -> dict[str, Any]:
    text = json.dumps(payload, ensure_ascii=False, sort_keys=True).casefold()
    present = [term for term in FORBIDDEN_METRIC_TERMS_V8_7 if term in text]
    return {
        "forbidden_terms_present": present,
        "metric_forbidden_terms_detected": bool(present),
    }


def build_strict_walk_forward_markdown_v8_7(manifest: dict[str, Any]) -> str:
    rows = "\n".join(
        f"- `{timeframe}` : `{len(folds)}` folds, scores `{manifest['outputs']['scores'][timeframe]['rows']}` lignes."
        for timeframe, folds in manifest["folds"].items()
    )
    return "\n".join(
        [
            "# Validation walk-forward offline stricte - V8.7",
            "",
            "## Objectif",
            "",
            "V8.7 applique une validation walk-forward offline stricte sur le dataset V8.4 OHLCV + aggTrades 1 an.",
            "Les modeles sont des baselines de recherche par fold et les scores `research_*` restent non actionnables.",
            "",
            "## Politique walk-forward",
            "",
            f"- Grouping : `{manifest['walk_forward_policy']['grouping']}`.",
            f"- Train initial : `{manifest['walk_forward_policy']['initial_train_months']}` mois.",
            f"- Validation : `{manifest['walk_forward_policy']['validation_months']}` mois.",
            f"- Test : `{manifest['walk_forward_policy']['test_months']}` mois.",
            f"- Step : `{manifest['walk_forward_policy']['step_months']}` mois.",
            f"- Purge / embargo : `{manifest['walk_forward_policy']['purge_bars']}` / `{manifest['walk_forward_policy']['embargo_bars']}` barres.",
            f"- Shuffle : `{manifest['walk_forward_policy']['shuffle']}`.",
            "",
            "## Outputs",
            "",
            rows,
            "",
            "## Controles",
            "",
            "- Cible unique : `up_down_flat_h1`.",
            "- Les lignes warmup, labels invalides, purged et embargoed sont exclues des entrainements et evaluations.",
            "- Les colonnes futures, labels, target, split, walk-forward et fold ne sont jamais utilisees comme features.",
            "- Les metriques sont descriptives et non actionnables.",
            "- La validation walk-forward offline n'est pas un backtest.",
            "- Les comparaisons avec V8.5 sont descriptives.",
            "- V8.7 ne valide aucune strategie.",
            "- V8.7 ne produit aucun backtest.",
            "- V8.7 ne produit aucun signal de trading.",
            "- V8.7 ne produit aucun ordre.",
            "- V8.7 n'autorise aucun paper live.",
            "- V8.7 n'autorise aucun trading reel.",
            "- Aucune metrique de trading interdite ou mesure d'execution n'est calculee.",
            "",
            "## Limitations",
            "",
            *[f"- {item}" for item in manifest["limitations"]],
        ]
    ) + "\n"


def _fold_assignments(
    dataset: pd.DataFrame,
    event_ts: pd.Series,
    fold_id: str,
    fold_order: int,
    train_start: pd.Timestamp,
    validation_start: pd.Timestamp,
    test_start: pd.Timestamp,
    test_end: pd.Timestamp,
) -> pd.DataFrame:
    train_mask = (event_ts >= train_start) & (event_ts < validation_start)
    validation_mask = (event_ts >= validation_start) & (event_ts < test_start)
    test_mask = (event_ts >= test_start) & (event_ts < test_end)
    frames = []
    for role, mask in [("train", train_mask), ("validation", validation_mask), ("test", test_mask)]:
        role_frame = dataset.loc[
            mask,
            ["source", "venue", "market_type", "symbol", "timeframe", "event_ts"],
        ].copy()
        role_frame["fold_id"] = fold_id
        role_frame["fold_role"] = role
        role_frame["fold_order"] = fold_order
        role_frame["is_embargoed"] = False
        role_frame["is_purged"] = False
        role_frame["walk_forward_policy_version"] = WALK_FORWARD_POLICY_VERSION_V8_7
        frames.append(role_frame)
    return pd.concat(frames, ignore_index=True)


def _apply_purge_embargo(fold: pd.DataFrame) -> pd.DataFrame:
    frame = fold.sort_values(["fold_role", "event_ts"]).reset_index(drop=True)
    purge = int(WALK_FORWARD_POLICY_V8_7["purge_bars"])
    embargo = int(WALK_FORWARD_POLICY_V8_7["embargo_bars"])
    for role in ["train", "validation"]:
        index = frame[frame["fold_role"] == role].sort_values("event_ts").tail(purge).index
        frame.loc[index, "is_purged"] = True
    for role in ["validation", "test"]:
        index = frame[frame["fold_role"] == role].sort_values("event_ts").head(embargo).index
        frame.loc[index, "is_embargoed"] = True
    return frame.sort_values(["fold_order", "event_ts", "fold_role"]).reset_index(drop=True)


def _classification_summary(y_true: pd.Series, y_pred: pd.Series) -> dict[str, float]:
    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "balanced_accuracy": float(balanced_accuracy_score(y_true, y_pred)),
        "macro_f1": float(f1_score(y_true, y_pred, average="macro", zero_division=0)),
    }


def _collect_warnings(aggregate_metrics: dict[str, Any], label_shuffle: dict[str, Any], comparison: dict[str, Any]) -> list[str]:
    warnings: list[str] = []
    for key, payload in aggregate_metrics.items():
        if payload.get("fold_concentration_warnings"):
            warnings.append(f"{key}: fold concentration warning")
    no_clear = [key for key, payload in label_shuffle.items() if payload.get("no_clear_edge_vs_shuffled_labels") is True]
    if no_clear:
        warnings.append(f"no clear edge vs shuffled labels in {len(no_clear)} fold/model/role cases")
    warnings.extend(comparison.get("warnings", []))
    return warnings


def _validate_dataset_layer(root: Path) -> None:
    result = validate_ohlcv_trades_1y_offline_supervised_dataset_v8_4(root)
    if not result["passed"]:
        raise RuntimeError(f"V8.4 dataset validation failed before V8.7: {result['errors']}")


def _input_window(manifest: dict[str, Any]) -> dict[str, Any]:
    return manifest["input_features_manifest"]


def _input_block(root: Path, path: Path, sha256: str, rows: int) -> dict[str, Any]:
    return {"path": str(path.relative_to(root)), "sha256": sha256, "rows": int(rows)}


def _output_block(root: Path, path: Path, rows: int) -> dict[str, Any]:
    return {
        "path": str(path.relative_to(root)),
        "sha256": sha256_file(path),
        "bytes": path.stat().st_size,
        "rows": int(rows),
        "format": "parquet",
    }


def _scores_report(manifest: dict[str, Any]) -> dict[str, Any]:
    return {
        "version": manifest["version"],
        "walk_forward_run_id": manifest["walk_forward_run_id"],
        "outputs": manifest["outputs"],
        "metrics": manifest["metrics"],
        "aggregate_metrics": manifest["aggregate_metrics"],
        "label_shuffle_falsification": manifest["label_shuffle_falsification"],
        "comparison_to_static_split_v8_5": manifest["comparison_to_static_split_v8_5"],
    }


def _update_project_state(root: Path, manifest: dict[str, Any]) -> None:
    state_path = root / "reports/PROJECT_STATE.json"
    state = json.loads(state_path.read_text(encoding="utf-8")) if state_path.exists() else {}
    window = manifest["input_dataset_manifest"]
    score_rows = {timeframe: payload["rows"] for timeframe, payload in manifest["outputs"]["scores"].items()}
    fold_counts = {timeframe: len(payload) for timeframe, payload in manifest["folds"].items()}
    state.update(
        {
            "last_validated_version": "V8.6",
            "candidate_version": "V8.7",
            "candidate_status": "pending_external_audit",
            "direction": "strict walk-forward offline validation",
            "strict_walk_forward_validation_v8_7_created": True,
            "strict_walk_forward_window_start_v8_7": window["window_start"],
            "strict_walk_forward_window_end_v8_7": window["window_end"],
            "strict_walk_forward_total_days_v8_7": window["total_days"],
            "strict_walk_forward_feature_columns_count_v8_7": manifest["feature_columns_count"],
            "strict_walk_forward_score_rows_v8_7": score_rows,
            "strict_walk_forward_folds_count_v8_7": fold_counts,
            "backtest_v8_7_created": False,
            "strategy_v8_7_created": False,
            "signal_v8_7_created": False,
            "orders_v8_7_created": False,
            "paper_live_v8_7_created": False,
            "trading_v8_7_created": False,
            "persistent_model_v8_7_created": False,
            "backtest_enabled": False,
            "strategy_enabled": False,
            "paper_live_enabled": False,
            "orders_enabled": False,
            "trading_enabled": False,
            "execution_enabled": False,
            "api_key_used": False,
            "private_endpoint_used": False,
            "authentication_used": False,
        }
    )
    _write_json(state_path, state)
    _write_json(root / "reports/current/latest_metrics.json", _latest_metrics(manifest))
    _write_text(root / "reports/PROJECT_STATE.md", _project_state_markdown(manifest))
    _write_text(root / "reports/current/latest_metrics.md", _latest_metrics_markdown(manifest))
    _write_text(root / "reports/current/latest_summary.md", _latest_summary_markdown(manifest))
    _write_text(root / "README.md", _readme_markdown(manifest))


def _latest_metrics(manifest: dict[str, Any]) -> dict[str, Any]:
    window = manifest["input_dataset_manifest"]
    return {
        "last_validated_version": "V8.6",
        "candidate_version": "V8.7",
        "candidate_status": "pending_external_audit",
        "direction": "strict walk-forward offline validation",
        "window_start": window["window_start"],
        "window_end": window["window_end"],
        "total_days": window["total_days"],
        "feature_columns_count": manifest["feature_columns_count"],
        "walk_forward_policy": manifest["walk_forward_policy"],
        "folds_count_by_timeframe": {timeframe: len(payload) for timeframe, payload in manifest["folds"].items()},
        "score_rows_by_timeframe": {timeframe: payload["rows"] for timeframe, payload in manifest["outputs"]["scores"].items()},
        "backtest_enabled": False,
        "strategy_enabled": False,
        "signal_created": False,
        "orders_enabled": False,
        "trading_enabled": False,
        "paper_live_enabled": False,
        "persistent_model_created": False,
        "external_validation_required": True,
    }


def _project_state_markdown(manifest: dict[str, Any]) -> str:
    window = manifest["input_dataset_manifest"]
    return f"""# Etat du Projet : V8.6 validee + candidat V8.7

- **Derniere version validee** : V8.6.
- **Version candidate** : V8.7.
- **Statut candidate** : `pending_external_audit`.
- **Direction** : strict walk-forward offline validation.

## Candidat V8.7

- Fenetre : `{window['window_start']}` -> `{window['window_end']}`.
- Nombre de jours : `{window['total_days']}`.
- Feature columns : `{manifest['feature_columns_count']}`.
- Folds par timeframe : `{ {timeframe: len(payload) for timeframe, payload in manifest['folds'].items()} }`.
- Scores par timeframe : `{ {timeframe: payload['rows'] for timeframe, payload in manifest['outputs']['scores'].items()} }`.
- Validation offline uniquement, sans backtest.

## Clause De Securite

- Aucun trading reel.
- Aucun paper live.
- Aucun ordre.
- Aucun backtest.
- Aucune strategie.
- Aucun signal de trading.
- Aucun modele persistant.
- Aucune API privee.
- Aucune cle API.
- V8.7 reste non validee avant audit externe.
"""


def _latest_metrics_markdown(manifest: dict[str, Any]) -> str:
    window = manifest["input_dataset_manifest"]
    folds = "\n".join(f"- {timeframe}: `{len(payload)}`" for timeframe, payload in manifest["folds"].items())
    scores = "\n".join(f"- {timeframe}: `{payload['rows']}`" for timeframe, payload in manifest["outputs"]["scores"].items())
    return f"""# Latest Metrics V8.7

- Derniere version validee : V8.6.
- Candidate : V8.7.
- Statut : `pending_external_audit`.
- Direction : strict walk-forward offline validation.
- Fenetre : `{window['window_start']}` -> `{window['window_end']}`.
- Total jours : `{window['total_days']}`.
- Feature columns : `{manifest['feature_columns_count']}`.

## Folds

{folds}

## Scores

{scores}

Aucun backtest, aucune strategie, aucun signal de trading, aucun ordre, aucun modele persistant et aucun trading reel.
"""


def _latest_summary_markdown(manifest: dict[str, Any]) -> str:
    window = manifest["input_dataset_manifest"]
    return f"""# Latest Summary V8.7

V8.6 est la derniere version validee par audit externe.

V8.7 est la candidate courante. Elle produit une validation walk-forward offline stricte sur le dataset V8.4 OHLCV + public trades 1 an, avec folds deterministes, purge/embargo, scores `research_*`, metriques descriptives par fold, falsification par labels train melanges et comparaison descriptive avec V8.5 static split.

Fenetre : `{window['window_start']}` -> `{window['window_end']}`.

Total jours : `{window['total_days']}`.

Feature columns : `{manifest['feature_columns_count']}`.

Aucun trading, aucun paper live, aucun ordre, aucun backtest, aucune strategie, aucun signal de trading, aucun modele persistant et aucun claim de rentabilite.

V8.7 reste `pending_external_audit`.
"""


def _readme_markdown(manifest: dict[str, Any]) -> str:
    window = manifest["input_dataset_manifest"]
    return f"""# Projet Galapagos

- Derniere version validee : V8.6.
- Candidate : V8.7, strict walk-forward offline validation.

V8.7 applique une validation walk-forward offline stricte sur le dataset V8.4 OHLCV + aggTrades 1 an avec des baselines ML simples par fold et des scores de recherche `research_*`.

Fenetre : `{window['window_start']}` -> `{window['window_end']}`, `{window['total_days']}` jours.

Feature columns : `{manifest['feature_columns_count']}`.

Aucun backtest, aucune strategie, aucun signal de trading, aucun ordre, aucun paper live, aucun trading reel et aucun modele persistant.

## Commandes V8.7

```bash
python scripts/run_strict_walk_forward_validation_v8_7.py
python scripts/validate_strict_walk_forward_validation_v8_7.py
python scripts/release_audit_lite_zip_v8_7.py
python scripts/audit_audit_lite_zip_v8_7.py --zip projet-galapagos-v8.7-audit-lite.zip
python scripts/smoke_audit_lite_zip_v8_7.py --zip projet-galapagos-v8.7-audit-lite.zip
```
"""


def _nullable_delta(left: Any, right: Any) -> float | None:
    if not isinstance(left, (int, float)) or not isinstance(right, (int, float)):
        return None
    return _round_metric(float(left) - float(right))


def _round_metric(value: Any) -> float:
    return round(float(value), 6)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
