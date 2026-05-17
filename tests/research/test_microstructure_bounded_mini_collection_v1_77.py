import pytest
from galapagos.research.microstructure_bounded_mini_collection.bounded_request_guard import BoundedRequestGuard
from galapagos.research.microstructure_bounded_mini_collection.input_guard import InputGuard
from galapagos.research.microstructure_bounded_mini_collection.response_preview_builder import ResponsePreviewBuilder

def test_bounded_request_guard_limit():
    guard = BoundedRequestGuard(max_requests=10)
    for _ in range(10):
        assert guard.can_request()
        guard.increment()
    assert not guard.can_request()
    assert guard.get_status()["requests_executed_count"] == 10

def test_input_guard_valid_state():
    guard = InputGuard()
    valid_summary = {
        "human_approval_granted": True,
        "approval_phrase_validated": True,
        "v1_77_bounded_mini_collection_authorized": True,
        "max_request_count": 10,
        "no_data_directory_writes": True,
        "dataset_created": False,
        "no_real_trading": True
    }
    res = guard.validate_v1_76_1_state(valid_summary)
    assert res["v1_76_1_state_validated"] is True
    assert len(res["issues"]) == 0

def test_input_guard_invalid_state():
    guard = InputGuard()
    invalid_summary = {
        "human_approval_granted": False,
        "v1_77_bounded_mini_collection_authorized": False
    }
    res = guard.validate_v1_76_1_state(invalid_summary)
    assert res["v1_76_1_state_validated"] is False
    assert len(res["issues"]) > 0

def test_response_preview_builder_limits():
    builder = ResponsePreviewBuilder(max_total_records=100, max_per_request=10)
    # Mock responses with 20 records each
    responses = [
        {"success": True, "json_body": [i for i in range(20)]} for _ in range(10)
    ]
    res = builder.build_preview(responses)
    assert res["records_preview_count_total"] == 100 # Capped at 100
    assert len(res["previews"]) == 10
    for p in res["previews"]:
        assert p["record_count"] == 10 # Capped at 10 per request
