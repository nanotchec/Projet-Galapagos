# Latest Summary

V3.0 est la dernière version validée par audit externe.

V3.1.9 est la candidate courante. Elle corrige uniquement le runtime du script run V3.1 : `run_multi_day_label_factory_v3_1.py` génère désormais les labels avec `validate_previous_layers=False` par défaut.

V3.1.8 a été refusée en strict parce que `run_multi_day_label_factory_v3_1.py` relançait les validations historiques et timeout. V3.1.9 conserve la séparation stricte avec les features V3.0 : aucune jointure features + labels, aucun dataset ML multi-day et aucun entraînement ML.

Garanties de périmètre V3.1 : aucun dataset ML V3.1, aucun modèle ML V3.1, aucun backtest, aucune stratégie, aucun paper live, aucun ordre et aucun trading réel.

V3.1.9 reste `pending_external_audit`.

V3.1 ne produit aucun dataset ML, aucun modèle ML, aucun backtest, aucune stratégie, aucun paper live, aucun ordre et aucun trading réel.
