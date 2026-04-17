import pytest

import numerapi


@pytest.fixture(scope='function', name="api")
def api_fixture():
    api = numerapi.CryptoAPI(verbosity='DEBUG')
    return api

def test_get_leaderboard(api):
    lb = api.get_leaderboard(1)
    assert len(lb) == 1