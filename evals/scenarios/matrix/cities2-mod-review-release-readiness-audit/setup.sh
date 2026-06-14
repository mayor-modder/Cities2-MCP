#!/usr/bin/env bash
set -euo pipefail

git init -b main >/dev/null
git config user.email "eval@example.invalid"
git config user.name "Eval Runner"

mkdir -p AuditReviewMod/src AuditReviewMod/package AuditReviewMod/assets

cat > AuditReviewMod/src/Mod.cs <<'EOF'
namespace AuditReviewMod;

public sealed class Mod
{
    public string Name => "Audit Review Mod";
}
EOF

cat > AuditReviewMod/package/manifest.json <<'EOF'
{
  "name": "Audit Review Mod",
  "version": "0.1.0",
  "description": "Small fixture mod for release-readiness review.",
  "package": "AuditReviewMod-0.1.0.zip"
}
EOF

cat > AuditReviewMod/assets/icon.txt <<'EOF'
Placeholder icon adapted from another public mod page.
License and attribution permission are not documented yet.
EOF

cat > AuditReviewMod/README.md <<'EOF'
# Audit Review Mod

Package artifact exists in the maintainer's local output folder.
The packaged mod has not been locally playtested in an installed playset.
No Modding.log, Player.log, UI debugger screenshot, or gameplay notes have been captured.
License and asset attribution still need review before public upload.
EOF

cat > AuditReviewMod/RELEASE_NOTES.md <<'EOF'
# Release notes

Ready for public Paradox Mods upload.

- Initial package prepared.
- Placeholder icon included.
EOF

git add AuditReviewMod
git commit -m "Seed release readiness review fixture" >/dev/null
