# Automated release versioning design

## Summary

Cities2-MCP should assign a semantic version to every merged update without requiring the maintainer to remember a release command. Pull requests default to a patch bump. A maintainer may apply `release:minor` or `release:major` when a larger bump is intentional. The first release under this design is explicitly `0.2.0`.

The version must have one canonical source. Python package metadata, MCP server metadata, generated plugin manifests, vendored plugin payloads, tests, tags, PyPI distributions, MCP Registry metadata, and the Mayor Modder plugin marketplace must all derive from or validate against that source.

Merging a fully validated Cities2-MCP pull request is the human release approval. Tagging, registry publication, GitHub Release creation, and catalog synchronization may proceed automatically after the merge.

## Goals

- Make an unlabeled pull request produce the next patch version automatically.
- Let the maintainer request a minor or major bump with one mutually exclusive pull request label.
- Establish `cities2_mcp.__version__` as the canonical public version.
- Remove duplicate hand-maintained version declarations and hard-coded version assertions.
- Keep generated plugin and marketplace metadata synchronized with the Python package and MCP Registry metadata.
- Publish each merged version through the existing tag-triggered PyPI, MCP Registry, and GitHub Release workflow.
- Open and auto-merge a validated update in `mayor-modder/Mayor-Modder-Cities2-Plugins` so installed clients receive the new payload.
- Fail visibly when any release surface is stale or publication is incomplete.

## Non-goals

- Infer semantic significance from commit messages or changed file paths.
- Publish prerelease, development, calendar, or build-metadata versions.
- Change skill behavior, MCP tool behavior, or the bundled corpus beyond carrying the already-approved corpus refresh into `0.2.0`.
- Write directly to the marketplace repository's protected `main` branch.
- Support automated writes to branches owned by external forks in the first implementation.

## Version model

`cities2_mcp.__version__` is the canonical full semantic version. Hatch reads that value dynamically when building the Python package. `cities2_mcp.mcp_server` imports the package version instead of declaring its own copy.

The release metadata generator renders `server.json` from the canonical version, including both the top-level MCP server version and the PyPI package version. Existing plugin metadata builders continue to import the canonical version and render Claude, Codex, and Antigravity manifests. The package synchronization command copies the canonical Python package into vendored plugin payloads.

Tests compare generated and runtime versions to `cities2_mcp.__version__`. They do not repeat a literal release number except in focused version-bump fixtures.

The initial implementation sets the canonical version to `0.2.0`. Subsequent bump rules are:

- No release label: increment patch and preserve major/minor, such as `0.2.0` to `0.2.1`.
- `release:minor`: increment minor and reset patch, such as `0.2.7` to `0.3.0`.
- `release:major`: increment major and reset minor/patch, such as `0.8.4` to `1.0.0`.
- Both release labels: fail without changing files.

## Pull request automation

A version preparation workflow runs for same-repository pull requests when they are opened, synchronized, reopened, or relabeled. It reads the current version from the pull request's base branch, applies the selected bump rule, and invokes a repository-owned version preparation command.

The version preparation command updates the canonical version, regenerates `server.json`, runs plugin package synchronization, and verifies that a second invocation produces no further diff. It must be usable locally and in CI even though maintainers normally rely on automation.

The workflow is idempotent: it calculates the target from the base branch rather than incrementing the pull request's current value. A rerun therefore preserves the same target version. Changing between no label, `release:minor`, and `release:major` recalculates the target from the same base version.

The automation uses a narrowly scoped GitHub App installation token to commit generated version changes to same-repository pull request branches. App-authored commits must trigger the normal required checks. External fork pull requests receive a failing explanatory check and require a maintainer-owned branch before release preparation can proceed.

Branch protection must require pull requests to be current with `main` before merge. If another release lands first, updating the branch recalculates its version from the new base and prevents duplicate versions.

## Merge and publication flow

On a push to `main`, release finalization runs only when the canonical version differs from the latest published version. It verifies that package runtime metadata, `server.json`, generated plugin manifests, and vendored payloads all agree before creating a tag.

The workflow creates `vX.Y.Z` at the `main` commit. If that tag already exists at the same commit, the operation is idempotently successful. If it exists at another commit, finalization fails and does not publish.

The existing tag-triggered release workflow remains responsible for running tests, building the wheel and source distribution, publishing to PyPI, publishing MCP Registry metadata, and creating or updating the GitHub Release.

After source publication succeeds, catalog synchronization checks out `mayor-modder/Mayor-Modder-Cities2-Plugins` with a narrowly scoped GitHub App token and runs the existing `python -m cities2_mcp.plugin_packages sync-catalog` path. It pushes the generated catalog diff to a dedicated branch, opens or updates one pull request, and enables squash auto-merge. Marketplace repository auto-merge is a documented one-time prerequisite. The workflow never pushes directly to catalog `main`.

The catalog pull request includes the Claude and Codex plugin packages, canonical skills, vendored Python implementation, refreshed corpus, generated plugin manifests, and marketplace entries. Catalog checks must confirm that its plugin version and corpus manifest match the source release before auto-merge.

## Authentication and permissions

The automation uses a GitHub App rather than a broad personal access token. Its installation is limited to Cities2-MCP and Mayor-Modder-Cities2-Plugins, with only the permissions needed to read repository metadata, write branches, create pull requests, and request auto-merge. Workflows read the App client ID from a repository variable and the private key from an Actions secret.

PyPI and MCP Registry publication continue using the existing GitHub OIDC configuration. No long-lived PyPI or MCP Registry credential is introduced.

If the GitHub App token is unavailable, version preparation or catalog synchronization fails with an explicit check summary naming the missing configuration. The workflow must not silently fall back to a broader credential.

## Failure handling

- Conflicting release labels fail before modifying the pull request branch.
- Invalid or non-semantic canonical versions fail before generation.
- A stale pull request must be updated with `main` and recalculated before merge.
- Generated metadata drift fails CI and prints the synchronization command that restores it.
- A second generation pass producing changes fails the idempotency check.
- A mismatched existing tag blocks publication.
- A version already present on PyPI at a different source commit blocks release finalization; retries of the same release remain safe.
- Catalog authentication, generation, tests, or auto-merge failures leave the catalog pull request open and mark marketplace distribution incomplete.
- Source publication success and catalog distribution success are reported separately so a partial release is visible.

## Validation

### Unit and repository checks

- Test patch, minor, and major calculations, including zero-valued components.
- Test conflicting labels, malformed versions, and idempotent reruns.
- Test that Hatch, package runtime, MCP initialization, CLI `--version`, `server.json`, generated manifests, and marketplace metadata agree with the canonical version.
- Test that generated catalog exports preserve unrelated marketplace plugins.
- Run `python -m unittest discover -s tests -v`.
- Run `python -m cities2_mcp.plugin_packages check`.

### Distribution checks

- Build the wheel and source distribution with `python -m build`.
- Inspect both artifacts for version `0.2.0`, the expected skills, and the refreshed 140-page, 1,219-chunk corpus.
- Launch the built Python package and generated plugin launchers, checking their reported version and MCP initialization response.
- Generate the sibling marketplace payload and verify that its source package, plugin manifests, and corpus hashes match Cities2-MCP.

### Client smoke checks

Follow the documented client-install and all-skills smoke process in `evals/reports/`. Install the generated Codex plugin, confirm that its MCP server starts, and exercise `cities2-knowledge`, `cities2-modding`, `cities2-mod-review`, `cities2-mod-debugging`, and `cities2-mod-release`.

For the knowledge smoke check, query an exact page introduced by the refreshed corpus, such as `cities2-docs:patch-1-6-x` or `cities2-docs:map-creation-outside-connections`. This check proves that Codex loaded the new `0.2.0` plugin payload rather than reusing the cached `0.1.9` package.

## Rollout

The implementation pull request carries the first explicit minor bump from `0.1.9` to `0.2.0` and includes the automation, generated metadata, plugin packages, and refreshed corpus already merged to `main`. The pull request receives `release:minor` as an explanatory signal, while the implementation directly establishes `0.2.0` because automation does not exist before that pull request.

After the implementation merges and publishes successfully, ordinary pull requests require no release label and receive patch versions automatically. Maintainers apply `release:minor` or `release:major` only when intentionally changing the corresponding semantic version component.
