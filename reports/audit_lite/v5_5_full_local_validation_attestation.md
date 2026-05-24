# Attestation full locale V5.5

- Scope : `full_local`
- Validation full locale remplacee par audit-lite : `false`
- Fenetre : `2023-03-25` -> `2026-05-23`
- Total jours : `1156`
- Aucun trading, aucun backtest, aucun ordre, aucune strategie.

## Commandes executees

- `python scripts/run_max_history_ml_robustness_v5_5.py` : PASS, `202.0`s
- `python scripts/validate_max_history_ml_robustness_v5_5.py` : PASS, `3.0`s
- `python -m pytest -q tests/ml/test_max_history_ml_robustness_v5_5.py` : PASS, `0.94`s
- `python -m pytest -q tests/validation/test_max_history_ml_robustness_v5_5_validator.py` : PASS, `2.98`s
- `python scripts/release_audit_lite_zip_v5_5.py` : PASS, `1.0`s
- `python scripts/audit_audit_lite_zip_v5_5.py --zip projet-galapagos-v5.5-audit-lite.zip` : PASS, `0.0`s
- `python scripts/smoke_audit_lite_zip_v5_5.py --zip projet-galapagos-v5.5-audit-lite.zip` : PASS, `2.244`s
- `python -m pytest --collect-only -q` : PASS, `1.71`s
