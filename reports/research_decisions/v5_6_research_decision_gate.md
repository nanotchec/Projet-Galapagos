# V5.6 - Max Historical Research Decision Gate

## 1. Executive summary

Verdict research : **mitige et non concluant**.

Les resultats ML OHLCV-only V5.4/V5.5 montrent un interet descriptif faible, surtout pour `logistic_regression` sur `5m` et `15m`. Cet interet ne suffit pas a conclure a une robustesse exploitable : les performances restent sensibles au timeframe, partiellement instables par groupes walk-forward, et la falsification label shuffle signale encore des zones fragiles.

Ce rapport ne contient aucune conclusion trading.

## 2. Resume des entrees analysees

- V5.4 : baselines ML offline max historical.
- V5.5 : robustesse, falsification et walk-forward descriptif.
- Fenetre : `2023-03-25` -> `2026-05-23`.
- Total jours : `1156`.
- Modeles : `majority_class_baseline`, `random_seeded_baseline`, `logistic_regression`, `decision_tree_depth_2`.
- Target : `up_down_flat_h1`.
- Timeframes : `1m`, `5m`, `15m`, `1h`.
- Walk-forward : groupes calendaires trimestriels descriptifs.

## 3. Comparaison aux baselines

`logistic_regression` bat les baselines sur plusieurs coupes descriptives, surtout en macro F1 sur `5m` et `15m`. Sur test, le gain macro F1 face a `majority_class_baseline` est de `+0.2116` sur `5m` et `+0.2187` sur `15m`. Face a `random_seeded_baseline`, le gain est plus modeste : `+0.0802` sur `5m`, `+0.0690` sur `15m`, et negatif sur `1h` avec `-0.0268`.

Verdict `logistic_regression` : **resultat mitige**.

`decision_tree_depth_2` ne bat pas les baselines de facon fiable. Sur `1m`, il revient exactement au niveau macro F1 de `majority_class_baseline`; sur `15m` et `1h`, il reste sous `random_seeded_baseline` en macro F1 test.

Verdict `decision_tree_depth_2` : **ne bat pas les baselines de facon robuste**.

## 4. Stabilite train / validation / test

V5.5 ne remonte pas d'avertissement de surapprentissage massif selon le seuil de gap `0.10`. Les ecarts train / validation / test restent contenus pour les modeles appris.

Cette stabilite relative est utile, mais elle ne suffit pas a valider une piste robuste : le resultat depend encore du timeframe et des groupes temporels.

## 5. Stabilite par timeframe

Les resultats ne sont pas pleinement stables entre `1m`, `5m`, `15m` et `1h`.

- `1m` affiche la meilleure accuracy pour les modeles, mais cette lecture est fortement influencee par la distribution de classes.
- `5m` et `15m` sont les timeframes les plus interessants en macro F1 pour `logistic_regression`.
- `1h` reste fragile : `logistic_regression` ne bat pas `random_seeded_baseline` en macro F1 test.

V5.5 signale des avertissements de concentration timeframe pour tous les modeles. Aucun modele ne doit etre considere stable tous timeframes.

## 6. Stabilite walk-forward

Les groupes walk-forward sont descriptifs et ne constituent pas un backtest.

Pour les modeles appris, aucun groupe faible n'est remonte par le scan V5.5. En revanche, des groupes instables apparaissent :

- `logistic_regression` : 2 groupes instables sur `1m`, 1 groupe instable sur `5m`.
- `decision_tree_depth_2` : 2 groupes instables sur `1m`, 1 groupe instable sur `5m`.

Les resultats semblent donc partiellement concentres sur certaines periodes, surtout aux timeframes courts.

## 7. Label shuffle falsification

Le label shuffle degrade generalement les performances, notamment sur `5m` et `15m`. Cela indique que certains resultats de `logistic_regression` ne sont pas purement aleatoires.

L'alerte reste forte pour `decision_tree_depth_2` : V5.5 remonte `no_clear_edge_vs_shuffled_labels` sur `1m` validation/test et sur `1h` test. Quand les labels train shuffles ne detruisent pas clairement la performance, le resultat ne peut pas etre interprete comme robuste.

## 8. Fuites / anti-leakage

Les scans V5.5 ne detectent pas de fuite de features :

- aucune feature `future_*` ;
- aucune feature `label_*` ;
- aucune feature `direction_*` ;
- aucune feature `up_down_flat_*` ;
- aucune feature `split` ou `walk_forward_group` ;
- aucune colonne de signal, ordre, strategie, PnL ou backtest.

Les scans de metriques interdites ne remontent pas d'anomalie.

## 9. Limites restantes malgre max historical OHLCV

- Les donnees restent OHLCV-only.
- Un seul actif est couvert : BTCUSDT spot.
- Les trades publics historiques ne sont pas encore integres.
- Le funding, l'open interest et l'order book ne sont pas couverts.
- Aucun cout, slippage ou effet d'execution n'est modelise.
- Aucun backtest n'est produit.
- Aucune vraie execution n'est simulee ou activee.
- La fenetre continue maximum validee ne couvre pas necessairement tous les fragments historiques segmentes de BTCUSDT.

## 10. Decision de direction

Option principale recommandee : **A. Ajouter les trades publics historiques.**

Raison : apres avoir pousse OHLCV-only jusqu'a l'historique continu maximum, le signal descriptif reste faible et instable. La prochaine source d'information publique raisonnable est le flux de trades historiques, qui peut apporter de la microstructure sans passer a une source privee.

Option secondaire recommandee : **D. Preparer une validation walk-forward offline plus stricte.**

Raison : avant toute discussion de backtest research borne, il faut renforcer l'evaluation offline et isoler les effets temporels.

## 11. Roadmap proposee

- V6.0 : decouverte et ingestion data-only des trades publics historiques BTCUSDT.
- V6.1 : qualite et agregations causales des trades publics, sans labels ni ML.
- V6.2 : assemblage offline OHLCV + trades publics avec features causales separees des labels.
- V6.3 : baselines ML offline et falsification sur dataset OHLCV + trades.
- V6.4 : decision gate walk-forward offline plus stricte avant toute discussion de backtest research borne.

## 12. Interdits maintenus

- Pas de trading.
- Pas de paper live.
- Pas d'ordre.
- Pas de backtest validant une strategie.
- Pas de claim de rentabilite.

V5.6 ne valide aucune strategie, ne valide aucun modele exploitable en trading, ne produit aucun signal de trading et ne produit aucun ordre.
