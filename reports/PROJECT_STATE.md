# État du Projet : V2.5.2 validée + candidat V2.6.1

- **Dernière version validée** : V2.5.2 (Feature Store Causal).
- **Versions antérieures validées** : V2.4.8 (Resampling OHLCV Silver), V2.3.1 (Ingestion Raw).
- **Version candidate** : V2.6.1.
- **Statut candidate** : `pending_external_audit`.
- **Direction suivante** : durcissement du manifest et du rapport JSON de la Clean Label Factory.
- **Contexte audit** : V2.6 est refusée en strict car son manifest et son rapport acceptaient des clés inattendues, des claims positives interdites et des mensonges sur `outputs` / `quality`.

## Candidat V2.6.1

- Le scope reste strictement celui de V2.6 : labels forward séparés en 1m, 5m, 15m et 1h sur BTCUSDT 2024-01-15.
- Aucun dataset ML n'est créé.
- Le manifest V2.6 applique un schéma strict top-level et nested.
- Le rapport JSON V2.6 est une projection déterministe du manifest.
- Les métriques `input_ohlcv`, `outputs` et `quality` sont recalculées depuis les fichiers physiques avant comparaison.
- Les claims positives interdites sont rejetées dans le manifest, le rapport JSON et le Markdown.
- `created_at_utc` et `label_run_id` sont validés par format strict.

## Clause De Sécurité

- Aucun trading réel.
- Aucun paper live.
- Aucun ordre.
- Aucun modèle ML.
- Aucun dataset ML.
- Aucun backtest.
- Aucune API privée.
- Aucune clé API.
- V2.6.1 reste non validée avant audit externe.
