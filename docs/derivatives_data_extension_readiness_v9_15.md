# V9.15 - Data Extension Readiness / Derivatives Feature Candidate

## Resume executif
- Decision V9.15 : `derivatives_readiness_not_compatible_with_v9_window`.
- Justification : Funding and open interest are present only partially in local reports and do not overlap the validated V9 window 2023-03-25 to 2024-03-24.
- Recommandation suivante : V9.16 - Derivatives Window Extension Diagnostic.
- Feature candidate derivatives creee : `False`.
- V9.15 est un diagnostic readiness offline; aucune donnee nouvelle n'est telechargee.
- Aucun trading, aucun paper live, aucun ordre, aucun backtest, aucun walk-forward, aucune strategie, aucun signal actionnable.

## Donnees derivatives locales
- Rapports derivatives detectes : `23`.
- Zips futures 4h locaux : `52`.
- Fichiers silver derivatives : `0`.
- Fichiers gold derivatives features : `0`.

## Funding readiness
- Exchanges : `['binance', 'bybit']`.
- Lignes disponibles : `2390`.
- Couverture combinee : `2024-05-05 16:00:00+00:00` -> `2026-05-05 08:00:00+00:00`.
- Compatible fenetre V9 : `False`.
- Decision readiness : `not_ready_missing_coverage`.

## Open interest readiness
- Exchanges : `['binance', 'bybit']`.
- Lignes disponibles : `200`.
- Couverture combinee : `2026-04-02 08:00:00+00:00` -> `2026-05-05 12:00:00+00:00`.
- Compatible fenetre V9 : `False`.
- Decision readiness : `not_ready_missing_coverage`.

## Compatibilite chaine V9
- Fenetre V9 : `2023-03-25_2024-03-24`.
- Timeframes V9 : `['1m', '5m', '15m', '1h']`.
- Timeframe derivatives local rapporte : `4h`.
- Compatible chaine V9 actuelle : `False`.
- Couverture attendue apres alignement : 0 for current V9 window when relying on V1.14 funding/OI reports.

## Feature candidate
- Creee : `False`.
- Raison : No feature candidate was created because funding/OI coverage in local V1.14 reports does not overlap the V9 window.

## Interdits maintenus
- Aucun trading reel.
- Aucun paper live.
- Aucun ordre.
- Aucun backtest execute.
- Aucun walk-forward.
- Aucune strategie.
- Aucun signal actionnable.
- Aucun modele persistant.
- Aucune API privee.
- Aucune cle API.
- Aucun reseau et aucun telechargement de nouvelles donnees.
- Aucun sidecar et aucune empreinte ZIP.
