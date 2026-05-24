# Attestation full locale V4.7

- Scope : `full_local`
- Validation full locale remplacee par audit-lite : `false`
- Aucun trading, aucun backtest, aucun ordre, aucune strategie.

## Commandes executees

- `python scripts/run_one_year_ml_robustness_v4_7.py` : PASS, `50.55`s
- `python scripts/validate_one_year_ml_robustness_v4_7.py` : PASS, `2.02`s
- `python -m pytest -q tests/ml/test_one_year_ml_robustness_v4_7.py` : PASS, `1.26`s
- `python -m pytest -q tests/validation/test_one_year_ml_robustness_v4_7_validator.py` : PASS, `2.13`s
- `python scripts/release_audit_lite_zip_v4_7.py` : PASS, `0.49`s
- `python scripts/audit_audit_lite_zip_v4_7.py --zip projet-galapagos-v4.7-audit-lite.zip` : PASS, `0.05`s
- `python scripts/smoke_audit_lite_zip_v4_7.py --zip projet-galapagos-v4.7-audit-lite.zip` : PASS, `0.98`s
- `python -m pytest --collect-only -q` : PASS, `3.1`s
