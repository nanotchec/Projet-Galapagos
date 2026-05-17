# Analyse d'Échec du Régime Récent (V1.17)

La version V1.17 introduit un module d'analyse automatisé des échecs récents (`src/galapagos/research/failure_analysis/`). Ce module a pour but de comprendre pourquoi un signal d'ensemble qui performe bien historiquement (2024, 2025) échoue sur la fenêtre la plus récente (2026).

L'analyse ne tente **pas** de corriger le signal magiquement (ex: sur-optimisation) ni d'activer le LLM. Elle se contente de générer un diagnostic objectif pour guider la prochaine phase de recherche.

## Composants de l'Analyse

1. **Recent Window Failure** (`recent_window.py`) : Vérifie si l'échec est confirmé. Compare la volatilité et les rendements bruts/nets de 2026 par rapport à 2024/2025.
2. **Regime Failure** (`regime_failure.py`) : Analyse la performance croisée par régime de tendance (uptrend, downtrend, range) et de volatilité. Détecte si le marché actuel présente un régime non vu ou si le modèle a "overfitté" un régime spécifique.
3. **Cost Failure** (`cost_failure.py`) : Simule plusieurs scénarios de frais et slippage (x0.5 à x3) pour voir si l'edge existe avant coûts, et s'il est simplement détruit par un marché de "chop" (bruit).
4. **Feature Drift** (`feature_drift.py`) : Mesure la dérive statistique (Z-score du shift de la moyenne, évolution des taux de valeurs manquantes) des features macro et dérivées pour identifier un éventuel changement structurel des données publiques.
5. **Label Diagnostics** (`label_diagnostics.py`) : Vérifie si la cible binaire (`target_up_after_cost`) n'est pas devenue trop difficile à atteindre en 2026 (base rate s'effondrant sous les 30% par exemple).
6. **Horizon Diagnostics** (`horizon_diagnostics.py`) : Compare des horizons alternatifs (1bar, 3bar, 24bar) au standard 6bar/12bar pour voir si un horizon plus court (moins de volatilité inter-bar) ou plus long serait plus robuste.
7. **Data Gap Analysis** (`data_gap_analysis.py`) : Examine les colonnes disponibles pour identifier les manques de données cruciaux (intrabar, liquidations exhaustives, multi-exchange OI).
8. **Recommendation Engine** (`recommendation_engine.py`) : Synthétise les résultats des 7 modules heuristiques et produit une recommandation finale (ex: *B. Add intrabar data first* ou *I. Pause trading-agent path and focus on research*).

## Contraintes
- Le système ne génère **aucun trade**.
- Le système ne valide **pas** le déploiement du Reviewer LLM.
- Les données restent strictement limitées à celles extraites (données publiques Binance/Bybit + Fred).
