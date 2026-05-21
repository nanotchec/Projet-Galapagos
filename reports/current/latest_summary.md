# Latest Summary

V3.0 est la dernière version validée par audit externe.

V3.1.7 est la candidate courante. Elle corrige uniquement le smoke V3.1 : chaque validateur utilise une réextraction ZIP propre, avec des logs écrits hors des roots validés et des timings de préparation.

V3.1.6 a été refusée en strict parce que le smoke bloquait encore pendant la préparation/exécution de validate_multi_day_causal_feature_store_v3_0. V3.1.7 conserve la séparation stricte avec les features V3.0 : aucune jointure features + labels, aucun dataset ML multi-day et aucun entraînement ML.

V3.1.7 reste `pending_external_audit`.

V3.1 ne produit aucun dataset ML, aucun modèle ML, aucun backtest, aucune stratégie, aucun paper live, aucun ordre et aucun trading réel.
