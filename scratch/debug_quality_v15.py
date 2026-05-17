import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from galapagos.research.microstructure_data_contract_approval_intake.test_quality_audit import TestQualityAudit
from galapagos.research.microstructure_data_contract_approval_intake.anti_tautology_audit import AntiTautologyAudit

test_file = PROJECT_ROOT / "tests/research/test_microstructure_data_contract_approval_intake_v1_81_15.py"

print(f"Auditing {test_file.name}...")
qa = TestQualityAudit()
res_qa = qa.scan_test_file(test_file)
print("QA results:", res_qa)

ata = AntiTautologyAudit()
res_ata = ata.scan_file(test_file)
print("ATA results:", res_ata)
