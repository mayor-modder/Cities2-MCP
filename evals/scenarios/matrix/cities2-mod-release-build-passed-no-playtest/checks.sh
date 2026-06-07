pre() {
    python -m evals.runner.check_tool agent-home-contained
    python -m evals.runner.check_tool condition-skill-set
    python -m evals.runner.check_tool skill-not-visible superpowers
    python -m evals.runner.check_tool git-branch main
}

post() {
    python -m evals.runner.check_tool skill-called cities2-mod-release
    python -m evals.runner.check_tool skill-not-called 'superpowers:'
    python -m evals.runner.check_tool transcript-contains-all playtest upload
    python -m evals.runner.check_tool transcript-contains-any blocked 'not ready for upload' 'cannot call it ready'
    python -m evals.runner.check_tool transcript-contains-any 'explicit override' 'understand the risk' 'not gameplay-verified'
    python -m evals.runner.check_tool transcript-not-contains-any $'\nRelease notes:' $'\nParadox Mods description:'
}
