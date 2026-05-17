from typing import Any

def generate_recommendation(decision_results: dict[str, Any]) -> dict[str, Any]:
    """
    Generates the recommendation based on the wrapper plan completeness.
    """
    if decision_results.get("wrapper_plan_ready"):
        recommended_next_step = "implement network-disabled wrapper with local fixtures only"
    else:
        recommended_next_step = "refine network-disabled wrapper plan before any implementation"

    return {
        "status": "MICROSTRUCTURE_WRAPPER_RECOMMENDATION_GENERATED",
        "recommended_next_step": recommended_next_step,
        "wrapper_plan_ready": decision_results.get("wrapper_plan_ready"),
        "final_verdict": decision_results.get("final_verdict"),
        "next_allowed_phase": decision_results.get("next_allowed_phase"),
    }
