import pytest
import responses

import pandas as pd

import numerapi
from numerapi import base_api


@pytest.fixture(scope='function', name="api")
def api_fixture():
    api = numerapi.SignalsAPI(verbosity='DEBUG')
    return api


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
