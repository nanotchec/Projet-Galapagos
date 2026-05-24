# Latest Summary V4.8

V4.7 est la dernière version validée par audit externe via audit-lite et attestation full locale.

V4.8 est la candidate courante. Elle produit uniquement un decision gate research après la chaîne complète 1 an V4.2 à V4.7, sans nouvelle donnée, sans nouveau modèle et sans backtest.

Verdict : mitigé et non concluant. `logistic_regression` montre un signal descriptif intéressant, mais la concentration par timeframe et les cas label shuffle sans avantage clair empêchent toute conclusion robuste.

Recommandation principale : A. Étendre à l historique max OHLCV.

Recommandation secondaire : E. Préparer une validation walk-forward offline.

Roadmap proposée : V5.0 historique max OHLCV, V5.1 features causales historique max, V5.2 labels forward historique max, V5.3 dataset offline avec design walk-forward, V5.4 ML offline et robustesse walk-forward/falsification.

Aucun trading, aucun paper live, aucun ordre, aucun backtest validant une stratégie et aucun claim de rentabilité.

V4.8 reste `pending_external_audit`.
