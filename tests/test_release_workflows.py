from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ReleaseWorkflowTests(unittest.TestCase):
    def test_pr_workflow_uses_labels_base_ref_and_app_token(self) -> None:
        text = (ROOT / ".github" / "workflows" / "prepare-release-version.yml").read_text(encoding="utf-8")
        self.assertIn("pull_request:", text)
        self.assertIn("release:none", text)
        self.assertIn("release:minor", text)
        self.assertIn("release:major", text)
        self.assertIn("GITHUB_BASE_REF", text)
        self.assertIn("actions/create-github-app-token@v3", text)
        self.assertIn("RELEASE_APP_CLIENT_ID", text)
        self.assertIn("RELEASE_APP_PRIVATE_KEY", text)
        self.assertIn("configured=false", text)
        self.assertIn("skipping automatic version commit", text)
        self.assertIn("cities2_mcp.release_version prepare", text)
        self.assertIn("git push", text)
        self.assertIn("unsupported-fork", text)

    def test_finalize_workflow_validates_before_app_tag_push(self) -> None:
        text = (ROOT / ".github" / "workflows" / "finalize-release.yml").read_text(encoding="utf-8")
        self.assertIn('branches: ["main"]', text)
        self.assertIn("python -m unittest discover -s tests -v", text)
        self.assertIn("python -m cities2_mcp.plugin_packages check", text)
        self.assertIn("actions/create-github-app-token@v3", text)
        self.assertIn('tag="v$version"', text)
        self.assertIn("release_version tag-state", text)
        self.assertIn("https://pypi.org/pypi/cities2-mcp/$version/json", text)
        self.assertIn("git push origin", text)

    def test_release_workflow_syncs_catalog_after_publish(self) -> None:
        text = (ROOT / ".github" / "workflows" / "release.yml").read_text(encoding="utf-8")
        self.assertIn("catalog:", text)
        self.assertIn("permissions:\n  contents: read", text)
        self.assertIn("needs: publish", text)
        self.assertIn("mayor-modder/Mayor-Modder-Cities2-Plugins", text)
        self.assertIn("cities2_mcp.plugin_packages sync-catalog", text)
        self.assertIn("automation/cities2-mcp-", text)
        self.assertIn("git merge --no-edit origin/main", text)
        self.assertIn("gh pr create", text)
        self.assertIn("gh pr merge --auto --squash", text)
        self.assertIn("*Co-authored by Cities2-MCP release automation.*", text)

    def test_maintainer_docs_cover_one_time_release_setup(self) -> None:
        text = (ROOT / "docs" / "maintainers" / "release-automation.md").read_text(encoding="utf-8")
        for required in (
            "release:none",
            "release:minor",
            "release:major",
            "RELEASE_APP_CLIENT_ID",
            "RELEASE_APP_PRIVATE_KEY",
            "Cities2-MCP",
            "Mayor-Modder-Cities2-Plugins",
            "Prepare release version / prepare",
            "allow_auto_merge",
            "contents: write",
            "pull requests: write",
        ):
            self.assertIn(required, text)


if __name__ == "__main__":
    unittest.main()
