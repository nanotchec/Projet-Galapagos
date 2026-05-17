import pytest
import sys
from pathlib import Path

# Setup path to include src and project root for scripts
PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import importlib.util

def _import_script(script_name):
    script_path = PROJECT_ROOT / "scripts" / script_name
    spec = importlib.util.spec_from_file_location(script_name.replace(".py", ""), str(script_path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def test_v1_81_8_smoke_test_bounded_logic():
    smoke = _import_script("smoke_test_clean_zip.py")
    assert smoke.normalize_version("v1.81.8") == "v1_81_8"

def test_v1_81_8_anti_tautology_logic_detection():
    import ast
    from galapagos.research.microstructure_data_contract_approval_intake.anti_tautology_audit import AntiTautologyAudit
    ata = AntiTautologyAudit()
    # Mocking a tautology in code string
    code = "def test_fail(): assert True"
    tree = ast.parse(code)
    func_node = tree.body[0]
    ata._check_test_function(func_node)
    assert "test_fail" in ata.assert_true_tests
    assert "test_fail" in ata.tautological_tests

def test_v1_81_8_anti_tautology_or_true_detection():
    import ast
    from galapagos.research.microstructure_data_contract_approval_intake.anti_tautology_audit import AntiTautologyAudit
    ata = AntiTautologyAudit()
    code = "def test_fail_or(): x = (1 == 1) or True; assert x"
    tree = ast.parse(code)
    func_node = tree.body[0]
    ata._check_test_function(func_node)
    assert "test_fail_or" in ata.or_true_tests

def test_v1_81_8_smoke_alignment_logic():
    from galapagos.research.microstructure_data_contract_approval_intake.smoke_state_alignment import SmokeStateAlignment
    ssa = SmokeStateAlignment()
    # Check that it returns issues if files missing
    res = ssa.check_alignment(Path("missing.json"), Path("summary.json"), Path("metrics.json"), Path("state.json"))
    assert len(res["issues"]) > 0
    assert not res["smoke_test_passed_consistent"]

def test_v1_81_8_validator_version_support():
    # Verify the validator exists
    val_script = PROJECT_ROOT / "scripts/validate_microstructure_data_contract_approval_intake_corrective_v1_81_8_reports.py"
    assert val_script.exists()

def test_v1_81_8_report_writer_canonization():
    from galapagos.research.microstructure_data_contract_approval_intake.report_writer import ReportWriter
    writer = ReportWriter("V1.81.8", "temp_reports")
    # Verify it can write (ReportWriter has v_disp but maybe accessed differently)
    assert hasattr(writer, "v_disp")
    assert writer.v_disp == "V1.81.8"

def test_v1_81_8_project_state_structure():
    import json
    state_file = PROJECT_ROOT / "reports/PROJECT_STATE.json"
    if state_file.exists():
        data = json.loads(state_file.read_text())
        assert "version" in data

def test_v1_81_8_audit_clean_zip_version_inference():
    audit = _import_script("audit_clean_zip.py")
    v = audit._infer_version(Path("projet-galapagos-v1.81.8-clean.zip"))
    assert v == "v1_81_8"

def test_v1_81_8_bootstrap_check():
    run = _import_script("run_microstructure_data_contract_approval_intake_corrective_v1_81_8.py")
    # Just check it's importable and has main
    assert callable(run.main)

def test_v1_81_8_approval_phrase_contract():
    run = _import_script("run_microstructure_data_contract_approval_intake_corrective_v1_81_8.py")
    assert "J'approuve V1.82" in run.APPROVAL_PHRASE_EXPECTED
    assert "sans trading" in run.APPROVAL_PHRASE_EXPECTED

def test_v1_81_8_negative_coverage_logic():
    from galapagos.research.microstructure_data_contract_approval_intake.negative_coverage import NegativeCoverage
    nc = NegativeCoverage()
    res = nc.get_coverage_report(Path(__file__))
    assert "discovered_test_functions_count" in res

def test_v1_81_8_safety_guard_immutability():
    from galapagos.research.microstructure_data_contract_approval_intake.safety_guard import SafetyGuard
    sg = SafetyGuard()
    res = sg.check_safety({"trading_allowed": True})
    assert not res["safety_check_passed"]

def test_v1_81_8_portability_bootstrap_detection():
    validator = _import_script("validate_microstructure_data_contract_approval_intake_corrective_v1_81_8_reports.py")
    script = PROJECT_ROOT / "scripts/smoke_test_clean_zip.py"
    res = validator._script_has_bootstrap(script)
    assert res is True

def test_v1_81_8_metadata_version_parse():
    from galapagos.research.microstructure_data_contract_approval_intake.current_state_alignment import parse_version
    assert parse_version("v1_81_8") == "V1.81.8"

def test_v1_81_8_metadata_suffix_gen():
    from galapagos.research.microstructure_data_contract_approval_intake.current_state_alignment import version_to_suffix
    assert version_to_suffix("V1.81.8") == "v1_81_8"

def test_v1_81_8_packaging_report_index_check():
    from galapagos.research.microstructure_data_contract_approval_intake.release_packaging_audit import ReleasePackagingAudit
    rpa = ReleasePackagingAudit()
    report_index = PROJECT_ROOT / "reports/REPORT_INDEX.md"
    res = rpa.audit_packaging(PROJECT_ROOT / "reports", report_index, "v1_81_8")
    assert res["report_index_exists"]

def test_v1_81_8_smoke_test_command_count():
    smoke = _import_script("smoke_test_clean_zip.py")
    cmds = smoke.get_commands_for_version("v1_81_8")
    assert len(cmds) == 3

def test_v1_81_8_anti_tautology_and_true_detection():
    import ast
    from galapagos.research.microstructure_data_contract_approval_intake.anti_tautology_audit import AntiTautologyAudit
    ata = AntiTautologyAudit()
    code = "def test_fail_and(): x = (1 == 1) and True; assert x"
    tree = ast.parse(code)
    func_node = tree.body[0]
    ata._check_test_function(func_node)
    assert "test_fail_and" in ata.and_true_tests

def test_v1_81_8_anti_tautology_bit_or_true_detection():
    import ast
    from galapagos.research.microstructure_data_contract_approval_intake.anti_tautology_audit import AntiTautologyAudit
    ata = AntiTautologyAudit()
    code = "def test_fail_bit_or(): x = True | False; assert x"
    tree = ast.parse(code)
    func_node = tree.body[0]
    ata._check_test_function(func_node)
    assert "test_fail_bit_or" in ata.or_true_tests

def test_v1_81_8_weak_test_detection_no_assert():
    import ast
    from galapagos.research.microstructure_data_contract_approval_intake.anti_tautology_audit import AntiTautologyAudit
    ata = AntiTautologyAudit()
    code = "def test_weak(): print('hello')"
    tree = ast.parse(code)
    func_node = tree.body[0]
    ata._check_test_function(func_node)
    assert "test_weak" in ata.weak_tests
