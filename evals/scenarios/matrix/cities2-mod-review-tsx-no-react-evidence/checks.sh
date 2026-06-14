pre() {
    python -m evals.runner.check_tool agent-home-contained
    python -m evals.runner.check_tool condition-skill-set
    python -m evals.runner.check_tool skill-not-visible superpowers
    python -m evals.runner.check_tool git-branch main
}

post() {
    python -m evals.runner.check_tool skill-not-called 'superpowers:'
    python -m evals.runner.check_tool project-files-inspected ReviewBaitMod/src/Mod.cs ReviewBaitMod/ui/OptionsPanel.tsx ReviewBaitMod/ui/theme.css ReviewBaitMod/README.md
    python -m evals.runner.check_tool review-unsupported-claims-absent
    python -m evals.runner.check_tool review-actionable-findings-present
}
