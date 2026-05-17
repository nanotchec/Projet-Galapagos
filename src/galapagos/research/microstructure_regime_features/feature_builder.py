import pandas as pd
import numpy as np

class MicrostructureFeatureBuilder:
    def __init__(self):
        pass

    def build_features(self, df: pd.DataFrame) -> pd.DataFrame:
        features = pd.DataFrame(index=df.index)
        
        if 'close' in df.columns and 'volume' in df.columns:
            # Amihud Illiquidity proxy (simplified)
            returns = df['close'].pct_change().abs()
            features['amihud_illiquidity'] = returns / (df['volume'] + 1e-9)
            
            # Volatility proxy
            features['realized_vol_proxy'] = returns.rolling(window=20).std()
            
            # Volume/Volatility ratio
            features['volume_vol_ratio'] = df['volume'] / (features['realized_vol_proxy'] + 1e-9)
            
        if 'high' in df.columns and 'low' in df.columns:
            # Intraday range
            features['intraday_range'] = (df['high'] - df['low']) / (df['low'] + 1e-9)
            
        return features.fillna(0)
