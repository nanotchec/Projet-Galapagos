# Audit robustesse, walk-forward et falsification - V8.0

## Objectif

V8.0 audite les resultats ML offline V8.0 avec des analyses descriptives et falsifiables sur une fenetre preview de 90 jours.
Cet audit ne transforme pas les scores en decision operationnelle.

## Analyses

- `baseline_delta` compare chaque modele aux baselines majority et random.
- `split_stability` mesure les ecarts train / validation / test.
- `timeframe_stability` compare les resultats entre 1m, 5m, 15m et 1h.
- `walk_forward_stability` resume les metriques descriptives par groupe walk-forward.
- `ohlcv_trades_90d_vs_references_comparison` compare descriptivement V8.0 OHLCV + trades a V7.4, V6.2 et V5.4 si les references sont disponibles.
- `label_shuffle_falsification` entraine logistic regression et decision tree depth 2 avec labels train melanges, seed 123.
- `feature_leakage_scan` verifie la liste de features V8.0.
- `metric_forbidden_scan` verifie l'absence de metriques de trading interdites.

## Findings

- Robust edge claimed : `False`.
- Validation de strategie declaree : `False`.
- Backtest effectue : `False`.
- Signal actionnable produit : `False`.
- OHLCV+trades valide pour trading : `False`.
- Warnings : `8`.

## Limitations

- V8.0 entraine uniquement des baselines ML offline simples sur le dataset OHLCV + aggTrades 90 jours V7.9.
- V8.0 produit une robustesse descriptive et une falsification offline, sans backtest, sans strategie, sans signal de trading et sans ordre.
- La fenetre de 90 jours reste insuffisante pour conclure a une robustesse statistique forte.

## Avertissements d'usage

- V8.0 ne valide aucune strategie.
- V8.0 ne valide aucun modele exploitable en trading.
- V8.0 ne valide pas les features OHLCV+trades pour trading.
- V8.0 ne produit aucun backtest.
- V8.0 ne produit aucun signal de trading.
- V8.0 ne produit aucun ordre.
- V8.0 n'autorise aucun paper live.
- V8.0 n'autorise aucun trading reel.
- Les resultats sont descriptifs et falsifiables.
- Les metriques walk-forward ne sont pas un backtest.
- La fenetre de 90 jours est trop courte pour une conclusion robuste.
- Les comparaisons avec V6.2/V5.4 sont non directement comparables si les fenetres different.
- La comparaison OHLCV+trades vs references OHLCV est descriptive, non actionnable.
- Toute interpretation doit rester prudente.
