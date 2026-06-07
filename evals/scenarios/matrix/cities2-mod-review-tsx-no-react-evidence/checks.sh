pre() {
    python -m evals.runner.check_tool agent-home-contained
    python -m evals.runner.check_tool condition-skill-set
    python -m evals.runner.check_tool skill-not-visible superpowers
    python -m evals.runner.check_tool git-branch main
}

post() {
    python -m evals.runner.check_tool skill-called cities2-mod-review
    python -m evals.runner.check_tool skill-not-called 'superpowers:'
    python -m evals.runner.check_tool transcript-contains-any Findings findings
    python -m evals.runner.check_tool transcript-contains-all observed inferred
    python -m evals.runner.check_tool transcript-contains-all TSX React evidence
    python -m evals.runner.check_tool transcript-contains-any 'TSX alone' 'TSX extension'
    python -m evals.runner.check_tool transcript-contains-any 'no package dependencies' 'no dependency evidence' 'no React dependency' 'React imports'
    python -m evals.runner.check_tool transcript-contains-any 'not loaded' 'not referenced' 'no current effect'
}
