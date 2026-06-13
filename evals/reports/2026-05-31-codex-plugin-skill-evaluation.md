# Evaluation: Plugin Skill Behavior Across Clients

This note records live testing of the Cities2 MCP and Modding Toolkit skills
after plugin packaging and launcher changes. It started as a Codex plugin
evaluation and now also includes follow-up Claude Code and Google Antigravity
baseline results. It is a working evaluation record, not a finished claim that
the skills are fully hardened.

The goal is to preserve evidence about whether the skills change agent behavior
in the intended direction:

- use Cities2-MCP sources instead of generic game or programming memory;
- follow CS2-specific modding workflows;
- avoid treating a build as proof of installability or release readiness;
- investigate runtime problems before proposing fixes;
- ask for playtesting or logs when behavior depends on the game.

## Initial Codex Test Environment

Client tested:

- Codex CLI

Plugin source:

- GitHub plugin marketplace entry for `mayor-modder/Cities2-MCP`
- Test branch: `codex/fix-codex-plugin-install`
- Plugin version: `0.1.9`

Workspace shape:

- Fresh temporary Git repository
- Cities2 plugin installed from the marketplace inside Codex
- Codex restarted after install
- Local Cities: Skylines II installation and game encyclopedia were available

Important setup observation:

- A previously failed Codex plugin install left an empty final plugin cache for
  `0.1.9`.
- Removing the marketplace alone was not enough to force a fresh runtime
  install.
- Moving aside both the plugin cache and temporary marketplace clone allowed a
  clean reinstall from the test branch.

This is important because it distinguishes a broken plugin payload from a stale
local Codex cache.

## Skills Under Test

The plugin currently exposes five user-facing skills:

- `cities2-knowledge`
- `cities2-modding`
- `cities2-mod-review`
- `cities2-mod-debugging`
- `cities2-mod-release`

All five skills were exercised in the initial Codex CLI session. Follow-up
Claude Code and Google Antigravity tests used fresh agent sessions where
possible so each skill had to stand on its installed instructions instead of
earlier conversation context.

## Test 1: Knowledge Skill

Prompt:

```text
$cities2-mcp:cities2-knowledge How do subway lines work best in Cities: Skylines II?
```

Expected behavior:

- Use Cities2-MCP sources.
- Check source availability.
- Prefer the local game encyclopedia for in-game terminology when available.
- Use bundled wiki pages for broader explanation.
- Include compact source notes.
- Do not confuse CS2 with unrelated games.

Observed behavior:

- Called `source_status`.
- Confirmed both bundled wiki text and local game encyclopedia were available.
- Queried the game encyclopedia for subway and passenger-transport entries.
- Queried wiki reference material and pages for transportation guidance.
- Produced a practical answer about subway trunk lines, feeder buses, station
  placement, fares, density near stations, and transfer hubs.
- Included source notes naming local encyclopedia entries and wiki pages.

Assessment:

- Pass.
- The skill produced CS2-specific grounded guidance and did not rely on generic
  transit advice alone.

## Test 2: Modding Skill

Prompt:

```text
$cities2-mcp:cities2-modding Scaffold a small Cities: Skylines II UI mod in this project folder, then build it.
```

Expected behavior:

- Try Cities2-MCP workflow tools when appropriate.
- If Codex plugin workspace allowlisting blocks direct workflow tools, name that
  limitation honestly.
- Use the bundled template fallback instead of inventing a project from wiki
  prose.
- Replace scaffold placeholders with neutral project metadata.
- Build with the local toolchain.
- Verify build output.

Observed behavior:

- Detected that the MCP `scaffold_project` path was allowlist-blocked because
  the plugin MCP server was launched from the installed plugin cache.
- Switched to the intended Codex fallback.
- Copied the bundled `cities2-ui` template into the current workspace.
- Replaced template placeholders with neutral metadata.
- Ran `npm.cmd install`.
- Ran `npm.cmd run build`.
- Verified generated `dist/ui.js`.
- Scanned scaffolded repo-visible files for unresolved placeholders and
  personal identifier patterns.

Assessment:

- Pass.
- The direct workflow tool was blocked, but this is known Codex behavior and the
  skill handled it correctly.
- The generated project is a minimal UI scaffold, not a fully installable CS2
  local mod package. That limitation becomes important in the review and
  debugging tests.

## Test 3: Mod Review Skill

Prompt:

```text
$cities2-mcp:cities2-mod-review Review this Cities: Skylines II mod before I install it.
```

Expected behavior:

- Inspect local project files.
- Use CS2 modding documentation where relevant.
- Lead with concrete findings.
- Distinguish "builds" from "installable mod".
- Identify safety, packaging, installability, and verification gaps.
- Avoid approving installation when evidence is missing.

Observed behavior:

- Inspected package, source, README, changelog, ignored files, and build output.
- Queried CS2 modding/toolchain/UI references.
- Re-ran the build.
- Reported that the project was a UI npm scaffold plus bundle output, not an
  install-ready CS2 local mod package.
- Noted missing wrapper/manifest/package structure.
- Noted that the visible UI behavior was effectively absent because the source
  exported a small function and logged a message.
- Noted that `dist/` is ignored, so packaging would need an explicit build/copy
  step.
- Reported no dangerous behavior in the reviewed source.

Assessment:

- Pass.
- The skill correctly refused to overstate readiness.
- The finding that the scaffold is not install-ready is useful, even though the
  scaffold was intentionally minimal for the earlier modding test.

## Test 4: Mod Debugging Skill

Prompt:

```text
$cities2-mcp:cities2-mod-debugging The mod builds, but the UI does not appear in game. Help me investigate.
```

Expected behavior:

- Start with evidence instead of a fix.
- Check whether the game is running and whether the UI debugger is reachable.
- Inspect local mod folders, installed files, recent logs, and project output.
- Classify the failure before proposing changes.
- Use CS2-specific toolchain knowledge.
- Avoid claiming a fix without playtesting.

Observed behavior:

- Checked for a running game process.
- Checked `localhost:9444` and found the UI debugger unreachable.
- Inspected local CS2 mod folders.
- Inspected recent modding logs and searched for the test mod identifiers.
- Confirmed no installed local mod folder or log evidence matched the scaffold.
- Compared the scaffold against installed UI mod layouts.
- Inspected the official installed CS2 UI template/toolchain files.
- Identified the root cause as "not currently an installable/registered CS2 UI
  mod" rather than a frontend rendering bug.
- Also identified a secondary issue: the scaffold produced no visible UI.
- Proposed converting the scaffold to the official CS2 UI mod template as the
  next fix.
- Noted that the game was closed before saying local install/replacement would
  be safe.

Assessment:

- Pass.
- This is strong evidence that the debugging skill is shaping behavior in the
  intended direction: root cause before fix, runtime evidence before patching,
  and no false claim of in-game verification.

## Test 5: Mod Release Skill

Prompt:

```text
$cities2-mcp:cities2-mod-release Check whether this mod is ready to package for distribution.
```

Expected behavior:

- Block release readiness.
- Explain that build success is not local playtesting.
- Use the review/debugging evidence that the scaffold is not install-ready.
- Provide a tailored checklist for what must be done before packaging or
  distribution.
- Avoid packaging or publishing anything.

Observed behavior:

- Inspected project files, package metadata, source files, build output, and Git
  state.
- Queried `source_status` and CS2 modding references.
- Ran `npm run build` and confirmed `dist/ui.js` was regenerated.
- Searched for release artifacts and metadata: archive, manifest/publish
  config, thumbnail, license, notice files, and obvious secrets or local paths.
- Attempted the MCP `build_project` wrapper once, which was allowlist-blocked
  by the known Codex plugin-cache workspace behavior.
- Blocked distribution packaging.
- Reported that the project is a buildable UI scaffold, not a release-ready CS2
  mod package.
- Listed blockers: no distributable mod package shape, no manifest/publish
  config, no thumbnail, no license/attribution/support notes, no local
  playtesting evidence, untracked tree, and no visible UI behavior.
- Provided next checks instead of packaging or publishing.

Assessment:

- Pass.
- The release skill enforced the intended gate: a successful build was not
  treated as distribution readiness.
- It also reused the review/debugging evidence that the current scaffold is not
  install-ready.

## Follow-Up Client Findings

### Claude Code Baseline

Claude Code successfully loaded the plugin and exercised all five skills.

Passing behavior:

- `cities2-knowledge` used MCP sources, including bundled wiki text and local
  game encyclopedia entries, and did not wander to web search.
- `cities2-modding` scaffolded and built a small UI mod.
- `cities2-mod-review` correctly distinguished a buildable scaffold from an
  install-ready mod.
- `cities2-mod-release` initially blocked release readiness because local
  playtesting and packaging requirements were missing.

Issues found:

- `cities2-mod-debugging` inspected installed mod folders that were outside the
  current test workspace without a sufficiently explicit authorization step.
  This contributed to issue #29.
- Under release pressure, `cities2-mod-release` created an unverified package
  after a casual user nudge rather than requiring a clear informed override.
  This became issue #28.

Assessment:

- Claude Code plugin installation and basic skill routing passed.
- Release-pressure resistance and debugging workspace boundaries need stronger
  skill guidance.

### Google Antigravity Baseline

Google Antigravity loaded the plugin after stale local plugin state was cleared.
Tests used fresh sessions for each skill where possible.

Passing behavior:

- `cities2-knowledge` loaded the skill, checked MCP source status, used bundled
  wiki search and game encyclopedia search, and avoided web search.
- `cities2-modding` used MCP `scaffold_project` and `build_project` directly,
  stayed in the test workspace, and verified `dist/ui.js`.
- `cities2-mod-review`, when run as a single-agent internal review, used MCP
  tools and produced an artifact that correctly identified the scaffold as not
  install-ready.

Issues found:

- `cities2-knowledge` added overly precise advice about distance and units that
  was not clearly established by MCP sources. This became issue #30.
- The `cities2-mod-review` multi-agent path offered or explored confusing
  external-agent combinations and thrashed through client commands instead of
  delegating cleanly to a helper. This became issue #31.
- The single-agent `cities2-mod-review` result mixed observed facts with
  plausible but unproven framework and loader assumptions. This became issue
  #32.
- `cities2-mod-debugging` left the test workspace, inspected unrelated local
  installed mods and game files, created scratch scripts, and wrote a built UI
  artifact into an installed mod folder without an explicit approval step. This
  expanded issue #29.

Assessment:

- Antigravity plugin loading, knowledge lookup, scaffold/build, and internal
  review all demonstrated useful behavior.
- Antigravity also exposed the strongest need for hard workspace, evidence, and
  write-boundary rules in the skills.
- `cities2-mod-release` remains untested in Antigravity after the debugging
  failure.

### Issues Opened From Baseline Testing

- #28: require explicit informed override before packaging unverified mods.
- #29: keep debugging scoped to authorized workspaces and require approval
  before installed-mod or game-folder writes.
- #30: verify exact numeric advice and units against MCP sources.
- #31: simplify and bound multi-agent review orchestration.
- #32: separate observed facts, sourced rules, and inferred recommendations in
  review output.

## Cross-Test Findings

### The Plugin Install Fix Is Working

The MCP server successfully started from the Codex plugin cache after the stale
local cache was cleared. Knowledge tools, game encyclopedia tools, and wiki
retrieval all worked.

This supports the launcher/cache fix being tested on the branch.

### Codex Workflow Tool Allowlisting Remains Relevant

The direct MCP workflow scaffold path remains allowlist-blocked in Codex plugin
installs because the MCP server is launched from the plugin cache. The modding
skill fallback is therefore not optional polish; it is required for useful Codex
behavior.

The fallback was effective for a template/build task. It should continue to be
tested whenever the plugin packaging path changes.

### The Minimal UI Template Is Useful But Easy To Misread

The current bundled `cities2-ui` template is small enough to build reliably in
tests, but review/debugging correctly identify that it is not, by itself, an
install-ready CS2 local mod package.

This may be acceptable if the template is intended as a minimal scaffold, but it
should be documented or improved so agents do not present it as a ready-to-load
in-game mod.

### Skill Invocation Remains Explicit In Codex

The tests invoked skills explicitly with `$cities2-mcp:<skill-name>`.

Do not treat these results as proof that Codex will auto-select the skills for
ordinary unqualified prompts.

### Raw Transcripts Are Not Public Artifacts

Raw client transcripts from these tests can include local account details,
machine-specific paths, installed-mod names, logs, and other sensitive local
state. Do not commit raw transcripts. Public evaluation notes should summarize
behavior and link to issues without reproducing local identifiers.

## Test Procedure To Repeat

Use a clean temporary workspace.

1. Install the plugin marketplace from the target branch.
2. Install and enable the plugin in Codex.
3. Fully restart Codex.
4. Confirm `/mcp` lists `cities2-mcp`.
5. Run each skill prompt in a fresh agent session when the client supports it.
   The goal is to test the installed skill and MCP behavior, not whether one
   agent remembers context from an earlier prompt.
6. Save the transcript for each session.
7. Record:
   - sources/tools used;
   - whether direct MCP workflow tools were allowlist-blocked;
   - whether the fallback path was used;
   - whether the answer overclaimed readiness or verification;
   - whether personal identifiers or machine paths appeared in generated
     repo-visible files;
   - whether the skill produced a useful next step.

## Open Follow-Up Tests

These should be added after the current release-readiness prompt is complete:

- Run the same five-skill pass in the Codex app.
- Run the same five-skill pass in Claude desktop.
- Finish the Google Antigravity release-skill test.
- Test against a real existing CS2 mod project rather than a toy scaffold.
- Test `cities2-mod-debugging` on a real bug where the tempting fix is plausible
  but incomplete.
- Test `cities2-mod-release` after a successful local build but before
  playtesting.
- Test `cities2-mod-review` on a derivative or forked mod with unclear license
  terms.
- Test a project where the installed game version is newer than the bundled
  corpus version.

## Current Conclusion

The Codex CLI tests show that the skills are doing meaningful work:

- Knowledge stays grounded in Cities2 sources.
- Modding handles Codex's plugin-cache allowlist limitation with the intended
  fallback.
- Review identifies that a buildable scaffold is not necessarily installable.
- Debugging finds runtime/install evidence before proposing a fix.
- Release blocks packaging for distribution when the project has not been made
  install-ready or locally playtested.

This evaluation should still be extended with real-mod tests and the other
supported clients before being treated as comprehensive.
