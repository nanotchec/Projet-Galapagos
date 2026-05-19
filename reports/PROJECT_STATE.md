# Etat Projet V2.3.1 + candidat V2.4.4

- Derniere version validee : V2.3.1.
- Verdict valide : ingestion publique read-only BTCUSDT 1m avec validation physique durcie.
- Version candidate : V2.4.4.
- Statut candidate : pending_external_audit.
- Direction suivante : durcissement global des claims des artefacts inclus et finalisation runtime du validateur OHLCV.
- V2.4 a ete refusee en validation stricte externe car le manifest et le rapport qualite pouvaient mentir sur `quality`, `input_1m`, `outputs`, `expected_rows` et `parent_child_consistency`.
- V2.4.1 a corrige ce point en recalculant la qualite physique et en validant le rapport JSON comme projection deterministe du manifest.
- V2.4.2 a refuse les cles inattendues dans le manifest, le rapport JSON et les sous-blocs critiques.
- V2.4.3 a impose les limitations attendues et les formats stricts de `created_at_utc` / `resampling_run_id`, mais a ete refusee car les artefacts V2.3 inclus acceptaient encore des fausses claims et le runtime complet du validateur V2.4 restait non fiable en audit.
- V2.4.4 durcit les artefacts V2.3 inclus : schema strict, limitations exactes, scan recursif des claims positives, validation Markdown et projection stricte du rapport qualite.
- V2.4.4 finalise la fixture du validateur V2.4 avec un projet template copie explicitement via `valid_v2_4_project`.
- V2.4.4 n'est pas declaree validee avant audit externe.
- Aucun trading, paper live, ordre reel, ML, label ou backtest n'est autorise.
