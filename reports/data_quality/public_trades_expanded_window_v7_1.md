# Public Trades Historical Window Expansion V7.1

## Objectif

V7.1 etend uniquement l'ingestion data-only de trades publics Binance `aggTrades` pour `BTCUSDT` spot.

## Fenetre

- Fenetre : `2023-03-25` -> `2023-04-23`.
- Total jours : `30`.
- Meme fenetre que V5.0 : `False`.
- Raison : bounded 30-day V7.1 aggTrades expansion after the one-day V7.0 ingestion preview.

## Raw inventory

- `2023-03-25` : `817141` lignes, `11729875` octets, checksum `5bba0a4fa33fb258d19fb6e8ab414f15ae15dc5ecb5f3a2a2e0c31a403193a85`
- `2023-03-26` : `786235` lignes, `11269189` octets, checksum `ab177c708ac32b540f8d88c14d1954c6298ceb9cff3a4e5c97251df526f8f7ad`
- `2023-03-27` : `1145084` lignes, `16461910` octets, checksum `e90b09c1601e3e497942430ae0bda274d0355c55055afee4217d3141b27d9ce2`
- `2023-03-28` : `1117559` lignes, `15965990` octets, checksum `674588d96bf5bd6c724c547f2033ce865310b16a91be54c73eb55f09c5eca4c3`
- `2023-03-29` : `1239862` lignes, `17658734` octets, checksum `fb50d7b630128bf1325027612f70a26577ea81c633bb022be6a97a1c174be55e`
- `2023-03-30` : `1384715` lignes, `19616032` octets, checksum `7a9534f90815a50d2e1751d964f8c24dd4d6c05f29807971a1c51889f23db8ff`
- `2023-03-31` : `1185212` lignes, `16787611` octets, checksum `aa55734db1bbc9c0b7bdd9e3a715d2c83f56dd9834b36c6bcaffb5ff6631fbb1`
- `2023-04-01` : `651525` lignes, `9325835` octets, checksum `cfb57330d78e1810f572af04fd5a7899d8bec6b65850ddb0880e3d7956c2eb94`
- `2023-04-02` : `741918` lignes, `10547181` octets, checksum `0f4d2cb9ae9ffde947542f875fcdf33904396359ae0a78382d5aed9d656f69bc`
- `2023-04-03` : `1287095` lignes, `18252206` octets, checksum `6e210516ec22fd45bcb4ddcfaa3c0a1d9dddd5d1c03fbaddab6486ef670607c4`
- `2023-04-04` : `862796` lignes, `12388279` octets, checksum `6a3d2b453ba9a546b468fb8a306ba68aa96f04d09e4be542f548a611b5c3419d`
- `2023-04-05` : `981428` lignes, `14044361` octets, checksum `360c3f8de9bb9bd307893a13f0a45c27f083d816634449f4d8eb223a5ac6e38b`
- `2023-04-06` : `741248` lignes, `10624252` octets, checksum `370610301ada89afe96bb553de993ec112908d207636de12ec4f2bad21058f56`
- `2023-04-07` : `524712` lignes, `7542531` octets, checksum `d995d9186ed374b334c31b5eb89fc92285d7fcaa4f6b32541b693f9b1f434b24`
- `2023-04-08` : `518781` lignes, `7407818` octets, checksum `733e3d95b3b2d1444a87f5ce442f21e66c34930ee44bc8de9bb0f11c68951655`
- `2023-04-09` : `621970` lignes, `8879695` octets, checksum `8cc285e350d43f4acee57cffc1beadafeada6f5a6d97d484eaadd7ce514e30bd`
- `2023-04-10` : `999793` lignes, `14273535` octets, checksum `20c4e645ec5641eb380fb30c3a6bf056b6addc7e0ec411b67d29c2404bd060db`
- `2023-04-11` : `1061109` lignes, `15187533` octets, checksum `7cbd36ed85445b3c97800d2fc5d0913af5b1a79bdc3bedf53efe504b051b4ad3`
- `2023-04-12` : `993870` lignes, `14264037` octets, checksum `9b078b720f86210d9a5537980cb21dc63a3837f79ecc793a7e28702925b47f7a`
- `2023-04-13` : `837590` lignes, `12024296` octets, checksum `3389eb98f89c91a3cabafce4f183f5cfdc0f138f9e287cf57f57efc4159d509d`
- `2023-04-14` : `1193393` lignes, `17137301` octets, checksum `fadf1ba6b92d4f87693ce65cd1f5ef8cc066a4931d7cc79be5ec43922e4296e4`
- `2023-04-15` : `601021` lignes, `8656948` octets, checksum `4235dae6028be0b7d8c5d8c137d587dfb2dc1987f90d6819018a5806529c7671`
- `2023-04-16` : `575262` lignes, `8298230` octets, checksum `3200b85d3cf0e44194e0436ef9729166e88c4b53d58073a8703a96d340e46b99`
- `2023-04-17` : `880114` lignes, `12602591` octets, checksum `1e0f719a83587cc39bb51df5b2f13c7293f7479355dce276121841afd4b33281`
- `2023-04-18` : `893647` lignes, `12924764` octets, checksum `7627a9aefbaa6a89cdb0da4ad3c69c2bdcae4c321f1e55e9a932e516b2e02f7f`
- `2023-04-19` : `1360410` lignes, `19537702` octets, checksum `156988cefcf5ea416071a7a4d0be63cee5cea8a928ed0ad29cf1c1565ec2b532`
- `2023-04-20` : `1136546` lignes, `16353102` octets, checksum `b79f1966c09773d1e7cd5961ac93c323a2c968ce74559f41bafdd9934eb32a96`
- `2023-04-21` : `1163429` lignes, `16670447` octets, checksum `6d15128a9df62e586474ead21fe7d02a2b8f4ddc16dbb58f9df90d0d8e00f65c`
- `2023-04-22` : `695126` lignes, `9931854` octets, checksum `b535241a2945c916c811ea3d89861f8e35ecfcf7a85b9aa33de7cbaaf5088e44`
- `2023-04-23` : `709690` lignes, `10147911` octets, checksum `1145b329a4d16c2c7f3a18b856ffe5818af2c16873c7e4754013156b920f62bc`

## Outputs partitionnes

- Rows totales : `27708281`.
- Bytes totaux : `1044554543`.
- Format : `partitioned_parquet`.

- `2023-03-25` : `data/research/v7_1/trades/aggTrades/source=binance_archive/market_type=spot/symbol=BTCUSDT/window=2023-03-25_2023-04-23/date=2023-03-25/agg_trades.parquet`, `817141` lignes, checksum `a94f71fad9a409a87e51954708bf8cc9e9ce4fc530cda472eedcb91cc3d60d63`
- `2023-03-26` : `data/research/v7_1/trades/aggTrades/source=binance_archive/market_type=spot/symbol=BTCUSDT/window=2023-03-25_2023-04-23/date=2023-03-26/agg_trades.parquet`, `786235` lignes, checksum `3bdec86305a4e80e85e19cda316371f7eefe9ba039b8147356bc01c29780fadc`
- `2023-03-27` : `data/research/v7_1/trades/aggTrades/source=binance_archive/market_type=spot/symbol=BTCUSDT/window=2023-03-25_2023-04-23/date=2023-03-27/agg_trades.parquet`, `1145084` lignes, checksum `95240f9d9c7eb2924fb0f534f8f6f30c81d8a607ea2ec7a2079cbc2c969c9487`
- `2023-03-28` : `data/research/v7_1/trades/aggTrades/source=binance_archive/market_type=spot/symbol=BTCUSDT/window=2023-03-25_2023-04-23/date=2023-03-28/agg_trades.parquet`, `1117559` lignes, checksum `9b43b06c8c2e4824d480055f9cf3539e28627d23c5679fc05c25ee8cec10fa55`
- `2023-03-29` : `data/research/v7_1/trades/aggTrades/source=binance_archive/market_type=spot/symbol=BTCUSDT/window=2023-03-25_2023-04-23/date=2023-03-29/agg_trades.parquet`, `1239862` lignes, checksum `c46a85110902e8e2227a87f76dcbd020ad61f94c680ded865cf3b04cd15421ce`
- `2023-03-30` : `data/research/v7_1/trades/aggTrades/source=binance_archive/market_type=spot/symbol=BTCUSDT/window=2023-03-25_2023-04-23/date=2023-03-30/agg_trades.parquet`, `1384715` lignes, checksum `f0d724809fd337360b199b86141d51801ff34699242517947d31145cc6dd6914`
- `2023-03-31` : `data/research/v7_1/trades/aggTrades/source=binance_archive/market_type=spot/symbol=BTCUSDT/window=2023-03-25_2023-04-23/date=2023-03-31/agg_trades.parquet`, `1185212` lignes, checksum `0511bd39abea0de507082d1189dc1195cdde8ccc20f02528608339678a2ada63`
- `2023-04-01` : `data/research/v7_1/trades/aggTrades/source=binance_archive/market_type=spot/symbol=BTCUSDT/window=2023-03-25_2023-04-23/date=2023-04-01/agg_trades.parquet`, `651525` lignes, checksum `b2e83f966959675e418a30d4fcb41a71a5fdd2501de27afb4cb527d9d1b9b2e0`
- `2023-04-02` : `data/research/v7_1/trades/aggTrades/source=binance_archive/market_type=spot/symbol=BTCUSDT/window=2023-03-25_2023-04-23/date=2023-04-02/agg_trades.parquet`, `741918` lignes, checksum `b0c1600cf00ae8db6196e3603a0965ca4a9e003d284e21da10af0ffbc5d708f9`
- `2023-04-03` : `data/research/v7_1/trades/aggTrades/source=binance_archive/market_type=spot/symbol=BTCUSDT/window=2023-03-25_2023-04-23/date=2023-04-03/agg_trades.parquet`, `1287095` lignes, checksum `845736c987509c667adf0a4fdb5b7a6f6562f1b83dbe7b01110e242f272bc692`
- `2023-04-04` : `data/research/v7_1/trades/aggTrades/source=binance_archive/market_type=spot/symbol=BTCUSDT/window=2023-03-25_2023-04-23/date=2023-04-04/agg_trades.parquet`, `862796` lignes, checksum `f6b4bf70286ae3c6347bd68529002e3336a0991d7d860e55dc6e0a8814ff346d`
- `2023-04-05` : `data/research/v7_1/trades/aggTrades/source=binance_archive/market_type=spot/symbol=BTCUSDT/window=2023-03-25_2023-04-23/date=2023-04-05/agg_trades.parquet`, `981428` lignes, checksum `41998edfd8a738c6390a1394f953b51c65ec9229cc4aeaccacd275fd4f710dc0`
- `2023-04-06` : `data/research/v7_1/trades/aggTrades/source=binance_archive/market_type=spot/symbol=BTCUSDT/window=2023-03-25_2023-04-23/date=2023-04-06/agg_trades.parquet`, `741248` lignes, checksum `254272f378c5f60dfc6d149726e119179be5fded6ff7c01ca7a30b29093de3d9`
- `2023-04-07` : `data/research/v7_1/trades/aggTrades/source=binance_archive/market_type=spot/symbol=BTCUSDT/window=2023-03-25_2023-04-23/date=2023-04-07/agg_trades.parquet`, `524712` lignes, checksum `345a2d678c2648d51b2b83add1d98b647b731557de2b5260bc49e61dae33aa41`
- `2023-04-08` : `data/research/v7_1/trades/aggTrades/source=binance_archive/market_type=spot/symbol=BTCUSDT/window=2023-03-25_2023-04-23/date=2023-04-08/agg_trades.parquet`, `518781` lignes, checksum `bf023c9a2be524a7921d2c89872fd4b3b4e823f237707f738b3ce5b78de02fb2`
- `2023-04-09` : `data/research/v7_1/trades/aggTrades/source=binance_archive/market_type=spot/symbol=BTCUSDT/window=2023-03-25_2023-04-23/date=2023-04-09/agg_trades.parquet`, `621970` lignes, checksum `d7d3aa2b942bd41c690d7528cba4e9aef8bc6570ab0d1946f26dad8d50b46c34`
- `2023-04-10` : `data/research/v7_1/trades/aggTrades/source=binance_archive/market_type=spot/symbol=BTCUSDT/window=2023-03-25_2023-04-23/date=2023-04-10/agg_trades.parquet`, `999793` lignes, checksum `d1546975a90c590f74087bca006b04c9bc2b569f2ef7ed1ffa5063d618076c40`
- `2023-04-11` : `data/research/v7_1/trades/aggTrades/source=binance_archive/market_type=spot/symbol=BTCUSDT/window=2023-03-25_2023-04-23/date=2023-04-11/agg_trades.parquet`, `1061109` lignes, checksum `32eb1751a38f192eaa660b6cd25ce49e2581154297f6501042b87656e6d6baa9`
- `2023-04-12` : `data/research/v7_1/trades/aggTrades/source=binance_archive/market_type=spot/symbol=BTCUSDT/window=2023-03-25_2023-04-23/date=2023-04-12/agg_trades.parquet`, `993870` lignes, checksum `3175cc06d8f835bd1468fa8268a7ec0bd85cd3513e7e7b7689125c05fb34969c`
- `2023-04-13` : `data/research/v7_1/trades/aggTrades/source=binance_archive/market_type=spot/symbol=BTCUSDT/window=2023-03-25_2023-04-23/date=2023-04-13/agg_trades.parquet`, `837590` lignes, checksum `32855c26f1f54c5604865ef855cf4e4505cc2bc4a427f20674c4c922a850a6db`
- `2023-04-14` : `data/research/v7_1/trades/aggTrades/source=binance_archive/market_type=spot/symbol=BTCUSDT/window=2023-03-25_2023-04-23/date=2023-04-14/agg_trades.parquet`, `1193393` lignes, checksum `a1fc5482d32a9b9603d7a554f10b7dbd483ae564b88fc030bf174988403c76ac`
- `2023-04-15` : `data/research/v7_1/trades/aggTrades/source=binance_archive/market_type=spot/symbol=BTCUSDT/window=2023-03-25_2023-04-23/date=2023-04-15/agg_trades.parquet`, `601021` lignes, checksum `3e8ac2d20294f939e9981bdc845aa65169c6f5719ec1ee1c275b7ffc6c4e1cce`
- `2023-04-16` : `data/research/v7_1/trades/aggTrades/source=binance_archive/market_type=spot/symbol=BTCUSDT/window=2023-03-25_2023-04-23/date=2023-04-16/agg_trades.parquet`, `575262` lignes, checksum `f24b07e49b05abeaeba097efe6b91a7bb540acaa0cfd7202acbfa15e962e38ad`
- `2023-04-17` : `data/research/v7_1/trades/aggTrades/source=binance_archive/market_type=spot/symbol=BTCUSDT/window=2023-03-25_2023-04-23/date=2023-04-17/agg_trades.parquet`, `880114` lignes, checksum `d690f3137443c2b7a67dd69292fed5b5bc385e9ee572660a5ae80208e1359f87`
- `2023-04-18` : `data/research/v7_1/trades/aggTrades/source=binance_archive/market_type=spot/symbol=BTCUSDT/window=2023-03-25_2023-04-23/date=2023-04-18/agg_trades.parquet`, `893647` lignes, checksum `d214366123d26aace98e188b17fc0b1119ebb013b91665723e38e3fac2faf6ee`
- `2023-04-19` : `data/research/v7_1/trades/aggTrades/source=binance_archive/market_type=spot/symbol=BTCUSDT/window=2023-03-25_2023-04-23/date=2023-04-19/agg_trades.parquet`, `1360410` lignes, checksum `062d304781e2dee2425e1134ab7be542ebdff2b645e8b8c34194f64cfd10a66c`
- `2023-04-20` : `data/research/v7_1/trades/aggTrades/source=binance_archive/market_type=spot/symbol=BTCUSDT/window=2023-03-25_2023-04-23/date=2023-04-20/agg_trades.parquet`, `1136546` lignes, checksum `ef6c50ae9981e025c448cc68dbcd7c44656291bf2c3abff02994336b3364db96`
- `2023-04-21` : `data/research/v7_1/trades/aggTrades/source=binance_archive/market_type=spot/symbol=BTCUSDT/window=2023-03-25_2023-04-23/date=2023-04-21/agg_trades.parquet`, `1163429` lignes, checksum `33556c5d05e85360bae68007358860b6d10558c2b413db2e679b01d23391fd20`
- `2023-04-22` : `data/research/v7_1/trades/aggTrades/source=binance_archive/market_type=spot/symbol=BTCUSDT/window=2023-03-25_2023-04-23/date=2023-04-22/agg_trades.parquet`, `695126` lignes, checksum `c52c65db92182e9d01aead75c9b0780ca9020f89c10d689fa4ba9431f26def42`
- `2023-04-23` : `data/research/v7_1/trades/aggTrades/source=binance_archive/market_type=spot/symbol=BTCUSDT/window=2023-03-25_2023-04-23/date=2023-04-23/agg_trades.parquet`, `709690` lignes, checksum `88ee682e0541a8a6e7210fbd6227d0dabda5a649440796d35bd483d3312f80e3`

## Qualite

- Doublons `aggregate_trade_id` : `0`.
- IDs non monotones : `0`.
- Timestamps non monotones : `0`.
- Prix non positifs : `0`.
- Quantites non positives : `0`.
- Colonnes interdites : `[]`.

## Limitations

- V7.1 etend uniquement l'ingestion de trades publics aggTrades sur une fenetre bornee de 30 jours.
- V7.1 ne produit aucune feature, aucun label, aucun dataset ML, aucun modele ML, aucun backtest, aucune strategie et aucun ordre.

## Securite

V7.1 ne valide aucune strategie.
V7.1 ne produit aucune feature.
V7.1 ne produit aucun label.
V7.1 ne produit aucun dataset ML.
V7.1 ne produit aucun modele ML.
V7.1 ne produit aucun backtest.
V7.1 ne produit aucun signal de trading.
V7.1 ne produit aucun ordre.
V7.1 n'autorise aucun paper live.
V7.1 n'autorise aucun trading reel.
