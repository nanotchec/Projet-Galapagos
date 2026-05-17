from typing import Any, Dict

class ApprovalPhraseValidator:
    def __init__(self):
        self.required_phrase = "I explicitly approve a two-request tiny network preflight with reports-only output, no data directory writes, and no trading."

    def validate(self, input_phrase: str) -> Dict[str, Any]:
        provided = bool(input_phrase and input_phrase.strip())
        validated = input_phrase == self.required_phrase
        
        return {
            "approval_phrase_required": True,
            "required_approval_phrase": self.required_phrase,
            "approval_phrase_input_present": provided,
            "approval_phrase_provided": provided,
            "approval_phrase_validated": validated,
            "human_approval_granted": validated
        }
