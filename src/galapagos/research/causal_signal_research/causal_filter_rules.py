from __future__ import annotations

import pandas as pd
from galapagos.research.causal_signal_research.causal_filter_schema import CausalFilter, CausalFilterMetadata

class ProbabilityThreshold(CausalFilter):
    def __init__(self, threshold: float):
        self.threshold = threshold
        
    def get_metadata(self) -> CausalFilterMetadata:
        return CausalFilterMetadata(
            name=f"prob_ge_{self.threshold}",
            family="probability_threshold",
            description=f"Predicted probability >= {self.threshold}",
            parameters={"threshold": self.threshold}
        )
        
    def apply(self, df: pd.DataFrame) -> pd.Series:
        if "predicted_probability" not in df:
            return pd.Series(False, index=df.index)
        return pd.to_numeric(df["predicted_probability"], errors="coerce").fillna(0) >= self.threshold

class FirstAboveThresholdPerPeriod(CausalFilter):
    def __init__(self, threshold: float, period: str = "7D"):
        self.threshold = threshold
        self.period = period
        
    def get_metadata(self) -> CausalFilterMetadata:
        return CausalFilterMetadata(
            name=f"first_ge_{self.threshold}_per_{self.period}",
            family="first_per_period",
            description=f"First signal >= {self.threshold} in each {self.period} window",
            parameters={"threshold": self.threshold, "period": self.period}
        )
        
    def apply(self, df: pd.DataFrame) -> pd.Series:
        if "predicted_probability" not in df or "timestamp" not in df:
            return pd.Series(False, index=df.index)
            
        work = df.copy()
        work["timestamp"] = pd.to_datetime(work["timestamp"], utc=True)
        work["_score"] = pd.to_numeric(work["predicted_probability"], errors="coerce").fillna(0)
        
        # Filter candidates above threshold first
        above = work[work["_score"] >= self.threshold].copy()
        if above.empty:
            return pd.Series(False, index=df.index)
            
        # Group by period and take the first arrival
        above["_period"] = above["timestamp"].dt.floor(self.period)
        idx = above.sort_values("timestamp").groupby("_period").head(1).index
        
        mask = pd.Series(False, index=df.index)
        mask.loc[idx] = True
        return mask

class CausalRunningTopScore(CausalFilter):
    """Signal if current score is the best seen so far in the period AND >= threshold."""
    def __init__(self, threshold: float, period: str = "7D"):
        self.threshold = threshold
        self.period = period
        
    def get_metadata(self) -> CausalFilterMetadata:
        return CausalFilterMetadata(
            name=f"running_top_ge_{self.threshold}_per_{self.period}",
            family="running_top",
            description=f"Running best score in {self.period} >= {self.threshold}",
            parameters={"threshold": self.threshold, "period": self.period}
        )
        
    def apply(self, df: pd.DataFrame) -> pd.Series:
        if "predicted_probability" not in df or "timestamp" not in df:
            return pd.Series(False, index=df.index)
            
        work = df.copy()
        work["timestamp"] = pd.to_datetime(work["timestamp"], utc=True)
        work["_score"] = pd.to_numeric(work["predicted_probability"], errors="coerce").fillna(0)
        work["_period"] = work["timestamp"].dt.floor(self.period)
        
        work = work.sort_values("timestamp")
        
        # Calculate running max per period
        work["_running_max"] = work.groupby("_period")["_score"].cummax()
        
        # Condition: current score is the running max AND >= threshold
        # To avoid multiple trades in same period if they have same running max, 
        # we only take the first time this happens in the period.
        
        mask_cond = (work["_score"] == work["_running_max"]) & (work["_score"] >= self.threshold)
        eligible = work[mask_cond].copy()
        
        if eligible.empty:
            return pd.Series(False, index=df.index)
            
        idx = eligible.groupby("_period").head(1).index
        
        mask = pd.Series(False, index=df.index)
        mask.loc[idx] = True
        return mask

class CooldownFilter(CausalFilter):
    def __init__(self, threshold: float, cooldown_hours: int = 168):
        self.threshold = threshold
        self.cooldown = pd.Timedelta(hours=cooldown_hours)
        
    def get_metadata(self) -> CausalFilterMetadata:
        return CausalFilterMetadata(
            name=f"prob_ge_{self.threshold}_cooldown_{self.cooldown}",
            family="cooldown",
            description=f"Prob >= {self.threshold} with {self.cooldown} cooldown",
            parameters={"threshold": self.threshold, "cooldown_hours": self.cooldown.total_seconds()/3600}
        )
        
    def apply(self, df: pd.DataFrame) -> pd.Series:
        if "predicted_probability" not in df or "timestamp" not in df:
            return pd.Series(False, index=df.index)
            
        work = df.copy()
        work["timestamp"] = pd.to_datetime(work["timestamp"], utc=True)
        work["_score"] = pd.to_numeric(work["predicted_probability"], errors="coerce").fillna(0)
        
        ordered = work.sort_values("timestamp")
        keep = pd.Series(False, index=df.index)
        last_kept = None
        
        for idx, row in ordered.iterrows():
            if row["_score"] >= self.threshold:
                ts = row["timestamp"]
                if last_kept is None or ts - last_kept >= self.cooldown:
                    keep.loc[idx] = True
                    last_kept = ts
        return keep
