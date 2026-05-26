# Research decision gate V8.8

## 1. Executive summary

- Verdict research : `interessant_mais_instable_non_concluant`.
- V8.8 ne produit aucune conclusion trading.
- V8.7 est interessant pour la recherche, mais reste instable, mitige et non concluant.
- V8.7 est une validation walk-forward offline stricte, pas un backtest.
- Un backtest research n'est pas justifie maintenant.

## 2. Resume des entrees analysees

- V8.5 : static split offline OHLCV + aggTrades 1 an.
- V8.7 : strict walk-forward offline OHLCV + aggTrades 1 an.
- Fenetre : `2023-03-25` -> `2024-03-24`.
- Total jours : `366`.
- Feature columns count : `71`.
- Target : `up_down_flat_h1`.
- Modeles : majority_class_baseline, random_seeded_baseline, logistic_regression, decision_tree_depth_2.
- Timeframes : 1m, 5m, 15m, 1h.
- Folds par timeframe : `{'1m': 5, '5m': 5, '15m': 5, '1h': 5}`.
- Purge bars : `5`.
- Embargo bars : `5`.
- Expanding train : `True`.

## 3. Resultats walk-forward par modele

### majority_class_baseline
- 1m: mean_test_accuracy=0.687306, mean_test_macro_f1=0.270450, std_test_accuracy=0.086777, weak_folds=[], unstable_folds=['fold_01', 'fold_02', 'fold_03', 'fold_04', 'fold_05'], fold_concentration_warnings=['test accuracy varies across folds'].
- 5m: mean_test_accuracy=0.382175, mean_test_macro_f1=0.183177, std_test_accuracy=0.066091, weak_folds=['fold_02', 'fold_03', 'fold_05'], unstable_folds=['fold_01', 'fold_02', 'fold_03', 'fold_04', 'fold_05'], fold_concentration_warnings=['test accuracy varies across folds', 'weak folds present'].
- 15m: mean_test_accuracy=0.301596, mean_test_macro_f1=0.151813, std_test_accuracy=0.094926, weak_folds=['fold_01', 'fold_02', 'fold_03', 'fold_04'], unstable_folds=['fold_01', 'fold_02', 'fold_03', 'fold_04', 'fold_05'], fold_concentration_warnings=['test accuracy varies across folds', 'weak folds present'].
- 1h: mean_test_accuracy=0.456830, mean_test_macro_f1=0.208978, std_test_accuracy=0.018673, weak_folds=[], unstable_folds=[], fold_concentration_warnings=[].

### random_seeded_baseline
- 1m: mean_test_accuracy=0.589466, mean_test_macro_f1=0.323323, std_test_accuracy=0.065774, weak_folds=[], unstable_folds=['fold_01', 'fold_02', 'fold_03', 'fold_04', 'fold_05'], fold_concentration_warnings=['test accuracy varies across folds'].
- 5m: mean_test_accuracy=0.347587, mean_test_macro_f1=0.323766, std_test_accuracy=0.020408, weak_folds=['fold_05'], unstable_folds=[], fold_concentration_warnings=['weak folds present'].
- 15m: mean_test_accuracy=0.329831, mean_test_macro_f1=0.323538, std_test_accuracy=0.008191, weak_folds=['fold_01', 'fold_02', 'fold_03', 'fold_04'], unstable_folds=[], fold_concentration_warnings=['weak folds present'].
- 1h: mean_test_accuracy=0.390837, mean_test_macro_f1=0.336685, std_test_accuracy=0.015676, weak_folds=[], unstable_folds=[], fold_concentration_warnings=[].

### logistic_regression
- 1m: mean_test_accuracy=0.686845, mean_test_macro_f1=0.374676, std_test_accuracy=0.084761, weak_folds=[], unstable_folds=['fold_01', 'fold_02', 'fold_03', 'fold_04', 'fold_05'], fold_concentration_warnings=['test accuracy varies across folds'].
- 5m: mean_test_accuracy=0.441580, mean_test_macro_f1=0.390105, std_test_accuracy=0.027680, weak_folds=[], unstable_folds=[], fold_concentration_warnings=[].
- 15m: mean_test_accuracy=0.416702, mean_test_macro_f1=0.359625, std_test_accuracy=0.020293, weak_folds=[], unstable_folds=[], fold_concentration_warnings=[].
- 1h: mean_test_accuracy=0.460549, mean_test_macro_f1=0.326971, std_test_accuracy=0.019825, weak_folds=[], unstable_folds=[], fold_concentration_warnings=[].

### decision_tree_depth_2
- 1m: mean_test_accuracy=0.687306, mean_test_macro_f1=0.270450, std_test_accuracy=0.086777, weak_folds=[], unstable_folds=['fold_01', 'fold_02', 'fold_03', 'fold_04', 'fold_05'], fold_concentration_warnings=['test accuracy varies across folds'].
- 5m: mean_test_accuracy=0.438180, mean_test_macro_f1=0.326170, std_test_accuracy=0.020878, weak_folds=[], unstable_folds=[], fold_concentration_warnings=[].
- 15m: mean_test_accuracy=0.405472, mean_test_macro_f1=0.320729, std_test_accuracy=0.021524, weak_folds=[], unstable_folds=['fold_01', 'fold_02', 'fold_03', 'fold_04', 'fold_05'], fold_concentration_warnings=['test macro_f1 varies across folds'].
- 1h: mean_test_accuracy=0.459017, mean_test_macro_f1=0.317487, std_test_accuracy=0.016009, weak_folds=[], unstable_folds=[], fold_concentration_warnings=[].

## 4. Comparaison aux baselines

- Verdict global : `mitige_pas_de_battement_net_generalise`.
- Clear wins appris : `2`.
- Resultats mitiges : `6`.
- Misses : `0`.
- 1m.logistic_regression: delta_macro_f1_vs_majority=0.104226, delta_macro_f1_vs_random=0.051353, verdict=`bat_les_baselines_en_macro_f1_mais_resultat_mitige`.
- 1m.decision_tree_depth_2: delta_macro_f1_vs_majority=0.0, delta_macro_f1_vs_random=-0.052872, verdict=`resultat_mitige`.
- 5m.logistic_regression: delta_macro_f1_vs_majority=0.206928, delta_macro_f1_vs_random=0.06634, verdict=`bat_clairement_les_baselines_sur_accuracy_et_macro_f1`.
- 5m.decision_tree_depth_2: delta_macro_f1_vs_majority=0.142993, delta_macro_f1_vs_random=0.002404, verdict=`resultat_mitige`.
- 15m.logistic_regression: delta_macro_f1_vs_majority=0.207813, delta_macro_f1_vs_random=0.036087, verdict=`bat_clairement_les_baselines_sur_accuracy_et_macro_f1`.
- 15m.decision_tree_depth_2: delta_macro_f1_vs_majority=0.168916, delta_macro_f1_vs_random=-0.00281, verdict=`resultat_mitige`.
- 1h.logistic_regression: delta_macro_f1_vs_majority=0.117994, delta_macro_f1_vs_random=-0.009714, verdict=`resultat_mitige`.
- 1h.decision_tree_depth_2: delta_macro_f1_vs_majority=0.10851, delta_macro_f1_vs_random=-0.019197, verdict=`resultat_mitige`.

## 5. Stabilite entre folds

- Verdict : `instable_ou_concentre`.
- Entrees instables : `7`.
- Entrees faibles : `4`.
- Concentration fold : `9` entrees.
- Les resultats dependent trop de certains folds pour justifier un backtest.

## 6. Stabilite par timeframe

- Verdict : `non_stable_entre_timeframes`.
- 1m : accuracy elevee, macro_f1 moins convaincante et folds instables.
- 5m : meilleur profil learned, mais il ne suffit pas a stabiliser tout le diagnostic.
- 15m : profil learned interessant, mais decision_tree_depth_2 reste instable.
- 1h : resultats mitiges et proches de la baseline random en macro_f1.
- Les resultats ne sont pas coherents sur tous les timeframes.

## 7. Label shuffle falsification par fold

- Cas analyses : `80`.
- Cas trop proches des labels melanges : `18`.
- Par modele : `{'decision_tree_depth_2': 10, 'logistic_regression': 8}`.
- Par timeframe : `{'1m': 12, '1h': 6}`.
- Par role : `{'validation': 8, 'test': 10}`.
- Le fait que 18 cas restent trop proches des labels melanges est une alerte forte.
- La falsification n'est pas proprement satisfaite.

## 8. Comparaison V8.7 vs V8.5 static split

- V8.5 static split et V8.7 strict walk-forward ne sont pas le meme design de validation.
- Cas learned compares : `8`.
- Deltas macro_f1 positifs : `4`.
- Deltas macro_f1 negatifs : `4`.
- Verdict : `v8_7_affaiblit_le_diagnostic_de_stabilite_v8_5`.
- V8.7 confirme que le diagnostic V8.5 doit rester prudent et descriptif.

## 9. Fuites / anti-leakage

- Feature leakage detectee : `False`.
- Colonnes interdites detectees : `[]`.
- Metriques interdites detectees : `False`.
- Aucune feature future, label, split ou fold n'est reportee comme utilisee.

## 10. Limites restantes

- Pas de backtest.
- Pas de couts ni slippage.
- Pas d'execution.
- Le label h1 peut etre trop bruite.
- Les features peuvent etre trop agregees.
- OHLCV + aggTrades seulement, sans funding, open interest ni order book.
- Les comparaisons avec d'autres fenetres ne sont pas directes.
- Les resultats ne sont pas valides pour trading.

## 11. Decision de direction

- Option principale : A. Ameliorer/refactoriser les features OHLCV + trades.
- Option secondaire : B. Revoir les labels.
- Un backtest research tres borne n'est pas recommande maintenant.
- La raison principale est la proximite aux labels melanges et la concentration folds/timeframes.

## 12. Roadmap proposee

- V8.9 - OHLCV + Trades Feature Audit / Selection
- V9.0 - Refined OHLCV + Trades Feature Store
- V9.1 - Refined OHLCV + Trades Dataset
- V9.2 - Refined OHLCV + Trades ML Offline
- V9.3 - Refined Strict Walk-Forward Validation

## 13. Interdits maintenus

- Pas de trading.
- Pas de paper live.
- Pas d'ordre.
- Pas de backtest destine a valider une strategie.
- Pas de strategie.
- Pas de signal de trading.
- Pas de claim de rentabilite.
