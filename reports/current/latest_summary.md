# Résumé courant — V2.8.3 candidate

La dernière version validée est **V2.7.2**. La version candidate est **V2.8.3**, en statut `pending_external_audit`.

V2.8 a ajouté un laboratoire ML offline borné sur les datasets supervisés V2.7 validés. V2.8.1 a corrigé le packaging release/audit et le garde-fou d'artefacts interdits. V2.8.2 a réduit le runtime du validateur. V2.8.3 finalise le runtime des tests de mutation score et rend le smoke ZIP robuste sans capture de gros JSON.

Le refus strict V2.8.2 portait sur deux points : certains tests de colonnes score utilisaient encore une validation physique trop lourde, et le smoke V2.8.2 capturait la sortie JSON complète du validateur ML.

Le système reste research/offline : aucun trading réel, aucun paper live, aucun ordre, aucun signal de trading, aucun backtest, aucune stratégie, aucun modèle persistant, aucune API privée et aucune clé API. Les métriques V2.8 restent descriptives, non actionnables, et ne valident aucune stratégie.
