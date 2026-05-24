# Attestation full locale V5.6.1

- Scope : `full_local`
- Validation full locale remplacee par audit-lite : `false`
- Fenetre : `2023-03-25` -> `2026-05-23`
- Total jours : `1156`
- Correction : roadmap Advanced OHLCV avant trades publics.
- Aucun trading, aucun backtest, aucun ordre, aucune strategie.

## Commandes executees

- `python scripts/validate_research_decision_gate_v5_6.py` : PASS, `0.24`s
- `python -m pytest -q tests/validation/test_research_decision_gate_v5_6.py` : PASS, `1.67`s
- `python -m pytest --collect-only -q` : PASS, `1.51`s
- `python scripts/release_audit_lite_zip_v5_6_1.py` : PASS, `0.5`s
- `python scripts/audit_audit_lite_zip_v5_6_1.py --zip projet-galapagos-v5.6.1-audit-lite.zip` : PASS, `0.5`s
- `python scripts/smoke_audit_lite_zip_v5_6_1.py --zip projet-galapagos-v5.6.1-audit-lite.zip` : PASS, `0.5`s
