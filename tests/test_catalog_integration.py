"""Integration tests for catalog fetching (calls real Ersilia API).

Run with: pytest tests/test_catalog_integration.py -v
Skip with: pytest -m "not integration"
"""

import pytest

from ersilia_mcp.catalog import fetch_catalog, format_catalog


@pytest.mark.integration
def test_fetch_catalog_real_api():
    """Test fetching the real catalog from Ersilia hub."""
    output = fetch_catalog()

    # Should succeed (non-empty output with no error message)
    assert output, "Catalog output is empty"
    assert "Failed to fetch catalog" not in output, f"Error in output: {output}"

    # Should have the expected format: identifier  slug — title
    lines = output.strip().split("\n")
    assert len(lines) > 0, "No catalog lines returned"

    # Spot-check: maip-malaria should be there
    malaria_lines = [l for l in lines if "maip-malaria" in l]
    assert len(malaria_lines) > 0, "Expected malaria models not found"

    # Check format: should have identifier  slug — title
    for line in lines[:3]:  # Check first 3 lines
        parts = line.split("  ")
        assert len(parts) >= 2, f"Line doesn't have expected format: {line}"


@pytest.mark.integration
def test_format_catalog_with_real_data():
    """Test format_catalog with realistic Ersilia data structure."""
    # Simulate real Ersilia DataFrame output
    real_like_data = [
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

    output = format_catalog(real_like_data)

    # Verify format
    lines = output.split("\n")
    assert len(lines) == 2
    assert all("  " in line for line in lines), "All lines should have '  ' separator"
    assert all(" — " in line for line in lines), "All lines should have title separator"
