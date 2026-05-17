"""Diagnostic verdict and recommendation engine for V1.51."""
from typing import Dict, Any

class QualityMaskVerdict:
    def get_verdict(self, score: Dict[str, Any]) -> str:
        grade = score.get("grade", "F")
        if grade == "A":
            return "MICROSTRUCTURE_QUALITY_MASK_READY_FOR_NEXT_DIAGNOSTIC"
        elif grade in ["B", "C"]:
            return "MICROSTRUCTURE_QUALITY_MASK_PARTIAL_BUT_USABLE"
        else:
            return "MICROSTRUCTURE_QUALITY_MASK_BLOCKS_NEXT_DIAGNOSTIC"

class RecommendationEngine:
    def get_recommendation(self, verdict: str) -> str:
        if verdict == "MICROSTRUCTURE_QUALITY_MASK_READY_FOR_NEXT_DIAGNOSTIC":
            return "rerun micro-regime diagnostics under coverage quality mask"
        elif verdict == "MICROSTRUCTURE_QUALITY_MASK_PARTIAL_BUT_USABLE":
            return "improve intrabar data before applying quality mask"
        else:
            return "collect richer microstructure data before further research"
