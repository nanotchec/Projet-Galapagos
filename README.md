# Projet Galapagos

- Derniere version validee : V7.9.
- Candidate : V8.0, OHLCV + public trades 90-day ML offline and robustness.

V8.0 entraine uniquement des baselines ML offline simples sur le dataset V7.9 OHLCV + aggTrades 90 jours, produit des scores de recherche `research_*`, puis audite la robustesse descriptive et la falsification par label shuffle.

Fenetre : `2023-03-25` -> `2023-06-22`, `90` jours.

Feature columns ML : `71`.

Aucun backtest, aucune strategie, aucun signal de trading, aucun ordre, aucun paper live, aucun trading reel et aucun modele persistant.

## Commandes V8.0

```bash
python scripts/run_ohlcv_trades_90d_offline_ml_research_v8_0.py
python scripts/validate_ohlcv_trades_90d_offline_ml_research_v8_0.py
python scripts/run_ohlcv_trades_90d_ml_robustness_v8_0.py
python scripts/validate_ohlcv_trades_90d_ml_robustness_v8_0.py
```

V8.0 reste `pending_external_audit` avant validation externe.
