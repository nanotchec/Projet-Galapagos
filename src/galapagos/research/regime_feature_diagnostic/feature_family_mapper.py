"""Map features to families for V1.43 diagnostic."""
from __future__ import annotations

def map_feature_to_family(col: str) -> str:
    """Classify column based on name keywords."""
    c = col.lower()
    
    if any(k in c for k in [
        "forward_return", "target", "label", "outcome", "future", "payoff_raw",
        "max_favorable_excursion", "max_adverse_excursion", "mfe", "mae"
    ]):
        return "target_outcome_forbidden"
    
    # Metadata
    if any(k in c for k in ["timestamp", "period", "year", "month", "id", "symbol"]):
        return "metadata"
        
    # Microstructure
    if any(k in c for k in ["spread", "depth", "imbalance", "liq", "book"]):
        return "microstructure"
        
    # Volatility
    if any(k in c for k in ["volat", "atr", "std", "range"]):
        return "volatility"
        
    # Trend/Momentum
    if any(k in c for k in ["ema", "sma", "rsi", "macd", "momentum", "trend", "adx"]):
        return "trend_momentum"
        
    # Volume/Liquidity
    if any(k in c for k in ["volume", "vwa", "obv"]):
        return "volume_liquidity"
        
    # Returns
    if any(k in c for k in ["return", "change", "diff_pct"]):
        return "price_return"
        
    # Alpha outputs
    if any(k in c for k in ["alpha", "combined_score", "score"]):
        return "alpha_score_family"
        
    # Model outputs
    if any(k in c for k in ["prob", "logit", "prediction"]):
        return "model_output_family"
        
    # Regimes
    if "regime" in c:
        return "regime_proxy"
        
    return "unknown"
        
def map_feature_to_source_type(col: str) -> str:
    """Determine the source type of a feature for strict inventory semantics."""
    c = col.lower()
    
    # Outcomes (Forbidden) - FUTURE_OR_POST_TRADE_OUTCOME
    if any(k in c for k in [
        "forward_return", "target", "label", "outcome", "future", "payoff_raw",
        "max_favorable_excursion", "max_adverse_excursion", "mfe", "mae",
        "direction_up_after_cost", "tp_before_sl"
    ]):
        return "outcome_forbidden_feature"
        
    # Metadata
    if any(k in c for k in [
        "timestamp", "period", "year", "month", "id", "symbol",
        "model_name", "feature_set", "split_name", "timeframe"
    ]):
        return "metadata_feature"
        
    # Model Outputs (Diagnostic only)
    if any(k in c for k in [
        "predicted_probability", "calibrated_probability", "score_rebuilt", 
        "prediction_label", "logit", "predicted_label"
    ]):
        return "model_output_feature"
        
    # EV / Payoff Proxies
    if any(k in c for k in [
        "avg_win_past", "avg_loss_past", "proxy", "ev_calibrated_proxy",
        "ev_raw_proxy", "ev_proxy_ready", "payoff_estimate_ready"
    ]):
        return "ev_proxy_feature"
        
    # Alpha Scores (Pre-computed combined signals)
    if any(k in c for k in [
        "alpha_score", "combined_score", "macro_derivatives_score", "alpha_only",
        "ohlcv_quality_score", "volatility_quality_score", "volume_quality_score"
    ]):
        return "alpha_score_feature"
        
    # Regimes
    if "regime" in c:
        return "regime_proxy_feature"
        
    # Assume technical indicators / OHLCV / Funding / OI are raw market features
    return "raw_market_feature"
