# Résumé courant — V2.8.2 candidate

La dernière version validée est **V2.7.2**. La version candidate est **V2.8.2**, en statut `pending_external_audit`.

V2.8 a ajouté un laboratoire ML offline borné sur les datasets supervisés V2.7 validés. V2.8.1 a corrigé le packaging release/audit et le garde-fou d'artefacts interdits. V2.8.2 corrige uniquement le runtime du fichier complet de tests du validateur V2.8.

Le refus strict V2.8.1 portait sur un seul point : plusieurs tests d'artefacts interdits relançaient encore le validateur complet alors qu'un helper ciblé suffisait.

Le système reste research/offline : aucun trading réel, aucun paper live, aucun ordre, aucun signal de trading, aucun backtest, aucune stratégie, aucun modèle persistant, aucune API privée et aucune clé API. Les métriques V2.8 restent descriptives, non actionnables, et ne valident aucune stratégie.
