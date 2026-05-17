from __future__ import annotations

def create_inventory(built_labels: list[str], version: str) -> dict:
    return {
        "version": version,
        "label_inventory": built_labels,
        "label_inventory_status": "MICROSTRUCTURE_ENRICHED_LABEL_INVENTORY_COMPLETED"
    }
