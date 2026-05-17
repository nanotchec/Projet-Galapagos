import re
from pathlib import Path
from typing import Any, Dict, List

class TestQualityAudit:
    def scan_test_file(self, test_file_path: Path) -> Dict[str, Any]:
        if not test_file_path.exists():
            return {
                "test_quality_audit_enabled": True,
                "test_file_scanned": False,
                "discovered_test_functions_count": 0,
                "pass_only_tests_count": 0,
                "pass_only_tests": [],
                "placeholder_tests_count": 0,
                "placeholder_tests": [],
                "weak_tests_count": 0,
                "weak_tests": [],
                "test_quality_passed": False
            }

        with open(test_file_path) as f:
            content = f.read()

        # Find all test functions and their bodies
        test_blocks = re.findall(r"(^def (test_[a-zA-Z0-9_]+)\(.*?:\n(?:(?!\n^def).*\n)*)", content, re.MULTILINE)
        
        discovered_test_functions_count = len(test_blocks)
        pass_only_tests = []
        placeholder_tests = []
        forbidden_test_names = []
        weak_tests = []

        placeholders_keywords = ["placeholder", "remaining", "todo", "stub", "dummy"]
        forbidden_keywords = ["ph_tests", "placeholder", "remaining", "todo", "stub", "dummy"]

        for full_block, func_name in test_blocks:
            # Extract body
            lines = full_block.splitlines()
            body_lines = [l.strip() for l in lines[1:] if l.strip()]
            body_content = "\n".join(body_lines)

            # 1. Forbidden names
            if any(k in func_name.lower() for k in forbidden_keywords):
                forbidden_test_names.append(func_name)

            # 2. Pass only or Ellipsis only
            if body_content == "pass" or body_content == "...":
                pass_only_tests.append(func_name)
                continue

            # 3. Placeholder in body (whole word)
            has_placeholder_in_body = any(re.search(r"\b" + k + r"\b", body_content.lower()) for k in placeholders_keywords)
            
            if has_placeholder_in_body:
                placeholder_tests.append(func_name)
                continue

            # 4. Weak tests
            verifiable_keywords = ["assert", "pytest.raises", "subprocess", "check_safety", "validate_approval", "compare_files", "get_coverage_report", "scan_test_file", "audit_release", "check_portability"]
            is_verifiable = any(k in body_content for k in verifiable_keywords)
            
            if not is_verifiable:
                weak_tests.append(func_name)

        # 5. Anti-Tautology (AST)
        from galapagos.research.microstructure_data_contract_approval_intake.anti_tautology_audit import AntiTautologyAudit
        ata = AntiTautologyAudit()
        ast_results = ata.scan_file(test_file_path)

        merged_weak_tests = sorted(set(weak_tests + ast_results.get("weak_tests", [])))

        test_quality_passed = (
            len(pass_only_tests) == 0 and
            len(placeholder_tests) == 0 and
            len(forbidden_test_names) == 0 and
            len(merged_weak_tests) == 0 and
            ast_results.get("test_quality_passed", False)
        )

        return {
            "test_quality_audit_enabled": True,
            "test_file_scanned": True,
            "discovered_test_functions_count": discovered_test_functions_count,
            "pass_only_tests_count": len(pass_only_tests),
            "pass_only_tests": pass_only_tests,
            "placeholder_tests_count": len(placeholder_tests),
            "placeholder_tests": placeholder_tests,
            "forbidden_test_names_count": len(forbidden_test_names),
            "forbidden_test_names": forbidden_test_names,
            "weak_tests_count": len(merged_weak_tests),
            "weak_tests": merged_weak_tests,
            "tautological_tests_count": ast_results.get("tautological_tests_count", 0),
            "tautological_tests": ast_results.get("tautological_tests", []),
            "or_true_tests_count": ast_results.get("or_true_tests_count", 0),
            "or_true_tests": ast_results.get("or_true_tests", []),
            "and_true_tests_count": ast_results.get("and_true_tests_count", 0),
            "and_true_tests": ast_results.get("and_true_tests", []),
            "assert_true_tests_count": ast_results.get("assert_true_tests_count", 0),
            "assert_true_tests": ast_results.get("assert_true_tests", []),
            "test_quality_passed": test_quality_passed,
            "test_count_reported": discovered_test_functions_count
        }
