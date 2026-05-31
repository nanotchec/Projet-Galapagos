from __future__ import annotations

import argparse
import json
import tempfile
import zipfile
from pathlib import Path
from typing import Any

from _bootstrap import bootstrap_src_path

bootstrap_src_path()


VERSION = "V9.52_to_V9.55"
ZIP_NAME = "projet-galapagos-v9.52-to-v9.55-audit-lite.zip"
REQUIRED_FILES = [
    "src/galapagos/research/derivatives_source_readiness_v9_52.py",
    "src/galapagos/data/derivatives_funding_oi_collection_v9_53.py",
    "src/galapagos/features/derivatives_funding_oi_feature_store_v9_54.py",
    "src/galapagos/features/derivatives_funding_oi_feature_store_validation_v9_55.py",
    "scripts/run_derivatives_source_readiness_v9_52.py",
    "scripts/run_derivatives_funding_oi_collection_v9_53.py",
    "scripts/run_derivatives_funding_oi_feature_store_v9_54.py",
    "scripts/run_derivatives_funding_oi_feature_store_validation_v9_55.py",
    "scripts/release_audit_lite_zip_v9_52_to_v9_55.py",
    "scripts/audit_audit_lite_zip_v9_52_to_v9_55.py",
    "scripts/smoke_audit_lite_zip_v9_52_to_v9_55.py",
    "reports/research_decisions/derivatives_source_readiness_v9_52.json",
    "reports/data/derivatives_funding_oi_collection_v9_53.json",
    "reports/research_decisions/derivatives_readiness_feature_chain_v9_52_to_v9_55.json",
    "reports/audit_lite/v9_52_to_v9_55_command_results.json",
    "reports/audit_lite/v9_52_to_v9_55_full_local_validation_attestation.json",
    "reports/audit_lite/v9_52_to_v9_55_artifact_inventory.json",
    "reports/audit_lite/zip_size_report_v9_52_to_v9_55.json",
]
FORBIDDEN_PREFIXES = ("data/raw/", "data/silver/", "data/research/", "data/gold/", "reports/backtests/", "reports/strategies/", "orders/", "execution/", "models/", "checkpoints/", ".git/", ".venv/")
FORBIDDEN_PARTS = {"__pycache__", ".pytest_cache", ".ruff_cache", ".mypy_cache"}
FORBIDDEN_NAMES = {".DS_Store", ".env", "Icon", "Icon\r"}
FORBIDDEN_SUFFIXES = {".pyc", ".pkl", ".pickle", ".joblib", ".onnx", ".pt", ".pth", ".ckpt", ".zip", ".pem", ".key", ".sha256.json", ".sha256.txt"}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--zip", required=True, dest="zip_path")
    args = parser.parse_args()
    zip_path = Path(args.zip_path).resolve()
    result = {"version": VERSION, "zip": str(zip_path), "passed": False, "errors": audit_zip(zip_path)}
    result["passed"] = not result["errors"]
    _write_reports(result)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["passed"] else 1


def audit_zip(zip_path: Path) -> list[str]:
    if not zip_path.exists():
        return [f"missing zip: {zip_path}"]
    errors: list[str] = []
    with tempfile.TemporaryDirectory(prefix="galapagos_v9_52_to_v9_55_audit_") as tmp:
        extract_root = Path(tmp)
        with zipfile.ZipFile(zip_path) as archive:
            names = sorted(archive.namelist())
            archive.extractall(extract_root)
        missing = [path for path in REQUIRED_FILES if path not in names]
        if missing:
            errors.append(f"missing required files: {missing}")
        forbidden = [name for name in names if _is_forbidden(name)]
        if forbidden:
            errors.append(f"forbidden files present: {forbidden[:50]}")
        errors.extend(_check_inventory(extract_root, names))
        errors.extend(_check_reports(extract_root))
        errors.extend(_check_command_results(extract_root))
    return errors


def _check_inventory(extract_root: Path, names: list[str]) -> list[str]:
    errors: list[str] = []
    inventory = _read_json(extract_root / "reports/audit_lite/v9_52_to_v9_55_artifact_inventory.json")
    size_report = _read_json(extract_root / "reports/audit_lite/zip_size_report_v9_52_to_v9_55.json")
    if inventory.get("zip_name") != ZIP_NAME:
        errors.append("inventory zip_name mismatch")
    if inventory.get("files_count") != len(names) or sorted(inventory.get("files", [])) != names:
        errors.append("inventory files do not match ZIP content")
    for payload_name, payload in {"inventory": inventory, "size_report": size_report}.items():
        if not isinstance(payload.get("zip_bytes_estimate"), int) or payload.get("zip_bytes_estimate", 0) <= 0:
            errors.append(f"{payload_name} must contain positive zip_bytes_estimate")
        if payload.get("zip_bytes_is_authoritative") is not False:
            errors.append(f"{payload_name} must mark zip_bytes_is_authoritative=false")
        if payload.get("sidecars_created") is not False or payload.get("zip_fingerprints_created") is not False:
            errors.append(f"{payload_name} must confirm no sidecars and no ZIP fingerprints")
        if _contains_forbidden_zip_field(payload):
            errors.append(f"{payload_name} contains forbidden ZIP fingerprint field")
    return errors


def _check_reports(extract_root: Path) -> list[str]:
    errors: list[str] = []
    v52 = _read_json(extract_root / "reports/research_decisions/derivatives_source_readiness_v9_52.json")
    v53 = _read_json(extract_root / "reports/data/derivatives_funding_oi_collection_v9_53.json")
    v54 = _read_json_optional(extract_root / "reports/features/derivatives_funding_oi_feature_store_v9_54.json")
    v55 = _read_json_optional(extract_root / "reports/features/derivatives_funding_oi_feature_store_validation_v9_55.json")
    group = _read_json(extract_root / "reports/research_decisions/derivatives_readiness_feature_chain_v9_52_to_v9_55.json")
    attestation = _read_json(extract_root / "reports/audit_lite/v9_52_to_v9_55_full_local_validation_attestation.json")
    source_stopped = v53.get("decision") == "funding_collection_failed_source_issue"
    if v52.get("decision") not in {"derivatives_source_readiness_funding_ready", "derivatives_source_readiness_funding_ready_oi_limited"}:
        errors.append("V9.52 readiness did not authorize continuation")
    if v53.get("decision") not in {"funding_collection_complete", "funding_collection_complete_oi_not_ready", "funding_collection_failed_source_issue"}:
        errors.append("V9.53 funding collection did not complete")
    if not source_stopped:
        if v54.get("decision") not in {"derivatives_funding_feature_store_created", "derivatives_funding_oi_feature_store_created", "derivatives_feature_store_created_with_warnings"}:
            errors.append("V9.54 feature store was not created")
        if v55.get("decision") not in {"derivatives_feature_store_validated", "derivatives_feature_store_validated_with_warnings"}:
            errors.append("V9.55 feature store was not validated")
    if group.get("decision") not in {"funding_feature_store_validated", "funding_oi_feature_store_validated", "funding_feature_store_validated_oi_not_ready", "derivatives_chain_stopped_source_issue"}:
        errors.append("global decision is not allowed")
    for payload_name, payload in {"v52": v52, "v53": v53, "v54": v54, "v55": v55, "group": group, "attestation": attestation}.items():
        if _contains_forbidden_zip_field(payload):
            errors.append(f"{payload_name} contains forbidden ZIP fingerprint field")
    for key in ["ml_executed", "dataset_created", "labels_created", "walk_forward_executed", "backtest_executed", "signal_created", "strategy_created"]:
        if (v55 and v55.get(key) is not False) or attestation.get(key) is not False:
            errors.append(f"forbidden execution flag must be false: {key}")
    return errors


def _check_command_results(extract_root: Path) -> list[str]:
    payload = _read_json(extract_root / "reports/audit_lite/v9_52_to_v9_55_command_results.json")
    commands = payload.get("commands", [])
    errors: list[str] = []
    if payload.get("version") != VERSION:
        errors.append("command_results version mismatch")
    for needle in [
        "pytest --collect-only -q",
        "run_derivatives_source_readiness_v9_52.py",
        "run_derivatives_funding_oi_collection_v9_53.py",
        "release_audit_lite_zip_v9_52_to_v9_55.py",
    ]:
        if not any(needle in item.get("command", "") and item.get("returncode") == 0 for item in commands):
            errors.append(f"missing successful command result for {needle}")
    return errors


def _is_forbidden(name: str) -> bool:
    path = Path(name)
    if any(part in FORBIDDEN_PARTS for part in path.parts):
        return True
    if path.name in FORBIDDEN_NAMES:
        return True
    if any(name.startswith(prefix) for prefix in FORBIDDEN_PREFIXES):
        return True
    return any(path.name.endswith(suffix) for suffix in FORBIDDEN_SUFFIXES)


def _contains_forbidden_zip_field(payload: Any) -> bool:
    if isinstance(payload, dict):
        for key, value in payload.items():
            lowered = str(key).casefold()
            if "zip_sha256" in lowered or lowered.endswith("_sha256") or lowered == "sha256":
                return True
            if _contains_forbidden_zip_field(value):
                return True
    if isinstance(payload, list):
        return any(_contains_forbidden_zip_field(item) for item in payload)
    return False


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_json_optional(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _write_reports(result: dict[str, Any]) -> None:
    report_dir = Path("reports/audit_lite")
    report_dir.mkdir(parents=True, exist_ok=True)
    (report_dir / "zip_audit_v9_52_to_v9_55.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (report_dir / "zip_audit_v9_52_to_v9_55.md").write_text(
        "# Audit ZIP V9.52 a V9.55\n\n"
        f"- Resultat : `{'PASS' if result['passed'] else 'FAIL'}`.\n"
        f"- Erreurs : `{result['errors']}`.\n"
        "- Aucun sidecar et aucune empreinte ZIP.\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    raise SystemExit(main())
