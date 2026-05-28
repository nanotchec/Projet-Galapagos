# V9.25 - AggTrades Post-V9 Remaining Window Completion Campaign

## Resume executif
- Decision V9.25 : `aggtrades_post_v9_remaining_window_collection_failed_storage`.
- Justification : L'espace disque libre est sous le seuil minimal de 60 GB ou la reserve de collecte journaliere V9.25; la campagne est arretee.
- Recommandation suivante : V9.26 - Storage Cleanup / Compression Review.
- V9.25 reste data-only : aucun label, dataset supervise, ML, walk-forward, backtest, strategie ou signal actionnable.
- Fenetre collectee : `2024-12-08` -> `2026-05-05`.
- Couverture locale finale : `2024-05-05` -> `2025-02-02`.
- Couverture complete atteinte : `False`.

## Preflight
- Espace disque libre : `63976546304` bytes.
- Statut stockage : `failed_storage`.
- Warning stockage : `free_disk_below_60gb_stop_before_collection`.
- Couverture locale precedente : `2024-05-05` -> `2024-12-07`.

## Lots internes
- Lots planifies/executés/reussis/echoues : `6` / `1` / `0` / `1`.
- Jours demandes/tentes/telecharges/normalises/valides : `90` / `0` / `57` / `57` / `57`.
- Jours echoues/quarantine/skips : `33` / `0` / `57`.
- Lignes nouvelles/cumulees : `104714234` / `409180982`.
- Raw bytes nouveaux/cumules : `1442302098` / `5287147417`.
- Silver bytes nouveaux/cumules : `2760944662` / `10241505826`.
- Runtime total secondes : `99.152`.
- Alertes aggregate_trade_id : `0`.
- Alertes timestamps : `0`.

## Source et garde-fous
- Source : archive publique Binance `data.binance.vision`, marche spot, symbole BTCUSDT.
- Aucun compte, aucune cle API, aucun endpoint prive, aucun client exchange authentifie, aucun websocket live.
- Aucune API privee.
- Aucun trading reel.
- Aucun paper live.
- Aucun ordre.
- Aucun backtest execute.
- Aucun walk-forward.
- Aucune strategie.
- Aucun signal actionnable.
- Aucun modele persistant.
- Aucun sidecar et aucune empreinte ZIP.
