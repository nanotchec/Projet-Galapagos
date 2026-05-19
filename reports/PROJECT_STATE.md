# État du Projet : V2.5.2 validée + candidat V2.6.2

- **Dernière version validée** : V2.5.2 (Feature Store Causal).
- **Versions antérieures validées** : V2.4.8 (Resampling OHLCV Silver), V2.3.1 (Ingestion Raw).
- **Version candidate** : V2.6.2.
- **Statut candidate** : `pending_external_audit`.
- **Direction suivante** : durcissement du garde-fou contre les artefacts dataset ML / backtest / execution dans la Clean Label Factory.
- **Contexte audit** : V2.6.1 est refusée en strict car le validateur acceptait `data/gold/datasets/ml_offline` et d'autres chemins réalistes de dataset ML ou d'exécution.

## Candidat V2.6.2

- Le scope reste strictement celui de V2.6 : labels forward séparés en 1m, 5m, 15m et 1h sur BTCUSDT 2024-01-15.
- Aucun dataset ML n'est créé.
- Le validateur rejette les artefacts interdits sous `data/gold/datasets`, `reports/ml`, `reports/backtests`, `models`, `orders` et `execution` dans le périmètre V2.6.
- Les chemins légitimes `data/gold/features` et `data/gold/labels` restent autorisés.
- Les schémas stricts manifest/report de V2.6.1 restent actifs.

## Clause De Sécurité

- Aucun trading réel.
- Aucun paper live.
- Aucun ordre.
- Aucun modèle ML.
- Aucun dataset ML.
- Aucun backtest.
- Aucune API privée.
- Aucune clé API.
- V2.6.2 reste non validée avant audit externe.
