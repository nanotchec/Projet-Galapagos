# Latest Summary

V3.2.1 est la dernière version validée par audit externe.

V3.3 est la candidate courante. Elle entraîne des baselines ML offline simples sur le dataset supervisé multi-day V3.2, sur BTCUSDT du 2024-01-15 au 2024-01-21.

Les scores V3.3 sont écrits sous `data/research/v3_3/ml/offline_research` avec quatre timeframes : 1m `40196` lignes, 5m `7940` lignes, 15m `2564` lignes et 1h `548` lignes.

La cible unique est `up_down_flat_h1`. Les features sont limitées aux colonnes causales V3.0 autorisées. Les métriques sont descriptives et non actionnables.

V3.3 ne produit aucun modèle persistant, aucun backtest, aucune stratégie, aucun paper live, aucun ordre et aucun trading réel.

V3.3 reste `pending_external_audit`.
