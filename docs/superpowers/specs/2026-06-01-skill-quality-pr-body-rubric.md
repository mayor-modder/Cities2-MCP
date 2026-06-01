# Skill-quality PR body rubric

## Purpose

Skill-quality PR bodies should let reviewers understand the change, evidence,
and remaining risk without reading private transcripts or every local note.
Use this rubric for draft PRs created by Codex, Claude, or Antigravity during
the skill-quality program.

Keep PRs narrow. If a finding does not belong to the linked issue, open or
reference a follow-up issue instead of adding unrelated scope to the PR.

## Required sections

### Summary

Name the user-facing or agent-facing behavior that changed. Keep this to the
smallest useful list of concrete changes.

### Evidence

State how the branch proves the issue was addressed. Include only public-safe
summaries:

- linked issue number and scope;
- relevant pressure-test name when one applies;
- baseline failure source or reason no live baseline applies;
- passing retest or manual evidence summary when behavior changed;
- local self-review result;
- privacy scan result for repo-visible and public GitHub text.

Do not paste raw private transcripts, private evidence locations, local paths,
or private tool output into the PR body.

### Verification

List the exact local commands that were run and their pass/fail summaries. Use
the documented gates for the touched files:

- code or package changes: `python -m unittest discover -s tests -v`;
- plugin payload changes: `python -m cities2_mcp.plugin_packages check`;
- skill behavior changes: relevant pressure tests under
  `docs/superpowers/pressure-tests/cs2-modding-quality/`;
- documentation-only changes: unit tests plus any focused text or privacy scan
  that proves the changed documentation is safe to publish.

### Residual risk

Call out what the branch does not prove. Examples:

- a pressure-test document was added but not yet exercised as a live transcript;
- a client install gate still needs Antigravity validation;
- a generated payload was not touched because the branch is documentation-only;
- an out-of-scope finding was moved to a separate issue.

## Closing and authorship

Use `Closes #NN` only when the PR fully resolves that issue. Use `Refs #NN` for
parent program issues or related follow-ups.

When creating, editing, or commenting on a PR, include the required co-author
line at the bottom of the public text:

```text
*Co-authored by Codex.*
```

Use the acting agent's name in that line.

## Size guardrail

Keep each PR small enough to review in one sitting. If the diff approaches the
program limit or starts mixing unrelated issue scopes, stop and split the work
before opening or updating the PR.
