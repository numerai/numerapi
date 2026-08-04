import decimal
from unittest.mock import patch

import pytest
import responses

import pandas as pd

import numerapi
from numerapi import base_api


@patch("numerapi.base_api.Api.raw_query")
def test_public_user_profile(mocked, api):
    mocked.return_value = {
        "data": {"v3UserProfile": {
            "id": "49962e16-6bc9-4a78-a751-09c20c99bcb3",
            "username": "floury_kerril_moodle",
            "startDate": "2020-05-12T01:23:00Z",
            "bio": None, "nmrStaked": None}}}

    profile = api.public_user_profile("floury_kerril_moodle")

    assert profile["id"] == "49962e16-6bc9-4a78-a751-09c20c99bcb3"
    args, _ = mocked.call_args
    # signals models must be resolved within the signals tournament (11)
    assert args[1]["tournament"] == api.tournament_id == 11


@pytest.fixture(scope='function', name="api")
def api_fixture():
    api = numerapi.SignalsAPI(verbosity='DEBUG')
    return api


@patch("numerapi.signalsapi.SignalsAPI.raw_query")
def test_stake_get(mocked, api):
    mocked.return_value = {"data": {"v3UserProfile": {"stakeValue": "14.63"}}}

    stake = api.stake_get("uuazed")

    assert stake == decimal.Decimal("14.63")
    args, _ = mocked.call_args
    # current stake lives in `stakeValue`; `totalStake` no longer exists
    assert "stakeValue" in args[0]
    assert "totalStake" not in args[0]
    assert args[1]["tournament"] == api.tournament_id == 11


@patch("numerapi.signalsapi.SignalsAPI.raw_query")
def test_stake_get_no_stake(mocked, api):
    # a model with no stake returns null -> None, not a KeyError
    mocked.return_value = {"data": {"v3UserProfile": {"stakeValue": None}}}
    assert api.stake_get("uuazed") is None


@pytest.mark.live_api
def test_get_leaderboard(api):
    lb = api.get_leaderboard(1)
    assert len(lb) == 1


@responses.activate
def test_upload_predictions(api, tmpdir):
    api.token = ("", "")
    # we need to mock 3 network calls: 1. auth 2. file upload and 3. submission
    data = {"data": {"submissionUploadSignalsAuth":
            {"url": "https://uploadurl", "filename": "filename"}}}
    responses.add(responses.POST, base_api.API_TOURNAMENT_URL, json=data)
    responses.add(responses.PUT, "https://uploadurl")
    data = {"data": {"createSignalsSubmission": {"id": "1234"}}}
    responses.add(responses.POST, base_api.API_TOURNAMENT_URL, json=data)

    path = tmpdir.join("somefilepath")
    path.write("content")
    submission_id = api.upload_predictions(str(path))

    assert submission_id == "1234"
    assert len(responses.calls) == 3

#Test pandas.DataFrame version of upload_predictions
@responses.activate
def test_upload_predictions_df(api):
    api.token = ("", "")
    # we need to mock 3 network calls: 1. auth 2. file upload and 3. submission
    data = {"data": {"submissionUploadSignalsAuth":
            {"url": "https://uploadurl", "filename": "predictions.csv"}}}
    responses.add(responses.POST, base_api.API_TOURNAMENT_URL, json=data)
    responses.add(responses.PUT, "https://uploadurl")
    data = {"data": {"createSignalsSubmission": {"id": "12345"}}}
    responses.add(responses.POST, base_api.API_TOURNAMENT_URL, json=data)

    df = pd.DataFrame.from_dict({"bloomberg_ticker":[],"signal":[]})
    submission_id = api.upload_predictions(df = df)

    assert submission_id == "12345"
    assert len(responses.calls) == 3
