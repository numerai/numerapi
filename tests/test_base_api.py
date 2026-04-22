import datetime
import decimal
import json
import os
import pytest
import responses

from numerapi import base_api


@pytest.fixture(scope='function', name="api")
def api_fixture():
    api = base_api.Api(verbosity='DEBUG')
    return api


def test_NumerAPI():
    # invalid log level should raise
    with pytest.raises(AttributeError):
        base_api.Api(verbosity="FOO")


def test__login(api):
    # passing only one of public_id and secret_key is not enough
    api._login(public_id="foo", secret_key=None)
    assert api.token is None
    api._login(public_id=None, secret_key="bar")
    assert api.token is None
    # passing both works
    api._login(public_id="foo", secret_key="bar")
    assert api.token == ("foo", "bar")

    # using env variables
    os.environ["NUMERAI_SECRET_KEY"] = "key"
    os.environ["NUMERAI_PUBLIC_ID"] = "id"
    api._login()
    assert api.token == ("id", "key")


@responses.activate
def test_raw_query(api):
    query = "query {latestNmrPrice {priceUsd}}"
    responses.add(
        responses.POST,
        base_api.API_TOURNAMENT_URL,
        json={"data": {"latestNmrPrice": {"priceUsd": "42.00"}}},
    )
    result = api.raw_query(query)
    assert isinstance(result, dict)
    assert "data" in result


@responses.activate
def test_get_account(api):
    api.token = ("", "")
    account = {'apiTokens': [{'name': 'uploads',
                              'public_id': 'AAA',
                              'scopes': ['upload_submission']},
                             {'name': '_internal_default',
                              'public_id': 'BBB',
                              'scopes': ['upload_submission',
                                         'read_submission_info',
                                         'read_user_info']},
                             {'name': 'all',
                              'public_id': 'CCC',
                              'scopes': ['upload_submission',
                                         'stake',
                                         'read_submission_info',
                                         'read_user_info']}],
               'availableNmr': '1.010000000000000000',
               'email': 'no-reply@eu83t4nncmxv3g2.xyz',
               'id': '0c10a70a-a851-478f-a289-7a05fe397008',
               'insertedAt': "2018-01-01 11:11:11",
               'mfaEnabled': False,
               'models': [{'id': '881778ad-2ee9-4fb0-82b4-7b7c0f7ce17d',
                           'name': 'model1',
                           'submissions':
                            [{'filename': 'predictions-pPbLKSHGiR.csv',
                              'id': 'f2369b69-8c43-47aa-b4de-de3a9de5f52c'}],
                           'v2Stake': {'status': None, 'txHash': None}},
                          {'id': '881778ad-2ee9-4fb0-82b4-7b7c0f7ce17d',
                           'name': 'model2',
                           'submissions':
                           [{'filename': 'predictions-pPbPOWQNGiR.csv',
                             'id': '46a62500-87c7-4d7c-98ad-b743037e8cfd'}],
                           'v2Stake': {'status': None, 'txHash': None}}],
               'status': 'VERIFIED',
               'username': 'username1',
               'walletAddress': '0x0000000000000000000000000000'}

    data = {'data': {'account': account}}
    responses.add(responses.POST, base_api.API_TOURNAMENT_URL, json=data)
    res = api.get_account()
    assert isinstance(res, dict)
    assert len(res.get('models')) == 2


@responses.activate
def test_get_models(api):
    api.token = ("", "")
    models_list = [
        {"name": "model_x", "id": "95b0d9e2-c901-4f2b-9c98-24138b0bd706",
         "tournament": 0},
        {"name": "model_y", "id": "2c6d63a4-013f-42d1-bbaf-bf35725d29f7",
         "tournament": 0}]
    data = {'data': {'account': {'models': models_list}}}
    responses.add(responses.POST, base_api.API_TOURNAMENT_URL, json=data)
    models = api.get_models()
    assert sorted(models.keys()) == ['model_x', 'model_y']
    assert sorted(models.values()) == ['2c6d63a4-013f-42d1-bbaf-bf35725d29f7',
                                       '95b0d9e2-c901-4f2b-9c98-24138b0bd706']


@responses.activate
def test_set_submission_webhook(api):
    api.token = ("", "")
    data = {
      "data": {
        "setSubmissionWebhook": "true"
      }
    }
    responses.add(responses.POST, base_api.API_TOURNAMENT_URL, json=data)
    res = api.set_submission_webhook(
        '2c6d63a4-013f-42d1-bbaf-bf35725d29f7',
        'https://triggerurl'
    )
    assert res


@responses.activate
def test_submission_scores(api):
    api.tournament_id = 11
    data = {
        "data": {
            "submissionScores": [
                {
                    "roundId": "round-1",
                    "submissionId": "submission-1",
                    "roundNumber": 123,
                    "roundResolveTime": "2026-04-01T00:00:00Z",
                    "roundScoreTime": "2026-03-29T00:00:00Z",
                    "roundCloseStakingTime": "2026-03-28T00:00:00Z",
                    "value": 0.12,
                    "percentile": 0.95,
                    "displayName": "CORR20",
                    "version": "v5",
                    "date": "2026-03-30T00:00:00Z",
                    "day": 2,
                    "resolveDate": "2026-04-01T00:00:00Z",
                    "resolved": True,
                }
            ]
        }
    }
    responses.add(responses.POST, base_api.API_TOURNAMENT_URL, json=data)

    res = api.submission_scores(
        "model-1",
        display_name="CORR20",
        version="v5",
        day=2,
        resolved=True,
        last_n_rounds=5,
        distinct_on_round=True,
    )

    assert len(res) == 1
    assert res[0]["displayName"] == "CORR20"
    assert isinstance(res[0]["roundResolveTime"], datetime.datetime)
    assert isinstance(res[0]["roundScoreTime"], datetime.datetime)
    assert isinstance(res[0]["roundCloseStakingTime"], datetime.datetime)
    assert isinstance(res[0]["date"], datetime.datetime)
    assert isinstance(res[0]["resolveDate"], datetime.datetime)

    request_body = json.loads(responses.calls[0].request.body)
    assert request_body["variables"]["tournament"] == 11
    assert request_body["variables"]["lastNRounds"] == 5
    assert request_body["variables"]["distinctOnRound"] is True


@responses.activate
def test_list_rounds(api):
    api.tournament_id = 11
    data = {
        "data": {
            "rounds": [
                {
                    "id": "round-1",
                    "tournament": 11,
                    "number": 123,
                    "target": "main",
                    "closeTime": "2026-03-27T00:00:00Z",
                    "closeStakingTime": "2026-03-26T12:00:00Z",
                    "openTime": "2026-03-20T00:00:00Z",
                    "scoreTime": "2026-03-29T00:00:00Z",
                    "resolveTime": "2026-04-01T00:00:00Z",
                    "resolvedGeneral": False,
                    "resolvedStaking": False,
                    "payoutFactor": "0.8",
                    "stakeThreshold": 0.1,
                    "minCorrMultiplier": 0.0,
                    "maxCorrMultiplier": 1.0,
                    "defaultCorrMultiplier": 0.5,
                    "minMmcMultiplier": 0.0,
                    "maxMmcMultiplier": 1.0,
                    "defaultMmcMultiplier": 0.5,
                    "dataDatestamp": 20260320,
                }
            ]
        }
    }
    responses.add(responses.POST, base_api.API_TOURNAMENT_URL, json=data)

    res = api.list_rounds(number=123, target="main", status="open", limit=5)

    assert len(res) == 1
    assert isinstance(res[0]["closeTime"], datetime.datetime)
    assert isinstance(res[0]["closeStakingTime"], datetime.datetime)
    assert isinstance(res[0]["openTime"], datetime.datetime)
    assert isinstance(res[0]["scoreTime"], datetime.datetime)
    assert isinstance(res[0]["resolveTime"], datetime.datetime)
    assert isinstance(res[0]["payoutFactor"], decimal.Decimal)

    request_body = json.loads(responses.calls[0].request.body)
    assert request_body["variables"]["tournament"] == 11
    assert request_body["variables"]["number"] == 123
    assert request_body["variables"]["target"] == "main"
    assert request_body["variables"]["status"] == "OPEN"
    assert request_body["variables"]["limit"] == 5


@responses.activate
def test_list_rounds_uses_api_tournament_id_by_default(api):
    api.tournament_id = 11
    data = {"data": {"rounds": []}}
    responses.add(responses.POST, base_api.API_TOURNAMENT_URL, json=data)

    api.list_rounds()

    request_body = json.loads(responses.calls[0].request.body)
    assert request_body["variables"]["tournament"] == 11


@responses.activate
def test_pending_model_payouts(api):
    api.token = ("", "")
    api.tournament_id = 12
    data = {
        "data": {
            "pendingModelPayouts": {
                "actual": [
                    {
                        "roundId": "round-a",
                        "roundNumber": 12,
                        "roundResolveTime": "2026-04-02T00:00:00Z",
                        "modelId": "model-a",
                        "modelName": "alpha",
                        "modelDisplayName": "Alpha",
                        "payoutNmr": "2.5000",
                        "payoutValue": "31.20",
                        "currencySymbol": "$",
                    }
                ],
                "pending": [
                    {
                        "roundId": "round-b",
                        "roundNumber": 13,
                        "roundResolveTime": "2026-04-09T00:00:00Z",
                        "modelId": "model-b",
                        "modelName": "beta",
                        "modelDisplayName": "Beta",
                        "payoutNmr": "1.1000",
                        "payoutValue": "13.73",
                        "currencySymbol": "$",
                    }
                ],
            }
        }
    }
    responses.add(responses.POST, base_api.API_TOURNAMENT_URL, json=data)

    res = api.pending_model_payouts()

    assert len(res["actual"]) == 1
    assert len(res["pending"]) == 1
    assert res["actual"][0]["payoutNmr"] == decimal.Decimal("2.5000")
    assert res["pending"][0]["payoutValue"] == decimal.Decimal("13.73")
    assert isinstance(res["actual"][0]["roundResolveTime"], datetime.datetime)
    assert isinstance(res["pending"][0]["roundResolveTime"], datetime.datetime)

    request_body = json.loads(responses.calls[0].request.body)
    assert request_body["variables"]["tournament"] == 12


@responses.activate
def test_round_model_performances_v2_warns(api):
    api.tournament_id = 8
    data = {
        "data": {
            "v2RoundModelPerformances": [
                {
                    "atRisk": "10.5",
                    "corrMultiplier": 1.0,
                    "mmcMultiplier": 0.5,
                    "roundPayoutFactor": "0.8",
                    "roundNumber": 456,
                    "roundOpenTime": "2026-03-01T00:00:00Z",
                    "roundResolveTime": "2026-03-29T00:00:00Z",
                    "roundResolved": True,
                    "roundTarget": "main",
                    "submissionScores": [
                        {
                            "date": "2026-03-28T00:00:00Z",
                            "day": 20,
                            "displayName": "CORR20",
                            "payoutPending": "0.8",
                            "payoutSettled": "0.7",
                            "percentile": 0.9,
                            "value": 0.12,
                        }
                    ],
                }
            ]
        }
    }
    responses.add(responses.POST, base_api.API_TOURNAMENT_URL, json=data)

    with pytest.warns(DeprecationWarning, match="round_model_performances_v2"):
        res = api.round_model_performances_v2("model-1")

    assert len(res) == 1
    assert res[0]["atRisk"] == decimal.Decimal("10.5")
    assert isinstance(res[0]["roundOpenTime"], datetime.datetime)
    assert isinstance(res[0]["roundResolveTime"], datetime.datetime)
    assert res[0]["submissionScores"][0]["payoutPending"] == decimal.Decimal("0.8")


@responses.activate
def test_v3_stake_auth(api):
    api.token = ("", "")
    data = {"data": {"v3StakeAuth": {
        "authorizationSigner": "0xsigner",
        "authorizationDigest": "0xdigest",
        "chainId": "11155111",
        "deadline": "1770000000",
        "maxAmount": "25",
        "modelId": "0xmodel",
        "nmrAddress": "0xnmr",
        "nonce": "0",
        "roundId": "4321",
        "signature": "0x1234",
        "staker": "0xstaker",
        "stakingAddress": "0xstaking",
        "submissionId": "submission-id",
        "submissionHash": "0xhash",
        "tournamentId": "8",
    }}}
    responses.add(responses.POST, base_api.API_TOURNAMENT_URL, json=data)

    result = api.v3_stake_auth("submission-id", "0xstaker", amount=25)

    body = json.loads(responses.calls[0].request.body)
    assert "mutation" not in body["query"]
    assert "query(" in body["query"]
    assert "v3StakeAuth" in body["query"]
    assert body["variables"]["submissionId"] == "submission-id"
    assert body["variables"]["maxAmount"] == "25"
    assert "maxAmount" in body["query"]
    assert result["maxAmount"] == "25"
    assert result["amount"] == "25"
    assert result["authorizationDigest"] == "0xdigest"


@responses.activate
def test_v3_stake_auth_accepts_max_amount(api):
    api.token = ("", "")
    data = {"data": {"v3StakeAuth": {
        "authorizationSigner": "0xsigner",
        "authorizationDigest": "0xdigest",
        "chainId": "11155111",
        "deadline": "1770000000",
        "maxAmount": "30",
        "modelId": "0xmodel",
        "nmrAddress": "0xnmr",
        "nonce": "0",
        "roundId": "4321",
        "signature": "0x1234",
        "staker": "0xstaker",
        "stakingAddress": "0xstaking",
        "submissionId": "submission-id",
        "submissionHash": "0xhash",
        "tournamentId": "8",
    }}}
    responses.add(responses.POST, base_api.API_TOURNAMENT_URL, json=data)

    result = api.v3_stake_auth(
        "submission-id",
        "0xstaker",
        max_amount="30",
    )

    body = json.loads(responses.calls[0].request.body)
    assert "mutation" not in body["query"]
    assert "query(" in body["query"]
    assert body["variables"]["maxAmount"] == "30"
    assert result["maxAmount"] == "30"
    assert result["amount"] == "30"


@responses.activate
def test_v3_stake_config(api):
    api.token = ("", "")
    data = {"data": {"v3StakeConfig": {
        "address": "0xstaking",
        "authorizationSigner": "0xsigner",
        "nmrAddress": "0xnmr",
        "owner": "0xowner",
        "paused": False,
        "pendingOwner": "0xpending",
        "serviceWallet": "0xservice",
    }}}
    responses.add(responses.POST, base_api.API_TOURNAMENT_URL, json=data)

    result = api.v3_stake_config()

    body = json.loads(responses.calls[0].request.body)
    assert "v3StakeConfig" in body["query"]
    assert result["authorizationSigner"] == "0xsigner"


@responses.activate
def test_v3_stake_round(api):
    api.token = ("", "")
    data = {"data": {"v3StakeRound": {
        "closeTime": "1",
        "merkleRoot": "0xroot",
        "openTime": "0",
        "payoutFactor": "0.5",
        "remainingBurn": "0",
        "remainingPayout": "2",
        "resolveTime": "2",
        "resolved": False,
        "roundId": "4321",
        "stakeCap": "100",
        "stakeThreshold": "10",
        "state": "open",
        "totalPayout": "2",
        "totalStaked": "50",
        "tournamentId": "8",
    }}}
    responses.add(responses.POST, base_api.API_TOURNAMENT_URL, json=data)

    result = api.v3_stake_round(4321)

    body = json.loads(responses.calls[0].request.body)
    assert "v3StakeRound" in body["query"]
    assert body["variables"]["roundId"] == "4321"
    assert result["roundId"] == "4321"


@responses.activate
def test_v3_stake_claim(api):
    api.token = ("", "")
    data = {"data": {"v3StakeClaim": {
        "apiModelId": "api-model-id",
        "burnAmountWei": "0",
        "merkleRoot": "0xroot",
        "modelId": "0xmodel",
        "payoutAmountWei": "2000000000000000000",
        "proof": ["0xproof"],
        "roundId": "4321",
        "staker": "0xstaker",
        "submissionId": "submission-id",
        "tournamentId": "8",
    }}}
    responses.add(responses.POST, base_api.API_TOURNAMENT_URL, json=data)

    result = api.v3_stake_claim(4321, "api-model-id", "0xstaker")

    body = json.loads(responses.calls[0].request.body)
    assert "v3StakeClaim" in body["query"]
    assert body["variables"]["roundId"] == "4321"
    assert body["variables"]["modelId"] == "api-model-id"
    assert result["proof"] == ["0xproof"]
