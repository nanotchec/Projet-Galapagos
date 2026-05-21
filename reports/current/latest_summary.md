# Latest Summary

V3.3.1 est la dernière version validée par audit externe.

V3.4.1 est la candidate courante. Elle audite la robustesse descriptive et la falsification des baselines ML offline V3.3.1, sur BTCUSDT du 2024-01-15 au 2024-01-21.

V3.4 a été refusée en strict parce que des métriques impossibles synchronisées entre manifest et report JSON étaient acceptées. V3.4.1 durcit le validateur en bornant les métriques numériques V3.4.

Les analyses V3.4 incluent `baseline_delta`, `split_stability`, `timeframe_stability`, `label_shuffle_falsification`, `feature_leakage_scan` et `metric_forbidden_scan`.

Les scores V3.3 sont écrits sous `data/research/v3_3/ml/offline_research` avec quatre timeframes : 1m `40196` lignes, 5m `7940` lignes, 15m `2564` lignes et 1h `548` lignes.

V3.4.1 ne revendique aucun edge robuste, ne valide aucun modèle exploitable en trading et ne produit aucun signal actionnable.

V3.4.1 ne produit aucun modèle persistant, aucun backtest, aucune stratégie, aucun signal de trading, aucun paper live, aucun ordre et aucun trading réel.

V3.4.1 reste `pending_external_audit`.
