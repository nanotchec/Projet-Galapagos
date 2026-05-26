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
from galapagos.datasets.refined_ohlcv_trades_window_validation import validate_refined_ohlcv_trades_offline_supervised_dataset_v9_1
from galapagos.datasets.schemas import MANIFEST_PATH_V9_1
from galapagos.ml.offline_baselines import fit_predict_model
from galapagos.ml.refined_strict_walk_forward_metrics import (
    compute_refined_strict_walk_forward_aggregate_metrics_v9_3,
    compute_refined_strict_walk_forward_metrics_v9_3,
)
from galapagos.ml.refined_strict_walk_forward_quality import assess_refined_strict_walk_forward_quality_v9_3
from galapagos.ml.schemas import (
    ALLOWED_FEATURE_COLUMNS_V9_3,
    DOC_PATH_V9_3,
    EXPECTED_LIMITATIONS_V9_3,
    FORBIDDEN_FEATURE_EXACT_V9_3,
    FORBIDDEN_FEATURE_PREFIXES_V9_3,
    FORBIDDEN_METRIC_TERMS_V9_3,
    LABEL_SHUFFLE_RANDOM_SEED_V9_3,
    MANIFEST_PATH_V9_2,
    MANIFEST_PATH_V9_3,
    ML_SCHEMA_VERSION_V9_3,
    ML_SCORE_COLUMNS_V9_3,
    MODEL_NAMES_V9_3,
    REPORT_JSON_PATH_V9_3,
    REPORT_MD_PATH_V9_3,
    SAFETY_FLAGS_V9_3,
    SCORES_JSON_PATH_V9_3,
    SCORES_MD_PATH_V9_3,
    TARGET_NAME_V9_3,
    TIMEFRAMES_V9_3,
    VERSION_V9_3,
    WALK_FORWARD_FOLD_COLUMNS_V9_3,
    get_feature_columns_sha256_v9_3,
    get_refined_strict_walk_forward_folds_path_v9_3,
    get_refined_strict_walk_forward_score_path_v9_3,
)


WALK_FORWARD_POLICY_VERSION_V9_3 = "refined_strict_walk_forward_v9_3_calendar_month_v1"
WALK_FORWARD_POLICY_V9_3 = {
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
ROBUSTNESS_MODELS_V9_3 = ["logistic_regression", "decision_tree_depth_2"]
EVALUATION_ROLES_V9_3 = ["validation", "test"]


def run_refined_strict_walk_forward_validation_v9_3(
    root: Path = Path("."),
    *,
    validate_dataset: bool = True,
) -> dict[str, Any]:
    root = root.resolve()
    if validate_dataset:
        _validate_dataset_layer(root)

    dataset_manifest = load_v9_1_dataset_manifest(root)
    window = _input_window(dataset_manifest)
    window_start = window["window_start"]
    window_end = window["window_end"]
    created_at = utc_now_iso()
    run_id = f"v9_3_{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}_{uuid.uuid4().hex[:8]}"

    outputs: dict[str, dict[str, Any]] = {"scores": {}, "folds": {}}
    input_datasets: dict[str, dict[str, Any]] = {}
    folds_manifest: dict[str, list[dict[str, Any]]] = {}
    metrics: dict[str, Any] = {}
    aggregate_metrics: dict[str, Any] = {}
    label_shuffle: dict[str, Any] = {}
    quality: dict[str, Any] = {}
    status = "PASS"

    for timeframe in TIMEFRAMES_V9_3:
        dataset_path = input_dataset_path(root, timeframe, dataset_manifest)
        dataset_sha = sha256_file(dataset_path)
        dataset = read_parquet(dataset_path).sort_values("event_ts").reset_index(drop=True)
        folds = build_refined_strict_walk_forward_folds_v9_3(dataset, window_start, window_end)
        scores = build_refined_strict_walk_forward_scores_v9_3(
            dataset,
            folds,
            dataset_sha256=dataset_sha,
            ml_run_id=run_id,
        )
        fold_metrics = compute_refined_strict_walk_forward_metrics_v9_3(scores)
        metrics.update(fold_metrics)
        aggregate_metrics.update(compute_refined_strict_walk_forward_aggregate_metrics_v9_3(fold_metrics))
        label_shuffle.update(compute_label_shuffle_falsification_v9_3(dataset, folds, fold_metrics))

        score_path = score_output_path(root, timeframe, window_start, window_end)
        folds_path = folds_output_path(root, timeframe, window_start, window_end)
        write_parquet(scores, score_path)
        write_parquet(folds, folds_path)

        input_datasets[timeframe] = _input_block(root, dataset_path, dataset_sha, len(dataset))
        outputs["scores"][timeframe] = _output_block(root, score_path, len(scores))
        outputs["folds"][timeframe] = _output_block(root, folds_path, len(folds))
        folds_manifest[timeframe] = summarize_folds_v9_3(folds)
        quality[timeframe] = assess_refined_strict_walk_forward_quality_v9_3(dataset, folds, scores, timeframe)
        if quality[timeframe]["errors"]:
            status = "FAIL"

    comparison_to_static_split = compare_to_static_split_v9_2(root, aggregate_metrics)
    feature_leakage_scan = scan_refined_strict_walk_forward_feature_leakage_v9_3(ALLOWED_FEATURE_COLUMNS_V9_3)
    metric_forbidden_scan = scan_refined_strict_walk_forward_metric_forbidden_terms_v9_3(
        {
            "metrics": metrics,
            "aggregate_metrics": aggregate_metrics,
            "label_shuffle_falsification": label_shuffle,
            "comparison_to_static_split_v9_2": comparison_to_static_split,
        }
    )
    if feature_leakage_scan["forbidden_feature_columns_present"] or metric_forbidden_scan["forbidden_terms_present"]:
        status = "FAIL"

    manifest = {
        "version": VERSION_V9_3,
        "status": status,
        "created_at_utc": created_at,
        "walk_forward_run_id": run_id,
        "input_dataset_manifest": {
            "path": MANIFEST_PATH_V9_1.as_posix(),
            "sha256": sha256_file(root / MANIFEST_PATH_V9_1),
            "window_start": window_start,
            "window_end": window_end,
            "total_days": int(window["total_days"]),
            "feature_columns_count": int(dataset_manifest["feature_columns_count"]),
        },
        "input_datasets": input_datasets,
        "walk_forward_policy": WALK_FORWARD_POLICY_V9_3,
        "folds": folds_manifest,
        "outputs": outputs,
        "target_name": TARGET_NAME_V9_3,
        "feature_columns": ALLOWED_FEATURE_COLUMNS_V9_3,
        "feature_columns_count": len(ALLOWED_FEATURE_COLUMNS_V9_3),
        "models": MODEL_NAMES_V9_3,
        "metrics": metrics,
        "aggregate_metrics": aggregate_metrics,
        "label_shuffle_falsification": label_shuffle,
        "comparison_to_static_split_v9_2": comparison_to_static_split,
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
        "safety": SAFETY_FLAGS_V9_3,
        "limitations": EXPECTED_LIMITATIONS_V9_3,
    }
    _write_json(root / MANIFEST_PATH_V9_3, manifest)
    _write_json(root / REPORT_JSON_PATH_V9_3, manifest)
    _write_json(root / SCORES_JSON_PATH_V9_3, _scores_report(manifest))
    markdown = build_refined_strict_walk_forward_markdown_v9_3(manifest)
    _write_text(root / REPORT_MD_PATH_V9_3, markdown)
    _write_text(root / SCORES_MD_PATH_V9_3, markdown)
    _write_text(root / DOC_PATH_V9_3, markdown)
    return manifest


def load_v9_1_dataset_manifest(root: Path = Path(".")) -> dict[str, Any]:
    return json.loads((root.resolve() / MANIFEST_PATH_V9_1).read_text(encoding="utf-8"))


def input_dataset_path(root: Path, timeframe: str, manifest: dict[str, Any] | None = None) -> Path:
    manifest = manifest or load_v9_1_dataset_manifest(root)
    return root.resolve() / manifest["outputs"][timeframe]["path"]


def score_output_path(root: Path, timeframe: str, window_start: str | None = None, window_end: str | None = None) -> Path:
    if window_start is None or window_end is None:
        window = _input_window(load_v9_1_dataset_manifest(root))
        window_start = window["window_start"]
        window_end = window["window_end"]
    return get_refined_strict_walk_forward_score_path_v9_3(root.resolve(), timeframe, window_start, window_end)


def folds_output_path(root: Path, timeframe: str, window_start: str | None = None, window_end: str | None = None) -> Path:
    if window_start is None or window_end is None:
        window = _input_window(load_v9_1_dataset_manifest(root))
        window_start = window["window_start"]
        window_end = window["window_end"]
    return get_refined_strict_walk_forward_folds_path_v9_3(root.resolve(), timeframe, window_start, window_end)


def build_refined_strict_walk_forward_folds_v9_3(dataset: pd.DataFrame, window_start: str, window_end: str) -> pd.DataFrame:
    event_ts = pd.to_datetime(dataset["event_ts"], utc=True)
    start = pd.Timestamp(f"{window_start}T00:00:00Z")
    end_exclusive = pd.Timestamp(f"{window_end}T00:00:00Z") + pd.Timedelta(days=1)
    fold_frames: list[pd.DataFrame] = []
    fold_order = 1
    offset = 0
    while True:
        train_start = start
        validation_start = start + pd.DateOffset(months=WALK_FORWARD_POLICY_V9_3["initial_train_months"] + offset)
        test_start = validation_start + pd.DateOffset(months=WALK_FORWARD_POLICY_V9_3["validation_months"])
        test_end = test_start + pd.DateOffset(months=WALK_FORWARD_POLICY_V9_3["test_months"])
        if test_end > end_exclusive:
            break
        fold_id = f"fold_{fold_order:02d}"
        fold = _fold_assignments(dataset, event_ts, fold_id, fold_order, train_start, validation_start, test_start, test_end)
        fold_frames.append(_apply_purge_embargo(fold))
        fold_order += 1
        offset += WALK_FORWARD_POLICY_V9_3["step_months"]
    if not fold_frames:
        return pd.DataFrame(columns=WALK_FORWARD_FOLD_COLUMNS_V9_3)
    return pd.concat(fold_frames, ignore_index=True)[WALK_FORWARD_FOLD_COLUMNS_V9_3]


def build_refined_strict_walk_forward_scores_v9_3(
    dataset: pd.DataFrame,
    folds: pd.DataFrame,
    *,
    dataset_sha256: str,
    ml_run_id: str,
) -> pd.DataFrame:
    score_frames: list[pd.DataFrame] = []
    feature_columns_sha256 = get_feature_columns_sha256_v9_3()
    if folds.empty:
        return pd.DataFrame(columns=ML_SCORE_COLUMNS_V9_3)
    merged = folds.merge(
        dataset,
        on=["source", "venue", "market_type", "symbol", "timeframe", "event_ts"],
        how="left",
        validate="many_to_one",
    )
    merged = prepare_refined_walk_forward_ml_frame_v9_3(merged)
    for _fold_id, fold_frame in merged.groupby("fold_id", sort=True):
        train = fold_frame[fold_frame["fold_role"] == "train"]
        if train.empty:
            continue
        train_features = train[ALLOWED_FEATURE_COLUMNS_V9_3]
        train_target = train[TARGET_NAME_V9_3].astype(str)
        predict_features = fold_frame[ALLOWED_FEATURE_COLUMNS_V9_3]
        for model_name in MODEL_NAMES_V9_3:
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
            scores["target_name"] = TARGET_NAME_V9_3
            scores["dataset_sha256"] = dataset_sha256
            scores["feature_columns_sha256"] = feature_columns_sha256
            scores["ml_schema_version"] = ML_SCHEMA_VERSION_V9_3
            scores["target_value"] = fold_frame[TARGET_NAME_V9_3].astype(str).to_numpy()
            scores["research_predicted_class"] = result.predicted_class.to_numpy()
            scores["research_probability_down"] = result.probabilities["DOWN"].to_numpy()
            scores["research_probability_flat"] = result.probabilities["FLAT"].to_numpy()
            scores["research_probability_up"] = result.probabilities["UP"].to_numpy()
            scores["prediction_available_ts"] = fold_frame["decision_ts"].to_numpy()
            scores["row_valid_for_ml"] = True
            scores["ml_null_count"] = scores.isna().sum(axis=1).astype(int)
            scores["ml_error_count"] = 0
            score_frames.append(scores[ML_SCORE_COLUMNS_V9_3])
    if not score_frames:
        return pd.DataFrame(columns=ML_SCORE_COLUMNS_V9_3)
    return pd.concat(score_frames, ignore_index=True)


def prepare_refined_walk_forward_ml_frame_v9_3(frame: pd.DataFrame) -> pd.DataFrame:
    filtered = frame[
        (frame["label_valid_h1"] == True)  # noqa: E712
        & (frame["warmup_row"] == False)  # noqa: E712
        & (frame["is_embargoed"] == False)  # noqa: E712
        & (frame["is_purged"] == False)  # noqa: E712
    ].copy()
    return filtered.sort_values(["fold_order", "fold_role", "event_ts"]).reset_index(drop=True)


def summarize_folds_v9_3(folds: pd.DataFrame) -> list[dict[str, Any]]:
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


def compute_label_shuffle_falsification_v9_3(
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
    merged = prepare_refined_walk_forward_ml_frame_v9_3(merged)
    for (fold_id, fold_order), fold_frame in merged.groupby(["fold_id", "fold_order"], sort=True):
        train = fold_frame[fold_frame["fold_role"] == "train"]
        if train.empty:
            continue
        rng = np.random.default_rng(LABEL_SHUFFLE_RANDOM_SEED_V9_3 + int(fold_order))
        shuffled_train_target = pd.Series(rng.permutation(train[TARGET_NAME_V9_3].astype(str).to_numpy()), index=train.index)
        predict_frame = fold_frame[fold_frame["fold_role"].isin(EVALUATION_ROLES_V9_3)]
        for model_name in ROBUSTNESS_MODELS_V9_3:
            result = fit_predict_model(
                model_name,
                train[ALLOWED_FEATURE_COLUMNS_V9_3],
                shuffled_train_target,
                predict_frame[ALLOWED_FEATURE_COLUMNS_V9_3],
            )
            for role in EVALUATION_ROLES_V9_3:
                role_frame = predict_frame[predict_frame["fold_role"] == role]
                y_true = role_frame[TARGET_NAME_V9_3].astype(str)
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
                    "random_seed": LABEL_SHUFFLE_RANDOM_SEED_V9_3 + int(fold_order),
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


def compare_to_static_split_v9_2(root: Path, aggregate_metrics: dict[str, Any]) -> dict[str, Any]:
    manifest_path = root / MANIFEST_PATH_V9_2
    if not manifest_path.exists():
        return {
            "status": "SKIPPED",
            "source_manifest_path": MANIFEST_PATH_V9_2.as_posix(),
            "descriptive_only": True,
            "not_same_validation_design": True,
            "comparisons": {},
            "warnings": ["V9.2 static split manifest absent; comparison skipped."],
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
            "v9_3_mean_test_accuracy": aggregate["mean_test_accuracy"],
            "v9_2_static_test_accuracy": static.get("accuracy"),
            "accuracy_delta_v9_3_minus_v9_2_static": _nullable_delta(aggregate["mean_test_accuracy"], static.get("accuracy")),
            "v9_3_mean_test_macro_f1": aggregate["mean_test_macro_f1"],
            "v9_2_static_test_macro_f1": static.get("macro_f1"),
            "macro_f1_delta_v9_3_minus_v9_2_static": _nullable_delta(aggregate["mean_test_macro_f1"], static.get("macro_f1")),
            "descriptive_only": True,
            "not_same_validation_design": True,
        }
    return {
        "status": "PASS",
        "source_manifest_path": MANIFEST_PATH_V9_2.as_posix(),
        "source_manifest_sha256": sha256_file(manifest_path),
        "descriptive_only": True,
        "not_same_validation_design": True,
        "compared_metrics": ["accuracy", "macro_f1"],
        "comparisons": comparisons,
        "warnings": ["V9.2 static split and V9.3 strict walk-forward are not identical validation designs."],
    }


def scan_refined_strict_walk_forward_feature_leakage_v9_3(feature_columns: list[str]) -> dict[str, Any]:
    exact = {term.casefold() for term in FORBIDDEN_FEATURE_EXACT_V9_3}
    prefixes = tuple(term.casefold() for term in FORBIDDEN_FEATURE_PREFIXES_V9_3)
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


def scan_refined_strict_walk_forward_metric_forbidden_terms_v9_3(payload: Any) -> dict[str, Any]:
    text = json.dumps(payload, ensure_ascii=False, sort_keys=True).casefold()
    present = [term for term in FORBIDDEN_METRIC_TERMS_V9_3 if term in text]
    return {
        "forbidden_terms_present": present,
        "metric_forbidden_terms_detected": bool(present),
    }


def build_refined_strict_walk_forward_markdown_v9_3(manifest: dict[str, Any]) -> str:
    rows = "\n".join(
        f"- `{timeframe}` : `{len(folds)}` folds, scores `{manifest['outputs']['scores'][timeframe]['rows']}` lignes."
        for timeframe, folds in manifest["folds"].items()
    )
    return "\n".join(
        [
            "# Validation walk-forward offline stricte raffinee - V9.3",
            "",
            "V9.3 applique une validation walk-forward offline stricte sur le dataset raffine V9.1 OHLCV + trades.",
            "Les modeles sont des baselines de recherche par fold et les scores `research_*` restent non actionnables.",
            "",
            "## Politique walk-forward",
            "",
            f"- Grouping : `{manifest['walk_forward_policy']['grouping']}`.",
            f"- Train initial : `{manifest['walk_forward_policy']['initial_train_months']}` mois.",
            f"- Validation : `{manifest['walk_forward_policy']['validation_months']}` mois.",
            f"- Test : `{manifest['walk_forward_policy']['test_months']}` mois.",
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
            "- Les comparaisons avec V9.2 sont descriptives.",
            "- V9.3 ne valide aucune strategie.",
            "- V9.3 ne produit aucun backtest.",
            "- V9.3 ne produit aucun signal de trading.",
            "- V9.3 ne produit aucun ordre.",
            "- V9.3 n'autorise aucun paper live.",
            "- V9.3 n'autorise aucun trading reel.",
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
        role_frame["walk_forward_policy_version"] = WALK_FORWARD_POLICY_VERSION_V9_3
        frames.append(role_frame)
    return pd.concat(frames, ignore_index=True)


def _apply_purge_embargo(fold: pd.DataFrame) -> pd.DataFrame:
    frame = fold.sort_values(["fold_role", "event_ts"]).reset_index(drop=True)
    purge = int(WALK_FORWARD_POLICY_V9_3["purge_bars"])
    embargo = int(WALK_FORWARD_POLICY_V9_3["embargo_bars"])
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
    result = validate_refined_ohlcv_trades_offline_supervised_dataset_v9_1(root)
    if not result["passed"]:
        raise RuntimeError(f"V9.1 dataset validation failed before V9.3: {result['errors']}")


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
        "comparison_to_static_split_v9_2": manifest["comparison_to_static_split_v9_2"],
    }


def _nullable_delta(left: Any, right: Any) -> float | None:
    if left is None or right is None:
        return None
    return _round_metric(float(left) - float(right))


def _round_metric(value: float) -> float:
    return float(round(float(value), 12))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
