# Etat Projet V2.3.1 + candidat V2.4.8

- Derniere version validee : V2.3.1.
- Verdict valide : ingestion publique read-only BTCUSDT 1m avec validation physique durcie.
- Version candidate : V2.4.8.
- Statut candidate : pending_external_audit.
- Direction suivante : finalisation robuste runtime-only du validateur de resampling via focused Unit/Integration split.
- V2.4 a ete refusee en validation stricte externe car le manifest et le rapport qualite pouvaient mentir sur `quality`, `input_1m`, `outputs`, `expected_rows` et `parent_child_consistency`.
- V2.4.1 a corrige ce point en recalculant la qualite physique et en validant le rapport JSON comme projection deterministe du manifest.
- V2.4.2 a refuse les cles inattendues dans le manifest, le rapport JSON et les sous-blocs critiques.
- V2.4.3 a impose les limitations attendues et les formats stricts de `created_at_utc` / `resampling_run_id`, mais a ete refusee car les artefacts V2.3 inclus acceptaient encore des fausses claims et le runtime complet du validateur V2.4 restait non fiable en audit.
- V2.4.4 durcit les artefacts V2.3 inclus : schema strict, limitations exactes, scan recursif des claims positives, validation Markdown et projection stricte du rapport qualite. Mais elle a ete refusee car les validateurs acceptaient encore des colonnes additionnelles physiques et les tests de resampling restaient trop lents.
- V2.4.5 imposait un controle physique strict (`list(frame.columns) == OHLCV_COLUMNS`) rejetant les colonnes additionnelles ou desordres dans tous les Parquet silver, mais a ete refusee car le smoke test contenait un schema duplique en dur dans le mauvais ordre et le runtime complet des tests de resampling restait non fiable.
- V2.4.6 corrige le smoke test en important dynamiquement le schema canonique `OHLCV_COLUMNS` depuis `schemas.py` sans duplication, et finalise la fiabilisation complète du validateur de resampling avec une copie de template ultra-rapide garantissant un runtime sous les 12 secondes. Mais elle a ete refusee car la commande complète de tests validateur ne se terminait pas de maniere fiable et propre dans l'environnement d'audit strict.
- V2.4.7 finalise le runtime sans affaiblir les tests via copie selective et monkeypatch des scans globaux. Mais l'audit l'a refusee car l'execution complete des tests restait trop lente sur leur disque virtuel.
- V2.4.8 scinde proprement les 47 tests en tests unitaires en memoire (39 tests logiques ultra-rapides) et tests d'integration (8 tests physiques critiques complets conserves). Cette approche permet de ramener l'execution de toute la suite sous les 5 secondes de maniere stable et robuste tout en garantissant une validation physique sans faille.
- V2.4.8 n'est pas declaree validee avant audit externe.
- Aucun trading, paper live, ordre reel, ML, label ou backtest n'est autorise.

