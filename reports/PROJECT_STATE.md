# État du Projet : V3.7 validée + candidat V3.8

- **Dernière version validée** : V3.7.
- **Versions antérieures validées** : V3.6, V3.5.2, V3.4.1, V3.3.1, V3.2.1, V3.1.10, V3.0, V2.9.1, V2.8.4, V2.7.2, V2.6.2, V2.5.2, V2.4.8, V2.3.1.
- **Version candidate** : V3.8.
- **Statut candidate** : `pending_external_audit`.
- **Direction suivante** : 90-day offline supervised dataset assembly preview.

## Dernière Couche Validée

- V3.7 valide les labels forward 90 jours séparés à partir des OHLCV V3.5.2 validés.
- Fenêtre : 2024-01-01 au 2024-03-30 inclus.
- Row counts labels V3.7 : 1m `129600`, 5m `25920`, 15m `8640`, 1h `2160`.
- Schéma labels : `LABEL_COLUMNS_V3_7` strict.
- Aucun dataset ML V3.7, aucun modèle ML V3.7, aucun backtest et aucun trading réel.

## Candidat V3.8

- V3.8 assemble uniquement un dataset supervisé offline 90 jours à partir des features V3.6 et labels V3.7 validés.
- Outputs datasets V3.8 : 1m `129600`, 5m `25920`, 15m `8640`, 1h `2160` lignes.
- Schéma dataset : `DATASET_COLUMNS_V3_8` strict.
- Splits temporels : train 60 %, validation 20 %, test 20 %, sans shuffle.
- V3.8 ne produit aucun ML, aucun modèle, aucune prédiction, aucun score ML, aucun backtest, aucune stratégie, aucun signal de trading, aucun ordre et aucun trading réel.
- V3.8 reste candidate `pending_external_audit`.

## Clause De Sécurité

- Aucun trading réel.
- Aucun paper live.
- Aucun ordre.
- Aucun backtest.
- Aucune stratégie.
- Aucun signal de trading.
- Aucun ML V3.8.
- Aucun modèle V3.8.
- Aucune API privée.
- Aucune clé API.
- V3.8 reste non validée avant audit externe.
