# Projet Galapagos

- Derniere version validee : V8.3.
- Candidate : V8.4, OHLCV + public trades 1-year offline supervised dataset preview.

V8.4 assemble uniquement un dataset supervise offline OHLCV + aggTrades Binance publiques avec labels V5.2 filtres sur la fenetre V8.3 d'environ 1 an.

Aucun ML V8.4, aucun modele V8.4, aucun backtest, aucune strategie, aucun signal de trading, aucun ordre et aucun trading reel.

## Commandes V8.4

```bash
python scripts/run_ohlcv_trades_1y_offline_supervised_dataset_v8_4.py
python scripts/validate_ohlcv_trades_1y_offline_supervised_dataset_v8_4.py
python -m pytest -q tests/datasets/test_ohlcv_trades_1y_offline_supervised_dataset_v8_4.py
python -m pytest -q tests/validation/test_ohlcv_trades_1y_offline_supervised_dataset_v8_4_validator.py
python scripts/release_audit_lite_zip_v8_4.py
python scripts/audit_audit_lite_zip_v8_4.py --zip projet-galapagos-v8.4-audit-lite.zip
python scripts/smoke_audit_lite_zip_v8_4.py --zip projet-galapagos-v8.4-audit-lite.zip
python -m pytest --collect-only -q
```

V8.4 reste `pending_external_audit` avant validation externe.
