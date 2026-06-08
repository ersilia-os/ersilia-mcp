"""Tests for catalog fetching and formatting."""

from unittest.mock import MagicMock, patch

import pandas as pd

from ersilia_mcp.catalog import fetch_catalog, format_catalog


def test_format_catalog():
    """Test formatting catalog JSON into compact text."""
    data = [
        {
            "Index": 1,
            "Identifier": "eos4zfy",
            "Slug": "maip-malaria",
            "Title": "MAIP: antimalarial activity prediction",
            "Task": "Annotation",
            "Output Dimension": 1,
        },
        {
            "Index": 2,
            "Identifier": "eos4an7",
            "Slug": "antimicrobial-activity-pfalciparum",
            "Title": "Antimicrobial activity prediction against Plasmodium falciparum",
            "Task": "Annotation",
            "Output Dimension": 95,
        },
    ]
    output = format_catalog(data)
    assert "eos4zfy  maip-malaria — MAIP: antimalarial activity prediction" in output
    assert (
        "eos4an7  antimicrobial-activity-pfalciparum — "
        "Antimicrobial activity prediction against Plasmodium falciparum"
    ) in output


def test_format_catalog_no_title():
    """Test formatting catalog records without titles."""
    data = [
        {
            "Index": 1,
            "Identifier": "eos4zfy",
            "Slug": "maip-malaria",
        },
    ]
    output = format_catalog(data)
    assert output == "eos4zfy  maip-malaria"


def test_format_catalog_empty():
    """Test formatting empty/invalid data returns empty string."""
    assert format_catalog([]) == ""
    assert format_catalog({}) == ""
    assert format_catalog("invalid") == ""


def test_format_catalog_skips_invalid_records():
    """Test that records missing required fields are skipped."""
    data = [
        {"Identifier": "eos4zfy"},  # missing Slug
        {"Slug": "maip-malaria"},  # missing Identifier
        {
            "Identifier": "eos4an7",
            "Slug": "antimicrobial-activity-pfalciparum",
            "Title": "Test",
        },  # valid
    ]
    output = format_catalog(data)
    assert "eos4an7" in output
    assert "eos4zfy" not in output


@patch("ersilia_mcp.catalog.catalog")
def test_fetch_catalog_success(mock_catalog):
    """Test fetching catalog when ersilia API succeeds."""
    df = pd.DataFrame([
        {
            "Identifier": "eos4zfy",
            "Slug": "maip-malaria",
            "Title": "MAIP test",
        }
    ])
    mock_catalog.return_value = df

    output = fetch_catalog()

    assert "eos4zfy  maip-malaria — MAIP test" in output
    mock_catalog.assert_called_once_with(hub=True, more=True)


@patch("ersilia_mcp.catalog.catalog")
def test_fetch_catalog_api_failure(mock_catalog):
    """Test fetch_catalog when the API call fails."""
    mock_catalog.side_effect = Exception("API error")
    output = fetch_catalog()
    assert "Failed to fetch catalog" in output


@patch("ersilia_mcp.catalog.catalog")
def test_fetch_catalog_returns_none(mock_catalog):
    """Test fetch_catalog when the API returns None."""
    mock_catalog.return_value = None
    output = fetch_catalog()
    assert "Failed to fetch catalog" in output
