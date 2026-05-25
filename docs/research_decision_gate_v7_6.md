# OHLCV + Public Trades Research Decision Gate - V7.6

## 1. Executive summary

Verdict : OHLCV + aggTrades est interessant mais non concluant sur 30 jours. V7.4/V7.5 montre des gains descriptifs partiels, surtout contre certaines baselines et references, mais les resultats restent instables entre splits, timeframes et groupes walk-forward. V7.6 ne tire aucune conclusion trading.

La fenetre de `30` jours est trop courte pour conclure statistiquement. Elle suffit pour valider une piste technique et une decision de direction prudente, pas pour valider un modele ou une strategie.

## 2. Resume des entrees analysees

- V7.1 : ingestion aggTrades publics BTCUSDT spot sur `30` jours.
- V7.2 : features causales OHLCV + aggTrades.
- V7.3 : dataset supervise offline OHLCV + aggTrades.
- V7.4 : ML offline OHLCV + aggTrades, scores `research_*`.
- V7.5 : robustesse, falsification et walk-forward descriptif.
- Fenetre : `2023-03-25` -> `2023-04-23`.
- Total jours : `30`.
- Trade source type : `aggTrades`.
- Modeles : `majority_class_baseline, random_seeded_baseline, logistic_regression, decision_tree_depth_2`.
- Target : `up_down_flat_h1`.
- Timeframes : `1m, 5m, 15m, 1h`.
- `walk_forward_group` : present.

## 3. Comparaison OHLCV + trades vs references

- `advanced_ohlcv_v6_2` : OHLCV+trades meilleur `22`, reference meilleure `14`, mitige/non conclusif `12`. Comparaison non directement comparable car la fenetre differe.
- `simple_ohlcv_v5_4` : OHLCV+trades meilleur `23`, reference meilleure `14`, mitige/non conclusif `11`. Comparaison non directement comparable car la fenetre differe.

Interpretation : OHLCV + trades apporte un gain descriptif partiel, mais les references V6.2/V5.4 utilisent des fenetres differentes. La comparaison est donc informative, non directement comparable et non actionnable.

## 4. Comparaison aux baselines

- `logistic_regression` : accuracy > majority `11/12`, macro_f1 > majority `12/12`, accuracy > random `12/12`, macro_f1 > random `12/12`.
- `decision_tree_depth_2` : accuracy > majority `9/12`, macro_f1 > majority `9/12`, accuracy > random `12/12`, macro_f1 > random `5/12`.

Conclusion : `logistic_regression` bat souvent les baselines descriptives. `decision_tree_depth_2` est plus mitige, notamment contre random en macro_f1. Les modeles appris montrent quelque chose d interessant, mais pas assez stable pour conclure.

## 5. Stabilite train / validation / test

Alertes de stabilite split : `['15m.logistic_regression', '1h.decision_tree_depth_2', '1h.logistic_regression', '1h.random_seeded_baseline']`.

Ces alertes indiquent un risque de surapprentissage ou de bruit sur certains couples timeframe/modele, notamment sur `15m` et `1h`. La stabilite train / validation / test n est pas suffisante pour passer a un backtest.

## 6. Stabilite par timeframe

Warnings de concentration timeframe : `['decision_tree_depth_2', 'logistic_regression', 'majority_class_baseline', 'random_seeded_baseline']`.

Le meilleur score accuracy est souvent concentre sur `1m`, alors que les macro_f1 varient selon `1m`, `5m`, `15m` et `1h`. Les resultats ne sont pas stables entre timeframes.

## 7. Stabilite walk-forward

Groupes faibles par modele : `{'15m.majority_class_baseline': ['wf_window_01', 'wf_window_02', 'wf_window_03', 'wf_window_04', 'wf_window_05_partial'], '15m.random_seeded_baseline': ['wf_window_01', 'wf_window_02', 'wf_window_03', 'wf_window_05_partial'], '1h.majority_class_baseline': ['wf_window_02', 'wf_window_04'], '1h.random_seeded_baseline': ['wf_window_04'], '5m.majority_class_baseline': ['wf_window_01'], '5m.random_seeded_baseline': ['wf_window_01']}`.

Groupes instables par modele : `{'1h.decision_tree_depth_2': ['wf_window_01', 'wf_window_04', 'wf_window_05_partial'], '1h.logistic_regression': ['wf_window_01', 'wf_window_03', 'wf_window_05_partial'], '1h.random_seeded_baseline': ['wf_window_04'], '5m.majority_class_baseline': ['wf_window_01']}`.

Concentration observee : `['1h.decision_tree_depth_2', '1h.logistic_regression']`.

Ces metriques walk-forward sont descriptives. Elles ne constituent pas un backtest et ne produisent aucun signal.

## 8. Label shuffle falsification

Cas ou l original ne se detache pas clairement des labels train shuffles : `['1h.decision_tree_depth_2.test', '1h.decision_tree_depth_2.validation', '1h.logistic_regression.test', '1m.decision_tree_depth_2.test', '1m.decision_tree_depth_2.validation']`.

Alerte : les performances ne disparaissent pas assez nettement dans plusieurs cas. Cela empêche de recommander un backtest a ce stade.

## 9. Fuites / anti-leakage

Les scans V7.5 ne detectent pas de feature interdite : `[]`.

Les scans V7.5 ne detectent pas de metrique trading interdite : `[]`.

Aucune anomalie anti-leakage n est signalee par les scans, mais cela ne transforme pas les resultats en preuve robuste.

## 10. Limites de la fenetre 30 jours

- Periode trop courte.
- Pas assez de regimes de marche.
- Comparaison non directe avec V6/V5.
- Risque de surinterpretation.
- Pas de couts ni slippage.
- Pas de backtest.
- Pas de vraie execution.
- Trades disponibles seulement sur fenetre courte dans cette branche.

## 11. Decision de direction

Option principale recommandee : A. Étendre les aggTrades à 90 jours.

Option secondaire recommandee : E. Préparer une validation walk-forward offline plus stricte.

Raison : la fenetre de 30 jours est trop courte, le label shuffle reste trop proche dans plusieurs cas, et les resultats sont concentres par timeframe ou groupe. Le passage direct a 1 an ou a un backtest serait premature. Une extension a 90 jours controle mieux le volume des aggTrades tout en testant la robustesse sur une periode plus informative.

## 12. Roadmap proposee

- V7.7 — Public Trades 90-Day Window Expansion
- V7.8 — OHLCV + Trades 90-Day Feature Store
- V7.9 — OHLCV + Trades 90-Day Dataset
- V8.0 — OHLCV + Trades 90-Day ML Offline / Robustness

## 13. Interdits maintenus

- Pas de trading.
- Pas de paper live.
- Pas d ordre.
- Pas de backtest validant une strategie.
- Pas de claim de rentabilite.
- V7.6 ne valide aucune strategie.
- V7.6 ne valide aucun modele exploitable en trading.
- V7.6 ne valide pas les features OHLCV + trades pour le trading.
