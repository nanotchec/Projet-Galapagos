from __future__ import annotations

import importlib.util
import sys
import zipfile
from pathlib import Path


def _load_smoke_test():
    script_path = Path(__file__).resolve().parents[1] / "scripts" / "smoke_test_clean_zip.py"
    sys.path.insert(0, str(script_path.parent))
    spec = importlib.util.spec_from_file_location("smoke_test_clean_zip_script", script_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.smoke_test_zip


def test_smoke_test_clean_zip_passes_on_minimal_mock(tmp_path: Path) -> None:
    smoke_test_zip = _load_smoke_test()
    zip_path = tmp_path / "mock.zip"
    with zipfile.ZipFile(zip_path, "w") as archive:
        archive.writestr("src/galapagos/__init__.py", "")
        archive.writestr("src/galapagos/data/__init__.py", "")
        archive.writestr("src/galapagos/data/macro/__init__.py", "")
        archive.writestr("src/galapagos/data/macro/fred_client.py", "")
        archive.writestr("src/galapagos/data/derivatives/__init__.py", "")
        archive.writestr("src/galapagos/data/derivatives/schema.py", "")
        archive.writestr("src/galapagos/research/__init__.py", "")
        archive.writestr("src/galapagos/research/ev_net_research/__init__.py", "")
        archive.writestr(
            "src/galapagos/research/ev_net_research/canonical_input_guard.py",
            "",
        )
        archive.writestr(
            "src/galapagos/research/ev_net_research/canonical_ev_feature_rebuilder.py",
            "",
        )
        archive.writestr(
            "src/galapagos/research/ev_net_research/recommendation_engine.py",
            "",
        )
        archive.writestr("src/galapagos/research/derivatives_signal_quality.py", "")
        archive.writestr("src/galapagos/research/alpha_scoring.py", "")
        archive.writestr("src/galapagos/research/signal_selection/__init__.py", "")
        archive.writestr("src/galapagos/research/signal_selection/selection_rules.py", "")
        archive.writestr("src/galapagos/research/signal_selection/leakage_audit.py", "")
        archive.writestr(
            "src/galapagos/research/signal_selection/walk_forward_validation.py",
            "",
        )
        archive.writestr("src/galapagos/research/intrabar/__init__.py", "")
        archive.writestr("src/galapagos/research/trade_ledger/__init__.py", "")
        archive.writestr("src/galapagos/research/trade_ledger/schema.py", "")
        archive.writestr("src/galapagos/research/trade_ledger/ledger_builder.py", "")
        archive.writestr("src/galapagos/research/trade_ledger/intrabar_evaluator.py", "")
        archive.writestr("src/galapagos/research/ml/__init__.py", "")
        archive.writestr("src/galapagos/research/ml/walk_forward.py", "")
        archive.writestr("src/galapagos/research/ml/metrics.py", "")
        archive.writestr("src/galapagos/research/ml/leakage_audit.py", "")
        archive.writestr("src/galapagos/research/ml/random_trading_baselines.py", "")
        archive.writestr(
            "scripts/run_ml_baseline_lab.py",
            "import argparse\nparser = argparse.ArgumentParser()\nparser.add_argument('--dataset')\nparser.add_argument('--config')\nparser.add_argument('--dry-run', action='store_true')\nargs = parser.parse_args()\nprint('{\"status\":\"dry_run_completed\"}')\n",
        )
        archive.writestr(
            "scripts/run_ml_permutation_tests.py",
            "import argparse\nparser = argparse.ArgumentParser()\nparser.add_argument('--dataset')\nparser.add_argument('--config')\nparser.add_argument('--dry-run', action='store_true')\nargs = parser.parse_args()\nprint('{\"status\":\"dry_run_completed\"}')\n",
        )
        archive.writestr(
            "scripts/run_ml_random_baseline_analysis.py",
            "import argparse\nparser = argparse.ArgumentParser()\nparser.add_argument('--dataset')\nparser.add_argument('--config')\nparser.add_argument('--dry-run', action='store_true')\nargs = parser.parse_args()\nprint('{\"status\":\"dry_run_completed\"}')\n",
        )
        archive.writestr(
            "scripts/compare_ml_vs_alpha_score.py",
            "import argparse\nparser = argparse.ArgumentParser()\nparser.add_argument('--dataset')\nparser.add_argument('--config')\nparser.add_argument('--dry-run', action='store_true')\nargs = parser.parse_args()\nprint('{\"status\":\"dry_run_completed\"}')\n",
        )
        archive.writestr(
            "scripts/run_trade_ledger_intrabar_eval.py",
            "import argparse\nparser = argparse.ArgumentParser()\nparser.add_argument('--dry-run', action='store_true')\nparser.add_argument('--version')\nargs = parser.parse_args()\nprint('{\"status\":\"dry_run_completed\"}')\n",
        )
        archive.writestr(
            "scripts/audit_derivatives_coverage.py",
            "print('{\"status\":\"planned\"}')\n",
        )
        archive.writestr(
            "scripts/check_fred_readiness.py",
            "print('{\"status\":\"requires_api_key\"}')\n",
        )
        archive.writestr(
            "scripts/check_derivatives_readiness.py",
            "print('{\"status\":\"planned\"}')\n",
        )
        archive.writestr(
            "scripts/check_historical_data_availability.py",
            "print('{\"available\":false}')\n",
        )
    payload = smoke_test_zip(zip_path, write_report=False)
    # The pytest stability command will fail on a minimal mock zip because
    # the full test/project files are not present. That is expected: the mock
    # test validates import-based commands; the real smoke test validates pytest
    # on a full extracted zip.
    import_commands = [
        r for r in payload["commands"] if "pytest" not in " ".join(str(c) for c in r["command"])
    ]
    pytest_commands = [
        r for r in payload["commands"] if "pytest" in " ".join(str(c) for c in r["command"])
    ]
    assert all(r["passed"] for r in import_commands), "Import-based commands should all pass"
    assert len(import_commands) >= 12
    assert len(pytest_commands) >= 1
