"""Parts of the API that is shared between Signals and Classic"""

import datetime
import logging
import os
import warnings
from io import BytesIO
from typing import Dict, List, Tuple, Union

import pandas as pd
import pytz
import requests

from numerapi import utils

API_TOURNAMENT_URL = "https://api-tournament.numer.ai"


class Api:
    """Wrapper around the Numerai API"""

    def __init__(
        self,
        public_id: str | None = None,
        secret_key: str | None = None,
        verbosity: str = "INFO",
        show_progress_bars: bool = True,
    ):
        """
        initialize Numerai API wrapper for Python

        Args:
            public_id (str): first part of your token generated at
                Numer.ai->Account->Custom API keys
            secret_key (str): second part of your token generated at
                Numer.ai->Account->Custom API keys
            verbosity (str): indicates what level of messages should be
                displayed. valid values are "debug", "info", "warning",
                "error" and "critical"
            show_progress_bars (bool): flag to turn of progress bars
        """

        # set up logging
        self.logger = logging.getLogger(__name__)
        numeric_log_level = getattr(logging, verbosity.upper())
        log_format = "%(asctime)s %(levelname)s %(name)s: %(message)s"
        logging.basicConfig(format=log_format, level=numeric_log_level)

        self._login(public_id, secret_key)

        self.show_progress_bars = show_progress_bars
        self.tournament_id = 0
        self.global_data_dir = "."

    def _login(
        self, public_id: str | None = None, secret_key: str | None = None
    ) -> None:
        # check env variables if not set
        if not public_id or not secret_key:
            public_id, secret_key = utils.load_secrets()

        if public_id and secret_key:
            self.token = (public_id, secret_key)
        elif not public_id and not secret_key:
            self.token = None
        else:
            self.logger.warning("You need to supply both a public id and a secret key.")
            self.token = None

    def _handle_call_error(self, errors) -> str:
        msg = ""
        if isinstance(errors, list):
            for error in errors:
                if "message" in error:
                    msg = error["message"]
                    self.logger.error(msg)
        elif isinstance(errors, dict):
            if "detail" in errors:
                msg = errors["detail"]
                self.logger.error(msg)
        return msg

    def raw_query(
        self,
        query: str,
        variables: Dict | None = None,
        authorization: bool = False,
        *,
        retries: int = 3,
        delay: int = 5,
        backoff: int = 2,
    ):
        """Send a raw request to the Numerai's GraphQL API.

        This function allows to build your own queries and fetch results from
        Numerai's GraphQL API. Checkout
        https://medium.com/numerai/getting-started-with-numerais-new-tournament-api-77396e895e72
        for an introduction and https://api-tournament.numer.ai/ for the
        documentation.

        Args:
            query (str): your query
            variables (dict, optional): dict of variables
            authorization (bool, optional): does the request require
                authorization, defaults to `False`
            retries (int): for 5XX errors, how often should numerapi retry
            delay (int): in case of retries, how many seconds to wait between tries
            backoff (int): in case of retries, multiplier to increase the delay between retries

        Returns:
            dict: Result of the request

        Raises:
            ValueError: if something went wrong with the requests. For example,
                this could be a wrongly formatted query or a problem at
                Numerai's end. Have a look at the error messages, in most cases
                the problem is obvious.

        Example:
            >>> query = '''query($tournament: Int!)
                           {rounds(tournament: $tournament number: 0)
                            {number}}'''
            >>> args = {'tournament': 1}
            >>> NumerAPI().raw_query(query, args)
            {'data': {'rounds': [{'number': 104}]}}
        """
        body = {"query": query, "variables": variables}
        self.logger.debug(body)
        headers = {"Content-type": "application/json", "Accept": "application/json"}
        if authorization:
            if self.token:
                public_id, secret_key = self.token
                headers["Authorization"] = f"Token {public_id}${secret_key}"
            else:
                raise ValueError("API keys required for this action.")

        result = utils.post_with_err_handling(
            API_TOURNAMENT_URL,
            body,
            headers,
            retries=retries,
            delay=delay,
            backoff=backoff,
        )

        if result and "errors" in result:
            err = self._handle_call_error(result["errors"])
            # fail!
            raise ValueError(err)
        return result

    def list_datasets(self, round_num: int | None = None) -> List[str]:
        """List of available data files

        Args:
            round_num (int, optional): tournament round you are interested in.
                defaults to the current round
        Returns:
            list of str: filenames
        Example:
            >>> NumerAPI().list_datasets()
            [
              "numerai_training_data.csv",
              "numerai_training_data.parquet",
              "numerai_validation_data.csv",
              "numerai_validation_data.parquet"
            ]
        """
        query = """
        query ($round: Int
               $tournament: Int) {
            listDatasets(round: $round
                         tournament: $tournament)
        }"""
        args = {"round": round_num, "tournament": self.tournament_id}
        return self.raw_query(query, args)["data"]["listDatasets"]

    def download_dataset(
        self, filename: str, dest_path: str | None = None, round_num: int | None = None
    ) -> str:
        """Download specified file for the given round.

        Args:
            filename (str, optional): file to be downloaded
            dest_path (str, optional): complete path where the file should be
                stored, defaults to the same name as the source file
            round_num (int, optional): tournament round you are interested in.
                defaults to the current round

        Returns:
            str: path of the downloaded file

        Example:
            >>> filenames = NumerAPI().list_datasets()
            >>> NumerAPI().download_dataset(filenames[0]}")
        """
        if dest_path is None:
            dest_path = filename

        if self.global_data_dir != ".":
            dest_path = os.path.join(self.global_data_dir, dest_path)

        # if directories are used, ensure they exist
        dirs = os.path.dirname(dest_path)
        if dirs:
            os.makedirs(dirs, exist_ok=True)

        query = """
        query ($filename: String!
               $round: Int
               $tournament: Int) {
            dataset(filename: $filename
                    round: $round
                    tournament: $tournament)
        }
        """
        args = {
            "filename": filename,
            "round": round_num,
            "tournament": self.tournament_id,
        }

        dataset_url = self.raw_query(query, args)["data"]["dataset"]
        utils.download_file(dataset_url, dest_path, self.show_progress_bars)
        return dest_path

    def set_global_data_dir(self, directory: str):
        """Set directory used for downloading files

        Args:
            directory (str): directory to be used
        """
        self.global_data_dir = directory
        # create folder if necessary
        os.makedirs(directory, exist_ok=True)

    def get_account(self) -> Dict:
        """Get all information about your account!

        Returns:
            dict: user information including the fields:

                * assignedEthAddress (`str`)
                * availableNmr (`decimal.Decimal`)
                * availableUsd (`decimal.Decimal`)
                * email (`str`)
                * id (`str`)
                * insertedAt (`datetime`)
                * mfaEnabled (`bool`)
                * status (`str`)
                * username (`str`)
                * apiTokens (`list`) each with the following fields:
                 * name (`str`)
                 * public_id (`str`)
                 * scopes (`list of str`)
                * models
                  * username
                  * id
                  * submissions
                  * v2Stake
                   * status (`str`)
                   * txHash (`str`)

        Example:
            >>> api = NumerAPI(secret_key="..", public_id="..")
            >>> api.get_account()
            {'apiTokens': [
                    {'name': 'tokenname',
                     'public_id': 'BLABLA',
                     'scopes': ['upload_submission', 'stake', ..]
                     }, ..],
             'assignedEthAddress': '0x0000000000000000000000000001',
             'availableNmr': Decimal('99.01'),
             'email': 'username@example.com',
             'id': '1234-ABC..',
             'insertedAt': datetime.datetime(2018, 1, 1, 2, 16, 48),
             'mfaEnabled': False,
             'status': 'VERIFIED',
             'username': 'cool username',
             }
        """
        query = """
          query {
            account {
              username
              walletAddress
              availableNmr
              email
              id
              mfaEnabled
              status
              insertedAt
              models {
                id
                name
                submissions {
                  id
                  filename
                }
                v2Stake {
                  status
                  txHash
                }
              }
              apiTokens {
                name
                public_id
                scopes
              }
            }
          }
        """
        data = self.raw_query(query, authorization=True)["data"]["account"]
        # convert strings to python objects
        utils.replace(data, "insertedAt", utils.parse_datetime_string)
        utils.replace(data, "availableNmr", utils.parse_float_string)
        return data

    def models_of_account(self, account) -> Dict[str, str]:
        """Get all models (name and id) of an account

        Args:
            account (str): account name

        Returns:
            dict: modelname->model_id mapping, string->string

        Example:
            >>> api = NumerAPI()
            >>> NumerAPI().models_of_account("uuazed")
            {'uuazed': '9b157d9b-ce61-4ab5-9413-413f13a0c0a6', ...}
        """
        query = """
            query($username: Str!
                  $tournament: Int) {
                accountProfile(username: $username
                               tournament: $tournament){
                    models {
                    id
                    displayName
                    }
                }
            }
        """
        args = {"username": account, "tournament": self.tournament_id}
        data = self.raw_query(query, args)["data"]["accountProfile"]["models"]
        return {
            item["displayName"]: item["id"]
            for item in sorted(data, key=lambda x: x["displayName"])
        }

    def get_models(self, tournament: int | None = None) -> Dict:
        """Get mapping of account model names to model ids for convenience

        Args:
            tournament (int): ID of the tournament (optional)

        Returns:
            dict: modelname->model_id mapping, string->string

        Example:
            >>> api = NumerAPI(secret_key="..", public_id="..")
            >>> model = api.get_models()
            {'uuazed': '9b157d9b-ce61-4ab5-9413-413f13a0c0a6'}
        """
        query = """
          query {
            account {
              models {
                id
                name
                tournament
              }
            }
          }
        """
        if tournament is None:
            tournament = self.tournament_id
        data = self.raw_query(query, authorization=True)["data"]["account"]["models"]
        mapping = {
            model["name"]: model["id"]
            for model in data
            if model["tournament"] == tournament
        }
        return mapping

    def v3_stake_auth(
        self,
        submission_id: str,
        staker: str,
        amount: float | str | None = None,
        max_amount: float | str | None = None,
    ) -> Dict:
        """Issue a staking v3 authorization for a selected submission.

        Args:
            submission_id (str): submission id for the selected submission
            staker (str): staker wallet address
            amount (float or str, optional): max stake amount for the
                authorization. Retained as a backwards-compatible alias for
                `max_amount`.
            max_amount (float or str, optional): max stake amount for the
                authorization.

        Returns:
            dict: authorization payload with the following fields:

                * authorizationSigner (`str`)
                * authorizationDigest (`str`)
                * chainId (`str`)
                * deadline (`str`)
                * maxAmount (`str`)
                * amount (`str`) alias for `maxAmount`
                * modelId (`str`)
                * nmrAddress (`str`)
                * nonce (`str`)
                * roundId (`str`)
                * signature (`str`)
                * staker (`str`)
                * stakingAddress (`str`)
                * submissionId (`str`)
                * submissionHash (`str`)
                * tournamentId (`str`)
        """
        if (amount is None) == (max_amount is None):
            raise ValueError("Provide exactly one of amount or max_amount.")

        max_amount = max_amount if max_amount is not None else amount
        query = """
          query($submissionId: ID!, $staker: String!, $maxAmount: String!) {
            v3StakeAuth(
              submissionId: $submissionId
              staker: $staker
              maxAmount: $maxAmount
            ) {
              authorizationSigner
              authorizationDigest
              chainId
              deadline
              maxAmount
              modelId
              nmrAddress
              nonce
              roundId
              signature
              staker
              stakingAddress
              submissionId
              submissionHash
              tournamentId
            }
          }
        """
        arguments = {
            "submissionId": submission_id,
            "staker": staker,
            "maxAmount": str(max_amount),
        }
        authorization = self.raw_query(query, arguments, authorization=True)["data"][
            "v3StakeAuth"
        ]
        authorization["amount"] = authorization["maxAmount"]
        return authorization

    def v3_stake_config(self) -> Dict:
        """Fetch staking v3 contract configuration.

        Returns:
            dict: staking v3 configuration with the following fields:

                * address (`str`)
                * authorizationSigner (`str`)
                * nmrAddress (`str`)
                * owner (`str`)
                * paused (`bool`)
                * pendingOwner (`str`)
                * serviceWallet (`str`)
        """
        query = """
          query {
            v3StakeConfig {
              address
              authorizationSigner
              nmrAddress
              owner
              paused
              pendingOwner
              serviceWallet
            }
          }
        """
        return self.raw_query(query, authorization=True)["data"]["v3StakeConfig"]

    def v3_stake_round(self, round_id: int | str) -> Dict:
        """Fetch staking v3 round status by round id.

        Args:
            round_id (int or str): round id

        Returns:
            dict: staking v3 round data with the following fields:

                * closeTime (`str`)
                * merkleRoot (`str`)
                * openTime (`str`)
                * payoutFactor (`str`)
                * remainingBurn (`str`)
                * remainingPayout (`str`)
                * resolveTime (`str`)
                * resolved (`bool`)
                * roundId (`str`)
                * stakeCap (`str`)
                * stakeThreshold (`str`)
                * state (`str`)
                * totalPayout (`str`)
                * totalStaked (`str`)
                * tournamentId (`str`)
        """
        query = """
          query($roundId: String!) {
            v3StakeRound(roundId: $roundId) {
              closeTime
              merkleRoot
              openTime
              payoutFactor
              remainingBurn
              remainingPayout
              resolveTime
              resolved
              roundId
              stakeCap
              stakeThreshold
              state
              totalPayout
              totalStaked
              tournamentId
            }
          }
        """
        arguments = {"roundId": str(round_id)}
        return self.raw_query(query, arguments, authorization=True)["data"][
            "v3StakeRound"
        ]

    def v3_stake_claim(self, round_id: int | str, model_id: str, staker: str) -> Dict:
        """Fetch a staking v3 claim proof for a model and staker.

        Args:
            round_id (int or str): round id
            model_id (str): model id
            staker (str): staker wallet address

        Returns:
            dict: claim payload with the following fields:

                * apiModelId (`str`)
                * burnAmountWei (`str`)
                * merkleRoot (`str`)
                * modelId (`str`)
                * payoutAmountWei (`str`)
                * proof (`list` of `str`)
                * roundId (`str`)
                * staker (`str`)
                * submissionId (`str`)
                * tournamentId (`str`)
        """
        query = """
          query($roundId: String!, $modelId: ID!, $staker: String!) {
            v3StakeClaim(roundId: $roundId, modelId: $modelId, staker: $staker) {
              apiModelId
              burnAmountWei
              merkleRoot
              modelId
              payoutAmountWei
              proof
              roundId
              staker
              submissionId
              tournamentId
            }
          }
        """
        arguments = {
            "roundId": str(round_id),
            "modelId": model_id,
            "staker": staker,
        }
        return self.raw_query(query, arguments, authorization=True)["data"][
            "v3StakeClaim"
        ]

    def get_current_round(self, tournament: int | None = None) -> int | None:
        """Get number of the current active round.

        Args:
            tournament (int): ID of the tournament (optional)

        Returns:
            int: number of the current active round

        Example:
            >>> NumerAPI().get_current_round()
            104
        """
        if tournament is None:
            tournament = self.tournament_id
        # zero is an alias for the current round!
        query = """
            query($tournament: Int!) {
              rounds(tournament: $tournament
                     number: 0) {
                number
              }
            }
        """
        arguments = {"tournament": tournament}
        data = self.raw_query(query, arguments)["data"]["rounds"][0]
        if data is None:
            return None
        round_num = data["number"]
        return round_num

    def list_rounds(
        self,
        number: int | None = None,
        target: str | None = None,
        status: str | None = None,
        limit: int | None = None,
    ) -> List[Dict]:
        """List rounds with the filters supported by the round resolver.

        Args:
            number (int, optional): round number filter
            target (str, optional): round target filter
            status (str, optional): round status filter. One of `upcoming`,
                `open`, `resolving`, or `resolved`
            limit (int, optional): maximum number of rounds to return

        Returns:
            list of dicts: round entries matching the provided filters
        """
        query = """
            query($tournament: Int
                  $number: Int
                  $target: String
                  $status: RoundStatus
                  $limit: Int) {
              rounds(tournament: $tournament
                     number: $number
                     target: $target
                     status: $status
                     limit: $limit) {
                id
                tournament
                number
                target
                closeTime
                closeStakingTime
                openTime
                scoreTime
                resolveTime
                resolvedGeneral
                resolvedStaking
                payoutFactor
                stakeThreshold
                minCorrMultiplier
                maxCorrMultiplier
                defaultCorrMultiplier
                minMmcMultiplier
                maxMmcMultiplier
                defaultMmcMultiplier
                dataDatestamp
              }
            }
        """
        arguments = {
            "tournament": self.tournament_id,
            "number": number,
            "target": target,
            "status": None if status is None else status.upper(),
            "limit": limit,
        }
        rounds = self.raw_query(query, arguments)["data"]["rounds"]
        for round_info in rounds:
            for field in [
                "closeTime",
                "closeStakingTime",
                "openTime",
                "scoreTime",
                "resolveTime",
            ]:
                utils.replace(round_info, field, utils.parse_datetime_string)
            utils.replace(round_info, "payoutFactor", utils.parse_float_string)
        return rounds

    def set_bio(self, model_id: str, bio: str) -> bool:
        """Set bio field for a model id.

        Args:
            model_id (str): Target model UUID
            bio (str)

        Returns:
            bool: if the bio was changed successfully

        Example:
            >>> napi = numerapi.NumerAPI()
            >>> model_id = napi.get_models()["uuazed"]
            >>> napi.set_bio(model_id, "This model stinks.")
            True
        """
        mutation = """
            mutation($value: String!
                  $modelId: String) {
                setUserBio(value: $value
                           modelId: $modelId)
            }
        """
        arguments = {"value": bio, "modelId": model_id}
        res = self.raw_query(mutation, arguments, authorization=True)
        return res["data"]["setUserBio"]

    def set_link(self, model_id: str, link_text: str, link: str) -> bool:
        """Set link field for a model id.

        Args:
            model_id (str): Target model UUID
            link_test (str)
            link (str)

        Returns:
            bool: if the bio was changed successfully

        Example:
            >>> napi = numerapi.NumerAPI()
            >>> model_id = napi.get_models()["uuazed"]
            >>> napi.set_link(model_id, "buy my predictions", "numerbay.ai")
            True
        """
        mutation = """
            mutation($linkUrl: String!
                     $linkText: String
                     $modelId: String) {
                setUserLink(linkText: $linkText
                            linkUrl: $linkUrl
                            modelId: $modelId)
            }
        """
        args = {"linkUrl": link, "linkText": link_text, "modelId": model_id}
        res = self.raw_query(mutation, args, authorization=True)
        return res["data"]["setUserLink"]

    def wallet_transactions(self) -> List:
        """Get all transactions in your wallet.

        Returns:
            list: List of dicts with the following structure:

                 * from (`str`)
                 * posted (`bool`)
                 * status (`str`)
                 * to (`str`)
                 * txHash (`str`)
                 * amount (`decimal.Decimal`)
                 * time (`datetime`)
                 * tournament (`int`)

        Example:
            >>> api = NumerAPI(secret_key="..", public_id="..")
            >>> api.wallet_transactions()
            [{'amount': Decimal('1.000000000000000000'),
              'from': '0x000000000000000000000000000000000000313bc',
              'status': 'confirmed',
              'time': datetime.datetime(2023, 4, 19, 13, 28, 45),
              'to': '0x000000000000000000000000000000000006621',
              'tournament': None,
              'txHash': '0xeasdfkjaskljf314451234',
              'type': 'withdrawal'},
              ...
              ]
        """
        query = """
          query {
            account {
              walletTxns {
                amount
                from
                status
                to
                time
                tournament
                txHash
                type
              }
            }
          }
        """
        txs = self.raw_query(query, authorization=True)["data"]["account"]["walletTxns"]
        # convert strings to python objects
        for transaction in txs:
            utils.replace(transaction, "time", utils.parse_datetime_string)
            utils.replace(transaction, "amount", utils.parse_float_string)
        return txs

    def set_submission_webhook(self, model_id: str, webhook: str | None = None) -> bool:
        """Set a model's submission webhook used in Numerai Compute.
        Read More: https://docs.numer.ai/tournament/compute

        Args:
            model_id (str): Target model UUID

            webhook (str): The compute webhook to trigger this model

        Returns:
            bool: confirmation that your webhook has been set

        Example:
            >>> api = NumerAPI(secret_key="..", public_id="..")
            >>> api.set_submission_webhook(model_id="..", webhook="..")
            True
        """
        query = """
          mutation (
            $modelId: String!
            $newSubmissionWebhook: String
          ) {
            setSubmissionWebhook(
              modelId: $modelId
              newSubmissionWebhook: $newSubmissionWebhook
            )
          }
        """
        arguments = {"modelId": model_id, "newSubmissionWebhook": webhook}
        res = self.raw_query(query, arguments, authorization=True)
        return res["data"]["setSubmissionWebhook"] == "true"

    def _upload_auth(
        self, endpoint: str, file_path: str, tournament: int, model_id: str
    ) -> Dict[str, str]:
        auth_query = f"""
            query($filename: String!
                  $tournament: Int!
                  $modelId: String) {{
                {endpoint}(filename: $filename
                                       tournament: $tournament
                                       modelId: $modelId) {{
                    filename
                    url
                }}
            }}
        """
        arguments = {
            "filename": os.path.basename(file_path),
            "tournament": tournament,
            "modelId": model_id,
        }
        return self.raw_query(auth_query, arguments, authorization=True)["data"][
            endpoint
        ]

    def upload_diagnostics(
        self,
        file_path: str = "predictions.csv",
        tournament: int | None = None,
        model_id: str = "",
        df: pd.DataFrame | None = None,
    ) -> str:
        """Upload predictions to diagnostics from file.

        Args:
            file_path (str): CSV file with predictions that will get uploaded
            tournament (int): ID of the tournament (optional, defaults to None)
            model_id (str): Target model UUID (required for accounts with
                multiple models)
            df (pandas.DataFrame): pandas DataFrame to upload, if function is
                given df and file_path, df will be uploaded.

        Returns:
            str: diagnostics_id

        Example:
            >>> api = NumerAPI(secret_key="..", public_id="..")
            >>> model_id = api.get_models()['uuazed']
            >>> api.upload_diagnostics("prediction.cvs", model_id=model_id)
            '93c46857-fed9-4594-981e-82db2b358daf'
            >>> # upload from pandas DataFrame directly:
            >>> api.upload_diagnostics(df=predictions_df, model_id=model_id)
        """
        self.logger.info("uploading diagnostics...")

        # write the pandas DataFrame as a binary buffer if provided
        buffer_csv = None
        if tournament is None:
            tournament = self.tournament_id

        if df is not None:
            buffer_csv = BytesIO(df.to_csv(index=False).encode())
            buffer_csv.name = file_path

        upload_auth = self._upload_auth(
            "diagnosticsUploadAuth", file_path, tournament, model_id
        )

        with open(file_path, "rb") if df is None else buffer_csv as file:
            requests.put(upload_auth["url"], data=file.read(), timeout=600)
        create_query = """
            mutation($filename: String!
                     $tournament: Int!
                     $modelId: String) {
                createDiagnostics(filename: $filename
                                  tournament: $tournament
                                  modelId: $modelId) {
                    id
                }
            }"""
        arguments = {
            "filename": upload_auth["filename"],
            "tournament": tournament,
            "modelId": model_id,
        }
        create = self.raw_query(create_query, arguments, authorization=True)
        diagnostics_id = create["data"]["createDiagnostics"]["id"]
        return diagnostics_id

    def diagnostics(self, model_id: str, diagnostics_id: str | None = None) -> Dict:
        """Fetch results of diagnostics run

        Args:
            model_id (str): Target model UUID (required for accounts with
                multiple models)
            diagnostics_id (str, optional): id returned by "upload_diagnostics"

        Returns:
            dict: diagnostic results with the following content:

                * validationCorrMean (`float`)
                * validationCorrSharpe (`float`)
                * examplePredsCorrMean (`float`)
                * validationMmcStd (`float`)
                * validationMmcSharpe (`float`)
                * validationCorrPlusMmcSharpeDiff (`float`)
                * validationMmcStdRating (`float`)
                * validationMmcMeanRating (`float`)
                * validationCorrPlusMmcSharpeDiffRating (`float`)
                * perEraDiagnostics (`list`) each with the following fields:
                    * era (`int`)
                    * examplePredsCorr (`float`)
                    * validationAlpha (`float`)
                    * validationBmc (`float`)
                    * validationCorr (`float`)
                    * validationCorrV4 (`float`)
                    * validationFeatureCorrMax (`float`)
                    * validationFeatureNeutralCorr (`float`)
                    * validationFeatureNeutralCorrV3
                    * validationMmc (`float`)
                    * validationFncV4 (`float`)
                    * validationIcV2 (`float`)
                    * validationRic (`float`)
                    * validationBmc (`float`)
                * validationCorrPlusMmcStd (`float`)
                * validationMmcMean (`float`)
                * validationCorrStdRating (`float`)
                * validationCorrPlusMmcSharpe (`float`)
                * validationMaxDrawdownRating (`float`)
                * validationFeatureNeutralCorrMean (`float`)
                * validationCorrPlusMmcMean (`float`)
                * validationFeatureCorrMax (`float`)
                * status (`string`),
                * validationCorrMeanRating (`float`)
                * validationFeatureNeutralCorrMeanRating (`float`)
                * validationCorrSharpeRating (`float`)
                * validationCorrPlusMmcMeanRating (`float`)
                * message (`string`)
                * validationMmcSharpeRating (`float`)
                * updatedAt (`datetime`)
                * validationFeatureCorrMaxRating (`float`)
                * validationCorrPlusMmcSharpeRating (`float`)
                * trainedOnVal (`bool`)
                * validationCorrStd (`float`)
                * erasAcceptedCount (`int`)
                * validationMaxDrawdown (`float`)
                * validationCorrPlusMmcStdRating (`float`)
                * validationAdjustedSharpe (`float`)
                * validationApy (`float`)
                * validationAutocorr (`float`)
                * validationCorrCorrWExamplePreds (`float`)
                * validationCorrMaxDrawdown (`float`)
                * validationCorrV4CorrWExamplePreds (`float`)
                * validationCorrV4MaxDrawdown (`float`)
                * validationCorrV4Mean (`float`)
                * validationBmcMean (`float`)
                * validationCorrV4Sharpe (`float`)
                * validationCorrV4Std (`float`)
                * validationFeatureNeutralCorrV3Mean (`float`)
                * validationFeatureNeutralCorrV3MeanRating (`float`)
                * validationFncV4CorrWExamplePreds (`float`)
                * validationFncV4MaxDrawdown (`float`)
                * validationFncV4Mean (`float`)
                * validationFncV4Sharpe (`float`)
                * validationFncV4Std (`float`)
                * validationIcV2CorrWExamplePreds (`float`)
                * validationIcV2MaxDrawdown (`float`)
                * validationIcV2Mean (`float`)
                * validationIcV2Sharpe (`float`)
                * validationIcV2Std (`float`)
                * validationRicCorrWExamplePreds (`float`)
                * validationRicMaxDrawdown (`float`)
                * validationRicMean (`float`)
                * validationRicSharpe (`float`)
                * validationRicStd (`float`)
                * validationAlphaCorrWExamplePreds (`float`)
                * validationAlphaMaxDrawdown (`float`)
                * validationAlphaMean (`float`)
                * validationAlphaSharpe (`float`)
                * validationAlphaStd (`float`)

        Example:
            >>> napi = NumerAPI(secret_key="..", public_id="..")
            >>> model_id = napi.get_models()['uuazed']
            >>> api.upload_diagnostics("prediction.cvs", model_id=model_id)
            '93c46857-fed9-4594-981e-82db2b358daf'
            >>> napi.diagnostic(model_id)
            {"validationCorrMean": 0.53231,
            ...
            }

        """
        query = """
            query($id: String
                  $modelId: String!) {
              diagnostics(id: $id
                          modelId: $modelId) {
                erasAcceptedCount
                examplePredsCorrMean
                message
                perEraDiagnostics {
                    era
                    examplePredsCorr
                    validationAlpha
                    validationBmc
                    validationChurn
                    validationCorr
                    validationCorrV4
                    validationFeatureCorrMax
                    validationFeatureNeutralCorr
                    validationFeatureNeutralCorrV3
                    validationMmc
                    validationFncV4
                    validationIcV2
                    validationRic
                }
                status
                trainedOnVal
                updatedAt
                validationCorrMean
                validationCorrMeanRating
                validationCorrPlusMmcMean
                validationCorrPlusMmcMeanRating
                validationCorrPlusMmcSharpe
                validationCorrPlusMmcSharpeDiff
                validationCorrPlusMmcSharpeDiffRating
                validationCorrPlusMmcSharpeRating
                validationCorrPlusMmcStd
                validationCorrPlusMmcStdRating
                validationCorrSharpe
                validationCorrSharpeRating
                validationCorrStd
                validationCorrStdRating
                validationFeatureCorrMax
                validationFeatureCorrMaxRating
                validationFeatureNeutralCorrMean
                validationFeatureNeutralCorrMeanRating
                validationMaxDrawdown
                validationMaxDrawdownRating
                validationMmcMean
                validationMmcMeanRating
                validationMmcSharpe
                validationMmcSharpeRating
                validationMmcStd
                validationMmcStdRating
                validationBmcMean

                validationAdjustedSharpe
                validationApy
                validationAutocorr
                validationCorrCorrWExamplePreds
                validationCorrMaxDrawdown
                validationCorrV4CorrWExamplePreds
                validationCorrV4MaxDrawdown
                validationCorrV4Mean
                validationCorrV4Sharpe
                validationCorrV4Std
                validationFeatureNeutralCorrV3Mean
                validationFeatureNeutralCorrV3MeanRating
                validationFncV4CorrWExamplePreds
                validationFncV4MaxDrawdown
                validationFncV4Mean
                validationFncV4Sharpe
                validationFncV4Std
                validationIcV2CorrWExamplePreds
                validationIcV2MaxDrawdown
                validationIcV2Mean
                validationIcV2Sharpe
                validationIcV2Std
                validationRicCorrWExamplePreds
                validationRicMaxDrawdown
                validationRicMean
                validationRicSharpe
                validationRicStd
                validationAlphaCorrWExamplePreds
                validationAlphaMaxDrawdown
                validationAlphaMean
                validationAlphaSharpe
                validationAlphaStd
              }
            }
        """
        args = {"modelId": model_id, "id": diagnostics_id}
        results = self.raw_query(query, args, authorization=True)["data"]["diagnostics"]
        utils.replace(results, "updatedAt", utils.parse_datetime_string)
        return results

    def submission_scores(
        self,
        model_id: str,
        display_name: str | None = None,
        version: str | None = None,
        day: int | None = None,
        resolved: bool | None = None,
        last_n_rounds: int | None = None,
        distinct_on_round: bool | None = None,
    ) -> List[Dict]:
        """Fetch submission score history for a model.

        Args:
            model_id (str): target model UUID
            display_name (str, optional): score metric name filter
            version (str, optional): score version filter
            day (int, optional): day filter
            resolved (bool, optional): resolved-state filter
            tournament (int, optional): tournament filter, defaults to the
                API instance tournament
            last_n_rounds (int, optional): limit by most recent rounds
            distinct_on_round (bool, optional): keep only the latest score per
                round after applying other filters

        Returns:
            list of dicts: list of submission score entries
        """

        query = """
          query($modelId: ID!
                $displayName: String
                $version: String
                $day: Int
                $resolved: Boolean
                $tournament: Int
                $lastNRounds: Int
                $distinctOnRound: Boolean) {
            submissionScores(modelId: $modelId
                             displayName: $displayName
                             version: $version
                             day: $day
                             resolved: $resolved
                             tournament: $tournament
                             lastNRounds: $lastNRounds
                             distinctOnRound: $distinctOnRound) {
                roundId
                submissionId
                roundNumber
                roundResolveTime
                roundScoreTime
                roundCloseStakingTime
                value
                percentile
                displayName
                version
                date
                day
                resolveDate
                resolved
            }
          }
        """
        arguments = {
            "modelId": model_id,
            "displayName": display_name,
            "version": version,
            "day": day,
            "resolved": resolved,
            "tournament": self.tournament_id,
            "lastNRounds": last_n_rounds,
            "distinctOnRound": distinct_on_round,
        }
        scores = self.raw_query(query, arguments)["data"]["submissionScores"]
        for score in scores:
            utils.replace(score, "roundResolveTime", utils.parse_datetime_string)
            utils.replace(score, "roundScoreTime", utils.parse_datetime_string)
            utils.replace(score, "roundCloseStakingTime", utils.parse_datetime_string)
            utils.replace(score, "date", utils.parse_datetime_string)
            utils.replace(score, "resolveDate", utils.parse_datetime_string)
        return scores

    def pending_model_payouts(self, tournament: int | None = None) -> Dict:
        """Fetch actual and pending payouts for the authenticated user's models.

        Args:
            tournament (int, optional): tournament filter, defaults to the API
                instance tournament

        Returns:
            dict: payout groups with `actual` and `pending` lists
        """

        query = """
          query($tournament: Int!) {
            pendingModelPayouts(tournament: $tournament) {
                actual {
                    roundId
                    roundNumber
                    roundResolveTime
                    modelId
                    modelName
                    modelDisplayName
                    payoutNmr
                    payoutValue
                    currencySymbol
                }
                pending {
                    roundId
                    roundNumber
                    roundResolveTime
                    modelId
                    modelName
                    modelDisplayName
                    payoutNmr
                    payoutValue
                    currencySymbol
                }
            }
          }
        """
        arguments = {
            "tournament": self.tournament_id if tournament is None else tournament
        }
        payouts = self.raw_query(query, arguments, authorization=True)["data"][
            "pendingModelPayouts"
        ]
        for payout_type in ["actual", "pending"]:
            for payout in payouts[payout_type]:
                utils.replace(payout, "roundResolveTime", utils.parse_datetime_string)
                utils.replace(payout, "payoutNmr", utils.parse_float_string)
                utils.replace(payout, "payoutValue", utils.parse_float_string)
        return payouts

    def round_model_performances_v2(self, model_id: str):
        """Fetch round model performance of a user.

        DEPRECATED - please use `submission_scores` instead when possible.

        Args:
            model_id (str)

        Returns:
            list of dicts: list of round model performance entries

            For each entry in the list, there is a dict with the following
            content:

                * atRisk (`float`)
                * corrMultiplier (`float` or None)
                * mmcMultiplier (`float` or None)
                * roundPayoutFactor (`float` or None)
                * roundNumber (`int`)
                * roundOpenTime (`datetime`)
                * roundResolveTime (`datetime`)
                * roundResolved (`bool`)
                * roundTarget (`str`)
                * submissionScores (`dict`)
                    * date (`datetime`)
                    * day (`int`)
                    * displayName (`str`): name of the metric
                    * payoutPending (`float`)
                    * payoutSettled (`float`)
                    * percentile (`float`)
                    * value (`float`): value of the metric
        """
        warnings.warn(
            "`round_model_performances_v2` is deprecated because it relies on "
            "`v2RoundModelPerformances`. Use `submission_scores` instead when "
            "possible.",
            DeprecationWarning,
            stacklevel=2,
        )

        query = """
          query($modelId: String!
                $tournament: Int!) {
            v2RoundModelPerformances(modelId: $modelId
                                     tournament: $tournament) {
                atRisk
                corrMultiplier,
                mmcMultiplier,
                roundPayoutFactor,
                roundNumber,
                roundOpenTime,
                roundResolveTime,
                roundResolved,
                roundTarget,
                submissionScores {
                    date
                    day
                    displayName
                    payoutPending
                    payoutSettled
                    percentile
                    value
                }
            }
          }
        """
        arguments = {"modelId": model_id, "tournament": self.tournament_id}
        data = self.raw_query(query, arguments)["data"]
        performances = data["v2RoundModelPerformances"]
        for perf in performances:
            utils.replace(perf, "roundOpenTime", utils.parse_datetime_string)
            utils.replace(perf, "roundResolveTime", utils.parse_datetime_string)
            utils.replace(perf, "atRisk", utils.parse_float_string)
            if perf["submissionScores"]:
                for submission in perf["submissionScores"]:
                    utils.replace(submission, "date", utils.parse_datetime_string)
                    utils.replace(submission, "payoutPending", utils.parse_float_string)
                    utils.replace(submission, "payoutSettled", utils.parse_float_string)
        return performances

    def intra_round_scores(self, model_id: str):
        """Fetch intra-round scores for your model.

        While only the final scores are relevant for payouts, it might be
        interesting to look how your scores evolve throughout a round.

        Args:
            model_id (str)

        Returns:
            list of dicts: list of intra-round model performance entries

            For each entry in the list, there is a dict with the following
            content:

                * roundNumber (`int`)
                * intraRoundSubmissionScores (`dict`)
                    * date (`datetime`)
                    * day (`int`)
                    * displayName (`str`): name of the metric
                    * payoutPending (`float`)
                    * payoutSettled (`float`)
                    * percentile (`float`)
                    * value (`float`): value of the metric
        """

        query = """
          query($modelId: String!
                $tournament: Int!) {
            v2RoundModelPerformances(modelId: $modelId
                                     tournament: $tournament) {
                roundNumber,
                intraRoundSubmissionScores {
                    date,
                    day,
                    displayName,
                    payoutPending,
                    payoutSettled,
                    percentile,
                    value
                }
            }
          }
        """
        arguments = {"modelId": model_id, "tournament": self.tournament_id}
        data = self.raw_query(query, arguments)["data"]
        performances = data["v2RoundModelPerformances"]
        for perf in performances:
            if perf["intraRoundSubmissionScores"]:
                for score in perf["intraRoundSubmissionScores"]:
                    utils.replace(score, "date", utils.parse_datetime_string)
                    fun = utils.parse_float_string
                    utils.replace(score, "payoutPending", fun)
                    utils.replace(score, "payoutSettled", fun)
        return performances

    def round_model_performances(self, username: str) -> List[Dict]:
        """Fetch round model performance of a user.

        DEPRECATED - please use `round_model_performances_v2` instead
        """
        self.logger.warning("Deprecated. Checkout round_model_performances_v2.")
        return self.round_model_performances_v2(username)

    def stake_change(
        self, nmr: float | str, action: str = "decrease", model_id: str = ""
    ) -> Dict:
        """Change stake by `value` NMR.

        Args:
            nmr (float or str): amount of NMR you want to increase/decrease
            action (str): `increase` or `decrease`
            model_id (str): Target model UUID (required for accounts with
                multiple models)

        Returns:
            dict: stake information with the following content:

              * dueDate (`datetime`)
              * status (`str`)
              * requestedAmount (`decimal.Decimal`)
              * type (`str`)

        Example:
            >>> api = NumerAPI(secret_key="..", public_id="..")
            >>> model = api.get_models()['uuazed']
            >>> api.stake_change(10, "decrease", model)
            {'dueDate': None,
             'requestedAmount': decimal.Decimal('10'),
             'type': 'decrease',
             'status': ''}
        """
        query = """
          mutation($value: String!
                   $type: String!
                   $tournamentNumber: Int!
                   $modelId: String) {
              v2ChangeStake(value: $value
                            type: $type
                            modelId: $modelId
                            tournamentNumber: $tournamentNumber) {
                dueDate
                requestedAmount
                status
                type
              }
        }
        """
        arguments = {
            "value": str(nmr),
            "type": action,
            "modelId": model_id,
            "tournamentNumber": self.tournament_id,
        }
        result = self.raw_query(query, arguments, authorization=True)
        stake = result["data"]["v2ChangeStake"]
        utils.replace(stake, "requestedAmount", utils.parse_float_string)
        utils.replace(stake, "dueDate", utils.parse_datetime_string)
        return stake

    def stake_drain(self, model_id: str | None = None) -> Dict:
        """Completely remove your stake.

        Args:
            model_id (str): Target model UUID

        Returns:
            dict: stake information with the following content:

              * dueDate (`datetime`)
              * status (`str`)
              * requestedAmount (`decimal.Decimal`)
              * type (`str`)
              * drain (`bool`)

        Example:
            >>> api = NumerAPI(secret_key="..", public_id="..")
            >>> model_id = api.get_models()['uuazed']
            >>> api.stake_drain(model_id)
            {'dueDate': None,
             'requestedAmount': decimal.Decimal('11000000'),
             'type': 'decrease',
             'status': '',
             'drain": True}
        """
        query = """
            mutation($drain: bool!
                     $amount: String
                     $modelId: String) {
                releaseStake(drain: $drain
                             modelId: $modelId
                             amount: $amount) {
                    id
                    dueDate
                    status
                    type
                    requestedAmount
                    drain
                }
            }"""
        arguments = {"drain": True, "modelId": model_id, "amount": "11000000"}
        raw = self.raw_query(query, arguments, authorization=True)
        return raw["data"]["releaseStake"]

    def stake_decrease(self, nmr: float | str, model_id: str) -> Dict:
        """Decrease your stake by `value` NMR.

        Args:
            nmr (float or str): amount of NMR you want to reduce
            model_id (str): Target model UUID (required for accounts with
                multiple models)
            tournament (int): ID of the tournament (optional, defaults to 8)

        Returns:
            dict: stake information with the following content:

              * dueDate (`datetime`)
              * status (`str`)
              * requestedAmount (`decimal.Decimal`)
              * type (`str`)

        Example:
            >>> api = NumerAPI(secret_key="..", public_id="..")
            >>> model = api.get_models()['uuazed']
            >>> api.stake_decrease(10, model)
            {'dueDate': None,
             'requestedAmount': decimal.Decimal('10'),
             'type': 'decrease',
             'status': ''}
        """
        return self.stake_change(nmr, "decrease", model_id)

    def stake_increase(self, nmr: float | str, model_id: str) -> Dict:
        """Increase your stake by `value` NMR.

        Args:
            nmr (float or str): amount of additional NMR you want to stake
            model_id (str): Target model UUID (required for accounts with
                multiple models)
            tournament (int): ID of the tournament (optional, defaults to 8)

        Returns:
            dict: stake information with the following content:

              * dueDate (`datetime`)
              * status (`str`)
              * requestedAmount (`decimal.Decimal`)
              * type (`str`)

        Example:
            >>> api = NumerAPI(secret_key="..", public_id="..")
            >>> model = api.get_models()['uuazed']
            >>> api.stake_increase(10, model)
            {'dueDate': None,
             'requestedAmount': decimal.Decimal('10'),
             'type': 'increase',
             'status': ''}
        """
        return self.stake_change(nmr, "increase", model_id)

    def check_round_open(self) -> bool:
        """Check if a round is currently open.

        Returns:
            bool: True if a round is currently open for submissions, False otherwise.

        Example:
            >>> NumerAPI().check_round_open()
            False
        """
        query = """
            query($tournament: Int!) {
              rounds(tournament: $tournament
              number: 0) {
                number
                openTime
                closeStakingTime
              }
            }
        """
        arguments = {"tournament": self.tournament_id}
        # in some period in between rounds, "number: 0" returns Value error -
        # "Current round not open for submissions", because there is no active
        # round. This is caught by the try / except.
        try:
            raw = self.raw_query(query, arguments)["data"]["rounds"][0]
        except ValueError:
            return False
        if raw is None:
            return False
        open_time = utils.parse_datetime_string(raw["openTime"])
        deadline = utils.parse_datetime_string(raw["closeStakingTime"])
        now = datetime.datetime.now(tz=pytz.utc)
        is_open = open_time < now < deadline
        return is_open

    def check_new_round(self, hours: int = 12) -> bool:
        """Check if a new round has started within the last `hours`.

        Args:
            hours (int, optional): timeframe to consider, defaults to 12

        Returns:
            bool: True if a new round has started, False otherwise.

        Example:
            >>> NumerAPI().check_new_round()
            False
        """
        query = """
            query($tournament: Int!) {
              rounds(tournament: $tournament
                     number: 0) {
                number
                openTime
              }
            }
        """
        arguments = {"tournament": self.tournament_id}
        # in some period in between rounds, "number: 0" returns Value error -
        # "Current round not open for submissions", because there is no active
        # round. This is caught by the try / except.
        try:
            raw = self.raw_query(query, arguments)["data"]["rounds"][0]
        except ValueError:
            return False
        if raw is None:
            return False
        open_time = utils.parse_datetime_string(raw["openTime"])
        now = datetime.datetime.now(tz=pytz.utc)
        is_new_round = open_time > now - datetime.timedelta(hours=hours)
        return is_new_round

    def get_account_leaderboard(self, limit: int = 50, offset: int = 0) -> List[Dict]:
        """Get the current account leaderboard

        Args:
            limit (int): number of items to return (optional, defaults to 50)
            offset (int): number of items to skip (optional, defaults to 0)

        Returns:
            list of dicts: list of leaderboard entries

            Each dict contains the following items:

                * username (`str`)
                * displayName (`str`)
                * rank (`int`)
                * nmrStaked (`decimal.Decimal`)
                * v2Corr20 (`float`)
                * cort20 (`float`)
                * corrV4 (`float`)
                * fncV4 (`float`)
                * icV2 (`float`)
                * mmc (`float`)
                * ric (`float`)
                * return1y (`float`)
                * return3m (`float`)
                * returnAllTime (`float`)
                * return1yNmr (`decimal.Decimal`)
                * return3mNmr (`decimal.Decimal`)
                * returnAllTimeNmr (`decimal.Decimal`)

        Example:
            >>> numerapi.NumerAPI().get_account_leaderboard()
            [{'username': 'leonidas',
              'rank': 1,
              'nmrStaked': Decimal('3034.00'),
              ...
              }]
        """
        query = """
            query($limit: Int!
                  $offset: Int!
                  $tournament: Int) {
              accountLeaderboard(limit: $limit
                                 offset: $offset
                                 tournament: $tournament) {
                displayName
                nmrStaked
                rank
                username
                v2Corr20
                cort20
                corJ60
                corrV4
                fncV4
                icV2
                mmc
                ric
                return1y
                return3m
                returnAllTime
                return1yNmr
                return3mNmr
                returnAllTimeNmr
              }
            }
        """
        args = {"limit": limit, "offset": offset, "tournament": self.tournament_id}
        data = self.raw_query(query, args)["data"]["accountLeaderboard"]
        for item in data:
            utils.replace(item, "nmrStaked", utils.parse_float_string)
            utils.replace(item, "return1yNmr", utils.parse_float_string)
            utils.replace(item, "return3mNmr", utils.parse_float_string)
            utils.replace(item, "returnAllTimeNmr", utils.parse_float_string)
        return data

    def modelid_to_modelname(self, model_id: str) -> str:
        """Get model name from a model_id.

        Args:
            model_id (str)

        Returns:
            str: modelname
        """
        query = """
            query($modelid: String!) {
                model(modelId: $modelid) {
                    name
                }
            }
        """
        arguments = {"modelid": model_id}
        res = self.raw_query(query, arguments, authorization=True)
        return res["data"]["model"]["name"]

    def pipeline_status(self, date: str | None = None) -> Dict:
        """Get status of Numerai's scoring pipeline

        Args:
            date (str, optional): date in YYYY-MM-DD format. Defaults to today.

        Returns:
            dict: pipeline status information including the following fields:
                * dataReadyAt (`str`)
                * isScoringDay (`bool`)
                * resolvedAt (`datetime`)
                * scoredAt (`datetime`)
                * startedAt (`datetime`)
                * tournament (`str`)

        Example:
            >>> napi = NumerAPI()
            >>> napi.pipeline_status()
        """
        if date is None:
            date = datetime.date.today().isoformat()
        tournament = "classic" if self.tournament_id == 8 else "signals"
        query = """
            query($tournament: String! $date: String) {
                pipelineStatus(date: $date, tournament: $tournament) {
                    dataReadyAt
                    isScoringDay
                    resolvedAt
                    scoredAt
                    startedAt
                    tournament
                }
            }
        """
        arguments = {"tournament": tournament, "date": date}
        res = self.raw_query(query, arguments)["data"]["pipelineStatus"]
        for field in res.keys():
            if field.endswith("At"):
                utils.replace(res, field, utils.parse_datetime_string)
        return res

    def model_upload(
        self,
        file_path: str,
        tournament: int | None = None,
        model_id: str | None = None,
        data_version: str | None = None,
        docker_image: str | None = None,
    ) -> str:
        """Upload pickled model to numerai.

        Args:
            file_path (str): pickle file, needs to endwith .pkl
            tournament (int): ID of the tournament (optional)
            model_id (str): Target model UUID
            data_version (str, optional): which data version to use. ID or name.
                    Check available options with 'model_upload_data_versions'
            docker_image (str, optional): which docker image to use. ID or name.
                    Check available options with 'model_upload_docker_images'

        Returns:
            str: model_upload_id

        Example:
            >>> api = NumerAPI(secret_key="..", public_id="..")
            >>> model_id = api.get_models()['uuazed']
            >>> api.model_upload("example.pkl", model_id=model_id)
            '93c46857-fed9-4594-981e-82db2b358daf'
        """
        if data_version is not None:
            if not utils.is_valid_uuid(data_version):
                data_versions = self.model_upload_data_versions()
                if data_version not in data_versions:
                    msg = "'data_version' needs to be one of"
                    msg += f"{list(data_versions.keys())}"
                    raise ValueError(msg)
                data_version = data_versions[data_version]
        if docker_image is not None:
            if not utils.is_valid_uuid(docker_image):
                docker_images = self.model_upload_docker_images()
                if docker_image not in docker_images:
                    msg = "'docker_image' needs to be one of"
                    msg += f"{list(docker_images.keys())}"
                    raise ValueError(msg)
                docker_image = docker_images[docker_image]

        auth_query = """
            query($filename: String! $modelId: String) {
                computePickleUploadAuth(filename: $filename
                                        modelId: $modelId) {
                    filename
                    url
                }
            }
        """
        arguments = {"filename": os.path.basename(file_path), "modelId": model_id}
        upload_auth = self.raw_query(auth_query, arguments, authorization=True)["data"][
            "computePickleUploadAuth"
        ]

        with open(file_path, "rb") as file:
            requests.put(upload_auth["url"], data=file.read(), timeout=600)
        create_query = """
            mutation($filename: String!
                     $tournament: Int!
                     $modelId: String
                     $dataVersionId: String
                     $dockerImageId: String) {
                createComputePickleUpload(filename: $filename
                                          tournament: $tournament
                                          modelId: $modelId
                                          dataVersionId: $dataVersionId
                                          dockerImageId: $dockerImageId) {
                    id
                }
            }"""
        tournament = self.tournament_id if tournament is None else tournament
        arguments = {
            "filename": upload_auth["filename"],
            "tournament": tournament,
            "modelId": model_id,
            "dataVersionId": data_version,
            "dockerImageId": docker_image,
        }
        create = self.raw_query(create_query, arguments, authorization=True)
        return create["data"]["createComputePickleUpload"]["id"]

    def model_upload_data_versions(self) -> Dict:
        """Get available data version for model uploads

        Returns:
            dict[str, str]: name to ID mapping

        Example:
            >>> api = NumerAPI(secret_key="..", public_id="..")
            >>> api.model_upload_data_versions()
            {'v4.1': 'a76bafa1-b25a-4f22-9add-65b528a0f3d0'}

        """
        query = """
            query {
                computePickleDataVersions {
                    name
                    id
                }
            }
        """
        data = self.raw_query(query, authorization=True)["data"]
        res = {item["name"]: item["id"] for item in data["computePickleDataVersions"]}
        return res

    def model_upload_docker_images(self) -> Dict:
        """Get available docker images for model uploads

        Returns:
            dict[str, str]: name to ID mapping

        Example:
            >>> api = NumerAPI(secret_key="..", public_id="..")
            >>> api.model_upload_docker_images()
            {'Python 3.10': 'c72ae05e-2831-4c50-b20f-c2fe01c206ef',
             'Python 3.9': '5a32b827-cd9a-40a9-a99d-e58401120a0b',
               ...
            }
        """
        query = """
            query {
                computePickleDockerImages {
                    name
                    id
                }
            }
        """
        data = self.raw_query(query, authorization=True)["data"]
        res = {item["name"]: item["id"] for item in data["computePickleDockerImages"]}
        return res

    def submission_ids(self, model_id: str):
        """Get all submission ids from a model

        Args:
            model_id (str)

        Returns:
            list of dicts: list of submissions

            For each entry in the list, there is a dict with the following
            content:

                * insertedAt (`datetime`)
                * filename (`str`)
                * id (`str`)

         Example:
            >>> api = NumerAPI(secret_key="..", public_id="..")
            >>> model_id = napi.get_models()["uuazed"]
            >>> api.submission_ids(model_id)
        """
        query = """
            query($modelId: String) {
                submissions(modelId: $modelId) {
                    id
                    filename
                    insertedAt
                }
            }
        """
        raw = self.raw_query(query, {"modelId": model_id}, authorization=True)
        data = raw["data"]["submissions"]
        utils.replace(data, "insertedAt", utils.parse_datetime_string)
        return data

    def download_submission(
        self, submission_id: str | None = None, model_id: str = "", dest_path: str = ""
    ) -> str:
        """Download previous submissions from numerai

        Args:
            submission_id (str, optional): the submission to be downloaded
            model_id (str, optional): if provided, the latest submission of that
                                      model gets downloaded
            dest_path (str, optional): where to save the downloaded file

        Returns:
            str: path to downloaded file

        Example:
            >>> # fetch latest submission
            >>> api = NumerAPI(secret_key="..", public_id="..")
            >>> model_id = api.get_models()["uuazed"]
            >>> api.download_submission(model_id=model_id)
            >>> # fetch older submssion
            >>> ids = api.submission_ids(model_id)
            >>> import random; submission_id = random.choice(ids)["id"]
            >>> api.download_submission(submission_id=submission_id)
        """
        msg = "You need to provide one of `model_id` and `submission_id"
        assert model_id != "" or submission_id != "", msg
        auth_query = """
            query($id: String) {
                submissionDownloadAuth(id: $id) {
                    filename
                    url
                }
            }"""
        if not submission_id:
            ids = self.submission_ids(model_id)
            submission_id = max(ids, key=lambda x: x["insertedAt"])["id"]

        data = self.raw_query(auth_query, {"id": submission_id}, authorization=True)[
            "data"
        ]["submissionDownloadAuth"]
        if dest_path == "":
            dest_path = data["filename"]
        path = utils.download_file(data["url"], dest_path)
        return path

    def upload_predictions(
        self,
        file_path: str = "predictions.csv",
        model_id: str | None = None,
        df: pd.DataFrame | None = None,
        data_datestamp: int | None = None,
        timeout: Union[None, float, Tuple[float, float]] = (10, 600),
    ) -> str:
        """Upload predictions from file.
        Will read TRIGGER_ID from the environment if this model is enabled with
        a Numerai Compute cluster setup by Numerai CLI.

        Args:
            file_path (str): CSV file with predictions that will get uploaded
            model_id (str): Target model UUID (required for accounts with
                multiple models)
            df (pandas.DataFrame): pandas DataFrame to upload, if function is
                given df and file_path, df will be uploaded.
            data_datestamp (int): Data lag, in case submission is done using
                data from the previous day(s).
            timeout (float|tuple(float,float)): waiting time (connection timeout,
                read timeout)

        Returns:
            str: submission_id

        Example:
            >>> api = NumerAPI(secret_key="..", public_id="..")
            >>> model_id = api.get_models()['uuazed']
            >>> api.upload_predictions("prediction.cvs", model_id=model_id)
            '93c46857-fed9-4594-981e-82db2b358daf'
            >>> # upload from pandas DataFrame directly:
            >>> api.upload_predictions(df=predictions_df, model_id=model_id)
        """
        self.logger.info("uploading predictions...")

        # write the pandas DataFrame as a binary buffer if provided
        buffer_csv = None

        if df is not None:
            buffer_csv = BytesIO(df.to_csv(index=False).encode())
            buffer_csv.name = file_path

        upload_auth = self._upload_auth(
            "submission_upload_auth", file_path, self.tournament_id, model_id
        )

        # get compute id if available and pass it along
        headers = {"x_compute_id": os.getenv("NUMERAI_COMPUTE_ID")}
        with open(file_path, "rb") if df is None else buffer_csv as file:
            requests.put(
                upload_auth["url"], data=file.read(), headers=headers, timeout=timeout
            )
        create_query = """
            mutation($filename: String!
                     $tournament: Int!
                     $modelId: String
                     $triggerId: String,
                     $dataDatestamp: Int) {
                create_submission(filename: $filename
                                  tournament: $tournament
                                  modelId: $modelId
                                  triggerId: $triggerId
                                  source: "numerapi"
                                  dataDatestamp: $dataDatestamp) {
                    id
                }
            }
            """
        arguments = {
            "filename": upload_auth["filename"],
            "tournament": self.tournament_id,
            "modelId": model_id,
            "triggerId": os.getenv("TRIGGER_ID", None),
            "dataDatestamp": data_datestamp,
        }
        create = self.raw_query(create_query, arguments, authorization=True)
        submission_id = create["data"]["create_submission"]["id"]
        return submission_id
