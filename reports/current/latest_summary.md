# Latest Summary V2.4.1 candidate

V2.3.1 est validee pour le scope data/research offline : ingestion publique read-only BTCUSDT 1m, raw ZIP reel, silver Parquet normalise, validation physique, lineage raw vers silver et absence de trading/ML/labels/backtest.

V2.4 a ete refusee en strict parce que le manifest et le rapport qualite pouvaient declarer des valeurs incoherentes avec les fichiers Parquet physiques. V2.4.1 est candidate et reste en attente d'audit externe. Elle durcit la validation du bloc `quality` contre les donnees recalculees, puis valide le rapport JSON comme projection deterministe du manifest. V2.4.1 ne valide aucune strategie, ne produit aucun signal, ne lance aucun ML, ne cree aucun label, ne fait aucun backtest et ne permet aucun ordre reel ni paper live.
