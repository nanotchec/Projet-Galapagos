# V9.11 - Label Failure Analysis & Redesign Plan

## Resume executif
- Decision V9.11 : `label_redesign_plan_horizon_extension`.
- Recommandation : V9.12 - Label Redesign Candidate: horizon extension + event-based diagnostic, sans ML ni backtest dans la phase de design.
- Aucun backtest n'est justifie. Aucun trading, paper live, ordre, strategie ou signal actionnable.

## Recap decisions
- `v9_4` : `backtest_not_justified_refine_labels` - Aucun backtest; raffinement des labels demande.
- `v9_5` : `label_redesign_candidate_volatility_normalized` - Candidat volatility-normalized recommande pour une factory future.
- `v9_10` : `backtest_not_justified_refine_labels_again` - Les labels volatility-normalized restent trop proches des labels melanges.

## Diagnostic d'echec

- `H1` horizon h1 trop bruite : `likely`. Tester un horizon plus long avant tout backtest.
- `H2` features actuelles insuffisantes pour predire ce label : `likely`. Coupler le redesign label a un audit feature si le label reste non falsifiable.
- `H3` classe FLAT encore mal definie : `possible`. Comparer une cible binaire et une cible event-based.
- `H4` seuil k=0.5 trop permissif : `likely`. Tester k plus strict ou barriere de mouvement significatif.
- `H5` labels multi-classes trop difficiles : `possible`. Evaluer un design binaire directionnel comme diagnostic, sans signal trading.
- `H6` fenetre 2023-2024 pas assez robuste : `possible`. Etendre les donnees uniquement apres un label mieux defini.
- `H7` probleme de regime de marche : `possible`. Ajouter une analyse de regime descriptive dans la prochaine iteration.
- `H8` signal absent dans OHLCV+trades agreges actuels : `plausible`. Prevoir un critere d'arret si un redesign label plus strict reste non falsifiable.

## Designs futurs compares

- `longer_horizon_labels` : priorite `high`, decision `accept_for_future_experiment`.
- `multi_horizon_labels` : priorite `medium`, decision `review_before_experiment`.
- `binary_directional_without_flat` : priorite `low`, decision `review_before_experiment`.
- `quantile_based_labels` : priorite `medium`, decision `review_before_experiment`.
- `event_based_labels` : priorite `high`, decision `accept_for_future_experiment`.
- `volnorm_different_k` : priorite `medium`, decision `review_before_experiment`.
- `significant_move_with_descriptive_cost` : priorite `medium`, decision `review_before_experiment`.
- `feature_or_data_extension_first` : priorite `medium`, decision `review_before_experiment`.

## Garde-fous
- V9.11 ne cree aucun nouveau label full.
- V9.11 ne lance aucun ML, aucun walk-forward et aucun backtest.
- V9.11 ne produit aucun signal actionnable, aucune strategie, aucun ordre et aucun trading reel.
- Les prochains ZIP doivent exclure `Icon`, `Icon\r`, `.DS_Store`, caches, secrets, modeles persistants, sidecars SHA256 et empreintes ZIP.
