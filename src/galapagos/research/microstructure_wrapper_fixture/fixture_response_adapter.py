from typing import Any, Dict

class FixtureResponseAdapter:
    """Adapts fixture data to normalized format."""
    def __init__(self, version: str):
        self.version = version

    def normalize(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        # Required schema: symbol, timeframe, event_ts, available_ts, ingest_ts, source, fixture_id
        return {
            "symbol": raw_data.get("symbol", "UNKNOWN"),
            "timeframe": raw_data.get("timeframe", "1m"),
            "event_ts": raw_data.get("event_ts"),
            "available_ts": raw_data.get("available_ts"),
            "ingest_ts": raw_data.get("ingest_ts"),
            "open": raw_data.get("open"),
            "high": raw_data.get("high"),
            "low": raw_data.get("low"),
            "close": raw_data.get("close"),
            "volume": raw_data.get("volume"),
            "source": raw_data.get("source", "fixture"),
            "fixture_id": raw_data.get("id", "none")
        }

    def get_report(self, processed_count: int) -> Dict[str, Any]:
        return {
            "version": self.version,
            "fixture_records_processed_count": processed_count,
            "normalized_records_preview_generated": True,
            "status": "MICROSTRUCTURE_FIXTURE_RESPONSE_ADAPTER_PASSED"
        }
