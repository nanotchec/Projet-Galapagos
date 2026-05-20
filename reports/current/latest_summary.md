# Résumé courant — V2.8.1 candidate

La dernière version validée est **V2.7.2**. La version candidate est **V2.8.1**, en statut `pending_external_audit`.

V2.8 a ajouté un laboratoire ML offline borné sur les datasets supervisés V2.7 validés. V2.8.1 corrige uniquement le packaging release/audit et le garde-fou d'artefacts interdits.

Le refus strict V2.8 portait sur deux points : les scripts release/audit dépendaient d'un script V2.7.2 absent du ZIP clean, et le validateur V2.8 ne rejetait pas encore certains backtests ou modèles persistants créés sous `reports/backtests` et `data/gold/ml`.

Le système reste research/offline : aucun trading réel, aucun paper live, aucun ordre, aucun signal de trading, aucun backtest, aucune stratégie, aucun modèle persistant, aucune API privée et aucune clé API. Les métriques V2.8 restent descriptives, non actionnables, et ne valident aucune stratégie.
