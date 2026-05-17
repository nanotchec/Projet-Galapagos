# Plan donnees historiques longues

Objectif research :
- BTC 4h sur 3 a 5 ans pour tester les regimes.
- BTC 1h sur 2 a 3 ans pour affiner les sorties.
- BTC 5m ou 1m pour simuler TP/SL intrabar.

La timeframe de signal reste separee de la timeframe d'execution. Un signal 4h
peut etre evalue avec une simulation d'execution 1m/5m, sans fuite temporelle.

Sources possibles :
- Binance public data / data.binance.vision.
- CCXT avec fetch pagine si le provider le permet.
- Kraken historique si disponible.
- Bybit klines.
- CoinGlass uniquement si cle API fournie.

V1.11 ne lance aucun gros telechargement. Les scripts readiness indiquent ce qui
existe localement et ce qui manque.
