# Public Trades Historical Window Expansion V7.7

## Objectif

V7.7 etend uniquement l'ingestion data-only de trades publics Binance `aggTrades` pour `BTCUSDT` spot.

## Fenetre

- Fenetre : `2023-03-25` -> `2023-06-22`.
- Total jours : `90`.
- Meme fenetre que V5.0 : `False`.
- Raison : bounded 90-day V7.7 aggTrades expansion after the 30-day V7.1 ingestion window and V7.6 decision gate.

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
- `2023-04-24` : `964211` lignes, `13790146` octets, checksum `4fd08008d722d4b4d0fdfc1237dc37053de9422d3bdf032a0165a33a1ce9f989`
- `2023-04-25` : `869887` lignes, `12465250` octets, checksum `00763a0f2e8b6708dab40a5741b0be3bbe1649670df701045025dd3e5129607e`
- `2023-04-26` : `1806038` lignes, `25771501` octets, checksum `d3caf6215b5237a30161089158e2caf06441d4d8057420d51ec5a78c65f22543`
- `2023-04-27` : `1587774` lignes, `22646038` octets, checksum `e0fff55072f82bc02e2436115c82345754cd240276fa38154f734b5b01122858`
- `2023-04-28` : `890853` lignes, `12760277` octets, checksum `5bcad564645e4656e89b20e900fadfe908a7cc037edd6ceb6e56ec99cf1a75ab`
- `2023-04-29` : `501597` lignes, `7229002` octets, checksum `42dcc17e0ca89c4b3375bb8e798cbc3ebc0087b7ac43980f987a51693cad043e`
- `2023-04-30` : `761291` lignes, `10910164` octets, checksum `8d37aa613e3a21858cdf58524e7b42802debbbd0775a77705eff53e4b1f785ae`
- `2023-05-01` : `1061375` lignes, `15127538` octets, checksum `e9131ac7e0d7eed8d2f6bc20025b7e8e4d9877eb5ddf7c24d90511bec2aef4d4`
- `2023-05-02` : `898518` lignes, `12882271` octets, checksum `c6def8bdb0f365c9a883b594eeffc08b50774ee29e2f310bc6d307bb6c75e3ec`
- `2023-05-03` : `1183358` lignes, `16909727` octets, checksum `8a1f4e40eaf3a0ae0cead47e4518d00fb570ae9ddfde89ad771008e11866a410`
- `2023-05-04` : `750657` lignes, `10814552` octets, checksum `4e3f5d538c68f43a9b11c3c605566cdfdf0432cd421aac142f503130b8ec405a`
- `2023-05-05` : `996866` lignes, `14299408` octets, checksum `03f7f62edd975236bd37a3acc47eb245a7b975bc099a396bf93d35e5e4ee15c2`
- `2023-05-06` : `954813` lignes, `13608386` octets, checksum `eb041e2664fa61402d93eaf9c11ddcf8095d020bb16e6a6605505a081145d6a2`
- `2023-05-07` : `665516` lignes, `9524876` octets, checksum `be26a9e836a2f61b000e60945e2ea77bbb2f2946443ae1c8a3477eae109364a9`
- `2023-05-08` : `1208202` lignes, `17272373` octets, checksum `5a4dc915948a96e62157827d6c2472e775d22f7907d7767e0f095456c1da796e`
- `2023-05-09` : `743776` lignes, `10726131` octets, checksum `b111e6fa12c1b822d8bef0330b8fd5d35a525493fc1b4161bb8a650d4a113875`
- `2023-05-10` : `1173713` lignes, `16828574` octets, checksum `55ff6407ba9c921e2dfca2ba55ed96b4bdf60284fbde8579561572840994969d`
- `2023-05-11` : `965862` lignes, `13796858` octets, checksum `cc15c43006910d8e635dfe304b9867a8745a51b8feb221a2c3680a008e52571f`
- `2023-05-12` : `1024511` lignes, `14839988` octets, checksum `dcfda6d429b06146d08e0c350889481efcde54346edce588de0d803ae8851206`
- `2023-05-13` : `462038` lignes, `6773951` octets, checksum `b2715f0e5e87eb0d64041620d218437811a2770b34d5b25cea426ab86ca1100e`
- `2023-05-14` : `485791` lignes, `7028486` octets, checksum `6189173c4cb011b1b68095f43982b138751aeefe580e73db60849b102b5ab701`
- `2023-05-15` : `721934` lignes, `10275553` octets, checksum `431d6e6d33772fb8305208d81889814a72a52021065e0347c465cd50bd3a2fc8`
- `2023-05-16` : `617457` lignes, `8826891` octets, checksum `c2738de5e4fb9148cd005355b9e7fef05859604eeb941f0ab13c53d417428af0`
- `2023-05-17` : `768095` lignes, `10866494` octets, checksum `3d8a3ca33e0ec03dd4af8d3e5235869aae45dce25f3e5f6ec28bcdfedc917d52`
- `2023-05-18` : `813533` lignes, `11575037` octets, checksum `3c91abab35e8e1119f090eabd7853b34ddc61daeda7b79e6ce93a7772fc2a231`
- `2023-05-19` : `603933` lignes, `8693905` octets, checksum `27cf6e54b7f13236bedc97a48a34d5bfbd360b2551afd0bec42b373a63787289`
- `2023-05-20` : `391975` lignes, `5628067` octets, checksum `101d64139a4ee0199a1e81a7c4014d7da068f78af2ab4154f19e4a607c90913a`
- `2023-05-21` : `447857` lignes, `6454684` octets, checksum `6cd14cbc1919cdae0aebe6af10e0a573075a1604e549a13fb973f1175f5dc879`
- `2023-05-22` : `536526` lignes, `7736100` octets, checksum `1bfa706c026940824de4488b493adb47bbde8ab91e1807501553673f3cc6f3a0`
- `2023-05-23` : `607062` lignes, `8777932` octets, checksum `f806567c92d726b81a2e30a99fb3676c1e3003efe35fb095c00796e2137640fb`
- `2023-05-24` : `784912` lignes, `11331802` octets, checksum `afffdab8a07411faf8d9e7f07b1b868ae355fb4c6d6864670a3345ad96588ba8`
- `2023-05-25` : `586231` lignes, `8541110` octets, checksum `88e23c803e37940fa9802025c175fe90e5626cceef6f6d37c73bd9d66691db42`
- `2023-05-26` : `506909` lignes, `7400702` octets, checksum `9833743e5d98a7da55dd28fc76c2f12164ec705853140acea2002cadd42b589d`
- `2023-05-27` : `327636` lignes, `4784716` octets, checksum `d686a1994a1a1058ac9240a6e433e2d19e6df1f6b234db2d0a3890c3ba0bfd8c`
- `2023-05-28` : `632934` lignes, `9197686` octets, checksum `0da2f9311f7a068aaf0a42cd1589cff2b31b93cd49b567537b725eb94d10d077`
- `2023-05-29` : `622753` lignes, `8938934` octets, checksum `8a63e882f0e97610d452a709b8bd7349a71d293bd2964a9c8bf608e5b5996b1a`
- `2023-05-30` : `580233` lignes, `8278589` octets, checksum `f1ab5cd886bbc83319d487dd5e38a1ba48e5fa13b4b743c93ea5067c3afaee85`
- `2023-05-31` : `710719` lignes, `10082725` octets, checksum `bdd5ff1e392e71f43ec62beffbbaecc4f81f9c89a6d5a9b2c5ccd4d1aac85c5d`
- `2023-06-01` : `627613` lignes, `8927371` octets, checksum `b209a79e0dfcbc599e9da01eeccfb683ef8a90a0db4336771418910727da3a35`
- `2023-06-02` : `628271` lignes, `8962722` octets, checksum `1435eaadc2b3dd30b0f57b2183df3ff2786433df1046b8c19e4f19b87ea55061`
- `2023-06-03` : `368778` lignes, `5271031` octets, checksum `c0d90bae75202208268a61612f0123ab03dd6a9274bd7837886e07aace6a562d`
- `2023-06-04` : `387272` lignes, `5506668` octets, checksum `bac9190b5d3b7c8a8d52969da365897d8290760602d2537dfce66fb9a133f4c0`
- `2023-06-05` : `1077982` lignes, `15345503` octets, checksum `4aa2f7a1ee5a695a06204fcac11cd744e8d8aec6e77b8403d105b5d334b0f156`
- `2023-06-06` : `1013521` lignes, `14365113` octets, checksum `92bfb414a768d65121c991e4c30adf71c595b0ddc1b132efbe1a729d74bc8eef`
- `2023-06-07` : `1003088` lignes, `14092292` octets, checksum `9185304c5895f4a046c293a62a70913a442b7428e77482bb7848b928923f6fbc`
- `2023-06-08` : `654984` lignes, `9180773` octets, checksum `9c78e033bedf3a42f464e66840a05c46a67994fc0285bda7c8561925683b71ec`
- `2023-06-09` : `589219` lignes, `8246466` octets, checksum `236f5a1295047393fbff0dc8a2cffba1c54e3dc50b066d171508f64ec6f72993`
- `2023-06-10` : `1328512` lignes, `18716651` octets, checksum `7bd18ba7d8f742cd6be5625b1c1d9da7401dd80d0d2f2d7bdd73d604db67e40e`
- `2023-06-11` : `631628` lignes, `8859647` octets, checksum `86fcaa4bf53d3ccdb1b3d479af8fac054ec1e6f07dc720dd66709307d6018506`
- `2023-06-12` : `665480` lignes, `9391405` octets, checksum `8d0b96da316a2ad135792cdd32d22b38e675102cc9f54b9476f1a79fb385f564`
- `2023-06-13` : `781671` lignes, `11014175` octets, checksum `185bdca3bb5c5d67539da7788854ce5750b7ea0b8b4c934962b1d8403b1dbdf4`
- `2023-06-14` : `713396` lignes, `10223381` octets, checksum `48beb7a04e931517ee9a9b75c8c4412b1b2db6d0749492fe52ec3852cb99c4e7`
- `2023-06-15` : `683170` lignes, `9850786` octets, checksum `2fc298b1dbe2b9762c58581511a3c1681471e3d09622b4fd33eb105457d39f34`
- `2023-06-16` : `688842` lignes, `9870043` octets, checksum `367da37aa8436edcf2c1e901d653d897b05450e1d7228a02312d5db8a4d35dec`
- `2023-06-17` : `506817` lignes, `7242849` octets, checksum `38db80fc574d4de784eb856dfd32161d1c1931c00ec2e130f9dc05c0da1a76bb`
- `2023-06-18` : `430860` lignes, `6133431` octets, checksum `020b34c2b6e698822362a3e4ee81508ba5627caec6df5f584d5dca0fafedaeec`
- `2023-06-19` : `558362` lignes, `7971034` octets, checksum `79b866ae0dc5085283dcc38908fdf5ed2b043ea1d3738ae620a63a7b22566b2c`
- `2023-06-20` : `859875` lignes, `12341445` octets, checksum `fd02485ffeff4211a97b42673066e0b42ca6682d15f852e36d0fb8d395fa1dad`
- `2023-06-21` : `1371327` lignes, `19668555` octets, checksum `db9fe25bfeda045454bea7eda48d82a3c04c80972b857916ad08867c4c214c9a`
- `2023-06-22` : `866275` lignes, `12430125` octets, checksum `6cc63bccc5d42d2362257cf40e52740b7ec0afa84b22c5a3e6dfc48c388b9bc0`

## Outputs partitionnes

- Rows totales : `74362570`.
- Bytes totaux : `2776097075`.
- Format : `partitioned_parquet`.

- `2023-03-25` : `data/research/v7_7/trades/aggTrades/source=binance_archive/market_type=spot/symbol=BTCUSDT/window=2023-03-25_2023-06-22/date=2023-03-25/agg_trades.parquet`, `817141` lignes, checksum `25d84f0d3f3fbdd8b77e13c9c4e7427541dba1f755779c2557997f1b9700b78c`
- `2023-03-26` : `data/research/v7_7/trades/aggTrades/source=binance_archive/market_type=spot/symbol=BTCUSDT/window=2023-03-25_2023-06-22/date=2023-03-26/agg_trades.parquet`, `786235` lignes, checksum `956bdc96a78dd6bcf004514161166a8eeb138da6835ca6f120fe5013723a8467`
- `2023-03-27` : `data/research/v7_7/trades/aggTrades/source=binance_archive/market_type=spot/symbol=BTCUSDT/window=2023-03-25_2023-06-22/date=2023-03-27/agg_trades.parquet`, `1145084` lignes, checksum `c55974e22ebeed0f2b11e49eb62c55bcd6543d8907d5502921df2106c9264940`
- `2023-03-28` : `data/research/v7_7/trades/aggTrades/source=binance_archive/market_type=spot/symbol=BTCUSDT/window=2023-03-25_2023-06-22/date=2023-03-28/agg_trades.parquet`, `1117559` lignes, checksum `0fec1678ba60c1e0707f9b48b7cb31b8babe0ccb4d693b194ae703fa3920caaf`
- `2023-03-29` : `data/research/v7_7/trades/aggTrades/source=binance_archive/market_type=spot/symbol=BTCUSDT/window=2023-03-25_2023-06-22/date=2023-03-29/agg_trades.parquet`, `1239862` lignes, checksum `2fffc4702f69c692c087c2c426396f8422cf27e2e0bddba7132a4961f32f54e8`
- `2023-03-30` : `data/research/v7_7/trades/aggTrades/source=binance_archive/market_type=spot/symbol=BTCUSDT/window=2023-03-25_2023-06-22/date=2023-03-30/agg_trades.parquet`, `1384715` lignes, checksum `a80804bf14147ae912ee312d5de53155daef821af1900ff5486345db2fee3030`
- `2023-03-31` : `data/research/v7_7/trades/aggTrades/source=binance_archive/market_type=spot/symbol=BTCUSDT/window=2023-03-25_2023-06-22/date=2023-03-31/agg_trades.parquet`, `1185212` lignes, checksum `dde1593f58439d179174f53b82aaf24897ac6c25c6576fcb50eb521c07eb648a`
- `2023-04-01` : `data/research/v7_7/trades/aggTrades/source=binance_archive/market_type=spot/symbol=BTCUSDT/window=2023-03-25_2023-06-22/date=2023-04-01/agg_trades.parquet`, `651525` lignes, checksum `266af83390e0d74b5b30e2ce0d07c70f88a0f2658b6b0a2e3ec80639c5b2b6e9`
- `2023-04-02` : `data/research/v7_7/trades/aggTrades/source=binance_archive/market_type=spot/symbol=BTCUSDT/window=2023-03-25_2023-06-22/date=2023-04-02/agg_trades.parquet`, `741918` lignes, checksum `a3c988cc56d439b1316da6a0a72be3b096ddab462c336d3a9f4462544f28362c`
- `2023-04-03` : `data/research/v7_7/trades/aggTrades/source=binance_archive/market_type=spot/symbol=BTCUSDT/window=2023-03-25_2023-06-22/date=2023-04-03/agg_trades.parquet`, `1287095` lignes, checksum `ee99c11350f65e079178de67a1973b87fb5415c7a2cd0063784a2cdcdec28d7f`
- `2023-04-04` : `data/research/v7_7/trades/aggTrades/source=binance_archive/market_type=spot/symbol=BTCUSDT/window=2023-03-25_2023-06-22/date=2023-04-04/agg_trades.parquet`, `862796` lignes, checksum `43cd545d21333ddb001511dc6ed77469ff5106450974f95f46545b62abe163cf`
- `2023-04-05` : `data/research/v7_7/trades/aggTrades/source=binance_archive/market_type=spot/symbol=BTCUSDT/window=2023-03-25_2023-06-22/date=2023-04-05/agg_trades.parquet`, `981428` lignes, checksum `15e046992e281d394196fc5d2d64f2773c48ac5dafe5fb2fbda90cf27b9c9982`
- `2023-04-06` : `data/research/v7_7/trades/aggTrades/source=binance_archive/market_type=spot/symbol=BTCUSDT/window=2023-03-25_2023-06-22/date=2023-04-06/agg_trades.parquet`, `741248` lignes, checksum `9382245a4067897225641586af8de6528ece179f68355119ad9dffb3d700999b`
- `2023-04-07` : `data/research/v7_7/trades/aggTrades/source=binance_archive/market_type=spot/symbol=BTCUSDT/window=2023-03-25_2023-06-22/date=2023-04-07/agg_trades.parquet`, `524712` lignes, checksum `10020b67fe73b90240402865949e62a6bdf2031079bf8053626d008db599f6df`
- `2023-04-08` : `data/research/v7_7/trades/aggTrades/source=binance_archive/market_type=spot/symbol=BTCUSDT/window=2023-03-25_2023-06-22/date=2023-04-08/agg_trades.parquet`, `518781` lignes, checksum `5f5b64d63001caae0542b012dd9951e48162f506596be77fd11ec037da483449`
- `2023-04-09` : `data/research/v7_7/trades/aggTrades/source=binance_archive/market_type=spot/symbol=BTCUSDT/window=2023-03-25_2023-06-22/date=2023-04-09/agg_trades.parquet`, `621970` lignes, checksum `cfd55fc5514ba8ecae1efd9f1f701d27b7a6138591684edc20a96e52976d862f`
- `2023-04-10` : `data/research/v7_7/trades/aggTrades/source=binance_archive/market_type=spot/symbol=BTCUSDT/window=2023-03-25_2023-06-22/date=2023-04-10/agg_trades.parquet`, `999793` lignes, checksum `4988c0d2f33796aea12b3e68b05cbb9ef48afabc8d1dba61d987c1cf3ffb233a`
- `2023-04-11` : `data/research/v7_7/trades/aggTrades/source=binance_archive/market_type=spot/symbol=BTCUSDT/window=2023-03-25_2023-06-22/date=2023-04-11/agg_trades.parquet`, `1061109` lignes, checksum `cf54cefc89ee47930ccca0a070ef7de063e76e3b00252e42f3bba8b147c3c499`
- `2023-04-12` : `data/research/v7_7/trades/aggTrades/source=binance_archive/market_type=spot/symbol=BTCUSDT/window=2023-03-25_2023-06-22/date=2023-04-12/agg_trades.parquet`, `993870` lignes, checksum `a1aa655569fc1faa57784ba7d7f7c1264fcd821553b275595f78055c62abf26b`
- `2023-04-13` : `data/research/v7_7/trades/aggTrades/source=binance_archive/market_type=spot/symbol=BTCUSDT/window=2023-03-25_2023-06-22/date=2023-04-13/agg_trades.parquet`, `837590` lignes, checksum `989bfa55dc1cea225b99dfa1e0306d4260d2e514e1a4755f1fd6b7b57e34ceff`
- `2023-04-14` : `data/research/v7_7/trades/aggTrades/source=binance_archive/market_type=spot/symbol=BTCUSDT/window=2023-03-25_2023-06-22/date=2023-04-14/agg_trades.parquet`, `1193393` lignes, checksum `93b083895de865675741e2106dae0144de930172de2b36bbfcfc720f72f143cb`
- `2023-04-15` : `data/research/v7_7/trades/aggTrades/source=binance_archive/market_type=spot/symbol=BTCUSDT/window=2023-03-25_2023-06-22/date=2023-04-15/agg_trades.parquet`, `601021` lignes, checksum `2df180ed7c857e650b0d6b9ed8b7d0bc0ea30233ef85b6ed082e1f4d13b49db5`
- `2023-04-16` : `data/research/v7_7/trades/aggTrades/source=binance_archive/market_type=spot/symbol=BTCUSDT/window=2023-03-25_2023-06-22/date=2023-04-16/agg_trades.parquet`, `575262` lignes, checksum `7265d2bf7695341b9a35741d45ee4a50b9d910fc6494376327398cbeea7955d4`
- `2023-04-17` : `data/research/v7_7/trades/aggTrades/source=binance_archive/market_type=spot/symbol=BTCUSDT/window=2023-03-25_2023-06-22/date=2023-04-17/agg_trades.parquet`, `880114` lignes, checksum `7e53605a359e4ec4c4a29053bda7a37a3f603bf2b8eb5bc1c9b9c0202b5909c9`
- `2023-04-18` : `data/research/v7_7/trades/aggTrades/source=binance_archive/market_type=spot/symbol=BTCUSDT/window=2023-03-25_2023-06-22/date=2023-04-18/agg_trades.parquet`, `893647` lignes, checksum `7671572c999e7a9a48fadf3204495cf263605069c8a7a65eafdcf11bcf312060`
- `2023-04-19` : `data/research/v7_7/trades/aggTrades/source=binance_archive/market_type=spot/symbol=BTCUSDT/window=2023-03-25_2023-06-22/date=2023-04-19/agg_trades.parquet`, `1360410` lignes, checksum `2bb4ecc5d26947b655722037eeab56797d521ff0909534f950a08aed2e28d538`
- `2023-04-20` : `data/research/v7_7/trades/aggTrades/source=binance_archive/market_type=spot/symbol=BTCUSDT/window=2023-03-25_2023-06-22/date=2023-04-20/agg_trades.parquet`, `1136546` lignes, checksum `86fd05f9de8c1fe81ceec08fb9f77533a26d4a2c7f79d4ff69274df3919afc57`
- `2023-04-21` : `data/research/v7_7/trades/aggTrades/source=binance_archive/market_type=spot/symbol=BTCUSDT/window=2023-03-25_2023-06-22/date=2023-04-21/agg_trades.parquet`, `1163429` lignes, checksum `0c76a277281b37f839201f2d6556a9416245b2c78f1f6dc380866ce6b4c92f2a`
- `2023-04-22` : `data/research/v7_7/trades/aggTrades/source=binance_archive/market_type=spot/symbol=BTCUSDT/window=2023-03-25_2023-06-22/date=2023-04-22/agg_trades.parquet`, `695126` lignes, checksum `908d6e7a2262e814ba881847c5a6b629330ed504c8a4bfb921b2f0f0d0f18252`
- `2023-04-23` : `data/research/v7_7/trades/aggTrades/source=binance_archive/market_type=spot/symbol=BTCUSDT/window=2023-03-25_2023-06-22/date=2023-04-23/agg_trades.parquet`, `709690` lignes, checksum `ce8069370effc4ca0496735e72a50b43bfd78389bafee92102db122b8d458d9d`
- `2023-04-24` : `data/research/v7_7/trades/aggTrades/source=binance_archive/market_type=spot/symbol=BTCUSDT/window=2023-03-25_2023-06-22/date=2023-04-24/agg_trades.parquet`, `964211` lignes, checksum `7997bbfef6837ebc6b26d394ef74378bea6f524a1e07445d66d387f5554b05d5`
- `2023-04-25` : `data/research/v7_7/trades/aggTrades/source=binance_archive/market_type=spot/symbol=BTCUSDT/window=2023-03-25_2023-06-22/date=2023-04-25/agg_trades.parquet`, `869887` lignes, checksum `ef0ee6efef169fe0cf822890c8d4c7186208c579dd736ccf7310c6c0e8f64615`
- `2023-04-26` : `data/research/v7_7/trades/aggTrades/source=binance_archive/market_type=spot/symbol=BTCUSDT/window=2023-03-25_2023-06-22/date=2023-04-26/agg_trades.parquet`, `1806038` lignes, checksum `2bd42fc353dac805402ea8857e87d0832f607f0b504e343cdcef2dfbf8457834`
- `2023-04-27` : `data/research/v7_7/trades/aggTrades/source=binance_archive/market_type=spot/symbol=BTCUSDT/window=2023-03-25_2023-06-22/date=2023-04-27/agg_trades.parquet`, `1587774` lignes, checksum `741fe359b1e5b736dd4f23f22762988853f8c1ae9c869b8fbf1e87891755a329`
- `2023-04-28` : `data/research/v7_7/trades/aggTrades/source=binance_archive/market_type=spot/symbol=BTCUSDT/window=2023-03-25_2023-06-22/date=2023-04-28/agg_trades.parquet`, `890853` lignes, checksum `60c6ae5bf9d253a7a565d4a75403920c74c5851e93c9f9f3c59591d82c8b9f0d`
- `2023-04-29` : `data/research/v7_7/trades/aggTrades/source=binance_archive/market_type=spot/symbol=BTCUSDT/window=2023-03-25_2023-06-22/date=2023-04-29/agg_trades.parquet`, `501597` lignes, checksum `d1cf25f83b463978a6b52a198d9044f1a1ed845f73e5a84f9d9c64d739025ff2`
- `2023-04-30` : `data/research/v7_7/trades/aggTrades/source=binance_archive/market_type=spot/symbol=BTCUSDT/window=2023-03-25_2023-06-22/date=2023-04-30/agg_trades.parquet`, `761291` lignes, checksum `704f8a3de2b21c4b165aec734f056936e3f45ba546727565bf66a430ff1fab9f`
- `2023-05-01` : `data/research/v7_7/trades/aggTrades/source=binance_archive/market_type=spot/symbol=BTCUSDT/window=2023-03-25_2023-06-22/date=2023-05-01/agg_trades.parquet`, `1061375` lignes, checksum `9a272662437a120950633fa007805fe53d9cac7c1d8dd06e63ba27cb94de5548`
- `2023-05-02` : `data/research/v7_7/trades/aggTrades/source=binance_archive/market_type=spot/symbol=BTCUSDT/window=2023-03-25_2023-06-22/date=2023-05-02/agg_trades.parquet`, `898518` lignes, checksum `1dea0c48af07c164cc3d4d6246900e95ff4ab51971aed7b1bddc3a65bf33f8bc`
- `2023-05-03` : `data/research/v7_7/trades/aggTrades/source=binance_archive/market_type=spot/symbol=BTCUSDT/window=2023-03-25_2023-06-22/date=2023-05-03/agg_trades.parquet`, `1183358` lignes, checksum `0784fffd1d3c3e106ac9fb430444c6889104d9843c19edcc6f9053ad49f0a7fe`
- `2023-05-04` : `data/research/v7_7/trades/aggTrades/source=binance_archive/market_type=spot/symbol=BTCUSDT/window=2023-03-25_2023-06-22/date=2023-05-04/agg_trades.parquet`, `750657` lignes, checksum `9a0536115a6c0d697baab5da8d0655cc84cb13db04da235d31a2a8c600675e61`
- `2023-05-05` : `data/research/v7_7/trades/aggTrades/source=binance_archive/market_type=spot/symbol=BTCUSDT/window=2023-03-25_2023-06-22/date=2023-05-05/agg_trades.parquet`, `996866` lignes, checksum `d8137bacde33b540031e43d37f26360093eef9cbaa99d22753ddce23604e4b9d`
- `2023-05-06` : `data/research/v7_7/trades/aggTrades/source=binance_archive/market_type=spot/symbol=BTCUSDT/window=2023-03-25_2023-06-22/date=2023-05-06/agg_trades.parquet`, `954813` lignes, checksum `3bf5c3833b6119669552f2403ab2b92e8893fc03b6ed2de405ba27c1b0f92f72`
- `2023-05-07` : `data/research/v7_7/trades/aggTrades/source=binance_archive/market_type=spot/symbol=BTCUSDT/window=2023-03-25_2023-06-22/date=2023-05-07/agg_trades.parquet`, `665516` lignes, checksum `420eac6169b049a9007ed13c5503b7f2ec4471f5f17e28a11bc59cac14d2fc7b`
- `2023-05-08` : `data/research/v7_7/trades/aggTrades/source=binance_archive/market_type=spot/symbol=BTCUSDT/window=2023-03-25_2023-06-22/date=2023-05-08/agg_trades.parquet`, `1208202` lignes, checksum `143ef2fce6de0e58d7401430a6d0945a5606c700b512739d6abf27d5b4c87893`
- `2023-05-09` : `data/research/v7_7/trades/aggTrades/source=binance_archive/market_type=spot/symbol=BTCUSDT/window=2023-03-25_2023-06-22/date=2023-05-09/agg_trades.parquet`, `743776` lignes, checksum `fb639ebd6b58b015593e22f3527d79ea2e16a03fc27cca50bdff98ce92a36cd9`
- `2023-05-10` : `data/research/v7_7/trades/aggTrades/source=binance_archive/market_type=spot/symbol=BTCUSDT/window=2023-03-25_2023-06-22/date=2023-05-10/agg_trades.parquet`, `1173713` lignes, checksum `27329fca74b32cdcac4db36182f66baec6c3da506621dde82ccb6ca1083c0f5b`
- `2023-05-11` : `data/research/v7_7/trades/aggTrades/source=binance_archive/market_type=spot/symbol=BTCUSDT/window=2023-03-25_2023-06-22/date=2023-05-11/agg_trades.parquet`, `965862` lignes, checksum `c6fc197fd6e1da86960526d0539d440b5c86952c0c42338127a8f3c84c437939`
- `2023-05-12` : `data/research/v7_7/trades/aggTrades/source=binance_archive/market_type=spot/symbol=BTCUSDT/window=2023-03-25_2023-06-22/date=2023-05-12/agg_trades.parquet`, `1024511` lignes, checksum `94522f93c9b5b107dae3ef9de829572cc1ef4543c42cb1821859af647361e7ba`
- `2023-05-13` : `data/research/v7_7/trades/aggTrades/source=binance_archive/market_type=spot/symbol=BTCUSDT/window=2023-03-25_2023-06-22/date=2023-05-13/agg_trades.parquet`, `462038` lignes, checksum `e31fc9e6f46d56964f7fe7fbc81aa68103761bab24476d5be96787c79c5044c7`
- `2023-05-14` : `data/research/v7_7/trades/aggTrades/source=binance_archive/market_type=spot/symbol=BTCUSDT/window=2023-03-25_2023-06-22/date=2023-05-14/agg_trades.parquet`, `485791` lignes, checksum `676f10f7761e960053c31ec3d69a5d68b419f0f874c11ef995cb48776559a2a1`
- `2023-05-15` : `data/research/v7_7/trades/aggTrades/source=binance_archive/market_type=spot/symbol=BTCUSDT/window=2023-03-25_2023-06-22/date=2023-05-15/agg_trades.parquet`, `721934` lignes, checksum `dfacb3cfdee0cb22641730a8e81ea1e7b94a0def064b6437d90d32c09a615615`
- `2023-05-16` : `data/research/v7_7/trades/aggTrades/source=binance_archive/market_type=spot/symbol=BTCUSDT/window=2023-03-25_2023-06-22/date=2023-05-16/agg_trades.parquet`, `617457` lignes, checksum `85e2fa19b703e2cc0a6c4c2bd5fe4a47b3546cd95da9b9d58d9d7efd49c97c50`
- `2023-05-17` : `data/research/v7_7/trades/aggTrades/source=binance_archive/market_type=spot/symbol=BTCUSDT/window=2023-03-25_2023-06-22/date=2023-05-17/agg_trades.parquet`, `768095` lignes, checksum `ccc36d1f419294a8f2c58da3c79a86b864c66b3b3a4132a2a84949ad5805e949`
- `2023-05-18` : `data/research/v7_7/trades/aggTrades/source=binance_archive/market_type=spot/symbol=BTCUSDT/window=2023-03-25_2023-06-22/date=2023-05-18/agg_trades.parquet`, `813533` lignes, checksum `45d4fbf581cdcef77e9a11cdb0d3d2384c755354a79ce0f541f6bd35f96f8dd0`
- `2023-05-19` : `data/research/v7_7/trades/aggTrades/source=binance_archive/market_type=spot/symbol=BTCUSDT/window=2023-03-25_2023-06-22/date=2023-05-19/agg_trades.parquet`, `603933` lignes, checksum `d83a724691eb501cce33193ab1866079710939b6c09ff3df0289e8e86d9284f1`
- `2023-05-20` : `data/research/v7_7/trades/aggTrades/source=binance_archive/market_type=spot/symbol=BTCUSDT/window=2023-03-25_2023-06-22/date=2023-05-20/agg_trades.parquet`, `391975` lignes, checksum `8c75d02094a46095c37516c37e7a55725b085634ffdfcc333aeda987f88af4f4`
- `2023-05-21` : `data/research/v7_7/trades/aggTrades/source=binance_archive/market_type=spot/symbol=BTCUSDT/window=2023-03-25_2023-06-22/date=2023-05-21/agg_trades.parquet`, `447857` lignes, checksum `6b3601ba52655ac5c372a126be819446780e56ea2351d4d9f702d881f3dd4237`
- `2023-05-22` : `data/research/v7_7/trades/aggTrades/source=binance_archive/market_type=spot/symbol=BTCUSDT/window=2023-03-25_2023-06-22/date=2023-05-22/agg_trades.parquet`, `536526` lignes, checksum `20e7410092a485e859fbb7398963debc92121fa355aab7e5b98d533117e9a624`
- `2023-05-23` : `data/research/v7_7/trades/aggTrades/source=binance_archive/market_type=spot/symbol=BTCUSDT/window=2023-03-25_2023-06-22/date=2023-05-23/agg_trades.parquet`, `607062` lignes, checksum `8776df5e854f9c91a5266d3621fbb9996f872fcdc62179e37865a9535f941ecc`
- `2023-05-24` : `data/research/v7_7/trades/aggTrades/source=binance_archive/market_type=spot/symbol=BTCUSDT/window=2023-03-25_2023-06-22/date=2023-05-24/agg_trades.parquet`, `784912` lignes, checksum `2ec174bfaccb5c9438b971bac83addd4fe669f65341343bb9b4a7840998b58e7`
- `2023-05-25` : `data/research/v7_7/trades/aggTrades/source=binance_archive/market_type=spot/symbol=BTCUSDT/window=2023-03-25_2023-06-22/date=2023-05-25/agg_trades.parquet`, `586231` lignes, checksum `906178d3381004c4a80b806365fd171f937392b0ddd442b193e48ae24a9f174c`
- `2023-05-26` : `data/research/v7_7/trades/aggTrades/source=binance_archive/market_type=spot/symbol=BTCUSDT/window=2023-03-25_2023-06-22/date=2023-05-26/agg_trades.parquet`, `506909` lignes, checksum `938dc188169bfdfef9ab961cf8ea4032acf17672a5387e7ecda59c76c6a456b2`
- `2023-05-27` : `data/research/v7_7/trades/aggTrades/source=binance_archive/market_type=spot/symbol=BTCUSDT/window=2023-03-25_2023-06-22/date=2023-05-27/agg_trades.parquet`, `327636` lignes, checksum `bb3b512c91d4b3850819cbe4110995b683f31456072de40092548fd464da7f35`
- `2023-05-28` : `data/research/v7_7/trades/aggTrades/source=binance_archive/market_type=spot/symbol=BTCUSDT/window=2023-03-25_2023-06-22/date=2023-05-28/agg_trades.parquet`, `632934` lignes, checksum `9de5e2c41255c3d68a3112a8b1bd8328acd558539e1609b99a3cb96a74c42891`
- `2023-05-29` : `data/research/v7_7/trades/aggTrades/source=binance_archive/market_type=spot/symbol=BTCUSDT/window=2023-03-25_2023-06-22/date=2023-05-29/agg_trades.parquet`, `622753` lignes, checksum `dbbe2f2f63d613f86c24abb3cee118f737a37055b21d3d39fb4ec2515059c799`
- `2023-05-30` : `data/research/v7_7/trades/aggTrades/source=binance_archive/market_type=spot/symbol=BTCUSDT/window=2023-03-25_2023-06-22/date=2023-05-30/agg_trades.parquet`, `580233` lignes, checksum `5268ea253cf7a1e177a48ec05ea82ac1e62383f73e9541ba9e87e47bde5776a9`
- `2023-05-31` : `data/research/v7_7/trades/aggTrades/source=binance_archive/market_type=spot/symbol=BTCUSDT/window=2023-03-25_2023-06-22/date=2023-05-31/agg_trades.parquet`, `710719` lignes, checksum `b7d42dbb8aff83f20aa1d59ad439522850bdeb08737534e8576bb6409bbe7f51`
- `2023-06-01` : `data/research/v7_7/trades/aggTrades/source=binance_archive/market_type=spot/symbol=BTCUSDT/window=2023-03-25_2023-06-22/date=2023-06-01/agg_trades.parquet`, `627613` lignes, checksum `33ec44b0067f4750ee7235a996bc799e3879d4605fa2011f70406744cc7fbf6c`
- `2023-06-02` : `data/research/v7_7/trades/aggTrades/source=binance_archive/market_type=spot/symbol=BTCUSDT/window=2023-03-25_2023-06-22/date=2023-06-02/agg_trades.parquet`, `628271` lignes, checksum `e8a29b9bbd7113a49262282acbce0e4f3cbd26cfa53c2a0f2c7915d7a32e05cf`
- `2023-06-03` : `data/research/v7_7/trades/aggTrades/source=binance_archive/market_type=spot/symbol=BTCUSDT/window=2023-03-25_2023-06-22/date=2023-06-03/agg_trades.parquet`, `368778` lignes, checksum `6e8af5d1ec2ef1eed6a7643d66c4ab5731699f06045ceee61de77326661e626b`
- `2023-06-04` : `data/research/v7_7/trades/aggTrades/source=binance_archive/market_type=spot/symbol=BTCUSDT/window=2023-03-25_2023-06-22/date=2023-06-04/agg_trades.parquet`, `387272` lignes, checksum `7492f48f5b2be26a4f4baac221652b86af09d669076f17db93bc4152a7324f27`
- `2023-06-05` : `data/research/v7_7/trades/aggTrades/source=binance_archive/market_type=spot/symbol=BTCUSDT/window=2023-03-25_2023-06-22/date=2023-06-05/agg_trades.parquet`, `1077982` lignes, checksum `50c539d6e95de17708f1fb1eaae2c66e20d663fc81e09ad3c61443671da6585f`
- `2023-06-06` : `data/research/v7_7/trades/aggTrades/source=binance_archive/market_type=spot/symbol=BTCUSDT/window=2023-03-25_2023-06-22/date=2023-06-06/agg_trades.parquet`, `1013521` lignes, checksum `46a444d6b6cd92b07b0471c62672d34fb93008db9bb6daf4602db44c69cff649`
- `2023-06-07` : `data/research/v7_7/trades/aggTrades/source=binance_archive/market_type=spot/symbol=BTCUSDT/window=2023-03-25_2023-06-22/date=2023-06-07/agg_trades.parquet`, `1003088` lignes, checksum `5ffc6ee4869b34fa00b6b532b36950eecd3d7f6eca5e0757dbb9e7a56c83b21e`
- `2023-06-08` : `data/research/v7_7/trades/aggTrades/source=binance_archive/market_type=spot/symbol=BTCUSDT/window=2023-03-25_2023-06-22/date=2023-06-08/agg_trades.parquet`, `654984` lignes, checksum `d740d80d743537d253895b06227da04111f79c05db4d852bfb2a61cd3e6fda3d`
- `2023-06-09` : `data/research/v7_7/trades/aggTrades/source=binance_archive/market_type=spot/symbol=BTCUSDT/window=2023-03-25_2023-06-22/date=2023-06-09/agg_trades.parquet`, `589219` lignes, checksum `c2005240150075b1b4c3251ac3b027609a7c91ae325df092b0d245b444e5823a`
- `2023-06-10` : `data/research/v7_7/trades/aggTrades/source=binance_archive/market_type=spot/symbol=BTCUSDT/window=2023-03-25_2023-06-22/date=2023-06-10/agg_trades.parquet`, `1328512` lignes, checksum `2e61d467f3df2b3a0f324e6b4e748fa2ae93879b6c6c4133ab6f47a11cb48465`
- `2023-06-11` : `data/research/v7_7/trades/aggTrades/source=binance_archive/market_type=spot/symbol=BTCUSDT/window=2023-03-25_2023-06-22/date=2023-06-11/agg_trades.parquet`, `631628` lignes, checksum `e02ca5a3faaf57e97c2540681bb36ddd12d34f3225e7e58b64eb7112213cd92d`
- `2023-06-12` : `data/research/v7_7/trades/aggTrades/source=binance_archive/market_type=spot/symbol=BTCUSDT/window=2023-03-25_2023-06-22/date=2023-06-12/agg_trades.parquet`, `665480` lignes, checksum `70e0a37d1b74c64e4df59fa832689d093e4b960a774812bd0a3dec4416d77cf7`
- `2023-06-13` : `data/research/v7_7/trades/aggTrades/source=binance_archive/market_type=spot/symbol=BTCUSDT/window=2023-03-25_2023-06-22/date=2023-06-13/agg_trades.parquet`, `781671` lignes, checksum `8fe9acd58c720bd132705161fcbc0ed397c7027adb6f700f4c6362298b66007d`
- `2023-06-14` : `data/research/v7_7/trades/aggTrades/source=binance_archive/market_type=spot/symbol=BTCUSDT/window=2023-03-25_2023-06-22/date=2023-06-14/agg_trades.parquet`, `713396` lignes, checksum `2c256e4582e364c5bd1876c9b3db4b3410a84827419bb499d3bc7f251ec5fa74`
- `2023-06-15` : `data/research/v7_7/trades/aggTrades/source=binance_archive/market_type=spot/symbol=BTCUSDT/window=2023-03-25_2023-06-22/date=2023-06-15/agg_trades.parquet`, `683170` lignes, checksum `416f5ca4629d4e9477ee6ad46d54fbc839d5c2e78897f62f59e92ca114049aab`
- `2023-06-16` : `data/research/v7_7/trades/aggTrades/source=binance_archive/market_type=spot/symbol=BTCUSDT/window=2023-03-25_2023-06-22/date=2023-06-16/agg_trades.parquet`, `688842` lignes, checksum `d5341819e8d9871a9b46ec3c69e96b768aad13a7ad2abb528dbf7d72eaeb11d2`
- `2023-06-17` : `data/research/v7_7/trades/aggTrades/source=binance_archive/market_type=spot/symbol=BTCUSDT/window=2023-03-25_2023-06-22/date=2023-06-17/agg_trades.parquet`, `506817` lignes, checksum `203aeb3d8d2e759b742c406fad87989bac7255c05d00374cac3f16f59a4102f4`
- `2023-06-18` : `data/research/v7_7/trades/aggTrades/source=binance_archive/market_type=spot/symbol=BTCUSDT/window=2023-03-25_2023-06-22/date=2023-06-18/agg_trades.parquet`, `430860` lignes, checksum `82b100688cac125c6066a146d818f34a1ffa6172bdc81f247cad6287a3f6e5d9`
- `2023-06-19` : `data/research/v7_7/trades/aggTrades/source=binance_archive/market_type=spot/symbol=BTCUSDT/window=2023-03-25_2023-06-22/date=2023-06-19/agg_trades.parquet`, `558362` lignes, checksum `8bc588473c600ed9e30927ce5b4853807a254941b43fd4c47c7b9f11c62a9007`
- `2023-06-20` : `data/research/v7_7/trades/aggTrades/source=binance_archive/market_type=spot/symbol=BTCUSDT/window=2023-03-25_2023-06-22/date=2023-06-20/agg_trades.parquet`, `859875` lignes, checksum `fe684dfe5c3a87ae6a3f7c509dd78db15e818853e392760068874583f8e5245e`
- `2023-06-21` : `data/research/v7_7/trades/aggTrades/source=binance_archive/market_type=spot/symbol=BTCUSDT/window=2023-03-25_2023-06-22/date=2023-06-21/agg_trades.parquet`, `1371327` lignes, checksum `94804c362c52b8f4b9cef60c4026055763cda4fe3605960c9aa49d69a444e1e6`
- `2023-06-22` : `data/research/v7_7/trades/aggTrades/source=binance_archive/market_type=spot/symbol=BTCUSDT/window=2023-03-25_2023-06-22/date=2023-06-22/agg_trades.parquet`, `866275` lignes, checksum `ba9cc48d563cc97613d1ff9a71cfbdac68af7e532e92f945ae0bc145b66bff34`

## Qualite

- Doublons `aggregate_trade_id` : `0`.
- IDs non monotones : `0`.
- Timestamps non monotones : `0`.
- Prix non positifs : `0`.
- Quantites non positives : `0`.
- Colonnes interdites : `[]`.

## Limitations

- V7.7 etend uniquement l'ingestion de trades publics aggTrades sur une fenetre bornee de 90 jours.
- V7.7 ne produit aucune feature, aucun label, aucun dataset ML, aucun modele ML, aucun backtest, aucune strategie et aucun ordre.

## Securite

V7.7 ne valide aucune strategie.
V7.7 ne produit aucune feature.
V7.7 ne produit aucun label.
V7.7 ne produit aucun dataset ML.
V7.7 ne produit aucun modele ML.
V7.7 ne produit aucun backtest.
V7.7 ne produit aucun signal de trading.
V7.7 ne produit aucun ordre.
V7.7 n'autorise aucun paper live.
V7.7 n'autorise aucun trading reel.
