# Release automation

Cities2-MCP defaults every same-repository pull request to a patch release. Apply `release:none` to repository-only changes that do not alter any published package, plugin, server, corpus, or distribution artifact. Apply `release:minor` or `release:major` only when that larger semantic bump is intentional. The three release labels are mutually exclusive.

Bundled wiki corpus refreshes are minor releases. Apply `release:minor` to every pull request that updates the shipped wiki corpus so the generated release version reflects the material knowledge-base update.

## GitHub App

Install one private GitHub App on `mayor-modder/Cities2-MCP` and `mayor-modder/Mayor-Modder-Cities2-Plugins`. Grant repository `contents: write`, `pull requests: write`, and metadata read access. Do not grant organization administration or unrelated repository access.

Store its client ID as a Cities2-MCP Actions variable named `RELEASE_APP_CLIENT_ID`. Store its private key as an Actions secret named `RELEASE_APP_PRIVATE_KEY`.

## Labels and branch rule

Create `release:none`, `release:minor`, and `release:major` in Cities2-MCP. Add `Prepare release version / prepare` to the required status checks for `main`, retaining strict up-to-date branch enforcement and the existing test and CodeQL checks.

Enable repository auto-merge in `mayor-modder/Mayor-Modder-Cities2-Plugins` (`allow_auto_merge: true`) so the validated generated catalog pull request can complete without a second maintainer action.

## Release path

The PR workflow writes the generated version commit. After a validated merge, finalization creates `vX.Y.Z`; the existing release workflow publishes PyPI, MCP Registry, and GitHub Release artifacts, then opens and auto-merges a generated marketplace pull request.

If source publication succeeds but catalog delivery fails, treat the marketplace as incomplete and rerun the failed catalog job after correcting the named authentication or validation error.
