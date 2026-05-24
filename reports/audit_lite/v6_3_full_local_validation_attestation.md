# Attestation full locale V6.3

- Scope : `full_local`
- Validation full locale remplacee par audit-lite : `false`
- Fenetre : `2023-03-25` -> `2026-05-23`
- Total jours : `1156`
- Advanced feature columns count : `158`
- Aucun trading, aucun backtest, aucun ordre, aucune strategie.

## Commandes executees

- `python scripts/run_advanced_ohlcv_ml_robustness_v6_3.py` : PASS, `273.12`s
- `python scripts/validate_advanced_ohlcv_ml_robustness_v6_3.py` : PASS, `3.11`s
- `python -m pytest -q tests/ml/test_advanced_ohlcv_ml_robustness_v6_3.py` : PASS, `1.18`s
- `python -m pytest -q tests/validation/test_advanced_ohlcv_ml_robustness_v6_3_validator.py` : PASS, `3.14`s
- `python scripts/release_audit_lite_zip_v6_3.py` : PASS, `1.17`s
- `python scripts/audit_audit_lite_zip_v6_3.py --zip projet-galapagos-v6.3-audit-lite.zip` : PASS, `0.07`s
- `python scripts/smoke_audit_lite_zip_v6_3.py --zip projet-galapagos-v6.3-audit-lite.zip` : PASS, `2.19`s
- `python -m pytest --collect-only -q` : PASS, `1.84`s
