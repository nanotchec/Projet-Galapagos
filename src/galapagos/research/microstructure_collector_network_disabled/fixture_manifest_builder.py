from __future__ import annotations
from typing import List, Dict, Any
from .normalized_record_schema import NormalizedMicrostructureRecord


class FixtureManifestBuilder:
    """Builds theoretical manifests for processed fixtures (V1.55)."""

    @staticmethod
    def build_manifest(records: List[NormalizedMicrostructureRecord]) -> Dict[str, Any]:
        """Creates a theoretical manifest summary for a set of normalized records."""
        if not records:
            return {"count": 0, "status": "EMPTY"}
            
        sources = sorted(list(set(r.source for r in records)))
        symbols = sorted(list(set(r.symbol for r in records)))
        
        return {
            "count": len(records),
            "sources": sources,
            "symbols": symbols,
            "min_event_ts": min(r.event_ts for r in records),
            "max_event_ts": max(r.event_ts for r in records),
            "causality_verified": all(r.event_ts <= r.available_ts <= r.ingest_ts for r in records),
            "fixture_only": True,
            "synthetic_or_minimal_sample": True,
            "not_for_research_results": True
        }
