# Projet Galapagos

- Derniere version validee : V7.3.
- Candidate : V7.4, OHLCV + public trades offline ML research baselines.

V7.4 entraine uniquement des baselines ML offline simples sur le dataset V7.3 OHLCV + aggTrades, avec scores de recherche `research_*` et metriques descriptives.

Fenetre : `2023-03-25` -> `2023-04-23`, `30` jours.

Feature columns ML : `71`.

Aucun backtest, aucune strategie, aucun signal de trading, aucun ordre, aucun paper live, aucun trading reel et aucun modele persistant.

## Commandes V7.4

```bash
python scripts/run_ohlcv_trades_offline_ml_research_v7_4.py
python scripts/validate_ohlcv_trades_offline_ml_research_v7_4.py
python -m pytest -q tests/ml/test_ohlcv_trades_offline_ml_research_v7_4.py
python -m pytest -q tests/validation/test_ohlcv_trades_offline_ml_research_v7_4_validator.py
python scripts/release_audit_lite_zip_v7_4.py
python scripts/audit_audit_lite_zip_v7_4.py --zip projet-galapagos-v7.4-audit-lite.zip
python scripts/smoke_audit_lite_zip_v7_4.py --zip projet-galapagos-v7.4-audit-lite.zip
python -m pytest --collect-only -q
```

V7.4 reste `pending_external_audit` avant validation externe.
