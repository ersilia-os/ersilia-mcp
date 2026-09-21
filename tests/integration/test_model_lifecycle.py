"""Integration test for complete model lifecycle (calls real Ersilia APIs).

Tests the full workflow: fetch → check → serve → generate_inputs → predict → close -> delete

The cache/inspect/read steps require a running Isaura store (``isaura engine
--start``); see DEVELOPMENT.md.

Run with: pytest tests/integration/test_model_lifecycle.py -v
Skip with: pytest -m "not integration"
"""

import subprocess
import sys
from pathlib import Path

import pytest

from ersilia_mcp.utils.generate_inputs import generate_inputs_helper
from ersilia_mcp.utils.isaura import isaura_operations
from ersilia_mcp.utils.model_operations import (
    check_model_fetched_helper,
    close_model_helper,
    delete_model_helper,
    fetch_model_helper,
    serve_model_helper,
)
from ersilia_mcp.utils.predict import predict_helper


def _isaura_cli() -> list:
    """Build the command prefix that runs the ``isaura`` console script.

    The CLI is installed alongside ``python`` in the active env, which isn't
    guaranteed to be on ``PATH`` when pytest is launched directly. The script
    is run *through* that interpreter rather than executed directly: a console
    script whose shebang was never rewritten from ``#!python`` cannot be
    exec'd, and ``subprocess`` reports the script itself as missing even
    though it exists.
    """
    candidate = Path(sys.executable).parent / "isaura"
    return [sys.executable, str(candidate)] if candidate.exists() else ["isaura"]


@pytest.mark.integration
def test_model_complete_lifecycle(tmp_path):
    """Test the full lifecycle, incl. caching predictions in Isaura and reading them back."""
    model_id = "eos3b5e"
    test_inputs = ["CCO", "CCC"]

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

    # Step 4: Generate example inputs from the served model
    n_samples = 2
    samples = generate_inputs_helper(model_id, n_samples=n_samples, mode="random")
    assert isinstance(samples, list), (
        f"Generate should return list, got {type(samples)}"
    )
    assert len(samples) == n_samples, (
        f"Expected {n_samples} samples for {model_id}, got {samples}"
    )

    # Step 5: Run a prediction against the served model using the generated inputs
    output_path = tmp_path / "predictions.csv"
    predict_result = predict_helper(model_id, "\n".join(samples), str(output_path))
    assert isinstance(predict_result, dict), (
        f"Predict should return dict, got {type(predict_result)}"
    )
    assert predict_result.get("num_predictions") == n_samples, (
        f"Expected {n_samples} predictions for {model_id}, got {predict_result}"
    )
    assert predict_result.get("output_path") == str(output_path), (
        f"Predict wrote to unexpected path: {predict_result}"
    )

    # The written CSV should have a header plus one row per input
    assert output_path.exists(), "Predict did not write the output file"
    rows = output_path.read_text().splitlines()
    assert len(rows) == len(test_inputs) + 1, (
        f"Expected header + {len(test_inputs)} rows, got {len(rows)}: {rows}"
    )

    # Step 5: Cache the predictions in the Isaura store via the CLI
    # TODO: Update this to use a isaura_write tool once we add that tool
    write = subprocess.run(
        [
            *_isaura_cli(),
            "write",
            "-i",
            str(output_path),
            "-pn",
            "isaura-public",
            "-m",
            model_id,
            "-v",
            "v1",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert write.returncode == 0, f"isaura write failed: {write.stderr}"

    # Step 6: Inspect the store; the predicted inputs should now be cached
    inspect_result = isaura_operations.inspect(model_id, ",".join(samples))
    assert inspect_result["status"] == "ok", f"Inspect failed: {inspect_result}"
    assert inspect_result["num_cached"] == n_samples, (
        f"Expected {n_samples} cached inputs, got {inspect_result}"
    )
    assert inspect_result["num_missing"] == 0, (
        f"Expected no missing inputs, got {inspect_result}"
    )

    # Step 7: Read the cached results back out of the store
    cache_output = tmp_path / "cached.csv"
    read_result = isaura_operations.read(
        model_id, ",".join(test_inputs), output_path=str(cache_output)
    )
    assert read_result["status"] == "ok", f"Read failed: {read_result}"
    assert read_result["num_cached"] == len(test_inputs), (
        f"Expected {len(test_inputs)} cached results, got {read_result}"
    )
    assert cache_output.exists(), "Read did not write the cached results file"
    cache_rows = cache_output.read_text().splitlines()
    assert len(cache_rows) == n_samples + 1, (
        f"Expected header + {n_samples} rows, got {len(cache_rows)}: {cache_rows}"
    )

    # Step 8: Close the model service
    close_result = close_model_helper(model_id)
    assert close_result is True

    # Step 9: Delete the model
    delete_result = delete_model_helper(model_id)
    assert delete_result is True
    check_result = check_model_fetched_helper(model_id)
    assert check_result is False
