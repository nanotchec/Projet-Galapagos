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
from galapagos.datasets.advanced_ohlcv_window_validation import validate_advanced_ohlcv_offline_supervised_dataset_v6_1
from galapagos.datasets.schemas import MANIFEST_PATH_V6_1, SPLIT_COLUMNS_V6_1
from galapagos.ml.advanced_ohlcv_window_metrics import (
    compute_advanced_ohlcv_classification_metrics_v6_2,
    compute_advanced_ohlcv_walk_forward_metrics_v6_2,
)
from galapagos.ml.advanced_ohlcv_window_quality import assess_advanced_ohlcv_ml_quality_v6_2
from galapagos.ml.offline_baselines import fit_predict_model
from galapagos.ml.schemas import (
    ALLOWED_FEATURE_COLUMNS_V6_2,
    DOC_PATH_V6_2,
    EXPECTED_LIMITATIONS_V6_2,
    MANIFEST_PATH_V6_2,
    ML_SCHEMA_VERSION_V6_2,
    ML_SCORE_COLUMNS_V6_2,
    MODEL_NAMES_V6_2,
    REPORT_JSON_PATH_V6_2,
    REPORT_MD_PATH_V6_2,
    SAFETY_FLAGS_V6_2,
    SCORES_JSON_PATH_V6_2,
    SCORES_MD_PATH_V6_2,
    TARGET_NAME_V6_2,
    TIMEFRAMES_V6_2,
    VERSION_V6_2,
    get_feature_columns_sha256_v6_2,
    get_advanced_ohlcv_ml_score_path_v6_2,
)


def run_advanced_ohlcv_offline_ml_research_v6_2(
    root: Path = Path("."),
    *,
    validate_dataset: bool = True,
) -> dict[str, Any]:
    root = root.resolve()
    if validate_dataset:
        _validate_dataset_layer(root)

    dataset_manifest = load_v6_1_dataset_manifest(root)
    window = _input_window(dataset_manifest)
    window_start = window["window_start"]
    window_end = window["window_end"]
    total_days = int(window["total_days"])

    created_at = utc_now_iso()
    ml_run_id = f"v6_2_{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}_{uuid.uuid4().hex[:8]}"
    input_datasets: dict[str, dict[str, Any]] = {}
    input_splits: dict[str, dict[str, Any]] = {}
    outputs: dict[str, dict[str, Any]] = {}
    metrics: dict[str, Any] = {}
    walk_forward_metrics: dict[str, Any] = {}
    quality: dict[str, dict[str, Any]] = {}
    sanity_checks: dict[str, dict[str, Any]] = {}
    status = "PASS"

    for timeframe in TIMEFRAMES_V6_2:
        dataset_path = input_dataset_path(root, timeframe, dataset_manifest)
        split_path = input_split_path(root, timeframe, dataset_manifest)
        score_path = score_output_path(root, timeframe, window_start, window_end)
        dataset = read_parquet(dataset_path)
        splits = read_parquet(split_path)
        dataset_for_ml = validate_split_alignment_v6_2(dataset, splits)
        dataset_sha = sha256_file(dataset_path)

        scores = build_advanced_ohlcv_model_scores_v6_2(dataset_for_ml, dataset_sha256=dataset_sha, ml_run_id=ml_run_id)
        write_parquet(scores, score_path)

        input_datasets[timeframe] = _input_block(root, dataset_path, dataset_sha, len(dataset))
        input_splits[timeframe] = _input_block(root, split_path, sha256_file(split_path), len(splits))
        outputs[timeframe] = _output_block(root, score_path, len(scores))
        quality[timeframe] = assess_advanced_ohlcv_ml_quality_v6_2(dataset_for_ml, scores, timeframe)
        if quality[timeframe]["errors"]:
            status = "FAIL"
        sanity_checks[timeframe] = _sanity_from_quality(dataset_for_ml, quality[timeframe])
        metrics.update(compute_advanced_ohlcv_classification_metrics_v6_2(scores))
        walk_forward_metrics.update(compute_advanced_ohlcv_walk_forward_metrics_v6_2(scores))

    comparison_to_simple_ohlcv_v5_4 = build_comparison_to_simple_ohlcv_v5_4(root, metrics)

    manifest = {
        "version": VERSION_V6_2,
        "status": status,
        "created_at_utc": created_at,
        "ml_run_id": ml_run_id,
        "input_dataset_manifest": {
            "path": MANIFEST_PATH_V6_1.as_posix(),
            "sha256": sha256_file(root / MANIFEST_PATH_V6_1),
            "window_start": window_start,
            "window_end": window_end,
            "total_days": total_days,
            "advanced_feature_columns_count": int(dataset_manifest["advanced_feature_columns_count"]),
        },
        "input_datasets": input_datasets,
        "input_splits": input_splits,
        "outputs": outputs,
        "target_name": TARGET_NAME_V6_2,
        "feature_columns": ALLOWED_FEATURE_COLUMNS_V6_2,
        "advanced_feature_columns_count": len(ALLOWED_FEATURE_COLUMNS_V6_2),
        "models": MODEL_NAMES_V6_2,
        "metrics": metrics,
        "walk_forward_metrics": walk_forward_metrics,
        "comparison_to_simple_ohlcv_v5_4": comparison_to_simple_ohlcv_v5_4,
        "sanity_checks": sanity_checks,
        "quality": quality,
        "safety": SAFETY_FLAGS_V6_2,
        "limitations": EXPECTED_LIMITATIONS_V6_2,
    }

    _write_json(root / MANIFEST_PATH_V6_2, manifest)
    _write_json(root / REPORT_JSON_PATH_V6_2, manifest)
    _write_json(root / SCORES_JSON_PATH_V6_2, _scores_report(manifest))
    markdown = build_advanced_ohlcv_ml_markdown_v6_2(manifest)
    _write_text(root / REPORT_MD_PATH_V6_2, markdown)
    _write_text(root / SCORES_MD_PATH_V6_2, markdown)
    _write_text(root / DOC_PATH_V6_2, markdown)
    _update_project_state(root, manifest)
    return manifest


def prepare_advanced_ohlcv_ml_frame_v6_2(dataset: pd.DataFrame) -> pd.DataFrame:
    frame = dataset[(dataset["label_valid_h1"] == True) & (dataset["warmup_row"] == False)].copy()  # noqa: E712
    return frame.reset_index(drop=True)


def validate_split_alignment_v6_2(dataset: pd.DataFrame, splits: pd.DataFrame) -> pd.DataFrame:
    missing_dataset = [column for column in SPLIT_COLUMNS_V6_1 if column not in dataset.columns]
    missing_splits = [column for column in SPLIT_COLUMNS_V6_1 if column not in splits.columns]
    if missing_dataset or missing_splits:
        raise ValueError(f"V6.2 split alignment missing dataset={missing_dataset}, missing_splits={missing_splits}")
    try:
        assert_frame_equal(
            dataset[SPLIT_COLUMNS_V6_1].reset_index(drop=True),
            splits[SPLIT_COLUMNS_V6_1].reset_index(drop=True),
            check_dtype=False,
        )
    except AssertionError as exc:
        raise ValueError("V6.2 dataset and split files are not aligned") from exc
    if dataset["walk_forward_group"].isna().any():
        raise ValueError("V6.2 dataset contains null walk_forward_group values")
    return dataset.copy()


def get_advanced_ohlcv_training_slices_v6_2(frame: pd.DataFrame) -> dict[str, pd.DataFrame]:
    return {split: frame[frame["split"] == split].copy() for split in ["train", "validation", "test"]}


def build_advanced_ohlcv_model_scores_v6_2(
    dataset: pd.DataFrame,
    *,
    dataset_sha256: str,
    ml_run_id: str,
) -> pd.DataFrame:
    ml_frame = prepare_advanced_ohlcv_ml_frame_v6_2(dataset)
    slices = get_advanced_ohlcv_training_slices_v6_2(ml_frame)
    train = slices["train"]
    if train.empty:
        return pd.DataFrame(columns=ML_SCORE_COLUMNS_V6_2)

    score_frames: list[pd.DataFrame] = []
    train_features = train[ALLOWED_FEATURE_COLUMNS_V6_2]
    train_target = train[TARGET_NAME_V6_2].astype(str)
    score_features = ml_frame[ALLOWED_FEATURE_COLUMNS_V6_2]
    feature_columns_sha256 = get_feature_columns_sha256_v6_2()

    for model_name in MODEL_NAMES_V6_2:
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
        scores["target_name"] = TARGET_NAME_V6_2
        scores["dataset_sha256"] = dataset_sha256
        scores["feature_columns_sha256"] = feature_columns_sha256
        scores["ml_schema_version"] = ML_SCHEMA_VERSION_V6_2
        scores["target_value"] = ml_frame[TARGET_NAME_V6_2].astype(str).to_numpy()
        scores["research_predicted_class"] = result.predicted_class.to_numpy()
        scores["research_probability_down"] = result.probabilities["DOWN"].to_numpy()
        scores["research_probability_flat"] = result.probabilities["FLAT"].to_numpy()
        scores["research_probability_up"] = result.probabilities["UP"].to_numpy()
        scores["prediction_available_ts"] = ml_frame["decision_ts"].to_numpy()
        scores["row_valid_for_ml"] = True
        scores["ml_null_count"] = scores.isna().sum(axis=1).astype(int)
        scores["ml_error_count"] = 0
        score_frames.append(scores[ML_SCORE_COLUMNS_V6_2])

    return pd.concat(score_frames, ignore_index=True)


def build_advanced_ohlcv_ml_markdown_v6_2(manifest: dict[str, Any]) -> str:
    lines = [
        "# Rapport qualite - V6.2 ML offline historique max",
        "",
        "## Objectif",
        "",
        "V6.2 entraine des baselines ML offline simples sur le dataset V6.1 valide avec advanced OHLCV features.",
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
        f"- Features : `{manifest['advanced_feature_columns_count']}` colonnes advanced OHLCV causales V6.0 autorisees uniquement.",
        "- `macd_like_signal` est une feature technique MACD-like autorisee, pas un signal de trading.",
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
            "- La comparaison V6.2 vs V5.4 est descriptive, non actionnable et sans conclusion de trading.",
            "",
            "## Limitations",
            "",
            *[f"- {item}" for item in manifest["limitations"]],
            "",
            "## Non-usage warnings",
            "",
            "- V6.2 ne valide aucune strategie.",
            "- V6.2 ne produit aucun backtest.",
            "- V6.2 ne produit aucun signal de trading.",
            "- V6.2 ne produit aucun ordre.",
            "- V6.2 n'autorise aucun paper live.",
            "- V6.2 n'autorise aucun trading reel.",
            "- Les metriques sont descriptives et non actionnables.",
            "- Les metriques walk-forward ne sont pas un backtest.",
            "- La comparaison V6.2 vs V5.4 est descriptive, non actionnable.",
        ]
    )
    return "\n".join(lines) + "\n"


def load_v6_1_dataset_manifest(root: Path = Path(".")) -> dict[str, Any]:
    return json.loads((root.resolve() / MANIFEST_PATH_V6_1).read_text(encoding="utf-8"))


def input_dataset_path(root: Path, timeframe: str, manifest: dict[str, Any] | None = None) -> Path:
    manifest = manifest or load_v6_1_dataset_manifest(root)
    return root.resolve() / manifest["outputs"][timeframe]["path"]


def input_split_path(root: Path, timeframe: str, manifest: dict[str, Any] | None = None) -> Path:
    manifest = manifest or load_v6_1_dataset_manifest(root)
    return root.resolve() / manifest["splits"][timeframe]["path"]


def score_output_path(root: Path, timeframe: str, window_start: str | None = None, window_end: str | None = None) -> Path:
    if window_start is None or window_end is None:
        window = _input_window(load_v6_1_dataset_manifest(root))
        window_start = window["window_start"]
        window_end = window["window_end"]
    return get_advanced_ohlcv_ml_score_path_v6_2(root.resolve(), timeframe, window_start, window_end)


def _validate_dataset_layer(root: Path) -> None:
    result = validate_advanced_ohlcv_offline_supervised_dataset_v6_1(root)
    if not result["passed"]:
        raise RuntimeError(f"V6.1 dataset validation failed before V6.2: {result['errors']}")


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
    used = prepare_advanced_ohlcv_ml_frame_v6_2(dataset)
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
    return sorted(frame[frame["split"] == split][TARGET_NAME_V6_2].dropna().astype(str).unique().tolist())


def build_comparison_to_simple_ohlcv_v5_4(root: Path, advanced_metrics: dict[str, Any]) -> dict[str, Any]:
    source_manifest_path = root / "reports/manifests/max_history_offline_ml_research_v5_4_manifest.json"
    if not source_manifest_path.exists():
        return {
            "status": "SKIPPED",
            "source_manifest_path": source_manifest_path.relative_to(root).as_posix(),
            "source_manifest_sha256": None,
            "compared_metrics": ["accuracy", "balanced_accuracy", "macro_f1"],
            "comparisons": {},
            "descriptive_only": True,
            "non_actionable": True,
            "warnings": ["V5.4 manifest not available; descriptive comparison skipped."],
        }
    source_manifest = json.loads(source_manifest_path.read_text(encoding="utf-8"))
    simple_metrics = source_manifest.get("metrics", {})
    comparisons: dict[str, dict[str, Any]] = {}
    for key, advanced_payload in sorted(advanced_metrics.items()):
        simple_payload = simple_metrics.get(key)
        if not isinstance(simple_payload, dict) or not isinstance(advanced_payload, dict):
            continue
        comparisons[key] = {
            "timeframe": advanced_payload.get("timeframe"),
            "model_name": advanced_payload.get("model_name"),
            "split": advanced_payload.get("split"),
            "accuracy_delta_v6_2_minus_v5_4": _metric_delta(advanced_payload, simple_payload, "accuracy"),
            "balanced_accuracy_delta_v6_2_minus_v5_4": _metric_delta(advanced_payload, simple_payload, "balanced_accuracy"),
            "macro_f1_delta_v6_2_minus_v5_4": _metric_delta(advanced_payload, simple_payload, "macro_f1"),
        }
    return {
        "status": "PASS",
        "source_manifest_path": source_manifest_path.relative_to(root).as_posix(),
        "source_manifest_sha256": sha256_file(source_manifest_path),
        "compared_metrics": ["accuracy", "balanced_accuracy", "macro_f1"],
        "comparisons": comparisons,
        "descriptive_only": True,
        "non_actionable": True,
        "warnings": [],
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
        "comparison_to_simple_ohlcv_v5_4": manifest["comparison_to_simple_ohlcv_v5_4"],
    }


def _update_project_state(root: Path, manifest: dict[str, Any]) -> None:
    state_path = root / "reports/PROJECT_STATE.json"
    state = json.loads(state_path.read_text(encoding="utf-8")) if state_path.exists() else {}
    window = manifest["input_dataset_manifest"]
    rows = {timeframe: payload["rows"] for timeframe, payload in manifest["outputs"].items()}
    state.update(
        {
            "last_validated_version": "V6.1",
            "candidate_version": "V6.2",
            "candidate_status": "pending_external_audit",
            "direction": "max historical offline ML with advanced OHLCV features",
            "v6_2_candidate": True,
            "advanced_ohlcv_offline_ml_research_v6_2_created": True,
            "advanced_ohlcv_ml_window_start_v6_2": window["window_start"],
            "advanced_ohlcv_ml_window_end_v6_2": window["window_end"],
            "advanced_ohlcv_ml_days_v6_2": window["total_days"],
            "advanced_ohlcv_ml_score_rows_v6_2": rows,
            "advanced_feature_columns_count_v6_2": manifest["advanced_feature_columns_count"],
            "advanced_ohlcv_ml_models_v6_2": MODEL_NAMES_V6_2,
            "advanced_ohlcv_ml_target_v6_2": TARGET_NAME_V6_2,
            "backtest_v6_2_created": False,
            "strategy_v6_2_created": False,
            "signal_v6_2_created": False,
            "orders_v6_2_created": False,
            "paper_live_v6_2_created": False,
            "trading_v6_2_created": False,
            "persistent_model_v6_2_created": False,
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


def _build_latest_metrics(manifest: dict[str, Any], state: dict[str, Any]) -> dict[str, Any]:
    window = manifest["input_dataset_manifest"]
    return {
        "last_validated_version": "V6.1",
        "candidate_version": "V6.2",
        "candidate_status": "pending_external_audit",
        "direction": state["direction"],
        "advanced_ohlcv_ml_window_start_v6_2": window["window_start"],
        "advanced_ohlcv_ml_window_end_v6_2": window["window_end"],
        "advanced_ohlcv_ml_days_v6_2": window["total_days"],
        "advanced_ohlcv_ml_score_rows_v6_2": {timeframe: payload["rows"] for timeframe, payload in manifest["outputs"].items()},
        "advanced_feature_columns_count_v6_2": manifest["advanced_feature_columns_count"],
        "advanced_ohlcv_ml_models_v6_2": manifest["models"],
        "advanced_ohlcv_ml_target_v6_2": manifest["target_name"],
        "ml_schema_version_v6_2": ML_SCHEMA_VERSION_V6_2,
        "ml_score_columns_count_v6_2": len(ML_SCORE_COLUMNS_V6_2),
        "walk_forward_metrics_v6_2": True,
        "backtest_v6_2_created": False,
        "strategy_v6_2_created": False,
        "signal_v6_2_created": False,
        "orders_v6_2_created": False,
        "paper_live_v6_2_created": False,
        "persistent_model_v6_2_created": False,
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
    return f"""# Etat du Projet : V6.1 validee + candidat V6.2

- **Derniere version validee** : V6.1.
- **Version candidate** : V6.2.
- **Statut candidate** : `pending_external_audit`.
- **Direction suivante** : max historical offline ML with advanced OHLCV features.

## Candidat V6.2

- Fenetre V5.0 utilisee : `{window['window_start']}` -> `{window['window_end']}`.
- Nombre de jours : `{window['total_days']}`.
- Row counts scores : `{rows}`.
- Schema : `ML_SCORE_COLUMNS_V6_2`.
- Cible : `{manifest['target_name']}`.
- Advanced feature columns : `{manifest['advanced_feature_columns_count']}`.
- Modeles offline autorises : `{manifest['models']}`.
- Metriques walk-forward : descriptives uniquement, pas un backtest.
- Comparaison V6.2 vs V5.4 : descriptive uniquement, non actionnable.
- V6.2 reste candidate `pending_external_audit`.

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
- V6.2 reste non validee avant audit externe.
"""


def _build_latest_metrics_markdown(manifest: dict[str, Any]) -> str:
    window = manifest["input_dataset_manifest"]
    rows = "\n".join(f"- {timeframe}: `{payload['rows']}`" for timeframe, payload in manifest["outputs"].items())
    return f"""# Latest Metrics V6.2

- Derniere version validee : V6.1.
- Candidate : V6.2.
- Statut : `pending_external_audit`.
- Direction : max historical offline ML with advanced OHLCV features.
- Fenetre : `{window['window_start']}` -> `{window['window_end']}`.
- Total jours : `{window['total_days']}`.
- Cible : `{manifest['target_name']}`.
- Advanced feature columns : `{manifest['advanced_feature_columns_count']}`.
- Modeles : `{manifest['models']}`.
- Metriques walk-forward : descriptives uniquement.

## Row counts scores

{rows}

Aucun backtest, aucune strategie, aucun signal de trading, aucun ordre, aucun modele persistant et aucun trading reel.
"""


def _build_latest_summary_markdown(manifest: dict[str, Any]) -> str:
    window = manifest["input_dataset_manifest"]
    rows = {timeframe: payload["rows"] for timeframe, payload in manifest["outputs"].items()}
    return f"""# Latest Summary V6.2

V6.1 est la derniere version validee par audit externe.

V6.2 est la candidate courante. Elle entraine uniquement des baselines ML offline simples sur le dataset V6.1 avec advanced OHLCV features, produit des scores de recherche `research_*`, calcule des metriques descriptives par split et par groupe walk-forward, et compare descriptivement V6.2 a V5.4 si disponible.

Fenetre utilisee : `{window['window_start']}` -> `{window['window_end']}`.

Total jours : `{window['total_days']}`.

Row counts scores : `{rows}`.

Advanced feature columns : `{manifest['advanced_feature_columns_count']}`.

Aucun trading, aucun paper live, aucun ordre, aucun backtest, aucune strategie, aucun signal de trading, aucun modele persistant et aucun claim de rentabilite.

V6.2 reste `pending_external_audit`.
"""


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
