# Audit robustesse, walk-forward et falsification - V6.3

## Objectif

V6.3 audite les resultats ML offline V6.2 avec des analyses descriptives et falsifiables sur la fenetre historique continue.
Cet audit ne transforme pas les scores en decision operationnelle.

## Analyses

- `baseline_delta` compare chaque modele aux baselines majority et random.
- `split_stability` mesure les ecarts train / validation / test.
- `timeframe_stability` compare les resultats entre 1m, 5m, 15m et 1h.
- `walk_forward_stability` resume les metriques descriptives par groupe walk-forward.
- `advanced_vs_simple_comparison` compare descriptivement V6.2 advanced OHLCV a V5.4 simple OHLCV si la reference est disponible.
- `label_shuffle_falsification` entraine logistic regression et decision tree depth 2 avec labels train melanges, seed 123.
- `feature_leakage_scan` verifie la liste de features V6.2 ; `macd_like_signal` reste autorisee comme feature technique.
- `metric_forbidden_scan` verifie l'absence de metriques de trading interdites.

## Findings

- Robust edge claimed : `False`.
- Validation de strategie declaree : `False`.
- Backtest effectue : `False`.
- Signal actionnable produit : `False`.
- Advanced features validees pour trading : `False`.
- Warnings : `7`.

## Limitations

- V6.3 audite uniquement la robustesse descriptive des baselines ML offline V6.2 avec advanced OHLCV features.
- V6.3 compare descriptivement V6.2 a V5.4 si disponible, sans produire aucun backtest, aucune strategie, aucun signal de trading et aucun ordre.

## Avertissements d'usage

- V6.3 ne valide aucune strategie.
- V6.3 ne valide aucun modele exploitable en trading.
- V6.3 ne valide pas les advanced features pour trading.
- V6.3 ne produit aucun backtest.
- V6.3 ne produit aucun signal de trading.
- V6.3 ne produit aucun ordre.
- V6.3 n'autorise aucun paper live.
- V6.3 n'autorise aucun trading reel.
- Les resultats sont descriptifs et falsifiables.
- Les metriques walk-forward ne sont pas un backtest.
- La comparaison advanced vs simple OHLCV est descriptive, non actionnable.
- Toute interpretation doit rester prudente.
