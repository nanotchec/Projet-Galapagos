def make_decision(version: str) -> dict:
    return {
        "version": version, "current_version": version,
        "preflight_plan_ready": True,
        "verdict": "MICROSTRUCTURE_PREFLIGHT_PLAN_READY",
        "next_allowed_phase": "controlled_local_preflight_dryrun",
        "evidence_classification": "INFRASTRUCTURE_ONLY",
        "policy_alignment_confirmed": True
    }
