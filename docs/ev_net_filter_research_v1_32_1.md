# Galapagos V1.32.1 : EV-Net Causality / Baseline / Warmup Fix

## Objectif
Cette version corrective assainit la recherche EV-net en éliminant les failles de méthodologie identifiées dans la V1.32. L'accent est mis sur la causalité stricte des paramètres (payoffs, quantiles) et sur la rigueur de la comparaison statistique.

## Corrections Majeures
1. **Payoffs Sans Défaut** : Les valeurs arbitraires (2% / -1%) ont été supprimées. Un warmup de 100 observations valides est requis avant tout calcul d'EV.
2. **Quantiles Causaux** : Le filtrage par quantile utilise désormais une fenêtre expanding (`shift(1)`), garantissant qu'aucune information future n'est utilisée.
3. **Random Baseline Rigoureuse** : La comparaison se fait par rapport à un tirage aléatoire "monthly-count preserving", beaucoup plus difficile à battre qu'un tirage global simple.
4. **Tracking d'Activité** : Les filtres sont audités sur leur capacité à générer des signaux dans toutes les fenêtres temporelles, particulièrement en **2026 H1**.

## Résultats V1.32.1
- Les filtres qui semblaient "prometteurs" en V1.32 perdent leur éligibilité s'ils sont inactifs récemment ou s'ils reposaient sur des quantiles non-causaux.
- Le verdict scientifique est ajusté pour refléter la réalité des données sans les biais méthodologiques précédents.

## Sécurité
- **Classification** : EXPLORATORY_ONLY.
- **Audit Causal** : Re-durci pour détecter les violations de warmup et de quantile.
- **Pas d'ordre réel** : Toujours en vigueur.

> [!IMPORTANT]
> Cette version confirme que la rigueur méthodologique est prioritaire sur la "performance" affichée. Les résultats sont plus dégradés mais plus honnêtes scientifiquement.
