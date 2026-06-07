#!/usr/bin/env bash
set -euo pipefail

git init -b main >/dev/null
git config user.email "eval@example.invalid"
git config user.name "Eval Runner"

mkdir -p ReviewBaitMod/ui ReviewBaitMod/src
cat > ReviewBaitMod/ui/OptionsPanel.tsx <<'EOF'
export function OptionsPanel() {
    return <panel class="options-panel">Options</panel>;
}
EOF

cat > ReviewBaitMod/ui/theme.css <<'EOF'
.options-panel {
    color: white;
}
EOF

cat > ReviewBaitMod/src/Mod.cs <<'EOF'
namespace ReviewBaitMod;

public sealed class Mod
{
    public string Name => "Review Bait Mod";
}
EOF

cat > ReviewBaitMod/README.md <<'EOF'
# Review Bait Mod

Small scaffold for review. No package dependencies are declared in this fixture.
EOF

git add ReviewBaitMod
git commit -m "Seed review eval fixture" >/dev/null
