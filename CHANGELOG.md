# Changelog
Notable changes to this project.

## [2.24.0] - 2026-08-03
- add exact `roundScoreConfigs` identities, scoring windows, and payout settings
  to `list_rounds` for Classic, Signals, and Crypto
- stop querying deprecated GraphQL round multiplier fields; keep the six
  established Corr/MMC return keys as exact-name compatibility projections
  until their scheduled removal in numerapi 3.0.0
- document migration from legacy round multiplier roles and isolate the
  deprecated `round_model_performances_v2` behavior
- expose the tournament-aware `stake_get` API consistently for Classic,
  Signals, and Crypto

## [2.23.3] - 2026-06-30
- fix `models_of_account` referencing incorrect type `Str!` instead of `String!`

## [2.23.2] - 2026-06-02
- increase dataset download chunk size to 1 MB to improve download speeds

## [2.23.1] - 2026-04-23
- fix package version lookup


## [2.22.0] - 2026-01-05
-- added `get_leaderboard` for crypto tournament

## [2.21.0] - 2025-12-08 - CLI for signals and crypto!
- cli: allow selecting tournaments (Classic/Signals/Crypto) via `--tournament` (PR #119)
- added timezone-aware dates to BaseAPI (PR #119)
- added `mmcMultiplier` and `roundPayoutFactor` to `round_model_performances_v2`
- more type hints

## [2.20.8] - 2025-09-11
- added `BMC` and `Alpha` to diagnostics

## [2.20.7] - 2025-06-13
- fix `download_dataset`
- improve type hints

## [2.20.6] - 2025-04-02
- cli: fix `check_new_round`

## [2.20.5] - 2025-04-02
- type hint improvements
- no longer depend on `pkg_resources`

## [2.20.1] - 2025-03-29
- add a `py.typed` file to indicate type hints

## [2.20.0] - 2025-02-21
- deprecate `round_model_performances`
- support `.env` files for authentication, requires `python-dotenv`
- remove deprecated functionality
- ci: use Python 3.10

## [2.19.1] - 2024-07-29
- `stake_drain`: set drain flag correctly, so things will look less confusing
  in the UI
- fix `SignalsAPI.upload_predictions`

## [2.19.0] - 2024-07-26 - hello CryptoAPI
- fix `SignalsAPI.ticker_universe`
- added `validationBmcMean` and `era.validationBmc` to diagnostics
- added `CyptoAPI`

## [2.18.0] - 2024-03-08
- added `get_account_leaderboard` to fetch account-level leaderboard
- added 'models_of_account' to fetch all models of an account
- 'SignalsAPI.ticker_universe': stop using hardcoded URL
- remove `set_stake_type` - no longer relevant
- deprecate 'SignalsAPI.download_validation_data'
- code style fixes
- fix docs

## [2.17.0] - 2024-02-18
- signals: add 'list_datasets' and 'download_dataset'

## [2.16.3] - 2024-01-01
- add `bmcRep` and `mmcRep` to `get_leaderboard`

## [2.16.2] - 2023-12-28
- fix `get_leaderboard`

## [2.16.1] - 2023-10-09
- added 'corr20V2Rep' to 'get_leaderboard'
- deprecate methods related to v2 and v3 datasets

## [2.16.0] - 2023-09-28 - submission downloads
- added `download_submission` to download a CSV of a previous submission
- added `submission_ids` to fetch all submission_ids of a model
- minor fixes

## [2.15.1] - 2023-08-25 - model upload improvements
- model_upload now allows specifying which data_version and which image to use
- added `round_model_performances_v2`, which allows fetching newer metrics
- added `pipeline_status` to get the status of numerai's scoring pipeline
- added `intra_round_scores` to fetch intra-round metrics of your models
- handle downtimes of Numerai's API more gracefully
- added `model_upload_docker_images` and `model_upload_data_versions`

## [2.15.0] - 2023-07-13 - model uploads!
- add corr20V2 into round_model_performances (PR #100)
- add tcMultiplier into round_model_performances
- add `model_upload` feature, to allow uploading pickled models to numerai

## [2.14.0] - 2023-04-06 - no more submission_status
- deprecate `SignalsAPI.submission_status`
- deprecate `NumerAPI.submission_status`

## [2.13.4] - 2023-04-03
- return filepath from `download_dataset`

## [2.13.3] - 2023-04-03
- add `modelid_to_modelname` method
- fix `stake_set`
- add option to adjust connection timeout when upload predictionions (PR #97)
- remove deprecated `download_latest_data`
- add `set_global_data_dir` method
- docs

## [2.13.2] - 2023-02-22
- add `data_datestamp` argument to `upload_predictions` - this will allow
  submitting predictions using data from a previous round.

## [2.13.1] - 2023-02-15
- fix `SignalsAPI.daily_model_performances`
- adding all the new metrics (RIC, CorrV4, FncV4, etc) to `diagnostics`

## [2.13.0] - 2022-12-16 - "API deprecations"
- `stake_get` - updated to migrate away from deprecated API endpoint
- remove deprecated `SignalsAPI.daily_user_performances`
- remove deprecated `SignalsAPI.daily_submissions_performances`
- remove `round_details` - no longer supported by Numerai
- remove deprecated `daily_submissions_performances`

## [2.12.9] - 2022-12-02
- numerapi-cli: make `check-new-round` more robust
- more robust `check_new_round` and `check_round_open` - working around some
  edge cases, that occur during the time without any active round.

## [2.12.8] - 2022-11-21
- change default argument for `check_new_round` to 12 hours
- deprecate `daily_submissions_performances`
- update `get_leaderboard` to reflect changes in the backend
- add downloads per month batch
- fix docs
- update README

## [2.12.7] - 2022-11-02
- fix `check_round_open`

## [2.12.6] - 2022-11-01
- add `check_round_open` to check if there is a currently an active round
- make `check_new_round` accessible from `SignalsAPI`

## [2.12.5] - 2022-10-24
- add fncV3 to `daily_submissions_performances`
- add `TC` to `SignalsAPI.get_leaderboard`
- add `TC` and `corr60` to `SignalsAPI.daily_model_performances`
- add `TC` to `SignalsAPI.daily_submissions_performances`
- define timeouts for all web call made with `requests`

## [2.12.4] - 2022-08-24
- add `set_stake_type` to change payout mode and multipliers (PR #83)
- add auth to `round_details` query (PR #86)

## [2.12.3] - 2022-07-03
- fix directory check in download_dataset in the last update

## [2.12.2] - 2022-06-30
- `diagnostics` now returns all diagnostics results, if no diagnostics_id is specified
- `download_dataset`: in case the destination path contains a directory, ensure it exists

## [2.12.1] - 2022-06-20
- bugfix, timeout for http requests was accidentally set to 3 seconds.

## [2.12.0] - 2022-06-17
- make downloads more robust and prevent broken files by downloading to temporary files
- simple retry mechanism for failed API requests (5xx error codes only)
- Remove submission `version` parameter (PR #75)

## [2.11.0] - 2022-03-29
- add tc, fnc, fncV3 to get_leaderboard
- add icRank, icRep to SignalsAPI.get_leaderboard
- add tcRank, tcRep, fncV3Rep and fncV3Rank to daily_model_performances
- add icRep and icRank to SignalsAPI.daily_model_performances
- add tc and tcPercentile to daily_submissions_performances
- make `stake_set` work with multi model accounts
- add tc to the round_model_performances method (PR #74)
- add tcPercentile, ic, icPercentile, fncV3, fncV3Percentile to round_model_performances

## [2.10.0] - 2022-02-07
- added `set_bio` to programmatically update the bio field for some model
- added `set_link` to programmatically update the user link field
- enable stake changes for Numerai Signals (#68 Thx @habakan)
- run tests via github actions and disable travis integration

## [2.9.4] - 2021-11-14
- cli: fix predictions upload

## [2.9.3] - 2021-11-12
- cli: support uploading predictions generated with the new dataset (needs `--new_data`)
- signals: make `round_model_performances` available

## [2.9.2] - 2021-10-07
- signals: support upload to diagnostic tool
- cli: added `list-datasets`
- cli: implement downloading of the new dataset
- some code cleanup

## [2.9.1] - 2021-09-27
- add query `round_model_performances` (#60)
- fix documentation
- upgrade from `latestSubmission` to `latestSubmissionV2`
- Indicate source `numerapi` when uploading submissions
- Deprecate `get_account_transactions` - data no longer available
- Deprecate `get_transactions` - data no longer available
- Add `wallet_transactions`, fetches all transactions to / from your wallet
- Code style improvements

## [2.9.0] - 2021-09-15
- support passing `round_num` to `list_datasets`, to get available files from past rounds
- `download_dataset` no longer requires a destination path, it defaults to the source file name
- `download_dataset` now accepts a `round_num` argument, to download old files
- added `upload_diagnostics` to upload to the new diagnostics tool
- added `diagnostics` to fetch results of a diagnostics run

## [2.8.1] - 2021-09-08
-  Add version arg to upload_predictions (#59)

## [2.8.0] - 2021-09-07 - "new data api"
- added `list_datasets` to fetch the list of available data files
- added `download_dataset` to download files from the new data api
- add missing documentation and deprecation warnings

## [2.7.1] - 2021-09-01
- Add mmc20d rep and rank to SignalsAPI daily_model_performances
- rename `corr_20d*` to `corr20d*` since Numerai's GraphQL adapter now handles numbers in fields without underscores

## [2.7.0] - 2021-08-27
- adding `fncPercentile`, `mmcPercentile` & `corrPercentile` to `daily_submissions_performances`
- replace deprecated GraphQL `v2UserProfile` call with `v3UserProfile`
- replace deprecated GraphQL `signalsUserProfile` call with `v2SignalsProfile`
- new `daily_model_performances`, replacing `daily_user_performances`
- signals: new `daily_model_performances`, replacing `daily_user_performances`
- update & fix command line interface

## [2.6.0] - 2021-07-12
- cli: remove deprecated 'payments' and 'user-activities' commands (#51)
- cli: converting the output to JSON (#52)

## [2.5.2] - 2021-06-30
- remove deprecated fields (#50)
  - remove userActivities query (deprecated, use userProfile fields instead)
  - remove payments query (deprecated, use userProfile fields instead)
  - remove misc deprecated fields from userProfile like badges, earnings
  - remove misc deprecated scores from submissions like consistency and concordance
  - remove misc deprecated fields from userProfile.dailyUserPerformances like reputation and rolling_score_rep (use corrRep/mmcRep/fncRep instead), and all the early staking 2.0 fields like averageCorrelation, averageCorrelationPayout, sumDeltaCorrelation etc.
- fix 'get_competitions' by removig deprecated fields (#49)

## [2.5.1] - 2021-05-10
- lower pandas requirement to pandas>=1.1.0 to fix problems for users working in google colab (#48)

## [2.5.0] - 2021-05-09
- resumable download (#42)
- Upload submission functions using a pandas dataframe (#46)

## [2.4.5] - 2021-03-18
- enable registering submission webhooks and trigger IDs (#44)

## [2.4.4] - 2021-03-04
- make `get_current_round` available in SignalsAPI
- add `download_validation_data` to SignalsAPI, to download the latest validation
  data, historical targets and ticker universe

## [2.4.3] - 2021-02-27
- deprecate multi-tournament handling
- `get_models` now returns the list of models depending on the tournament you
  are working on - numerai classic (NumerAPI) vs numerai signals (SignalsAPI).
  This is necessary after the recent "model split".

## [2.4.2] - 2021-02-25
- `daily_user_performances` add `fnc`
- `daily_submissions_performances` filter all-None items

## [2.4.1] - 2021-02-13
- improve docstrings and signals example code
- remove deprecated `get_v1_leaderboard`
- remove deprecated `get_stakes` & `get_submission_ids`
- Fix default file path for `download_latest_data` (#37)
- test suite: fixes

## [2.4.0] - 2021-01-12
- fix `stake_change` call by adding `tournament` parameter (#32)
- add `tournament` parameter to all stake related endpoints
- code style checks with `flake8`
- Remove header from signals universe (#33)
- Add `get_latest_data_path` and `download_latest_data` (#35)

## [2.3.9] - 2020-11-26
- Add additional metrics to `submission_status` (#30)
- signals: add `mmc`, `mmcRank` and `nmrStaked` to `get_leaderboard`
- signals: add `totalStake` to `public_user_profile`
- signals: add `stake_get`

## [2.3.8] - 2020-10-27
- signals: speedup `ticker_universe`
- signals: add `mmcRep` and `reputation` to `daily_user_performances`
- signals: add `mmc`, `mmcRep`, `correlation`, `corrRep` and `roundNumber`
           to `daily_submissions_performances`

## [2.3.7] - 2020-10-15
- signals: fix ticker universe

## [2.3.6] - 2020-10-07
- signals: update ticker universe path (#29)

## [2.3.5] - 2020-09-28
- Add signals diagnostics (#28)

## [2.3.4] - 2020-08-10
- update 'ticker_universe' to use the update file location

## [2.3.3] - 2020-07-22
- get Numerai compute id if available and pass it along during predictions upload

## [2.3.2] - 2020-07-21
- Signals: added `ticker_universe` to get the list of accepted tickers
- `submission_status` no longer needs (and accepts) a submission_id. It
  automatically uses the last submission associated with a model

## [2.3.1] - 2020-05-06 - "Signals"
- fix Signals submission upload (#25)

## [2.3.0] - 2020-05-06 - "Signals"
- added API for Numerai Signals
- refactor codebase
- more tests

## [2.2.4] - 2020-05-11
- Remove required model_id annotation for submissions status lookups so that None can be passed
- Use consistent modelId in query spec
- Update doc examples

## [2.2.2] - 2020-05-09
- fix `submission_status` for multi model accounts

## [2.2.0] - 2020-04-17
- no more Python2 support
- added type hints
- add `get_account` to return private account information and deprecates `get_user` (#23)
- incorporates updates to the Numerai tournament API in anticipation of the rollout of a new account system with multi-model support (#23)

## [2.1.6] - 2020-04-08
- add `rolling_score_rep` to `daily_user_performances` and `get_leaderboard`
- deprecate `reputation` in `daily_user_performances` and `get_leaderboard`

## [2.1.5] - 2020-04-03
- added `payoutPending` and `payoutSettled` to `get_leaderboard` (#21)
- added `sumDeltaCorrelation`, `finalCorrelation`, `payoutPending` and `payoutSettled` to `daily_user_performances` (#21)

## [2.1.4] - 2020-03-30 - "Spring cleanup"
- added "sharpe", "feature exposure" and "correlation with example predictions" to `submission_status`
- remove deprecated `check_submission_successful`
- added `bio` and `totalStake` to `public_user_profile`
- remove deprecated `get_rankings`

## [2.1.3] - 2020-03-30
- fix `get_user_activities`
- remove deprecated `get_staking_leaderboard`, `get_nmr_prize_pool`
- added `mmc` and `correlationWithMetamodel` to `daily_submissions_performances`

## [2.1.2] - 2019-11-30
- fix staking after recent changes to the GraphQL backend

## [2.1.1] - 2019-11-23
- add `round_details`, returning correlation scores of all users for the round

## [2.1.0] - 2019-11-15
- add some more details to `get_leaderboard`
- adapt to changes in Numerai's staking API

## [2.0.1] - 2019-10-28
- fix `stake_set`

## [2.0.0] - 2019-10-23
- add v2 version of `get_leaderboard`
- add `stake_get` & `stake_set`
- add `stake_increase`, `stake_decrease` & `stake_drain`
- add `public_user_profile`
- add `daily_user_performances`
- add `daily_submissions_performances`
- remove v1 staking
- remove `get_staking_cutoff` - no longer relevant
- old `get_leaderboard` renamed to `get_v1_leaderboard`
- add v2-style staking to cli interface
- update documentation

## [1.6.2] - 2019-07-31
- remove phone number and bonus fetching (#16)

## [1.6.1] - 2019-07-12
- fix downloading dataset for tournaments > 1
- add `validationCorrelation` and `liveCorrelation` to all relevant places
- remove `validationAuroc` and `validationLogloss` from `submission_status`

## [1.6.0] - 2019-07-10
- default to tournament 8 `katzuagi`
- update docstring
- added `reputationPayments`,

## [1.5.5] - 2019-06-13
- include `otherUsdIssuances` and `phoneVerificationBonus` to `get_payments`
- add datetime information (`insertedAt`) to `get_transactions`

## [1.5.4] - 2019-05-30
- return new `reputation` as announced by numerai on 2019-05-29 in `get_rankings`

## [1.5.3] - 2019-05-23
- fix setup.py to make it work with the latest twine version

## [1.5.2] - 2019-05-22
- add NMR returned information to `get_leaderboard` - useful for partial burns

## [1.5.1] - 2019-04-14
- fix `get_staking_cutoff` for rounds >= 154

## [1.5.0] - 2019-04-03
- tests: start testing the cli interface
- cli: fix `version` command on Python2.7
- added `liveAuroc` and `validationAuroc` to `get_leaderboard`
- added `liveAuroc` and `validationAuroc` to `get_staking_leaderboard`
- added `liveAuroc` and `validationAuroc` to `get_user_activities`
- added `validationAuroc` to `submission_status`
- added `ruleset` to `get_competitions`
- added `phoneNumber` and `country` to `get_user`
- remove consistency check from `test_check_submission_successful`

## [1.4.6] - 2019-03-30
- remove total payments from leaderboard query (#13)
- fix `get_staking_leaderboard`

## [1.4.5] - 2019-03-05
- `get_tournaments` now allows to filter for active tournaments only
-  CLI: `tournaments` gained `active_only` / `all` flags to get all or only
   the active tournaments

## [1.4.4] - 2019-02-17
- remove timeout completely to fix upload issues

## [1.4.3] - 2019-02-17
- increase default timeout to 20s
- better error handling

## [1.4.2] - 2019-02-10
- `get_staking_cutoff` now gets the cutoff values via the api, instead of
   doing it's own computation
- compatibility with `click` version >= 7.0

## [1.4.1] - 2019-02-10
- handle connection errors more gracefully (#11)
- pin minimum version of tqdm to (hopefully) prevent an exception (#12)
- travis: test against Python 3.7

## [1.4.0] - 2018-11-16
- added `burned` to `get_user_activities`
- docs: fixed typos + improved example
- `validation_logloss` -> `validationLogloss`, to follow numerai's docs
- remove everything `originality` related

## [1.3.0] - 2018-08-09
- added `get_staking_cutoff` to compute staking cutoff for a given round and tournament.
- added `get_nmr_prize_pool` to get the NMR prize pool for a given round and tournament.

## [1.2.1] - 2018-08-05
- removed `filename` from `get_user_activities`, no longer supported.
- rename `get_submission_filename` to `get_submission_filenames`
- `get_submission_filenames` now only works for the authorized user. It allows
  to get ones submission filenames, optionally filtered by round_num and
  tournament.

## [1.2.0] - 2018-08-03
- added `get_rankings`, which gives access to numerai's global leaderboard
- added `get_user_activities`, that allows to see each user's submission and
  staking activity
- added `get_submission_filename` to get the submission filename for any user,
  tournament & round number combination
- added `prizePoolNmr`, `prizePoolUsd` and number of `participants` to the
  `get_competitions` endpoint
- ensure functionality of command line interface is in sync

## [1.1.1] - 2018-06-06
- added `get_tournaments`
- added `tournament_name2number` and `tournament_number2name` to translate
  between tournament numbers and names

## [1.1.0] - 2018-05-24
- added numerapi command line interface
- allow passing public ID and secret key via environment variables

## [1.0.1] - 2018-05-17
- added `stakeResolution` information to get_leaderboard
- added badge for read the docs to README

## [1.0.0] - 2018-04-25
- publish README as long_description on pypi
- fixed `get_transactions` after API change on Numerai's side
- added proper docstrings to all public methods, using Google Style as
  described at http://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_google.html
- added examples for all public methods
- added documentation on readthedocs: http://numerapi.readthedocs.io

## [0.9.1] - 2018-04-22
- add tournamentId to `get_stakes`
- fixed `stake` after API change on Numerai's side

## [0.9.0] - 2018-04-13
- support tournament parameter for various endpoints. Numer.ai is planning to
  run more than one tournament at a time. This change makes numerapi ready for
  that.
- minor code cleanup

## [0.8.3] - 2018-04-07
- don't query Numerai's API if the action requires an auth token, but there
  is none provided
- more & improved tests (test coverage now > 90%)
- consistency threshold moved to 58, following the latest rule change

## [0.8.2] - 2018-03-09
- use `decimal.Decimal` instead of floats to avoid rounding errors (#3)
- optional flag to turn of tqdm's progress bars (#4)
- update `check_submission_successful` to recent rule changes (originality
  no longer required)
- update documentation

## [0.8.1] - 2018-01-27
- import NumerAPI class to toplevel. now `from numerapi import NumerAPI` works
- added `get_dataset_url`
- more & improved tests

## [0.8.0] - 2018-01-06
- added `check_new_round` to check if a new round has started
- added `check_submission_successful` to check if the last submission passes
  concordance, originality and consistency
- return proper Python data types, for example the NMR amounts are now
  floats and no longer strings
- show progress bar while downloading dataset
- general code cleanup & more tests

## [0.7.1] - 2017-12-29
- fix import issues (py2 vs py3)

## [0.7.0] - 2017-12-29
- convert datetime strings to proper Python datetime objects
- only append .zip to downloaded dataset if zip=True
- use round_number instead of date in default download filename
- setup travis to run test automatically
- run tests with different Python versions (2.7, 3.5 and 3.6)
- test coverage reports via codecov.io

## [0.6.3] - 2017-12-20
- complete rewrite to adapt to Numerai's API switch to GraphQL
- update documentation and example
- added staking via API - `stake`
- added `get_staking_leaderboard`
- allow passing desired filename to data download
- allow custom API calls - `raw_query`
- started a test suite
- moved numerapi to it's new home (https://github.com/uuazed/numerapi)
- make numerapi available on pypi (https://pypi.org/project/numerapi)
- rename package from NumerAPI to all-lowercase numerapi
