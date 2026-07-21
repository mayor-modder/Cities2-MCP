import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ReleaseWorkflowTests(unittest.TestCase):
    def test_catalog_pr_merge_handles_clean_status_and_auto_merge_race(self) -> None:
        workflow = (ROOT / ".github" / "workflows" / "release.yml").read_text(encoding="utf-8")
        merge_step = workflow.split("      - name: Open or update catalog pull request", 1)[1]

        state_query = 'gh pr view "$pr" --json mergeStateStatus --jq \'.mergeStateStatus\''
        direct_merge = 'gh pr merge --squash "$pr"'
        auto_merge = 'gh pr merge --auto --squash "$pr"'

        self.assertGreaterEqual(merge_step.count(state_query), 2)
        self.assertGreaterEqual(merge_step.count(direct_merge), 2)
        self.assertEqual(merge_step.count(auto_merge), 1)
        self.assertIn('if [[ "$merge_state" == "CLEAN" ]]; then', merge_step)
        self.assertIn('elif ! gh pr merge --auto --squash "$pr"; then', merge_step)


if __name__ == "__main__":
    unittest.main()
