# Diagnostic ML/feature/label V9.44

- Version : `V9.44`.
- Source : `V9.43`.
- Decision : `feature_enrichment_before_more_ml`.
- Recommandation : `V9.45 - AggTrades Exact Feature Enrichment`.

## Diagnostic ML

- Baseline clear wins : `0`.
- Comparaisons proches du shuffle : `15`.
- Delta macro-F1 moyen vs meilleure baseline : `-0.071234`.
- Synthese baselines : Aucun modele learned ne produit de clear win; la moyenne de macro-F1 vs meilleure baseline est negative.
- Synthese shuffle : Quinze comparaisons restent proches du shuffle; seul le meilleur cas 1h validation reste legerement au-dessus mais non suffisant.
- Collapse : Les modeles learned predisent presque exclusivement FLAT; les arbres depth-2 sont equivalants a une majority baseline sur validation/test.
- Meilleur cas : 1h logistic_regression validation macro_f1=0.292091, balanced_accuracy=0.34209, flat_prediction_ratio=0.977879.
- Pire cas : 1m decision_tree_depth_2 test macro_f1=0.249419, balanced_accuracy=0.333333, flat_prediction_ratio=1.0.

## Diagnostic label

- Label : `up_down_flat_volnorm_h1_5y`.
- Ratio FLAT par timeframe : `{'15m': 0.653432, '1h': 0.673145, '1m': 0.612538, '5m': 0.638638}`.
- Entropie par timeframe : `{'15m': 1.277523, '1h': 1.238517, '1m': 1.350603, '5m': 1.30517}`.
- Diagnostic : Le label contribue fortement au collapse FLAT, mais les ratios FLAT de 61-67% n'expliquent pas seuls l'incapacite des modeles a predire DOWN/UP.

## Diagnostic features

- Nombre de features : `41`.
- Scan direct aggTrades full : `False`.
- Features exactes manquantes : `{'median_trade_size_exact': 'absent', 'large_trade_count_exact': 'absent', 'buyer_maker_count_exact': 'absent', 'taker_buy_sell_count_exact': 'absent', 'trade_size_distribution_buckets': 'absent'}`.
- Relation au collapse : Les features agrégées ne donnent pas assez de separation directionnelle; les modeles reduisent le risque en predisant la classe majoritaire FLAT.

## Comparaison options

- `feature_enrichment_aggtrades_exact` : `recommended_first` - Les modeles V9.43 ne sortent presque jamais de FLAT; les features aggTrades disponibles restent agrégées et ne couvrent pas les comptages exacts buyer-maker, tailles medianes, gros trades et buckets de taille.
- `label_redesign` : `recommended_after_feature_gap` - Le label h1 est majoritairement FLAT mais pas suffisamment extreme pour expliquer seul l'absence de discrimination; il faut toutefois tester un label directionnel binaire ou quantile apres enrichissement.
- `derivatives_data_extension` : `defer_until_aggtrades_exact_review` - Funding/open interest peuvent ajouter un regime derivatives utile, mais le diagnostic actuel pointe d'abord un manque de microstructure spot exacte dans les features existantes.
- `walk_forward` : `not_justified` - Aucun edge robuste n'est demontre par V9.43; les resultats sont proches du shuffle et des baselines.
- `stop_branch_or_manual_review` : `not_primary` - Les donnees et labels sont valides; l'etape la plus informative reste un enrichissement feature cible, puis un nouveau diagnostic.

## Garde-fous

- Aucun trading.
- Aucun paper live.
- Aucun ordre.
- Aucun backtest.
- Aucun walk-forward.
- Aucune strategie.
- Aucun signal actionnable.
- Aucun modele persistant.
- Aucun reseau.
- Aucun telechargement de nouvelles donnees.
- Aucune suppression destructive.
- Aucun sidecar et aucune empreinte ZIP.
