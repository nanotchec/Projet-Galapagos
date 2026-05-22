# Latest Metrics

- Dernière version validée : `V3.8`
- Candidate : `V3.9`
- Statut : `pending_external_audit`
- Direction : 90-day offline ML research baselines

## Row counts V3.9 scores

- 1m : `518276`
- 5m : `103556`
- 15m : `34436`
- 1h : `8516`

## Lignes utilisées pour le ML

- 1m : `129569`
- 5m : `25889`
- 15m : `8609`
- 1h : `2129`

## Splits ML utilisés

- 1m : train `77730`, validation `25920`, test `25919`
- 5m : train `15522`, validation `5184`, test `5183`
- 15m : train `5154`, validation `1728`, test `1727`
- 1h : train `1266`, validation `432`, test `431`

## Politique ML

- Cible : `up_down_flat_h1`
- Modèles : `majority_class_baseline`, `random_seeded_baseline`, `logistic_regression`, `decision_tree_depth_2`
- Features autorisées : `31`
- Warmup exclu : `true`
- Labels h1 invalides exclus : `true`
- Shuffle : `false`

## Safety

- Aucun modèle persistant.
- Aucun backtest.
- Aucune stratégie.
- Aucun signal de trading.
- Aucun paper live.
- Aucun ordre.
- Aucun trading réel.
