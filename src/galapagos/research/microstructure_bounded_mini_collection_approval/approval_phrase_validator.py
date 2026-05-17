from typing import Any, Dict

class ApprovalPhraseValidator:
    def __init__(self):
        self.required_phrase = "I explicitly approve a bounded reports-only mini-collection with at most 10 public requests, no data directory writes, no dataset creation, and no trading."

    def validate_phrase(self, input_phrase: str) -> Dict[str, Any]:
        is_exact = input_phrase == self.required_phrase
        return {
            "approval_phrase_input_present": bool(input_phrase),
            "approval_phrase_provided": bool(input_phrase),
            "approval_phrase_validated": is_exact,
            "human_approval_granted": is_exact,
            "required_phrase_match": is_exact
        }
