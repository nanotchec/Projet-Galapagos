# OHLCV Resampling V2.4

V2.4 construit une couche de resampling OHLCV normalise a partir du silver 1m valide en V2.3.1.

Correction V2.4.1 : V2.4 a ete refusee en validation stricte externe car le manifest et le rapport qualite pouvaient declarer des valeurs incoherentes avec les fichiers physiques. V2.4.1 conserve les artefacts de resampling V2.4, recalcule la qualite physique par timeframe et valide le rapport JSON comme projection deterministe du manifest.

Correction V2.4.2 : V2.4.1 a ete refusee car le manifest et le rapport JSON acceptaient encore des cles supplementaires mensongeres. V2.4.2 ajoute `correction_version = V2.4.2`, impose un schema strict top-level et sous-blocs, et scanne le Markdown pour les fausses claims evidentes.

Correction V2.4.3 : V2.4.2 a ete refusee car `limitations` pouvait encore contenir des claims positives synchronisees, et parce que le runtime du fichier complet de tests validateur devait etre durci. V2.4.3 ajoute `correction_version = V2.4.3`, impose les limitations attendues exactes, scanne les claims positives dans le manifest et le rapport JSON, valide strictement `created_at_utc` et `resampling_run_id`, et optimise les tests par template physique recopie.

## Objectif

L'objectif est de produire des fichiers Parquet silver 5m, 15m et 1h deterministes, audites physiquement et comparables a leur parent 1m. Cette version reste strictement data-only.

## Entree

- Source : silver OHLCV V2.3.1
- Symbole : `BTCUSDT`
- Venue : `binance`
- Market type : `spot`
- Timeframe source : `1m`
- Date : `2024-01-15`
- Lignes attendues : `1440`

## Sorties

- `5m` : `288` lignes attendues
- `15m` : `96` lignes attendues
- `1h` : `24` lignes attendues

## Regles d'agregation

Pour chaque bucket complet :

- `open` = premier open du bucket ;
- `high` = maximum des high ;
- `low` = minimum des low ;
- `close` = dernier close du bucket ;
- `volume`, `quote_volume`, `trade_count`, `taker_buy_base_volume`, `taker_buy_quote_volume` = sommes ;
- `event_ts` = debut du bucket ;
- `close_ts` = close timestamp de la derniere bougie 1m du bucket ;
- `available_ts = close_ts` ;
- `decision_ts = available_ts`.

Aucun bucket partiel n'est materialise.

## Parent-child consistency

Le validateur V2.4 relit physiquement le silver 1m, recalcule les sorties 5m, 15m et 1h, puis compare ces resultats aux Parquet ecrits. Une mutation d'un high, d'un volume, d'un close, d'un ordre physique ou d'une provenance doit faire echouer la validation, meme si le checksum du manifest est resynchronise.

En V2.4.1, le validateur compare aussi strictement `manifest["quality"][timeframe]` avec la qualite recalculee pour `1m`, `5m`, `15m` et `1h`. Le rapport `reports/data_quality/ohlcv_resampling_v2_4.json` doit correspondre au manifest sur `version`, `correction_version`, `status`, `created_at_utc`, `resampling_run_id`, `input_1m`, `outputs`, `expected_rows`, `quality`, `parent_child_consistency`, `safety` et `limitations`. En V2.4.2, toute cle inattendue dans ces structures fait echouer la validation. En V2.4.3, les limitations doivent correspondre exactement a la liste attendue et les champs `created_at_utc` / `resampling_run_id` doivent respecter leur format strict.

## Timestamps et provenance

Les timestamps restent en UTC. Les colonnes `raw_file_sha256`, `ingestion_run_id` et `ingested_at_ts` sont conservees depuis le parent 1m et verifiees physiquement.

## Limitations

V2.4 est limitee a BTCUSDT spot sur la date fixe `2024-01-15`. Elle ne cree aucune nouvelle source, aucun carnet d'ordres, aucun trade tick, aucun funding et aucun open interest.

## Securite

V2.4 ne valide aucune strategie. V2.4 ne valide aucun modele ML. V2.4 ne produit aucun signal de trading. V2.4 ne produit aucun ordre. V2.4 n'autorise aucun paper live. V2.4 ne fait aucun backtest. V2.4 est uniquement une etape de stockage/resampling OHLCV data-only.
