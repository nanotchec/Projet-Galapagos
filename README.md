# Projet Galapagos

- Derniere version validee : V7.2.
- Candidate : V7.3, OHLCV + public trades offline supervised dataset preview.

V7.3 assemble uniquement un dataset supervise offline OHLCV + aggTrades Binance publiques avec labels V5.2 filtres sur la fenetre V7.2 de 30 jours.

Aucun ML V7.3, aucun modele V7.3, aucun backtest, aucune strategie, aucun signal de trading, aucun ordre et aucun trading reel.

## Commandes V7.3

```bash
python scripts/run_ohlcv_trades_offline_supervised_dataset_v7_3.py
python scripts/validate_ohlcv_trades_offline_supervised_dataset_v7_3.py
python -m pytest -q tests/datasets/test_ohlcv_trades_offline_supervised_dataset_v7_3.py
python -m pytest -q tests/validation/test_ohlcv_trades_offline_supervised_dataset_v7_3_validator.py
python scripts/release_audit_lite_zip_v7_3.py
python scripts/audit_audit_lite_zip_v7_3.py --zip projet-galapagos-v7.3-audit-lite.zip
python scripts/smoke_audit_lite_zip_v7_3.py --zip projet-galapagos-v7.3-audit-lite.zip
python -m pytest --collect-only -q
```

V7.3 reste `pending_external_audit` avant validation externe.
