from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from galapagos.data.public_market.provenance import sha256_file
from galapagos.datasets.ohlcv_trades_1y_window_validation import validate_ohlcv_trades_1y_offline_supervised_dataset_v8_4
from galapagos.features.ohlcv_trades_feature_selection import build_leakage_guard_v8_9, is_forbidden_feature_v8_9
from galapagos.features.ohlcv_trades_feature_selection_schemas import (
    ALLOWED_FEATURE_COLUMNS_V8_9,
    ATTESTATION_JSON_V8_9,
    DOC_PATH_V8_9,
    EXPECTED_LIMITATIONS_V8_9,
    FINDINGS_FALSE_FIELDS_V8_9,
    FORBIDDEN_MARKDOWN_CLAIMS_V8_9,
    INPUT_DATASET_MANIFEST_PATH_V8_9,
    INPUT_DECISION_JSON_PATH_V8_9,
    INPUT_FEATURE_MANIFEST_PATH_V8_9,
    INPUT_FEATURE_REPORT_PATH_V8_9,
    INPUT_ML_MANIFEST_PATH_V8_9,
    INPUT_ML_REPORT_PATH_V8_9,
    INPUT_WALK_FORWARD_MANIFEST_PATH_V8_9,
    INPUT_WALK_FORWARD_REPORT_PATH_V8_9,
    MANIFEST_PATH_V8_9,
    REPORT_JSON_PATH_V8_9,
    REPORT_MD_PATH_V8_9,
    SAFETY_FLAGS_V8_9,
    SELECTION_JSON_PATH_V8_9,
    SELECTION_MD_PATH_V8_9,
    VERSION_V8_9,
)
from galapagos.validation.safety import validate_exact_keys, validate_markdown_forbidden_claims


MANIFEST_KEYS_V8_9 = {
    "version",
    "status",
    "created_at_utc",
    "feature_audit_run_id",
    "input_dataset_manifest",
    "input_feature_manifest",
    "input_feature_report",
    "input_ml_manifest",
    "input_walk_forward_manifest",
    "input_decision_gate_v8_8",
    "feature_inventory",
    "missingness_summary",
    "variance_summary",
    "collinearity_summary",
    "feature_family_balance",
    "stability_by_timeframe",
    "candidate_refined_feature_set",
    "leakage_guard",
    "findings",
    "safety",
    "limitations",
}
SELECTION_REPORT_KEYS_V8_9 = {
    "version",
    "status",
    "created_at_utc",
    "feature_audit_run_id",
    "candidate_refined_feature_set",
    "feature_family_balance",
    "leakage_guard",
    "findings",
    "safety",
    "limitations",
}
FORBIDDEN_ARTIFACT_ROOTS_V8_9 = [
    Path("data/research/v8_9/datasets"),
    Path("data/research/v8_9/ml"),
    Path("data/research/v8_9/backtests"),
    Path("reports/backtests"),
    Path("reports/strategies"),
    Path("orders"),
    Path("execution"),
    Path("models"),
    Path("checkpoints"),
]
PERSISTENT_MODEL_SUFFIXES = {".pkl", ".pickle", ".joblib", ".ckpt", ".pt", ".pth", ".onnx"}
IGNORED_SCAN_PARTS = {".git", ".venv", "__pycache__", ".pytest_cache", ".ruff_cache", ".mypy_cache"}


def validate_ohlcv_trades_feature_audit_v8_9(project_root: Path = Path(".")) -> dict[str, Any]:
    root = project_root.resolve()
    warnings: list[str] = []
    errors: list[str] = []
    for relative in [
        INPUT_DATASET_MANIFEST_PATH_V8_9,
        INPUT_FEATURE_MANIFEST_PATH_V8_9,
        INPUT_FEATURE_REPORT_PATH_V8_9,
        INPUT_ML_MANIFEST_PATH_V8_9,
        INPUT_ML_REPORT_PATH_V8_9,
        INPUT_DECISION_JSON_PATH_V8_9,
    ]:
        if not (root / relative).exists():
            errors.append(f"missing V8.9 input: {relative}")
    for relative in [MANIFEST_PATH_V8_9, REPORT_JSON_PATH_V8_9, SELECTION_JSON_PATH_V8_9, REPORT_MD_PATH_V8_9, SELECTION_MD_PATH_V8_9, DOC_PATH_V8_9]:
        if not (root / relative).exists():
            errors.append(f"missing V8.9 output: {relative}")
    if errors:
        return _result(errors, warnings)
    if _v8_4_full_dataset_files_available(root):
        dataset_result = validate_ohlcv_trades_1y_offline_supervised_dataset_v8_4(root)
        if not dataset_result["passed"]:
            errors.append(f"V8.4 dataset validation failed before V8.9 validation: {dataset_result['errors']}")
            return _result(errors, warnings)
    else:
        warnings.append("V8.4 full Parquet artifacts absent; using V8.9 audit-lite input manifest validation.")
        errors.extend(_validate_audit_lite_input_files_v8_9(root))
        if errors:
            return _result(errors, warnings)

    manifest = _load_json(root / MANIFEST_PATH_V8_9)
    report = _load_json(root / REPORT_JSON_PATH_V8_9)
    selection_report = _load_json(root / SELECTION_JSON_PATH_V8_9)
    errors.extend(validate_feature_audit_manifest_payload_v8_9(manifest, root))
    if report != manifest:
        errors.append("V8.9 feature audit report JSON must match manifest")
    errors.extend(validate_feature_selection_report_payload_v8_9(selection_report, manifest))
    for relative in [REPORT_MD_PATH_V8_9, SELECTION_MD_PATH_V8_9, DOC_PATH_V8_9]:
        errors.extend(validate_feature_audit_markdown_v8_9((root / relative).read_text(encoding="utf-8"), str(relative)))
    errors.extend(find_forbidden_v8_9_artifacts(root))
    return _result(errors, warnings, manifest)


def _v8_4_full_dataset_files_available(root: Path) -> bool:
    dataset_manifest_path = root / INPUT_DATASET_MANIFEST_PATH_V8_9
    if not dataset_manifest_path.exists():
        return False
    try:
        dataset_manifest = _load_json(dataset_manifest_path)
    except json.JSONDecodeError:
        return False
    paths: list[str] = []
    for block_name in ["outputs", "splits"]:
        block = dataset_manifest.get(block_name, {})
        if not isinstance(block, dict):
            return False
        for item in block.values():
            if not isinstance(item, dict) or not item.get("path"):
                return False
            paths.append(str(item["path"]))
    return bool(paths) and all((root / path).exists() for path in paths)


def _validate_audit_lite_input_files_v8_9(root: Path) -> list[str]:
    errors: list[str] = []
    manifest = _load_json(root / MANIFEST_PATH_V8_9)
    required = [
        INPUT_DATASET_MANIFEST_PATH_V8_9,
        INPUT_FEATURE_MANIFEST_PATH_V8_9,
        INPUT_FEATURE_REPORT_PATH_V8_9,
        INPUT_ML_MANIFEST_PATH_V8_9,
        INPUT_ML_REPORT_PATH_V8_9,
        INPUT_DECISION_JSON_PATH_V8_9,
    ]
    if manifest.get("input_walk_forward_manifest", {}).get("available") is True:
        required.append(INPUT_WALK_FORWARD_MANIFEST_PATH_V8_9)
        required.append(INPUT_WALK_FORWARD_REPORT_PATH_V8_9)
    for relative in required:
        if not (root / relative).exists():
            errors.append(f"missing V8.9 audit-lite input: {relative}")
    if errors:
        return errors
    expected_hashes = [
        (manifest.get("input_dataset_manifest", {}).get("sha256"), INPUT_DATASET_MANIFEST_PATH_V8_9, "input_dataset_manifest"),
        (manifest.get("input_feature_manifest", {}).get("sha256"), INPUT_FEATURE_MANIFEST_PATH_V8_9, "input_feature_manifest"),
        (manifest.get("input_feature_report", {}).get("sha256"), INPUT_FEATURE_REPORT_PATH_V8_9, "input_feature_report"),
        (manifest.get("input_ml_manifest", {}).get("sha256"), INPUT_ML_MANIFEST_PATH_V8_9, "input_ml_manifest"),
        (manifest.get("input_decision_gate_v8_8", {}).get("sha256"), INPUT_DECISION_JSON_PATH_V8_9, "input_decision_gate_v8_8"),
    ]
    if manifest.get("input_walk_forward_manifest", {}).get("available") is True:
        expected_hashes.append((manifest.get("input_walk_forward_manifest", {}).get("sha256"), INPUT_WALK_FORWARD_MANIFEST_PATH_V8_9, "input_walk_forward_manifest"))
    for expected, relative, label in expected_hashes:
        if expected != sha256_file(root / relative):
            errors.append(f"V8.9 audit-lite {label}.sha256 mismatch")
    for relative, version in [
        (INPUT_DATASET_MANIFEST_PATH_V8_9, "V8.4"),
        (INPUT_FEATURE_MANIFEST_PATH_V8_9, "V8.3"),
        (INPUT_ML_MANIFEST_PATH_V8_9, "V8.5"),
    ]:
        payload = _load_json(root / relative)
        if payload.get("version") != version or payload.get("status") != "PASS":
            errors.append(f"V8.9 audit-lite input {relative} must be {version} PASS")
    return errors


def validate_feature_audit_manifest_payload_v8_9(payload: dict[str, Any], root: Path | None = None) -> list[str]:
    errors: list[str] = []
    errors.extend(validate_exact_keys(payload, MANIFEST_KEYS_V8_9, "V8.9 manifest"))
    if payload.get("version") != VERSION_V8_9:
        errors.append("V8.9 manifest version mismatch")
    if payload.get("status") != "PASS":
        errors.append("V8.9 manifest status must be PASS")
    if not isinstance(payload.get("feature_inventory"), list) or not payload["feature_inventory"]:
        errors.append("V8.9 feature_inventory must be non-empty")
    candidate = payload.get("candidate_refined_feature_set", {})
    errors.extend(validate_candidate_refined_feature_set_v8_9(candidate))
    if payload.get("leakage_guard") != build_leakage_guard_v8_9(candidate.get("selected_features", [])):
        errors.append("V8.9 leakage_guard mismatch")
    if payload.get("leakage_guard", {}).get("passed") is not True:
        errors.append("V8.9 leakage_guard.passed must be true")
    findings = payload.get("findings", {})
    for field in FINDINGS_FALSE_FIELDS_V8_9:
        if findings.get(field) is not False:
            errors.append(f"V8.9 findings.{field} must be false")
    if payload.get("safety") != SAFETY_FLAGS_V8_9:
        errors.append("V8.9 safety flags mismatch")
    if payload.get("limitations") != EXPECTED_LIMITATIONS_V8_9:
        errors.append("V8.9 limitations mismatch")
    if root is not None:
        input_dataset = payload.get("input_dataset_manifest", {})
        if input_dataset.get("sha256") != sha256_file(root / INPUT_DATASET_MANIFEST_PATH_V8_9):
            errors.append("V8.9 input_dataset_manifest.sha256 mismatch")
        input_feature = payload.get("input_feature_manifest", {})
        if input_feature.get("sha256") != sha256_file(root / INPUT_FEATURE_MANIFEST_PATH_V8_9):
            errors.append("V8.9 input_feature_manifest.sha256 mismatch")
    return errors


def validate_candidate_refined_feature_set_v8_9(candidate: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    selected = candidate.get("selected_features", [])
    dropped = candidate.get("dropped_features", [])
    review = candidate.get("review_features", [])
    if not selected:
        errors.append("V8.9 selected_features must be non-empty")
    unknown = sorted(set(selected) - set(ALLOWED_FEATURE_COLUMNS_V8_9))
    if unknown:
        errors.append(f"V8.9 selected_features outside allowed features: {unknown}")
    forbidden = sorted(feature for feature in selected if is_forbidden_feature_v8_9(feature))
    if forbidden:
        errors.append(f"V8.9 selected_features contain forbidden features: {forbidden}")
    if candidate.get("selected_features_count") != len(selected):
        errors.append("V8.9 selected_features_count mismatch")
    if candidate.get("dropped_features_count") != len(dropped):
        errors.append("V8.9 dropped_features_count mismatch")
    if candidate.get("review_features_count") != len(review):
        errors.append("V8.9 review_features_count mismatch")
    if set(selected) & set(dropped):
        errors.append("V8.9 selected and dropped features overlap")
    if set(selected) & set(review):
        errors.append("V8.9 selected and review features overlap")
    return errors


def validate_feature_selection_report_payload_v8_9(payload: dict[str, Any], manifest: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    errors.extend(validate_exact_keys(payload, SELECTION_REPORT_KEYS_V8_9, "V8.9 selection report"))
    for key in ["version", "status", "created_at_utc", "feature_audit_run_id", "candidate_refined_feature_set", "leakage_guard", "findings", "safety", "limitations"]:
        if payload.get(key) != manifest.get(key):
            errors.append(f"V8.9 selection report {key} mismatch")
    return errors


def validate_feature_audit_markdown_v8_9(text: str, label: str) -> list[str]:
    errors = validate_markdown_forbidden_claims(text, label)
    lowered = text.casefold()
    errors.extend(f"{label} contains forbidden claim: {claim}" for claim in FORBIDDEN_MARKDOWN_CLAIMS_V8_9 if claim in lowered)
    for required in [
        "V8.9 ne valide aucune strategie",
        "V8.9 ne produit aucun backtest",
        "V8.9 ne produit aucun signal de trading",
        "V8.9 ne produit aucun ordre",
    ]:
        if required.casefold() not in lowered:
            errors.append(f"{label} missing required statement: {required}")
    return errors


def find_forbidden_v8_9_artifacts(root: Path) -> list[str]:
    errors: list[str] = []
    for relative in FORBIDDEN_ARTIFACT_ROOTS_V8_9:
        if (root / relative).exists():
            errors.append(f"Forbidden V8.9 artifact detected: {relative}")
    for path in root.rglob("*"):
        if not path.is_file() or any(part in IGNORED_SCAN_PARTS for part in path.parts):
            continue
        if path.suffix.casefold() in PERSISTENT_MODEL_SUFFIXES:
            errors.append(f"Forbidden V8.9 persistent model artifact detected: {path.relative_to(root)}")
    return errors


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _result(errors: list[str], warnings: list[str], report: dict[str, Any] | None = None) -> dict[str, Any]:
    return {"version": VERSION_V8_9, "passed": not errors, "errors": errors, "warnings": warnings, "report": report}
