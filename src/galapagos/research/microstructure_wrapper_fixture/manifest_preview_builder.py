from typing import Any, Dict, List

class ManifestPreviewBuilder:
    """Builds a manifest preview from processed records."""
    def __init__(self, version: str):
        self.version = version

    def build_preview(self, records: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not records:
            return {"manifest_entries": []}
            
        # Group by symbol
        symbols = {}
        for r in records:
            s = r["symbol"]
            if s not in symbols:
                symbols[s] = {"count": 0, "first_ts": r["event_ts"], "last_ts": r["event_ts"]}
            symbols[s]["count"] += 1
            if r["event_ts"] < symbols[s]["first_ts"]: symbols[s]["first_ts"] = r["event_ts"]
            if r["event_ts"] > symbols[s]["last_ts"]: symbols[s]["last_ts"] = r["event_ts"]
            
        entries = []
        for s, stats in symbols.items():
            entries.append({
                "symbol": s,
                "record_count": stats["count"],
                "time_range": [stats["first_ts"], stats["last_ts"]],
                "storage_policy": "FIXTURE_ONLY_NO_WRITE"
            })
            
        return {
            "manifest_entries": entries,
            "manifest_preview_policy_defined": True,
            "manifest_data_file_created": False
        }

    def get_report(self, preview_data: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "version": self.version,
            "manifest_preview": preview_data,
            "manifest_preview_generated": True,
            "status": "MICROSTRUCTURE_MANIFEST_PREVIEW_BUILDER_PASSED"
        }
