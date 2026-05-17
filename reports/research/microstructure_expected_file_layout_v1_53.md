# Microstructure Expected File Layout V1 53

```json
{
  "status": "EXPECTED_FILE_LAYOUT_DEFINED",
  "layout": {
    "bronze": "data/bronze/microstructure/{source}/{symbol}/{timeframe}/{year}/{month}/",
    "silver": "data/silver/microstructure/{source}/{symbol}/{timeframe}/",
    "manifests": "data/manifests/microstructure/{source}/{symbol}/{timeframe}/",
    "qc_reports": "reports/qc/microstructure/{source}/{symbol}/{timeframe}/"
  },
  "file_naming_convention": "{symbol}_{timeframe}_{start_date}_{end_date}.parquet",
  "manifest_naming_convention": "{symbol}_{timeframe}_{start_date}_{end_date}_manifest.json"
}
```
