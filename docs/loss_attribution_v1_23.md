# Loss Attribution - Galapagos V1.23

## Objectif
L'objectif de cette version est d'identifier les causes profondes de la non-rentabilité des politiques de trading actuelles sur le dataset intrabar continu.
La version **V1.23.1** apporte une correction majeure en effectuant l'attribution des pertes **par policy** (`fixed_percent`, `atr_proxy`, `horizon_only`) au lieu de se focaliser uniquement sur la meilleure d'entre elles.

## Méthodologie
Nous avons décomposé la performance de chaque politique en plusieurs dimensions :
1. **Attribution des Coûts** : Impact des frais et du slippage sur le PnL brut (par policy).
2. **Qualité d'Entrée (MAE/MFE)** : Analyse de l'asymétrie favorable/défavorable après l'entrée.
3. **Analyse des Sorties** : Répartition des raisons de sortie (TP, SL, Horizon).
4. **Régimes de Marché** : Performance en fonction de la tendance et de la volatilité.
5. **Calibration ML** : Relation entre la probabilité prédite et le résultat net.
6. **Risque de Queue** : Concentration des pertes sur les trades extrêmes (avec nomenclature corrigée).

## Résultats de la V1.23
L'analyse approfondie de la politique `horizon_only` (la plus performante à 53.2% de win rate brut) révèle que :
1. **Driver Principal** : Les **coûts de transaction** (`costs_dominate`) sont la cause primaire des pertes. Le PnL brut est légèrement positif mais insuffisant pour couvrir les frais/slippage.
2. **Edge Directionnel** : Le signal ML montre un edge brut, mais il est trop faible (`NO_INTRATRADE_EDGE`) pour compenser les frictions de marché.
3. **Calibration** : Même les trades à haute confiance restent négatifs après coûts (`HIGH_CONFIDENCE_STILL_NEGATIVE`).
4. **Sorties** : La politique de sortie n'est pas le problème majeur (`EXIT_POLICY_NOT_PRIMARY_DRIVER`).
5. **Concentration** : Les pertes sont diffuses et non concentrées sur quelques trades (`LOSSES_DIFFUSE`).

## Recommandation Scientifique
**Réduire la fréquence de trading ou cibler des configurations à plus haute volatilité** pour distancer les coûts.
- Ne pas activer le Reviewer LLM tant que l'edge brut n'est pas renforcé.
- Ne pas exécuter le Holdout.
- Améliorer la sélection des signaux (feature engineering / target tuning) avant toute optimisation des sorties.

## Suite V1.24
La V1.24 prolonge cette conclusion sans modifier les sorties : elle teste des filtres de selection cost-aware sur les candidats existants.
L'objectif est de verifier si une reduction disciplinee de frequence peut ameliorer l'esperance nette apres couts.
Les filtres restent research-only et sont compares a une baseline random same-count.

## Sécurité et Conformité
- **Exécution Réelle** : Aucun ordre réel.
- **Holdout** : Non exécuté.
- **Codex CLI** : Non appelé.
- **Levier** : Non implémenté.
- **Verdict Final** : Recherche Complète - Non Rentable.
