import datetime
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


@patch("numerapi.cryptoapi.CryptoAPI.raw_query")
def test_public_user_profile(mocked, api):
    mocked.return_value = {
        "data": {
            "v3UserProfile": {
                "id": "08d44800-be35-41f5-9896-63a1be9c51ef",
                "username": "crypto_user",
                "startDate": "2024-11-28T13:09:20Z",
                "bio": None,
                "nmrStaked": "13.0",
            }
        }
    }

    profile = api.public_user_profile("crypto_user")

    assert profile["id"] == "08d44800-be35-41f5-9896-63a1be9c51ef"
    assert profile["username"] == "crypto_user"
    # string fields are converted to python objects
    assert isinstance(profile["startDate"], datetime.datetime)
    assert profile["nmrStaked"] == decimal.Decimal("13.0")
    mocked.assert_called_once()
    args, kwargs = mocked.call_args
    # crypto must be resolved by name *within its own tournament* (12),
    # otherwise a model id from another tournament could be returned
    assert "v3UserProfile" in args[0]
    assert args[1]["tournament"] == api.tournament_id == 12


@patch("numerapi.cryptoapi.CryptoAPI.raw_query")
def test_public_user_profile_to_model_id(mocked, api):
    # the model id is what `submission_scores` needs
    mocked.return_value = {
        "data": {"v3UserProfile": {
            "id": "the-model-id", "username": "crypto_user",
            "startDate": None, "bio": None, "nmrStaked": None}}}
    model_id = api.public_user_profile("crypto_user")["id"]
    assert model_id == "the-model-id"
