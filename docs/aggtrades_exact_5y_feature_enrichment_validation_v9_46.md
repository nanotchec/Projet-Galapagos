# Validation features exactes aggTrades 5Y V9.46

- Decision : `aggtrades_exact_5y_feature_enrichment_validated_with_non_blocking_warnings`.
- Recommandation : `V9.47 - Combine Base + Exact AggTrades Feature Store`.
- Mode : `full-local`.
- Fenetre : `2021-05-05` -> `2026-05-05`.
- Coverage : `PASS`.
- Schema : `PASS`.
- Qualite : `PASS`.
- Leakage guard : `PASS`.
- Forbidden columns scan : `PASS`.
- Zero-trade buckets : `{'1m': 542, '5m': 108, '15m': 36, '1h': 8}`.
- Row counts : `{'1m': 2630880, '5m': 526176, '15m': 175392, '1h': 43848}`.

## Reconciliation runtime / stockage

- Free GiB courant data mount : `61.67`.
- Free GiB V9.45 : `60.692`.
- Output size GiB : `0.872`.
- Runtime reporting acceptable : `True`.

## Garde-fous

- Validation-only.
- Aucun feature store combine cree.
- Aucun label, dataset supervise, ML, backtest, walk-forward, strategie ou signal.
- Aucun reseau, aucune cle API, aucun endpoint prive.
- Aucune suppression destructive, aucun sidecar et aucune empreinte ZIP.
