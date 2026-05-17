import re
import json
from pathlib import Path
from typing import Any, Dict, List

class ReleasePackagingAudit:
    REQUIRED_REPORTS_V1_81_6 = [
        "zip_audit_v1_81_6",
        "zip_smoke_test_v1_81_6",
        "release_zip_v1_81_6",
        "current_state_alignment_v1_81_6",
        "negative_test_coverage_v1_81_6",
        "test_quality_v1_81_6",
        "report_index_audit_v1_81_6",
        "portability_audit_v1_81_6",
        "metadata_audit_v1_81_6"
    ]

    # V1.81.7: noms canoniques dans reports/research/ (stems sans extension)
    REQUIRED_RESEARCH_REPORTS_V1_81_7 = [
        "microstructure_data_contract_approval_intake_corrective_summary_v1_81_7",
        "microstructure_data_contract_approval_intake_corrective_safety_check_v1_81_7",
        "microstructure_data_contract_approval_intake_corrective_negative_coverage_v1_81_7",
        "microstructure_data_contract_approval_intake_corrective_test_quality_audit_v1_81_7",
        "microstructure_data_contract_approval_intake_corrective_script_portability_audit_v1_81_7",
        "microstructure_data_contract_approval_intake_corrective_release_metadata_audit_v1_81_7",
        "microstructure_data_contract_approval_intake_corrective_current_state_alignment_v1_81_7",
        "microstructure_data_contract_approval_intake_corrective_release_packaging_audit_v1_81_7",
        "microstructure_data_contract_approval_intake_corrective_decision_v1_81_7",
        "microstructure_data_contract_approval_intake_corrective_consistency_check_v1_81_7",
        "v1_81_7_recommendation",
    ]

    REQUIRED_ROOT_REPORTS_V1_81_7 = [
        "zip_audit_v1_81_7",
        "zip_smoke_test_v1_81_7",
        "release_zip_v1_81_7",
    ]

    REQUIRED_DOCS_V1_81_7 = [
        "microstructure_data_contract_approval_intake_corrective_v1_81_7.md",
        "code_review_v1_81_7.md",
    ]

    def audit_packaging(self, reports_dir: Path, report_index_path: Path, version_suffix: str = "v1_81_6") -> Dict[str, Any]:
        if version_suffix == "v1_81_7":
            return self._audit_packaging_v1_81_7(reports_dir, report_index_path)
        return self._audit_packaging_v1_81_6(reports_dir, report_index_path, version_suffix)

    def _audit_packaging_v1_81_6(self, reports_dir: Path, report_index_path: Path, version_suffix: str) -> Dict[str, Any]:
        results = {
            "packaging_audit_enabled": True,
            "version_suffix": version_suffix,
            "required_reports_checked": True,
            "missing_reports": [],
            "required_reports_present": False,
            "report_index_exists": report_index_path.exists(),
            "report_index_links_checked": False,
            "dead_links": [],
            "report_index_references_version": False,
            "packaging_audit_passed": False
        }

        present_count = 0
        for r_name in self.REQUIRED_REPORTS_V1_81_6:
            json_file = reports_dir / f"{r_name}.json"
            if json_file.exists():
                present_count += 1
            else:
                results["missing_reports"].append(f"{r_name}.json")
        results["required_reports_present"] = (present_count == len(self.REQUIRED_REPORTS_V1_81_6))

        if results["report_index_exists"]:
            with open(report_index_path) as f:
                content = f.read()
            results["report_index_references_version"] = version_suffix in content
            links = re.findall(r"\[.*?\]\((.*?)\)", content)
            dead_links = []
            for link in links:
                if link.startswith("http"):
                    continue
                target = report_index_path.parent / link
                if not target.exists():
                    dead_links.append(link)
            results["dead_links"] = dead_links
            results["report_index_links_checked"] = True

        results["packaging_audit_passed"] = (
            results["required_reports_present"] and
            results["report_index_references_version"] and
            len(results["dead_links"]) == 0
        )
        return results

    def _audit_packaging_v1_81_7(self, reports_dir: Path, report_index_path: Path) -> Dict[str, Any]:
        research_dir = reports_dir / "research"
        docs_dir = reports_dir.parent / "docs"
        version_suffix = "v1_81_7"

        missing: List[str] = []

        # Rapports research/
        for stem in self.REQUIRED_RESEARCH_REPORTS_V1_81_7:
            if not (research_dir / f"{stem}.json").exists():
                missing.append(f"reports/research/{stem}.json")

        # Rapports root
        for stem in self.REQUIRED_ROOT_REPORTS_V1_81_7:
            if not (reports_dir / f"{stem}.json").exists():
                missing.append(f"reports/{stem}.json")

        # Docs
        docs_missing: List[str] = []
        for dname in self.REQUIRED_DOCS_V1_81_7:
            if not (docs_dir / dname).exists():
                docs_missing.append(f"docs/{dname}")

        required_reports_present = len(missing) == 0
        docs_present = len(docs_missing) == 0

        # REPORT_INDEX
        report_index_exists = report_index_path.exists()
        dead_links: List[str] = []
        references_version = False
        references_canonical = False

        if report_index_exists:
            content = report_index_path.read_text()
            references_version = version_suffix in content

            # Check canonical references (research/ paths)
            references_canonical = "research/microstructure_data_contract_approval_intake_corrective_summary_v1_81_7" in content

            links = re.findall(r"\[.*?\]\((.*?)\)", content)
            for link in links:
                if link.startswith("http"):
                    continue
                target = report_index_path.parent / link
                if not target.exists():
                    dead_links.append(link)

        passed = (
            required_reports_present
            and docs_present
            and report_index_exists
            and references_version
            and len(dead_links) == 0
        )

        return {
            "packaging_audit_enabled": True,
            "version_suffix": version_suffix,
            "required_reports_checked": True,
            "missing_reports": missing,
            "required_reports_present": required_reports_present,
            "required_docs_present": docs_present,
            "missing_docs": docs_missing,
            "report_index_exists": report_index_exists,
            "report_index_links_checked": True,
            "dead_links": dead_links,
            "report_index_references_version": references_version,
            "report_index_references_canonical_research_reports": references_canonical,
            "packaging_audit_passed": passed,
        }
