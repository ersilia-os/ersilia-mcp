"""Integration tests for fetch operations (calls real Ersilia APIs).

Run with: pytest tests/integration/test_fetch.py -v
Skip with: pytest -m "not integration"
"""

import pytest

from ersilia_mcp.utils.model_operations import check_model_fetched_helper


@pytest.mark.integration
def test_check_model_fetched_real_api():
    """Test check_model_fetched against real Model API."""
    result = check_model_fetched_helper("eos8v1a")

    # Should return a boolean (True if locally present, False otherwise)
    assert isinstance(result, bool)
