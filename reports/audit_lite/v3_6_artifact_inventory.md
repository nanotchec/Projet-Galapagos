# Inventaire audit-lite V3.6

Ce rapport decrit les artefacts lourds exclus du ZIP `audit-lite`.

- Raw zips exclus : `90`
- Parquet complets exclus : `8`
- Validation full locale remplacee : `false`
- Note : `audit-lite does not replace full local validation`

## Samples Parquet inclus

- `1m` : `data/audit_lite/v3_6/features/timeframe=1m/sample.parquet` (398 lignes)
- `5m` : `data/audit_lite/v3_6/features/timeframe=5m/sample.parquet` (398 lignes)
- `15m` : `data/audit_lite/v3_6/features/timeframe=15m/sample.parquet` (397 lignes)
- `1h` : `data/audit_lite/v3_6/features/timeframe=1h/sample.parquet` (390 lignes)

## Garantie de scope

Les validateurs de production ne sont pas relaches. Le ZIP audit-lite sert a transmettre le code, les rapports, les manifests, les checksums et des samples stricts. Il ne pretend pas revalider physiquement les 90 jours sans les raw zips locaux.
