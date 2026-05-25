# Projet Galapagos

- Derniere version validee : V8.1.
- Candidate : V8.2, public aggTrades 1-year window expansion.

V8.2 etend uniquement l'ingestion data-only des aggTrades publics Binance BTCUSDT spot sur une fenetre d'environ 1 an.

Fenetre : `2023-03-25` -> `2024-03-24`, `366` jours.

Trade source type : `aggTrades`.

Raw files V8.2 : `366`.

Lignes trades V8.2 : `352055121`.

Aucune feature V8.2, aucun label V8.2, aucun dataset ML V8.2, aucun modele ML V8.2, aucun backtest, aucune strategie, aucun signal de trading, aucun ordre, aucun paper live et aucun trading reel.

## Commandes V8.2

```bash
python scripts/discover_public_trades_v8_2.py
python scripts/run_public_trades_1y_window_v8_2.py --no-network --skip-project-state-check
python scripts/validate_public_trades_1y_window_v8_2.py
python -m pytest -q tests/data/test_public_trades_1y_window_v8_2.py
python -m pytest -q tests/validation/test_public_trades_1y_window_v8_2_validator.py
python -m pytest --collect-only -q
```

V8.2 reste `pending_external_audit` avant validation externe.
