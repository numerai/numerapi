# Round score and payout configuration

Starting in numerapi 2.24.0, `NumerAPI.list_rounds()`,
`SignalsAPI.list_rounds()`, and `CryptoAPI.list_rounds()` return the public
`roundScoreConfigs` list. Each item is an exact score definition and per-round
snapshot from the Tournament API. New code should select entries by `name`,
`version`, or `scoreConfigId`; it should not infer score identity from a legacy
payout role.

Each item includes:

- identity: `id`, `scoreConfigId`, `name`, `version`, and `displayName`;
- applicability: `roundNumberStart`, `roundNumberEnd`, `universe`,
  and `isCanonScore`;
- scoring: `totalScoreDays`, `returnsLagDays`, `dataDelayDays`,
  `scoringStart`, and `scoringEnd`;
- payout settings: `isPayout`, `minMultiplier`, `maxMultiplier`,
  `defaultMultiplier`, `clipThreshold`, `stakeThreshold`, and `payoutFactor`.

`scoringStart` and `scoringEnd` are returned as `datetime.datetime` objects,
consistent with other date fields in numerapi. GraphQL float and integer fields
retain their normal Python JSON types.

## Legacy multiplier keys removed in 3.0.0

Before 2.24.0, `list_rounds()` requested server compatibility fields. For a
Signals round, a response could look like this even though the payout scores
were Alpha and MPC:

```python
{
    "defaultCorrMultiplier": 0.3,
    "defaultMmcMultiplier": 0.8,
}
```

In 3.0.0, the exact identities are the only payout configuration returned by
`list_rounds()`:

```python
{
    "roundScoreConfigs": [
        {
            "scoreConfigId": "...",
            "name": "alpha",
            "version": "2",
            "displayName": "alpha",
            "isPayout": True,
            "defaultMultiplier": 0.3,
            # Other identity, scoring, timing, and payout fields omitted.
        },
        {
            "scoreConfigId": "...",
            "name": "meta_portfolio_contribution",
            "version": "2",
            "displayName": "mpc",
            "isPayout": True,
            "defaultMultiplier": 0.8,
        },
    ]
}
```

The six Corr/MMC compatibility keys (`min`, `max`, and `default` for each) are
no longer added to the returned round dictionary. `list_rounds()` never
exposed the three legacy TC multiplier fields. Code should filter
`roundScoreConfigs`, normally starting with `isPayout`, and preserve each
configuration's `name`, `version`, and `scoreConfigId` rather than projecting
different scores into Corr or MMC roles.

## Deprecated performance endpoint

`round_model_performances_v2()` remains an isolated deprecated compatibility
method. Its `corrMultiplier` and `mmcMultiplier` fields come from the deprecated
`v2RoundModelPerformances` GraphQL endpoint and must not be used to infer score
identity. Use `submission_scores()` for identity-preserving score results and
join them to `list_rounds()` by round when payout configuration is needed.
Neither performance method nor `list_rounds()` has a dedicated CLI command, so
there is no CLI return shape to migrate.
