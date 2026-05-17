from typing import Any, Dict

class ApprovalPhraseValidator:
    REQUIRED_PHRASE = "I explicitly approve a one-request tiny network preflight with no data directory writes and no trading."

    def validate_phrase(self, phrase_input: str) -> Dict[str, Any]:
        is_exact = (phrase_input == self.REQUIRED_PHRASE)
        return {
            "approval_phrase_provided": bool(phrase_input),
            "approval_phrase_validated": is_exact,
            "required_approval_phrase": self.REQUIRED_PHRASE
        }
