"""API for Numerai Classic"""

import decimal
from typing import List, Dict

from numerapi import utils
from numerapi import base_api


class NumerAPI(base_api.Api):
    """Wrapper around the Numerai API

    Automatically download and upload data for the Numerai machine learning
    competition.

    This library is a Python client to the Numerai API. The interface is
    implemented in Python and tournamentallows downloading the training data,
    uploading predictions, accessing user, submission and competitions
    information and much more.
    """

    def __init__(self, *args, **kwargs):
        base_api.Api.__init__(self, *args, **kwargs)
        self.tournament_id = 8

    def get_competitions(self, tournament=8):
        """Retrieves information about all competitions

        Args:
            tournament (int, optional): ID of the tournament, defaults to 8

        Returns:
            list of dicts: list of rounds

            Each round's dict contains the following items:

                * number (`int`)
                * openTime (`datetime`)
                * resolveTime (`datetime`)
                * resolvedGeneral (`bool`)
                * resolvedStaking (`bool`)

        Example:
            >>> NumerAPI().get_competitions()
            [
             {'number': 71,
              'openTime': datetime.datetime(2017, 8, 31, 0, 0),
              'resolveTime': datetime.datetime(2017, 9, 27, 21, 0),
              'resolvedGeneral': True,
              'resolvedStaking': True,
             },
              ..
            ]
        """
        self.logger.info("getting rounds...")

        query = '''
            query($tournament: Int!) {
              rounds(tournament: $tournament) {
                number
                resolveTime
                openTime
                resolvedGeneral
                resolvedStaking
              }
            }
        '''
        arguments = {'tournament': tournament}
        result = self.raw_query(query, arguments)
        rounds = result['data']['rounds']
        # convert datetime strings to datetime.datetime objects
        for rnd in rounds:
            utils.replace(rnd, "openTime", utils.parse_datetime_string)
            utils.replace(rnd, "resolveTime", utils.parse_datetime_string)
        return rounds

    def get_submission_filenames(self, tournament=None, round_num=None,
                                 model_id=None) -> List[Dict]:
        """Get filenames of the submission of the user.

        Args:
            tournament (int): optionally filter by ID of the tournament
            round_num (int): optionally filter round number
            model_id (str): Target model UUID (required for accounts with
                multiple models)

        Returns:
            list: list of user filenames (`dict`)

            Each filenames in the list as the following structure:

                * filename (`str`)
                * round_num (`int`)
                * tournament (`int`)

        Example:
            >>> api = NumerAPI(secret_key="..", public_id="..")
            >>> model = api.get_models()['uuazed']
            >>> api.get_submission_filenames(3, 111, model)
            [{'filename': 'model57-dMpHpYMPIUAF.csv',
              'round_num': 111,
              'tournament': 3}]

        """
        query = """
          query($modelId: String) {
            model(modelId: $modelId) {
              submissions {
                filename
                selected
                round {
                   tournament
                   number
                }
              }
            }
          }
        """
        arguments = {'modelId': model_id}
        data = self.raw_query(
            query, arguments, authorization=True)['data']['model']

        filenames = [{"round_num": item['round']['number'],
                      "tournament": item['round']['tournament'],
                      "filename": item['filename']}
                     for item in data['submissions'] if item['selected']]

        if round_num is not None:
            filenames = [f for f in filenames if f['round_num'] == round_num]
        if tournament is not None:
            filenames = [f for f in filenames if f['tournament'] == tournament]
        filenames.sort(key=lambda f: (f['round_num'], f['tournament']))
        return filenames

    def get_leaderboard(self, limit: int = 50, offset: int = 0) -> List[Dict]:
        """Get the current model leaderboard

        Args:
            limit (int): number of items to return (optional, defaults to 50)
            offset (int): number of items to skip (optional, defaults to 0)

        Returns:
            list of dicts: list of leaderboard entries

            Each dict contains the following items:

                * username (`str`)
                * rank (`int`)
                * nmrStaked (`decimal.Decimal`)
                * corr20Rep (`float`)
                * corj60Rep (`float`)
                * fncRep (`float`)
                * fncV3Rep (`float`)
                * tcRep (`float`)
                * mmcRep (`float`)
                * bmcRep (`float`)
                * team (`bool`)
                * return_1_day (`float`)
                * return_52_day (`float`)
                * return_13_day (`float`)

        Example:
            >>> numerapi.NumerAPI().get_leaderboard(1)
            [{'username': 'anton',
              'rank': 143,
              'nmrStaked': Decimal('12'),
              ...
              }]

        """
        query = '''
            query($limit: Int!
                  $offset: Int!) {
              v2Leaderboard(limit: $limit
                            offset: $offset) {
                nmrStaked
                rank
                username
                corr20Rep
                corr20V2Rep
                corj60Rep
                fncRep
                fncV3Rep
                tcRep
                mmcRep
                bmcRep
                team
                return_1_day
                return_52_weeks
                return_13_weeks
              }
            }
        '''

        arguments = {'limit': limit, 'offset': offset}
        data = self.raw_query(query, arguments)['data']['v2Leaderboard']
        for item in data:
            utils.replace(item, "nmrStaked", utils.parse_float_string)
        return data

    def stake_set(self, nmr, model_id: str) -> Dict:
        """Set stake to value by decreasing or increasing your current stake

        Args:
            nmr (float or str): amount of NMR you want to stake
            model_id (str): model_id for where you want to stake

        Returns:
            dict: stake information with the following content:

              * insertedAt (`datetime`)
              * status (`str`)
              * txHash (`str`)
              * value (`decimal.Decimal`)
              * source (`str`)
              * to (`str`)
              * from (`str`)
              * posted (`bool`)

        Example:
            >>> api = NumerAPI(secret_key="..", public_id="..")
            >>> api.stake_set(10)
            {'from': None,
             'insertedAt': None,
             'status': None,
             'txHash': '0x76519...2341ca0',
             'from': '',
             'to': '',
             'posted': True,
             'value': '10'}
        """
        # fetch current stake
        modelname = self.modelid_to_modelname(model_id)
        current = self.stake_get(modelname)
        # convert everything to decimals
        if current is None:
            current = decimal.Decimal(0)
        else:
            current = decimal.Decimal(str(current))
        if not isinstance(nmr, decimal.Decimal):
            nmr = decimal.Decimal(str(nmr))
        # update stake!
        if nmr < current:
            return self.stake_decrease(current - nmr, model_id)
        if nmr > current:
            return self.stake_increase(nmr - current, model_id)
        self.logger.info("Stake already at desired value. Nothing to do.")
        return None

    def stake_get(self, modelname: str) -> float:
        """Get your current stake amount.

        Args:
            modelname (str)

        Returns:
            float: current stake (including projected NMR earnings from open
                   rounds)

        Example:
            >>> api = NumerAPI()
            >>> api.stake_get("uuazed")
            1.1
        """
        query = """
          query($modelname: String!) {
            v3UserProfile(modelName: $modelname) {
               stakeValue
            }
          }
        """
        arguments = {'modelname': modelname}
        data = self.raw_query(query, arguments)['data']['v3UserProfile']
        return data['stakeValue']

    def daily_model_performances(self, username: str) -> List[Dict]:
        """Fetch daily performance of a user.

        Args:
            username (str)

        Returns:
            list of dicts: list of daily model performance entries

            For each entry in the list, there is a dict with the following
            content:

                * date (`datetime`)
                * corrRep (`float` or None)
                * corrRank (`int`)
                * mmcRep (`float` or None)
                * mmcRank (`int`)
                * fncRep (`float` or None)
                * fncRank (`int`)
                * fncV3Rep (`float` or None)
                * fncV3Rank (`int`)
                * tcRep (`float` or None)
                * tcRank (`int`)

        Example:
            >>> api = NumerAPI()
            >>> api.daily_model_performances("uuazed")
            [{'corrRank': 485,
             'corrRep': 0.027951873730771848,
             'date': datetime.datetime(2021, 9, 14, 0, 0, tzinfo=tzutc()),
             'fncRank': 1708,
             'fncRep': 0.014548700790462122,
             'tcRank': 1708,
             'tcRep': 0.014548700790462122,
             'fncV3Rank': 1708,
             'fncV3Rep': 0.014548700790462122,
             'mmcRank': 508,
             'mmcRep': 0.005321406467445256},
             ...
            ]
        """
        query = """
          query($username: String!) {
            v3UserProfile(modelName: $username) {
              dailyModelPerformances {
                date
                corrRep
                corrRank
                mmcRep
                mmcRank
                fncRep
                fncRank
                fncV3Rep
                fncV3Rank
                tcRep
                tcRank
              }
            }
          }
        """
        arguments = {'username': username}
        data = self.raw_query(query, arguments)['data']['v3UserProfile']
        performances = data['dailyModelPerformances']
        # convert strings to python objects
        for perf in performances:
            utils.replace(perf, "date", utils.parse_datetime_string)
        return performances
