"""Coverage gap specification for Microstructure Data Enrichment Spec (V1.52)."""

class CoverageGapSpec:
    def __init__(self, quality_mask_summary):
        self.quality_mask_summary = quality_mask_summary

    def analyze(self):
        impact = self.quality_mask_summary.get("impact", {}) if self.quality_mask_summary else {}
        return {
            "status": "COMPLETED",
            "priority_gap_periods": ["2026-H1", "2026-H2"],
            "priority_gap_2026": True,
            "blocked_ratio_2026": impact.get("blocked_ratio_2026", 1.0),
            "gap_explanation": "Total lack of intrabar (5m) microstructure data for 2026 BTC dataset."
        }
