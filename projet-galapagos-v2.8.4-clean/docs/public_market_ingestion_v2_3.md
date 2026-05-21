# Public Market Ingestion V2.3

V2.3 introduit une premiere ingestion physique de donnees marche publiques reelles pour Galapagos. L'objectif est volontairement borne : prouver que le projet sait recuperer une archive publique read-only, conserver le raw immuable, produire un silver OHLCV normalise, calculer des checksums, produire un rapport qualite et valider physiquement les fichiers.

## Source

- Source : Binance public data archive
- Hote autorise : `data.binance.vision`
- Market type : `spot`
- Symbole : `BTCUSDT`
- Timeframe : `1m`
- Date fixe : `2024-01-15`

BTCUSDT est utilise comme premier actif parce qu'il est liquide, standard et disponible dans les archives publiques. Le timeframe `1m` permet de tester la granularite fine sans telecharger un historique massif. Une seule journee complete limite le scope a `1440` bougies attendues.

## Raw vs silver

Le raw ZIP est stocke sans transformation sous `data/raw/public_market/`. Le silver Parquet est une table OHLCV normalisee sous `data/silver/market_data/ohlcv/`.

Le raw reste la source immuable. Le silver est un artefact de normalisation auditable.

## Timestamps

Les timestamps normalises sont en UTC :

- `event_ts` : ouverture de bougie ;
- `close_ts` : fermeture de bougie ;
- `available_ts >= close_ts` ;
- `decision_ts >= available_ts` ;
- `ingested_at_ts` : date UTC de l'ingestion.

La regle physique est : `event_ts < close_ts <= available_ts <= decision_ts`.

## Qualite

Le rapport qualite controle le nombre de lignes, les doublons, les trous temporels, les violations OHLC, les volumes negatifs, les nulls critiques, la monotonie temporelle et les checksums raw/silver.

Correction V2.3.1 :

- la monotonie `event_ts` est verifiee dans l'ordre physique du Parquet ;
- le raw ZIP est reparsse et compare strictement au silver Parquet ;
- un nombre de lignes different de `1440` est une erreur, pas un simple warning ;
- la colonne `normalized_file_sha256` a ete supprimee du silver, car un fichier ne peut pas porter son propre checksum final de maniere stable.

Durcissement V2.4.4 applique aux artefacts V2.3 inclus :

- le manifest V2.3 et le rapport qualite V2.3 ont des schemas stricts ;
- les limitations V2.3 doivent correspondre exactement aux limitations attendues ;
- les claims positives de type strategie validee, trading active, ordre active, ML valide ou backtest valide sont scannees dans les JSON et le Markdown ;
- `created_at_utc` et `ingestion_run_id` sont valides physiquement.

## Securite

V2.3 utilise uniquement une source publique read-only. Aucune cle API, aucun secret, aucun endpoint prive et aucune authentification ne sont utilises.

V2.3 ne valide aucune strategie. V2.3 ne valide aucun modele ML. V2.3 ne produit aucun signal de trading. V2.3 ne produit aucun ordre. V2.3 n'autorise aucun paper live. V2.3 est uniquement une preview d'ingestion de donnees publiques reelles.

## Statut

V2.3.1 est la derniere version validee pour le scope ingestion publique read-only. V2.4.4 reutilise ces artefacts comme source incluse et durcit leur validation contre les fausses claims.
