class MicrostructureQualityScorecard:
    def __init__(self):
        pass

    def build_scorecard(self, coverage, missingness, stability, relevance, causal) -> dict:
        scorecard = {
            "overall_quality_score": 0.0,
            "metrics": {
                "coverage_score": coverage.get("coverage_ratio", 0.0),
                "causal_availability_score": causal.get("causal_availability_score", 0.0),
                "missingness_penalty": sum(missingness.get("missing_ratios", {}).values()) / len(missingness.get("missing_ratios", {})) if missingness.get("missing_ratios") else 1.0,
                "stability_average": sum(m.get("autocorr_lag1", 0.0) for m in stability.get("stability_metrics", {}).values()) / len(stability.get("stability_metrics", {})) if stability.get("stability_metrics") else 0.0
            }
        }
        scorecard["overall_quality_score"] = (scorecard["metrics"]["coverage_score"] + scorecard["metrics"]["causal_availability_score"]) / 2.0
        
        return {
            "status": "MICROSTRUCTURE_SCORECARD_COMPLETED",
            "scorecard": scorecard
        }
