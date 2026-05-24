# Advanced OHLCV Research Decision Gate - V6.4

## 1. Executive summary

Verdict : advanced OHLCV est interessant mais non concluant. Les resultats V6.2/V6.3 montrent des signaux descriptifs, surtout pour `logistic_regression`, mais ils ne sont pas assez stables pour justifier un backtest research. V6.4 ne tire aucune conclusion trading.

Advanced OHLCV ameliore V5.4 dans `20` comparaisons descriptives, simple OHLCV reste meilleur dans `11` comparaisons, et `17` comparaisons restent mitigees ou non conclusives. La consistency advanced est `0.416666666667`. Conclusion : l amelioration n est pas claire et stable.

## 2. Resume des entrees analysees

- V6.2 : ML offline advanced OHLCV, scores `research_*`, target `up_down_flat_h1`.
- V6.3 : robustesse, falsification, walk-forward descriptif et comparaison advanced vs simple.
- Reference V5.4 : simple OHLCV disponible et comparee descriptivement.
- Fenetre : `2023-03-25` -> `2026-05-23`.
- Total jours : `1156`.
- Modeles : `majority_class_baseline, random_seeded_baseline, logistic_regression, decision_tree_depth_2`.
- Timeframes : `1m, 5m, 15m, 1h`.
- Advanced feature columns count : `158`.
- `walk_forward_group` : present dans les metriques descriptives.

## 3. Comparaison advanced OHLCV vs simple OHLCV

- Global : advanced meilleur `20`, simple meilleur `11`, mitige/non conclusif `17`.
- `logistic_regression` : `{'advanced_better': 7, 'simple_better': 1, 'mixed_or_inconclusive': 4}`.
- `decision_tree_depth_2` : `{'advanced_better': 5, 'simple_better': 3, 'mixed_or_inconclusive': 4}`.
- `majority_class_baseline` : `{'advanced_better': 1, 'simple_better': 3, 'mixed_or_inconclusive': 8}`.
- `random_seeded_baseline` : `{'advanced_better': 7, 'simple_better': 4, 'mixed_or_inconclusive': 1}`.

Interpretation : advanced OHLCV apporte une amelioration descriptive partielle, mais le resultat reste mitige. Ce n est pas une preuve d avantage exploitable.

## 4. Comparaison aux baselines

- `logistic_regression` bat majority sur accuracy et macro_f1 dans `12/12` et `12/12` cas. Elle bat random en accuracy dans `12/12` cas, mais pas partout en macro_f1.
- `decision_tree_depth_2` est plus mitige : il bat majority dans `9/12` cas accuracy et random en macro_f1 dans seulement `4/12` cas.

Conclusion : les modeles appris battent parfois les baselines, mais pas assez uniformement pour conclure.

## 5. Stabilite train / validation / test

Une alerte de stabilite split est presente : `['15m.decision_tree_depth_2']`. Elle concerne `15m.decision_tree_depth_2`, avec un gap macro_f1 train -> validation superieur au seuil `0.10`. Le risque de surapprentissage reste donc localise mais reel.

## 6. Stabilite par timeframe

Les warnings de concentration timeframe sont presents sur les quatre modeles suivis. Le meilleur timeframe accuracy est souvent `1m`, avec des ranges accuracy importants : `{'decision_tree_depth_2': {'best_accuracy_timeframe': '1m', 'accuracy_range': 0.333704470092, 'macro_f1_range': 0.110127375314, 'single_timeframe_concentration_warning': True}, 'logistic_regression': {'best_accuracy_timeframe': '1m', 'accuracy_range': 0.30047775208, 'macro_f1_range': 0.093917741203, 'single_timeframe_concentration_warning': True}, 'majority_class_baseline': {'best_accuracy_timeframe': '1m', 'accuracy_range': 0.345463875364, 'macro_f1_range': 0.097460205324, 'single_timeframe_concentration_warning': True}, 'random_seeded_baseline': {'best_accuracy_timeframe': '1m', 'accuracy_range': 0.217679291403, 'macro_f1_range': 0.00520181184, 'single_timeframe_concentration_warning': True}}`.

Conclusion : les resultats sont instables entre `1m`, `5m`, `15m` et `1h`.

## 7. Stabilite walk-forward

Groupes faibles observes : `['wf_2023_Q1', 'wf_2023_Q2', 'wf_2023_Q3', 'wf_2023_Q4', 'wf_2024_Q1', 'wf_2024_Q2', 'wf_2024_Q3', 'wf_2024_Q4', 'wf_2025_Q1', 'wf_2025_Q2', 'wf_2025_Q3', 'wf_2025_Q4', 'wf_2026_Q1', 'wf_2026_Q2']`.

Groupes instables observes : `['wf_2023_Q3', 'wf_2025_Q3']`.

Les resultats montrent une sensibilite a certaines periodes, notamment `wf_2023_Q3` et `wf_2025_Q3` pour plusieurs sorties. Ces metriques walk-forward sont descriptives et ne constituent pas un backtest.

## 8. Label shuffle falsification

Le label shuffle detruit majoritairement les performances, mais deux cas restent trop proches de l original : `['15m.decision_tree_depth_2.validation', '15m.decision_tree_depth_2.test']`. Cette alerte touche `15m.decision_tree_depth_2` en validation et test. Elle empêche de recommander un backtest a ce stade.

## 9. Fuites / anti-leakage

Les scans V6.3 ne detectent aucune feature interdite ni metrique de trading interdite. `macd_like_signal` est une feature technique MACD-like, pas un signal de trading.

## 10. Limites restantes malgre advanced OHLCV

- OHLCV-only, meme avec 158 advanced features.
- Un seul actif: BTCUSDT spot.
- Aucun trade public historique dans les features.
- Pas de funding, open interest ni order book.
- Pas de couts, slippage, backtest ni execution reelle.
- Risque de data mining avec une bibliotheque large de features.
- Risque de colinearite entre indicateurs OHLCV avances.
- Fenetre max continue validee, mais pas necessairement toute l histoire segmentee de BTCUSDT.

## 11. Decision de direction

Option principale recommandee : A. Ajouter les trades publics historiques.

Option secondaire recommandee : D. Préparer une validation walk-forward offline plus stricte.

Raison : advanced OHLCV ne bat pas clairement et stablement simple OHLCV, le label shuffle reste trop proche dans certains cas, et les gains sont concentres par timeframe/periode. La prochaine etape utile est donc d enrichir l information source avec les trades publics historiques, tout en preparant une validation walk-forward offline plus stricte.

## 12. Roadmap proposee

- V7.0 — Public Trades Historical Ingestion
- V7.1 — OHLCV + Trades Feature Store
- V7.2 — Multi-source Dataset
- V7.3 — Multi-source ML Offline
- V7.4 — Multi-source Robustness / Walk-forward

## 13. Interdits maintenus

- Pas de trading.
- Pas de paper live.
- Pas d ordre.
- Pas de backtest validant une strategie.
- Pas de claim de rentabilite.
- V6.4 ne valide aucune strategie.
- V6.4 ne valide aucun modele exploitable en trading.
- V6.4 ne valide pas les advanced features pour le trading.
