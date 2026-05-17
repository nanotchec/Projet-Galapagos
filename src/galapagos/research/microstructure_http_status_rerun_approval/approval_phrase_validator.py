from typing import Any, Dict

class ApprovalPhraseValidator:
    def __init__(self):
        self.required_phrase = "I explicitly approve a bounded reports-only HTTP-status rerun with at most 10 public requests, no data directory writes, no dataset creation, and no trading."

    def validate_phrase(self, phrase: str) -> Dict[str, Any]:
        is_valid = phrase == self.required_phrase
        return {
            "approval_phrase_input_present": True,
            "approval_phrase_provided": bool(phrase),
            "approval_phrase_validated": is_valid,
            "human_approval_granted": is_valid,
            "required_approval_phrase": self.required_phrase
        }
