"""Data loader for Microstructure Data Enrichment Spec (V1.52)."""
import pandas as pd
from pathlib import Path
import json

class EnrichmentDataLoader:
    def __init__(self, predictions_path=None, dataset_path=None, alpha_dataset_path=None, intrabar_path=None):
        self.predictions_path = predictions_path
        self.dataset_path = dataset_path
        self.alpha_dataset_path = alpha_dataset_path
        self.intrabar_path = intrabar_path

    def load_inventory(self):
        inventory = {}
        paths = {
            "predictions": self.predictions_path,
            "dataset": self.dataset_path,
            "alpha_dataset": self.alpha_dataset_path,
            "intrabar": self.intrabar_path
        }
        for key, path in paths.items():
            if path and Path(path).exists():
                inventory[key] = {
                    "path": str(path),
                    "size": Path(path).stat().st_size,
                    "exists": True
                }
            else:
                inventory[key] = {"exists": False}
        return inventory

    def load_report(self, path):
        if path and Path(path).exists():
            with open(path, "r") as f:
                return json.load(f)
        return None
