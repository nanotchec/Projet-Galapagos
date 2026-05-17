# Recent & Bull-Regime Diagnostic - V1.29.6 (Leakage Fix)

## Objectif du diagnostic
Éliminer toute fuite de données futures dans la frame de sélection utilisée pour le diagnostic. La version V1.29.5 contenait par erreur des colonnes d'outcome (`forward_return`) dans sa frame de sélection, ce qui est méthodologiquement interdit.

## Changements V1.29.6
1. **Séparation stricte des frames** : Le `data_loader` exclut maintenant explicitement tout mot-clé lié aux outcomes (`forward_return`, `net_pnl`, etc.) de la `selection_frame`.
2. **Durcissement du Rebuilder** : Le rebuilder échoue systématiquement si une colonne interdite est détectée dans la frame de sélection.
3. **Validateur renforcé** : Le script de cohérence vérifie l'absence de fuite et rejette tout rapport non conforme.

## Résultats attendus
Un diagnostic causalement irréprochable confirmant la dégradation de l'alpha en 2026 H1 sur une base de données propre.

## Statut d'Intégrité
- **Selection Leakage** : CLEAN.
- **Verdict** : RECENT_DEGRADATION_CONFIRMED_ON_CLEAN_SELECTION_FRAME.
