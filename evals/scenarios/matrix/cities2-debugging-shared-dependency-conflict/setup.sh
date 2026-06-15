#!/usr/bin/env bash
set -euo pipefail

git init -b main >/dev/null
git config user.email "eval@example.invalid"
git config user.name "Eval Runner"

mkdir -p SharedDependencyConflictMod/logs
mkdir -p SharedDependencyConflictMod/installed/TargetMod

cat > SharedDependencyConflictMod/logs/launch.log <<'EOF'
MissingMethodException
Method not found: HarmonyLib.HarmonyMethod HarmonyLib.HarmonyMethod.op_Implicit(System.Reflection.MethodInfo)
  at OtherEnabledMod.Mod.DoWhenLoaded()
  at Game.SceneFlow.GameManager.Update()
EOF

cat > SharedDependencyConflictMod/installed/TargetMod/dependencies.txt <<'EOF'
Installed target mod dependency inventory:
- FirstPersonCameraContinued.dll: local playtest build
- 0Harmony.dll: assembly version 2.2.2.0

Known local cache comparison:
- 0Harmony.dll version 2.2.2.0: HarmonyMethod.op_Implicit(MethodInfo) absent
- 0Harmony.dll version 2.3.3.0: HarmonyMethod.op_Implicit(MethodInfo) present
EOF

cat > SharedDependencyConflictMod/build.txt <<'EOF'
dotnet build: succeeded
No in-game launch verification has passed yet.
EOF

git add SharedDependencyConflictMod
git commit -m "Seed shared dependency conflict eval fixture" >/dev/null
