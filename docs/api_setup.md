# API setup

Les cles sont optionnelles en V1.11 et doivent venir de variables
d'environnement ou d'un fichier `.env` non commite.

Variables supportees :
- `COINGLASS_API_KEY` : donnees crypto agregees, liquidations, ETF flows selon plan.
- `FRED_API_KEY` : donnees macro US futures.
- `BYBIT_API_KEY` / `BYBIT_API_SECRET` : non requis pour certains endpoints publics.
- `BINANCE_API_KEY` / `BINANCE_API_SECRET` : non requis pour certains endpoints publics.

Regles :
- Ne jamais commiter `.env`.
- Ne jamais logguer les cles.
- Si aucune cle n'est disponible, les scripts doivent signaler `requires_api_key`
  ou `unavailable` sans faire echouer toute la release.
- CoinGlass et FRED ne doivent pas etre appeles sans cle explicite.

## Derivatives public vs API-key data

Binance Futures et Bybit V5 exposent plusieurs endpoints publics utilisables sans cle pour la recherche BTC : funding, certains open interest, premium/mark/index snapshots et quelques ratios. Ces donnees sont utilisees par defaut en mode research et doivent toujours conserver un `available_timestamp` causal.

CoinGlass reste optionnel et probablement payant. Il peut debloquer liquidations historiques, open interest multi-exchange, funding agrege, ETF flows et ratios plus complets. Sans `COINGLASS_API_KEY`, Galapagos marque ces jeux comme `requires_api_key` ou `unavailable` et ne les appelle pas.

Les cles Binance/Bybit restent optionnelles pour V1.13. Les scripts ne doivent jamais afficher les secrets; ils indiquent seulement `configured` ou `missing`.

## Derivatives public vs API-key data V1.14

V1.14 continue d'exploiter Binance/Bybit publics avant tout achat. Les donnees publiques couvrent surtout funding, une partie de l'open interest, certains ratios taker/long-short et des snapshots premium.

Les liquidations historiques completes, l'OI multi-exchange agrege, les flux ETF BTC et certains historiques basis/premium restent plutot du domaine provider payant. CoinGlass, CryptoQuant, Kaiko, Glassnode, CCData, Amberdata, Laevitas et Coinalyze restent en matrice de decision, sans achat automatique.

Les prix exacts ne sont pas inventes: ils doivent etre verifies manuellement avant toute decision.
