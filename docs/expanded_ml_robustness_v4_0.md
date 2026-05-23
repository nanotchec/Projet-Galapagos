# Audit robustesse et falsification - V4.0

## Objectif

V4.0 audite les resultats ML offline V3.9 avec des analyses descriptives et falsifiables sur 90 jours.
Cet audit ne transforme pas les scores en decision operationnelle.

## Correction V4.0.1

V4.0.1 corrige uniquement la completude du ZIP audit-lite V4.0. Le package transmissible inclut maintenant les packages source `src/galapagos/features/` et `src/galapagos/labels/`, requis par les imports des schemas dataset et ML pendant l'audit externe.

Cette correction ne recalcule aucun diagnostic V4.0, ne modifie aucune metrique V4.0, ne modifie aucun score V3.9, ne modifie aucun dataset, aucune feature et aucun label.

## Correction V4.0.2

V4.0.2 corrige uniquement l'exclusion des caches Python dans le ZIP audit-lite V4.0. Le release, l'audit et le smoke refusent explicitement `__pycache__`, `*.pyc` et `*.pyo` a tous les niveaux du package.

Cette correction ne recalcule aucun diagnostic V4.0, ne modifie aucune metrique V4.0, ne modifie aucun score V3.9, ne modifie aucun dataset, aucune feature et aucun label.

## Analyses

- `baseline_delta` compare chaque modele aux baselines majority et random.
- `split_stability` mesure les ecarts train / validation / test.
- `timeframe_stability` compare les resultats entre 1m, 5m, 15m et 1h.
- `label_shuffle_falsification` entraine logistic regression et decision tree depth 2 avec labels train melanges, seed 123.
- `feature_leakage_scan` verifie la liste de features V3.9.
- `metric_forbidden_scan` verifie l'absence de metriques de trading interdites.

## Findings

- robust_edge_claimed : `False`.
- validation de strategie declaree : `False`.
- backtest_performed : `False`.
- actionable_signal_produced : `False`.
- warnings : `8`.

## Limitations

- V4.0 audite uniquement la robustesse descriptive des baselines ML offline V3.9 sur une fenetre de 90 jours.
- V4.0 ne produit aucun backtest, aucune strategie, aucun signal de trading et aucun ordre.

## Non-usage warnings

- V4.0 ne valide aucune strategie.
- V4.0 ne valide aucun modele exploitable en trading.
- V4.0 ne produit aucun backtest.
- V4.0 ne produit aucun signal de trading.
- V4.0 ne produit aucun ordre.
- V4.0 n'autorise aucun paper live.
- V4.0 n'autorise aucun trading reel.
- Les resultats sont descriptifs et falsifiables.
- Toute interpretation doit rester prudente.
