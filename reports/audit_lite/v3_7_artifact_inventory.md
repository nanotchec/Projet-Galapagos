# Inventaire audit-lite V3.7

Ce rapport decrit les artefacts lourds exclus du ZIP `audit-lite`.

- Raw zips exclus : `90`
- Parquet complets exclus : `12`
- Validation full locale remplacee : `false`
- Note : `audit-lite does not replace full local validation`

## Samples Parquet labels inclus

- `1m` : `data/audit_lite/v3_7/labels/timeframe=1m/sample.parquet` (418 lignes)
- `5m` : `data/audit_lite/v3_7/labels/timeframe=5m/sample.parquet` (418 lignes)
- `15m` : `data/audit_lite/v3_7/labels/timeframe=15m/sample.parquet` (417 lignes)
- `1h` : `data/audit_lite/v3_7/labels/timeframe=1h/sample.parquet` (409 lignes)

## Garantie de scope

Les validateurs de production ne sont pas relaches. Le ZIP audit-lite sert a transmettre le code, les rapports, les manifests, les checksums et des samples stricts. Il ne pretend pas revalider physiquement les 90 jours sans les raw zips et Parquet complets locaux.
