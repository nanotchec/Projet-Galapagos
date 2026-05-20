# Résumé courant — V2.9 candidate

La dernière version validée est **V2.8.4**. La version candidate est **V2.9**, en statut `pending_external_audit`.

V2.9 ne passe pas au backtest. Elle élargit uniquement les données marché publiques réelles avant toute conclusion robuste : BTCUSDT spot 1m sur Binance public archive, du 2024-01-15 au 2024-01-21 inclus.

Les sorties V2.9 sont isolées sous `data/research/v2_9/silver/ohlcv` avec row counts attendus 1m `10080`, 5m `2016`, 15m `672`, 1h `168`. Les artefacts V2.3 à V2.8.4 restent inchangés.

Le système reste data/research/offline : aucun trading réel, aucun paper live, aucun ordre, aucun signal de trading, aucun backtest, aucune stratégie, aucun modèle ML V2.9, aucune API privée et aucune clé API.
