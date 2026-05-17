from __future__ import annotations
from typing import Dict, List, Any

class AdapterFieldGapAnalyzer:
    """Analyzes the gap between required fields and actual adapter mappings."""

    def __init__(self, classification: Dict[str, Any]):
        self.classification = classification
        self.alias_map = classification["field_alias_map"]

    def analyze(self, mapped_fields: Dict[str, List[str]]) -> Dict[str, Any]:
        report = {}
        for adapter, fields in mapped_fields.items():
            covered_internal = set(fields)
            
            covered_v152 = []
            missing_mandatory = []
            missing_optional = []
            
            for v152_name in self.classification["mandatory_for_offline_review"]:
                internal_name = self.alias_map.get(v152_name)
                if internal_name in covered_internal:
                    covered_v152.append(v152_name)
                else:
                    missing_mandatory.append(v152_name)
            
            for v152_name in self.classification["optional_for_real_collection"]:
                internal_name = self.alias_map.get(v152_name)
                if internal_name in covered_internal:
                    covered_v152.append(v152_name)
                else:
                    missing_optional.append(v152_name)
            
            report[adapter] = {
                "covered_required_fields": sorted(covered_v152),
                "still_missing_mandatory": sorted(missing_mandatory),
                "still_missing_optional": sorted(missing_optional)
            }
        
        return report
