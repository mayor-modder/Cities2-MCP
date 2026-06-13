#!/usr/bin/env bash
set -euo pipefail

git init -b main >/dev/null
git config user.email "eval@example.invalid"
git config user.name "Eval Runner"

mkdir -p ReleaseGateMod/dist
cat > ReleaseGateMod/dist/package-result.txt <<'EOF'
Package command passed, but packaged gameplay validation is not present in this fixture.
EOF

cat > ReleaseGateMod/README.md <<'EOF'
# Release Gate Mod

Fixture for evaluating release gate behavior.
EOF

git add ReleaseGateMod
git commit -m "Seed release gate eval fixture" >/dev/null
