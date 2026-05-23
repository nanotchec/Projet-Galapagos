# Attestation full locale V4.6

- Scope : `full_local`
- Validation full locale remplacee par audit-lite : `false`
- Aucun trading, aucun backtest, aucun ordre, aucun modele persistant.

## Commandes executees

- `python scripts/run_one_year_offline_ml_research_v4_6.py` : PASS, `58.44`s
- `python scripts/validate_one_year_offline_ml_research_v4_6.py` : PASS, `33.92`s
- `python -m pytest -q tests/ml/test_one_year_offline_ml_research_v4_6.py` : PASS, `1.25`s
- `python -m pytest -q tests/validation/test_one_year_offline_ml_research_v4_6_validator.py` : PASS, `34.05`s
- `python scripts/release_audit_lite_zip_v4_6.py` : PASS, `2.88`s
- `python scripts/audit_audit_lite_zip_v4_6.py --zip projet-galapagos-v4.6-audit-lite.zip` : PASS, `0.34`s
- `python scripts/smoke_audit_lite_zip_v4_6.py --zip projet-galapagos-v4.6-audit-lite.zip` : PASS, `1.25`s
- `python -m pytest --collect-only -q` : PASS, `1.81`s

## Outputs scores complets

- `15m` : `140420` lignes, checksum `25c23aac857349d15de194a2556e2d3e16aecde40ece2f30d21b9c62a99f0ab0`
- `1h` : `35012` lignes, checksum `9e4f938b41a11fe9e40e8424749da55fb22156b235507dfdf29773457cd4a6f5`
- `1m` : `2108036` lignes, checksum `e675b74fd910c8c9180180e1b2f36c2aa5ffa68ee464bd21671eac923bec2b8a`
- `5m` : `421508` lignes, checksum `d9c7e96bba0f50fd47f95a128fa25aa3e2ab88ac4843c10a328336bc1a6dc1ee`
