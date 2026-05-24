# V4.8 - 1-Year Research Decision Gate & Next Roadmap

## 1. Executive summary

Verdict : **mitigé et non concluant, avec un signal descriptif intéressant mais fragile**.

Les résultats V4.6/V4.7 montrent que `logistic_regression` bat souvent les baselines naïves sur validation/test, surtout en macro F1. Ce point mérite attention. En revanche, la stabilité entre timeframes est faible, les meilleurs résultats se concentrent sur `1m`, et les tests de labels train shufflés ne détruisent pas systématiquement les performances. Ce rapport ne tire aucune conclusion trading, ne valide aucune stratégie et ne déclare aucun modèle exploitable en trading.

Décision principale : **A. Étendre à l'historique max OHLCV.**

Décision secondaire : **E. Préparer une validation walk-forward offline.**

## 2. Résumé des entrées analysées

- V4.6 : baselines ML offline 1 an, statut `PASS`.
- V4.7 : audit robustesse et falsification 1 an, statut `PASS`.
- Fenêtre : `2024-01-01` à `2024-12-31` inclus.
- Modèles : `majority_class_baseline, random_seeded_baseline, logistic_regression, decision_tree_depth_2`.
- Modèles appris évalués dans cette décision : `logistic_regression`, `decision_tree_depth_2`.
- Target : `up_down_flat_h1`.
- Timeframes : `1m, 5m, 15m, 1h`.

## 3. Comparaison aux baselines

Lecture : les deltas comparent le modèle appris à la baseline indiquée sur le même timeframe et le même split.

| Modèle | Timeframe | Split | Accuracy | Macro F1 | Delta acc vs majority | Delta F1 vs majority | Delta acc vs random | Delta F1 vs random |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| logistic_regression | 1m | validation | 0.7058 | 0.3477 | +0.0040 | +0.0727 | +0.1868 | +0.0134 |
| logistic_regression | 1m | test | 0.6581 | 0.3632 | +0.0048 | +0.0998 | +0.1629 | +0.0287 |
| logistic_regression | 5m | validation | 0.4492 | 0.3815 | +0.0565 | +0.1935 | +0.1063 | +0.0421 |
| logistic_regression | 5m | test | 0.4276 | 0.3843 | +0.0695 | +0.2086 | +0.0956 | +0.0538 |
| logistic_regression | 15m | validation | 0.4318 | 0.3993 | +0.0360 | +0.2102 | +0.0680 | +0.0577 |
| logistic_regression | 15m | test | 0.4246 | 0.3891 | +0.0139 | +0.1950 | +0.0667 | +0.0556 |
| logistic_regression | 1h | validation | 0.4952 | 0.3499 | +0.0467 | +0.1435 | +0.0962 | +0.0190 |
| logistic_regression | 1h | test | 0.4806 | 0.3380 | +0.0051 | +0.1231 | +0.0746 | -0.0020 |
| decision_tree_depth_2 | 1m | validation | 0.7018 | 0.2749 | +0.0000 | +0.0000 | +0.1828 | -0.0593 |
| decision_tree_depth_2 | 1m | test | 0.6533 | 0.2634 | +0.0000 | +0.0000 | +0.1581 | -0.0710 |
| decision_tree_depth_2 | 5m | validation | 0.4208 | 0.2778 | +0.0282 | +0.0899 | +0.0780 | -0.0616 |
| decision_tree_depth_2 | 5m | test | 0.4142 | 0.3086 | +0.0561 | +0.1329 | +0.0822 | -0.0219 |
| decision_tree_depth_2 | 15m | validation | 0.4039 | 0.2794 | +0.0081 | +0.0904 | +0.0401 | -0.0621 |
| decision_tree_depth_2 | 15m | test | 0.4211 | 0.2743 | +0.0104 | +0.0802 | +0.0632 | -0.0591 |
| decision_tree_depth_2 | 1h | validation | 0.4775 | 0.3131 | +0.0290 | +0.1067 | +0.0785 | -0.0178 |
| decision_tree_depth_2 | 1h | test | 0.4903 | 0.3221 | +0.0148 | +0.1072 | +0.0843 | -0.0179 |

Conclusion `logistic_regression` : **résultat intéressant mais non concluant**. Le modèle bat les baselines sur la majorité des comparaisons validation/test, mais les gains restent descriptifs, modestes et non transformables en décision opérationnelle.

Conclusion `decision_tree_depth_2` : **résultat faible à mitigé**. Le modèle bat parfois la baseline majoritaire, mais il ne bat pas la baseline random en macro F1 sur validation/test. Le résultat n'est pas assez stable pour soutenir une piste prioritaire.

## 4. Stabilité train / validation / test

| Modèle | Timeframe | Train acc | Validation acc | Test acc | Gap train-validation | Gap validation-test | Overfit warning |
| --- | --- | --- | --- | --- | --- | --- | --- |
| logistic_regression | 1m | 0.6761 | 0.7058 | 0.6581 | -0.0297 | +0.0477 | false |
| logistic_regression | 5m | 0.4425 | 0.4492 | 0.4276 | -0.0067 | +0.0216 | false |
| logistic_regression | 15m | 0.4424 | 0.4318 | 0.4246 | +0.0107 | +0.0071 | false |
| logistic_regression | 1h | 0.4811 | 0.4952 | 0.4806 | -0.0141 | +0.0145 | false |
| decision_tree_depth_2 | 1m | 0.6675 | 0.7018 | 0.6533 | -0.0344 | +0.0485 | false |
| decision_tree_depth_2 | 5m | 0.4259 | 0.4208 | 0.4142 | +0.0051 | +0.0067 | false |
| decision_tree_depth_2 | 15m | 0.4136 | 0.4039 | 0.4211 | +0.0097 | -0.0172 | false |
| decision_tree_depth_2 | 1h | 0.4802 | 0.4775 | 0.4903 | +0.0026 | -0.0128 | false |

La stabilité train / validation / test est meilleure que sur la fenêtre 90 jours : aucun modèle appris ne déclenche `overfit_warning` selon le seuil V4.7. Cela reste insuffisant pour conclure, car les écarts validation/test persistent et la stabilité temporelle n'est pas testée en walk-forward multi-régime.

## 5. Stabilité par timeframe

| Modèle | Meilleur timeframe test acc | Range acc | Range macro F1 | Warning concentration | Accuracy par timeframe |
| --- | --- | --- | --- | --- | --- |
| logistic_regression | 1m | 0.2335 | 0.0511 | true | 1m=0.6581, 5m=0.4276, 15m=0.4246, 1h=0.4806 |
| decision_tree_depth_2 | 1m | 0.2392 | 0.0586 | true | 1m=0.6533, 5m=0.4142, 15m=0.4211, 1h=0.4903 |

Les résultats ne sont pas stables entre timeframes. Les deux modèles appris ont leur meilleure accuracy test sur `1m` et déclenchent un warning de concentration. La lecture `1m` est donc fragile et ne doit pas être généralisée aux autres horizons.

## 6. Label shuffle falsification

| Modèle | Timeframe | Split | Original acc | Shuffled acc | Delta acc | Delta macro F1 | No clear edge |
| --- | --- | --- | --- | --- | --- | --- | --- |
| logistic_regression | 1m | validation | 0.7058 | 0.7018 | +0.0040 | +0.0727 | false |
| logistic_regression | 1m | test | 0.6581 | 0.6533 | +0.0048 | +0.0998 | false |
| logistic_regression | 5m | validation | 0.4492 | 0.3942 | +0.0550 | +0.1868 | false |
| logistic_regression | 5m | test | 0.4276 | 0.3611 | +0.0665 | +0.1987 | false |
| logistic_regression | 15m | validation | 0.4318 | 0.4222 | +0.0095 | +0.0871 | false |
| logistic_regression | 15m | test | 0.4246 | 0.4315 | -0.0068 | +0.0711 | true |
| logistic_regression | 1h | validation | 0.4952 | 0.4491 | +0.0461 | +0.0351 | false |
| logistic_regression | 1h | test | 0.4806 | 0.4476 | +0.0330 | +0.0232 | false |
| decision_tree_depth_2 | 1m | validation | 0.7018 | 0.7018 | +0.0000 | +0.0000 | false |
| decision_tree_depth_2 | 1m | test | 0.6533 | 0.6533 | +0.0000 | +0.0000 | true |
| decision_tree_depth_2 | 5m | validation | 0.4208 | 0.3928 | +0.0280 | +0.0893 | false |
| decision_tree_depth_2 | 5m | test | 0.4142 | 0.3583 | +0.0558 | +0.1288 | false |
| decision_tree_depth_2 | 15m | validation | 0.4039 | 0.4151 | -0.0112 | -0.0055 | true |
| decision_tree_depth_2 | 15m | test | 0.4211 | 0.4192 | +0.0019 | -0.0113 | true |
| decision_tree_depth_2 | 1h | validation | 0.4775 | 0.4519 | +0.0256 | -0.0048 | true |
| decision_tree_depth_2 | 1h | test | 0.4903 | 0.4476 | +0.0427 | +0.0082 | false |

Le shuffle des labels train dégrade plusieurs performances, mais pas toutes. Cas sans avantage clair face aux labels shufflés : `15m.logistic_regression.test, 1m.decision_tree_depth_2.test, 15m.decision_tree_depth_2.validation, 15m.decision_tree_depth_2.test, 1h.decision_tree_depth_2.validation`. C'est une alerte forte : il reste du bruit ou une dépendance trop faible pour déclarer un edge robuste.

## 7. Fuites / anti-leakage

- `feature_leakage_detected` : `false`.
- Colonnes features interdites détectées : `[]`.
- `metric_forbidden_terms_detected` : `false`.
- Termes métriques interdits présents : `[]`.

Les scans V4.7 ne détectent pas de fuite feature. Les alertes restantes viennent surtout de la concentration par timeframe et des tests de falsification label shuffle.

## 8. Limites restantes malgré 1 an

- Un seul actif : BTCUSDT spot.
- Une seule année civile : 2024.
- Pas de trades publics historiques intégrés.
- Pas de funding ni open interest.
- Pas d'order book.
- Pas de walk-forward multi-régime.
- Pas de coûts ni slippage.
- Pas de backtest.

Ces limites empêchent de transformer les résultats en conclusion robuste.

## 9. Décision de direction

Option principale retenue : **A. Étendre à l'historique max OHLCV.**

Justification : les résultats sur 1 an sont plus informatifs que les 90 jours, mais restent trop concentrés et fragiles. L'étape la plus rationnelle est d'augmenter la diversité temporelle avant d'améliorer les modèles ou d'envisager un backtest research.

Option secondaire retenue : **E. Préparer une validation walk-forward offline.**

Justification : l'historique max doit être découpé en fenêtres temporelles successives pour vérifier si les gains descriptifs survivent hors segment, sans créer de stratégie et sans produire de signal.

Options non retenues maintenant : ajouter les trades publics, améliorer les features, revoir les labels, préparer un backtest research très borné, ou geler toute la piste ML. Ces options restent possibles, mais elles doivent venir après une validation temporelle plus large.

## 10. Roadmap proposée

- **V5.0** : extension à l'historique max OHLCV public BTCUSDT, data-only, sans feature, label, ML ni backtest.
- **V5.1** : feature store causal sur historique max OHLCV, sans label, dataset ML, backtest ni stratégie.
- **V5.2** : label factory forward sur historique max, séparée des features, sans dataset ML ni backtest.
- **V5.3** : dataset supervisé offline historique max avec splits temporels et design walk-forward offline, sans modèle ni backtest.
- **V5.4** : baselines ML offline et audit robustesse walk-forward/falsification, métriques descriptives uniquement.

## 11. Interdits maintenus

- Pas de trading.
- Pas de paper live.
- Pas d'ordre.
- Pas de backtest validant une stratégie.
- Pas de claim de rentabilité.
- Aucune stratégie n'est validée.
- Aucun modèle n'est validé pour le trading.

V4.8 reste une décision research `pending_external_audit` avant validation externe.
