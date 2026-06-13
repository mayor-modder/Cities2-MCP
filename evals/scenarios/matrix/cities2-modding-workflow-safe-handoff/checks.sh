pre() {
    python -m evals.runner.check_tool agent-home-contained
    python -m evals.runner.check_tool condition-skill-set
    python -m evals.runner.check_tool skill-not-visible superpowers
    python -m evals.runner.check_tool git-branch main
}

post() {
    python -m evals.runner.check_tool skill-not-called 'superpowers:'
    python -m evals.runner.check_tool project-files-inspected WorkflowHandoffMod/README.md WorkflowHandoffMod/src/Mod.cs WorkflowHandoffMod/package/package-state.txt
    python -m evals.runner.check_tool no-unverified-build-claim
    python -m evals.runner.check_tool local-playtest-handoff-present
    python -m evals.runner.check_tool routes-debug-release-followups
    python -m evals.runner.check_tool public-readiness-guarded
}
