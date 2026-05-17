# Robust Signal Selection Validation - Galapagos V1.25

## Objectif
Cette version vise à valider la robustesse du filtre `low_frequency_strict_score` identifié en V1.24.1. 
L'objectif n'est pas d'optimiser la performance, mais de vérifier si l'edge observé est statistiquement significatif et stable dans le temps.

## Méthodologie de Validation
Nous avons appliqué plusieurs tests de robustesse :
1. **Robustesse Temporelle** : Analyse par années (2024, 2025, 2026 YTD) et demi-années.
2. **Same-Frequency Random** : Comparaison avec une baseline aléatoire qui respecte la même fréquence mensuelle de trading.
3. **Sensibilité aux Coûts** : Mesure de la dégradation de la performance de 0.0% à 0.5% de frais par trade.
4. **Tests Placebo** : Shuffling des timestamps pour détecter des corrélations fallacieuses.
5. **Audit d'Overfit** : Évaluation du risque lié au multiple testing (26 filtres testés initialement).

## Résultats (Synthèse)
Les résultats détaillés sont disponibles dans les rapports suivants :
- `reports/research/signal_selection_temporal_robustness_v1_25.json`
- `reports/research/signal_selection_same_frequency_random_v1_25.json`
- `reports/research/signal_selection_cost_sensitivity_v1_25.json`
- `reports/research/signal_selection_placebo_tests_v1_25.json`

## Sécurité
- Aucun ordre réel.
- Reviewer LLM désactivé.
- Holdout non exécuté.

## Correction V1.25.1 (Robustesse et Honnêteté Méthodologique)
La version V1.25.1 corrige des conclusions trop optimistes de la V1.25 :
- **Rétrogradation du Verdict** : Le verdict passe de `ROBUST_SIGNAL_SELECTION_CANDIDATE` à `PROMISING_BUT_REQUIRES_OUT_OF_SAMPLE_CONFIRMATION` en raison de la concentration de la performance (61% sur 10 trades) et du risque de multiple testing élevé (26 règles testées).
- **Précision Aléatoire** : La baseline est désormais documentée comme `monthly-count-preserving random`, ce qui est une condition nécessaire mais non suffisante pour la robustesse.
- **Audit des Coûts** : Ajout d'une vérification de cohérence Gross/Net/Cost pour éviter des biais de reconstruction.
- **Placebo Incomplet** : Les tests placebo sont marqués comme partiels car ils ne réappliquent pas la logique de filtrage sur les données bruitées.
- **Reviewer** : Maintenu désactivé.

## Étape Suivante (V1.26)
Un protocole de validation pré-enregistré a été établi dans la version [V1.26](preregistered_signal_validation_v1_26.md) pour figer les critères de succès futurs.
