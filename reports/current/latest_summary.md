# Latest Summary

V3.0 est la dernière version validée par audit externe.

V3.1.10 est la candidate courante. Elle corrige uniquement les références de tests smoke V3.1 : les tests validator lisent désormais `smoke_test_clean_zip_v3_1_10.py`.

V3.1.9 a été refusée en strict parce que les tests V3.1 référaient encore `smoke_test_clean_zip_v3_1_8.py`, absent du ZIP V3.1.9. V3.1.10 conserve la séparation stricte avec les features V3.0 : aucune jointure features + labels, aucun dataset ML multi-day et aucun entraînement ML.

Garanties de périmètre V3.1 : aucun dataset ML V3.1, aucun modèle ML V3.1, aucun backtest, aucune stratégie, aucun paper live, aucun ordre et aucun trading réel.

V3.1.10 reste `pending_external_audit`.

V3.1 ne produit aucun dataset ML, aucun modèle ML, aucun backtest, aucune stratégie, aucun paper live, aucun ordre et aucun trading réel.
