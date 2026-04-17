"""Ensure tests import the local numerapi package."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
root_str = str(ROOT)
if root_str not in sys.path:
    sys.path.insert(0, root_str)

from numerapi import base_api

DEFAULT_FAKE_GRAPHQL_API_URL = "https://fake-api-tournament.numer.ai"


def pytest_addoption(parser):
    group = parser.getgroup("graphql")
    group.addoption(
        "--mode",
        action="store",
        choices=("mock", "integration"),
        default="mock",
        help=(
            "Select whether tests use a fake GraphQL API base URL or a real one. "
            "Live API tests only run in integration mode."
        ),
    )
    group.addoption(
        "--api-url",
        action="store",
        default=None,
        help=(
            "Base GraphQL API URL to use in tests when --mode=integration. "
            "Defaults to numerapi.base_api.API_TOURNAMENT_URL."
        ),
    )


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "live_api: test requires a real GraphQL API backend",
    )


def pytest_collection_modifyitems(config, items):
    if config.getoption("--mode") == "integration":
        return

    skip_live_api = pytest.mark.skip(
        reason="requires --mode=integration to run against a real GraphQL API backend"
    )
    for item in items:
        if "live_api" in item.keywords:
            item.add_marker(skip_live_api)


@pytest.fixture(scope="session", autouse=True)
def configure_graphql_api_url(pytestconfig):
    original_url = base_api.API_TOURNAMENT_URL
    mode = pytestconfig.getoption("--mode")
    configured_url = pytestconfig.getoption("--api-url")

    if mode == "integration":
        base_api.API_TOURNAMENT_URL = configured_url or original_url
    else:
        base_api.API_TOURNAMENT_URL = DEFAULT_FAKE_GRAPHQL_API_URL

    yield base_api.API_TOURNAMENT_URL

    base_api.API_TOURNAMENT_URL = original_url
