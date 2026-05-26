# Projet Galapagos

- Derniere version validee : V8.8.
- Candidate : V8.9, OHLCV + trades feature audit / selection.

V8.9 audite et propose une selection/refactorisation des features OHLCV + aggTrades existantes sans recalculer les features, sans creer de dataset et sans entrainer de modele.

Fenetre : `2023-03-25` -> `2024-03-24`, `366` jours.

Feature columns originales : `71`.

Selected / dropped / review : `18` / `27` / `29`.

Aucun backtest, aucune strategie, aucun signal de trading, aucun ordre, aucun paper live, aucun trading reel et aucun modele ML.

## Commandes V8.9

```bash
python scripts/run_ohlcv_trades_feature_audit_v8_9.py
python scripts/validate_ohlcv_trades_feature_audit_v8_9.py
python -m pytest -q tests/features/test_ohlcv_trades_feature_audit_v8_9.py
python -m pytest -q tests/validation/test_ohlcv_trades_feature_audit_v8_9_validator.py
python scripts/release_audit_lite_zip_v8_9.py
python scripts/audit_audit_lite_zip_v8_9.py --zip projet-galapagos-v8.9-audit-lite.zip
python scripts/smoke_audit_lite_zip_v8_9.py --zip projet-galapagos-v8.9-audit-lite.zip
python -m pytest --collect-only -q
```
