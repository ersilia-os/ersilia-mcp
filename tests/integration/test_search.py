"""Integration tests for search (calls real Ersilia APIs).

Run with: pytest tests/test_search_integration.py -v
Skip with: pytest -m "not integration"
"""

import pytest

from ersilia_mcp.utils.search_api import search_catalog


@pytest.mark.integration
def test_search_catalog_real_api():
    """Test searching the real Ersilia search API."""
    output = search_catalog("malaria")

    # Should succeed (non-empty output with no error message)
    assert output, "Search output is empty"
    assert "Failed to search catalog" not in output, f"Error in output: {output}"

    # Should have the expected format: identifier  slug — title (score: X)
    lines = output.strip().split("\n")
    assert len(lines) > 0, "No search results returned"

    # Check format: should have identifier  slug — title (score: X)
    for line in lines[:3]:  # Check first 3 lines
        assert "  " in line, f"Line doesn't have identifier-slug separator: {line}"
        assert " — " in line, f"Line doesn't have title separator: {line}"
        assert "(score:" in line, f"Line doesn't have score: {line}"
