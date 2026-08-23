from __future__ import annotations

import io
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

from cities2_mcp.release_version import SemVer, main, prepare_release, select_release_level, version_from_ref


class ReleaseVersionTests(unittest.TestCase):
    def test_parse_and_render_stable_semver(self) -> None:
        self.assertEqual(str(SemVer.parse("0.2.19")), "0.2.19")

    def test_bump_levels_reset_lower_components(self) -> None:
        version = SemVer.parse("1.7.9")
        self.assertEqual(version.bump("none"), version)
        self.assertEqual(str(version.bump("patch")), "1.7.10")
        self.assertEqual(str(version.bump("minor")), "1.8.0")
        self.assertEqual(str(version.bump("major")), "2.0.0")

    def test_labels_default_to_patch(self) -> None:
        self.assertEqual(select_release_level([]), "patch")
        self.assertEqual(select_release_level(["documentation"]), "patch")
        self.assertEqual(select_release_level(["release:none"]), "none")
        self.assertEqual(select_release_level(["release:minor"]), "minor")
        self.assertEqual(select_release_level(["release:major"]), "major")

    def test_initial_minor_transition_is_0_2_0(self) -> None:
        base = SemVer.parse("0.1.9")
        self.assertEqual(base.bump(select_release_level(["release:minor"])), SemVer.parse("0.2.0"))

    def test_conflicting_release_labels_are_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "mutually exclusive"):
            select_release_level(["release:minor", "release:major"])
        with self.assertRaisesRegex(ValueError, "mutually exclusive"):
            select_release_level(["release:none", "release:minor"])

    def test_release_none_preserves_base_version_and_syncs_metadata(self) -> None:
        with tempfile.TemporaryDirectory(prefix="cities2-release-version-") as tmp:
            root = Path(tmp)
            version_file = root / "cities2_mcp" / "_version.py"
            version_file.parent.mkdir(parents=True)
            version_file.write_text('__version__ = "0.3.1"\n', encoding="utf-8")

            with mock.patch("cities2_mcp.release_version._sync_and_check") as sync:
                target = prepare_release(root, SemVer.parse("0.3.2"), ["release:none"])

            self.assertEqual(target, SemVer.parse("0.3.1"))
            self.assertEqual(version_file.read_text(encoding="utf-8"), '__version__ = "0.3.1"\n')
            sync.assert_called_once_with(root)

    def test_tag_action_is_idempotent_at_the_same_commit(self) -> None:
        from cities2_mcp.release_version import tag_action

        version = SemVer.parse("0.2.0")
        self.assertEqual(tag_action(version, "abc123", None), "create")
        self.assertEqual(tag_action(version, "abc123", "abc123"), "exists")
        with self.assertRaisesRegex(ValueError, "different commit"):
            tag_action(version, "abc123", "def456")

    def test_prepare_is_idempotent_for_the_same_base(self) -> None:
        with tempfile.TemporaryDirectory(prefix="cities2-release-version-") as tmp:
            root = Path(tmp)
            version_file = root / "cities2_mcp" / "_version.py"
            version_file.parent.mkdir(parents=True)
            version_file.write_text('__version__ = "0.2.4"\n', encoding="utf-8")

            with mock.patch("cities2_mcp.release_version._sync_and_check") as sync:
                first = prepare_release(root, SemVer.parse("0.2.4"), [])
                second = prepare_release(root, SemVer.parse("0.2.4"), [])

            self.assertEqual(first, SemVer.parse("0.2.5"))
            self.assertEqual(second, first)
            self.assertEqual(version_file.read_text(encoding="utf-8"), '__version__ = "0.2.5"\n')
            self.assertEqual(sync.call_count, 2)

    def test_version_from_ref_reads_canonical_file_from_git(self) -> None:
        completed = mock.Mock(returncode=0, stdout='__version__ = "1.2.3"\n')
        with mock.patch("cities2_mcp.release_version.subprocess.run", return_value=completed) as run:
            version = version_from_ref(Path("repo"), "origin/main")

        self.assertEqual(version, SemVer.parse("1.2.3"))
        run.assert_called_once_with(
            ["git", "show", "origin/main:cities2_mcp/_version.py"],
            cwd=Path("repo"),
            text=True,
            capture_output=True,
        )

    def test_version_from_ref_falls_back_to_legacy_init_version(self) -> None:
        missing = mock.Mock(returncode=128, stdout="", stderr="fatal: path not found")
        legacy = mock.Mock(stdout='from pathlib import Path\n\n__version__ = "0.1.9"\n')
        with mock.patch("cities2_mcp.release_version.subprocess.run", side_effect=(missing, legacy)) as run:
            version = version_from_ref(Path("repo"), "origin/main")

        self.assertEqual(version, SemVer.parse("0.1.9"))
        self.assertEqual(
            [call.args[0] for call in run.call_args_list],
            [
                ["git", "show", "origin/main:cities2_mcp/_version.py"],
                ["git", "show", "origin/main:cities2_mcp/__init__.py"],
            ],
        )

    def test_version_from_ref_reads_committed_canonical_file(self) -> None:
        with tempfile.TemporaryDirectory(prefix="cities2-release-git-ref-") as tmp:
            root = Path(tmp)
            version_file = root / "cities2_mcp" / "_version.py"
            version_file.parent.mkdir(parents=True)
            version_file.write_text('__version__ = "0.2.4"\n', encoding="utf-8")
            subprocess.run(["git", "init"], cwd=root, check=True, capture_output=True)
            subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=root, check=True)
            subprocess.run(["git", "config", "user.name", "Release Test"], cwd=root, check=True)
            subprocess.run(["git", "add", "cities2_mcp/_version.py"], cwd=root, check=True)
            subprocess.run(["git", "commit", "-m", "version"], cwd=root, check=True, capture_output=True)

            version = version_from_ref(root, "HEAD")

        self.assertEqual(version, SemVer(0, 2, 4))

    def test_version_from_ref_reads_legacy_committed_init_file(self) -> None:
        with tempfile.TemporaryDirectory(prefix="cities2-release-git-ref-") as tmp:
            root = Path(tmp)
            init_file = root / "cities2_mcp" / "__init__.py"
            init_file.parent.mkdir(parents=True)
            init_file.write_text('from pathlib import Path\n\n__version__ = "0.1.9"\n', encoding="utf-8")
            subprocess.run(["git", "init"], cwd=root, check=True, capture_output=True)
            subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=root, check=True)
            subprocess.run(["git", "config", "user.name", "Release Test"], cwd=root, check=True)
            subprocess.run(["git", "add", "cities2_mcp/__init__.py"], cwd=root, check=True)
            subprocess.run(["git", "commit", "-m", "version"], cwd=root, check=True, capture_output=True)

            version = version_from_ref(root, "HEAD")

        self.assertEqual(version, SemVer(0, 1, 9))

    def test_cli_help_lists_prepare_arguments(self) -> None:
        result = subprocess.run(
            [sys.executable, "-m", "cities2_mcp.release_version", "prepare", "--help"],
            text=True,
            capture_output=True,
            check=True,
        )

        self.assertIn("prepare", result.stdout)
        self.assertIn("--base-version", result.stdout)
        self.assertIn("--base-ref", result.stdout)
        self.assertIn("--label", result.stdout)

    def test_cli_prepare_accepts_base_version_and_labels(self) -> None:
        with mock.patch("cities2_mcp.release_version.prepare_release", return_value=SemVer.parse("0.3.0")) as prepare:
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                exit_code = main(["prepare", "--base-version", "0.2.9", "--label", "release:minor"])

        self.assertEqual(exit_code, 0)
        self.assertEqual(stdout.getvalue(), "0.3.0\n")
        prepare.assert_called_once_with(Path.cwd().resolve(), SemVer.parse("0.2.9"), ["release:minor"])

    def test_cli_prepare_accepts_base_ref(self) -> None:
        with (
            mock.patch("cities2_mcp.release_version.version_from_ref", return_value=SemVer.parse("2.4.6")) as base,
            mock.patch("cities2_mcp.release_version.prepare_release", return_value=SemVer.parse("2.4.7")) as prepare,
        ):
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                exit_code = main(["prepare", "--base-ref", "origin/main"])

        self.assertEqual(exit_code, 0)
        self.assertEqual(stdout.getvalue(), "2.4.7\n")
        base.assert_called_once_with(Path.cwd().resolve(), "origin/main")
        prepare.assert_called_once_with(Path.cwd().resolve(), SemVer.parse("2.4.6"), [])


if __name__ == "__main__":
    unittest.main()
