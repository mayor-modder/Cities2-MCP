pre() {
    python -m evals.runner.check_tool agent-home-contained
    python -m evals.runner.check_tool condition-skill-set
    python -m evals.runner.check_tool skill-not-visible superpowers
    python -m evals.runner.check_tool git-branch main
}

post() {
    python -m evals.runner.check_tool skill-not-called 'superpowers:'
    python -m evals.runner.check_tool required-tool-called source_status
    python -m evals.runner.check_tool required-tool-called search
    python -m evals.runner.check_tool compact-search-query office demand
    python -m evals.runner.check_tool knowledge-office-demand-grounded
    python -m evals.runner.check_tool not-tool-called web_search
}
