# Recent & Bull-Regime Diagnostic - V1.29.4

## Objectif du diagnostic
Comprendre la dégradation récente (2026 H1) du filtre exploratoire `prob_ge_0.65` et sa dépendance exclusive au régime de marché haussier.

## Méthodologie du diagnostic
L'analyse porte sur plusieurs axes :
1. **Robustesse Temporelle** : Comparaison des métriques clés (PnL, Win Rate, Profit Factor) par semestre.
2. **Dépendance Régime** : Audit de la concentration des signaux sur le proxy `bull_strength`.
3. **Calibration des Probabilités** : Vérification de la fiabilité des scores hauts dans le temps.
4. **Dérive de Distribution** : Analyse de la fréquence et de l'intensité des signaux récents.
5. **Impact des Coûts** : Estimation de l'absorption de l'edge brut par les frais de transaction.
6. **Distribution des Outcomes** : Analyse des queues de distribution (queues gauches/droites).

## Résultats attendus
Identifier si l'edge est structurellement brisé ou simplement temporairement inadapté au régime de marché actuel.

## Recommandations prioritaires
- Ne pas passer à la V1.30 si la dégradation est confirmée.
- Explorer de nouvelles features alpha ou des filtres "regime-aware".
