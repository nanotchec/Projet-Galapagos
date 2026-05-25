# Projet Galapagos

- Derniere version validee : V8.5.
- Candidate : V8.6, OHLCV + public trades 1-year robustness and research decision gate.

V8.6 audite uniquement les resultats ML offline V8.5, produit des diagnostics de robustesse/falsification et une decision gate research. Elle ne produit aucun backtest, aucune strategie et aucun signal de trading.

Fenetre : `2023-03-25` -> `2024-03-24`, `366` jours.

Feature columns ML : `71`.

Verdict research : `interessant_mais_mitige_non_concluant`.

Recommandation principale : D. Preparer une validation walk-forward offline plus stricte.

Recommandation secondaire : B. Ameliorer/refactoriser les features OHLCV + trades.

## Commandes V8.6

```bash
python scripts/run_ohlcv_trades_1y_ml_robustness_v8_6.py
python scripts/validate_ohlcv_trades_1y_ml_robustness_v8_6.py
python scripts/run_research_decision_gate_v8_6.py
python scripts/validate_research_decision_gate_v8_6.py
python -m pytest -q tests/ml/test_ohlcv_trades_1y_ml_robustness_v8_6.py
python -m pytest -q tests/validation/test_ohlcv_trades_1y_ml_robustness_v8_6_validator.py
python -m pytest -q tests/validation/test_research_decision_gate_v8_6.py
python scripts/release_audit_lite_zip_v8_6.py
python scripts/audit_audit_lite_zip_v8_6.py --zip projet-galapagos-v8.6-audit-lite.zip
python scripts/smoke_audit_lite_zip_v8_6.py --zip projet-galapagos-v8.6-audit-lite.zip
python -m pytest --collect-only -q
```

V8.6 reste `pending_external_audit` avant validation externe.
