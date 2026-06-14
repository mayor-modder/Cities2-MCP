pre() {
    python -m evals.runner.check_tool agent-home-contained
    python -m evals.runner.check_tool condition-skill-set
    python -m evals.runner.check_tool skill-not-visible superpowers
    python -m evals.runner.check_tool git-branch main
}

post() {
    python -m evals.runner.check_tool skill-not-called 'superpowers:'
    python -m evals.runner.check_tool project-files-inspected AuditReviewMod/src/Mod.cs AuditReviewMod/README.md AuditReviewMod/package/manifest.json AuditReviewMod/assets/icon.txt AuditReviewMod/RELEASE_NOTES.md
    python -m evals.runner.check_tool review-release-readiness-audit-present
    python -m evals.runner.check_tool public-readiness-guarded
}
