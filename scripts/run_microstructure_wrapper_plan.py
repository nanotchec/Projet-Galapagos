import argparse
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from galapagos.research.microstructure_wrapper_plan.data_loader import load_previous_state
from galapagos.research.microstructure_wrapper_plan.input_guard import check_input_preconditions
from galapagos.research.microstructure_wrapper_plan.wrapper_scope_definition import define_wrapper_scope
from galapagos.research.microstructure_wrapper_plan.collector_interface_plan import plan_collector_interface
from galapagos.research.microstructure_wrapper_plan.network_interception_policy import define_network_interception_policy
from galapagos.research.microstructure_wrapper_plan.write_interception_policy import define_write_interception_policy
from galapagos.research.microstructure_wrapper_plan.request_mocking_policy import define_request_mocking_policy
from galapagos.research.microstructure_wrapper_plan.manifest_preview_policy import define_manifest_preview_policy
from galapagos.research.microstructure_wrapper_plan.wrapper_test_plan import define_wrapper_test_plan
from galapagos.research.microstructure_wrapper_plan.wrapper_decision import evaluate_wrapper_plan
from galapagos.research.microstructure_wrapper_plan.recommendation_engine import generate_recommendation
from galapagos.research.microstructure_wrapper_plan.report_writer import write_reports


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", required=True)
    parser.add_argument("--hardened-preflight-review-summary", required=True)
    parser.add_argument("--hardened-preflight-review-consistency", required=True)
    parser.add_argument("--hardened-preflight-next-phase-policy", required=True)
    parser.add_argument("--hardened-preflight-recommendation", required=True)
    parser.add_argument("--v1-62-1-recommendation", required=True)
    parser.add_argument("--preflight-hardening-summary", required=True)
    parser.add_argument("--preflight-dryrun-summary", required=True)
    parser.add_argument("--preflight-plan-summary", required=True)
    parser.add_argument("--adapter-fixture-summary", required=True)
    parser.add_argument("--adapter-field-mapping", required=True)
    parser.add_argument("--normalized-record-schema", required=True)
    parser.add_argument("--source-adapter-contract", required=True)
    parser.add_argument("--request-builder", required=True)
    parser.add_argument("--canonical-summary", required=True)
    
    args = parser.parse_args()

    # Load states
    previous_state = load_previous_state(
        hardened_preflight_review_summary_path=args.hardened_preflight_review_summary,
        hardened_preflight_review_consistency_path=args.hardened_preflight_review_consistency,
        hardened_preflight_next_phase_policy_path=args.hardened_preflight_next_phase_policy,
        hardened_preflight_recommendation_path=args.hardened_preflight_recommendation,
        v1_62_1_recommendation_path=args.v1_62_1_recommendation,
        preflight_hardening_summary_path=args.preflight_hardening_summary,
        preflight_dryrun_summary_path=args.preflight_dryrun_summary,
        preflight_plan_summary_path=args.preflight_plan_summary,
        adapter_fixture_summary_path=args.adapter_fixture_summary,
        adapter_field_mapping_path=args.adapter_field_mapping,
        normalized_record_schema_path=args.normalized_record_schema,
        source_adapter_contract_path=args.source_adapter_contract,
        request_builder_path=args.request_builder,
        canonical_summary_path=args.canonical_summary,
    )

    results = {}
    
    # Run pipeline
    results["input_guard"] = check_input_preconditions(previous_state)
    results["wrapper_scope"] = define_wrapper_scope(previous_state)
    results["collector_interface"] = plan_collector_interface(previous_state)
    results["network_policy"] = define_network_interception_policy(previous_state)
    results["write_policy"] = define_write_interception_policy(previous_state)
    results["mocking_policy"] = define_request_mocking_policy(previous_state)
    results["manifest_policy"] = define_manifest_preview_policy(previous_state)
    results["test_plan"] = define_wrapper_test_plan(previous_state)
    
    results["wrapper_decision"] = evaluate_wrapper_plan(results)
    results["recommendation"] = generate_recommendation(results["wrapper_decision"])
    
    # Write reports
    write_reports(results, previous_state, args.version)
    print(f"Successfully generated wrapper plan reports for {args.version}")

if __name__ == "__main__":
    main()
