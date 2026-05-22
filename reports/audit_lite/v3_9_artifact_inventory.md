# Inventaire audit-lite V3.9

Ce rapport decrit les artefacts lourds exclus du ZIP `audit-lite`.

- Raw zips exclus : `90`
- Parquet complets exclus : `12`
- Validation full locale remplacee : `false`
- Note : `audit-lite does not replace full local validation`

## Samples Parquet scores inclus

- `1m` `ml_scores` : `data/audit_lite/v3_9/ml_scores/timeframe=1m/sample.parquet` (418 lignes)
- `5m` `ml_scores` : `data/audit_lite/v3_9/ml_scores/timeframe=5m/sample.parquet` (418 lignes)
- `15m` `ml_scores` : `data/audit_lite/v3_9/ml_scores/timeframe=15m/sample.parquet` (418 lignes)
- `1h` `ml_scores` : `data/audit_lite/v3_9/ml_scores/timeframe=1h/sample.parquet` (416 lignes)

## Garantie de scope

Les validateurs de production ne sont pas relaches. Le ZIP audit-lite sert a transmettre le code, les rapports, les manifests, les checksums et des samples stricts. Il ne pretend pas revalider physiquement les 90 jours sans les donnees completes locales.
