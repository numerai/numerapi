import decimal
from unittest.mock import patch

import pytest

import numerapi


@pytest.fixture(scope="function", name="api")
def api_fixture():
    api = numerapi.CryptoAPI(verbosity="DEBUG")
    return api


@patch("numerapi.cryptoapi.CryptoAPI.raw_query")
def test_get_leaderboard(mocked, api):
    mocked.return_value = {
        "data": {
            "cryptosignalsLeaderboard": [
                {
                    "nmrStaked": "13.0",
                    "rank": 1,
                    "username": "crypto_user",
                    "corrRep": 0.1,
                    "mmcRep": 0.2,
                    "return_1_day": 0.03,
                    "return_52_weeks": 0.4,
                    "return_13_weeks": 0.15,
                }
            ]
        }
    }

    lb = api.get_leaderboard(1)

    assert len(lb) == 1
    assert lb[0]["username"] == "crypto_user"
    assert lb[0]["nmrStaked"] == decimal.Decimal("13.0")
    mocked.assert_called_once()
    args, kwargs = mocked.call_args
    assert "cryptosignalsLeaderboard" in args[0]
    assert args[1] == {"limit": 1, "offset": 0}
    assert kwargs == {}
