"""Integration test for complete model lifecycle (calls real Ersilia APIs).

Tests the full workflow: fetch → check → serve → predict → close

Run with: pytest tests/integration/test_model_lifecycle.py -v
Skip with: pytest -m "not integration"
"""

import pytest

from ersilia_mcp.utils.model_operations import (
    check_model_fetched_helper,
    close_model_helper,
    delete_model_helper,
    fetch_model_helper,
    serve_model_helper,
)
from ersilia_mcp.utils.predict import predict_helper


@pytest.mark.integration
def test_model_complete_lifecycle(tmp_path):
    """Test complete model lifecycle: fetch → check → serve → predict → close."""
    model_id = "eos3b5e"

    # Step 1: Fetch the model
    fetch_result = fetch_model_helper(model_id)
    assert isinstance(fetch_result, bool), (
        f"Fetch should return bool, got {type(fetch_result)}"
    )
    assert fetch_result is True, f"Fetch failed for {model_id}"

    # Step 2: Check that model is fetched
    check_result = check_model_fetched_helper(model_id)
    assert isinstance(check_result, bool), (
        f"Check should return bool, got {type(check_result)}"
    )
    assert check_result is True, f"Model {model_id} should be fetched"

    # Step 3: Serve the model
    serve_result = serve_model_helper(model_id)
    assert isinstance(serve_result, dict), (
        f"Serve should return dict, got {type(serve_result)}"
    )
    # TODO: Make this more specific once the API is updated
    assert serve_result is not None, f"Serve returned None for {model_id}"

    # Step 4: Run a prediction against the served model
    output_path = tmp_path / "predictions.csv"
    predict_result = predict_helper(model_id, "CCO\nCCC", str(output_path))
    assert isinstance(predict_result, dict), (
        f"Predict should return dict, got {type(predict_result)}"
    )
    assert predict_result.get("num_predictions") == 2, (
        f"Expected 2 predictions for {model_id}, got {predict_result}"
    )
    assert predict_result.get("output_path") == str(output_path), (
        f"Predict wrote to unexpected path: {predict_result}"
    )

    # The written CSV should have a header plus one row per input
    assert output_path.exists(), "Predict did not write the output file"
    rows = output_path.read_text().splitlines()
    assert len(rows) == 3, f"Expected header + 2 rows, got {len(rows)}: {rows}"

    # Step 5: Close the model service
    close_result = close_model_helper(model_id)
    assert close_result is True

    # Step 6: Delete the model
    delete_result = delete_model_helper(model_id)
    assert delete_result is True
