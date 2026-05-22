# État du Projet : V3.6 validée + candidat V3.7

- **Dernière version validée** : V3.6.
- **Versions antérieures validées** : V3.5.2, V3.4.1, V3.3.1, V3.2.1, V3.1.10, V3.0, V2.9.1, V2.8.4, V2.7.2, V2.6.2, V2.5.2, V2.4.8, V2.3.1.
- **Version candidate** : V3.7.
- **Statut candidate** : `pending_external_audit`.
- **Direction suivante** : 90-day clean forward label factory preview.

## Dernière Couche Validée

- V3.6 valide les features OHLCV causales 90 jours à partir des OHLCV V3.5.2 validés.
- Fenêtre : 2024-01-01 au 2024-03-30 inclus.
- Row counts features V3.6 : 1m `129600`, 5m `25920`, 15m `8640`, 1h `2160`.
- Schéma features : `FEATURE_COLUMNS_V3_6` strict.
- Aucun label V3.6, aucun dataset ML V3.6, aucun modèle ML V3.6, aucun backtest et aucun trading réel.

## Candidat V3.7

- V3.7 produit uniquement des labels forward 90 jours séparés à partir des OHLCV V3.5 validés.
- Outputs labels V3.7 : 1m `129600`, 5m `25920`, 15m `8640`, 1h `2160` lignes.
- Schéma labels : `LABEL_COLUMNS_V3_7` strict.
- Horizons : `[1, 3, 5]`.
- Threshold fixe : `0.0005`.
- V3.7 ne joint pas features et labels.
- V3.7 ne produit aucun dataset ML, aucun modèle ML, aucun backtest, aucune stratégie, aucun signal de trading, aucun ordre et aucun trading réel.
- V3.7 reste candidate `pending_external_audit`.

## Clause De Sécurité

- Aucun trading réel.
- Aucun paper live.
- Aucun ordre.
- Aucun backtest.
- Aucune stratégie.
- Aucun signal de trading.
- Aucun dataset ML V3.7.
- Aucun modèle ML V3.7.
- Aucune API privée.
- Aucune clé API.
- V3.7 reste non validée avant audit externe.
