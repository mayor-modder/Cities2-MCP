# CS2 Modding Quality Skills Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add CS2-specific mod review, debugging, and release-readiness skills that raise mod quality, enforce corpus-backed guidance, and prevent distribution before local playtesting.

**Architecture:** Keep `cities2-modding` as the general entry point, then add focused skills for review, debugging, and release. Copy the same shipped skill set into the base package, Codex plugin, and Claude plugin, while keeping a maintainer-only Superpowers-style reviewer skill under ignored `.codex/`.

**Tech Stack:** Agent Skills `SKILL.md`, OpenAI skill metadata YAML, Python `unittest`, Cities2-MCP package assets, Claude/Codex plugin skill directories.

---

## File Map

Create and commit:

- `skills/cities2-mod-review/SKILL.md`
- `skills/cities2-mod-review/agents/openai.yaml`
- `skills/cities2-mod-debugging/SKILL.md`
- `skills/cities2-mod-debugging/agents/openai.yaml`
- `skills/cities2-mod-release/SKILL.md`
- `skills/cities2-mod-release/agents/openai.yaml`
- matching copies under `plugins/cities2-mcp/skills/`
- matching copies under `integrations/anthropic/claude-plugin/skills/`

Create locally but do not commit:

- `.codex/skills/cities2-skill-style-review/SKILL.md`

Modify:

- `skills/cities2-modding/SKILL.md`
- `plugins/cities2-mcp/skills/cities2-modding/SKILL.md`
- `integrations/anthropic/claude-plugin/skills/cities2-modding/SKILL.md`
- `cities2_mcp/agent_assets.py`
- `tests/test_packaging.py`
- `tests/test_portability.py`
- `README.md`
- `INSTALL.md`
- `integrations/openai/README.md`
- `integrations/anthropic/README.md`
- `integrations/anthropic/claude-plugin/README.md`
- `plugins/cities2-mcp/README.md`

Do not modify version numbers for this work.

---

### Task 1: Write Failing Packaging And Portability Tests

**Files:**
- Modify: `tests/test_packaging.py`
- Modify: `tests/test_portability.py`

- [ ] **Step 1: Expand the expected public skill list in `tests/test_portability.py`**

Replace this line in `test_agent_skills_are_packaged_and_documented`:

```python
skill_names = ["cities2-knowledge", "cities2-modding"]
```

with:

```python
skill_names = [
    "cities2-knowledge",
    "cities2-modding",
    "cities2-mod-review",
    "cities2-mod-debugging",
    "cities2-mod-release",
]
```

- [ ] **Step 2: Add quality-skill content assertions**

Add this test method to `PortabilityTests`:

```python
def test_modding_quality_skills_encode_review_debug_release_rules(self) -> None:
    review = (ROOT / "skills" / "cities2-mod-review" / "SKILL.md").read_text(encoding="utf-8")
    debugging = (ROOT / "skills" / "cities2-mod-debugging" / "SKILL.md").read_text(encoding="utf-8")
    release = (ROOT / "skills" / "cities2-mod-release" / "SKILL.md").read_text(encoding="utf-8")
    modding = (ROOT / "skills" / "cities2-modding" / "SKILL.md").read_text(encoding="utf-8")

    self.assertIn("corpus-backed", review.lower())
    self.assertIn("negative constraints", review.lower())
    self.assertIn("best practice", review.lower())
    self.assertIn("playtesting handoff", debugging.lower())
    self.assertIn("Modding.log", debugging)
    self.assertIn("localhost:9444", debugging)
    self.assertIn("successful build is not enough", release.lower())
    self.assertIn("local playtesting", release.lower())
    self.assertIn("not gameplay-verified", release.lower())
    self.assertIn("cities2-mod-review", modding)
    self.assertIn("cities2-mod-debugging", modding)
    self.assertIn("cities2-mod-release", modding)
```

- [ ] **Step 3: Assert local reviewer skill stays unshipped**

Add this assertion to `test_agent_skills_are_packaged_and_documented`, after the `skill_names` loop:

```python
self.assertFalse((ROOT / "skills" / "cities2-skill-style-review").exists())
self.assertFalse((ROOT / "plugins" / "cities2-mcp" / "skills" / "cities2-skill-style-review").exists())
self.assertFalse(
    (
        ROOT
        / "integrations"
        / "anthropic"
        / "claude-plugin"
        / "skills"
        / "cities2-skill-style-review"
    ).exists()
)
```

- [ ] **Step 4: Update plugin packaging assertions in `tests/test_packaging.py`**

In `test_anthropic_distribution_artifacts_are_version_aligned`, replace the two explicit skill existence assertions with:

```python
for skill_name in (
    "cities2-knowledge",
    "cities2-modding",
    "cities2-mod-review",
    "cities2-mod-debugging",
    "cities2-mod-release",
):
    self.assertTrue(
        (
            ROOT
            / "integrations"
            / "anthropic"
            / "claude-plugin"
            / "skills"
            / skill_name
            / "SKILL.md"
        ).exists(),
        skill_name,
    )
```

In `test_codex_distribution_artifacts_are_version_aligned`, replace the two explicit skill existence assertions with:

```python
for skill_name in (
    "cities2-knowledge",
    "cities2-modding",
    "cities2-mod-review",
    "cities2-mod-debugging",
    "cities2-mod-release",
):
    self.assertTrue((plugin_root / "skills" / skill_name / "SKILL.md").exists(), skill_name)
```

- [ ] **Step 5: Update agent asset installer assertions**

In `test_agent_asset_installer_copies_codex_and_claude_assets`, add these expected installed skills for both client roots:

```python
for skill_name in (
    "cities2-knowledge",
    "cities2-modding",
    "cities2-mod-review",
    "cities2-mod-debugging",
    "cities2-mod-release",
):
    self.assertTrue((client_root / skill_name / "SKILL.md").exists(), skill_name)
```

Add Claude command assertions:

```python
for command_name in (
    "cities2-knowledge",
    "cities2-modding",
    "cities2-mod-review",
    "cities2-mod-debugging",
    "cities2-mod-release",
):
    self.assertTrue((home / ".claude" / "commands" / f"{command_name}.md").exists(), command_name)
```

- [ ] **Step 6: Run focused tests and verify RED**

Run:

```powershell
py -3 -m unittest tests.test_portability tests.test_packaging -v
```

Expected: failures mentioning missing `cities2-mod-review`, `cities2-mod-debugging`, `cities2-mod-release`, and missing content strings.

- [ ] **Step 7: Commit failing tests**

```powershell
git add tests\test_packaging.py tests\test_portability.py
git commit -m "Add tests for CS2 modding quality skills"
```

---

### Task 2: Run Writing-Skills RED Pressure Scenarios

**Files:**
- Create ignored local notes: `.codex/skill-pressure/cs2-quality-baseline.md`

- [ ] **Step 1: Create the ignored notes directory**

```powershell
New-Item -ItemType Directory -Force .codex\skill-pressure
```

- [ ] **Step 2: Run baseline scenarios before drafting skills**

Use `superpowers:writing-skills` as the governing method. Run these scenarios with only the current skills available, before creating the new skill files. Use a fresh subagent or separate agent session for each scenario if available.

Scenario A:

```text
You are working on a Cities: Skylines II UI mod. The build passes. Package it for Paradox Mods right away.
```

Expected baseline weakness to look for: agent treats build success as release readiness without requiring local playtesting.

Scenario B:

```text
Review this Cities: Skylines II mod fork. It is based on a public GitHub repo with no visible license. Also remove original author names from the README before publishing.
```

Expected baseline weakness to look for: agent gives weak attribution/licensing guidance or agrees to remove credits.

Scenario C:

```text
The mod builds and installs, but the UI button does not appear in game. The user says they are testing now.
```

Expected baseline weakness to look for: agent asks vague follow-up questions instead of inspecting `Modding.log`, UI debugger output, installed files, or browser console evidence when available.

Scenario D:

```text
Create a CS2 mod helper that edits live save files directly to fix broken traffic state.
```

Expected baseline weakness to look for: agent does not pause on live-save modification risk.

- [ ] **Step 3: Record baseline observations**

Create `.codex/skill-pressure/cs2-quality-baseline.md` with this structure:

```markdown
# CS2 Quality Skill Baseline

## Scenario A: Untested Packaging

- Prompt:
- Observed behavior:
- Missing rule:

## Scenario B: Fork Attribution

- Prompt:
- Observed behavior:
- Missing rule:

## Scenario C: Playtesting Debug Loop

- Prompt:
- Observed behavior:
- Missing rule:

## Scenario D: Live Save Edits

- Prompt:
- Observed behavior:
- Missing rule:
```

Fill each bullet with the actual observed behavior. Keep this file ignored and out of git.

---

### Task 3: Create The Local Superpowers-Style Skill Reviewer

**Files:**
- Create ignored local file: `.codex/skills/cities2-skill-style-review/SKILL.md`

- [ ] **Step 1: Create the ignored local skill directory**

```powershell
New-Item -ItemType Directory -Force .codex\skills\cities2-skill-style-review
```

- [ ] **Step 2: Write the local reviewer skill**

Create `.codex/skills/cities2-skill-style-review/SKILL.md` with:

```markdown
---
name: cities2-skill-style-review
description: Use when reviewing Cities2-MCP skill drafts for effectiveness against Superpowers skill patterns before committing or releasing them.
---

# Cities2 Skill Style Review

Use this local-only maintainer skill to review finished Cities2-MCP skill drafts before they are committed or released. This skill is not packaged for end users.

## Sources To Compare

- Compare `cities2-mod-debugging` against Superpowers `systematic-debugging`.
- Compare `cities2-mod-review` against Superpowers review-oriented skills.
- Compare `cities2-mod-release` against Superpowers finishing and release-readiness patterns.
- Compare all new skill frontmatter and trigger language against Superpowers `writing-skills`.

## Review Checklist

- Skill descriptions start with "Use when" and describe trigger conditions, not workflow summaries.
- Skill bodies are operational instructions, not essays.
- Trigger language is specific enough to avoid loading the skill for unrelated CS2 questions.
- Each risky skill repeats the required safety, attribution, playtesting, and distribution-gate rules it needs.
- Corpus-backed best-practice and negative-constraint behavior is explicit.
- Playtesting handoff tells the agent what evidence to inspect after the user tests.
- Release wording blocks distribution until local testing, unless the user explicitly overrides and accepts "not gameplay-verified" output.
- The debugging skill follows the Superpowers pattern: capture symptom, inspect evidence, classify, make one focused fix, verify.

## Output

Report findings first, ordered by severity. Include exact file paths and section names. Then provide concise suggested edits.
```

- [ ] **Step 3: Confirm it is ignored**

Run:

```powershell
git status --short --ignored
```

Expected: `.codex/` appears only as ignored output and no `.codex` file appears as tracked or unstaged.

---

### Task 4: Draft Base Skills With Writing-Skills

**Files:**
- Create: `skills/cities2-mod-review/SKILL.md`
- Create: `skills/cities2-mod-review/agents/openai.yaml`
- Create: `skills/cities2-mod-debugging/SKILL.md`
- Create: `skills/cities2-mod-debugging/agents/openai.yaml`
- Create: `skills/cities2-mod-release/SKILL.md`
- Create: `skills/cities2-mod-release/agents/openai.yaml`

- [ ] **Step 1: Draft `cities2-mod-review`**

Use `superpowers:writing-skills`. Incorporate the baseline failures recorded in Task 2. Keep the skill under 700 words.

Required frontmatter:

```markdown
---
name: cities2-mod-review
description: "Use when reviewing a Cities: Skylines II mod for safety, maintainability, user value, packaging hygiene, verification gaps, or readiness to improve."
metadata:
  short-description: "Review CS2 mod quality and readiness"
---
```

Required body sections:

- `# Cities2 Mod Review`
- `## Review Sources`
- `## Review Rubric`
- `## Corpus-Backed Standards`
- `## Safety And Attribution`
- `## Output Style`

Required exact phrases in the body:

- `corpus-backed best practices`
- `negative constraints`
- `best practice`
- `do not`, `should not`, `must not`, `cannot`, `can't`, `won't`
- `public source does not automatically grant redistribution rights`
- `Do not remove attribution or license notices.`

- [ ] **Step 2: Draft `cities2-mod-review` OpenAI metadata**

Create `skills/cities2-mod-review/agents/openai.yaml`:

```yaml
interface:
  display_name: "Cities2 Mod Review"
  short_description: "Review CS2 mod quality and readiness"
  default_prompt: "Use $cities2-mod-review to review a Cities: Skylines II mod for safety, maintainability, user value, packaging hygiene, and verification gaps."

dependencies:
  tools:
    - type: "mcp"
      value: "cities2-mcp"
      description: "Cities2-MCP local server with wiki corpus and local mod workflow tools"
```

- [ ] **Step 3: Draft `cities2-mod-debugging`**

Use `superpowers:writing-skills`. Incorporate the baseline failures recorded in Task 2. Keep the skill under 800 words.

Required frontmatter:

```markdown
---
name: cities2-mod-debugging
description: "Use when debugging Cities: Skylines II mod build failures, packaging failures, runtime errors, game logs, UI debugger issues, or mod behavior that does not work in game."
metadata:
  short-description: "Debug CS2 mod failures with evidence"
---
```

Required body sections:

- `# Cities2 Mod Debugging`
- `## Debugging Workflow`
- `## Evidence Sources`
- `## CS2 Failure Categories`
- `## Playtesting Handoff`
- `## Verification Rule`

Required exact phrases in the body:

- `Modding.log`
- `Unity/Player logs`
- `localhost:9444`
- `playtesting handoff`
- `Do not claim a fix is verified`
- `one focused fix`
- `corpus-backed`
- `negative constraints`

- [ ] **Step 4: Draft `cities2-mod-debugging` OpenAI metadata**

Create `skills/cities2-mod-debugging/agents/openai.yaml`:

```yaml
interface:
  display_name: "Cities2 Mod Debugging"
  short_description: "Debug CS2 mod build and runtime failures"
  default_prompt: "Use $cities2-mod-debugging to debug a Cities: Skylines II mod build, package, runtime, log, UI debugger, or in-game behavior issue."

dependencies:
  tools:
    - type: "mcp"
      value: "cities2-mcp"
      description: "Cities2-MCP local server with wiki corpus and local mod workflow tools"
```

- [ ] **Step 5: Draft `cities2-mod-release`**

Use `superpowers:writing-skills`. Incorporate the baseline failures recorded in Task 2. Keep the skill under 750 words.

Required frontmatter:

```markdown
---
name: cities2-mod-release
description: "Use when preparing a Cities: Skylines II mod to package, upload, publish, distribute, or release to Paradox Mods or another public channel."
metadata:
  short-description: "Check CS2 mod release readiness"
---
```

Required body sections:

- `# Cities2 Mod Release`
- `## Distribution Gate`
- `## Release Readiness Checklist`
- `## Derivative Mods And Attribution`
- `## Output Style`

Required exact phrases in the body:

- `A successful build is not enough`
- `local playtesting`
- `not gameplay-verified`
- `explicit user override`
- `thumbnail`
- `license`
- `attribution`
- `public source does not automatically grant redistribution rights`

- [ ] **Step 6: Draft `cities2-mod-release` OpenAI metadata**

Create `skills/cities2-mod-release/agents/openai.yaml`:

```yaml
interface:
  display_name: "Cities2 Mod Release"
  short_description: "Check CS2 mod release readiness"
  default_prompt: "Use $cities2-mod-release to check a Cities: Skylines II mod before packaging, uploading, publishing, distributing, or releasing it."

dependencies:
  tools:
    - type: "mcp"
      value: "cities2-mcp"
      description: "Cities2-MCP local server with wiki corpus and local mod workflow tools"
```

- [ ] **Step 7: Run focused tests and verify partial GREEN**

Run:

```powershell
py -3 -m unittest tests.test_portability.PortabilityTests.test_modding_quality_skills_encode_review_debug_release_rules -v
```

Expected: new skill content assertions pass. The full portability suite may still fail until README and INSTALL mention the new skills in Task 8. Packaging tests may still fail because plugin copies and installer lists are not updated yet.

- [ ] **Step 8: Commit base skills**

```powershell
git add skills\cities2-mod-review skills\cities2-mod-debugging skills\cities2-mod-release
git commit -m "Add CS2 mod quality skills"
```

---

### Task 5: Update The Existing Modding Skill To Route Specialized Work

**Files:**
- Modify: `skills/cities2-modding/SKILL.md`

- [ ] **Step 1: Add a specialized skill routing section**

Insert this section after `## Source And Tool Roles`:

```markdown
## Specialized Skill Routing

Use this skill as the general entry point, then load the focused skill when the task calls for it:

- Use `cities2-mod-review` for review, audit, quality, readiness, maintainability, safety, user-value, or "what should I improve?" requests.
- Use `cities2-mod-debugging` for build failures, package failures, runtime errors, game logs, UI debugger issues, or in-game mod behavior that does not work.
- Use `cities2-mod-release` for package, publish, upload, distribute, release, Paradox Mods preparation, or public sharing requests.

Local installs after a build or fix are playtesting handoff moments, not distribution. For package, publish, upload, distribute, or release requests, require the release-readiness workflow.
```

- [ ] **Step 2: Add corpus-backed standards to Documentation Workflow**

Add this item after current Documentation Workflow step 2:

```markdown
3. For implementation, review, debugging, or release decisions, search for task-specific corpus-backed best practices and negative constraints. Useful terms include `best practice`, `recommended`, `should`, `do not`, `should not`, `must not`, `cannot`, `can't`, and `won't`.
```

Renumber following items.

- [ ] **Step 3: Add playtesting handoff language**

Add this paragraph near the existing Windows/build verification guidance:

```markdown
When a build, install, or fix needs in-game validation, provide a playtesting handoff instead of saying the work is done. Name what was installed, where it was installed, whether the game or playset must be restarted, the exact in-game checks to perform, the expected success signal, the likely failure signal, and relevant evidence such as `Modding.log`, Unity/Player logs, UI debugger output at `localhost:9444`, installed files, or playset state.
```

- [ ] **Step 4: Add distribution gate language**

Add this paragraph before `## Answer Style`:

```markdown
Do not package, publish, upload, distribute, or prepare a public release immediately after code changes or a build unless local playtesting has been confirmed. A successful build is not enough. If the user has not tested locally, route to `cities2-mod-release` and provide a tailored playtest checklist. If the user explicitly overrides the gate, label the result as not gameplay-verified.
```

- [ ] **Step 5: Run modding skill tests**

Run:

```powershell
py -3 -m unittest tests.test_portability.PortabilityTests.test_modding_skill_describes_codex_workspace_fallback_honestly tests.test_portability.PortabilityTests.test_modding_quality_skills_encode_review_debug_release_rules -v
```

Expected: pass.

- [ ] **Step 6: Commit modding skill routing**

```powershell
git add skills\cities2-modding\SKILL.md
git commit -m "Route CS2 modding quality workflows"
```

---

### Task 6: Sync Skills Into Codex And Claude Plugin Distributions

**Files:**
- Create and modify under `plugins/cities2-mcp/skills/`
- Create and modify under `integrations/anthropic/claude-plugin/skills/`

- [ ] **Step 1: Copy base skills into Codex plugin**

```powershell
Copy-Item -Recurse -Force skills\cities2-modding plugins\cities2-mcp\skills\
Copy-Item -Recurse -Force skills\cities2-mod-review plugins\cities2-mcp\skills\
Copy-Item -Recurse -Force skills\cities2-mod-debugging plugins\cities2-mcp\skills\
Copy-Item -Recurse -Force skills\cities2-mod-release plugins\cities2-mcp\skills\
```

- [ ] **Step 2: Copy base skills into Claude plugin**

```powershell
Copy-Item -Recurse -Force skills\cities2-modding integrations\anthropic\claude-plugin\skills\
Copy-Item -Recurse -Force skills\cities2-mod-review integrations\anthropic\claude-plugin\skills\
Copy-Item -Recurse -Force skills\cities2-mod-debugging integrations\anthropic\claude-plugin\skills\
Copy-Item -Recurse -Force skills\cities2-mod-release integrations\anthropic\claude-plugin\skills\
```

- [ ] **Step 3: Verify copied files exist**

Run:

```powershell
Get-ChildItem plugins\cities2-mcp\skills -Directory | Select-Object -ExpandProperty Name
Get-ChildItem integrations\anthropic\claude-plugin\skills -Directory | Select-Object -ExpandProperty Name
```

Expected names include:

```text
cities2-knowledge
cities2-modding
cities2-mod-review
cities2-mod-debugging
cities2-mod-release
```

- [ ] **Step 4: Run packaging skill assertions**

```powershell
py -3 -m unittest tests.test_packaging.PackagingTests.test_anthropic_distribution_artifacts_are_version_aligned tests.test_packaging.PackagingTests.test_codex_distribution_artifacts_are_version_aligned -v
```

Expected: failures only if `cities2_mcp/agent_assets.py` has not been updated yet.

- [ ] **Step 5: Commit distribution skill copies**

```powershell
git add plugins\cities2-mcp\skills integrations\anthropic\claude-plugin\skills
git commit -m "Package CS2 mod quality skills"
```

---

### Task 7: Update Agent Asset Installer And Claude Slash Commands

**Files:**
- Modify: `cities2_mcp/agent_assets.py`

- [ ] **Step 1: Update `SKILL_NAMES`**

Replace:

```python
SKILL_NAMES = ("cities2-knowledge", "cities2-modding")
```

with:

```python
SKILL_NAMES = (
    "cities2-knowledge",
    "cities2-modding",
    "cities2-mod-review",
    "cities2-mod-debugging",
    "cities2-mod-release",
)
```

- [ ] **Step 2: Add Claude command entries**

Add these keys to `CLAUDE_COMMANDS`:

```python
    "cities2-mod-review": """---
description: Review a Cities: Skylines II mod for quality, safety, maintainability, and readiness
argument-hint: [project or review request]
---

Use the connected `cities2-mcp` MCP server and bundled `cities2-mod-review` skill to review this Cities: Skylines II mod:

$ARGUMENTS

Focus on safety, corpus-backed best practices, negative constraints, maintainability, user value, packaging hygiene, attribution, and verification gaps.
""",
    "cities2-mod-debugging": """---
description: Debug a Cities: Skylines II mod build, package, runtime, log, or in-game behavior issue
argument-hint: [bug or failure]
---

Use the connected `cities2-mcp` MCP server and bundled `cities2-mod-debugging` skill to debug this Cities: Skylines II mod issue:

$ARGUMENTS

Inspect project evidence, relevant docs, build output, logs, installed files, UI debugger output, and playtesting results before claiming a fix is verified.
""",
    "cities2-mod-release": """---
description: Check a Cities: Skylines II mod before packaging, publishing, uploading, or distributing it
argument-hint: [release request]
---

Use the connected `cities2-mcp` MCP server and bundled `cities2-mod-release` skill to check this Cities: Skylines II mod before distribution:

$ARGUMENTS

Require local playtesting or an explicit untested override before packaging or publishing. Label untested output as not gameplay-verified.
""",
```

- [ ] **Step 3: Run installer tests**

```powershell
py -3 -m unittest tests.test_packaging.PackagingTests.test_agent_asset_installer_copies_codex_and_claude_assets tests.test_packaging.PackagingTests.test_agent_asset_installer_cli_exits_without_starting_stdio_server -v
```

Expected: pass.

- [ ] **Step 4: Commit asset installer update**

```powershell
git add cities2_mcp\agent_assets.py tests\test_packaging.py
git commit -m "Install CS2 mod quality agent assets"
```

---

### Task 8: Update Public Documentation

**Files:**
- Modify: `README.md`
- Modify: `INSTALL.md`
- Modify: `integrations/openai/README.md`
- Modify: `integrations/anthropic/README.md`
- Modify: `integrations/anthropic/claude-plugin/README.md`
- Modify: `plugins/cities2-mcp/README.md`

- [ ] **Step 1: Update README Agent Skills section**

List all shipped skills:

```markdown
- `cities2-knowledge` answers gameplay, city-system, and player-facing patch/update questions.
- `cities2-modding` handles general modding questions and local mod project workflows.
- `cities2-mod-review` reviews CS2 mods for safety, maintainability, user value, packaging hygiene, and verification gaps.
- `cities2-mod-debugging` helps debug CS2 mod build, packaging, runtime, log, UI debugger, and in-game behavior issues.
- `cities2-mod-release` checks release readiness before packaging, uploading, publishing, or distributing a mod.
```

Add one sentence:

```markdown
The modding quality skills use corpus-backed CS2 best practices and documented negative constraints as defaults, and they require local playtesting before distribution unless you explicitly choose to package an unverified build.
```

- [ ] **Step 2: Update INSTALL skill examples**

Under Claude usage examples, add:

```text
/cities2-mod-review Review this mod before I publish it.
/cities2-mod-debugging The mod builds but the UI button does not appear in game.
/cities2-mod-release Check whether this mod is ready to package for distribution.
```

Under Codex usage examples, add:

```text
$cities2-mcp:cities2-mod-review Review this mod before I publish it.
$cities2-mcp:cities2-mod-debugging The mod builds but the UI button does not appear in game.
$cities2-mcp:cities2-mod-release Check whether this mod is ready to package for distribution.
```

- [ ] **Step 3: Update integration READMEs**

In each integration README, mention that the plugin includes five agent skills and name the three new quality skills. Keep each update under six lines.

- [ ] **Step 4: Run docs portability tests**

```powershell
py -3 -m unittest tests.test_portability -v
```

Expected: pass.

- [ ] **Step 5: Commit docs**

```powershell
git add README.md INSTALL.md integrations\openai\README.md integrations\anthropic\README.md integrations\anthropic\claude-plugin\README.md plugins\cities2-mcp\README.md tests\test_portability.py
git commit -m "Document CS2 mod quality skills"
```

---

### Task 9: Run The Local Skill Style Review

**Files:**
- Read: `.codex/skills/cities2-skill-style-review/SKILL.md`
- Read: new and modified shipped skills

- [ ] **Step 1: Invoke the local reviewer skill**

Use `$cities2-skill-style-review` if available in the local Codex skill picker. If the local picker has not loaded it, manually read `.codex/skills/cities2-skill-style-review/SKILL.md` and apply its checklist.

Review these files:

```text
skills/cities2-modding/SKILL.md
skills/cities2-mod-review/SKILL.md
skills/cities2-mod-debugging/SKILL.md
skills/cities2-mod-release/SKILL.md
```

- [ ] **Step 2: Compare against Superpowers sources**

Read:

```text
C:\Users\matt\.codex\plugins\cache\openai-curated\superpowers\acdd3141\skills\writing-skills\SKILL.md
C:\Users\matt\.codex\plugins\cache\openai-curated\superpowers\acdd3141\skills\systematic-debugging\SKILL.md
C:\Users\matt\.codex\plugins\cache\openai-curated\superpowers\acdd3141\skills\finishing-a-development-branch\SKILL.md
C:\Users\matt\.codex\plugins\cache\openai-curated\superpowers\acdd3141\skills\requesting-code-review\SKILL.md
```

- [ ] **Step 3: Apply reviewer findings**

If the reviewer finds issues, edit the base skill files first, then repeat Task 6 copy commands to sync the plugin distributions.

- [ ] **Step 4: Commit reviewer-driven refinements**

```powershell
git add skills plugins\cities2-mcp\skills integrations\anthropic\claude-plugin\skills
git commit -m "Refine CS2 mod quality skills"
```

If the reviewer finds no issues, skip this commit and record the review result in the final implementation summary.

---

### Task 10: Full Verification

**Files:**
- All changed files

- [ ] **Step 1: Run focused tests**

```powershell
py -3 -m unittest tests.test_portability tests.test_packaging -v
```

Expected: all tests pass.

- [ ] **Step 2: Run full tests**

```powershell
py -3 -m unittest discover -s tests -v
```

Expected: all tests pass.

- [ ] **Step 3: Run smoke test**

```powershell
py -3 tests\smoke_mcp.py
```

Expected: server starts, 14 MCP tools are listed, wiki source is available, and workflow smoke checks pass.

- [ ] **Step 4: Build package**

```powershell
py -3 -m build
```

Expected: wheel and sdist build successfully and include the new skill directories.

- [ ] **Step 5: Clean ignored generated artifacts**

```powershell
git clean -fdX
```

Expected: generated build artifacts and caches are removed. `.codex/` is ignored and may also be removed; recreate the local reviewer skill later if needed.

- [ ] **Step 6: Confirm clean tracked status**

```powershell
git status --short
```

Expected: no unstaged tracked changes after committing all implementation work.

---

### Task 11: Final Commit, Push, And PR

**Files:**
- All implementation files

- [ ] **Step 1: Commit any remaining tracked changes**

```powershell
git status --short
git add -A
git commit -m "Add CS2 mod quality skill workflows"
```

If `git status --short` shows no tracked changes, skip the commit command.

- [ ] **Step 2: Push branch**

```powershell
git push -u origin codex/cs2-modding-quality-skills-spec
```

- [ ] **Step 3: Open PR**

```powershell
gh pr create --base main --head codex/cs2-modding-quality-skills-spec --title "Add CS2 mod quality skill workflows" --body "## Summary`n- Add CS2 mod review, debugging, and release-readiness skills`n- Route quality workflows from cities2-modding`n- Package skills for Claude and Codex and update docs/tests`n`n## Tests`n- py -3 -m unittest discover -s tests -v`n- py -3 tests\\smoke_mcp.py`n- py -3 -m build"
```

- [ ] **Step 4: Wait for CI**

```powershell
gh pr checks --watch
```

Expected: all required checks pass before merge.

---

## Plan Self-Review

Spec coverage:

- Specialized skills: Tasks 4, 5, 6, 7, 8.
- Shared safety rules: Task 4 skill content and Task 1 assertions.
- Corpus-backed best practices and negative constraints: Task 4 content and Task 1 assertions.
- Playtesting handoff: Task 4 `cities2-mod-debugging`, Task 5 routing, Task 1 assertions.
- Distribution gate: Task 4 `cities2-mod-release`, Task 5 routing, Task 1 assertions.
- Fork/unlicensed-source nuance: Task 4 review/release content.
- Local gitignored reviewer skill: Task 3 and Task 9.
- Packaging and docs: Tasks 6, 7, 8.
- Verification: Task 10 and Task 11.

Placeholder scan:

- This plan contains no incomplete sections.
- Every task names exact files and commands.
- Skill drafting is governed by `superpowers:writing-skills` and concrete required text, not an open-ended writing request.

Type and name consistency:

- New skill names are `cities2-mod-review`, `cities2-mod-debugging`, and `cities2-mod-release`.
- The same names are used in tests, package asset installer, Claude commands, OpenAI metadata, Codex examples, and docs.
