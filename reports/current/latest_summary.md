# Latest Summary

V3.0 est la dernière version validée par audit externe.

V3.1.8 est la candidate courante. Elle corrige uniquement le smoke V3.1 : le smoke ne relance plus les validateurs historiques V2.3 à V3.0, vérifie leurs artefacts par manifest/rapports, lit les labels V3.1 et relance uniquement `validate_multi_day_label_factory_v3_1.py`.

V3.1.7 a été refusée en strict parce que le smoke relançait encore trop de validateurs historiques lourds. V3.1.8 conserve la séparation stricte avec les features V3.0 : aucune jointure features + labels, aucun dataset ML multi-day et aucun entraînement ML.

Garanties de périmètre V3.1 : aucun dataset ML V3.1, aucun modèle ML V3.1, aucun backtest, aucune stratégie, aucun paper live, aucun ordre et aucun trading réel.

V3.1.8 reste `pending_external_audit`.

V3.1 ne produit aucun dataset ML, aucun modèle ML, aucun backtest, aucune stratégie, aucun paper live, aucun ordre et aucun trading réel.
