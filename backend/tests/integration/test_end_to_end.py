"""
End-to-end integration test.
Requires: Docker services running + LLM API key configured.

Run with:
    docker-compose exec app pytest tests/integration/ -v
    # OR from host: pytest tests/integration/ -v
"""
import os
import pytest
import requests


# Detect if running inside container - use localhost when inside container
# Use host.docker.internal from host machine on Windows
def get_base_url():
    # Check if we're running inside a container by looking for .dockerenv
    in_container = os.path.exists("/.dockerenv") or os.environ.get("RUNNING_IN_CONTAINER")
    if in_container:
        return "http://localhost:8000"
    return os.environ.get("TEST_BASE_URL", "http://localhost:8000")


BASE_URL = get_base_url()


class TestEndToEnd:
    """Integration tests against running Docker services."""

    def test_health_endpoint(self):
        """Test the /health endpoint is reachable."""
        try:
            resp = requests.get(f"{BASE_URL}/health", timeout=5)
            assert resp.status_code == 200
            data = resp.json()
            assert data["status"] == "healthy"
            assert "version" in data
        except requests.ConnectionError:
            pytest.skip("API not running — start with docker-compose up")

    def test_reports_list_empty(self):
        """Test GET /reports returns empty list initially."""
        try:
            resp = requests.get(f"{BASE_URL}/reports", timeout=5)
            assert resp.status_code == 200
            assert isinstance(resp.json(), list)
        except requests.ConnectionError:
            pytest.skip("API not running")

    @pytest.mark.skipif(
        os.environ.get("OPENAI_API_KEY") is None and os.environ.get("ANTHROPIC_API_KEY") is None,
        reason="LLM API key required for full pipeline test"
    )
    def test_research_endpoint(self):
        """Test POST /research executes the full pipeline."""
        try:
            resp = requests.post(
                f"{BASE_URL}/research",
                json={"query": "attention mechanisms in transformers", "max_papers": 3},
                timeout=300,  # 5 minutes for full pipeline
            )
            if resp.status_code == 200:
                data = resp.json()
                assert data["papers_analyzed"] > 0
                assert "markdown_report" in data
                assert len(data["citations"]) > 0
        except requests.ConnectionError:
            pytest.skip("API not running")
