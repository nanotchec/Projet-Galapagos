from __future__ import annotations

import json
import zipfile
from pathlib import Path
from typing import Any

import _bootstrap

_bootstrap.bootstrap_src_path()

from galapagos.data.public_market.provenance import sha256_file


VERSION = "V5.4.1"
BASE_VERSION = "V5.4"
ZIP_NAME = "projet-galapagos-v5.4.1-audit-lite.zip"
AUDIT_DIR = Path("reports/audit_lite")
ARTIFACT_INVENTORY_JSON = AUDIT_DIR / "v5_4_1_artifact_inventory.json"
ARTIFACT_INVENTORY_MD = AUDIT_DIR / "v5_4_1_artifact_inventory.md"
ZIP_SIZE_JSON = AUDIT_DIR / "zip_size_report_v5_4_1.json"
ZIP_SIZE_MD = AUDIT_DIR / "zip_size_report_v5_4_1.md"

SOURCE_PREFIXES = [
    Path("src/galapagos/data/public_market"),
    Path("src/galapagos/features"),
    Path("src/galapagos/labels"),
    Path("src/galapagos/datasets"),
    Path("src/galapagos/ml"),
    Path("src/galapagos/validation"),
]
SOURCE_EXACT = [
    Path("src/galapagos/__init__.py"),
    Path("src/galapagos/data/__init__.py"),
]
SCRIPT_EXACT = [
    Path("scripts/_bootstrap.py"),
    Path("scripts/run_max_history_offline_ml_research_v5_4.py"),
    Path("scripts/validate_max_history_offline_ml_research_v5_4.py"),
    Path("scripts/release_audit_lite_zip_v5_4.py"),
    Path("scripts/audit_audit_lite_zip_v5_4.py"),
    Path("scripts/smoke_audit_lite_zip_v5_4.py"),
    Path("scripts/release_audit_lite_zip_v5_4_1.py"),
    Path("scripts/audit_audit_lite_zip_v5_4_1.py"),
    Path("scripts/smoke_audit_lite_zip_v5_4_1.py"),
]
TEST_EXACT = [
    Path("tests/ml/test_max_history_offline_ml_research_v5_4.py"),
    Path("tests/validation/test_max_history_offline_ml_research_v5_4_validator.py"),
]
REPORT_EXACT = [
    Path("reports/manifests/max_history_offline_ml_research_v5_4_manifest.json"),
    Path("reports/ml/max_history_offline_ml_research_v5_4.json"),
    Path("reports/ml/max_history_offline_ml_research_v5_4.md"),
    Path("reports/ml/max_history_offline_research_scores_v5_4.json"),
    Path("reports/ml/max_history_offline_research_scores_v5_4.md"),
    Path("docs/max_history_offline_ml_research_v5_4.md"),
    Path("reports/audit_lite/v5_4_artifact_inventory.json"),
    Path("reports/audit_lite/v5_4_artifact_inventory.md"),
    Path("reports/audit_lite/v5_4_parquet_summary.json"),
    Path("reports/audit_lite/v5_4_full_local_validation_attestation.json"),
    Path("reports/audit_lite/v5_4_full_local_validation_attestation.md"),
    Path("reports/audit_lite/zip_size_report_v5_4.json"),
    Path("reports/audit_lite/zip_size_report_v5_4.md"),
    Path("reports/PROJECT_STATE.json"),
    Path("reports/PROJECT_STATE.md"),
    Path("reports/current/latest_metrics.json"),
    Path("reports/current/latest_metrics.md"),
    Path("reports/current/latest_summary.md"),
    Path("README.md"),
    Path("pyproject.toml"),
]
SAMPLE_EXACT = [
    Path("data/audit_lite/v5_4/ml_scores/timeframe=1m/sample.parquet"),
    Path("data/audit_lite/v5_4/ml_scores/timeframe=5m/sample.parquet"),
    Path("data/audit_lite/v5_4/ml_scores/timeframe=15m/sample.parquet"),
    Path("data/audit_lite/v5_4/ml_scores/timeframe=1h/sample.parquet"),
]
FORBIDDEN_PARTS = {".git", ".venv", "__pycache__", ".pytest_cache", ".ruff_cache", ".mypy_cache"}
FORBIDDEN_SUFFIXES = {".pyc", ".pyo", ".pkl", ".pickle", ".joblib", ".ckpt", ".pt", ".pth", ".onnx", ".zip"}
FORBIDDEN_PREFIXES = [
    "data/raw/",
    "data/research/",
    "reports/backtests/",
    "reports/strategies/",
    "reports/signals/",
    "reports/predictions/",
    "orders/",
    "execution/",
    "models/",
    "checkpoints/",
]


def main() -> None:
    root = Path(".").resolve()
    _update_project_state(root)

    zip_path = root / ZIP_NAME
    zip_size_bytes = zip_path.stat().st_size if zip_path.exists() else 0
    included = _collect_files(root)
    included = _collect_files(root)
    for _attempt in range(5):
        inventory = _build_inventory(root, included)
        _write_json(root / ARTIFACT_INVENTORY_JSON, inventory)
        _write_text(root / ARTIFACT_INVENTORY_MD, _render_inventory_markdown(inventory))
        included = _collect_files(root)
        _write_size_report(root, zip_size_bytes=zip_size_bytes, included=included)
        included = _collect_files(root)
        inventory = _build_inventory(root, included)
        _write_json(root / ARTIFACT_INVENTORY_JSON, inventory)
        _write_text(root / ARTIFACT_INVENTORY_MD, _render_inventory_markdown(inventory))
        included = _collect_files(root)
        _write_zip(root, zip_path, included)
        current_size = zip_path.stat().st_size
        if current_size == zip_size_bytes:
            break
        zip_size_bytes = current_size

    payload = {
        "version": VERSION,
        "base_version": BASE_VERSION,
        "status": "PASS",
        "zip_path": str(zip_path),
        "zip_size_bytes": zip_path.stat().st_size,
        "files_included": len(included),
        "pytest_collectible_scripts_excluded": True,
        "test_llm_provider_excluded": True,
        "run_forward_paper_test_excluded": True,
        "audit_lite_does_not_replace_full_validation": True,
    }
    print(json.dumps(payload, indent=2, ensure_ascii=False))


def _collect_files(root: Path) -> list[Path]:
    files: set[Path] = set()
    for exact in [*SOURCE_EXACT, *SCRIPT_EXACT, *TEST_EXACT, *REPORT_EXACT, *SAMPLE_EXACT, ARTIFACT_INVENTORY_JSON, ARTIFACT_INVENTORY_MD, ZIP_SIZE_JSON, ZIP_SIZE_MD]:
        path = root / exact
        if path.exists() and path.is_file() and _allowed_member(exact):
            files.add(exact)
    for prefix in SOURCE_PREFIXES:
        base = root / prefix
        if not base.exists():
            continue
        for child in base.rglob("*"):
            if child.is_file():
                relative = child.relative_to(root)
                if _allowed_member(relative):
                    files.add(relative)
    forbidden_scripts = [relative for relative in files if _is_forbidden_pytest_collectible_script(relative)]
    if forbidden_scripts:
        raise RuntimeError(f"V5.4.1 release would include pytest-collectible scripts: {[p.as_posix() for p in forbidden_scripts]}")
    return sorted(files)


def _allowed_member(relative: Path) -> bool:
    text = relative.as_posix()
    if any(part in FORBIDDEN_PARTS for part in relative.parts):
        return False
    if relative.suffix.casefold() in FORBIDDEN_SUFFIXES:
        return False
    if _is_forbidden_pytest_collectible_script(relative):
        return False
    for prefix in FORBIDDEN_PREFIXES:
        if text.startswith(prefix) and not text.startswith("data/audit_lite/v5_4/"):
            return False
    return True


def _is_forbidden_pytest_collectible_script(relative: Path) -> bool:
    if len(relative.parts) != 2 or relative.parts[0] != "scripts" or relative.suffix != ".py":
        return False
    name = relative.name
    return name in {"run_forward_paper_test.py", "test_llm_provider.py"} or name.startswith("test_") or name.endswith("_test.py")


def _build_inventory(root: Path, included: list[Path]) -> dict[str, Any]:
    self_describing_reports = {
        ARTIFACT_INVENTORY_JSON,
        ARTIFACT_INVENTORY_MD,
        ZIP_SIZE_JSON,
        ZIP_SIZE_MD,
    }
    return {
        "version": VERSION,
        "base_version": BASE_VERSION,
        "status": "PASS",
        "purpose": "Audit-lite packaging correction for pytest collect-only compatibility.",
        "files_included": len(included),
        "included_files_sha256": [
            {"path": relative.as_posix(), "sha256": sha256_file(root / relative)}
            for relative in included
            if (root / relative).is_file() and relative not in self_describing_reports
        ],
        "self_describing_reports_excluded_from_sha256": [
            relative.as_posix() for relative in sorted(self_describing_reports)
        ],
        "pytest_collectible_scripts_excluded": True,
        "forbidden_scripts_absent": [
            "scripts/run_forward_paper_test.py",
            "scripts/test_llm_provider.py",
            "scripts/test_*.py",
            "scripts/*_test.py",
        ],
        "raw_zips_excluded": True,
        "full_research_parquet_excluded": True,
        "no_score_recalculation": True,
        "no_functional_ml_change": True,
    }


def _render_inventory_markdown(inventory: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Inventaire audit-lite V5.4.1",
            "",
            "- Correction packaging uniquement pour rendre le ZIP auto-testable en collect-only.",
            "- Les scripts historiques collectables par pytest sont exclus.",
            "- Les artefacts V5.4 utiles sont conserves.",
            f"- Fichiers inclus : `{inventory['files_included']}`.",
            "- Aucun score V5.4 n'est modifie ou recalcule.",
        ]
    ) + "\n"


def _update_project_state(root: Path) -> None:
    state_path = root / "reports/PROJECT_STATE.json"
    state = json.loads(state_path.read_text(encoding="utf-8")) if state_path.exists() else {}
    state.update(
        {
            "last_validated_version": "V5.3",
            "candidate_version": "V5.4.1",
            "candidate_status": "pending_external_audit",
            "direction": "audit-lite pytest collection packaging fix",
            "correction_version": "V5.4.1",
            "base_candidate_version": "V5.4",
            "v5_4_1_candidate": True,
            "v5_4_1_packaging_only": True,
            "v5_4_1_pytest_collect_only_fix": True,
            "v5_4_scores_modified": False,
            "v5_4_scores_recalculated": False,
            "backtest_v5_4_1_created": False,
            "strategy_v5_4_1_created": False,
            "signal_v5_4_1_created": False,
            "orders_v5_4_1_created": False,
            "paper_live_v5_4_1_created": False,
            "trading_v5_4_1_created": False,
            "persistent_model_v5_4_1_created": False,
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
    _write_json(root / "reports/current/latest_metrics.json", _latest_metrics_payload(state))
    _write_text(root / "reports/PROJECT_STATE.md", _project_state_markdown())
    _write_text(root / "reports/current/latest_metrics.md", _latest_metrics_markdown())
    _write_text(root / "reports/current/latest_summary.md", _latest_summary_markdown())


def _latest_metrics_payload(state: dict[str, Any]) -> dict[str, Any]:
    return {
        "last_validated_version": "V5.3",
        "candidate_version": "V5.4.1",
        "candidate_status": "pending_external_audit",
        "direction": state["direction"],
        "correction_scope": "audit_lite_packaging_only",
        "base_candidate_version": "V5.4",
        "pytest_collect_only_zip_fix": True,
        "v5_4_scores_modified": False,
        "v5_4_scores_recalculated": False,
        "backtest_enabled": False,
        "strategy_enabled": False,
        "paper_live_enabled": False,
        "orders_enabled": False,
        "trading_enabled": False,
        "execution_enabled": False,
        "api_key_used": False,
        "private_endpoint_used": False,
        "authentication_used": False,
        "external_validation_required": True,
    }


def _project_state_markdown() -> str:
    return """# Etat du Projet : V5.3 validee + correctif candidat V5.4.1

- **Derniere version validee** : V5.3.
- **Version candidate** : V5.4.1.
- **Statut candidate** : `pending_external_audit`.
- **Direction** : audit-lite pytest collection packaging fix.

## Correctif V5.4.1

- V5.4.1 corrige uniquement le packaging audit-lite V5.4.
- Objectif : produire un ZIP auto-testable avec `PYTHONPATH=src python -m pytest --collect-only -q`.
- Les scores, datasets, features, labels et resultats ML V5.4 ne sont pas modifies.
- Les scripts historiques collectables par pytest et inutiles au ZIP V5.4 sont exclus.

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
- V5.4.1 reste non validee avant audit externe.
"""


def _latest_metrics_markdown() -> str:
    return """# Latest Metrics V5.4.1

- Derniere version validee : V5.3.
- Candidate : V5.4.1.
- Statut : `pending_external_audit`.
- Correction : packaging audit-lite uniquement.
- Base concernee : V5.4.
- Objectif : collect-only pytest dans le ZIP audit-lite.
- Scores V5.4 modifies : `false`.
- Scores V5.4 recalcules : `false`.

Aucun backtest, aucune strategie, aucun signal de trading, aucun ordre, aucun modele persistant et aucun trading reel.
"""


def _latest_summary_markdown() -> str:
    return """# Latest Summary V5.4.1

V5.3 est la derniere version validee par audit externe.

V5.4.1 est la candidate courante. Elle corrige uniquement le packaging audit-lite V5.4 afin que le ZIP extrait passe `PYTHONPATH=src python -m pytest --collect-only -q`.

Le correctif exclut les scripts historiques collectables par pytest et inutiles au ZIP V5.4, notamment `scripts/test_llm_provider.py` et `scripts/run_forward_paper_test.py`.

Les scores V5.4, datasets, features, labels, rapports ML et validateurs de production ne sont pas modifies.

Aucun trading, aucun paper live, aucun ordre, aucun backtest, aucune strategie, aucun signal de trading et aucun claim de rentabilite.

V5.4.1 reste `pending_external_audit`.
"""


def _write_zip(root: Path, zip_path: Path, included: list[Path]) -> None:
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for relative in included:
            archive.write(root / relative, relative.as_posix())


def _write_size_report(root: Path, *, zip_size_bytes: int, included: list[Path]) -> None:
    payload = {
        "version": VERSION,
        "base_version": BASE_VERSION,
        "zip_name": ZIP_NAME,
        "zip_size_bytes": int(zip_size_bytes),
        "files_included": len(included),
        "pytest_collectible_scripts_excluded": True,
        "raw_zips_excluded": True,
    }
    _write_json(root / ZIP_SIZE_JSON, payload)
    _write_text(
        root / ZIP_SIZE_MD,
        "\n".join(
            [
                "# Rapport taille ZIP V5.4.1",
                "",
                f"- ZIP : `{ZIP_NAME}`.",
                f"- Taille octets : `{zip_size_bytes}`.",
                f"- Fichiers inclus : `{len(included)}`.",
                "- Les scripts historiques collectables par pytest sont exclus.",
            ]
        )
        + "\n",
    )


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
