# Projet Galapagos

- Derniere version validee : V8.4.
- Candidate : V8.5, OHLCV + public trades 1-year ML offline.

V8.5 entraine uniquement des baselines ML offline simples sur le dataset V8.4 OHLCV + aggTrades, avec scores de recherche `research_*` et metriques descriptives.

Fenetre : `2023-03-25` -> `2024-03-24`, `366` jours.

Feature columns ML : `71`.

Aucun backtest, aucune strategie, aucun signal de trading, aucun ordre, aucun paper live, aucun trading reel et aucun modele persistant.

## Commandes V8.5

```bash
python scripts/run_ohlcv_trades_1y_offline_ml_research_v8_5.py
python scripts/validate_ohlcv_trades_1y_offline_ml_research_v8_5.py
python -m pytest -q tests/ml/test_ohlcv_trades_1y_offline_ml_research_v8_5.py
python -m pytest -q tests/validation/test_ohlcv_trades_1y_offline_ml_research_v8_5_validator.py
python scripts/release_audit_lite_zip_v8_5.py
python scripts/audit_audit_lite_zip_v8_5.py --zip projet-galapagos-v8.5-audit-lite.zip
python scripts/smoke_audit_lite_zip_v8_5.py --zip projet-galapagos-v8.5-audit-lite.zip
python -m pytest --collect-only -q
```

V8.5 reste `pending_external_audit` avant validation externe.
