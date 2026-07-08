"""Integration test for complete model lifecycle (calls real Ersilia APIs).

Tests the full workflow: fetch → check → serve → close

Run with: pytest tests/integration/test_model_lifecycle.py -v
Skip with: pytest -m "not integration"
"""

import pytest

from ersilia_mcp.utils.model_operations import (
    check_model_fetched_helper,
    close_model_helper,
    fetch_model_helper,
    serve_model_helper,
)


@pytest.mark.integration
def test_model_complete_lifecycle():
    """Test complete model lifecycle: fetch → check → serve → close."""
    model_id = "eos8v1a"

    # Step 1: Fetch the model
    fetch_result = fetch_model_helper(model_id)
    assert isinstance(fetch_result, bool), f"Fetch should return bool, got {type(fetch_result)}"
    assert fetch_result is True, f"Fetch failed for {model_id}"

    # Step 2: Check that model is fetched
    check_result = check_model_fetched_helper(model_id)
    assert isinstance(check_result, bool), f"Check should return bool, got {type(check_result)}"
    assert check_result is True, f"Model {model_id} should be fetched"

    # Step 3: Serve the model
    serve_result = serve_model_helper(model_id)
    assert isinstance(serve_result, dict), f"Serve should return dict, got {type(serve_result)}"
    # TODO: Make this more specific once the API is updated
    assert serve_result is not None, f"Serve returned None for {model_id}"

    # Step 4: Close the model service
    close_result = close_model_helper(model_id)
    # TODO: This should pass once the API is updated
    assert close_result is True
