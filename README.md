# Projet Galapagos

- Derniere version validee : V8.8.
- Candidate : V8.9.1, correctif packaging audit-lite V8.9 autoporteur.

V8.9.1 corrige uniquement le ZIP audit-lite V8.9 pour inclure les petits manifests/reports d'entree necessaires aux tests et validateurs nominaux. Les rapports metier et resultats V8.9 restent inchanges.

Fenetre : `2023-03-25` -> `2024-03-24`, `366` jours.

Feature columns originales : `71`.

Selected / dropped / review : `18` / `27` / `29`.

Aucun backtest, aucune strategie, aucun signal de trading, aucun ordre, aucun paper live, aucun trading reel et aucun modele ML.

## Commandes V8.9.1

```bash
python scripts/release_audit_lite_zip_v8_9_1.py
python scripts/audit_audit_lite_zip_v8_9_1.py --zip projet-galapagos-v8.9.1-audit-lite.zip
python scripts/smoke_audit_lite_zip_v8_9_1.py --zip projet-galapagos-v8.9.1-audit-lite.zip
PYTHONPATH=src python -m pytest --collect-only -q
PYTHONPATH=src python -m pytest -q tests/features/test_ohlcv_trades_feature_audit_v8_9.py tests/validation/test_ohlcv_trades_feature_audit_v8_9_validator.py
```
