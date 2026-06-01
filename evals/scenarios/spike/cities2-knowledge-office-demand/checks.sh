pre() {
    python -m evals.runner.check_tool agent-home-contained
    python -m evals.runner.check_tool condition-skill-set
    python -m evals.runner.check_tool skill-not-visible superpowers
    python -m evals.runner.check_tool git-branch main
}

post() {
    python -m evals.runner.check_tool skill-called cities2-knowledge
    python -m evals.runner.check_tool skill-not-called 'superpowers:'
    python -m evals.runner.check_tool tool-called source_status
    python -m evals.runner.check_tool tool-called search
    python -m evals.runner.check_tool transcript-contains 'office demand'
    python -m evals.runner.check_tool transcript-contains 'Source'
    python -m evals.runner.check_tool not-tool-called web_search
}
