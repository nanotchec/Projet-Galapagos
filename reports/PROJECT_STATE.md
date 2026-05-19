# Etat Projet V2.3.1 + candidat V2.4.1

- Derniere version validee : V2.3.1.
- Verdict valide : ingestion publique read-only BTCUSDT 1m avec validation physique durcie.
- Version candidate : V2.4.1.
- Statut candidate : pending_external_audit.
- Direction suivante : durcissement de coherence physique manifest/report du resampling OHLCV.
- V2.4 a ete refusee en validation stricte externe car le manifest et le rapport qualite pouvaient mentir sur `quality`, `input_1m`, `outputs`, `expected_rows` et `parent_child_consistency`.
- V2.4.1 corrige ce point en recalculant la qualite physique et en validant le rapport JSON comme projection deterministe du manifest.
- V2.4.1 n'est pas declaree validee avant audit externe.
- Aucun trading, paper live, ordre reel, ML, label ou backtest n'est autorise.
