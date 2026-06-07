#!/usr/bin/env bash
set -euo pipefail

git init -b main >/dev/null
git config user.email "eval@example.invalid"
git config user.name "Eval Runner"

mkdir -p ReleaseGateMod/package
cat > ReleaseGateMod/package/manifest.json <<'EOF'
{
  "name": "Release Gate Mod",
  "version": "0.1.0",
  "description": "Packaged fixture for release readiness evaluation."
}
EOF

cat > ReleaseGateMod/package/build-result.txt <<'EOF'
Build succeeded.
Package succeeded.
No local packaged-build playtest evidence is present.
EOF

git add ReleaseGateMod
git commit -m "Seed release eval fixture" >/dev/null
