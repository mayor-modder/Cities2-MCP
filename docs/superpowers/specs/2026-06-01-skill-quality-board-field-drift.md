# Skill quality board field drift notes

## Purpose

This note gives orchestrator agents a small checklist for repairing skill-quality
project field drift during a live work cycle. It is intentionally manual and
does not introduce background monitors, scheduled polling, or public-posting
automation.

## Refresh inputs

Before changing project fields, refresh the real state from GitHub:

- open issues and linked PRs
- project items and their `Agent`, `Status`, and `Work type` fields
- recent issue and PR comments that show an active claim
- draft PR state, changed-file count, and check status

Do not rely on a stale dispatcher prompt when GitHub disagrees.

## Repair immediately

Repair immediately when the intended state is clear and the edit only restores
routing hygiene:

Use this as the repair immediately list:

- a skill-quality issue is missing from the project
- an issue has no `Agent`, `Status`, or `Work type`
- a claimed implementation issue still says `Ready`
- an issue with an open linked PR still says `In progress`
- a closed or merged item still appears as active
- a duplicate project item points at the same issue and one item is clearly
  empty or stale

For duplicate project item drift, keep the item with the useful field history
when that is visible. If it is not obvious which item to preserve, do not delete
or close anything. Report only.

## Report only

Report only when a field change could overwrite another agent's active work or
requires maintainer judgment:

Use this as the report only list:

- recent comments show another agent claimed the issue
- the issue is assigned to the maintainer
- the intended owner is ambiguous
- the linked PR and issue body disagree about scope
- test gates or client evidence are missing but the owner is still working
- project fields conflict with a user-stated validation gate

In these cases, leave a concise coordination note only if it materially helps.
Do not close issues, delete branches, merge PRs, change versions, or publish
release artifacts while repairing board drift.

## Handoff summary

When reporting board drift locally, include:

- issue or PR number
- observed project fields
- repaired field, if any
- reason no public comment was needed, if you stayed quiet
- blocker or maintainer question, if repair was unsafe

Public summaries should stay neutral and omit private paths, private evidence
locations, credential-shaped strings, and private tool output.
