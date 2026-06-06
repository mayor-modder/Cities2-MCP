#!/usr/bin/env bash
set -euo pipefail

git init -b main >/dev/null
git config user.email "eval@example.invalid"
git config user.name "Eval Runner"
cat > README.md <<'EOF'
# Cities2 knowledge eval fixture

This fixture gives the coding agent a normal git worktree. The scenario does
not require source edits.
EOF
git add README.md
git commit -m "Seed knowledge eval fixture" >/dev/null
