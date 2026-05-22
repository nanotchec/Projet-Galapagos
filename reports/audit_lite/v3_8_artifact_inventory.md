# Inventaire audit-lite V3.8

Ce rapport decrit les artefacts lourds exclus du ZIP `audit-lite`.

- Raw zips exclus : `90`
- Parquet complets exclus : `20`
- Validation full locale remplacee : `false`
- Note : `audit-lite does not replace full local validation`

## Samples Parquet dataset/splits inclus

- `1m` `dataset` : `data/audit_lite/v3_8/datasets/timeframe=1m/sample.parquet` (418 lignes)
- `1m` `splits` : `data/audit_lite/v3_8/datasets/timeframe=1m/splits_sample.parquet` (418 lignes)
- `5m` `dataset` : `data/audit_lite/v3_8/datasets/timeframe=5m/sample.parquet` (418 lignes)
- `5m` `splits` : `data/audit_lite/v3_8/datasets/timeframe=5m/splits_sample.parquet` (418 lignes)
- `15m` `dataset` : `data/audit_lite/v3_8/datasets/timeframe=15m/sample.parquet` (417 lignes)
- `15m` `splits` : `data/audit_lite/v3_8/datasets/timeframe=15m/splits_sample.parquet` (417 lignes)
- `1h` `dataset` : `data/audit_lite/v3_8/datasets/timeframe=1h/sample.parquet` (409 lignes)
- `1h` `splits` : `data/audit_lite/v3_8/datasets/timeframe=1h/splits_sample.parquet` (409 lignes)

## Garantie de scope

Les validateurs de production ne sont pas relaches. Le ZIP audit-lite sert a transmettre le code, les rapports, les manifests, les checksums et des samples stricts. Il ne pretend pas revalider physiquement les 90 jours sans les raw zips et Parquet complets locaux.
