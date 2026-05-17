import pytest
from pathlib import Path
from galapagos.research.microstructure_preflight_skeleton.preflight_skeleton_builder import PreflightSkeletonBuilder
from galapagos.research.microstructure_preflight_skeleton.wrapper_fixture_review import WrapperFixtureReview
from galapagos.research.microstructure_preflight_skeleton.aggressive_safety_tests import AggressiveNetworkSafetyTests, AggressiveWriteSafetyTests

def test_skeleton_builder():
    builder = PreflightSkeletonBuilder("V1.65")
    info = builder.get_skeleton_info()
    assert info["version"] == "V1.65"
    assert info["preflight_skeleton_created"] is True
    assert info["network_enabled"] is False
    assert info["write_enabled"] is False

def test_wrapper_review_pass():
    summary = {
        "wrapper_fixture_implementation_passed": True,
        "network_enabled": False,
        "requests_executed_count": 0,
        "network_gate_enabled": True,
        "write_gate_enabled": True
    }
    review = WrapperFixtureReview(summary)
    res = review.run_review()
    assert res["wrapper_fixture_review_passed"] is True

def test_wrapper_review_fail_network():
    summary = {
        "wrapper_fixture_implementation_passed": True,
        "network_enabled": True,
        "requests_executed_count": 0,
        "network_gate_enabled": True,
        "write_gate_enabled": True
    }
    review = WrapperFixtureReview(summary)
    res = review.run_review()
    assert res["wrapper_fixture_review_passed"] is False

def test_aggressive_network_safety():
    tests = AggressiveNetworkSafetyTests()
    res = tests.run_tests()
    assert res["aggressive_network_tests_defined"] is True
    assert res["aggressive_network_tests_passed"] is True

def test_aggressive_write_safety():
    tests = AggressiveWriteSafetyTests()
    res = tests.run_tests()
    assert res["aggressive_write_tests_defined"] is True
    assert res["aggressive_write_tests_passed"] is True
