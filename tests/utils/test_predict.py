"""Tests for input parsing and prediction helpers."""

import os
import tempfile
from unittest.mock import MagicMock, patch

import pandas as pd

from ersilia_mcp.utils.predict import parse_input, predict_helper


def test_parse_input_from_string_commas_and_newlines():
    """Test that a delimited string is split on commas and newlines."""
    result = parse_input("CCO,CCC\nCCCC")
    assert result == ["CCO", "CCC", "CCCC"]


def test_parse_input_strips_whitespace_and_drops_empties():
    """Test that whitespace is stripped and empty entries removed."""
    result = parse_input(" CCO , , \n  CCC \n")
    assert result == ["CCO", "CCC"]


def test_parse_input_from_file(tmp_path):
    """Test that inputs are read line-by-line from an existing file."""
    input_file = tmp_path / "inputs.txt"
    input_file.write_text("CCO\nCCC\n\nCCCC\n")
    result = parse_input(str(input_file))
    assert result == ["CCO", "CCC", "CCCC"]


@patch("ersilia_mcp.utils.predict.Model")
def test_predict_helper_success(mock_model_class, tmp_path):
    """Test predict_helper runs the model and writes results to CSV."""
    mock_instance = MagicMock()
    mock_instance.run.return_value = pd.DataFrame(
        {"input": ["CCO", "CCC"], "value": [1.0, 2.0]}
    )
    mock_model_class.return_value = mock_instance

    output_path = tmp_path / "out.csv"
    result = predict_helper("eos3b5e", "CCO,CCC", str(output_path))

    assert result == {
        "status": "ok",
        "output_path": str(output_path),
        "num_predictions": 2,
        "columns": ["input", "value"],
    }
    mock_instance.run.assert_called_once_with(["CCO", "CCC"])
    assert output_path.exists()


@patch("ersilia_mcp.utils.predict.Model")
def test_predict_helper_default_output_path(mock_model_class):
    """Test predict_helper creates a temp CSV when no output path is given."""
    mock_instance = MagicMock()
    mock_instance.run.return_value = pd.DataFrame({"input": ["CCO"], "value": [1.0]})
    mock_model_class.return_value = mock_instance

    result = predict_helper("eos3b5e", "CCO")

    try:
        assert result["num_predictions"] == 1
        assert result["output_path"].endswith(".csv")
    finally:
        os.remove(result["output_path"])


@patch("ersilia_mcp.utils.predict.Model")
def test_predict_helper_no_valid_inputs(mock_model_class):
    """Test predict_helper returns an error when there are no inputs."""
    result = predict_helper("eos3b5e", "  ,  \n ")

    assert result == {"status": "error", "error": "No valid inputs provided"}
    mock_model_class.assert_not_called()


@patch("ersilia_mcp.utils.predict.Model")
def test_predict_helper_run_fails(mock_model_class):
    """Test predict_helper returns the error when the model run fails."""
    mock_instance = MagicMock()
    mock_instance.run.side_effect = Exception("Model crashed")
    mock_model_class.return_value = mock_instance

    result = predict_helper("eos3b5e", "CCO")

    assert result == {"status": "error", "error": "Model crashed"}


# --- chunked prediction -----------------------------------------------------


def _chunk_model(fail_on_call=None, columns_on_call=None):
    """A mocked Model whose run() echoes its inputs back with a value column."""
    calls = []

    def run(chunk):
        calls.append(list(chunk))
        if fail_on_call == len(calls):
            raise RuntimeError("Model crashed")
        name = "other" if columns_on_call == len(calls) else "value"
        return pd.DataFrame(
            {"input": chunk, name: [float(i) for i in range(len(chunk))]}
        )

    model = MagicMock()
    model.run.side_effect = run
    return model, calls


@patch("ersilia_mcp.utils.predict.Model")
def test_large_input_runs_in_chunks_and_reports_progress(mock_model_class, tmp_path):
    """Test 2500 inputs run as 1000 + 1000 + 500, with progress after each chunk."""
    model, calls = _chunk_model()
    mock_model_class.return_value = model
    inputs = [f"C{i}" for i in range(2500)]
    progress = []

    output_path = tmp_path / "out.csv"
    result = predict_helper(
        "eos3b5e",
        ",".join(inputs),
        str(output_path),
        on_progress=lambda done, total, message: progress.append(
            (done, total, message)
        ),
    )

    assert [len(c) for c in calls] == [1000, 1000, 500]
    assert [x for c in calls for x in c] == inputs
    assert progress == [
        (0, 2500, "0/2500 inputs"),
        (1000, 2500, "1000/2500 inputs"),
        (2000, 2500, "2000/2500 inputs"),
        (2500, 2500, "2500/2500 inputs"),
    ]
    assert result == {
        "status": "ok",
        "output_path": str(output_path),
        "num_predictions": 2500,
        "columns": ["input", "value"],
    }
    # One header, every row, in order, and no leftover partial file.
    written = pd.read_csv(output_path)
    assert list(written["input"]) == inputs
    assert output_path.read_text().count("input,value") == 1
    assert not (tmp_path / "out.csv.partial").exists()


@patch("ersilia_mcp.utils.predict.Model")
def test_input_at_the_chunk_size_stays_a_single_call(mock_model_class):
    """Test exactly CHUNK_SIZE inputs behaves as before: one run, no progress calls."""
    model, calls = _chunk_model()
    mock_model_class.return_value = model
    progress = []

    result = predict_helper(
        "eos3b5e",
        ",".join(f"C{i}" for i in range(1000)),
        on_progress=lambda *a: progress.append(a),
    )

    try:
        assert len(calls) == 1 and len(calls[0]) == 1000
        assert progress == []
        assert result["num_predictions"] == 1000
    finally:
        os.remove(result["output_path"])


@patch("ersilia_mcp.utils.predict.Model")
def test_chunked_run_without_output_path_uses_a_temp_file(mock_model_class):
    """Test a large run with no output path still returns a real CSV path."""
    model, _ = _chunk_model()
    mock_model_class.return_value = model

    result = predict_helper("eos3b5e", ",".join(f"C{i}" for i in range(1500)))

    try:
        assert result["status"] == "ok"
        assert result["output_path"].endswith(".csv")
        assert len(pd.read_csv(result["output_path"])) == 1500
    finally:
        os.remove(result["output_path"])


@patch("ersilia_mcp.utils.predict.Model")
def test_chunk_failure_leaves_nothing_half_written(mock_model_class, tmp_path):
    """Test a failure mid-run returns the error and keeps an existing results file."""
    model, _ = _chunk_model(fail_on_call=2)
    mock_model_class.return_value = model
    output_path = tmp_path / "out.csv"
    output_path.write_text("previous results\n")

    result = predict_helper(
        "eos3b5e", ",".join(f"C{i}" for i in range(2500)), str(output_path)
    )

    assert result == {"status": "error", "error": "Model crashed"}
    assert output_path.read_text() == "previous results\n"
    assert not (tmp_path / "out.csv.partial").exists()


@patch("ersilia_mcp.utils.predict.Model")
def test_chunk_failure_removes_the_temp_output(mock_model_class, tmp_path, monkeypatch):
    """Test the temporary results file is cleaned up when a chunk fails."""
    monkeypatch.setattr(tempfile, "tempdir", str(tmp_path))
    model, _ = _chunk_model(fail_on_call=2)
    mock_model_class.return_value = model

    result = predict_helper("eos3b5e", ",".join(f"C{i}" for i in range(2500)))

    assert result["status"] == "error"
    assert list(tmp_path.iterdir()) == []


@patch("ersilia_mcp.utils.predict.Model")
def test_changed_columns_between_chunks_is_an_error(mock_model_class, tmp_path):
    """Test chunks that disagree on columns fail instead of writing a corrupt CSV."""
    model, _ = _chunk_model(columns_on_call=2)
    mock_model_class.return_value = model
    output_path = tmp_path / "out.csv"

    result = predict_helper(
        "eos3b5e", ",".join(f"C{i}" for i in range(2500)), str(output_path)
    )

    assert result["status"] == "error"
    assert "different columns" in result["error"]
    assert list(tmp_path.iterdir()) == []
