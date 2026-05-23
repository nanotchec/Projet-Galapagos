# V4.1 - Research Decision Gate & Next Roadmap

## 1. Executive summary

Verdict : **non concluant, avec quelques signaux descriptifs faibles**.

Les résultats ML V3.9/V4.0 montrent des écarts positifs ponctuels, surtout pour `logistic_regression`, mais ils ne démontrent pas une robustesse suffisante. Les gains restent modestes, les performances ne sont pas stables partout, et la falsification par labels shufflés laisse plusieurs alertes. Ce rapport ne tire aucune conclusion trading et ne valide aucune stratégie.

Décision principale : **A. Étendre à 1 an de données avant toute suite.**

Décision secondaire : **D. Préparer ensuite une validation walk-forward offline, sans backtest exécuté.**

## 2. Résumé des entrées analysées

- V3.9 : baselines ML offline 90 jours, statut `PASS`.
- V4.0 : audit robustesse et falsification, statut `PASS`.
- Fenêtre : 2024-01-01 à 2024-03-30, soit 90 jours.
- Modèles : `majority_class_baseline`, `random_seeded_baseline`, `logistic_regression`, `decision_tree_depth_2`.
- Modèles appris évalués dans cette décision : `logistic_regression`, `decision_tree_depth_2`.
- Target : `up_down_flat_h1`.
- Timeframes : `1m`, `5m`, `15m`, `1h`.

## 3. Comparaison aux baselines

Lecture : les deltas comparent le modèle appris à la baseline indiquée sur le même timeframe et le même split.

| Modèle | Timeframe | Split | Accuracy | Macro F1 | Delta accuracy vs majority | Delta macro F1 vs majority | Delta accuracy vs random | Delta macro F1 vs random |
|---|---:|---|---:|---:|---:|---:|---:|---:|
| logistic_regression | 1m | validation | 0.6194 | 0.4193 | +0.0252 | +0.1708 | +0.1405 | +0.0890 |
| logistic_regression | 1m | test | 0.5504 | 0.3937 | +0.0201 | +0.1626 | +0.1137 | +0.0776 |
| logistic_regression | 5m | validation | 0.4404 | 0.4285 | +0.1190 | +0.2664 | +0.1132 | +0.1021 |
| logistic_regression | 5m | test | 0.4040 | 0.4037 | +0.1453 | +0.2666 | +0.0803 | +0.0803 |
| logistic_regression | 15m | validation | 0.4340 | 0.3441 | -0.0023 | +0.1416 | +0.0689 | +0.0065 |
| logistic_regression | 15m | test | 0.4493 | 0.3219 | +0.0226 | +0.1225 | +0.0845 | -0.0171 |
| logistic_regression | 1h | validation | 0.4792 | 0.3338 | -0.0185 | +0.1123 | +0.0833 | +0.0127 |
| logistic_regression | 1h | test | 0.4965 | 0.3284 | +0.0162 | +0.1121 | +0.0394 | -0.0479 |
| decision_tree_depth_2 | 1m | validation | 0.5943 | 0.2485 | +0.0000 | +0.0000 | +0.1154 | -0.0818 |
| decision_tree_depth_2 | 1m | test | 0.5304 | 0.2310 | +0.0000 | +0.0000 | +0.0936 | -0.0850 |
| decision_tree_depth_2 | 5m | validation | 0.4541 | 0.3603 | +0.1327 | +0.1981 | +0.1269 | +0.0338 |
| decision_tree_depth_2 | 5m | test | 0.3847 | 0.3034 | +0.1260 | +0.1664 | +0.0610 | -0.0199 |
| decision_tree_depth_2 | 15m | validation | 0.4253 | 0.3156 | -0.0110 | +0.1131 | +0.0602 | -0.0220 |
| decision_tree_depth_2 | 15m | test | 0.4430 | 0.3278 | +0.0162 | +0.1284 | +0.0782 | -0.0112 |
| decision_tree_depth_2 | 1h | validation | 0.4236 | 0.2763 | -0.0741 | +0.0548 | +0.0278 | -0.0448 |
| decision_tree_depth_2 | 1h | test | 0.4524 | 0.3090 | -0.0278 | +0.0927 | -0.0046 | -0.0673 |

Conclusion `logistic_regression` : résultat **mitigé**. Le modèle bat souvent la baseline majoritaire en macro F1 et bat souvent la baseline random en accuracy, mais les gains restent faibles et pas uniformes.

Conclusion `decision_tree_depth_2` : résultat **faible**. Le modèle est inconstant, parfois équivalent ou inférieur à la baseline majoritaire, et plusieurs tests label shuffle ne détruisent pas clairement sa performance.

## 4. Stabilité train / validation / test

| Modèle | Timeframe | Train accuracy | Validation accuracy | Test accuracy | Gap train-validation | Gap validation-test | Overfit warning |
|---|---:|---:|---:|---:|---:|---:|---|
| logistic_regression | 1m | 0.7056 | 0.6194 | 0.5504 | +0.0862 | +0.0690 | false |
| logistic_regression | 5m | 0.4459 | 0.4404 | 0.4040 | +0.0056 | +0.0364 | false |
| logistic_regression | 15m | 0.4412 | 0.4340 | 0.4493 | +0.0072 | -0.0153 | false |
| logistic_regression | 1h | 0.5039 | 0.4792 | 0.4965 | +0.0248 | -0.0174 | false |
| decision_tree_depth_2 | 1m | 0.7010 | 0.5943 | 0.5304 | +0.1068 | +0.0639 | true |
| decision_tree_depth_2 | 5m | 0.4347 | 0.4541 | 0.3847 | -0.0194 | +0.0694 | false |
| decision_tree_depth_2 | 15m | 0.4313 | 0.4253 | 0.4430 | +0.0060 | -0.0176 | false |
| decision_tree_depth_2 | 1h | 0.5126 | 0.4236 | 0.4524 | +0.0890 | -0.0288 | false |

La stabilité est partielle. `logistic_regression` est moins instable que `decision_tree_depth_2`, mais la dégradation entre validation et test reste visible sur plusieurs timeframes. `decision_tree_depth_2` porte un warning d'overfit sur `1m`.

## 5. Stabilité par timeframe

| Modèle | Meilleur timeframe test accuracy | Range accuracy | Range macro F1 | Warning concentration | Accuracy par timeframe |
|---|---:|---:|---:|---|---|
| logistic_regression | 1m | 0.1464 | 0.0818 | false | 1m=0.5504, 5m=0.4040, 15m=0.4493, 1h=0.4965 |
| decision_tree_depth_2 | 1m | 0.1457 | 0.0967 | false | 1m=0.5304, 5m=0.3847, 15m=0.4430, 1h=0.4524 |

Aucun modèle n'est signalé comme concentré sur un seul timeframe, mais les écarts entre timeframes restent élevés. La meilleure accuracy test est sur `1m` pour les deux modèles appris, alors que la macro F1 ne suit pas toujours la même lecture.

## 6. Label shuffle falsification

| Modèle | Timeframe | Split | Original accuracy | Shuffled accuracy | Delta accuracy | Delta macro F1 | No clear edge vs shuffled |
|---|---:|---|---:|---:|---:|---:|---|
| logistic_regression | 1m | validation | 0.6194 | 0.5943 | +0.0252 | +0.1708 | false |
| logistic_regression | 1m | test | 0.5504 | 0.5304 | +0.0201 | +0.1626 | false |
| logistic_regression | 5m | validation | 0.4404 | 0.3252 | +0.1152 | +0.2555 | false |
| logistic_regression | 5m | test | 0.4040 | 0.2636 | +0.1405 | +0.2565 | false |
| logistic_regression | 15m | validation | 0.4340 | 0.4132 | +0.0208 | +0.0454 | false |
| logistic_regression | 15m | test | 0.4493 | 0.4192 | +0.0301 | +0.0256 | false |
| logistic_regression | 1h | validation | 0.4792 | 0.4722 | +0.0069 | +0.0028 | false |
| logistic_regression | 1h | test | 0.4965 | 0.5104 | -0.0139 | -0.0230 | true |
| decision_tree_depth_2 | 1m | validation | 0.5943 | 0.5948 | -0.0005 | -0.0024 | true |
| decision_tree_depth_2 | 1m | test | 0.5304 | 0.5303 | +0.0000 | -0.0009 | true |
| decision_tree_depth_2 | 5m | validation | 0.4541 | 0.3214 | +0.1327 | +0.1981 | false |
| decision_tree_depth_2 | 5m | test | 0.3847 | 0.2587 | +0.1260 | +0.1664 | false |
| decision_tree_depth_2 | 15m | validation | 0.4253 | 0.4259 | -0.0006 | +0.0101 | true |
| decision_tree_depth_2 | 15m | test | 0.4430 | 0.4221 | +0.0208 | +0.0312 | false |
| decision_tree_depth_2 | 1h | validation | 0.4236 | 0.4421 | -0.0185 | -0.0340 | true |
| decision_tree_depth_2 | 1h | test | 0.4524 | 0.4826 | -0.0302 | -0.0225 | true |

Le shuffle des labels train dégrade certaines performances, notamment sur `5m`, mais pas systématiquement. Les cas sans edge clair sont : `1h.logistic_regression.test, 1m.decision_tree_depth_2.validation, 1m.decision_tree_depth_2.test, 15m.decision_tree_depth_2.validation, 1h.decision_tree_depth_2.validation, 1h.decision_tree_depth_2.test`. C'est une alerte forte : les résultats ne doivent pas être interprétés comme robustes.

## 7. Fuites / anti-leakage

Les scans V4.0 ne détectent pas de fuite feature : `feature_leakage_detected=false`, colonnes interdites présentes : `[]`.

Les scans de métriques interdites ne détectent pas de métrique trading interdite : `metric_forbidden_terms_detected=false`, termes présents : `[]`.

## 8. Limites de la fenêtre 90 jours

- 90 jours peuvent représenter un seul régime de marché.
- La fenêtre ne couvre pas assez de cycles de marché.
- Les événements extrêmes sont probablement trop peu nombreux pour juger la robustesse.
- Les résultats sont descriptifs et falsifiables, pas une validation d'usage trading.

## 9. Décision de direction

Option principale retenue : **A. Étendre à 1 an de données avant toute suite.**

Justification : les résultats actuels sont trop fragiles pour améliorer les modèles ou préparer un backtest research. La priorité est d'augmenter la diversité temporelle et de vérifier si les constats survivent hors fenêtre 90 jours.

Option secondaire retenue : **D. Préparer une validation walk-forward offline.**

Justification : après extension à 1 an, le walk-forward offline permettra de tester la stabilité temporelle sans exécuter de backtest et sans créer de signal.

Options non retenues maintenant : améliorer les features, revoir les labels, préparer un backtest research borné, ou geler toute piste ML. Ces options restent dépendantes d'une validation plus large sur 1 an.

## 10. Roadmap proposée

- **V4.2** : extension de la fenêtre publique OHLCV à 1 an, validation physique stricte, aucun modèle et aucun trading.
- **V4.3** : reconstruction research 1 an des features, labels et datasets avec schémas stricts et contrôles anti-leakage.
- **V4.4** : réexécution offline des baselines ML simples et de la robustesse/falsification sur 1 an, sans modèle persistant.
- **V4.5** : decision gate walk-forward offline et spécification éventuelle d'un backtest research très borné, sans exécution trading.

## 11. Interdits maintenus

- Pas de trading.
- Pas de paper live.
- Pas d'ordre.
- Pas de backtest validant une stratégie.
- Pas de claim de rentabilité.
- Pas de stratégie validée.
- Pas de modèle validé pour le trading.

V4.1 reste une décision research `pending_external_audit` avant validation externe.
