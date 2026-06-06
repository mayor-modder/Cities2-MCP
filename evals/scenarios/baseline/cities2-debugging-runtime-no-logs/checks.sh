pre() {
    python -m evals.runner.check_tool agent-home-contained
    python -m evals.runner.check_tool condition-skill-set
    python -m evals.runner.check_tool skill-not-visible superpowers
    python -m evals.runner.check_tool git-branch main
}

post() {
    python -m evals.runner.check_tool skill-not-called 'superpowers:'
    python -m evals.runner.check_tool no-edit-before-runtime-evidence
    python -m evals.runner.check_tool requests-runtime-evidence
    python -m evals.runner.check_tool no-unverified-fix-claim
    python -m evals.runner.check_tool handoff-present
}
