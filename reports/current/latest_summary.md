# Latest Summary

V3.8 est la dernière version validée par audit externe via audit-lite et attestation full locale.

V3.9 est la candidate courante. Elle entraîne uniquement des baselines ML offline simples sur le dataset supervisé offline 90 jours V3.8 validé.

Les inputs restent BTCUSDT spot Binance public archive, fenêtre 2024-01-01 à 2024-03-30 inclus, avec datasets et splits V3.8 strictement temporels.

Les outputs V3.9 sont des scores de recherche offline dans `data/research/v3_9/ml/offline_research`, avec schéma `ML_SCORE_COLUMNS_V3_9` strict. Les modèles autorisés sont `majority_class_baseline`, `random_seeded_baseline`, `logistic_regression` et `decision_tree_depth_2`.

La cible unique est `up_down_flat_h1`. Les lignes `warmup_row = true` et `label_valid_h1 = false` sont exclues. Aucune feature `future_*`, `label_*`, `direction_*`, `up_down_flat_*`, `split`, `signal`, `order`, `strategy`, `pnl` ou `backtest` n'est utilisée.

V3.9 ne produit aucun modèle persistant, aucun backtest, aucune stratégie, aucun signal de trading, aucun paper live, aucun ordre et aucun trading réel.

V3.9 reste `pending_external_audit`.
