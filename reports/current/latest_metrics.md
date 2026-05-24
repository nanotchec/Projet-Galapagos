# Latest Metrics

- Dernière version validée : `V4.6`
- Candidate : `V4.7`
- Statut : `pending_external_audit`
- Direction : 1-year ML robustness and falsification audit

## Inputs V4.7

- Source dataset : dataset supervisé offline V4.5 validé.
- Source ML : scores et métriques offline V4.6 validés.
- Fenêtre : `2024-01-01` à `2024-12-31` inclus.
- Timeframes : `1m`, `5m`, `15m`, `1h`.

## Analyses

- baseline_delta : présent.
- split_stability : présent.
- timeframe_stability : présent.
- label_shuffle_falsification : présent, seed `123`, labels train uniquement.
- feature_leakage_scan : `False`.
- metric_forbidden_scan : `False`.

## Input Scores V4.6

- `1m` : `2108036` lignes.
- `5m` : `421508` lignes.
- `15m` : `140420` lignes.
- `1h` : `35012` lignes.

## Findings

- robust_edge_claimed : `false`
- strategy_validated : `false`
- backtest_performed : `false`
- actionable_signal_produced : `false`
- warnings : `8`

## Safety

- Audit de robustesse offline V4.7 uniquement.
- Aucun modèle persistant.
- Aucun trading réel.
- Aucun paper live.
- Aucun ordre.
- Aucun backtest.
- Aucune stratégie.
- Aucun signal de trading.
