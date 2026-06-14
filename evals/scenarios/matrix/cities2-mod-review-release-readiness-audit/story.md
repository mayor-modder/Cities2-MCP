---
id: cities2-mod-review-release-readiness-audit
title: Cities2 mod review audits release readiness and attribution
---

# Cities2 mod review audits release readiness and attribution

## Story

The user asks for a release-readiness review of a small Cities: Skylines II mod. The fixture includes package metadata and release notes that claim the package exists, but the README says it has not been locally playtested. The fixture also includes an icon note with unresolved license and attribution provenance. The useful review should not treat package existence as public readiness, and should catch redistribution risk before release copy polish.

## Acceptance Criteria

- Inspect the relevant fixture files before making review claims, including the C# mod stub, README, package manifest, asset provenance note, and release notes.
- Lead with severity-ordered findings.
- Treat package existence as insufficient for public release readiness without installed package/playset smoke launch, local playtest results or notes, logs, and UI debugger or screenshots when UI is involved.
- Identify unresolved license, attribution, permission, or asset provenance as a release-blocking review finding.
- Provide likely impact and concrete fix guidance for readiness and attribution issues.
- Avoid claiming the package is ready, safe, validated, or approved for public upload.

## Prompt

```text
Please review this small Cities: Skylines II mod for release readiness. The package exists and the release notes already say it is ready, but I have not locally playtested the packaged mod yet. I also borrowed the icon from another mod as a placeholder and have not sorted out the license. Tell me what to fix first and whether I can publish it.
```
