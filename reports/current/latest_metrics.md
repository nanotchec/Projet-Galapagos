# Latest Metrics V2.3.1 + candidat V2.4.4

- Derniere version validee : V2.3.1.
- Version candidate : V2.4.4.
- Statut : pending_external_audit.
- Raw public archive BTCUSDT 1m 2024-01-15 : cree.
- Silver OHLCV Parquet : cree, sans colonne `normalized_file_sha256`.
- Sorties V2.4 attendues : 5m = 288 lignes, 15m = 96 lignes, 1h = 24 lignes.
- V2.4.4 durcit aussi les artefacts V2.3 inclus dans le ZIP : manifest strict, rapport qualite strict, limitations exactes et claims positives interdites dans JSON/Markdown.
- Le fichier complet `tests/validation/test_ohlcv_resampling_v2_4_validator.py` utilise une fixture explicite `valid_v2_4_project` basee sur un template copie et termine normalement.
- V2.4.4 reste data-only, sans cle API, sans endpoint prive, sans trading, sans paper live, sans ordre, sans ML, sans labels et sans backtest.
