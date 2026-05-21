# État du Projet : V3.0 validée + candidat V3.1.9

- **Dernière version validée** : V3.0.
- **Versions antérieures validées** : V2.9.1, V2.8.4, V2.7.2, V2.6.2, V2.5.2, V2.4.8, V2.3.1.
- **Version candidate** : V3.1.9.
- **Statut candidate** : `pending_external_audit`.
- **Direction suivante** : correction smoke-only avec reextraction ZIP par validateur.

## Candidat V3.1.9

- V3.1.8 a été refusée en strict parce que `run_multi_day_label_factory_v3_1.py` relançait les validations historiques et timeout.
- V3.1.9 conserve les labels forward multi-day séparés et corrige uniquement le runtime du script run : par défaut, `validate_previous_layers=False`; les validations historiques restent exécutées séparément par les commandes d'audit.
- Inputs autorisés : OHLCV multi-day V2.9 validés sous `data/research/v2_9/silver/ohlcv`.
- Outputs : labels isolés sous `data/research/v3_1/labels/forward_returns`.
- Fenêtre : 2024-01-15 à 2024-01-21 inclus.
- Row counts attendus : 1m `10080`, 5m `2016`, 15m `672`, 1h `168`.
- Horizons : `[1, 3, 5]`.
- Threshold fixe : `0.0005`.
- Les features multi-day V3.0 restent séparées et ne sont pas modifiées par V3.1.
- V3.1 ne produit aucun dataset ML, aucun modèle ML, aucun backtest, aucune stratégie et aucun ordre.
- V3.1.9 reste candidate `pending_external_audit`.

## Clause De Sécurité

- Aucun trading réel.
- Aucun paper live.
- Aucun ordre.
- Aucun signal de trading.
- Aucun backtest.
- Aucune stratégie.
- Aucune API privée.
- Aucune clé API.
- Aucun modèle ML V3.1.
- V3.1.9 reste non validée avant audit externe.
