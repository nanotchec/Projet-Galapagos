from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd
from pandas.testing import assert_frame_equal

from galapagos.data.public_market.provenance import sha256_file, utc_now_iso
from galapagos.data.public_market.storage import read_parquet, write_parquet
from galapagos.datasets.ohlcv_trades_1y_window_validation import validate_ohlcv_trades_1y_offline_supervised_dataset_v8_4
from galapagos.datasets.schemas import MANIFEST_PATH_V8_4, SPLIT_COLUMNS_V8_4
from galapagos.ml.ohlcv_trades_1y_window_metrics import (
    compute_ohlcv_trades_classification_metrics_v8_5,
    compute_ohlcv_trades_walk_forward_metrics_v8_5,
)
from galapagos.ml.ohlcv_trades_1y_window_quality import assess_ohlcv_trades_ml_quality_v8_5
from galapagos.ml.offline_baselines import fit_predict_model
from galapagos.ml.schemas import (
    ALLOWED_FEATURE_COLUMNS_V8_5,
    DOC_PATH_V8_5,
    EXPECTED_LIMITATIONS_V8_5,
    MANIFEST_PATH_V7_4,
    MANIFEST_PATH_V8_0,
    MANIFEST_PATH_V8_5,
    ML_SCHEMA_VERSION_V8_5,
    ML_SCORE_COLUMNS_V8_5,
    MODEL_NAMES_V8_5,
    REPORT_JSON_PATH_V8_5,
    REPORT_MD_PATH_V8_5,
    SAFETY_FLAGS_V8_5,
    SCORES_JSON_PATH_V8_5,
    SCORES_MD_PATH_V8_5,
    TARGET_NAME_V8_5,
    TIMEFRAMES_V8_5,
    VERSION_V8_5,
    get_feature_columns_sha256_v8_5,
    get_ohlcv_trades_ml_score_path_v8_5,
)


def run_ohlcv_trades_1y_offline_ml_research_v8_5(
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
    total_days = int(window["total_days"])

    created_at = utc_now_iso()
    ml_run_id = f"v8_5_{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}_{uuid.uuid4().hex[:8]}"
    input_datasets: dict[str, dict[str, Any]] = {}
    input_splits: dict[str, dict[str, Any]] = {}
    outputs: dict[str, dict[str, Any]] = {}
    metrics: dict[str, Any] = {}
    walk_forward_metrics: dict[str, Any] = {}
    quality: dict[str, dict[str, Any]] = {}
    sanity_checks: dict[str, dict[str, Any]] = {}
    status = "PASS"

    for timeframe in TIMEFRAMES_V8_5:
        dataset_path = input_dataset_path(root, timeframe, dataset_manifest)
        split_path = input_split_path(root, timeframe, dataset_manifest)
        score_path = score_output_path(root, timeframe, window_start, window_end)
        dataset = read_parquet(dataset_path)
        splits = read_parquet(split_path)
        dataset_for_ml = validate_split_alignment_v8_5(dataset, splits)
        dataset_sha = sha256_file(dataset_path)

        scores = build_ohlcv_trades_model_scores_v8_5(dataset_for_ml, dataset_sha256=dataset_sha, ml_run_id=ml_run_id)
        write_parquet(scores, score_path)

        input_datasets[timeframe] = _input_block(root, dataset_path, dataset_sha, len(dataset))
        input_splits[timeframe] = _input_block(root, split_path, sha256_file(split_path), len(splits))
        outputs[timeframe] = _output_block(root, score_path, len(scores))
        quality[timeframe] = assess_ohlcv_trades_ml_quality_v8_5(dataset_for_ml, scores, timeframe)
        if quality[timeframe]["errors"]:
            status = "FAIL"
        sanity_checks[timeframe] = _sanity_from_quality(dataset_for_ml, quality[timeframe])
        metrics.update(compute_ohlcv_trades_classification_metrics_v8_5(scores))
        walk_forward_metrics.update(compute_ohlcv_trades_walk_forward_metrics_v8_5(scores))

    comparison_to_references = build_comparison_to_references_v8_5(root, metrics)

    manifest = {
        "version": VERSION_V8_5,
        "status": status,
        "created_at_utc": created_at,
        "ml_run_id": ml_run_id,
        "input_dataset_manifest": {
            "path": MANIFEST_PATH_V8_4.as_posix(),
            "sha256": sha256_file(root / MANIFEST_PATH_V8_4),
            "window_start": window_start,
            "window_end": window_end,
            "total_days": total_days,
            "feature_columns_count": int(dataset_manifest["feature_columns_count"]),
        },
        "input_datasets": input_datasets,
        "input_splits": input_splits,
        "outputs": outputs,
        "target_name": TARGET_NAME_V8_5,
        "feature_columns": ALLOWED_FEATURE_COLUMNS_V8_5,
        "feature_columns_count": len(ALLOWED_FEATURE_COLUMNS_V8_5),
        "models": MODEL_NAMES_V8_5,
        "metrics": metrics,
        "walk_forward_metrics": walk_forward_metrics,
        "comparison_to_references": comparison_to_references,
        "sanity_checks": sanity_checks,
        "quality": quality,
        "safety": SAFETY_FLAGS_V8_5,
        "limitations": EXPECTED_LIMITATIONS_V8_5,
    }

    _write_json(root / MANIFEST_PATH_V8_5, manifest)
    _write_json(root / REPORT_JSON_PATH_V8_5, manifest)
    _write_json(root / SCORES_JSON_PATH_V8_5, _scores_report(manifest))
    markdown = build_ohlcv_trades_ml_markdown_v8_5(manifest)
    _write_text(root / REPORT_MD_PATH_V8_5, markdown)
    _write_text(root / SCORES_MD_PATH_V8_5, markdown)
    _write_text(root / DOC_PATH_V8_5, markdown)
    _update_project_state(root, manifest)
    return manifest


def prepare_ohlcv_trades_ml_frame_v8_5(dataset: pd.DataFrame) -> pd.DataFrame:
    frame = dataset[(dataset["label_valid_h1"] == True) & (dataset["warmup_row"] == False)].copy()  # noqa: E712
    return frame.reset_index(drop=True)


def validate_split_alignment_v8_5(dataset: pd.DataFrame, splits: pd.DataFrame) -> pd.DataFrame:
    missing_dataset = [column for column in SPLIT_COLUMNS_V8_4 if column not in dataset.columns]
    missing_splits = [column for column in SPLIT_COLUMNS_V8_4 if column not in splits.columns]
    if missing_dataset or missing_splits:
        raise ValueError(f"V8.5 split alignment missing dataset={missing_dataset}, missing_splits={missing_splits}")
    try:
        assert_frame_equal(
            dataset[SPLIT_COLUMNS_V8_4].reset_index(drop=True),
            splits[SPLIT_COLUMNS_V8_4].reset_index(drop=True),
            check_dtype=False,
        )
    except AssertionError as exc:
        raise ValueError("V8.5 dataset and split files are not aligned") from exc
    if dataset["walk_forward_group"].isna().any():
        raise ValueError("V8.5 dataset contains null walk_forward_group values")
    return dataset.copy()


def get_ohlcv_trades_training_slices_v8_5(frame: pd.DataFrame) -> dict[str, pd.DataFrame]:
    return {split: frame[frame["split"] == split].copy() for split in ["train", "validation", "test"]}


def build_ohlcv_trades_model_scores_v8_5(
    dataset: pd.DataFrame,
    *,
    dataset_sha256: str,
    ml_run_id: str,
) -> pd.DataFrame:
    ml_frame = prepare_ohlcv_trades_ml_frame_v8_5(dataset)
    slices = get_ohlcv_trades_training_slices_v8_5(ml_frame)
    train = slices["train"]
    if train.empty:
        return pd.DataFrame(columns=ML_SCORE_COLUMNS_V8_5)

    score_frames: list[pd.DataFrame] = []
    train_features = train[ALLOWED_FEATURE_COLUMNS_V8_5]
    train_target = train[TARGET_NAME_V8_5].astype(str)
    score_features = ml_frame[ALLOWED_FEATURE_COLUMNS_V8_5]
    feature_columns_sha256 = get_feature_columns_sha256_v8_5()

    for model_name in MODEL_NAMES_V8_5:
        result = fit_predict_model(
            model_name,
            train_features,
            train_target,
            score_features,
        )
        scores = ml_frame[
            [
                "source",
                "venue",
                "market_type",
                "symbol",
                "timeframe",
                "event_ts",
                "close_ts",
                "decision_ts",
                "split",
                "walk_forward_group",
            ]
        ].copy()
        scores["ml_run_id"] = ml_run_id
        scores["model_name"] = model_name
        scores["target_name"] = TARGET_NAME_V8_5
        scores["dataset_sha256"] = dataset_sha256
        scores["feature_columns_sha256"] = feature_columns_sha256
        scores["ml_schema_version"] = ML_SCHEMA_VERSION_V8_5
        scores["target_value"] = ml_frame[TARGET_NAME_V8_5].astype(str).to_numpy()
        scores["research_predicted_class"] = result.predicted_class.to_numpy()
        scores["research_probability_down"] = result.probabilities["DOWN"].to_numpy()
        scores["research_probability_flat"] = result.probabilities["FLAT"].to_numpy()
        scores["research_probability_up"] = result.probabilities["UP"].to_numpy()
        scores["prediction_available_ts"] = ml_frame["decision_ts"].to_numpy()
        scores["row_valid_for_ml"] = True
        scores["ml_null_count"] = scores.isna().sum(axis=1).astype(int)
        scores["ml_error_count"] = 0
        score_frames.append(scores[ML_SCORE_COLUMNS_V8_5])

    return pd.concat(score_frames, ignore_index=True)


def build_ohlcv_trades_ml_markdown_v8_5(manifest: dict[str, Any]) -> str:
    lines = [
        "# Rapport qualite - V8.5 ML offline OHLCV + public trades",
        "",
        "## Objectif",
        "",
        "V8.5 entraine des baselines ML offline simples sur le dataset V8.4 valide avec OHLCV + public trades features.",
        "Ces sorties sont des scores de recherche descriptifs, non actionnables et sans usage de trading.",
        "",
        "## Fenetre",
        "",
        f"- Debut : `{manifest['input_dataset_manifest']['window_start']}`.",
        f"- Fin : `{manifest['input_dataset_manifest']['window_end']}`.",
        f"- Jours : `{manifest['input_dataset_manifest']['total_days']}`.",
        "",
        "## Cible et modeles",
        "",
        f"- Cible : `{manifest['target_name']}`.",
        f"- Modeles : `{', '.join(manifest['models'])}`.",
        f"- Features ML : `{manifest['feature_columns_count']}` colonnes causales OHLCV + aggTrades autorisees uniquement.",
        "- `walk_forward_group` est conserve pour les metriques descriptives, jamais utilise comme feature.",
        "",
        "## Outputs",
        "",
    ]
    for timeframe, output in manifest["outputs"].items():
        item = manifest["quality"][timeframe]
        lines.extend(
            [
                f"- `{timeframe}` scores : `{output['path']}` ({output['rows']} lignes).",
                f"  - lignes ML utilisees : `{item['rows_used_for_ml']}`.",
                f"  - train/validation/test : `{item['train_rows']}` / `{item['validation_rows']}` / `{item['test_rows']}`.",
                f"  - groupes walk-forward : `{len(item['walk_forward_groups'])}`.",
            ]
        )
    lines.extend(
        [
            "",
            "## Sanity checks",
            "",
            "- La cible unique est `up_down_flat_h1`.",
            "- Les lignes `warmup_row = true` et `label_valid_h1 = false` sont exclues.",
            "- Les features `future_*`, `label_*`, `direction_*`, `up_down_flat_*`, `split`, `walk_forward_group`, `signal`, `order`, `strategy`, `pnl` et `backtest` sont interdites.",
            "- Les sorties sont nommees `research_*` et ne sont pas des signaux.",
            "- Les metriques sont descriptives : accuracy, balanced accuracy, macro F1, precision/rappel par classe et matrices de confusion.",
            "- Les metriques walk-forward sont descriptives et ne sont pas un backtest.",
            "- Les comparaisons a V8.0/V7.4/V6.2/V5.4 sont descriptives, non actionnables et non directement comparables si les fenetres different.",
            "",
            "## Limitations",
            "",
            *[f"- {item}" for item in manifest["limitations"]],
            "",
            "## Non-usage warnings",
            "",
            "- V8.5 ne valide aucune strategie.",
            "- V8.5 ne produit aucun backtest.",
            "- V8.5 ne produit aucun signal de trading.",
            "- V8.5 ne produit aucun ordre.",
            "- V8.5 n'autorise aucun paper live.",
            "- V8.5 n'autorise aucun trading reel.",
            "- Les metriques sont descriptives et non actionnables.",
            "- Les metriques walk-forward ne sont pas un backtest.",
            "- La fenetre de 1 an est trop courte pour une conclusion robuste.",
            "- Les comparaisons V8.5 vs V8.0/V7.4/V6.2/V5.4 sont descriptives, non actionnables.",
        ]
    )
    return "\n".join(lines) + "\n"


def load_v8_4_dataset_manifest(root: Path = Path(".")) -> dict[str, Any]:
    return json.loads((root.resolve() / MANIFEST_PATH_V8_4).read_text(encoding="utf-8"))


def input_dataset_path(root: Path, timeframe: str, manifest: dict[str, Any] | None = None) -> Path:
    manifest = manifest or load_v8_4_dataset_manifest(root)
    return root.resolve() / manifest["outputs"][timeframe]["path"]


def input_split_path(root: Path, timeframe: str, manifest: dict[str, Any] | None = None) -> Path:
    manifest = manifest or load_v8_4_dataset_manifest(root)
    return root.resolve() / manifest["splits"][timeframe]["path"]


def score_output_path(root: Path, timeframe: str, window_start: str | None = None, window_end: str | None = None) -> Path:
    if window_start is None or window_end is None:
        window = _input_window(load_v8_4_dataset_manifest(root))
        window_start = window["window_start"]
        window_end = window["window_end"]
    return get_ohlcv_trades_ml_score_path_v8_5(root.resolve(), timeframe, window_start, window_end)


def _validate_dataset_layer(root: Path) -> None:
    result = validate_ohlcv_trades_1y_offline_supervised_dataset_v8_4(root)
    if not result["passed"]:
        raise RuntimeError(f"V8.4 dataset validation failed before V8.5: {result['errors']}")


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


def _sanity_from_quality(dataset: pd.DataFrame, quality: dict[str, Any]) -> dict[str, Any]:
    used = prepare_ohlcv_trades_ml_frame_v8_5(dataset)
    return {
        "train_rows": quality["train_rows"],
        "validation_rows": quality["validation_rows"],
        "test_rows": quality["test_rows"],
        "target_classes_seen_train": _target_classes(used, "train"),
        "target_classes_seen_validation": _target_classes(used, "validation"),
        "target_classes_seen_test": _target_classes(used, "test"),
        "no_shuffle_confirmed": quality["no_shuffle_confirmed"],
        "forbidden_feature_columns_present": quality["forbidden_feature_columns_present"],
        "forbidden_output_columns_present": quality["forbidden_output_columns_present"],
    }


def _target_classes(frame: pd.DataFrame, split: str) -> list[str]:
    return sorted(frame[frame["split"] == split][TARGET_NAME_V8_5].dropna().astype(str).unique().tolist())


def build_comparison_to_references_v8_5(root: Path, ohlcv_trades_metrics: dict[str, Any]) -> dict[str, Any]:
    references = {
        "ohlcv_trades_90d_v8_0": root / MANIFEST_PATH_V8_0,
        "ohlcv_trades_30d_v7_4": root / MANIFEST_PATH_V7_4,
        "advanced_ohlcv_v6_2": root / "reports/manifests/advanced_ohlcv_offline_ml_research_v6_2_manifest.json",
        "simple_ohlcv_v5_4": root / "reports/manifests/max_history_offline_ml_research_v5_4_manifest.json",
    }
    return {
        name: _build_reference_comparison(root, path, ohlcv_trades_metrics, name)
        for name, path in references.items()
    }


def _build_reference_comparison(
    root: Path,
    source_manifest_path: Path,
    ohlcv_trades_metrics: dict[str, Any],
    reference_name: str,
) -> dict[str, Any]:
    if not source_manifest_path.exists():
        return {
            "status": "SKIPPED",
            "source_manifest_path": source_manifest_path.relative_to(root).as_posix(),
            "source_manifest_sha256": None,
            "compared_metrics": ["accuracy", "balanced_accuracy", "macro_f1"],
            "comparisons": {},
            "descriptive_only": True,
            "non_actionable": True,
            "not_directly_comparable": True,
            "warnings": [f"{reference_name} manifest not available; descriptive comparison skipped."],
        }
    source_manifest = json.loads(source_manifest_path.read_text(encoding="utf-8"))
    reference_metrics = source_manifest.get("metrics", {})
    comparisons: dict[str, dict[str, Any]] = {}
    for key, current_payload in sorted(ohlcv_trades_metrics.items()):
        reference_payload = reference_metrics.get(key)
        if not isinstance(reference_payload, dict) or not isinstance(current_payload, dict):
            continue
        comparisons[key] = {
            "timeframe": current_payload.get("timeframe"),
            "model_name": current_payload.get("model_name"),
            "split": current_payload.get("split"),
            "accuracy_delta_v8_5_minus_reference": _metric_delta(current_payload, reference_payload, "accuracy"),
            "balanced_accuracy_delta_v8_5_minus_reference": _metric_delta(current_payload, reference_payload, "balanced_accuracy"),
            "macro_f1_delta_v8_5_minus_reference": _metric_delta(current_payload, reference_payload, "macro_f1"),
        }
    return {
        "status": "PASS",
        "source_manifest_path": source_manifest_path.relative_to(root).as_posix(),
        "source_manifest_sha256": sha256_file(source_manifest_path),
        "source_window_start": source_manifest.get("input_dataset_manifest", {}).get("window_start"),
        "source_window_end": source_manifest.get("input_dataset_manifest", {}).get("window_end"),
        "source_total_days": source_manifest.get("input_dataset_manifest", {}).get("total_days"),
        "compared_metrics": ["accuracy", "balanced_accuracy", "macro_f1"],
        "comparisons": comparisons,
        "descriptive_only": True,
        "non_actionable": True,
        "not_directly_comparable": True,
        "warnings": ["not directly comparable due to different window length/source set"],
    }


def _metric_delta(advanced_payload: dict[str, Any], simple_payload: dict[str, Any], metric_name: str) -> float | None:
    advanced_value = advanced_payload.get(metric_name)
    simple_value = simple_payload.get(metric_name)
    if not isinstance(advanced_value, (int, float)) or not isinstance(simple_value, (int, float)):
        return None
    return float(advanced_value) - float(simple_value)


def _scores_report(manifest: dict[str, Any]) -> dict[str, Any]:
    return {
        "version": manifest["version"],
        "ml_run_id": manifest["ml_run_id"],
        "outputs": manifest["outputs"],
        "metrics": manifest["metrics"],
        "walk_forward_metrics": manifest["walk_forward_metrics"],
        "comparison_to_references": manifest["comparison_to_references"],
    }


def _update_project_state(root: Path, manifest: dict[str, Any]) -> None:
    state_path = root / "reports/PROJECT_STATE.json"
    state = json.loads(state_path.read_text(encoding="utf-8")) if state_path.exists() else {}
    window = manifest["input_dataset_manifest"]
    rows = {timeframe: payload["rows"] for timeframe, payload in manifest["outputs"].items()}
    state.update(
        {
            "last_validated_version": "V8.4",
            "candidate_version": "V8.5",
            "candidate_status": "pending_external_audit",
            "direction": "OHLCV + public trades 1-year ML offline",
            "v8_5_candidate": True,
            "ohlcv_trades_1y_offline_ml_research_v8_5_created": True,
            "ohlcv_trades_ml_window_start_v8_5": window["window_start"],
            "ohlcv_trades_ml_window_end_v8_5": window["window_end"],
            "ohlcv_trades_ml_days_v8_5": window["total_days"],
            "ohlcv_trades_ml_score_rows_v8_5": rows,
            "feature_columns_count_v8_5": manifest["feature_columns_count"],
            "ohlcv_trades_ml_models_v8_5": MODEL_NAMES_V8_5,
            "ohlcv_trades_ml_target_v8_5": TARGET_NAME_V8_5,
            "backtest_v8_5_created": False,
            "strategy_v8_5_created": False,
            "signal_v8_5_created": False,
            "orders_v8_5_created": False,
            "paper_live_v8_5_created": False,
            "trading_v8_5_created": False,
            "persistent_model_v8_5_created": False,
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
    _write_json(root / "reports/current/latest_metrics.json", _build_latest_metrics(manifest, state))
    _write_text(root / "reports/PROJECT_STATE.md", _build_project_state_markdown(manifest))
    _write_text(root / "reports/current/latest_metrics.md", _build_latest_metrics_markdown(manifest))
    _write_text(root / "reports/current/latest_summary.md", _build_latest_summary_markdown(manifest))
    _write_text(root / "README.md", _build_readme_markdown(manifest))


def _build_latest_metrics(manifest: dict[str, Any], state: dict[str, Any]) -> dict[str, Any]:
    window = manifest["input_dataset_manifest"]
    return {
        "last_validated_version": "V8.4",
        "candidate_version": "V8.5",
        "candidate_status": "pending_external_audit",
        "direction": state["direction"],
        "ohlcv_trades_ml_window_start_v8_5": window["window_start"],
        "ohlcv_trades_ml_window_end_v8_5": window["window_end"],
        "ohlcv_trades_ml_days_v8_5": window["total_days"],
        "ohlcv_trades_ml_score_rows_v8_5": {timeframe: payload["rows"] for timeframe, payload in manifest["outputs"].items()},
        "feature_columns_count_v8_5": manifest["feature_columns_count"],
        "ohlcv_trades_ml_models_v8_5": manifest["models"],
        "ohlcv_trades_ml_target_v8_5": manifest["target_name"],
        "ml_schema_version_v8_5": ML_SCHEMA_VERSION_V8_5,
        "ml_score_columns_count_v8_5": len(ML_SCORE_COLUMNS_V8_5),
        "walk_forward_metrics_v8_5": True,
        "backtest_v8_5_created": False,
        "strategy_v8_5_created": False,
        "signal_v8_5_created": False,
        "orders_v8_5_created": False,
        "paper_live_v8_5_created": False,
        "persistent_model_v8_5_created": False,
        "trading_enabled": False,
        "paper_live_enabled": False,
        "orders_enabled": False,
        "backtest_enabled": False,
        "strategy_enabled": False,
        "execution_enabled": False,
        "api_key_used": False,
        "private_endpoint_used": False,
        "authentication_used": False,
        "external_validation_required": True,
    }


def _build_project_state_markdown(manifest: dict[str, Any]) -> str:
    window = manifest["input_dataset_manifest"]
    rows = {timeframe: payload["rows"] for timeframe, payload in manifest["outputs"].items()}
    return f"""# Etat du Projet : V8.4 validee + candidat V8.5

- **Derniere version validee** : V8.4.
- **Version candidate** : V8.5.
- **Statut candidate** : `pending_external_audit`.
- **Direction suivante** : OHLCV + public trades offline ML research baselines.

## Candidat V8.5

- Fenetre V8.4 utilisee : `{window['window_start']}` -> `{window['window_end']}`.
- Nombre de jours : `{window['total_days']}`.
- Row counts scores : `{rows}`.
- Schema : `ML_SCORE_COLUMNS_V8_5`.
- Cible : `{manifest['target_name']}`.
- Feature columns ML : `{manifest['feature_columns_count']}`.
- Modeles offline autorises : `{manifest['models']}`.
- Metriques walk-forward : descriptives uniquement, pas un backtest.
- Comparaisons V8.5 vs V8.0/V7.4/V6.2/V5.4 : descriptives uniquement, non actionnables et non directement comparables si les fenetres different.
- V8.5 reste candidate `pending_external_audit`.

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
- V8.5 reste non validee avant audit externe.
"""


def _build_latest_metrics_markdown(manifest: dict[str, Any]) -> str:
    window = manifest["input_dataset_manifest"]
    rows = "\n".join(f"- {timeframe}: `{payload['rows']}`" for timeframe, payload in manifest["outputs"].items())
    return f"""# Latest Metrics V8.5

- Derniere version validee : V8.4.
- Candidate : V8.5.
- Statut : `pending_external_audit`.
- Direction : OHLCV + public trades 1-year ML offline.
- Fenetre : `{window['window_start']}` -> `{window['window_end']}`.
- Total jours : `{window['total_days']}`.
- Cible : `{manifest['target_name']}`.
- Feature columns ML : `{manifest['feature_columns_count']}`.
- Modeles : `{manifest['models']}`.
- Metriques walk-forward : descriptives uniquement.

## Row counts scores

{rows}

Aucun backtest, aucune strategie, aucun signal de trading, aucun ordre, aucun modele persistant et aucun trading reel.
"""


def _build_latest_summary_markdown(manifest: dict[str, Any]) -> str:
    window = manifest["input_dataset_manifest"]
    rows = {timeframe: payload["rows"] for timeframe, payload in manifest["outputs"].items()}
    return f"""# Latest Summary V8.5

V8.4 est la derniere version validee par audit externe.

V8.5 est la candidate courante. Elle entraine uniquement des baselines ML offline simples sur le dataset V8.4 avec OHLCV + public trades features, produit des scores de recherche `research_*`, calcule des metriques descriptives par split et par groupe walk-forward, et compare descriptivement V8.5 a V8.0/V7.4/V6.2/V5.4 si disponible.

Fenetre utilisee : `{window['window_start']}` -> `{window['window_end']}`.

Total jours : `{window['total_days']}`.

Row counts scores : `{rows}`.

Feature columns ML : `{manifest['feature_columns_count']}`.

Aucun trading, aucun paper live, aucun ordre, aucun backtest, aucune strategie, aucun signal de trading, aucun modele persistant et aucun claim de rentabilite.

V8.5 reste `pending_external_audit`.
"""


def _build_readme_markdown(manifest: dict[str, Any]) -> str:
    window = manifest["input_dataset_manifest"]
    return f"""# Projet Galapagos

- Derniere version validee : V8.4.
- Candidate : V8.5, OHLCV + public trades 1-year ML offline.

V8.5 entraine uniquement des baselines ML offline simples sur le dataset V8.4 OHLCV + aggTrades, avec scores de recherche `research_*` et metriques descriptives.

Fenetre : `{window['window_start']}` -> `{window['window_end']}`, `{window['total_days']}` jours.

Feature columns ML : `{manifest['feature_columns_count']}`.

Aucun backtest, aucune strategie, aucun signal de trading, aucun ordre, aucun paper live, aucun trading reel et aucun modele persistant.

## Commandes V8.5

```bash
python scripts/run_ohlcv_trades_1y_offline_ml_research_v8_5.py
python scripts/validate_ohlcv_trades_1y_offline_ml_research_v8_5.py
python -m pytest -q tests/ml/test_ohlcv_trades_1y_offline_ml_research_v8_5.py
python -m pytest -q tests/validation/test_ohlcv_trades_1y_offline_ml_research_v8_5_validator.py
python scripts/release_audit_lite_zip_v8_5.py
python scripts/audit_audit_lite_zip_v8_5.py --zip projet-galapagos-v8.5-audit-lite.zip
python scripts/smoke_audit_lite_zip_v8_5.py --zip projet-galapagos-v8.5-audit-lite.zip
python -m pytest --collect-only -q
```

V8.5 reste `pending_external_audit` avant validation externe.
"""


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
