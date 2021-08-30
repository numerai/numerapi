# System
from typing import List, Dict
import os
import codecs
import decimal
from io import BytesIO

# Third Party
import requests
import pandas as pd

from numerapi import base_api
from numerapi import utils

SIGNALS_DOM = "https://numerai-signals-public-data.s3-us-west-2.amazonaws.com"


class SignalsAPI(base_api.Api):
    TICKER_UNIVERSE_URL = f"{SIGNALS_DOM}/latest_universe.csv"
    HISTORICAL_DATA_URL = f"{SIGNALS_DOM}/signals_train_val_bbg.csv"

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
              }
            }
        '''

        arguments = {'limit': limit, 'offset': offset}
        data = self.raw_query(query, arguments)['data']['signalsLeaderboard']
        return data

    def upload_predictions(self, file_path: str = "predictions.csv",
                           model_id: str = None,
                           df: pd.DataFrame = None) -> str:
        """Upload predictions from file.
        Will read TRIGGER_ID from the environment if this model is enabled with
        a Numerai Compute cluster setup by Numerai CLI.

        Args:
            file_path (str): CSV file with predictions that will get uploaded
            model_id (str): Target model UUID (required for accounts
                            with multiple models)
            df (pandas.DataFrame): Pandas DataFrame to upload, if function is
                given df and file_path, df will be uploaded

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

        auth_query = '''
            query($filename: String!
                  $modelId: String) {
              submissionUploadSignalsAuth(filename: $filename
                                        modelId: $modelId) {
                    filename
                    url
                }
            }
            '''

        arguments = {'filename': os.path.basename(file_path),
                     'modelId': model_id}
        submission_resp = self.raw_query(auth_query, arguments,
                                         authorization=True)
        auth = submission_resp['data']['submissionUploadSignalsAuth']

        # get compute id if available and pass it along
        headers = {"x_compute_id": os.getenv("NUMERAI_COMPUTE_ID")}

        with open(file_path, 'rb') if df is None else buffer_csv as fh:
            requests.put(auth['url'], data=fh.read(), headers=headers)
        create_query = '''
            mutation($filename: String!
                     $modelId: String
                     $triggerId: String) {
                createSignalsSubmission(filename: $filename
                                        modelId: $modelId
                                        triggerId: $triggerId) {
                    id
                    firstEffectiveDate
                }
            }
            '''
        arguments = {'filename': auth['filename'],
                     'modelId': model_id,
                     'triggerId': os.getenv('TRIGGER_ID', None)}
        create = self.raw_query(create_query, arguments, authorization=True)
        return create['data']['createSignalsSubmission']['id']

    def submission_status(self, model_id: str = None) -> Dict:
        """submission status of the last submission associated with the account

        Args:
            model_id (str)

        Returns:
            dict: submission status with the following content:

                * firstEffectiveDate (`datetime.datetime`):
                * userId (`string`)
                * filename (`string`)
                * id (`string`)
                * submissionIp (`string`)
                * submittedCount (`int`)
                * filteredCount (`int`)
                * invalidTickers (`string`)
                * hasHistoric (`bool`)
                * historicMean (`float`)
                * historicStd (`float`)
                * historicSharpe (`float`)
                * historicMaxDrawdown (`float`)

        Example:
            >>> api = SignalsAPI(secret_key="..", public_id="..")
            >>> model_id = api.get_models()['uuazed']
            >>> api.submission_status(model_id)
            {'firstEffectiveDate': datetime.datetime(2020, 5, 12, 1, 23),
             'userId': "slyfox",
             'filename': 'model57-HPzOyr56TPaD.csv',
             'id': '1234'
             'submissionIp': "102.142.12.12",
             'submittedCount': 112,
             'filteredCount': 12,
             'invalidTickers': 'AAAPL,GOOOG',
             'hasHistoric': true,
             'historicMean': 1.23,
             'historicStd': 2.34,
             'historicSharpe': 3.45,
             'historicMaxDrawdown': 4.56}
        """

        query = '''
            query($modelId: String) {
                model(modelId: $modelId) {
                  latestSignalsSubmission {
                    id
                    filename
                    firstEffectiveDate
                    userId
                    submissionIp
                    submittedCount
                    filteredCount
                    invalidTickers
                    hasHistoric
                    historicMean
                    historicStd
                    historicSharpe
                    historicMaxDrawdown
                  }
                }
              }
            '''
        arguments = {'modelId': model_id}
        data = self.raw_query(query, arguments, authorization=True)
        status = data['data']['model']['latestSignalsSubmission']
        return status

    def public_user_profile(self, username: str) -> Dict:
        """Fetch the public Numerai Signals profile of a user.

        Args:
            username (str)

        Returns:
            dict: user profile including the following fields:

                * username (`str`)
                * startDate (`datetime`)
                * id (`string`)
                * rank (`int`)
                * bio (`str`)
                * sharpe (`float`)
                * totalStake (`decimal.Decimal`)

        Example:
            >>> api = SignalsAPI()
            >>> api.public_user_profile("floury_kerril_moodle")
            {'bio': None,
             'id': '635db2a4-bdc6-4e5d-b515-f5120392c8c9',
             'rank': 1,
             'sharpe': 2.35,
             'startDate': datetime.datetime(2019, 3, 26, 0, 43),
             'username': 'floury_kerril_moodle',
             'totalStake': Decimal('14.630994874320760131')}

        """
        query = """
          query($username: String!) {
            signalsUserProfile(username: $username) {
              rank
              id
              startDate
              username
              bio
              sharpe
              totalStake
            }
          }
        """
        arguments = {'username': username}
        data = self.raw_query(query, arguments)['data']['signalsUserProfile']
        # convert strings to python objects
        utils.replace(data, "startDate", utils.parse_datetime_string)
        utils.replace(data, "totalStake", utils.parse_float_string)
        return data

    def daily_user_performances(self, username: str) -> List[Dict]:
        """Fetch daily Numerai Signals performance of a user.

        Args:
            username (str)

        Returns:
            list of dicts: list of daily user performance entries

            For each entry in the list, there is a dict with the following
            content:

                * rank (`int`)
                * date (`datetime`)
                * sharpe (`float`)
                * mmcRep (`float`)
                * reputation (`float`)

        Example:
            >>> api = SignalsAPI()
            >>> api.daily_user_performances("floury_kerril_moodle")
            [{'date': datetime.datetime(2020, 5, 16, 0, 0,
              'rank': 1,
              'sharpe': 2.35,
              'mmcRep': 0.35,
              'reputation': 1.35
              },
             ...]
        """
        query = """
          query($username: String!) {
            signalsUserProfile(username: $username) {
              dailyUserPerformances {
                rank
                corr20dRank
                date
                sharpe
                mmcRep
                mmc20dRep
                reputation
                corr20dRep
              }
            }
          }
        """
        arguments = {'username': username}
        data = self.raw_query(query, arguments)['data']['signalsUserProfile']
        performances = data['dailyUserPerformances']
        # convert strings to python objects
        for perf in performances:
            utils.replace(perf, "date", utils.parse_datetime_string)
        return performances

    def daily_submissions_performances(self, username: str) -> List[Dict]:
        """Fetch daily Numerai Signals performance of a user's submissions.

        Args:
            username (str)

        Returns:
            list of dicts: list of daily submission performance entries

            For each entry in the list, there is a dict with the following
            content:

                * date (`datetime`)
                * returns (`float`)
                * submission_time (`datetime`)
                * correlation (`float`)
                * mmc (`float`)
                * roundNumber (`int`)
                * corrRep (`float`)
                * mmcRep (`float`)


        Example:
            >>> api = SignalsAPI()
            >>> api.daily_submissions_performances("uuazed")
            [{'date': datetime.datetime(2020, 5, 16, 0, 0),
              'returns': 1.256,
              'submissionTime': datetime.datetime(2020, 5, 12, 1, 23)},
              'corrRep': None,
              'mmc': None,
              'mmcRep': None,
              'roundNumber': 226,
              'correlation': 0.03}
             ...
              ]
        """
        query = """
          query($username: String!) {
            signalsUserProfile(username: $username) {
              dailySubmissionPerformances {
                date
                returns
                submissionTime
                correlation
                mmc
                roundNumber
                corrRep
                mmcRep
              }
            }
          }
        """
        arguments = {'username': username}
        data = self.raw_query(query, arguments)['data']['signalsUserProfile']
        performances = data['dailySubmissionPerformances']
        # convert strings to python objects
        for perf in performances:
            utils.replace(perf, "date", utils.parse_datetime_string)
            utils.replace(perf, "submissionTime", utils.parse_datetime_string)
        return performances

    def ticker_universe(self) -> List[str]:
        """fetch universe of accepted tickers

        Returns:
            list of strings: list of currently accepted tickers

        Example:
            >>> SignalsAPI().ticker_universe()
            ["MSFT", "AMZN", "APPL", ...]
        """
        result = requests.get(self.TICKER_UNIVERSE_URL, stream=True)
        iterator = codecs.iterdecode(result.iter_lines(), 'utf-8')
        tickers = [t.strip() for t in iterator if t != 'bloomberg_ticker']
        return tickers

    def download_validation_data(self, dest_path: str = ".",
                                 dest_filename: str = None) -> str:
        """download CSV file with historical targets and ticker universe

        Returns:
            str: path to csv file

        Example:
            >>> SignalsAPI().download_validation_data()
            signals_train_val_bbg.csv
        """
        # set up download path
        if dest_filename is None:
            dest_filename = "numerai_signals_historical.csv"

        path = os.path.join(dest_path, dest_filename)

        # create parent folder if necessary
        utils.ensure_directory_exists(dest_path)
        utils.download_file(
            self.HISTORICAL_DATA_URL, path, self.show_progress_bars)
        return path

    def stake_get(self, username) -> decimal.Decimal:
        """get current stake for a given users

        Args:
            username (str)

        Returns:
            decimal.Decimal: current stake

        Example:
            >>> SignalsAPI().stake_get("uuazed")
            Decimal('14.63')
        """
        data = self.public_user_profile(username)
        return data['totalStake']
