import pytest
import datetime
import json
import pytz
import responses

import pandas as pd

import numerapi
from numerapi import base_api


@pytest.fixture(scope='function', name="api")
def api_fixture():
    api = numerapi.NumerAPI(verbosity='DEBUG')
    return api


@pytest.mark.live_api
def test_get_competitions(api):
    res = api.get_competitions(tournament=1)
    assert isinstance(res, list)
    assert len(res) > 80


@pytest.mark.live_api
def test_get_current_round(api):
    current_round = api.get_current_round()
    assert current_round >= 82


@pytest.mark.live_api
@pytest.mark.parametrize("fun", ["get_account", "wallet_transactions"])
def test_unauthorized_requests(api, fun):
    with pytest.raises(ValueError) as err:
        # while this won't work because we are not authorized, it still tells
        # us if the remaining code works
        getattr(api, fun)()
    # error should warn about not being logged in.
    assert "API keys required for this action" in str(err.value) or \
           "Your session is invalid or has expired." in str(err.value)


@pytest.mark.live_api
def test_error_handling(api):
    # String instead of Int
    with pytest.raises(ValueError):
        api.get_competitions("foo")
    # unauthendicated request
    with pytest.raises(ValueError):
        # set wrong token
        api.token = ("foo", "bar")
        api.get_account()


@responses.activate
def test_upload_predictions(api, tmpdir):
    api.token = ("", "")
    # we need to mock 3 network calls: 1. auth 2. file upload and 3. submission
    data = {"data": {"submission_upload_auth": {"url": "https://uploadurl",
                                                "filename": "filename"}}}
    responses.add(responses.POST, base_api.API_TOURNAMENT_URL, json=data)
    responses.add(responses.PUT, "https://uploadurl")
    data = {"data": {"create_submission": {"id": "1234"}}}
    responses.add(responses.POST, base_api.API_TOURNAMENT_URL, json=data)

    path = tmpdir.join("somefilepath")
    path.write("content")
    submission_id = api.upload_predictions(str(path))

    assert submission_id == "1234"
    assert len(responses.calls) == 3


@responses.activate
def test_upload_predictions_df(api):
    api.token = ("", "")
    data = {"data": {
        "submission_upload_auth": {"url": "https://uploadurl",
                                          "filename": "predictions.csv"}}}
    responses.add(responses.POST, base_api.API_TOURNAMENT_URL, json=data)
    responses.add(responses.PUT, "https://uploadurl")
    data = {"data": {"create_submission": {"id": "12345"}}}
    responses.add(responses.POST, base_api.API_TOURNAMENT_URL, json=data)

    df = pd.DataFrame.from_dict({"id": [], "prediction": []})
    submission_id = api.upload_predictions(df=df)

    assert len(responses.calls) == 3
    assert submission_id == "12345"


@responses.activate
def test_check_new_round(api):
    open_time = datetime.datetime.now(tz=pytz.utc)
    data = {"data": {"rounds": [{"openTime": open_time.isoformat()}]}}
    responses.add(responses.POST, base_api.API_TOURNAMENT_URL, json=data)

    open_time = datetime.datetime(2000, 1, 1).replace(tzinfo=pytz.utc)
    data = {"data": {"rounds": [{"openTime": open_time.isoformat()}]}}
    responses.add(responses.POST, base_api.API_TOURNAMENT_URL, json=data)

    # first example
    assert api.check_new_round()
    # second
    assert not api.check_new_round()

