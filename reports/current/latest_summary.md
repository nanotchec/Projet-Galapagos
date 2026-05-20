# Résumé courant — V2.8 candidate

La dernière version validée est **V2.7.2**. La version candidate est **V2.8**, en statut `pending_external_audit`.

V2.8 ajoute un laboratoire ML offline borné sur les datasets supervisés V2.7 validés. Les seules sorties sont des scores de recherche, des métriques descriptives, un manifest, un rapport et un validateur physique.

Les modèles autorisés sont volontairement simples : majority class, random seed baseline, logistic regression et decision tree depth 2. La cible unique est `up_down_flat_h1`.

Le système reste research/offline : aucun trading réel, aucun paper live, aucun ordre, aucun signal de trading, aucun backtest, aucune API privée et aucune clé API. Les métriques V2.8 ne sont pas actionnables et ne valident aucune stratégie.
