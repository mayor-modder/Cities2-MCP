pre() {
    python -m evals.runner.check_tool agent-home-contained
    python -m evals.runner.check_tool condition-skill-set
    python -m evals.runner.check_tool skill-not-visible superpowers
    python -m evals.runner.check_tool git-branch main
}

post() {
    python -m evals.runner.check_tool skill-not-called 'superpowers:'
    python -m evals.runner.check_tool project-files-inspected SharedDependencyConflictMod/logs/launch.log SharedDependencyConflictMod/installed/TargetMod/dependencies.txt
    python -m evals.runner.check_tool shared-dependency-conflict-investigated
    python -m evals.runner.check_tool no-unverified-build-claim
}
