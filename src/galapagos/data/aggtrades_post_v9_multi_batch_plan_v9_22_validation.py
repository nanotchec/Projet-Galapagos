from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from galapagos.data.aggtrades_post_v9_multi_batch_plan_v9_22 import (
    ALLOWED_DECISIONS,
    BASE_SAFETY_FLAGS,
    FINDINGS,
    MANIFEST_PATH,
    REPORT_JSON_PATH,
    REPORT_MD_PATH,
    SOURCE_VERSION,
    TARGET_WINDOW_END,
    TARGET_WINDOW_START,
    VERSION,
)


FORBIDDEN_CLAIMS = [
    "strategy validated",
    "tradable edge confirmed",
    "live trading ready",
    "profitability confirmed",
]
FORBIDDEN_TERMS = ["sharpe", "drawdown", "equity curve", "profit factor", "pnl"]
FORBIDDEN_FILENAMES = {"Icon", "Icon\r", ".DS_Store", ".env"}
FORBIDDEN_SUFFIXES = {".pyc", ".pkl", ".pickle", ".joblib", ".onnx", ".pt", ".pth", ".ckpt", ".pem", ".key", ".sha256.json", ".sha256.txt"}


def validate_aggtrades_post_v9_multi_batch_plan_v9_22(root: Path = Path(".")) -> list[str]:
    root = root.resolve()
    errors: list[str] = []
    report_path = root / REPORT_JSON_PATH
    manifest_path = root / MANIFEST_PATH
    markdown_path = root / REPORT_MD_PATH
    if not report_path.exists():
        errors.append(f"missing V9.22 report: {REPORT_JSON_PATH}")
        return errors
    if not manifest_path.exists():
        errors.append(f"missing V9.22 manifest: {MANIFEST_PATH}")
        return errors
    if not markdown_path.exists():
        errors.append(f"missing V9.22 markdown: {REPORT_MD_PATH}")
        return errors
    report = _read_json(report_path)
    manifest = _read_json(manifest_path)
    errors.extend(validate_report_payload_v9_22(report))
    errors.extend(validate_manifest_payload_v9_22(manifest, report))
    errors.extend(validate_markdown_v9_22(markdown_path.read_text(encoding="utf-8")))
    errors.extend(validate_no_forbidden_artifacts_v9_22(root))
    return errors


def validate_report_payload_v9_22(report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if report.get("version") != VERSION:
        errors.append("V9.22 report version mismatch")
    if report.get("source_version") != SOURCE_VERSION:
        errors.append("V9.22 source_version mismatch")
    if report.get("status") != "PASS":
        errors.append("V9.22 status must be PASS")
    if report.get("mode") != "plan-only":
        errors.append("V9.22 must stay plan-only")
    decision = report.get("v9_22_decision", {})
    if decision.get("decision") not in ALLOWED_DECISIONS:
        errors.append("V9.22 decision is not allowed")
    if "backtest" in str(decision.get("next_recommendation", "")).casefold():
        errors.append("V9.22 next recommendation must not be a backtest")
    errors.extend(validate_current_coverage_v9_22(report.get("current_coverage", {})))
    errors.extend(validate_remaining_and_batches_v9_22(report))
    errors.extend(validate_outputs_absent_v9_22(report))
    errors.extend(validate_safety_flags_v9_22(report))
    if report.get("findings") != FINDINGS:
        errors.append("V9.22 findings mismatch")
    if _contains_forbidden_zip_field(report):
        errors.append("V9.22 report must not contain sidecar or ZIP hash fields")
    return errors


def validate_current_coverage_v9_22(coverage: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if coverage.get("target_window_start") != TARGET_WINDOW_START or coverage.get("target_window_end") != TARGET_WINDOW_END:
        errors.append("V9.22 target window mismatch")
    if coverage.get("days_covered", 0) < 0 or coverage.get("days_remaining", 0) < 0:
        errors.append("V9.22 coverage counts must be non-negative")
    if coverage.get("days_covered") + coverage.get("days_remaining") != coverage.get("target_days_total"):
        errors.append("V9.22 coverage counts must sum to target days")
    if coverage.get("current_coverage_start") != "2024-05-05":
        errors.append("V9.22 current coverage must start at 2024-05-05 when local batches are present")
    if coverage.get("current_coverage_end") != "2024-08-09":
        errors.append("V9.22 current coverage must end at 2024-08-09 when V9.19/V9.20/V9.21 are present")
    if coverage.get("gaps_detected"):
        errors.append("V9.22 expected no gaps after validated V9.19/V9.20/V9.21 batches")
    if coverage.get("v9_19_days") != 7 or coverage.get("v9_20_days") != 30 or coverage.get("v9_21_days") != 60:
        errors.append("V9.22 previous batch day counts mismatch")
    return errors


def validate_remaining_and_batches_v9_22(report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    remaining = report.get("remaining_window", {})
    batches = report.get("proposed_batches", [])
    estimates = report.get("estimated_remaining_volume", {})
    if remaining.get("remaining_start") != "2024-08-10" or remaining.get("remaining_end") != "2026-05-05":
        errors.append("V9.22 remaining window mismatch")
    if remaining.get("remaining_days") != 634:
        errors.append("V9.22 remaining days must be 634")
    if len(batches) != 11:
        errors.append("V9.22 must propose 11 controlled batches for 634 remaining days at 60-day max")
    if batches:
        if batches[0].get("start_date") != "2024-08-10" or batches[0].get("end_date") != "2024-10-08":
            errors.append("V9.22 first proposed batch mismatch")
        if batches[-1].get("end_date") != "2026-05-05":
            errors.append("V9.22 final proposed batch must end at target end")
    previous_end = None
    for batch in batches:
        if batch.get("max_downloads", 0) > 60 or batch.get("expected_days", 0) > 60:
            errors.append("V9.22 proposed batches must not exceed 60 days")
        if batch.get("checkpoint_required") is not True or batch.get("audit_required_after_batch") is not True:
            errors.append("V9.22 each proposed batch must require checkpoint and audit")
        if previous_end:
            expected_start = _next_day(previous_end)
            if batch.get("start_date") != expected_start:
                errors.append("V9.22 proposed batches must be contiguous")
        previous_end = batch.get("end_date")
    if estimates.get("estimated_remaining_rows", 0) <= 0:
        errors.append("V9.22 remaining row estimate must be positive")
    if estimates.get("estimated_remaining_raw_bytes", 0) <= 0 or estimates.get("estimated_remaining_silver_bytes", 0) <= 0:
        errors.append("V9.22 remaining byte estimates must be positive")
    return errors


def validate_outputs_absent_v9_22(report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for key in ["collection_executed", "network_used", "new_data_downloaded", "ingestion_executed", "features_created", "labels_created", "dataset_created", "ml_executed", "walk_forward_executed", "backtest_executed", "complete_collection_reached"]:
        if report.get(key) is not False:
            errors.append(f"V9.22 must keep {key}=false")
    return errors


def validate_safety_flags_v9_22(report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    flags = report.get("safety_flags", {})
    for key, expected in BASE_SAFETY_FLAGS.items():
        if flags.get(key) is not expected:
            errors.append(f"V9.22 safety flag mismatch: {key}")
    return errors


def validate_manifest_payload_v9_22(manifest: dict[str, Any], report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if manifest.get("version") != VERSION:
        errors.append("V9.22 manifest version mismatch")
    if manifest.get("status") != report.get("status"):
        errors.append("V9.22 manifest status mismatch")
    if manifest.get("mode") != report.get("mode"):
        errors.append("V9.22 manifest mode mismatch")
    for key in ["current_coverage_start", "current_coverage_end", "days_covered", "days_remaining", "gaps_detected"]:
        if manifest.get(key) != report.get("current_coverage", {}).get(key):
            errors.append(f"V9.22 manifest {key} mismatch")
    if manifest.get("proposed_batches_count") != len(report.get("proposed_batches", [])):
        errors.append("V9.22 manifest proposed batch count mismatch")
    if manifest.get("collection_executed") is not False or manifest.get("network_used") is not False:
        errors.append("V9.22 manifest must confirm no collection and no network")
    if manifest.get("v9_22_decision", {}).get("decision") != report.get("v9_22_decision", {}).get("decision"):
        errors.append("V9.22 manifest decision mismatch")
    if manifest.get("findings") != report.get("findings"):
        errors.append("V9.22 manifest findings mismatch")
    if manifest.get("safety_flags") != report.get("safety_flags"):
        errors.append("V9.22 manifest safety flags mismatch")
    if _contains_forbidden_zip_field(manifest):
        errors.append("V9.22 manifest must not contain sidecar or ZIP hash fields")
    return errors


def validate_markdown_v9_22(text: str) -> list[str]:
    lowered = text.casefold()
    errors: list[str] = []
    for claim in FORBIDDEN_CLAIMS:
        if claim in lowered:
            errors.append(f"V9.22 markdown contains forbidden claim: {claim}")
    for forbidden in FORBIDDEN_TERMS:
        if forbidden in lowered:
            errors.append(f"V9.22 markdown contains forbidden metric term: {forbidden}")
    for phrase in [
        "aucun trading",
        "aucun paper live",
        "aucun ordre",
        "aucun backtest",
        "aucun walk-forward",
        "aucune strategie",
        "aucun signal actionnable",
        "aucun modele persistant",
        "aucune api privee",
        "aucune cle api",
        "aucun client exchange authentifie",
        "aucun websocket live",
        "aucun reseau",
        "aucun telechargement",
        "aucune ingestion",
        "aucun sidecar",
        "aucune empreinte zip",
    ]:
        if phrase not in lowered:
            errors.append(f"V9.22 markdown missing safety phrase: {phrase}")
    for phrase in ["plan multi-batch", "jours restants", "gaps detectes", "stockage"]:
        if phrase not in lowered:
            errors.append(f"V9.22 markdown missing planning phrase: {phrase}")
    return errors


def validate_no_forbidden_artifacts_v9_22(root: Path) -> list[str]:
    errors: list[str] = []
    forbidden_paths = [
        root / "data/research/v9_22",
        root / "reports/backtests",
        root / "reports/strategies",
        root / "orders",
        root / "execution",
        root / "models",
        root / "checkpoints",
    ]
    for path in forbidden_paths:
        if path.exists():
            errors.append(f"forbidden V9.22 artifact exists: {path}")
    for path in root.glob("projet-galapagos-v9.22-audit-lite.zip.sha256.*"):
        errors.append(f"forbidden V9.22 sidecar present: {path}")
    for path in root.rglob("*v9_22*"):
        if "__pycache__" in path.parts or ".pytest_cache" in path.parts:
            continue
        if path.name in FORBIDDEN_FILENAMES:
            errors.append(f"forbidden V9.22 file present: {path}")
        if path.suffix.casefold() in FORBIDDEN_SUFFIXES:
            errors.append(f"forbidden V9.22 file suffix present: {path}")
    return errors


def _contains_forbidden_zip_field(payload: Any) -> bool:
    if isinstance(payload, dict):
        for key, value in payload.items():
            text = str(key).casefold()
            if text == "zip_sha256" or text.startswith("sidecar_"):
                return True
            if _contains_forbidden_zip_field(value):
                return True
    if isinstance(payload, list):
        return any(_contains_forbidden_zip_field(item) for item in payload)
    return False


def _next_day(value: str) -> str:
    from datetime import date, timedelta

    return (date.fromisoformat(value) + timedelta(days=1)).isoformat()


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))
