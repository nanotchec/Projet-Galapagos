# Attestation full locale V7.5

- Scope : `full_local`
- Validation full locale remplacee par audit-lite : `false`
- Fenetre : `2023-03-25` -> `2023-04-23`
- Total jours : `30`
- Feature columns count : `71`
- Aucun trading, aucun backtest, aucun ordre, aucune strategie.

## Commandes executees

- `python scripts/run_ohlcv_trades_ml_robustness_v7_5.py` : PASS, `9.84`s
- `python scripts/validate_ohlcv_trades_ml_robustness_v7_5.py` : PASS, `1.55`s
- `python -m pytest -q tests/ml/test_ohlcv_trades_ml_robustness_v7_5.py` : PASS, `1.36`s
- `python -m pytest -q tests/validation/test_ohlcv_trades_ml_robustness_v7_5_validator.py` : PASS, `1.88`s
- `python scripts/release_audit_lite_zip_v7_5.py` : PASS, `1.5`s
- `python scripts/audit_audit_lite_zip_v7_5.py --zip projet-galapagos-v7.5-audit-lite.zip` : PASS, `0.08`s
- `python scripts/smoke_audit_lite_zip_v7_5.py --zip projet-galapagos-v7.5-audit-lite.zip` : PASS, `2.46`s
- `python -m pytest --collect-only -q` : PASS, `2.14`s
