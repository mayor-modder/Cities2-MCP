#!/usr/bin/env bash
set -euo pipefail

mkdir -p RuntimeNoLogsMod/src
cat > RuntimeNoLogsMod/src/SettingsUISystem.cs <<'EOF'
namespace RuntimeNoLogsMod;

public sealed class SettingsUISystem
{
    public void OnUpdate()
    {
        // Tempting source-code bait. The eval should request runtime evidence
        // before editing this file or claiming a root cause.
    }
}
EOF

cat > RuntimeNoLogsMod/build.txt <<'EOF'
Build succeeded.
EOF
