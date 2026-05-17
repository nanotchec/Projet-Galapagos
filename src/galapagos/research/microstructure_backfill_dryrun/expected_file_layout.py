from __future__ import annotations


class ExpectedFileLayout:
    """Defines the directory layout for the downloaded microstructure data."""

    def analyze(self) -> dict:
        return {
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
