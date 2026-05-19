from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType


def _load_root_validator() -> ModuleType:
    root = Path(__file__).resolve().parents[2]
    path = root / "scripts/validate_regime_feature_diagnostic_reports.py"
    spec = importlib.util.spec_from_file_location("_galapagos_root_regime_feature_validator", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load root validator from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def validate_reports(version: str = "v1.43") -> bool:
    return bool(_load_root_validator().validate_reports(version))
