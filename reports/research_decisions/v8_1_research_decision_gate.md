# OHLCV + Public Trades 90-Day Research Decision Gate - V8.1

## 1. Executive summary

Verdict : OHLCV + aggTrades sur 90 jours est interessant, mais reste mitige et non concluant. V8.0 montre des gains descriptifs partiels, surtout pour `logistic_regression`, mais les resultats restent trop fragiles pour tirer une conclusion trading.

La fenetre de `90` jours est plus informative que 30 jours, mais elle reste limitee. V8.1 ne recommande pas de backtest : label shuffle reste trop proche dans plusieurs cas, les comparaisons aux references ne sont pas directes, et l accuracy est concentree sur `1m`.

## 2. Resume des entrees analysees

- V7.7 : ingestion aggTrades publics BTCUSDT spot sur `90` jours.
- V7.8 : features causales OHLCV + aggTrades sur `90` jours.
- V7.9 : dataset supervise offline OHLCV + aggTrades sur `90` jours.
- V8.0 : ML offline, robustesse descriptive et falsification label shuffle.
- Fenetre : `2023-03-25` -> `2023-06-22`.
- Total jours : `90`.
- Trade source type : `aggTrades`.
- Modeles : `majority_class_baseline`, `random_seeded_baseline`, `logistic_regression`, `decision_tree_depth_2`.
- Target : `up_down_flat_h1`.
- Timeframes : `1m`, `5m`, `15m`, `1h`.
- `walk_forward_group` : present.
- Feature columns count : `71`.

## 3. Comparaison OHLCV + trades 90 jours vs references

- V7.4 OHLCV+trades 30 jours : V8.0 meilleur `21`, reference meilleure `20`, mitige/non conclusif `7`. Comparaison non directement comparable car la fenetre differe.
- V6.2 advanced OHLCV : V8.0 meilleur `20`, reference meilleure `16`, mitige/non conclusif `12`. Comparaison non directement comparable car la fenetre et le jeu de sources different.
- V5.4 simple OHLCV : V8.0 meilleur `23`, reference meilleure `15`, mitige/non conclusif `10`. Comparaison non directement comparable car la fenetre et le jeu de sources different.

Interpretation : les features OHLCV + trades 90 jours apportent un gain descriptif partiel, mais pas un gain net et robuste. Ces comparaisons sont informatives, non directement comparables et non actionnables.

## 4. Comparaison aux baselines

- `logistic_regression` : accuracy > majority `11/12`, macro_f1 > majority `12/12`, accuracy > random `12/12`, macro_f1 > random `11/12`.
- `decision_tree_depth_2` : accuracy > majority `8/12`, macro_f1 > majority `9/12`, accuracy > random `12/12`, macro_f1 > random `2/12`.

Conclusion : `logistic_regression` bat souvent les baselines descriptives, mais pas assez proprement face a la falsification label shuffle. `decision_tree_depth_2` est plus mitige, notamment contre random en macro_f1. Le resultat est interessant, mais non interpretable comme preuve robuste.

## 5. Stabilite train / validation / test

V8.0 ne signale pas d alerte `overfit_warning` selon le seuil `0.10` sur les splits train / validation / test.

Cette stabilite split est un point positif par rapport a la fenetre 30 jours, mais elle ne suffit pas. Les autres diagnostics restent limitants : label shuffle trop proche dans plusieurs cas et concentration par timeframe.

## 6. Stabilite par timeframe

- `1m` : meilleur timeframe en accuracy pour tous les modeles, y compris les baselines.
- `5m` : meilleure macro_f1 test pour `logistic_regression`, mais l avantage n est pas stable sur toutes les comparaisons.
- `15m` : resultats plus faibles en accuracy et mitiges en macro_f1.
- `1h` : resultats faibles ou instables selon le modele.

Warnings de concentration timeframe : `decision_tree_depth_2`, `logistic_regression`, `majority_class_baseline`, `random_seeded_baseline`.

Interpretation : les resultats ne sont pas stables entre timeframes. Le fait que `1m` domine l accuracy, y compris pour les baselines, invite a la prudence.

## 7. Stabilite walk-forward

Groupes faibles observes :

- `15m.majority_class_baseline` : `wf_2023_03_partial`, `wf_2023_04`, `wf_2023_05`, `wf_2023_06_partial`.
- `15m.random_seeded_baseline` : `wf_2023_03_partial`, `wf_2023_04`, `wf_2023_05`.
- `1h.majority_class_baseline` : `wf_2023_04`, `wf_2023_06_partial`.
- `5m.majority_class_baseline` : `wf_2023_03_partial`.
- `5m.random_seeded_baseline` : `wf_2023_03_partial`.

V8.0 ne signale pas de groupe instable explicite ni de concentration sur quelques groupes. C est meilleur que la fenetre 30 jours, mais cela reste descriptif. Ces metriques walk-forward ne constituent pas un backtest.

## 8. Label shuffle falsification

Cas ou l original ne se detache pas clairement des labels train shuffles :

- `1m.logistic_regression.validation`.
- `1m.decision_tree_depth_2.test`.
- `1h.logistic_regression.test`.

Alerte : les performances ne disparaissent pas assez nettement dans plusieurs cas. Cela empeche de recommander un backtest a ce stade.

## 9. Fuites / anti-leakage

Les scans V8.0 ne detectent pas de feature interdite : `[]`.

Les scans V8.0 ne detectent pas de metrique trading interdite : `[]`.

Aucune anomalie anti-leakage n est signalee par les scans. Cette absence d anomalie ne transforme pas les resultats en preuve robuste.

## 10. Limites de la fenetre 90 jours

- Periode encore courte.
- Pas assez de regimes de marche.
- Comparaison non directe avec V7.4, V6.2 et V5.4.
- Risque de surinterpretation.
- Pas de couts ni slippage.
- Pas de backtest.
- Pas de vraie execution.
- AggTrades disponibles seulement sur fenetre 90 jours dans cette branche.
- Les resultats ne doivent pas etre transformes en strategie.

## 11. Decision de direction

Option principale recommandee : A. Étendre les aggTrades à 1 an.

Option secondaire recommandee : D. Préparer une validation walk-forward offline plus stricte.

Raison : 90 jours est techniquement valide et plus informatif que 30 jours, mais pas assez robuste. Le label shuffle reste trop proche dans plusieurs cas et les resultats sont concentres par timeframe. Un backtest research serait premature. La prochaine etape utile est d etendre la fenetre pour tester plus de regimes, tout en durcissant la validation walk-forward offline.

## 12. Roadmap proposee

- V8.2 — Public Trades 1-Year Window Expansion
- V8.3 — OHLCV + Trades 1-Year Feature Store
- V8.4 — OHLCV + Trades 1-Year Dataset
- V8.5 — OHLCV + Trades 1-Year ML Offline
- V8.6 — OHLCV + Trades 1-Year Robustness / Decision Gate

## 13. Interdits maintenus

- Pas de trading.
- Pas de paper live.
- Pas d ordre.
- Pas de backtest validant une strategie.
- Pas de claim de rentabilite.
- V8.1 ne valide aucune strategie.
- V8.1 ne valide aucun modele exploitable en trading.
- V8.1 ne valide pas les features OHLCV + trades pour le trading.
