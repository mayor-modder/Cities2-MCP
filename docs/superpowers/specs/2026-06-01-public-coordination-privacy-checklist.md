# Public coordination privacy checklist

## Purpose

Skill-quality agents often need to write public issue bodies, PR bodies, and
coordination comments while using private local evidence. This checklist keeps
those public writes useful without exposing local identifiers or raw private
tool output.

Use it before any public GitHub write that summarizes local testing,
self-review, pressure-test evidence, or dispatcher context.

## Preflight scan

Before posting, scan the exact text that will become public. Treat a hit as a
stop-and-rewrite event, not as something to explain in the public post.

Check for:

- Personal names or standalone usernames.
- Home-directory paths, machine-specific paths, and local URI references.
- Credential-shaped strings, authentication output, and copied command secrets.
- Private evidence folder names, private transcript locations, and dispatcher
  log locations.
- Raw private tool output that contains environment details unrelated to the
  public review.
- Overly specific local setup details that are not needed to understand the
  issue, PR, or verification result.

## Neutral replacements

Use public-safe summaries that preserve the engineering evidence without
preserving the private identifier.

| Private detail type | Public replacement |
| --- | --- |
| Local home-directory path | `local workspace path` or `private evidence folder` |
| Personal username or name | `maintainer`, `user`, or `local account` |
| Raw private transcript path | `local self-review transcript stored privately` |
| Authentication or credential output | `authenticated GitHub CLI session` |
| Private tool output with local paths | `local verification output` plus a pass/fail summary |
| Local file URI reference | `local artifact reference` |

Do not make the public replacement so vague that reviewers lose the result. For
example, prefer `151 tests passed, 2 skipped` over `tests were run`, but omit
the skipped test's machine-specific temporary path.

## Public write workflow

1. Draft the public text locally.
2. Run a literal scan for private marker classes.
3. Rewrite any hit using a neutral replacement.
4. Re-scan the rewritten text.
5. Post only the sanitized text.
6. Keep the full private transcript in the private evidence location when the
   dispatcher or issue asks for it.

If the public text cannot explain the result without leaking private details,
do not post a workaround. Mark the work blocked and ask what evidence can be
shared publicly.

## Review notes

This checklist is a manual guardrail. It does not replace judgment, because a
perfect literal scan can still miss private context that is obvious to a human
reviewer. Use local self-review to check the final public text before opening a
PR for skill-quality work.
