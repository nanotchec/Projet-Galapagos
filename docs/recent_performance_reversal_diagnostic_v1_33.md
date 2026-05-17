# Recent Performance Reversal Diagnostic - V1.33

## Contexte
Cette recherche diagnostique vise à comprendre pourquoi le filtre `filter_ev_gt_cost_buffer` a montré une performance négative en 2026 H1 (-0.00382 PnL moyen), alors qu'il était historiquement positif.

## Méthodologie de Diagnostic
L'analyse porte sur 8 dimensions clés :
1. **Calibration** : Stabilité des probabilités calibrées.
2. **EV Proxy** : Alignement entre l'Expected Value prédite et le réalisé.
3. **Payoff** : Décomposition de l'asymétrie gains/pertes.
4. **Cost Drag** : Impact des coûts de transaction (slippage/spread).
5. **Score Drift** : Shift de distribution des scores ML et EV.
6. **Feature Drift** : Drift des features alpha causales.
7. **Regime Shift** : Changement de régime de marché macro.
8. **Concentration** : Analyse de la dispersion des pertes.

## Conclusion Préliminaire
Le diagnostic identifie les drivers principaux de cette inversion de performance afin de guider les recherches futures en V1.34 (re-calibration, modèles conscients du payoff, ou adaptation au régime).

## Contraintes de Sécurité
- Diagnostic uniquement.
- Aucun nouveau filtre de trading.
- Aucun paper live ou trading réel.
