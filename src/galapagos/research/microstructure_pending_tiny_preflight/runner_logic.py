from typing import Any, Dict

class TinyPreflightCommandBuilder:
    """
    Prépare la commande future de preflight.
    """
    def build(self) -> Dict[str, Any]:
        return {
            "tiny_network_preflight_command_prepared": True,
            "tiny_network_preflight_command_executed": False,
            "command_parameters": {
                "max_request_count": 1,
                "max_records_preview": 10,
                "output_scope": "reports_only",
                "data_directory_writes_allowed": False,
                "trading_allowed": False,
                "strategy_link_allowed": False,
                "symbol": "BTCUSDT",
                "timeframe": "1m"
            }
        }

class BlockedRunner:
    """
    Runner qui refuse l'exécution sans approbation validée.
    """
    def run_dry(self, approval_validated: bool) -> Dict[str, Any]:
        # En V1.69, on ne fournit jamais approval_validated=True
        execution_blocked = not approval_validated
        return {
            "tiny_network_preflight_runner_blocked_without_approval": execution_blocked,
            "blocked_runner_test_passed": execution_blocked,
            "tiny_network_collection_executed": False,
            "requests_executed_count": 0
        }
