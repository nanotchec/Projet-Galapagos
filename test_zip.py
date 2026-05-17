import re
from pathlib import Path

_regexes = [
    r"src/galapagos/research/microstructure_wrapper_plan/.*",
    r"scripts/run_microstructure_wrapper_plan\.py",
    r"scripts/validate_microstructure_wrapper_plan_reports\.py",
    r"reports/research/microstructure_.*_v1_63\.(json|md)",
    r"reports/research/v1_63_recommendation\.(json|md)",
    r"docs/microstructure_network_disabled_wrapper_plan_v1_63\.md",
    r"reports/release_zip_v1_63\.json",
    r"reports/zip_audit_v1_63\.json",
    r"reports/zip_smoke_test_v1_63\.json",
]

base_dir = Path.cwd()
f = base_dir / "reports" / "research" / "microstructure_wrapper_plan_input_guard_v1_63.json"
rel_path = str(f.relative_to(base_dir))
print(f"File exists: {f.exists()}")

def _is_internal_file(rel_s: str) -> bool:
    if "reports/research/microstructure_" in rel_s:
        return True
    return False

if _is_internal_file(rel_path):
    if any(re.match(p, rel_path) for p in _regexes):
        pass
    else:
        print("skipped by internal_file check")

if any(re.match(p, rel_path) for p in _regexes):
    print("ADDED!")
else:
    print("Not added by regexes")
