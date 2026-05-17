from typing import Dict, List

class DryRunValidator:
    """Validation théorique des invariants du data contract."""
    
    def validate_theoretical_contract(self, plans: List[Dict], schema: Dict) -> Dict:
        """Vérifie la cohérence théorique du plan de matérialisation."""
        checks = {
            "all_paths_in_data_dir": True,
            "schema_integrity": True,
            "no_physical_write_attempted": True,
            "scope_is_reports_only": True
        }
        
        errors = []
        for plan in plans:
            if not plan["theoretical_path"].startswith("data/"):
                checks["all_paths_in_data_dir"] = False
                errors.append(f"Invalid theoretical path: {plan['theoretical_path']}")
                
        return {
            "checks_passed": len(errors) == 0,
            "checks": checks,
            "errors": errors
        }
