# Latest Summary

V3.0 est la dernière version validée par audit externe.

V3.1.6 est la candidate courante. Elle corrige uniquement l’isolation du smoke V3.1 : chaque validateur est lancé sur un root propre isolé, avec des logs écrits hors des roots validés.

V3.1.5 a été refusée en strict parce que le smoke lançait tous les validateurs sur le même root extrait, provoquant encore un timeout sur V2.8. V3.1.6 conserve la séparation stricte avec les features V3.0 : aucune jointure features + labels, aucun dataset ML multi-day et aucun entraînement ML.

V3.1.6 reste `pending_external_audit`.

V3.1 ne produit aucun dataset ML, aucun modèle ML, aucun backtest, aucune stratégie, aucun paper live, aucun ordre et aucun trading réel.
