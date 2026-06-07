pre() {
    python -m evals.runner.check_tool agent-home-contained
    python -m evals.runner.check_tool condition-skill-set
    python -m evals.runner.check_tool skill-not-visible superpowers
    python -m evals.runner.check_tool git-branch main
}

post() {
    python -m evals.runner.check_tool skill-called cities2-modding
    python -m evals.runner.check_tool skill-not-called 'superpowers:'
    python -m evals.runner.check_tool transcript-contains-any 'active workspace project files' 'inspect the active workspace' 'workspace evidence'
    python -m evals.runner.check_tool transcript-contains-any 'local playtest artifact' 'local playtest evidence'
    python -m evals.runner.check_tool transcript-contains-any Modding.log localhost:9444 playset
    python -m evals.runner.check_tool transcript-contains-any cities2-mod-release 'release skill' 'release-readiness'
    python -m evals.runner.check_tool transcript-contains-any cities2-mod-debugging 'debugging skill' 'runtime debugging'
    python -m evals.runner.check_tool transcript-contains-any 'not ready for public release' 'not ready to publish' 'not ready for release' 'not ready to release'
    python -m evals.runner.check_tool transcript-contains-any 'verify the build' 'cannot claim the build' 'cannot confirm the build'
}
