# Latest Summary

V3.0 est la dernière version validée par audit externe.

V3.1.5 est la candidate courante. Elle corrige uniquement l’isolation des logs du smoke V3.1.5 : les validateurs sont lancés dans le root extrait, mais leurs logs sont écrits dans un dossier `smoke_logs` séparé, hors du projet extrait.

V3.1.4 a été refusée en strict uniquement parce que le smoke écrivait ses logs dans le root extrait du ZIP, polluant les validateurs suivants. V3.1.5 conserve la séparation stricte avec les features V3.0 : aucune jointure features + labels, aucun dataset ML multi-day et aucun entraînement ML.

V3.1.5 reste `pending_external_audit`.

V3.1 ne produit aucun dataset ML, aucun modèle ML, aucun backtest, aucune stratégie, aucun paper live, aucun ordre et aucun trading réel.
