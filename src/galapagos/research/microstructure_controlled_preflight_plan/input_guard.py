def validate_input(baseline: dict) -> dict:
    if baseline.get("version") != "V1.58.2":
         return {"status": "FAILED", "reason": "Invalid baseline version"}
    return {"status": "PASSED"}
