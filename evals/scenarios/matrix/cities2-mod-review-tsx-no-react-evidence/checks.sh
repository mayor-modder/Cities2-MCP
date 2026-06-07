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
    python -m evals.runner.check_tool transcript-rubric evidence-grounded-review 'Separates observed files from inferred recommendations.' all observed inferred
    python -m evals.runner.check_tool transcript-rubric react-evidence 'Explains that TSX alone is not enough evidence for React.' all TSX React evidence
    python -m evals.runner.check_tool transcript-rubric tsx-framing 'Frames TSX as file-extension evidence, not framework proof.' any 'TSX alone' 'TSX extension'
    python -m evals.runner.check_tool transcript-rubric missing-react-proof 'Names the missing dependency or import evidence instead of assuming React.' any 'no package dependencies' 'no dependency evidence' 'no React dependency' 'React imports'
    python -m evals.runner.check_tool transcript-rubric css-effect 'Explains that an unreferenced CSS file has no current effect.' any 'not loaded' 'not referenced' 'no current effect'
}
