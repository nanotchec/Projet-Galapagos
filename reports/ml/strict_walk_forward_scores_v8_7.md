# Validation walk-forward offline stricte - V8.7

## Objectif

V8.7 applique une validation walk-forward offline stricte sur le dataset V8.4 OHLCV + aggTrades 1 an.
Les modeles sont des baselines de recherche par fold et les scores `research_*` restent non actionnables.

## Politique walk-forward

- Grouping : `calendar_month`.
- Train initial : `6` mois.
- Validation : `1` mois.
- Test : `1` mois.
- Step : `1` mois.
- Purge / embargo : `5` / `5` barres.
- Shuffle : `False`.

## Outputs

- `1m` : `5` folds, scores `8805440` lignes.
- `5m` : `5` folds, scores `1759808` lignes.
- `15m` : `5` folds, scores `585536` lignes.
- `1h` : `5` folds, scores `145184` lignes.

## Controles

- Cible unique : `up_down_flat_h1`.
- Les lignes warmup, labels invalides, purged et embargoed sont exclues des entrainements et evaluations.
- Les colonnes futures, labels, target, split, walk-forward et fold ne sont jamais utilisees comme features.
- Les metriques sont descriptives et non actionnables.
- La validation walk-forward offline n'est pas un backtest.
- Les comparaisons avec V8.5 sont descriptives.
- V8.7 ne valide aucune strategie.
- V8.7 ne produit aucun backtest.
- V8.7 ne produit aucun signal de trading.
- V8.7 ne produit aucun ordre.
- V8.7 n'autorise aucun paper live.
- V8.7 n'autorise aucun trading reel.
- Aucune metrique de trading interdite ou mesure d'execution n'est calculee.

## Limitations

- V8.7 produit une validation walk-forward offline stricte des baselines ML sur le dataset OHLCV + aggTrades 1 an V8.4.
- V8.7 ne produit aucun backtest, aucune strategie, aucun signal de trading et aucun ordre.
- Les resultats restent descriptifs et ne valident pas une exploitation trading.
