from __future__ import annotations

class InputGuard:
    def __init__(self, data: dict[str, Any]):
        self.data = data

    def validate(self) -> dict[str, Any]:
        missing = [k for k, v in self.data.items() if v is None]
        passed = len(missing) == 0
        
        return {
            "status": "PASSED" if passed else "FAILED",
            "missing_inputs": missing,
            "input_guard_status": "PASSED" if passed else "FAILED"
        }
