# Projet Galapagos

- Derniere version validee : V7.1.
- Candidate : V7.2, OHLCV + public trades feature store preview.

V7.2 produit uniquement des features causales OHLCV + aggTrades Binance publiques sur la fenetre V7.1 de 30 jours.

Aucun label V7.2, aucun dataset ML V7.2, aucun modele ML V7.2, aucun backtest, aucune strategie, aucun signal de trading, aucun ordre et aucun trading reel.

## Commandes V7.2

```bash
python scripts/run_ohlcv_trades_feature_store_v7_2.py
python scripts/validate_ohlcv_trades_feature_store_v7_2.py
python -m pytest -q tests/features/test_ohlcv_trades_features_v7_2.py
python -m pytest -q tests/validation/test_ohlcv_trades_feature_store_v7_2_validator.py
python scripts/release_audit_lite_zip_v7_2.py
python scripts/audit_audit_lite_zip_v7_2.py --zip projet-galapagos-v7.2-audit-lite.zip
python scripts/smoke_audit_lite_zip_v7_2.py --zip projet-galapagos-v7.2-audit-lite.zip
python -m pytest --collect-only -q
```

V7.2 reste `pending_external_audit` avant validation externe.
