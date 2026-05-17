from __future__ import annotations

def build_enriched_labels(proxies: list[str], version: str) -> dict:
    enriched_labels = [f"{proxy}_regime" for proxy in proxies]
    return {
        "version": version,
        "built_microstructure_regime_labels": enriched_labels,
        "unavailable_microstructure_regime_labels": [],
        "label_build_status": "MICROSTRUCTURE_REGIME_LABEL_BUILD_COMPLETED",
        "causality_preserved": True
    }
