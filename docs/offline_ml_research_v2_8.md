# V2.8 — First Offline ML Research Baselines

## Correction V2.8.1

V2.8.1 conserve le scope ML offline V2.8, sans ajouter de modèle ni de métrique.

La correction rend les scripts release/audit autonomes dans le ZIP clean et durcit le garde-fou contre les artefacts interdits :

- aucun fichier sous `reports/backtests/` dans le ZIP clean ;
- aucun modèle persistant `.pkl`, `.pickle`, `.joblib`, `.sav`, `.model`, `.ckpt`, `.pt`, `.pth` ou `.onnx` ;
- sous `data/gold/ml/offline_research/`, seuls les fichiers `ml-scores-2024-01-15.parquet` sont autorisés ;
- aucune stratégie, aucun ordre, aucun backtest et aucun artefact d'exécution.

V2.8.1 reste `pending_external_audit`.

## Correction V2.8.2

V2.8.2 conserve exactement le même scope ML offline que V2.8/V2.8.1.

La correction finalise uniquement le runtime du fichier complet `tests/validation/test_offline_ml_research_v2_8_validator.py` :

- les tests d'artefacts interdits utilisent directement `_find_forbidden_artifacts()` ;
- les tests JSON, safety et métriques restent ciblés sur les helpers de validation ;
- le validateur de production `validate_offline_ml_research_v2_8()` n'est pas relâché ;
- aucun modèle, backtest, stratégie, ordre ou artefact d'exécution n'est ajouté.

V2.8.2 reste `pending_external_audit`.

## Correction V2.8.4

V2.8.4 conserve le même scope ML offline et ne modifie pas les modèles, les features autorisées, la cible ou les métriques.

La correction est strictement runtime/smoke :

- les tests de colonnes score utilisent un helper pur `_validate_score_frame_schema_only()` quand une validation physique complète n'est pas nécessaire ;
- un seul test de colonne score conserve une mutation Parquet physique ;
- le smoke V2.8.4 appelle directement les fonctions de validation dans le process du smoke et ne capture aucun gros JSON ;
- aucun backtest, aucune stratégie, aucun ordre, aucun modèle persistant et aucun artefact d'exécution n'est ajouté.

V2.8.4 reste `pending_external_audit`.

## Objectif

V2.8 construit un laboratoire ML offline borné à partir du dataset supervisé V2.7 validé.

La chaîne cible est :

`dataset supervisé offline V2.7 -> entraînement ML offline simple -> scores de recherche -> métriques descriptives -> manifest -> rapport -> validateur`

V2.8 ne transforme pas les prédictions en décision, signal, stratégie, ordre ou backtest.

## Entrées

Les seules entrées autorisées sont les datasets supervisés V2.7 et les split files V2.7 pour :

- `1m`
- `5m`
- `15m`
- `1h`

Avant entraînement, le script V2.8 relance les validateurs V2.3, V2.4, V2.5, V2.6 et V2.7.

## Cible

- Target unique : `up_down_flat_h1`
- Lignes exclues : `label_valid_h1 = false`
- Lignes exclues : `warmup_row = true`

V2.8 n'utilise pas `h3` ou `h5` comme cible.

## Features autorisées

Les features sont limitées aux colonnes causales V2.5 listées dans `ALLOWED_FEATURE_COLUMNS_V2_8`.

Sont explicitement interdits comme features :

- `future_*`
- `label_*`
- `direction_*`
- `up_down_flat_*`
- `split`
- `warmup_row`
- `tail_row`
- toute colonne assimilable à signal, stratégie, ordre, PnL ou backtest.

## Modèles autorisés

- `majority_class_baseline`
- `random_seeded_baseline`
- `logistic_regression`
- `decision_tree_depth_2`

Aucune recherche d'hyperparamètres, aucun modèle complexe et aucun modèle exploitable en trading ne sont ajoutés.

## Sorties

Les scores de recherche sont écrits sous :

`data/gold/ml/offline_research/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=<tf>/year=2024/month=01/ml-scores-2024-01-15.parquet`

Les rapports sont écrits sous :

- `reports/manifests/offline_ml_research_v2_8_manifest.json`
- `reports/ml/offline_ml_research_v2_8.json`
- `reports/ml/offline_ml_research_v2_8.md`
- `reports/ml/offline_research_scores_v2_8.json`
- `reports/ml/offline_research_scores_v2_8.md`

Les colonnes de scores utilisent des noms de recherche (`research_predicted_class`, `research_probability_*`) et jamais des noms de signal ou d'ordre.

## Métriques

V2.8 calcule uniquement des métriques de classification descriptives :

- accuracy
- balanced accuracy
- macro F1
- precision/recall par classe
- matrice de confusion
- distributions de classes

V2.8 ne calcule aucun PnL, Sharpe, drawdown, equity curve, profit factor ou métrique de trading.

## Sécurité

- V2.8 ne valide aucune stratégie.
- V2.8 ne produit aucun backtest.
- V2.8 ne produit aucun signal de trading.
- V2.8 ne produit aucun ordre.
- V2.8 n'autorise aucun paper live.
- V2.8 n'autorise aucun trading réel.
- Les métriques sont descriptives et non actionnables.
- V2.8 reste `pending_external_audit`.
