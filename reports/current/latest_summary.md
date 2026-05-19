# Latest Summary V2.4.4 candidate

V2.3.1 est validee pour le scope data/research offline : ingestion publique read-only BTCUSDT 1m, raw ZIP reel, silver Parquet normalise, validation physique, lineage raw vers silver et absence de trading/ML/labels/backtest.

V2.4 a ajoute le resampling OHLCV 1m vers 5m, 15m et 1h, puis les sous-versions V2.4.1 a V2.4.3 ont durci la coherence manifest/report, les schemas stricts, les limitations, les claims et les formats temporels. V2.4.3 a ete refusee car les artefacts V2.3 inclus acceptaient encore des fausses claims et parce que le runtime complet du validateur V2.4 devait etre finalise. V2.4.4 est candidate et reste en attente d'audit externe. Elle applique le durcissement global aux artefacts V2.3 inclus et finalise la fixture du validateur V2.4. V2.4.4 ne valide aucune strategie, ne produit aucun signal, ne lance aucun ML, ne cree aucun label, ne fait aucun backtest et ne permet aucun ordre reel ni paper live.
