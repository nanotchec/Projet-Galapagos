# Research decision gate V8.6

## Executive summary

- Verdict research : `interessant_mais_mitige_non_concluant`.
- V8.6 ne produit aucune conclusion trading.
- OHLCV + aggTrades 1 an reste interessant pour la recherche, mais les resultats doivent rester prudents et descriptifs.
- Recommandation principale : D. Preparer une validation walk-forward offline plus stricte.
- Recommandation secondaire : B. Ameliorer/refactoriser les features OHLCV + trades.

## Entrees analysees

- V8.4 : dataset supervise offline OHLCV + aggTrades 1 an.
- V8.5 : scores ML offline `research_*` et metriques descriptives.
- Fenetre : `2023-03-25` -> `2024-03-24`.
- Total jours : `366`.
- Feature columns count : `71`.
- Target : `up_down_flat_h1`.
- Modeles : majority_class_baseline, random_seeded_baseline, logistic_regression, decision_tree_depth_2.

## Comparaison aux references

- Les comparaisons avec V8.0, V7.4, V6.2 et V5.4 sont descriptives.
- Les fenetres et sources peuvent differer : elles ne sont pas directement comparables.
- Aucune superiorite trading n'est conclue.

## Baselines

- Cas appris positifs vs baselines : `9`.
- Verdict : `mitige`.

## Stabilite train / validation / test

- Warnings overfit : `4`.
- Verdict : `instable`.

## Stabilite par timeframe

- Warnings concentration timeframe : `4`.
- Verdict : `concentration_possible`.

## Stabilite walk-forward

- Les metriques walk-forward sont descriptives et ne constituent pas un backtest.
- Verdict : `instable_ou_concentre`.

## Label shuffle falsification

- Seed : `123`.
- Cas sans edge clair vs labels melanges : `5`.
- Verdict : `alerte_si_proche_shuffle`.

## Fuites / anti-leakage

- Feature leakage detectee : `False`.
- Metriques interdites detectees : `False`.

## Limites

- La fenetre d'environ 1 an reste limitee et ne couvre pas tous les regimes de marche disponibles dans V5.0.
- Les comparaisons avec V8.0/V7.4/V6.2/V5.4 sont descriptives et souvent non directement comparables.
- Aucune metrique de trading interdite ou mesure d'execution n'est calculee.
- Les resultats ne doivent pas etre transformes en strategie ou en signal de trading.

## Roadmap proposee

- V8.7 - Walk-forward offline stricte OHLCV + trades 1 an
- V8.8 - Diagnostics labels et raffinement features OHLCV + trades
- V8.9 - Dataset raffine OHLCV + trades
- V9.0 - ML offline raffine et falsification
- V9.1 - Research decision gate avant toute consideration de backtest

## Interdits maintenus

- Pas de trading.
- Pas de paper live.
- Pas d'ordre.
- Pas de backtest validant une strategie.
- Pas de strategie.
- Pas de signal de trading.
- Pas de modele persistant.
- Pas de claim de rentabilite.
