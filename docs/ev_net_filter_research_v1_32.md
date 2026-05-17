# Galapagos V1.32 : Calibrated EV-Net Filter Research

## Objectif
Cette version explore l'utilisation des probabilités calibrées pour construire des filtres d'Expected Value (EV) nette. L'objectif est de déterminer si une approche basée sur l'espérance mathématique (incluant payoffs et coûts) est plus robuste qu'un simple seuil de probabilité brute.

## Méthodologie
1. **Calibration Walk-Forward** : Reconstruction des probabilités via Platt Scaling sur des fenêtres glissantes historiques.
2. **Estimation Causale des Payoffs** : Calcul des gains/pertes moyens uniquement sur les données passées par rapport à chaque signal.
3. **EV Nette** : EV = P(win) * AvgWin + (1 - P(win)) * AvgLoss - Cost_Proxy.
4. **Baselines Random** : Comparaison systématique avec des tirages aléatoires préservant le compte mensuel de signaux.

## Résultats Clés
- **Causalité** : Tous les filtres testés respectent la causalité (pas de look-ahead bias).
- **Ranking** : L'EV calibrée montre une meilleure corrélation avec le PnL réalisé que la probabilité brute.
- **Stabilité** : Les performances observées sont robustes dans la fenêtre 2026 H1.

## Sécurité
- **Classification** : EXPLORATORY_ONLY.
- **Validation** : Aucune stratégie n'est déclarée validée pour le trading.
- **Paper Trading** : Interdit en V1.32.

> [!CAUTION]
> Ce rapport est purement exploratoire. Les résultats ne doivent pas être interprétés comme une validation de performance future.
