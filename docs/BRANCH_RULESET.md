# Recommended `main` Branch Ruleset

## Current state

At the v0.2.0 public verification point, GitHub reports `main` as unprotected. The following staged policy avoids accidental history damage without locking a solo maintainer out of the repository.

## Stage A — enable now

Open **Repository → Settings → Rules → Rulesets → New branch ruleset**.

Use:

- **Name:** `main-release-safety`
- **Enforcement status:** `Active`
- **Target branches:** Include default branch

Enable:

- Restrict deletions
- Block force pushes
- Require linear history

Do not enable required deployments, merge queue or required status checks until the pull-request workflow in Stage B is adopted. Avoid broad bypass permissions; if an owner recovery bypass is retained, use it only for repository recovery and never for normal delivery.

## Stage B — enable for subsequent development

Develop on a feature branch and open a pull request into `main`. Then add:

- Require a pull request before merging
- Require conversation resolution before merging
- Require status checks to pass
- Require branches to be up to date before merging

Required check names from the current CI matrix:

```text
Python 3.11
Python 3.12
Python 3.13
```

Retain:

- Restrict deletions
- Block force pushes
- Require linear history

Recommended merge method: **Squash and merge** for independently reviewable phase commits.

## Commit signing

The v0.2.0 baseline commit is unsigned. Do not rewrite or force-push that published history. Configure SSH or GPG signing for future commits first; only then consider enabling **Require signed commits** in the ruleset.

## Recovery warning

Before activating a restrictive rule, confirm that:

1. the owner can create and merge a test pull request;
2. all three check names appear exactly as listed;
3. Pages deployment does not need to be a required source-code check;
4. at least one documented recovery path exists.

Never disable a failing check merely to merge. Diagnose the failure or explicitly revert the change through a reviewed commit.
