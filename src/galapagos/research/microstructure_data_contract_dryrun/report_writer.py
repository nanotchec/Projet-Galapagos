import json
from pathlib import Path
from galapagos.research.report_models import write_research_report

class ReportWriter:
    """Générateur de rapports pour le dry-run V1.82."""
    
    def __init__(self, version: str = "v1_82"):
        self.version = version

    def write_dryrun_reports(self, summary_payload: dict, contract_payload: dict, safety_payload: dict):
        # 1. Summary
        write_research_report(
            name=f"microstructure_data_contract_dryrun_summary_{self.version}",
            payload=summary_payload,
            title=f"Microstructure Data Contract Dry-Run Summary {self.version.upper()}",
            lines=["Simulation théorique de matérialisation de contrat de données."],
            output_dir="reports/research"
        )
        
        # 2. Contract
        write_research_report(
            name=f"microstructure_data_contract_dryrun_contract_{self.version}",
            payload=contract_payload,
            title=f"Microstructure Data Contract Definition {self.version.upper()}",
            lines=["Définition théorique des schémas et des partitions."],
            output_dir="reports/research"
        )
        
        # 3. Safety
        write_research_report(
            name=f"microstructure_data_contract_dryrun_safety_check_{self.version}",
            payload=safety_payload,
            title=f"Dry-Run Safety Audit {self.version.upper()}",
            lines=["Audit de non-écriture et respect du scope reports-only."],
            output_dir="reports/research"
        )
