from __future__ import annotations

class FieldCoverageAnalyzer:
    def __init__(self, required_fields: list[str]):
        self.required_fields = required_fields

    def analyze(self, mapped_fields: dict[str, list[str]]) -> dict[str, Any]:
        report = {}
        for adapter, fields in mapped_fields.items():
            # Standardize names for comparison (v1.52 used _5m suffix, v1.55 stubs might not)
            norm_required = {f.replace("_5m", "") for f in self.required_fields}
            norm_mapped = {f for f in fields}
            
            covered = norm_required.intersection(norm_mapped)
            missing = norm_required.difference(norm_mapped)
            
            report[adapter] = {
                "covered_fields": sorted(list(covered)),
                "missing_required_fields": sorted(list(missing)),
                "coverage_ratio": len(covered) / len(norm_required) if norm_required else 1.0
            }
        
        all_adapters_covered = all(not r["missing_required_fields"] for r in report.values())
        
        return {
            "status": "PASSED" if all_adapters_covered else "PARTIAL",
            "adapters": report,
            "all_adapters_covered": all_adapters_covered
        }
