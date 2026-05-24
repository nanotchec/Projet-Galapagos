from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd

from galapagos.data.public_market.provenance import sha256_file, utc_now_iso
from galapagos.data.public_market.storage import read_parquet, write_parquet
from galapagos.datasets.max_history_window_validation import validate_max_history_offline_supervised_dataset_v5_3
from galapagos.datasets.schemas import MANIFEST_PATH_V5_3
from galapagos.ml.max_history_window_metrics import (
    compute_max_history_classification_metrics_v5_4,
    compute_max_history_walk_forward_metrics_v5_4,
)
from galapagos.ml.max_history_window_quality import assess_max_history_ml_quality_v5_4
from galapagos.ml.offline_baselines import fit_predict_model
from galapagos.ml.schemas import (
    ALLOWED_FEATURE_COLUMNS_V5_4,
    DOC_PATH_V5_4,
    EXPECTED_LIMITATIONS_V5_4,
    MANIFEST_PATH_V5_4,
    ML_SCHEMA_VERSION_V5_4,
    ML_SCORE_COLUMNS_V5_4,
    MODEL_NAMES_V5_4,
    REPORT_JSON_PATH_V5_4,
    REPORT_MD_PATH_V5_4,
    SAFETY_FLAGS_V5_4,
    SCORES_JSON_PATH_V5_4,
    SCORES_MD_PATH_V5_4,
    TARGET_NAME_V5_4,
    TIMEFRAMES_V5_4,
    VERSION_V5_4,
    get_feature_columns_sha256_v5_4,
    get_max_history_ml_score_path_v5_4,
)


def run_max_history_offline_ml_research_v5_4(
    root: Path = Path("."),
    *,
    validate_dataset: bool = True,
) -> dict[str, Any]:
    root = root.resolve()
    if validate_dataset:
        _validate_dataset_layer(root)

    dataset_manifest = load_v5_3_dataset_manifest(root)
    window = _input_window(dataset_manifest)
    window_start = window["window_start"]
    window_end = window["window_end"]
    total_days = int(window["total_days"])

    created_at = utc_now_iso()
    ml_run_id = f"v5_4_{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}_{uuid.uuid4().hex[:8]}"
    input_datasets: dict[str, dict[str, Any]] = {}
    input_splits: dict[str, dict[str, Any]] = {}
    outputs: dict[str, dict[str, Any]] = {}
    metrics: dict[str, Any] = {}
    walk_forward_metrics: dict[str, Any] = {}
    quality: dict[str, dict[str, Any]] = {}
    sanity_checks: dict[str, dict[str, Any]] = {}
    status = "PASS"

    for timeframe in TIMEFRAMES_V5_4:
        dataset_path = input_dataset_path(root, timeframe, dataset_manifest)
        split_path = input_split_path(root, timeframe, dataset_manifest)
        score_path = score_output_path(root, timeframe, window_start, window_end)
        dataset = read_parquet(dataset_path)
        splits = read_parquet(split_path)
        dataset_for_ml = attach_walk_forward_groups_v5_4(dataset, splits)
        dataset_sha = sha256_file(dataset_path)

        scores = build_max_history_model_scores_v5_4(dataset_for_ml, dataset_sha256=dataset_sha, ml_run_id=ml_run_id)
        write_parquet(scores, score_path)

        input_datasets[timeframe] = _input_block(root, dataset_path, dataset_sha, len(dataset))
        input_splits[timeframe] = _input_block(root, split_path, sha256_file(split_path), len(splits))
        outputs[timeframe] = _output_block(root, score_path, len(scores))
        quality[timeframe] = assess_max_history_ml_quality_v5_4(dataset_for_ml, scores, timeframe)
        if quality[timeframe]["errors"]:
            status = "FAIL"
        sanity_checks[timeframe] = _sanity_from_quality(dataset_for_ml, quality[timeframe])
        metrics.update(compute_max_history_classification_metrics_v5_4(scores))
        walk_forward_metrics.update(compute_max_history_walk_forward_metrics_v5_4(scores))

    manifest = {
        "version": VERSION_V5_4,
        "status": status,
        "created_at_utc": created_at,
        "ml_run_id": ml_run_id,
        "input_dataset_manifest": {
            "path": MANIFEST_PATH_V5_3.as_posix(),
            "sha256": sha256_file(root / MANIFEST_PATH_V5_3),
            "window_start": window_start,
            "window_end": window_end,
            "total_days": total_days,
        },
        "input_datasets": input_datasets,
        "input_splits": input_splits,
        "outputs": outputs,
        "target_name": TARGET_NAME_V5_4,
        "feature_columns": ALLOWED_FEATURE_COLUMNS_V5_4,
        "models": MODEL_NAMES_V5_4,
        "metrics": metrics,
        "walk_forward_metrics": walk_forward_metrics,
        "sanity_checks": sanity_checks,
        "quality": quality,
        "safety": SAFETY_FLAGS_V5_4,
        "limitations": EXPECTED_LIMITATIONS_V5_4,
    }

    _write_json(root / MANIFEST_PATH_V5_4, manifest)
    _write_json(root / REPORT_JSON_PATH_V5_4, manifest)
    _write_json(root / SCORES_JSON_PATH_V5_4, _scores_report(manifest))
    markdown = build_max_history_ml_markdown_v5_4(manifest)
    _write_text(root / REPORT_MD_PATH_V5_4, markdown)
    _write_text(root / SCORES_MD_PATH_V5_4, markdown)
    _write_text(root / DOC_PATH_V5_4, markdown)
    _update_project_state(root, manifest)
    return manifest


def prepare_max_history_ml_frame_v5_4(dataset: pd.DataFrame) -> pd.DataFrame:
    frame = dataset[(dataset["label_valid_h1"] == True) & (dataset["warmup_row"] == False)].copy()  # noqa: E712
    return frame.reset_index(drop=True)


def attach_walk_forward_groups_v5_4(dataset: pd.DataFrame, splits: pd.DataFrame) -> pd.DataFrame:
    merge_keys = [
        "source",
        "venue",
        "market_type",
        "symbol",
        "timeframe",
        "event_ts",
        "close_ts",
        "available_ts",
        "decision_ts",
        "split",
        "split_order",
        "purge_embargo_group",
    ]
    missing_dataset = [column for column in merge_keys if column not in dataset.columns]
    missing_splits = [column for column in [*merge_keys, "walk_forward_group"] if column not in splits.columns]
    if missing_dataset or missing_splits:
        raise ValueError(f"V5.4 cannot attach walk_forward_group: missing dataset={missing_dataset}, missing_splits={missing_splits}")
    enriched = dataset.merge(splits[[*merge_keys, "walk_forward_group"]], on=merge_keys, how="left", validate="one_to_one")
    if enriched["walk_forward_group"].isna().any():
        raise ValueError("V5.4 split enrichment produced null walk_forward_group values")
    return enriched


def get_max_history_training_slices_v5_4(frame: pd.DataFrame) -> dict[str, pd.DataFrame]:
    return {split: frame[frame["split"] == split].copy() for split in ["train", "validation", "test"]}


def build_max_history_model_scores_v5_4(
    dataset: pd.DataFrame,
    *,
    dataset_sha256: str,
    ml_run_id: str,
) -> pd.DataFrame:
    ml_frame = prepare_max_history_ml_frame_v5_4(dataset)
    slices = get_max_history_training_slices_v5_4(ml_frame)
    train = slices["train"]
    if train.empty:
        return pd.DataFrame(columns=ML_SCORE_COLUMNS_V5_4)

    score_frames: list[pd.DataFrame] = []
    train_features = train[ALLOWED_FEATURE_COLUMNS_V5_4]
    train_target = train[TARGET_NAME_V5_4].astype(str)
    feature_columns_sha256 = get_feature_columns_sha256_v5_4()

    for model_name in MODEL_NAMES_V5_4:
        for split_name, split_frame in slices.items():
            if split_frame.empty:
                continue
            result = fit_predict_model(
                model_name,
                train_features,
                train_target,
                split_frame[ALLOWED_FEATURE_COLUMNS_V5_4],
            )
            scores = split_frame[
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
            scores["target_name"] = TARGET_NAME_V5_4
            scores["dataset_sha256"] = dataset_sha256
            scores["feature_columns_sha256"] = feature_columns_sha256
            scores["ml_schema_version"] = ML_SCHEMA_VERSION_V5_4
            scores["target_value"] = split_frame[TARGET_NAME_V5_4].astype(str).to_numpy()
            scores["research_predicted_class"] = result.predicted_class.to_numpy()
            scores["research_probability_down"] = result.probabilities["DOWN"].to_numpy()
            scores["research_probability_flat"] = result.probabilities["FLAT"].to_numpy()
            scores["research_probability_up"] = result.probabilities["UP"].to_numpy()
            scores["prediction_available_ts"] = split_frame["decision_ts"].to_numpy()
            scores["row_valid_for_ml"] = True
            scores["ml_null_count"] = scores.isna().sum(axis=1).astype(int)
            scores["ml_error_count"] = 0
            score_frames.append(scores[ML_SCORE_COLUMNS_V5_4])

    return pd.concat(score_frames, ignore_index=True)


def build_max_history_ml_markdown_v5_4(manifest: dict[str, Any]) -> str:
    lines = [
        "# Rapport qualite - V5.4 ML offline historique max",
        "",
        "## Objectif",
        "",
        "V5.4 entraine des baselines ML offline simples sur le dataset historique V5.3 valide.",
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
        "- Features : colonnes causales V5.1 autorisees uniquement.",
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
            "",
            "## Limitations",
            "",
            *[f"- {item}" for item in manifest["limitations"]],
            "",
            "## Non-usage warnings",
            "",
            "- V5.4 ne valide aucune strategie.",
            "- V5.4 ne produit aucun backtest.",
            "- V5.4 ne produit aucun signal de trading.",
            "- V5.4 ne produit aucun ordre.",
            "- V5.4 n'autorise aucun paper live.",
            "- V5.4 n'autorise aucun trading reel.",
            "- Les metriques sont descriptives et non actionnables.",
            "- Les metriques walk-forward ne sont pas un backtest.",
        ]
    )
    return "\n".join(lines) + "\n"


def load_v5_3_dataset_manifest(root: Path = Path(".")) -> dict[str, Any]:
    return json.loads((root.resolve() / MANIFEST_PATH_V5_3).read_text(encoding="utf-8"))


def input_dataset_path(root: Path, timeframe: str, manifest: dict[str, Any] | None = None) -> Path:
    manifest = manifest or load_v5_3_dataset_manifest(root)
    return root.resolve() / manifest["outputs"][timeframe]["path"]


def input_split_path(root: Path, timeframe: str, manifest: dict[str, Any] | None = None) -> Path:
    manifest = manifest or load_v5_3_dataset_manifest(root)
    return root.resolve() / manifest["splits"][timeframe]["path"]


def score_output_path(root: Path, timeframe: str, window_start: str | None = None, window_end: str | None = None) -> Path:
    if window_start is None or window_end is None:
        window = _input_window(load_v5_3_dataset_manifest(root))
        window_start = window["window_start"]
        window_end = window["window_end"]
    return get_max_history_ml_score_path_v5_4(root.resolve(), timeframe, window_start, window_end)


def _validate_dataset_layer(root: Path) -> None:
    result = validate_max_history_offline_supervised_dataset_v5_3(root)
    if not result["passed"]:
        raise RuntimeError(f"V5.3 dataset validation failed before V5.4: {result['errors']}")


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
    used = prepare_max_history_ml_frame_v5_4(dataset)
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
    return sorted(frame[frame["split"] == split][TARGET_NAME_V5_4].dropna().astype(str).unique().tolist())


def _scores_report(manifest: dict[str, Any]) -> dict[str, Any]:
    return {
        "version": manifest["version"],
        "ml_run_id": manifest["ml_run_id"],
        "outputs": manifest["outputs"],
        "metrics": manifest["metrics"],
        "walk_forward_metrics": manifest["walk_forward_metrics"],
    }


def _update_project_state(root: Path, manifest: dict[str, Any]) -> None:
    state_path = root / "reports/PROJECT_STATE.json"
    state = json.loads(state_path.read_text(encoding="utf-8")) if state_path.exists() else {}
    window = manifest["input_dataset_manifest"]
    rows = {timeframe: payload["rows"] for timeframe, payload in manifest["outputs"].items()}
    state.update(
        {
            "last_validated_version": "V5.3",
            "candidate_version": "V5.4",
            "candidate_status": "pending_external_audit",
            "direction": "max historical offline ML research baselines",
            "v5_4_candidate": True,
            "max_history_offline_ml_research_v5_4_created": True,
            "max_history_ml_window_start_v5_4": window["window_start"],
            "max_history_ml_window_end_v5_4": window["window_end"],
            "max_history_ml_days_v5_4": window["total_days"],
            "max_history_ml_score_rows_v5_4": rows,
            "max_history_ml_models_v5_4": MODEL_NAMES_V5_4,
            "max_history_ml_target_v5_4": TARGET_NAME_V5_4,
            "backtest_v5_4_created": False,
            "strategy_v5_4_created": False,
            "signal_v5_4_created": False,
            "orders_v5_4_created": False,
            "paper_live_v5_4_created": False,
            "trading_v5_4_created": False,
            "persistent_model_v5_4_created": False,
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
        "last_validated_version": "V5.3",
        "candidate_version": "V5.4",
        "candidate_status": "pending_external_audit",
        "direction": state["direction"],
        "max_history_ml_window_start_v5_4": window["window_start"],
        "max_history_ml_window_end_v5_4": window["window_end"],
        "max_history_ml_days_v5_4": window["total_days"],
        "max_history_ml_score_rows_v5_4": {timeframe: payload["rows"] for timeframe, payload in manifest["outputs"].items()},
        "max_history_ml_models_v5_4": manifest["models"],
        "max_history_ml_target_v5_4": manifest["target_name"],
        "ml_schema_version_v5_4": ML_SCHEMA_VERSION_V5_4,
        "ml_score_columns_count_v5_4": len(ML_SCORE_COLUMNS_V5_4),
        "walk_forward_metrics_v5_4": True,
        "backtest_v5_4_created": False,
        "strategy_v5_4_created": False,
        "signal_v5_4_created": False,
        "orders_v5_4_created": False,
        "paper_live_v5_4_created": False,
        "persistent_model_v5_4_created": False,
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
    return f"""# Etat du Projet : V5.3 validee + candidat V5.4

- **Derniere version validee** : V5.3.
- **Version candidate** : V5.4.
- **Statut candidate** : `pending_external_audit`.
- **Direction suivante** : max historical offline ML research baselines.

## Candidat V5.4

- Fenetre V5.0 utilisee : `{window['window_start']}` -> `{window['window_end']}`.
- Nombre de jours : `{window['total_days']}`.
- Row counts scores : `{rows}`.
- Schema : `ML_SCORE_COLUMNS_V5_4`.
- Cible : `{manifest['target_name']}`.
- Modeles offline autorises : `{manifest['models']}`.
- Metriques walk-forward : descriptives uniquement, pas un backtest.
- V5.4 reste candidate `pending_external_audit`.

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
- V5.4 reste non validee avant audit externe.
"""


def _build_latest_metrics_markdown(manifest: dict[str, Any]) -> str:
    window = manifest["input_dataset_manifest"]
    rows = "\n".join(f"- {timeframe}: `{payload['rows']}`" for timeframe, payload in manifest["outputs"].items())
    return f"""# Latest Metrics V5.4

- Derniere version validee : V5.3.
- Candidate : V5.4.
- Statut : `pending_external_audit`.
- Direction : max historical offline ML research baselines.
- Fenetre : `{window['window_start']}` -> `{window['window_end']}`.
- Total jours : `{window['total_days']}`.
- Cible : `{manifest['target_name']}`.
- Modeles : `{manifest['models']}`.
- Metriques walk-forward : descriptives uniquement.

## Row counts scores

{rows}

Aucun backtest, aucune strategie, aucun signal de trading, aucun ordre, aucun modele persistant et aucun trading reel.
"""


def _build_latest_summary_markdown(manifest: dict[str, Any]) -> str:
    window = manifest["input_dataset_manifest"]
    rows = {timeframe: payload["rows"] for timeframe, payload in manifest["outputs"].items()}
    return f"""# Latest Summary V5.4

V5.3 est la derniere version validee par audit externe.

V5.4 est la candidate courante. Elle entraine uniquement des baselines ML offline simples sur le dataset historique V5.3, produit des scores de recherche `research_*` et calcule des metriques descriptives par split et par groupe walk-forward.

Fenetre utilisee : `{window['window_start']}` -> `{window['window_end']}`.

Total jours : `{window['total_days']}`.

Row counts scores : `{rows}`.

Aucun trading, aucun paper live, aucun ordre, aucun backtest, aucune strategie, aucun signal de trading, aucun modele persistant et aucun claim de rentabilite.

V5.4 reste `pending_external_audit`.
"""


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
