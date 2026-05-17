import pandas as pd
import os

class MicrostructureDataLoader:
    def __init__(self, dataset_path: str, intrabar_path: str):
        self.dataset_path = dataset_path
        self.intrabar_path = intrabar_path

    def load_data(self) -> pd.DataFrame:
        if not os.path.exists(self.dataset_path):
            return pd.DataFrame()
        return pd.read_csv(self.dataset_path)

    def load_intrabar(self) -> pd.DataFrame:
        if not os.path.exists(self.intrabar_path):
            return pd.DataFrame()
        return pd.read_csv(self.intrabar_path)
