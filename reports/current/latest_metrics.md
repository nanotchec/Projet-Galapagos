# Latest Metrics V2.3.1 + candidat V2.4.3

- Derniere version validee : V2.3.1.
- Version candidate : V2.4.3.
- Statut : pending_external_audit.
- Raw public archive BTCUSDT 1m 2024-01-15 : cree.
- Silver OHLCV Parquet : cree, sans colonne `normalized_file_sha256`.
- Sorties V2.4 attendues : 5m = 288 lignes, 15m = 96 lignes, 1h = 24 lignes.
- V2.4.1 durcit la coherence physique manifest/report : le bloc `quality` est compare aux donnees recalculees et le rapport JSON doit correspondre au manifest.
- V2.4.2 ajoute le schema strict : aucune cle inattendue n'est acceptee dans le manifest, le rapport JSON ou les sous-blocs critiques.
- V2.4.3 ajoute les limitations attendues exactes, le scan de claims positives dans les JSON, la validation stricte de `created_at_utc` et du `resampling_run_id`, et la stabilisation runtime du fichier complet de tests validateur.
- V2.4.3 reste data-only, sans cle API, sans endpoint prive, sans trading, sans paper live, sans ordre, sans ML, sans labels et sans backtest.
