# État du Projet : V3.5.2 validée + candidat V3.6

- **Dernière version validée** : V3.5.2.
- **Versions antérieures validées** : V3.4.1, V3.3.1, V3.2.1, V3.1.10, V3.0, V2.9.1, V2.8.4, V2.7.2, V2.6.2, V2.5.2, V2.4.8, V2.3.1.
- **Version candidate** : V3.6.
- **Statut candidate** : `pending_external_audit`.
- **Direction suivante** : 90-day causal feature store preview.

## Dernière Couche Validée

- V3.5.2 valide les données OHLCV publiques BTCUSDT 90 jours.
- Fenêtre : 2024-01-01 au 2024-03-30 inclus.
- Row counts OHLCV V3.5 : 1m `129600`, 5m `25920`, 15m `8640`, 1h `2160`.
- Schéma OHLCV : `OHLCV_COLUMNS` strict.
- Aucun trou, aucun doublon, timestamps UTC et parent-child consistency validés.

## Candidat V3.6

- V3.6 produit uniquement un feature store OHLCV causal 90 jours à partir des OHLCV V3.5.2 validés.
- Outputs features V3.6 : 1m `129600`, 5m `25920`, 15m `8640`, 1h `2160` lignes.
- Schéma features : `FEATURE_COLUMNS_V3_6` strict.
- Warmup attendu : 30 lignes par timeframe.
- V3.6 ne produit aucun label, aucun dataset ML et aucun modèle ML.
- V3.6 ne produit aucun backtest, aucune stratégie, aucun signal de trading, aucun ordre et aucun trading réel.
- V3.6 reste candidate `pending_external_audit`.

## Clause De Sécurité

- Aucun trading réel.
- Aucun paper live.
- Aucun ordre.
- Aucun backtest.
- Aucune stratégie.
- Aucun signal de trading.
- Aucun label V3.6.
- Aucun dataset ML V3.6.
- Aucun modèle ML V3.6.
- Aucune API privée.
- Aucune clé API.
- V3.6 reste non validée avant audit externe.
