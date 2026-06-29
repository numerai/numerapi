"""API for Numerai Signals"""

from typing import List, Dict, Tuple, Union
import os
import decimal
from io import BytesIO

import requests
import pandas as pd

from numerapi import base_api
from numerapi import utils


class SignalsAPI(base_api.Api):
    """"API for Numerai Signals"""

    def __init__(self, *args, **kwargs):
        base_api.Api.__init__(self, *args, **kwargs)
        self.tournament_id = 11

    def get_leaderboard(self, limit: int = 50, offset: int = 0) -> List[Dict]:
        """Get the current Numerai Signals leaderboard
        Args:
            limit (int): number of items to return (optional, defaults to 50)
            offset (int): number of items to skip (optional, defaults to 0)
        Returns:
            list of dicts: list of leaderboard entries
            Each dict contains the following items:
                * username (`str`)
                * sharpe (`float`)
                * rank (`int`)
                * prevRank (`int`)
                * today (`float`)
                * mmc (`float`)
                * mmcRank (`int`)
                * icRep (`float`)
                * icRank (`int`)
                * tcRep (`float`)
                * tcRank (`int`)
                * nmrStaked (`float`)
        Example:
            >>> numerapi.SignalsAPI().get_leaderboard(1)
            [{'prevRank': 1,
              'rank': 1,
              'sharpe': 2.3,
              'today': 0.01321,
              'username': 'floury_kerril_moodle',
              'mmc': -0.0101202715,
              'mmcRank': 30,
              'nmrStaked': 13.0,
              'icRep': -0.0101202715,
              'icRank': 30,
              ..
             }]
        """
        query = '''
            query($limit: Int!
                  $offset: Int!) {
              signalsLeaderboard(limit: $limit
                            offset: $offset) {
                prevRank
                rank
                sharpe
                today
                username
                mmc
                mmcRank
                nmrStaked
                icRank
                icRep
                tcRep
                tcRank
              }
            }
        '''

        arguments = {'limit': limit, 'offset': offset}
        data = self.raw_query(query, arguments)['data']['signalsLeaderboard']
        return data

    def upload_predictions(self, file_path: str = "predictions.csv",
                           model_id: str | None = None,
                           df: pd.DataFrame | None = None,
                           data_datestamp: int | None = None,
                           timeout: Union[None, float, Tuple[float, float]] = (10, 600)
    ) -> str:
        """Upload predictions from file.
        Will read TRIGGER_ID from the environment if this model is enabled with
        a Numerai Compute cluster setup by Numerai CLI.

        Args:
            file_path (str): CSV file with predictions that will get uploaded
            model_id (str): Target model UUID (required for accounts
                            with multiple models)
            df (pandas.DataFrame): Pandas DataFrame to upload, if function is
                given df and file_path, df will be uploaded
            timeout (float|tuple(float,float)): waiting time (connection timeout,
                read timeout)

        Returns:
            str: submission_id

        Example:
            >>> api = SignalsAPI(secret_key="..", public_id="..")
            >>> model_id = api.get_models()['uuazed']
            >>> api.upload_predictions("prediction.cvs", model_id=model_id)
            '93c46857-fed9-4594-981e-82db2b358daf'

            >>> # upload directly from a pandas DataFrame:
            >>> api.upload_predictions(df = predictions_df, model_id=model_id)
        """
        self.logger.info("uploading predictions...")

        # write the pandas DataFrame as a binary buffer if provided
        buffer_csv = None

        if df is not None:
            buffer_csv = BytesIO(df.to_csv(index=False).encode())
            buffer_csv.name = file_path

        upload_auth = self._upload_auth(
            'submissionUploadSignalsAuth', file_path,
            self.tournament_id, model_id)

        # get compute id if available and pass it along
        headers = {"x_compute_id": os.getenv("NUMERAI_COMPUTE_ID")}

        with open(file_path, 'rb') if df is None else buffer_csv as file:
            requests.put(upload_auth['url'], data=file.read(),
                         headers=headers, timeout=timeout)
        create_query = '''
            mutation($filename: String!
                     $modelId: String
                     $triggerId: String
                     $dataDatestamp: Int) {
                createSignalsSubmission(filename: $filename
                                        modelId: $modelId
                                        triggerId: $triggerId
                                        source: "numerapi"
                                        dataDatestamp: $dataDatestamp) {
                    id
                    firstEffectiveDate
                }
            }
            '''
        arguments = {'filename': upload_auth['filename'],
                     'modelId': model_id,
                     'triggerId': os.getenv('TRIGGER_ID', None),
                     'dataDatestamp': data_datestamp}
        create = self.raw_query(create_query, arguments, authorization=True)
        return create['data']['createSignalsSubmission']['id']

    def public_user_profile(self, username: str) -> Dict:
        """Fetch the public Numerai Signals profile of a user.

        Args:
            username (str)

        Returns:
            dict: user profile including the following fields:

                * username (`str`)
                * startDate (`datetime`)
                * id (`string`)
                * bio (`str`)
                * nmrStaked (`decimal.Decimal`)

        Example:
            >>> api = SignalsAPI()
            >>> api.public_user_profile("floury_kerril_moodle")
            {'bio': None,
             'id': '635db2a4-bdc6-4e5d-b515-f5120392c8c9',
             'startDate': datetime.datetime(2019, 3, 26, 0, 43),
             'username': 'floury_kerril_moodle',
             'nmrStaked': Decimal('14.630994874320760131')}

        """
        query = """
          query($username: String!) {
            v2SignalsProfile(modelName: $username) {
              id
              startDate
              username
              bio
              nmrStaked
            }
          }
        """
        arguments = {'username': username}
        data = self.raw_query(query, arguments)['data']['v2SignalsProfile']
        # convert strings to python objects
        utils.replace(data, "startDate", utils.parse_datetime_string)
        utils.replace(data, "nmrStaked", utils.parse_float_string)
        return data

    def daily_model_performances(self, username: str) -> List[Dict]:
        """Fetch daily Numerai Signals performance of a model.

        Args:
            username (str)

        Returns:
            list of dicts: list of daily user performance entries

            For each entry in the list, there is a dict with the following
            content:

                * date (`datetime`)
                * corrRank (`int`)
                * corrRep (`float` or None)
                * mmcRank (`int`)
                * mmcRep (`float` or None)
                * icRank (`int`)
                * icRep (`float` or None)
                * tcRank (`int`)
                * tcRep (`float` or None)
                * corr20dRank (`int`)
                * corr20dRep (`float` or None)
                * corr60Rank (`int`)
                * corr60Rep (`float` or None)
                * mmc20dRank (`int`)
                * mmc20dRep (`float` or None)

        Example:
            >>> api = SignalsAPI()
            >>> api.daily_model_performances("floury_kerril_moodle")
            [{'corrRank': 45,
              'corrRep': -0.00010935616731632354,
              'corr20dRank': None,
              'corr20dRep': None,
              'mmc20dRank': None,
              'mmc20dRep': None,
              'date': datetime.datetime(2020, 9, 18, 0, 0, tzinfo=tzutc()),
              'mmcRank': 6,
              'mmcRep': 0.0,
              'icRank': 6,
              'icRep': 0.0,
              ...},
              ...
              ]
        """
        query = """
          query($username: String!) {
            v2SignalsProfile(modelName: $username) {
              dailyModelPerformances {
                date
                corrRank
                corrRep
                mmcRep
                mmcRank
                corr20dRep
                corr20dRank
                corr60Rep
                corr60Rank
                icRep
                icRank
                tcRank
                tcRep
                mmc20dRep
                mmc20dRank
              }
            }
          }
        """
        arguments = {'username': username}
        data = self.raw_query(query, arguments)['data']['v2SignalsProfile']
        performances = data['dailyModelPerformances']
        # convert strings to python objects
        for perf in performances:
            utils.replace(perf, "date", utils.parse_datetime_string)
        return performances

    def ticker_universe(self) -> List[str]:
        """fetch universe of accepted tickers

        Returns:
            list of strings: list of currently accepted tickers

        Example:
            >>> SignalsAPI().ticker_universe()
            ["MSFT", "AMZN", "APPL", ...]
        """
        path = self.download_dataset("signals/v1.0/live.parquet")
        return pd.read_parquet(path).numerai_ticker.tolist()

    def stake_get(self, username) -> decimal.Decimal | None:
        """get current stake for a given user

        Args:
            username (str)

        Returns:
            decimal.Decimal or None: current stake, or None if the model has
                no stake

        Example:
            >>> SignalsAPI().stake_get("uuazed")
            Decimal('14.63')
        """
        query = """
          query($model_name: String!
                $tournament: Int) {
            v3UserProfile(model_name: $model_name
                          tournament: $tournament) {
              stakeValue
            }
          }
        """
        arguments = {'model_name': username, 'tournament': self.tournament_id}
        data = self.raw_query(query, arguments)['data']['v3UserProfile']
        return utils.parse_float_string(data['stakeValue'])
