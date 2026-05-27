from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from galapagos.research.label_failure_analysis_v9_11 import (
    ALLOWED_DECISIONS,
    DECISION_TYPE,
    FINDINGS,
    MANIFEST_PATH,
    REPORT_JSON_PATH,
    REPORT_MD_PATH,
    SAFETY,
    SAFETY_FLAGS,
    VERSION,
)


FORBIDDEN_CLAIMS = [
    "strategy validated",
    "tradable edge confirmed",
    "live trading ready",
    "profitability confirmed",
]
FORBIDDEN_FILENAMES = {"Icon", "Icon\r", ".DS_Store", ".env"}
FORBIDDEN_SUFFIXES = {".pyc", ".pkl", ".pickle", ".joblib", ".onnx", ".pt", ".pth", ".ckpt", ".pem", ".key", ".sha256.json", ".sha256.txt"}


def validate_label_failure_analysis_v9_11(root: Path = Path(".")) -> list[str]:
    root = root.resolve()
    errors: list[str] = []
    report_path = root / REPORT_JSON_PATH
    manifest_path = root / MANIFEST_PATH
    markdown_path = root / REPORT_MD_PATH
    if not report_path.exists():
        errors.append(f"missing V9.11 report: {REPORT_JSON_PATH}")
        return errors
    if not manifest_path.exists():
        errors.append(f"missing V9.11 manifest: {MANIFEST_PATH}")
        return errors
    if not markdown_path.exists():
        errors.append(f"missing V9.11 markdown: {REPORT_MD_PATH}")
        return errors
    report = _read_json(report_path)
    manifest = _read_json(manifest_path)
    errors.extend(validate_report_payload_v9_11(report))
    errors.extend(validate_manifest_payload_v9_11(manifest, report))
    errors.extend(validate_markdown_v9_11(markdown_path.read_text(encoding="utf-8")))
    errors.extend(validate_no_forbidden_artifacts_v9_11(root))
    return errors


def validate_report_payload_v9_11(report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if report.get("version") != VERSION:
        errors.append("V9.11 report version mismatch")
    if report.get("status") != "PASS":
        errors.append("V9.11 status must be PASS")
    if report.get("decision_type") != DECISION_TYPE:
        errors.append("V9.11 decision_type mismatch")
    recap = report.get("decision_recap", {})
    if recap.get("v9_4", {}).get("decision") != "backtest_not_justified_refine_labels":
        errors.append("V9.11 must preserve V9.4 label-refinement decision")
    if recap.get("v9_5", {}).get("decision") != "label_redesign_candidate_volatility_normalized":
        errors.append("V9.11 must preserve V9.5 volatility-normalized decision")
    if recap.get("v9_10", {}).get("decision") != "backtest_not_justified_refine_labels_again":
        errors.append("V9.11 must preserve V9.10 conservative decision")
    label_analysis = report.get("label_analysis_v9_6", {})
    if label_analysis.get("target_name") != "up_down_flat_volnorm_h1":
        errors.append("V9.11 label target mismatch")
    if label_analysis.get("selected_k") != 0.5:
        errors.append("V9.11 must preserve selected k=0.5")
    if not label_analysis.get("timeframes"):
        errors.append("V9.11 label analysis must contain timeframes")
    ml = report.get("ml_analysis_v9_8", {})
    if ml.get("decision") != "offline_ml_completed_but_close_to_shuffled_labels":
        errors.append("V9.11 must preserve V9.8 weak ML decision")
    wf = report.get("walk_forward_analysis_v9_9", {})
    if wf.get("decision") != "strict_walk_forward_completed_but_close_to_shuffled_labels":
        errors.append("V9.11 must preserve V9.9 weak walk-forward decision")
    if wf.get("no_clear_edge_vs_shuffled_labels_count") != 76:
        errors.append("V9.11 must preserve the 76 no-clear walk-forward cases")
    hypotheses = report.get("failure_hypotheses", [])
    if {item.get("id") for item in hypotheses} != {"H1", "H2", "H3", "H4", "H5", "H6", "H7", "H8"}:
        errors.append("V9.11 hypotheses H1-H8 must be complete")
    future_designs = report.get("future_designs_compared", [])
    if len(future_designs) < 6:
        errors.append("V9.11 must compare multiple future label designs")
    decision = report.get("v9_11_decision", {})
    if decision.get("decision") not in ALLOWED_DECISIONS:
        errors.append("V9.11 decision is not allowed")
    if "backtest" in decision.get("decision", ""):
        errors.append("V9.11 decision must not be a backtest")
    if report.get("findings") != FINDINGS:
        errors.append("V9.11 findings mismatch")
    for key, expected in SAFETY.items():
        if report.get("safety", {}).get(key) is not expected:
            errors.append(f"V9.11 safety mismatch: {key}")
    for key, expected in SAFETY_FLAGS.items():
        if report.get("safety_flags", {}).get(key) is not expected:
            errors.append(f"V9.11 safety flag mismatch: {key}")
    packaging = report.get("packaging_observations", {})
    for key in ["exclude_icon_files_from_future_zips", "add_internal_timeouts_to_smoke_import_subprocesses", "do_not_reintroduce_sha256_sidecars"]:
        if packaging.get(key) is not True:
            errors.append(f"V9.11 packaging observation missing: {key}")
    if report.get("forbidden_terms_scan", {}).get("passed") is not True:
        errors.append("V9.11 forbidden term scan must pass")
    return errors


def validate_manifest_payload_v9_11(manifest: dict[str, Any], report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if manifest.get("version") != VERSION:
        errors.append("V9.11 manifest version mismatch")
    if manifest.get("status") != report.get("status"):
        errors.append("V9.11 manifest status mismatch")
    if manifest.get("decision_type") != DECISION_TYPE:
        errors.append("V9.11 manifest decision_type mismatch")
    if manifest.get("v9_11_decision", {}).get("decision") != report.get("v9_11_decision", {}).get("decision"):
        errors.append("V9.11 manifest decision mismatch")
    if manifest.get("findings") != report.get("findings"):
        errors.append("V9.11 manifest findings mismatch")
    if manifest.get("safety") != report.get("safety"):
        errors.append("V9.11 manifest safety mismatch")
    if "zip_sha256" in manifest or any(str(key).startswith("sidecar_") for key in manifest):
        errors.append("V9.11 manifest must not contain sidecar or ZIP hash fields")
    return errors


def validate_markdown_v9_11(text: str) -> list[str]:
    lowered = text.casefold()
    errors: list[str] = []
    for claim in FORBIDDEN_CLAIMS:
        if claim in lowered:
            errors.append(f"V9.11 markdown contains forbidden claim: {claim}")
    for phrase in ["aucun backtest", "aucun trading", "aucun ordre", "aucune strategie", "aucun signal actionnable"]:
        if phrase not in lowered:
            errors.append(f"V9.11 markdown missing safety phrase: {phrase}")
    return errors


def validate_no_forbidden_artifacts_v9_11(root: Path) -> list[str]:
    errors: list[str] = []
    forbidden_roots = [
        root / "data/research/v9_11",
        root / "reports/backtests",
        root / "reports/strategies",
        root / "orders",
        root / "execution",
        root / "models",
        root / "checkpoints",
    ]
    for path in forbidden_roots:
        if path.exists():
            errors.append(f"forbidden V9.11 artifact exists: {path}")
    for path in root.glob("projet-galapagos-v9.11-audit-lite.zip.sha256.*"):
        errors.append(f"forbidden V9.11 sidecar present: {path}")
    for path in [root / "Icon", root / "Icon\r"]:
        if path.exists():
            errors.append(f"forbidden parasite file present: {path}")
    return errors


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))
