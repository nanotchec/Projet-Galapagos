# Audit robustesse, walk-forward et falsification - V8.6

## Objectif

V8.6 audite les resultats ML offline V8.6 avec des analyses descriptives et falsifiables sur une fenetre preview de 1 an.
Cet audit ne transforme pas les scores en decision operationnelle.

## Analyses

- `baseline_delta` compare chaque modele aux baselines majority et random.
- `split_stability` mesure les ecarts train / validation / test.
- `timeframe_stability` compare les resultats entre 1m, 5m, 15m et 1h.
- `walk_forward_stability` resume les metriques descriptives par groupe walk-forward.
- `ohlcv_trades_1y_vs_references_comparison` compare descriptivement V8.6 OHLCV + trades a V7.4, V6.2 et V5.4 si les references sont disponibles.
- `label_shuffle_falsification` entraine logistic regression et decision tree depth 2 avec labels train melanges, seed 123.
- `feature_leakage_scan` verifie la liste de features V8.6.
- `metric_forbidden_scan` verifie l'absence de metriques de trading interdites.

## Findings

- Robust edge claimed : `False`.
- Validation de strategie declaree : `False`.
- Backtest effectue : `False`.
- Signal actionnable produit : `False`.
- OHLCV+trades valide pour trading : `False`.
- Warnings : `16`.

## Limitations

- V8.6 audite uniquement la robustesse descriptive des baselines ML offline V8.5 sur la fenetre OHLCV + aggTrades d'environ 1 an.
- V8.6 compare descriptivement V8.5 a des references si disponibles, mais certaines fenetres peuvent differer.
- V8.6 ne produit aucun backtest, aucune strategie, aucun signal de trading et aucun ordre.

## Avertissements d'usage

- V8.6 ne valide aucune strategie.
- V8.6 ne valide aucun modele exploitable en trading.
- V8.6 ne valide pas les features OHLCV+trades pour trading.
- V8.6 ne produit aucun backtest.
- V8.6 ne produit aucun signal de trading.
- V8.6 ne produit aucun ordre.
- V8.6 n'autorise aucun paper live.
- V8.6 n'autorise aucun trading reel.
- Les resultats sont descriptifs et falsifiables.
- Les metriques walk-forward ne sont pas un backtest.
- La fenetre de 1 an est trop courte pour une conclusion robuste.
- Les comparaisons avec V6.2/V5.4 sont non directement comparables si les fenetres different.
- La comparaison OHLCV+trades vs references OHLCV est descriptive, non actionnable.
- Toute interpretation doit rester prudente.
