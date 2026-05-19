# État du Projet : V2.6.2 validée + candidat V2.7

- **Dernière version validée** : V2.6.2 (Clean Label Factory hardened).
- **Versions antérieures validées** : V2.5.2 (Feature Store Causal), V2.4.8 (Resampling OHLCV Silver), V2.3.1 (Ingestion Raw).
- **Version candidate** : V2.7.
- **Statut candidate** : `pending_external_audit`.
- **Direction suivante** : offline supervised dataset assembly preview.

## Candidat V2.7

- V2.7 assemble les features causales V2.5 et les labels forward V2.6 dans un dataset supervise offline.
- Les sorties couvrent `1m`, `5m`, `15m` et `1h` sur BTCUSDT 2024-01-15.
- Les splits temporels train / validation / test sont une preview technique sans shuffle.
- Les fichiers features et labels sources restent separes et leurs hashes sont controles.
- V2.7 ne declare aucune strategie validee et ne produit aucun modele.

## Clause De Sécurité

- Aucun trading réel.
- Aucun paper live.
- Aucun ordre.
- Aucun modèle ML.
- Aucun backtest.
- Aucune API privée.
- Aucune clé API.
- V2.7 reste non validée avant audit externe.
