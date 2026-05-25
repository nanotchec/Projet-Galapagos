# Projet Galapagos

- Derniere version validee : V8.2.
- Candidate : V8.3, OHLCV + public trades 1-year feature store preview.

V8.3 produit uniquement des features causales OHLCV + aggTrades Binance publiques sur la fenetre V8.2 de 366 jours.

Aucun label V8.3, aucun dataset ML V8.3, aucun modele ML V8.3, aucun backtest, aucune strategie, aucun signal de trading, aucun ordre et aucun trading reel.

## Commandes V8.3

```bash
python scripts/run_ohlcv_trades_1y_feature_store_v8_3.py
python scripts/validate_ohlcv_trades_1y_feature_store_v8_3.py
python -m pytest -q tests/features/test_ohlcv_trades_1y_features_v8_3.py
python -m pytest -q tests/validation/test_ohlcv_trades_1y_feature_store_v8_3_validator.py
python scripts/release_audit_lite_zip_v8_3.py
python scripts/audit_audit_lite_zip_v8_3.py --zip projet-galapagos-v8.3-audit-lite.zip
python scripts/smoke_audit_lite_zip_v8_3.py --zip projet-galapagos-v8.3-audit-lite.zip
python -m pytest --collect-only -q
```

V8.3 reste `pending_external_audit` avant validation externe.
