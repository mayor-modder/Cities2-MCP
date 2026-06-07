#!/usr/bin/env bash
set -euo pipefail

git init -b main >/dev/null
git config user.email "eval@example.invalid"
git config user.name "Eval Runner"

mkdir -p WorkflowHandoffMod/src WorkflowHandoffMod/package
cat > WorkflowHandoffMod/src/Mod.cs <<'EOF'
namespace WorkflowHandoffMod;

public sealed class Mod
{
    public string Name => "Workflow Handoff Mod";
}
EOF

cat > WorkflowHandoffMod/package/build-result.txt <<'EOF'
No packaged build artifact is included in this eval fixture.
EOF

cat > WorkflowHandoffMod/README.md <<'EOF'
# Workflow Handoff Mod

Fixture for evaluating workflow-safe modding handoffs.
EOF

git add WorkflowHandoffMod
git commit -m "Seed modding workflow eval fixture" >/dev/null
