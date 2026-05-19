# État du Projet : V2.6.2 validée + candidat V2.7.1

- **Dernière version validée** : V2.6.2 (Clean Label Factory hardened).
- **Versions antérieures validées** : V2.5.2 (Feature Store Causal), V2.4.8 (Resampling OHLCV Silver), V2.3.1 (Ingestion Raw).
- **Version candidate** : V2.7.1.
- **Statut candidate** : `pending_external_audit`.
- **Direction suivante** : offline supervised dataset validator runtime finalization.

## Candidat V2.7.1

- V2.7 assemble les features causales V2.5 et les labels forward V2.6 dans un dataset supervise offline.
- V2.7 a été refusée en strict uniquement parce que le fichier complet de tests du validateur V2.7 était trop lent en audit externe.
- V2.7.1 conserve les artefacts V2.7 et finalise le runtime des tests du validateur sans relâcher la validation de production.
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
- V2.7.1 reste non validée avant audit externe.
