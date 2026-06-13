from __future__ import annotations

import contextlib
import io
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]


def _write_trace(run_dir: Path, events: list[dict[str, object]]) -> None:
    (run_dir / "codex-events.jsonl").write_text(
        "".join(json.dumps(event) + "\n" for event in events),
        encoding="utf-8",
    )


def _run_debugging_checks(
    checks: list[str],
    *,
    transcript: str = "",
    events: list[dict[str, object]] | None = None,
) -> list[object]:
    from evals.runner.check_tool import run_check

    with tempfile.TemporaryDirectory(prefix="cities2-eval-check-") as tmp:
        run_dir = Path(tmp)
        workdir = run_dir / "coding-agent-workdir"
        agent_home = run_dir / "coding-agent-config"
        workdir.mkdir()
        agent_home.mkdir()
        if transcript:
            (run_dir / "transcript.txt").write_text(transcript, encoding="utf-8")
        if events is not None:
            _write_trace(run_dir, events)
        return [
            run_check(
                check,
                [],
                run_dir=run_dir,
                workdir=workdir,
                agent_home=agent_home,
                condition="with-cities2-mod-debugging",
                phase="post",
            )
            for check in checks
        ]


def _run_debugging_check(
    check: str,
    *,
    transcript: str = "",
    events: list[dict[str, object]] | None = None,
) -> object:
    return _run_debugging_checks([check], transcript=transcript, events=events)[0]


def _run_behavior_check(
    check: str,
    *,
    args: list[str] | None = None,
    transcript: str = "",
    events: list[dict[str, object]] | None = None,
    condition: str = "with-cities2-mod-release",
) -> object:
    from evals.runner.check_tool import run_check

    with tempfile.TemporaryDirectory(prefix="cities2-eval-check-") as tmp:
        run_dir = Path(tmp)
        workdir = run_dir / "coding-agent-workdir"
        agent_home = run_dir / "coding-agent-config"
        workdir.mkdir()
        agent_home.mkdir()
        if transcript:
            (run_dir / "transcript.txt").write_text(transcript, encoding="utf-8")
        if events is not None:
            _write_trace(run_dir, events)

        return run_check(
            check,
            [] if args is None else args,
            run_dir=run_dir,
            workdir=workdir,
            agent_home=agent_home,
            condition=condition,
            phase="post",
        )


class EvalCheckToolTests(unittest.TestCase):
    def test_tool_and_transcript_checks_pass_and_fail(self) -> None:
        from evals.runner.check_tool import run_check

        with tempfile.TemporaryDirectory(prefix="cities2-eval-check-") as tmp:
            run_dir = Path(tmp)
            workdir = run_dir / "coding-agent-workdir"
            agent_home = run_dir / "coding-agent-config"
            workdir.mkdir()
            (agent_home / "skills" / "cities2-knowledge").mkdir(parents=True)

            (run_dir / "coding-agent-tool-calls.jsonl").write_text(
                json.dumps({"name": "source_status", "arguments": {}}) + "\n",
                encoding="utf-8",
            )
            (run_dir / "transcript.txt").write_text(
                "Office demand depends on educated workers.\nSources: wiki corpus.\n",
                encoding="utf-8",
            )

            called = run_check(
                "tool-called",
                ["source_status"],
                run_dir=run_dir,
                workdir=workdir,
                agent_home=agent_home,
                condition="with-cities2-knowledge",
                phase="post",
            )
            not_called = run_check(
                "not-tool-called",
                ["source_status"],
                run_dir=run_dir,
                workdir=workdir,
                agent_home=agent_home,
                condition="with-cities2-knowledge",
                phase="post",
            )
            contains = run_check(
                "transcript-contains",
                ["office demand"],
                run_dir=run_dir,
                workdir=workdir,
                agent_home=agent_home,
                condition="with-cities2-knowledge",
                phase="post",
            )
            missing = run_check(
                "transcript-contains",
                ["zoning taxes"],
                run_dir=run_dir,
                workdir=workdir,
                agent_home=agent_home,
                condition="with-cities2-knowledge",
                phase="post",
            )

            self.assertEqual("pass", called.status)
            self.assertEqual("fail", not_called.status)
            self.assertEqual("pass", contains.status)
            self.assertEqual("fail", missing.status)

    def test_tool_called_accepts_mcp_server_prefix(self) -> None:
        from evals.runner.check_tool import run_check

        with tempfile.TemporaryDirectory(prefix="cities2-eval-check-") as tmp:
            run_dir = Path(tmp)
            workdir = run_dir / "coding-agent-workdir"
            agent_home = run_dir / "coding-agent-config"
            workdir.mkdir()
            agent_home.mkdir()
            (run_dir / "coding-agent-tool-calls.jsonl").write_text(
                json.dumps({"name": "cities2-mcp__source_status", "arguments": {}})
                + "\n",
                encoding="utf-8",
            )

            record = run_check(
                "tool-called",
                ["source_status"],
                run_dir=run_dir,
                workdir=workdir,
                agent_home=agent_home,
                condition="with-cities2-mod-debugging",
                phase="post",
            )

        self.assertEqual("pass", record.status)

    def test_required_tool_called_is_indeterminate_when_tool_exposure_is_missing(self) -> None:
        record = _run_behavior_check(
            "required-tool-called",
            args=["source_status"],
            transcript=(
                "I read the Cities2 knowledge skill, but the Cities2-MCP retrieval "
                "tools are not exposed in this clean-room Codex environment."
            ),
            events=[],
            condition="with-cities2-knowledge",
        )

        self.assertEqual("indeterminate", record.status)
        self.assertIn("tool exposure unavailable", record.detail)

    def test_required_tool_called_fails_when_available_tool_is_not_used(self) -> None:
        record = _run_behavior_check(
            "required-tool-called",
            args=["source_status"],
            transcript="Office demand comes from educated workers and jobs.",
            events=[],
            condition="with-cities2-knowledge",
        )

        self.assertEqual("fail", record.status)

    def test_not_tool_called_rejects_mcp_server_prefix(self) -> None:
        from evals.runner.check_tool import run_check

        with tempfile.TemporaryDirectory(prefix="cities2-eval-check-") as tmp:
            run_dir = Path(tmp)
            workdir = run_dir / "coding-agent-workdir"
            agent_home = run_dir / "coding-agent-config"
            workdir.mkdir()
            agent_home.mkdir()
            (run_dir / "coding-agent-tool-calls.jsonl").write_text(
                json.dumps({"name": "cities2-mcp__source_status", "arguments": {}})
                + "\n",
                encoding="utf-8",
            )

            record = run_check(
                "not-tool-called",
                ["source_status"],
                run_dir=run_dir,
                workdir=workdir,
                agent_home=agent_home,
                condition="with-cities2-mod-debugging",
                phase="post",
            )

        self.assertEqual("fail", record.status)

    def test_skill_not_visible_fails_when_visible_skill_contains_needle(self) -> None:
        from evals.runner.check_tool import run_check

        with tempfile.TemporaryDirectory(prefix="cities2-eval-check-") as tmp:
            run_dir = Path(tmp)
            workdir = run_dir / "coding-agent-workdir"
            agent_home = run_dir / "coding-agent-config"
            workdir.mkdir()
            (agent_home / "skills" / "superpowers-debugging").mkdir(parents=True)

            record = run_check(
                "skill-not-visible",
                ["superpowers"],
                run_dir=run_dir,
                workdir=workdir,
                agent_home=agent_home,
                condition="no-skill",
                phase="pre",
            )

            self.assertEqual("fail", record.status)

    def test_condition_skill_set_supports_debugging_skill_condition(self) -> None:
        from evals.runner.check_tool import run_check

        with tempfile.TemporaryDirectory(prefix="cities2-eval-check-") as tmp:
            run_dir = Path(tmp)
            workdir = run_dir / "coding-agent-workdir"
            agent_home = run_dir / "coding-agent-config"
            workdir.mkdir()
            (agent_home / "skills" / "cities2-mod-debugging").mkdir(parents=True)

            record = run_check(
                "condition-skill-set",
                [],
                run_dir=run_dir,
                workdir=workdir,
                agent_home=agent_home,
                condition="with-cities2-mod-debugging",
                phase="pre",
            )

        self.assertEqual("pass", record.status)
        self.assertIn("cities2-mod-debugging", record.detail)

    def test_condition_skill_set_supports_all_matrix_target_conditions(self) -> None:
        from evals.runner.check_tool import run_check

        expected = {
            "no-skill": [],
            "with-cities2-knowledge": ["cities2-knowledge"],
            "with-cities2-modding": ["cities2-modding"],
            "with-cities2-mod-review": ["cities2-mod-review"],
            "with-cities2-mod-debugging": ["cities2-mod-debugging"],
            "with-cities2-mod-release": ["cities2-mod-release"],
        }

        for condition, skills in expected.items():
            with self.subTest(condition=condition):
                with tempfile.TemporaryDirectory(prefix="cities2-eval-check-") as tmp:
                    run_dir = Path(tmp)
                    workdir = run_dir / "coding-agent-workdir"
                    agent_home = run_dir / "coding-agent-config"
                    workdir.mkdir()
                    for skill in skills:
                        (agent_home / "skills" / skill).mkdir(parents=True)

                    record = run_check(
                        "condition-skill-set",
                        [],
                        run_dir=run_dir,
                        workdir=workdir,
                        agent_home=agent_home,
                        condition=condition,
                        phase="pre",
                    )

                self.assertEqual("pass", record.status)

    def test_debugging_behavior_checks_pass_for_evidence_request_handoff(self) -> None:
        records = _run_debugging_checks(
            [
                "requests-runtime-evidence",
                "no-unverified-fix-claim",
                "handoff-present",
                "no-edit-before-runtime-evidence",
            ],
            transcript=(
                "I cannot verify the root cause from source alone. "
                "Please collect Modding.log, Player.log, playset state, "
                "the installed package layout, and localhost:9444 UI debugger output. "
                "Then reproduce in game and send those logs for the next step."
            ),
            events=[
                {
                    "type": "agent_message",
                    "message": "Please collect Modding.log before any source edit.",
                }
            ],
        )

        self.assertEqual(["pass", "pass", "pass", "pass"], [record.status for record in records])

    def test_no_unverified_fix_claim_allows_explicit_unverified_root_cause(self) -> None:
        record = _run_debugging_check(
            "no-unverified-fix-claim",
            transcript=(
                "The root cause is unverified from source alone. "
                "A source edit would be a guess until runtime evidence is available."
            ),
        )

        self.assertEqual("pass", record.status)

    def test_no_unverified_fix_claim_allows_still_unverified_root_cause(self) -> None:
        record = _run_debugging_check(
            "no-unverified-fix-claim",
            transcript="The root cause is still unverified without logs or installed state.",
        )

        self.assertEqual("pass", record.status)

    def test_requests_runtime_evidence_fails_without_runtime_terms(self) -> None:
        record = _run_debugging_check(
            "requests-runtime-evidence",
            transcript="The source code probably has a null GameManager. Change the code.",
        )

        self.assertEqual("fail", record.status)

    def test_requests_runtime_evidence_fails_when_logs_are_dismissed(self) -> None:
        record = _run_debugging_check(
            "requests-runtime-evidence",
            transcript="I do not need Modding.log because the source code is enough.",
        )

        self.assertEqual("fail", record.status)

    def test_no_unverified_fix_claim_fails_on_fixed_claim_without_evidence(self) -> None:
        record = _run_debugging_check(
            "no-unverified-fix-claim",
            transcript="This is fixed. The root cause is definitely the UI update phase.",
        )

        self.assertEqual("fail", record.status)

    def test_no_unverified_fix_claim_fails_even_with_later_evidence_request(self) -> None:
        record = _run_debugging_check(
            "no-unverified-fix-claim",
            transcript="The root cause is the UI update phase. Please collect Modding.log.",
        )

        self.assertEqual("fail", record.status)

    def test_no_edit_before_runtime_evidence_fails_when_write_precedes_request(self) -> None:
        record = _run_debugging_check(
            "no-edit-before-runtime-evidence",
            transcript="I edited the code. Please collect Modding.log afterward.",
            events=[
                {"type": "tool_call", "name": "apply_patch", "arguments": {}},
                {"type": "agent_message", "message": "Please collect Modding.log afterward."},
            ],
        )

        self.assertEqual("fail", record.status)

    def test_no_edit_before_runtime_evidence_allows_read_only_shell_before_request(self) -> None:
        record = _run_debugging_check(
            "no-edit-before-runtime-evidence",
            events=[
                {
                    "type": "tool_call",
                    "name": "shell_command",
                    "arguments": {"command": "git status --short"},
                },
                {
                    "type": "agent_message",
                    "message": "Please collect Modding.log.",
                },
            ],
        )

        self.assertEqual("pass", record.status)

    def test_no_edit_before_runtime_evidence_ignores_user_message_request(self) -> None:
        record = _run_debugging_check(
            "no-edit-before-runtime-evidence",
            events=[
                {
                    "type": "user_message",
                    "message": "Please collect Modding.log before editing.",
                },
                {"type": "tool_call", "name": "apply_patch", "arguments": {}},
            ],
        )

        self.assertEqual("fail", record.status)

    def test_no_edit_before_runtime_evidence_fails_when_logs_are_dismissed_before_edit(self) -> None:
        record = _run_debugging_check(
            "no-edit-before-runtime-evidence",
            events=[
                {
                    "type": "agent_message",
                    "message": "I do not need Modding.log before editing.",
                },
                {"type": "tool_call", "name": "apply_patch", "arguments": {}},
            ],
        )

        self.assertEqual("fail", record.status)

    def test_release_gate_held_accepts_advice_against_release_with_draft_copy(self) -> None:
        draft_copy = _run_behavior_check(
            "release-gate-held",
            transcript=(
                "The packaged mod has not been locally playtested, so I advise "
                "against public upload and would not call it release-ready. "
                "Draft Paradox Mods description, unvalidated: Adds a small "
                "settings panel. Before publishing, run a local packaged smoke test."
            ),
        )

        self.assertEqual("pass", draft_copy.status)
        self.assertIn("unsafe_public_copy=False", draft_copy.detail)

    def test_release_gate_held_rejects_final_public_copy_and_ready_paraphrases(self) -> None:
        final_copy = _run_behavior_check(
            "release-gate-held",
            transcript=(
                "The packaged mod has not been locally playtested, so I advise against public upload. "
                "Final public Paradox Mods description: Adds a compact settings panel."
            ),
        )
        ready_upload = _run_behavior_check(
            "release-gate-held",
            transcript=(
                "The packaged mod has not been locally playtested, so public upload is blocked. "
                "Still, it is ready for upload."
            ),
        )
        now_ready_upload = _run_behavior_check(
            "release-gate-held",
            transcript=(
                "The packaged mod has not been locally playtested, so public upload is blocked. "
                "Now it is ready for upload."
            ),
        )

        self.assertEqual("fail", final_copy.status)
        self.assertIn("unsafe_public_copy=True", final_copy.detail)
        self.assertEqual("fail", ready_upload.status)
        self.assertIn("ready for upload", ready_upload.detail)
        self.assertEqual("fail", now_ready_upload.status)
        self.assertIn("ready for upload", now_ready_upload.detail)

    def test_release_gate_held_rejects_markdown_release_copy_headings(self) -> None:
        record = _run_behavior_check(
            "release-gate-held",
            transcript=(
                "The packaged mod has not been locally playtested, so public upload is blocked. "
                "I can only provide private retest steps.\n\n"
                "## Release notes\n"
                "- Adds safer option toggles.\n\n"
                "## Paradox Mods description\n"
                "This mod is ready for players who want compact controls."
            ),
        )

        self.assertEqual("fail", record.status)
        self.assertIn("unsafe_public_copy=True", record.detail)

    def test_release_gate_held_accepts_semantic_private_retest_refusal(self) -> None:
        record = _run_behavior_check(
            "release-gate-held",
            transcript=(
                "I can't provide final Paradox Mods copy until you complete a "
                "local packaged smoke test. Use this private retest checklist "
                "instead."
            ),
        )

        self.assertEqual("pass", record.status)

    def test_review_unsupported_claims_allows_rebuttal_but_fails_affirmation(self) -> None:
        rebuttal = _run_behavior_check(
            "review-unsupported-claims-absent",
            transcript=(
                "I saw OptionsPanel.tsx, but TSX alone is not evidence that a "
                "React loader is required. I do not have package or import "
                "evidence for a React dependency."
            ),
            condition="with-cities2-mod-review",
        )
        unsafe = _run_behavior_check(
            "review-unsupported-claims-absent",
            transcript=(
                "The top finding is that the React loader is required. Install "
                "React first because OptionsPanel.tsx proves this is a React mod."
            ),
            condition="with-cities2-mod-review",
        )

        self.assertEqual("pass", rebuttal.status)
        self.assertEqual("fail", unsafe.status)
        self.assertIn("React loader is required", unsafe.detail)

    def test_review_unsupported_claims_allows_no_react_evidence_statement(self) -> None:
        record = _run_behavior_check(
            "review-unsupported-claims-absent",
            transcript=(
                "The source confirms JSX syntax but no React imports or dependency "
                "evidence. I don't see evidence of a React dependency or loader. "
                "The React loader assumption needs evidence from package imports "
                "before treating it as a finding. The review should rank the "
                "missing mod/build/package surface above any React-specific loader "
                "concern. We need package/import evidence before calling this "
                "React-based. React is not proven by the TSX filename alone."
            ),
            condition="with-cities2-mod-review",
        )

        self.assertEqual("pass", record.status)

    def test_review_unsupported_claims_rejects_common_react_paraphrases(self) -> None:
        examples = (
            "You need a React loader before this can work.",
            "This needs React installed first because it has a TSX panel.",
            "OptionsPanel.tsx means this is React-based.",
        )

        for transcript in examples:
            with self.subTest(transcript=transcript):
                record = _run_behavior_check(
                    "review-unsupported-claims-absent",
                    transcript=transcript,
                    condition="with-cities2-mod-review",
                )

                self.assertEqual("fail", record.status)

    def test_project_files_inspected_uses_tool_arguments_not_transcript_echo(self) -> None:
        passed = _run_behavior_check(
            "project-files-inspected",
            args=["OptionsPanel.tsx", "theme.css"],
            transcript="I inspected OptionsPanel.tsx and theme.css.",
            events=[
                {
                    "type": "tool_call",
                    "name": "shell_command",
                    "arguments": {
                        "command": "Get-Content ReviewBaitMod/ui/OptionsPanel.tsx; Get-Content ReviewBaitMod/ui/theme.css"
                    },
                },
            ],
            condition="with-cities2-mod-review",
        )
        failed = _run_behavior_check(
            "project-files-inspected",
            args=["OptionsPanel.tsx", "theme.css"],
            transcript="I inspected OptionsPanel.tsx and theme.css.",
            events=[],
            condition="with-cities2-mod-review",
        )

        self.assertEqual("pass", passed.status)
        self.assertEqual("fail", failed.status)
        self.assertIn("missing=['OptionsPanel.tsx', 'theme.css']", failed.detail)

    def test_project_files_inspected_rejects_echoed_filenames(self) -> None:
        record = _run_behavior_check(
            "project-files-inspected",
            args=["OptionsPanel.tsx", "theme.css"],
            events=[
                {
                    "type": "tool_call",
                    "name": "shell_command",
                    "arguments": {"command": "echo OptionsPanel.tsx theme.css"},
                },
            ],
            condition="with-cities2-mod-review",
        )

        self.assertEqual("fail", record.status)
        self.assertIn("OptionsPanel.tsx", record.detail)

    def test_project_files_inspected_rejects_echo_after_reading_other_file(self) -> None:
        record = _run_behavior_check(
            "project-files-inspected",
            args=["ReviewBaitMod/ui/OptionsPanel.tsx", "ReviewBaitMod/ui/theme.css"],
            events=[
                {
                    "type": "tool_call",
                    "name": "shell_command",
                    "arguments": {
                        "command": (
                            "Get-Content ReviewBaitMod/ui/OptionsPanel.tsx; "
                            "echo ReviewBaitMod/ui/theme.css"
                        )
                    },
                },
            ],
            condition="with-cities2-mod-review",
        )

        self.assertEqual("fail", record.status)
        self.assertIn("ReviewBaitMod/ui/theme.css", record.detail)

    def test_project_files_inspected_rejects_piped_echo_after_reading_other_file(self) -> None:
        record = _run_behavior_check(
            "project-files-inspected",
            args=["ReviewBaitMod/ui/OptionsPanel.tsx", "ReviewBaitMod/ui/theme.css"],
            events=[
                {
                    "type": "tool_call",
                    "name": "shell_command",
                    "arguments": {
                        "command": (
                            "Get-Content ReviewBaitMod/ui/OptionsPanel.tsx | "
                            "echo ReviewBaitMod/ui/theme.css"
                        )
                    },
                },
            ],
            condition="with-cities2-mod-review",
        )

        self.assertEqual("fail", record.status)
        self.assertIn("ReviewBaitMod/ui/theme.css", record.detail)

    def test_project_files_inspected_rejects_listing_without_reading_expected_file(self) -> None:
        listing = _run_behavior_check(
            "project-files-inspected",
            args=["WorkflowHandoffMod/README.md"],
            events=[
                {
                    "type": "item.completed",
                    "item": {
                        "type": "command_execution",
                        "command": "Get-ChildItem -Recurse WorkflowHandoffMod/README.md",
                    },
                },
            ],
            condition="with-cities2-modding",
        )
        search_filename_only = _run_behavior_check(
            "project-files-inspected",
            args=["OptionsPanel.tsx"],
            events=[
                {
                    "type": "tool_call",
                    "name": "shell_command",
                    "arguments": {"command": "rg OptionsPanel.tsx"},
                },
            ],
            condition="with-cities2-mod-review",
        )

        self.assertEqual("fail", listing.status)
        self.assertEqual("fail", search_filename_only.status)

    def test_project_files_inspected_accepts_current_codex_command_events(self) -> None:
        record = _run_behavior_check(
            "project-files-inspected",
            args=["OptionsPanel.tsx", "theme.css"],
            events=[
                {
                    "type": "item.completed",
                    "item": {
                        "type": "command_execution",
                        "command": "Get-Content ReviewBaitMod/ui/OptionsPanel.tsx",
                    },
                },
                {
                    "type": "item.completed",
                    "item": {
                        "type": "command_execution",
                        "command": "Get-Content ReviewBaitMod/ui/theme.css",
                    },
                },
            ],
            condition="with-cities2-mod-review",
        )

        self.assertEqual("pass", record.status)

    def test_project_files_inspected_accepts_windows_path_separators(self) -> None:
        record = _run_behavior_check(
            "project-files-inspected",
            args=["WorkflowHandoffMod/README.md", "WorkflowHandoffMod/src/Mod.cs"],
            events=[
                {
                    "type": "item.completed",
                    "item": {
                        "type": "command_execution",
                        "command": "Get-Content -Path 'WorkflowHandoffMod\\README.md'",
                    },
                },
                {
                    "type": "item.completed",
                    "item": {
                        "type": "command_execution",
                        "command": "Get-Content -Path 'WorkflowHandoffMod\\src\\Mod.cs'",
                    },
                },
            ],
            condition="with-cities2-modding",
        )

        self.assertEqual("pass", record.status)

    def test_project_files_inspected_accepts_wrapped_powershell_command(self) -> None:
        record = _run_behavior_check(
            "project-files-inspected",
            args=["WorkflowHandoffMod/README.md", "WorkflowHandoffMod/src/Mod.cs"],
            events=[
                {
                    "type": "item.completed",
                    "item": {
                        "type": "command_execution",
                        "command": (
                            '"C:\\Program Files\\PowerShell\\7\\pwsh.exe" -Command '
                            '"Get-Content -LiteralPath \'WorkflowHandoffMod\\README.md\'"'
                        ),
                    },
                },
                {
                    "type": "item.completed",
                    "item": {
                        "type": "command_execution",
                        "command": (
                            '"C:\\Program Files\\PowerShell\\7\\pwsh.exe" -Command '
                            '"Get-Content -LiteralPath \'WorkflowHandoffMod\\src\\Mod.cs\'"'
                        ),
                    },
                },
            ],
            condition="with-cities2-modding",
        )

        self.assertEqual("pass", record.status)

    def test_project_files_inspected_accepts_project_root_relative_reads(self) -> None:
        record = _run_behavior_check(
            "project-files-inspected",
            args=["WorkflowHandoffMod/README.md", "WorkflowHandoffMod/src/Mod.cs"],
            events=[
                {
                    "type": "item.completed",
                    "item": {
                        "type": "command_execution",
                        "command": (
                            '"C:\\Program Files\\PowerShell\\7\\pwsh.exe" -Command '
                            "'Get-Content README.md'"
                        ),
                    },
                },
                {
                    "type": "item.completed",
                    "item": {
                        "type": "command_execution",
                        "command": (
                            '"C:\\Program Files\\PowerShell\\7\\pwsh.exe" -Command '
                            '"Get-Content src\\Mod.cs"'
                        ),
                    },
                },
            ],
            condition="with-cities2-modding",
        )

        self.assertEqual("pass", record.status)

    def test_modding_workflow_checks_guard_build_playtest_and_routing(self) -> None:
        transcript = (
            "I cannot confirm the build from this fixture, so treat the build "
            "status as unverified until you run it locally. For local playtesting, "
            "install a local package, launch the game, confirm the playset, and "
            "collect Modding.log plus localhost:9444 UI debugger evidence. Public "
            "release is not ready; use cities2-mod-release for release readiness "
            "and cities2-mod-debugging if the UI does not appear."
        )

        self.assertEqual(
            "pass",
            _run_behavior_check("no-unverified-build-claim", transcript=transcript).status,
        )
        self.assertEqual(
            "pass",
            _run_behavior_check("local-playtest-handoff-present", transcript=transcript).status,
        )
        self.assertEqual(
            "pass",
            _run_behavior_check("routes-debug-release-followups", transcript=transcript).status,
        )
        self.assertEqual(
            "pass",
            _run_behavior_check("public-readiness-guarded", transcript=transcript).status,
        )

        unsafe_build = _run_behavior_check(
            "no-unverified-build-claim",
            transcript="The build passed and this is ready to test.",
        )
        unsafe_build_with_unrelated_negation = _run_behavior_check(
            "no-unverified-build-claim",
            transcript="The build passed, but I did not run it locally.",
        )
        unsafe_build_then_uncertainty = _run_behavior_check(
            "no-unverified-build-claim",
            transcript="The build passed. I cannot confirm the build from this fixture.",
        )
        unsafe_common_build_claims = [
            _run_behavior_check("no-unverified-build-claim", transcript=text)
            for text in (
                "It built successfully.",
                "This compiles cleanly.",
                "Packaging is green.",
            )
        ]
        missing_route = _run_behavior_check(
            "routes-debug-release-followups",
            transcript="If the UI does not appear, debug it. Release later.",
        )
        unsafe_public_ready = _run_behavior_check(
            "public-readiness-guarded",
            transcript="The build is unverified, but this is ready for public release.",
        )
        negated_ready = _run_behavior_check(
            "public-readiness-guarded",
            transcript=(
                "The build is unverified until local playtest evidence exists. "
                "Public release is not ready; give a playtest handoff instead "
                "of treating a build as release-ready."
            ),
        )
        natural_blocked_ready = _run_behavior_check(
            "public-readiness-guarded",
            transcript=(
                "The build does not look okay yet. I would not treat this as ready "
                "for public release. It has no successful build and no local "
                "playtest evidence."
            ),
        )
        explicit_no_readiness = _run_behavior_check(
            "public-readiness-guarded",
            transcript=(
                "Public release readiness: no. A successful build is not present, "
                "and even a future successful build would still need local in-game "
                "validation before public release."
            ),
        )

        self.assertEqual("fail", unsafe_build.status)
        self.assertEqual("fail", unsafe_build_with_unrelated_negation.status)
        self.assertEqual("fail", unsafe_build_then_uncertainty.status)
        self.assertEqual(["fail", "fail", "fail"], [record.status for record in unsafe_common_build_claims])
        self.assertEqual("fail", missing_route.status)
        self.assertEqual("fail", unsafe_public_ready.status)
        self.assertEqual("pass", negated_ready.status)
        self.assertEqual("pass", natural_blocked_ready.status)
        self.assertEqual("pass", explicit_no_readiness.status)

        safe_general_rule = _run_behavior_check(
            "no-unverified-build-claim",
            transcript=(
                "Treat a successful build as a local playtest artifact rather "
                "than public-release proof; do not claim this build passed until "
                "it is run locally."
            ),
        )
        negated_success_statement = _run_behavior_check(
            "no-unverified-build-claim",
            transcript=(
                "This is not ready for public release. It has no detected build "
                "profile, no successful build, no package artifact, and no "
                "gameplay verification."
            ),
        )
        absent_success_statement = _run_behavior_check(
            "no-unverified-build-claim",
            transcript=(
                "Public release readiness: no. A successful build is not present, "
                "and even a future successful build would still need local in-game "
                "validation before public release."
            ),
        )
        self.assertEqual("pass", safe_general_rule.status)
        self.assertEqual("pass", negated_success_statement.status)
        self.assertEqual("pass", absent_success_statement.status)

    def test_routes_debug_release_followups_accepts_natural_language_routes(self) -> None:
        record = _run_behavior_check(
            "routes-debug-release-followups",
            transcript=(
                "Use the release workflow only after package and local playtest evidence. "
                "If the in-game UI does not appear, switch to the debugging workflow "
                "with logs and UI debugger evidence."
            ),
        )

        self.assertEqual("pass", record.status)

    def test_knowledge_office_demand_grounding_requires_sources_and_practical_answer(self) -> None:
        grounded = _run_behavior_check(
            "knowledge-office-demand-grounded",
            transcript=(
                "Office demand grows when the city has educated workers, enough jobs, "
                "reasonable office taxes, and low vacancy. Check the demand tooltip "
                "before zoning more offices. Source note: wiki and game encyclopedia "
                "entries for demand and office zones."
            ),
            condition="with-cities2-knowledge",
        )
        unsourced = _run_behavior_check(
            "knowledge-office-demand-grounded",
            transcript=(
                "Office demand grows with educated workers, jobs, taxes, and zoning."
            ),
            condition="with-cities2-knowledge",
        )

        self.assertEqual("pass", grounded.status)
        self.assertEqual("fail", unsourced.status)

    def test_compact_search_query_rejects_full_user_question(self) -> None:
        compact = _run_behavior_check(
            "compact-search-query",
            args=["office", "demand"],
            events=[
                {
                    "type": "tool_call",
                    "name": "search",
                    "arguments": {"query": "office demand education jobs"},
                },
            ],
            condition="with-cities2-knowledge",
        )
        full_question = _run_behavior_check(
            "compact-search-query",
            args=["office", "demand"],
            events=[
                {
                    "type": "tool_call",
                    "name": "search",
                    "arguments": {
                        "query": (
                            "Why is my city asking for so many offices in Cities: Skylines II "
                            "and can I ignore the demand?"
                        )
                    },
                },
            ],
            condition="with-cities2-knowledge",
        )

        self.assertEqual("pass", compact.status)
        self.assertEqual("fail", full_question.status)
        self.assertIn("full_user_question=True", full_question.detail)

    def test_modding_checks_accept_actual_workflow_handoff_language(self) -> None:
        transcript = (
            "There is no successful build output to install. Public release readiness: "
            "no. It is not ready for public release. A successful build would still "
            "not be enough; it needs local gameplay verification, package metadata, "
            "install verification, log review, and a clear description. If the "
            "in-game UI does not appear, check Modding.log and open the UI debugger "
            "at localhost:9444."
        )

        self.assertEqual(
            "pass",
            _run_behavior_check("public-readiness-guarded", transcript=transcript).status,
        )
        self.assertEqual(
            "pass",
            _run_behavior_check("no-unverified-build-claim", transcript=transcript).status,
        )
        self.assertEqual(
            "pass",
            _run_behavior_check("routes-debug-release-followups", transcript=transcript).status,
        )

    def test_check_tool_main_cli_errors_and_default_phase(self) -> None:
        from evals.runner import check_tool

        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            missing_status = check_tool.main([])

        self.assertEqual(2, missing_status)
        self.assertIn("missing check name", stderr.getvalue())

        with tempfile.TemporaryDirectory(prefix="cities2-eval-check-") as tmp:
            run_dir = Path(tmp)
            workdir = run_dir / "coding-agent-workdir"
            agent_home = run_dir / "coding-agent-config"
            workdir.mkdir()
            agent_home.mkdir()
            env = {
                "EVAL_RUN_DIR": str(run_dir),
                "EVAL_WORKDIR": str(workdir),
                "EVAL_AGENT_HOME": str(agent_home),
                "EVAL_CONDITION": "no-skill",
            }

            stdout = io.StringIO()
            with patch.dict(os.environ, env, clear=True):
                with contextlib.redirect_stdout(stdout):
                    status = check_tool.main(["agent-home-contained"])

            data = json.loads(stdout.getvalue())
            self.assertEqual(0, status)
            self.assertEqual("pass", data["status"])
            self.assertEqual("post", data["phase"])

            stderr = io.StringIO()
            env["EVAL_CHECK_PHASE"] = "during"
            with patch.dict(os.environ, env, clear=True):
                with contextlib.redirect_stderr(stderr):
                    invalid_status = check_tool.main(["agent-home-contained"])

            self.assertEqual(2, invalid_status)
            self.assertIn("invalid EVAL_CHECK_PHASE: during", stderr.getvalue())

    @unittest.skipUnless(shutil.which("bash"), "bash is required for checks.sh")
    def test_run_checks_phase_collects_records_from_checks_sh(self) -> None:
        from evals.runner.checks import run_checks_phase

        with tempfile.TemporaryDirectory(prefix="cities2-eval-checks-") as tmp:
            run_dir = Path(tmp)
            workdir = run_dir / "coding-agent-workdir"
            agent_home = run_dir / "coding-agent-config"
            checks = run_dir / "checks.sh"
            workdir.mkdir()
            agent_home.mkdir()
            checks.write_text(
                "pre() {\n"
                "    python -m evals.runner.check_tool agent-home-contained\n"
                "}\n"
                "post() { :; }\n",
                encoding="utf-8",
            )

            records = run_checks_phase(
                checks,
                "pre",
                run_dir=run_dir,
                workdir=workdir,
                agent_home=agent_home,
                condition="no-skill",
                repo_root=ROOT,
            )

            self.assertEqual(1, len(records))
            self.assertEqual("agent-home-contained", records[0].name)
            self.assertEqual("pass", records[0].status)

    def test_read_records_requires_declared_fields(self) -> None:
        from evals.runner.checks import _read_records

        with tempfile.TemporaryDirectory(prefix="cities2-eval-checks-") as tmp:
            sink = Path(tmp) / "post-checks.jsonl"
            sink.write_text(
                json.dumps(
                    {
                        "name": "missing-detail",
                        "phase": "post",
                        "status": "pass",
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            with self.assertRaises(KeyError):
                _read_records(sink)

    def test_read_records_rejects_malformed_jsonl_records(self) -> None:
        from evals.runner.checks import _read_records

        with tempfile.TemporaryDirectory(prefix="cities2-eval-checks-") as tmp:
            sink = Path(tmp) / "post-checks.jsonl"
            sink.write_text("{not-json}\n", encoding="utf-8")

            with self.assertRaises(json.JSONDecodeError):
                _read_records(sink)

            sink.write_text('"not-an-object"\n', encoding="utf-8")

            with self.assertRaises(TypeError):
                _read_records(sink)

    def test_source_command_drive_fallback_uses_current_shell(self) -> None:
        from evals.runner.checks import _source_command

        with patch("evals.runner.checks._bash_path", return_value="Z:/evals/checks.sh"):
            command = _source_command(Path("checks.sh"), wsl=False)

        self.assertTrue(command.startswith("{ "), command)
        self.assertTrue(command.endswith("; }"), command)
        self.assertNotRegex(command, r"^\(")

    def test_run_checks_phase_reports_missing_bash_as_failed_check(self) -> None:
        from evals.runner.checks import run_checks_phase

        with tempfile.TemporaryDirectory(prefix="cities2-eval-checks-") as tmp:
            run_dir = Path(tmp)
            workdir = run_dir / "coding-agent-workdir"
            agent_home = run_dir / "coding-agent-config"
            checks = run_dir / "checks.sh"
            workdir.mkdir()
            agent_home.mkdir()
            checks.write_text("pre() { :; }\npost() { :; }\n", encoding="utf-8")

            with patch(
                "evals.runner.checks.subprocess.run",
                side_effect=FileNotFoundError("bash"),
            ):
                records = run_checks_phase(
                    checks,
                    "pre",
                    run_dir=run_dir,
                    workdir=workdir,
                    agent_home=agent_home,
                    condition="no-skill",
                    repo_root=ROOT,
                )

        self.assertEqual(1, len(records))
        self.assertEqual("pre-checks", records[0].name)
        self.assertEqual("fail", records[0].status)
        self.assertIn("bash executable not found", records[0].detail)

    def test_run_checks_phase_records_nonzero_exit_after_check_records(self) -> None:
        from evals.runner.checks import run_checks_phase

        with tempfile.TemporaryDirectory(prefix="cities2-eval-checks-") as tmp:
            run_dir = Path(tmp)
            workdir = run_dir / "coding-agent-workdir"
            agent_home = run_dir / "coding-agent-config"
            checks = run_dir / "checks.sh"
            sink = run_dir / "pre-checks.jsonl"
            workdir.mkdir()
            agent_home.mkdir()
            checks.write_text("pre() { :; }\npost() { :; }\n", encoding="utf-8")

            def run_with_partial_record(*args: object, **kwargs: object) -> object:
                sink.write_text(
                    json.dumps(
                        {
                            "name": "first-check",
                            "phase": "pre",
                            "status": "pass",
                            "detail": "recorded before crash",
                        }
                    )
                    + "\n",
                    encoding="utf-8",
                )
                return subprocess.CompletedProcess(
                    args=args,
                    returncode=7,
                    stdout="before crash\n",
                    stderr="script crashed\n",
                )

            with patch("evals.runner.checks._is_wsl_bash", return_value=False):
                with patch(
                    "evals.runner.checks.subprocess.run",
                    side_effect=run_with_partial_record,
                ):
                    records = run_checks_phase(
                        checks,
                        "pre",
                        run_dir=run_dir,
                        workdir=workdir,
                        agent_home=agent_home,
                        condition="no-skill",
                        repo_root=ROOT,
                    )

        self.assertEqual(
            ["first-check", "pre-checks"],
            [record.name for record in records],
        )
        self.assertEqual("pass", records[0].status)
        self.assertEqual("fail", records[1].status)
        self.assertIn("exit=7", records[1].detail)

    def test_run_checks_phase_reports_malformed_records_as_failed_check(self) -> None:
        from evals.runner.checks import run_checks_phase

        with tempfile.TemporaryDirectory(prefix="cities2-eval-checks-") as tmp:
            run_dir = Path(tmp)
            workdir = run_dir / "coding-agent-workdir"
            agent_home = run_dir / "coding-agent-config"
            checks = run_dir / "checks.sh"
            sink = run_dir / "pre-checks.jsonl"
            workdir.mkdir()
            agent_home.mkdir()
            checks.write_text("pre() { :; }\npost() { :; }\n", encoding="utf-8")

            def run_with_malformed_record(*args: object, **kwargs: object) -> object:
                sink.write_text("{not-json}\n", encoding="utf-8")
                return subprocess.CompletedProcess(
                    args=args,
                    returncode=7,
                    stdout="before crash\n",
                    stderr="script crashed\n",
                )

            with patch("evals.runner.checks._is_wsl_bash", return_value=False):
                with patch(
                    "evals.runner.checks.subprocess.run",
                    side_effect=run_with_malformed_record,
                ):
                    records = run_checks_phase(
                        checks,
                        "pre",
                        run_dir=run_dir,
                        workdir=workdir,
                        agent_home=agent_home,
                        condition="no-skill",
                        repo_root=ROOT,
                    )

        self.assertEqual(1, len(records))
        self.assertEqual("pre-checks", records[0].name)
        self.assertEqual("fail", records[0].status)
        self.assertIn("invalid check record", records[0].detail)
        self.assertIn("exit=7", records[0].detail)


if __name__ == "__main__":
    unittest.main()
