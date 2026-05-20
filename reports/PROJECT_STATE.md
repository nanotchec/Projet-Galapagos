# État du Projet : V2.8.4 validée + candidat V2.9.1

- **Dernière version validée** : V2.8.4 (Offline ML Research runtime/smoke finalisé).
- **Versions antérieures validées** : V2.7.2, V2.6.2, V2.5.2, V2.4.8, V2.3.1.
- **Version candidate** : V2.9.1.
- **Statut candidate** : `pending_external_audit`.
- **Direction suivante** : finalisation runtime du validateur multi-day public market data.
- **Refus audit V2.9** : V2.9 a été refusée en strict uniquement parce que le fichier complet de tests du validateur V2.9 était trop lent.

## Candidat V2.9.1

- V2.9 étend uniquement les données marché publiques BTCUSDT sur une fenêtre fixe de 7 jours.
- V2.9.1 ne change pas le périmètre data ; elle finalise le runtime des tests du validateur V2.9.
- Source : Binance public archive, spot, BTCUSDT, klines 1m.
- Fenêtre : 2024-01-15 à 2024-01-21 inclus.
- Row counts attendus : 1m `10080`, 5m `2016`, 15m `672`, 1h `168`.
- Les sorties sont isolées sous `data/research/v2_9/silver/ohlcv`.
- Les artefacts validés V2.3 à V2.8.4 ne sont pas écrasés.
- V2.9 ne produit aucune feature, aucun label, aucun dataset ML, aucun modèle ML, aucun backtest, aucune stratégie et aucun ordre.
- V2.9.1 reste candidate `pending_external_audit`.

## Clause De Sécurité

- Aucun trading réel.
- Aucun paper live.
- Aucun ordre.
- Aucun signal de trading.
- Aucun backtest.
- Aucune stratégie.
- Aucune API privée.
- Aucune clé API.
- Aucun modèle ML V2.9.
- V2.9.1 reste non validée avant audit externe.
