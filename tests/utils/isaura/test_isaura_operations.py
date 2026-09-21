"""Tests for the Isaura cache operations (helpers, read, and inspect)."""

import os
from unittest.mock import patch

import pandas as pd
import pytest

from ersilia_mcp.utils.isaura.isaura_operations import (
    _csv_inputs,
    _inspect_cached,
    _resolve_inputs,
    _write_input_csv,
    inspect,
    read,
)

_OPS = "ersilia_mcp.utils.isaura.isaura_operations"


# --- _write_input_csv -------------------------------------------------------


def test_write_input_csv_roundtrips_inputs():
    """Test _write_input_csv writes an 'input' header plus one row per value."""
    path = _write_input_csv(["CCO", "CCC"])
    try:
        assert _csv_inputs(path) == ["CCO", "CCC"]
    finally:
        os.remove(path)


# --- _csv_inputs ------------------------------------------------------------


def test_csv_inputs_reads_input_column(tmp_path):
    """Test _csv_inputs reads the 'input' column, stripping and dropping empties."""
    csv_file = tmp_path / "in.csv"
    csv_file.write_text("input\n CCO \n\nCCC\n")
    assert _csv_inputs(str(csv_file)) == ["CCO", "CCC"]


def test_csv_inputs_falls_back_to_smiles_column(tmp_path):
    """Test _csv_inputs uses the 'smiles' column when 'input' is absent."""
    csv_file = tmp_path / "in.csv"
    csv_file.write_text("smiles\nCCO\nCCC\n")
    assert _csv_inputs(str(csv_file)) == ["CCO", "CCC"]


def test_csv_inputs_raises_without_recognized_column(tmp_path):
    """Test _csv_inputs raises when neither 'input' nor 'smiles' is present."""
    csv_file = tmp_path / "in.csv"
    csv_file.write_text("mol\nCCO\n")
    with pytest.raises(ValueError, match="input.*smiles"):
        _csv_inputs(str(csv_file))


# --- _resolve_inputs --------------------------------------------------------


def test_resolve_inputs_csv_file_reuses_file_without_tempfile(tmp_path):
    """Test a CSV path is passed through and no temp CSV is written for it."""
    csv_file = tmp_path / "in.csv"
    csv_file.write_text("input\nCCO\nCCC\n")
    with patch(f"{_OPS}._write_input_csv") as mock_write:
        requested, source_csv, temp_input_csv = _resolve_inputs(str(csv_file))
    assert requested == ["CCO", "CCC"]
    assert source_csv == str(csv_file)
    assert temp_input_csv is None
    mock_write.assert_not_called()


def test_resolve_inputs_string_writes_tempfile():
    """Test a delimited string is parsed and materialised to a temp CSV."""
    requested, source_csv, temp_input_csv = _resolve_inputs(" CCO , CCC ")
    try:
        assert requested == ["CCO", "CCC"]
        assert source_csv == temp_input_csv
        assert os.path.isfile(temp_input_csv)
    finally:
        os.remove(temp_input_csv)


def test_resolve_inputs_empty_string_yields_nothing():
    """Test an empty/blank string resolves to no inputs and no CSV."""
    assert _resolve_inputs("  ,  ") == ([], None, None)


# --- _inspect_cached --------------------------------------------------------


@patch(f"{_OPS}.IsauraInspect")
def test_inspect_cached_returns_available_column(mock_inspect_class):
    """Test _inspect_cached returns the cached inputs from the availability frame."""
    mock_inspect_class.return_value.inspect_inputs.return_value = pd.DataFrame(
        {"input": ["CCO", "CCC"]}
    )
    result = _inspect_cached("eos3b5e", "v1", "isaura-public", "in.csv")
    assert result == ["CCO", "CCC"]


@patch(f"{_OPS}.IsauraInspect")
def test_inspect_cached_returns_empty_when_no_key_column(mock_inspect_class):
    """Test _inspect_cached returns [] when the frame has no input/smiles column."""
    mock_inspect_class.return_value.inspect_inputs.return_value = pd.DataFrame(
        {"other": [1, 2]}
    )
    assert _inspect_cached("eos3b5e", "v1", "isaura-public", "in.csv") == []


# --- inspect ----------------------------------------------------------------


@patch(f"{_OPS}._inspect_cached")
def test_inspect_returns_counts_only_by_default(mock_cached):
    """Test inspect returns only counts (no input lists) when not verbose."""
    mock_cached.return_value = ["CCO", "CCC"]
    result = inspect("eos3b5e", "CCO,CCC,CCCC")
    assert result == {
        "status": "ok",
        "num_requested": 3,
        "num_cached": 2,
        "num_missing": 1,
    }


@patch(f"{_OPS}._inspect_cached")
def test_inspect_verbose_includes_cached_and_missing(mock_cached):
    """Test inspect includes the full cached/missing lists when verbose."""
    mock_cached.return_value = ["CCO", "CCC"]
    result = inspect("eos3b5e", "CCO,CCC,CCCC", verbose=True)
    assert result == {
        "status": "ok",
        "num_requested": 3,
        "num_cached": 2,
        "num_missing": 1,
        "cached": ["CCO", "CCC"],
        "missing": ["CCCC"],
    }


def test_inspect_no_valid_inputs():
    """Test inspect returns an error status when there are no inputs."""
    result = inspect("eos3b5e", "  ,  ")
    assert result["status"] == "error"


@patch(f"{_OPS}._inspect_cached", side_effect=Exception("store unreachable"))
def test_inspect_error(mock_cached):
    """Test inspect returns an error status when inspection fails."""
    result = inspect("eos3b5e", "CCO")
    assert result["status"] == "error"
    assert "store unreachable" in result["error"]


# --- read -------------------------------------------------------------------


@patch(f"{_OPS}.IsauraReader")
@patch(f"{_OPS}._inspect_cached")
def test_read_all_cached_writes_results(mock_cached, mock_reader_class, tmp_path):
    """Test read retrieves and writes results when every input is cached."""
    mock_cached.return_value = ["CCO", "CCC"]
    df = pd.DataFrame({"input": ["CCO", "CCC"], "value": [1.0, 2.0]})
    mock_reader_class.return_value.__enter__.return_value.read.return_value = df

    output_path = tmp_path / "out.csv"
    result = read("eos3b5e", "CCO,CCC", output_path=str(output_path))

    assert result["status"] == "ok"
    assert result["num_cached"] == 2
    assert result["num_missing"] == 0
    assert result["output_path"] == str(output_path)
    assert result["columns"] == ["input", "value"]
    assert output_path.exists()


@patch(f"{_OPS}.IsauraReader")
@patch(f"{_OPS}._inspect_cached")
def test_read_partial_cached_reports_missing(mock_cached, mock_reader_class, tmp_path):
    """Test read retrieves only the cached subset and reports missing inputs."""
    mock_cached.return_value = ["CCO"]
    df = pd.DataFrame({"input": ["CCO"], "value": [1.0]})
    mock_reader_class.return_value.__enter__.return_value.read.return_value = df

    output_path = tmp_path / "out.csv"
    result = read("eos3b5e", "CCO,CCC", output_path=str(output_path))

    assert result["num_cached"] == 1
    assert result["num_missing"] == 1
    assert result["missing"] == ["CCC"]
    assert output_path.exists()


@patch(f"{_OPS}.IsauraReader")
@patch(f"{_OPS}._inspect_cached")
def test_read_nothing_cached_skips_reader(mock_cached, mock_reader_class):
    """Test read returns early without reading when nothing is cached."""
    mock_cached.return_value = []
    result = read("eos3b5e", "CCO,CCC")
    assert result["num_cached"] == 0
    assert result["output_path"] is None
    assert result["columns"] == []
    mock_reader_class.assert_not_called()


def test_read_no_valid_inputs():
    """Test read returns an error status when there are no inputs."""
    result = read("eos3b5e", "  ,  ")
    assert result["status"] == "error"


@patch(f"{_OPS}._inspect_cached", side_effect=Exception("store unreachable"))
def test_read_error(mock_cached):
    """Test read returns an error status when the store is unreachable."""
    result = read("eos3b5e", "CCO")
    assert result["status"] == "error"
    assert "store unreachable" in result["error"]
