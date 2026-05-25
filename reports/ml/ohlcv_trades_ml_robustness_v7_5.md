# Audit robustesse, walk-forward et falsification - V7.5

## Objectif

V7.5 audite les resultats ML offline V7.4 avec des analyses descriptives et falsifiables sur une fenetre preview de 30 jours.
Cet audit ne transforme pas les scores en decision operationnelle.

## Analyses

- `baseline_delta` compare chaque modele aux baselines majority et random.
- `split_stability` mesure les ecarts train / validation / test.
- `timeframe_stability` compare les resultats entre 1m, 5m, 15m et 1h.
- `walk_forward_stability` resume les metriques descriptives par groupe walk-forward.
- `ohlcv_trades_vs_references_comparison` compare descriptivement V7.4 OHLCV + trades a V6.2 et V5.4 si les references sont disponibles.
- `label_shuffle_falsification` entraine logistic regression et decision tree depth 2 avec labels train melanges, seed 123.
- `feature_leakage_scan` verifie la liste de features V7.4.
- `metric_forbidden_scan` verifie l'absence de metriques de trading interdites.

## Findings

- Robust edge claimed : `False`.
- Validation de strategie declaree : `False`.
- Backtest effectue : `False`.
- Signal actionnable produit : `False`.
- OHLCV+trades valide pour trading : `False`.
- Warnings : `16`.

## Limitations

- V7.5 audite uniquement la robustesse descriptive des baselines ML offline V7.4 sur une fenetre bornee de 30 jours.
- V7.5 compare descriptivement V7.4 a des references si disponibles, mais les fenetres peuvent differer.
- V7.5 ne produit aucun backtest, aucune strategie, aucun signal de trading et aucun ordre.

## Avertissements d'usage

- V7.5 ne valide aucune strategie.
- V7.5 ne valide aucun modele exploitable en trading.
- V7.5 ne valide pas les features OHLCV+trades pour trading.
- V7.5 ne produit aucun backtest.
- V7.5 ne produit aucun signal de trading.
- V7.5 ne produit aucun ordre.
- V7.5 n'autorise aucun paper live.
- V7.5 n'autorise aucun trading reel.
- Les resultats sont descriptifs et falsifiables.
- Les metriques walk-forward ne sont pas un backtest.
- La fenetre de 30 jours est trop courte pour une conclusion robuste.
- Les comparaisons avec V6.2/V5.4 sont non directement comparables si les fenetres different.
- La comparaison OHLCV+trades vs references OHLCV est descriptive, non actionnable.
- Toute interpretation doit rester prudente.
