# Projet Galapagos

- Derniere version validee : V7.7.
- Candidate : V7.8, OHLCV + public trades 90-day feature store preview.

V7.8 produit uniquement des features causales OHLCV + aggTrades Binance publiques sur la fenetre V7.7 de 90 jours.

Aucun label V7.8, aucun dataset ML V7.8, aucun modele ML V7.8, aucun backtest, aucune strategie, aucun signal de trading, aucun ordre et aucun trading reel.

## Commandes V7.8

```bash
python scripts/run_ohlcv_trades_90d_feature_store_v7_8.py
python scripts/validate_ohlcv_trades_90d_feature_store_v7_8.py
python -m pytest -q tests/features/test_ohlcv_trades_90d_features_v7_8.py
python -m pytest -q tests/validation/test_ohlcv_trades_90d_feature_store_v7_8_validator.py
python scripts/release_audit_lite_zip_v7_8.py
python scripts/audit_audit_lite_zip_v7_8.py --zip projet-galapagos-v7.8-audit-lite.zip
python scripts/smoke_audit_lite_zip_v7_8.py --zip projet-galapagos-v7.8-audit-lite.zip
python -m pytest --collect-only -q
```

V7.8 reste `pending_external_audit` avant validation externe.
