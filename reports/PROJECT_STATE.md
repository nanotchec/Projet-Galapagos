# État du Projet : V3.1.10 validée + candidat V3.2.1

- **Dernière version validée** : V3.1.10.
- **Versions antérieures validées** : V3.0, V2.9.1, V2.8.4, V2.7.2, V2.6.2, V2.5.2, V2.4.8, V2.3.1.
- **Version candidate** : V3.2.1.
- **Statut candidate** : `pending_external_audit`.
- **Direction suivante** : multi-day offline supervised dataset assembly preview.

## Candidat V3.2.1

- V3.2.1 assemble un dataset supervisé offline multi-day à partir des features causales V3.0 et des labels forward V3.1.
- Inputs autorisés : features V3.0 sous `data/research/v3_0/features/ohlcv` et labels V3.1 sous `data/research/v3_1/labels/forward_returns`.
- Outputs : datasets et splits isolés sous `data/research/v3_2/datasets/offline_supervised`.
- Fenêtre : 2024-01-15 à 2024-01-21 inclus.
- Row counts attendus : 1m `10080`, 5m `2016`, 15m `672`, 1h `168`.
- Splits temporels : train 60 %, validation 20 %, test 20 %, sans shuffle.
- Les features sources V3.0 et labels sources V3.1 ne sont pas modifiés par V3.2.
- V3.2 a été refusée en strict car un artefact `reports/backtests/not_named_backtest_report.json` a été accepté.
- V3.2.1 renforce le garde-fou et refuse tout contenu sous `reports/backtests` (fichier, dossier vide ou fichier imbriqué).
- V3.2 ne produit aucun modèle ML, aucun backtest, aucune stratégie, aucun signal de trading et aucun ordre.
- V3.2 reste candidate `pending_external_audit`.

## Clause De Sécurité

- Aucun trading réel.
- Aucun paper live.
- Aucun ordre.
- Aucun signal de trading.
- Aucun backtest.
- Aucune stratégie.
- Aucune API privée.
- Aucune clé API.
- Aucun ML V3.2.
- Aucun modèle ML V3.2.
- V3.2 reste non validée avant audit externe.
