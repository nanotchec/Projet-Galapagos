# État du Projet : V2.9.1 validée + candidat V3.0

- **Dernière version validée** : V2.9.1.
- **Versions antérieures validées** : V2.8.4, V2.7.2, V2.6.2, V2.5.2, V2.4.8, V2.3.1.
- **Version candidate** : V3.0.
- **Statut candidate** : `pending_external_audit`.
- **Direction suivante** : multi-day causal feature store preview.

## Candidat V3.0

- V3.0 produit uniquement des features OHLCV causales multi-day.
- Inputs autorisés : OHLCV multi-day V2.9 validés sous `data/research/v2_9/silver/ohlcv`.
- Outputs : features isolées sous `data/research/v3_0/features/ohlcv`.
- Fenêtre : 2024-01-15 à 2024-01-21 inclus.
- Row counts attendus : 1m `10080`, 5m `2016`, 15m `672`, 1h `168`.
- Les features single-day V2.5 ne sont pas écrasées.
- V3.0 ne produit aucun label, aucun dataset ML, aucun modèle ML, aucun backtest, aucune stratégie et aucun ordre.
- V3.0 reste candidate `pending_external_audit`.

## Clause De Sécurité

- Aucun trading réel.
- Aucun paper live.
- Aucun ordre.
- Aucun signal de trading.
- Aucun backtest.
- Aucune stratégie.
- Aucune API privée.
- Aucune clé API.
- Aucun modèle ML V3.0.
- V3.0 reste non validée avant audit externe.
