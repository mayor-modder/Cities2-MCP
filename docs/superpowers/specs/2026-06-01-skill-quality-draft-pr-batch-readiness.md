# Draft PR batch readiness checklist

Use this checklist when a skill-quality PM agent refreshes several draft PRs in
one cycle. The goal is to give the maintainer a compact readiness view without
adding noisy comments or expanding active PR scope.

## Per-PR fields

Record these fields privately first, then publish only the useful summary:

- PR number and linked issue.
- Owning agent and Work type.
- changed-line size and changed-file count.
- Check status, including failing or pending gates.
- Privacy scan result for PR body, comments, and added repo-visible text.
- required gates still missing, such as package checks, skill pressure-test
  evidence, client install smoke evidence, or generated-copy synchronization.
- remaining blocker, if any.

## Comment decision

Skip a coordination comment when the PR body already names the issue, scope,
verification, privacy scan, and residual risk, and checks are passing or clearly
pending.

Leave a concise comment only when it changes what the next reviewer can safely
do. Useful comments include:

- a privacy or public-text issue that must be fixed before the PR leaves draft;
- a missing documented gate that is specific to that PR;
- a size or scope concern that should become a follow-up issue;
- a stale project field or linked-issue mismatch.

Do not leave a comment just to repeat that checks passed or that the PR is small.
Those facts belong in the private batch notes unless they affect routing.

## Batch summary

When reporting the batch locally, group PRs by state:

- ready for maintainer review after required gates are documented;
- blocked on a specific missing gate;
- needs author follow-up for privacy, scope, or evidence;
- should stay draft because a validation gate is still pending.

Keep out-of-scope findings out of active PRs. Open or route a separate issue when
the finding is real but not required for the branch under review.
