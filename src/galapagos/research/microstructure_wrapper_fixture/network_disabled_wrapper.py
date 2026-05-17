from typing import Any, Dict, List
from .network_gate import NetworkGate
from .write_gate import WriteGate
from .fixture_request_loader import FixtureRequestLoader
from .fixture_response_adapter import FixtureResponseAdapter
from .manifest_preview_builder import ManifestPreviewBuilder

class NetworkDisabledWrapper:
    """Wrapper around the collector that strictly uses local fixtures."""
    def __init__(self, version: str, config: Dict[str, Any]):
        self.version = version
        self.network_gate = NetworkGate(version)
        self.write_gate = WriteGate(version)
        self.loader = FixtureRequestLoader(version, config.get("fixtures_dir", "tests/fixtures/microstructure"))
        self.adapter = FixtureResponseAdapter(version)
        self.manifest_builder = ManifestPreviewBuilder(version)
        
        self.processed_records: List[Dict[str, Any]] = []
        self.run_executed = False

    def run(self) -> Dict[str, Any]:
        """Execute the wrapper in fixture-only mode."""
        # 1. Load fixtures
        raw_fixtures = self.loader.load_fixtures()
        
        # 2. Process records (simulating collection)
        for raw in raw_fixtures:
            # Check network gate (simulated)
            if not self.network_gate.check_request("local_fixture"):
                continue
                
            # Check write gate (simulated)
            if not self.write_gate.check_write("data/simulated.parquet"):
                pass # Blocked as expected
                
            normalized = self.adapter.normalize(raw)
            self.processed_records.append(normalized)
            
        self.run_executed = True
        
        # 3. Build manifest preview
        preview = self.manifest_builder.build_preview(self.processed_records)
        
        return {
            "version": self.version,
            "wrapper_fixture_run_executed": self.run_executed,
            "records_processed": len(self.processed_records),
            "manifest_preview": preview,
            "wrapper_real_execution": False,
            "status": "MICROSTRUCTURE_NETWORK_DISABLED_WRAPPER_EXECUTED"
        }

    def get_report(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "network_disabled_wrapper_active": True,
            "wrapper_fixture_only": True,
            "wrapper_real_execution": False,
            "status": "MICROSTRUCTURE_NETWORK_DISABLED_WRAPPER_READY"
        }
