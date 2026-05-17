# ML Baseline Research Lab - V1.15

## Objectif

Tester si les features disponibles (OHLCV + macro + derives + alpha scores)
contiennent un signal predictif exploitable, avant d'investir dans un LLM
reviewer complexe.

## Pourquoi ML avant LLM reviewer

Le LLM (GPT) est couteux, non deterministe et difficile a evaluer
statistiquement. Un modele ML simple (logistic regression, random forest,
gradient boosting) donne une borne superieure du signal quantitatif
disponible dans les features. Si un modele simple ne bat pas le hasard,
un LLM ne fera pas mieux sur les memes features.

## Pourquoi des modeles simples

Les modeles complexes (deep learning, AutoML, transformers) memorisent
facilement les patterns historiques sans generaliser. Un modele simple
avec walk-forward strict est plus fiable pour detecter un vrai signal.

## Pourquoi les predictions ne prouvent pas une strategie rentable

Un modele qui bat le hasard en accuracy ne garantit pas un PnL positif
apres couts de transaction, slippage et risk management. La section
cost-adjusted metrics tente d'estimer cet ecart.

## Holdout verrouille

Le holdout trading existant (derniere fenetre des backtests) n'est PAS
utilise pour le ML. Les fenêtres walk-forward utilisent des splits
chronologiques independants : train 2022-2023, validation 2024,
validation 2025, recent 2026.

## Integration des couts

Le target `target_up_after_cost_6bar` inclut le seuil de cout (0.3%)
dans la definition du label. Un modele qui predit « up after cost »
doit battre le base rate pour etre interessant.

## Structure du package

```
src/galapagos/research/ml/
  __init__.py
  dataset.py      - chargement et preparation
  targets.py      - construction des labels ML
  feature_sets.py - definition des features, exclusion future/target
  models.py       - modeles simples, fallback si sklearn absent
  walk_forward.py - evaluation walk-forward stricte
  metrics.py      - metriques classification/regression/trading
  calibration.py  - analyse de calibration des probabilites
  feature_importance.py - importance par feature et par groupe
  report.py       - generation de rapports et verdicts
```

## Securite

- Aucun ordre reel.
- Aucun Codex CLI.
- Aucun holdout trading.
- Aucun levier.
- Research-only.
