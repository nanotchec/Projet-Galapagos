# Résumé courant — V2.7.2 candidate

La dernière version validée est **V2.6.2**. La version candidate est **V2.7.2**, en statut `pending_external_audit`.

V2.7 assemble un premier dataset supervise offline a partir des features causales V2.5 et des labels forward V2.6. Les splits temporels train / validation / test sont produits comme preview technique sur BTCUSDT 2024-01-15.

V2.7.1 a été refusée en strict uniquement parce que le fichier complet de tests du validateur V2.7 restait trop lent en audit externe. V2.7.2 impose un hard cap de 4 tests d'intégration complète du validateur et transforme les autres controles en tests cibles rapides, sans changer la logique dataset ni relâcher le validateur de production.

Le système reste data/research only : aucun trading réel, aucun paper live, aucun ordre, aucun ML, aucun modèle, aucun backtest, aucune API privée et aucune clé API.
