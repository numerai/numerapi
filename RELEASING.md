# Releasing numerapi

numerapi ships to **PyPI only**. There are no container images, no ECR, and no
branch-triggered deploys in this repo — if you are thinking of the
`master` → prod / `staging` → staging image flow from our other repos, that does
not apply here.

## The model

Two rules explain everything else:

1. **`numerapi_version` in `setup.py` is the release.** The git tag is only the
   trigger. Whatever that string says is what lands on PyPI.
2. **The version string picks the channel**, not the branch. A
   [PEP 440](https://peps.python.org/pep-0440/) pre-release (`3.2.0.dev0`) is
   invisible to `pip install numerapi`; a final version (`3.2.0`) is what
   everyone gets by default.

| Ref | Role |
| --- | --- |
| `<user>/<topic>` | all work; branch off `preview` |
| `preview` | integration branch; **beta** releases are cut here |
| `master` | released state; **final** releases are cut here |
| `vX.Y.Z.devN` tag | publishes a pre-release |
| `vX.Y.Z` tag | publishes a final release |

Nothing publishes on a branch push. Only pushing a tag publishes.

| What a user runs | What they get |
| --- | --- |
| `pip install numerapi` / `pip install -U numerapi` | latest **final** version |
| `pip install 'numerapi==3.2.0.dev0'` | that exact pre-release |
| `pip install --pre numerapi` | latest including pre-releases |

## Conventions

- Tags are `v`-prefixed and must match `setup.py` exactly: `v3.2.0`,
  `v3.2.0.dev0`. CI rejects a mismatch.
- Use the canonical PEP 440 spelling with the dot: `3.2.0.dev0`, not `3.2.0dev0`.
  Both normalize to the same release, but the canonical form avoids confusion.
- Pre-releases use `.devN`. Increment `N` for each beta on the same version line.
- **A version number can never be reused.** PyPI permanently rejects re-uploading
  a version, even one that was deleted. If you burn a number, move to the next.

## Develop without releasing

```bash
git checkout preview && git pull
git checkout -b josh/some-feature
# ... work ...
git push -u origin josh/some-feature
gh pr create --base preview
```

Tests and lint run on every push. No tag means nothing is published. `preview`
can sit ahead of `master` indefinitely — that is what it is for. Leave
`setup.py` alone until you are actually cutting something.

## Cut a beta (from `preview`)

For beta users who need the code before it is stable.

```bash
git checkout preview && git pull

# 1. setup.py:  numerapi_version = "3.2.0.dev0"
# 2. CHANGELOG.md: open an entry
#    ## [3.2.0] - Unreleased
#    - what changed
git commit -am "numerapi 3.2.0.dev0"
git push origin preview          # publishes nothing

# 3. tag and push — this is the release event
git tag v3.2.0.dev0
git push origin v3.2.0.dev0
```

Verify:

```bash
gh run list --workflow=pypi.yml --limit 1                 # expect success
pip install 'numerapi==3.2.0.dev0'                        # what beta users run
pip install -U numerapi                                   # must NOT be the dev version
```

Tell beta users to install the exact version. Note that `pip index versions` and
the simple index can lag a few minutes behind a successful publish on CDN cache;
an exact-version install works immediately.

For the next beta, repeat with `.dev1`, `.dev2`, …

## Promote to a final release (from `master`)

Flip the version to final **on `preview`, as the last commit before merging**, so
`master` never holds a pre-release string and picks up the release version
atomically at merge.

```bash
git checkout preview && git pull

# 1. setup.py:  numerapi_version = "3.2.0"      (drop the .devN suffix)
# 2. CHANGELOG.md: date the entry, e.g. ## [3.2.0] - 2026-08-17
git commit -am "numerapi 3.2.0"
git push origin preview

# 3. merge preview into master
gh pr create --base master --head preview --title "numerapi 3.2.0"
gh pr merge <n> --merge

# 4. tag master
git checkout master && git pull
grep numerapi_version setup.py                   # must read exactly 3.2.0
git tag v3.2.0
git push origin v3.2.0

# 5. keep preview caught up so it does not drift
git checkout preview && git merge master && git push origin preview
```

Verify with `pip install -U numerapi`.

Then bump the numerapi pin in `tournament-monorepo` (`shared`, `init-round`,
`integration-test`, `compute-pickle-scheduler`). That PR moving through the
monorepo's own staging → master is what carries the new numerapi into staging
and prod images. Never pin a `.devN` version in anything that reaches prod.

## Hotfix a released version

Use this when `master` is released and `preview` holds unreleased work you do not
want to ship yet.

```bash
git checkout -b hotfix/3.2.1 master     # branch off master, NOT preview
# fix + setup.py 3.2.1 + CHANGELOG entry
gh pr create --base master
# after merge:
git checkout master && git pull
git tag v3.2.1 && git push origin v3.2.1
git checkout preview && git merge master && git push origin preview
```

## Documentation

Read the Docs is fully automatic — there is nothing to tag or move.

- `/en/latest/` tracks `master`.
- `/en/stable/` tracks the greatest **non-pre-release** semver tag, so cutting
  `v3.2.0` promotes it; `v3.2.0.dev0` is correctly ignored.

Do not create a tag or branch named `stable`. That overrides the automatic
behavior above, has to be force-moved by hand on every release, and silently goes
stale when someone forgets. One used to exist here and was removed for exactly
those reasons. The trade-off is that a docs-only fix reaches `/en/latest/`
immediately but does not appear on `/en/stable/` until the next release; if that
matters, cut a patch release.

## What CI enforces

`.github/workflows/pypi.yml` runs on tag pushes matching `v[0-9]*` and will
refuse to publish unless:

1. **The tag matches `setup.py`.** Compared as normalized PEP 440 versions, so
   `v3.2.0dev0` and `v3.2.0.dev0` are equivalent, but `v3.2.0` against a
   `setup.py` of `3.2.0.dev0` fails.
2. **Final releases point at a commit on `master`.** Pre-releases skip this
   check, so betas can be cut from `preview` but a final one cannot.

`pytest.yml` (Python 3.10–3.14) and `ruff.yml` run on every push and PR.

## Troubleshooting

**`File already exists` on publish.** That version is already on PyPI. Bump to
the next number — you cannot re-upload, and you cannot fix it by deleting the
release on PyPI either.

**Tag mismatch error.** You tagged without bumping `setup.py`, or vice versa. Fix
`setup.py`, commit, delete the tag locally and on origin
(`git push origin :refs/tags/vX.Y.Z`), then re-tag. Deleting a tag never
publishes anything.

**"Final release tags must point at a commit on master."** You tagged a
suffix-free version on `preview`. Either merge to `master` first, or cut it as a
`.devN` pre-release instead.

**Do not retro-tag old releases.** Any new tag matching `v[0-9]*` triggers a
publish attempt that will fail on a duplicate version. Historical tags are
inconsistent (some `v`-prefixed, some not, several `.devN` tags that published
final versions before the guards existed) — leave them as they are.

**Do not delete the `3.0.0.dev2` tag.** The commit it points at is on no branch,
and that tag is the only thing keeping the source of the published 3.0.0
reachable.
