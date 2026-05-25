# Projet Galapagos

- Derniere version validee : V7.8.
- Candidate : V7.9, OHLCV + public trades 90-day offline supervised dataset preview.

V7.9 assemble uniquement un dataset supervise offline OHLCV + aggTrades Binance publiques avec labels V5.2 filtres sur la fenetre V7.8 de 90 jours.

Aucun ML V7.9, aucun modele V7.9, aucun backtest, aucune strategie, aucun signal de trading, aucun ordre et aucun trading reel.

## Commandes V7.9

```bash
python scripts/run_ohlcv_trades_90d_offline_supervised_dataset_v7_9.py
python scripts/validate_ohlcv_trades_90d_offline_supervised_dataset_v7_9.py
python -m pytest -q tests/datasets/test_ohlcv_trades_90d_offline_supervised_dataset_v7_9.py
python -m pytest -q tests/validation/test_ohlcv_trades_90d_offline_supervised_dataset_v7_9_validator.py
python scripts/release_audit_lite_zip_v7_9.py
python scripts/audit_audit_lite_zip_v7_9.py --zip projet-galapagos-v7.9-audit-lite.zip
python scripts/smoke_audit_lite_zip_v7_9.py --zip projet-galapagos-v7.9-audit-lite.zip
python -m pytest --collect-only -q
```

V7.9 reste `pending_external_audit` avant validation externe.
