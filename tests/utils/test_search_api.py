"""Tests for catalog fetching and formatting."""

from unittest.mock import MagicMock, patch

import pandas as pd

from ersilia_mcp.utils.search_api import (
    format_search_results,
    search_catalog,
)


def test_format_search_results():
    """Test formatting search API results."""
    results = [
        {
            "Identifier": "eos2gth",
            "Slug": "maip-malaria-surrogate",
            "Title": "MAIP distillation: antimalarial potential prediction",
            "score": 12.0,
            "matched_keywords": 'Title: "malaria"(x1)',
        },
        {
            "Identifier": "eos4rta",
            "Slug": "malaria-mmv",
            "Title": "Antimalarial activity (MMV Data)",
            "score": 12.0,
            "matched_keywords": 'Title: "malaria"(x1)',
        },
    ]
    lines = format_search_results(results)
    assert len(lines) == 2
    assert (
        'eos2gth  maip-malaria-surrogate — MAIP distillation: antimalarial potential prediction (score: 12.0, matched: Title: "malaria"(x1))'
        in lines[0]
    )


def test_format_search_results_empty():
    """Test formatting empty search results."""
    lines = format_search_results([])
    assert lines == []


def test_format_search_results_skips_invalid():
    """Test that search results missing required fields are skipped."""
    results = [
        {"Identifier": "eos2gth"},  # missing Slug
        {"Slug": "malaria-mmv"},  # missing Identifier
        {
            "Identifier": "eos4rta",
            "Slug": "malaria-mmv",
            "Title": "Valid result",
            "score": 10.0,
        },
    ]
    lines = format_search_results(results)
    assert len(lines) == 1
    assert "eos4rta" in lines[0]


@patch("ersilia_mcp.utils.search_api.requests.get")
def test_search_catalog_success(mock_get):
    """Test searching catalog when API succeeds."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "count": 2,
        "results": [
            {
                "Identifier": "eos2gth",
                "Slug": "maip-malaria-surrogate",
                "Title": "MAIP distillation test",
                "score": 12.0,
                "matched_keywords": 'Title: "malaria"',
            },
            {
                "Identifier": "eos4rta",
                "Slug": "malaria-mmv",
                "Title": "Antimalarial activity test",
                "score": 11.5,
                "matched_keywords": 'Title: "malaria"',
            },
        ],
    }
    mock_get.return_value = mock_response

    output = search_catalog("malaria")

    assert "eos2gth" in output
    assert "eos4rta" in output
    assert "score:" in output
    assert "matched:" in output
    mock_get.assert_called_once()


@patch("ersilia_mcp.utils.search_api.requests.get")
def test_search_catalog_no_results(mock_get):
    """Test search when no results are found."""
    mock_response = MagicMock()
    mock_response.json.return_value = {"count": 0, "results": []}
    mock_get.return_value = mock_response

    output = search_catalog("nonexistent")

    assert "No results found" in output


@patch("ersilia_mcp.utils.search_api.requests.get")
def test_search_catalog_request_failure(mock_get):
    """Test search_catalog when the API request fails."""
    mock_get.side_effect = Exception("Network error")
    output = search_catalog("malaria")
    assert "Search API request failed" in output or "Failed to search catalog" in output
