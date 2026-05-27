# Refined Research Decision Gate V9.4

## Resume executif

Decision research : `backtest_not_justified_refine_labels`.

V9.4 analyse les resultats V9.2 et V9.3 de la chaine refined OHLCV + trades. Le verdict est conservateur : aucun backtest research n'est justifie maintenant. Les resultats restent descriptifs, instables par endroits et trop proches des labels melanges dans plusieurs cas.

## Entrees

- Derniere version validee : `V9.0_to_V9.3.2`.
- Fenetre : `2023-03-25` -> `2024-03-24` (`366` jours).
- Target : `up_down_flat_h1`.
- Modeles : `['majority_class_baseline', 'random_seeded_baseline', 'logistic_regression', 'decision_tree_depth_2']`.
- Timeframes : `['1m', '5m', '15m', '1h']`.
- Selected features : `18`.

## Diagnostic V9.2 static split

V9.2 fournit des metriques offline descriptives sur split temporel simple. Ces metriques ne sont pas un backtest et ne produisent aucun signal actionnable.

## Diagnostic V9.3 walk-forward strict

- Entrees de concentration fold/timeframe : `9`.
- Entrees instables : `7`.
- Cas trop proches des labels melanges : `21`.
- Fuite feature detectee : `False`.
- Metriques interdites detectees : `False`.

## Comparaison aux baselines

- Gains walk-forward clairs : `3`.
- Cas walk-forward mitiges : `5`.
- Politique : `accuracy and macro_f1 above majority and random baselines by more than 0.01`.

Les gains ne sont pas assez nets et generalises pour justifier un backtest.

## Label shuffle falsification

La falsification n'est pas propre : `21` cas restent trop proches des labels melanges. Cela pointe plutot vers un probleme de definition ou de bruit des labels que vers un edge exploitable.

## Static split vs walk-forward

La comparaison V9.2/V9.3 est descriptive uniquement. Les deux designs ne sont pas equivalents : `True`.

## Decision

Justification : Le backtest n'est pas justifie : 21 cas restent trop proches des labels melanges, avec 9 entrees de concentration et seulement 3 gains walk-forward clairs contre les baselines.

Niveau de confiance : `medium_high`.

Prochaine etape recommandee : V9.5 - Alternative Label Design Audit avant tout backtest research.

Etape secondaire : Revenir aux features seulement si le redesign de labels ne reduit pas le bruit.

## Interdits maintenus

V9.4 ne valide aucune strategie, ne produit aucun backtest, ne produit aucun signal actionnable, ne produit aucun ordre, n'autorise aucun paper live et n'autorise aucun trading reel. Aucun modele persistant, aucune API privee et aucune cle API ne sont utilises.
