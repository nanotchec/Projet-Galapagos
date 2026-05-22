# Attestation full locale V4.0

- Version : `V4.0`
- Scope : `full_local`
- Validation full locale : `true`
- Audit-lite ne remplace pas la validation full locale : `true`
- Aucun trading, aucun backtest, aucune strategie, aucun ordre.

## Commandes executees

- `python scripts/run_expanded_ml_robustness_v4_0.py` : code `0`, `16.37` s
- `python scripts/validate_expanded_ml_robustness_v4_0.py` : code `0`, `1.83` s
- `python -m pytest -q tests/ml/test_expanded_ml_robustness_v4_0.py` : code `0`, `1.29` s
- `python -m pytest -q tests/validation/test_expanded_ml_robustness_v4_0_validator.py` : code `0`, `1.85` s
- `python scripts/release_audit_lite_zip_v4_0.py` : code `0`, `0.38` s
- `python scripts/audit_audit_lite_zip_v4_0.py --zip projet-galapagos-v4.0-audit-lite.zip` : code `0`, `0.05` s
- `python scripts/smoke_audit_lite_zip_v4_0.py --zip projet-galapagos-v4.0-audit-lite.zip` : code `0`, `1.07` s
- `python -m pytest --collect-only -q` : code `0`, `2.37` s
