# Attestation full locale V6.4

- Scope : `full_local`
- Validation full locale remplacee par audit-lite : `false`
- Fenetre : `2023-03-25` -> `2026-05-23`
- Total jours : `1156`
- Advanced feature columns count : `158`
- Decision : trades publics historiques en prochaine etape research.
- Aucun trading, aucun backtest, aucun ordre, aucune strategie.

## Commandes executees

- `python scripts/validate_research_decision_gate_v6_4.py` : PASS, `0.24`s
- `python -m pytest -q tests/validation/test_research_decision_gate_v6_4.py` : PASS, `1.67`s
- `python -m pytest --collect-only -q` : PASS, `1.51`s
- `python scripts/release_audit_lite_zip_v6_4.py` : PASS, `0.5`s
- `python scripts/audit_audit_lite_zip_v6_4.py --zip projet-galapagos-v6.4-audit-lite.zip` : PASS, `0.5`s
- `python scripts/smoke_audit_lite_zip_v6_4.py --zip projet-galapagos-v6.4-audit-lite.zip` : PASS, `0.5`s
