# Projet Galapagos

- Derniere version validee : V8.6.
- Candidate : V8.7, strict walk-forward offline validation.

V8.7 applique une validation walk-forward offline stricte sur le dataset V8.4 OHLCV + aggTrades 1 an avec des baselines ML simples par fold et des scores de recherche `research_*`.

Fenetre : `2023-03-25` -> `2024-03-24`, `366` jours.

Feature columns : `71`.

Aucun backtest, aucune strategie, aucun signal de trading, aucun ordre, aucun paper live, aucun trading reel et aucun modele persistant.

## Commandes V8.7

```bash
python scripts/run_strict_walk_forward_validation_v8_7.py
python scripts/validate_strict_walk_forward_validation_v8_7.py
python scripts/release_audit_lite_zip_v8_7.py
python scripts/audit_audit_lite_zip_v8_7.py --zip projet-galapagos-v8.7-audit-lite.zip
python scripts/smoke_audit_lite_zip_v8_7.py --zip projet-galapagos-v8.7-audit-lite.zip
```
