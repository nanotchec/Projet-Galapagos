# Resultats des commandes V9.39

- `git branch --show-current` : PASS, `main`.
- `git status --short --branch` : PASS, `## main...origin/main [ahead 8]`.
- `PYTHONPATH=src python -m pytest --collect-only -q` : PASS, `5714 tests collected in 1.75s`.
- `PYTHONPATH=src python -m pytest -q tests/datasets/test_ohlcv_aggtrades_5y_dataset_v9_39.py` : PASS, `5 passed in 0.27s`.
- `PYTHONPATH=src python -m pytest -q tests/validation/test_ohlcv_aggtrades_5y_dataset_v9_39_validator.py` : PASS, `6 passed in 0.27s`.
- `python scripts/run_ohlcv_aggtrades_5y_dataset_v9_39.py` : PASS, decision `ohlcv_aggtrades_5y_dataset_blocked_by_missing_labels`, dataset cree `false`.
- `python scripts/validate_ohlcv_aggtrades_5y_dataset_v9_39.py` : PASS, erreurs `[]`.
- `python scripts/release_audit_lite_zip_v9_39.py` : PASS, ZIP `projet-galapagos-v9.39-audit-lite.zip`, `44` fichiers inclus.
- `python scripts/audit_audit_lite_zip_v9_39.py --zip projet-galapagos-v9.39-audit-lite.zip` : premier passage FAIL attendu, le `command_results` ne contenait pas encore le resultat de release ; corrige avant l'audit final.
- `python scripts/audit_audit_lite_zip_v9_39.py --zip projet-galapagos-v9.39-audit-lite.zip` : PASS final, erreurs `[]`.
- `python scripts/smoke_audit_lite_zip_v9_39.py --zip projet-galapagos-v9.39-audit-lite.zip` : PASS final, erreurs `[]`, parquet checks requis `false`.

Aucun sidecar et aucune empreinte ZIP.
