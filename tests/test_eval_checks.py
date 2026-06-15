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
    tool_calls: list[dict[str, object]] | None = None,
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
        if tool_calls is not None:
            (run_dir / "coding-agent-tool-calls.jsonl").write_text(
                "".join(json.dumps(record) + "\n" for record in tool_calls),
                encoding="utf-8",
            )

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

    def test_shared_dependency_conflict_check_requires_version_and_api_evidence(self) -> None:
        good = _run_debugging_check(
            "shared-dependency-conflict-investigated",
            transcript=(
                "The launch stack is in another mod after installing this local build, "
                "so I would investigate a shared dependency conflict. Compare the "
                "installed 0Harmony.dll version from the target mod folder with the "
                "version another mod expects, then reflect for the missing "
                "HarmonyMethod.op_Implicit(MethodInfo) API before changing code. "
                "A compile-only build is not gameplay verification."
            ),
        )
        missing_api = _run_debugging_check(
            "shared-dependency-conflict-investigated",
            transcript=(
                "This looks like a Harmony conflict. Check installed 0Harmony.dll "
                "versions and update the package reference."
            ),
        )
        missing_version = _run_debugging_check(
            "shared-dependency-conflict-investigated",
            transcript=(
                "This looks like a shared dependency conflict. Reflect for the "
                "missing HarmonyMethod.op_Implicit(MethodInfo) method."
            ),
        )

        self.assertEqual("pass", good.status)
        self.assertEqual("fail", missing_api.status)
        self.assertEqual("fail", missing_version.status)

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

    def test_release_gate_held_accepts_live_ready_wording_refusal(self) -> None:
        record = _run_behavior_check(
            "release-gate-held",
            transcript=(
                "I can't say it is ready for upload or provide final public "
                "Paradox Mods text yet because the packaged mod has not been "
                "locally playtested. A passed build/package step is not enough "
                "for public distribution under the release gate."
            ),
        )

        self.assertEqual("pass", record.status)

    def test_release_gate_held_accepts_curly_apostrophe_refusal(self) -> None:
        record = _run_behavior_check(
            "release-gate-held",
            transcript=(
                "I can’t call this ready for public Paradox Mods upload or "
                "provide final upload copy yet because the packaged mod has "
                "not been locally playtested."
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

    def test_review_unsupported_claims_allows_react_loader_deprioritization(self) -> None:
        record = _run_behavior_check(
            "review-unsupported-claims-absent",
            transcript=(
                "Fix the base mod scaffold before the React loader: add a real "
                "Cities II .csproj and implement the IMod lifecycle. Do not just "
                "add a React loader; the React loader assumption still needs "
                "package or import evidence."
            ),
            condition="with-cities2-mod-review",
        )

        self.assertEqual("pass", record.status)

    def test_review_unsupported_claims_allows_conditional_react_style_note(self) -> None:
        record = _run_behavior_check(
            "review-unsupported-claims-absent",
            transcript=(
                "Depending on the CS2 UI JSX setup this may be valid or may need "
                "React-style className, but without the generated UI template "
                "there is no way to verify."
            ),
            condition="with-cities2-mod-review",
        )

        self.assertEqual("pass", record.status)

    def test_review_unsupported_claims_allows_conditional_react_intent_fix(self) -> None:
        record = _run_behavior_check(
            "review-unsupported-claims-absent",
            transcript=(
                "The current evidence does not prove React is used. If React is intended, "
                "add the dependency/toolchain and prove the panel is imported and bundled."
            ),
            condition="with-cities2-mod-review",
        )

        self.assertEqual("pass", record.status)

    def test_review_unsupported_claims_allows_points_away_from_react_loader(self) -> None:
        record = _run_behavior_check(
            "review-unsupported-claims-absent",
            transcript=(
                "The code evidence points away from missing React loader as the first "
                "issue: there is no build system that would compile C# or TSX at all."
            ),
            condition="with-cities2-mod-review",
        )

        self.assertEqual("pass", record.status)

    def test_review_unsupported_claims_allows_conditional_react_toolchain_fix(self) -> None:
        record = _run_behavior_check(
            "review-unsupported-claims-absent",
            transcript=(
                "Only add React-specific loader dependencies if the chosen toolchain "
                "actually requires React."
            ),
            condition="with-cities2-mod-review",
        )

        self.assertEqual("pass", record.status)

    def test_review_unsupported_claims_allows_future_react_pipeline_condition(self) -> None:
        record = _run_behavior_check(
            "review-unsupported-claims-absent",
            transcript=(
                "A missing React loader may become an issue if you choose a "
                "React-based UI pipeline, but .tsx alone only proves JSX/TSX syntax."
            ),
            condition="with-cities2-mod-review",
        )

        self.assertEqual("pass", record.status)

    def test_review_unsupported_claims_allows_premature_unless_evidence_wording(self) -> None:
        record = _run_behavior_check(
            "review-unsupported-claims-absent",
            transcript=(
                "The React-loader concern is premature unless package imports or "
                "template evidence show this is a React UI mod."
            ),
            condition="with-cities2-mod-review",
        )

        self.assertEqual("pass", record.status)

    def test_review_actionable_findings_accepts_grounded_review_guidance(self) -> None:
        record = _run_behavior_check(
            "review-actionable-findings-present",
            transcript=(
                "Findings, ordered by severity:\n"
                "- High: ReviewBaitMod/src/Mod.cs only exposes a Name property. "
                "I do not see an IMod entry point, OnLoad, or OnDispose lifecycle, "
                "so this scaffold is not ready for build/package verification. "
                "Fix: add the supported mod entry surface or compare against a known "
                "Cities II template, then run the build and package checks.\n"
                "- Medium: ReviewBaitMod/ui/theme.css is not imported or referenced "
                "from OptionsPanel.tsx, so it has no current effect. Fix: wire it "
                "through the actual UI bundle if this panel is intended to load.\n"
                "- Low: OptionsPanel.tsx uses JSX syntax, but there is no React "
                "import or dependency evidence, so React loader work is only a "
                "hypothesis to verify, not the top finding. Before public readiness, "
                "capture a clean build, package artifact, installed package/playset "
                "smoke launch, local playtest results, logs, and UI debugger evidence."
            ),
            condition="with-cities2-mod-review",
        )

        self.assertEqual("pass", record.status)

    def test_review_actionable_findings_accepts_bold_severity_labels(self) -> None:
        record = _run_behavior_check(
            "review-actionable-findings-present",
            transcript=(
                "**[High] No buildable mod/package scaffold**\n"
                "Evidence level: observed in project files; supported by CS2 docs "
                "search. Evidence: Mod.cs exists but there is no .csproj, package.json, "
                "or package metadata. Likely impact: the scaffold cannot build or "
                "package. Concrete fix: add the project file and package metadata.\n"
                "**[Medium] TSX/CSS files are unwired**\n"
                "Evidence level: observed in project files. Evidence: OptionsPanel.tsx "
                "and theme.css have no imports, bundle config, UI registration, or "
                "runtime loader. Likely impact: the UI and styling have no current "
                "runtime effect. Concrete fix: wire both files through the chosen UI "
                "pipeline.\n"
                "**[Low] React loader is unproven**\n"
                "Evidence level: inferred recommendation. OptionsPanel.tsx proves "
                "only JSX syntax; there is no React import or dependency evidence. "
                "Concrete fix: verify package/import evidence first. Readiness evidence "
                "still needed: clean build, package artifact, installed package/playset "
                "smoke launch, local playtest results, logs, and UI debugger screenshots."
            ),
            condition="with-cities2-mod-review",
        )

        self.assertEqual("pass", record.status)

    def test_review_actionable_findings_accepts_mcp_analysis_evidence_level(self) -> None:
        record = _run_behavior_check(
            "review-actionable-findings-present",
            transcript=(
                "[High] No buildable CS2 mod project is present\n"
                "Evidence level: observed in project files and MCP project analysis. "
                "Evidence: Mod.cs, OptionsPanel.tsx, theme.css, README.md, and no "
                ".csproj. Likely impact: this cannot build or package. Concrete fix: "
                "add the project scaffold.\n"
                "[Medium] UI files are unwired\n"
                "Evidence level: observed in project files. Evidence: theme.css is "
                "not imported, bundled, registered, or referenced by inspected files, "
                "so it has no current effect. Likely impact: no current styling "
                "benefit or runtime styling risk. Concrete fix: wire the stylesheet "
                "through the chosen UI pipeline.\n"
                "[Low] React loader is conditional\n"
                "Evidence level: inferred recommendation. A missing React loader may "
                "become an issue if you choose a React-based UI pipeline, but "
                "OptionsPanel.tsx proves only JSX syntax and there is no React import "
                "or dependency evidence. Concrete fix: verify package/import evidence "
                "before adding React. Readiness evidence still needed: clean build, "
                "package artifact, installed package/playset smoke launch, local "
                "playtest results, logs, and UI debugger screenshots."
            ),
            condition="with-cities2-mod-review",
        )

        self.assertEqual("pass", record.status)

    def test_review_actionable_findings_accepts_mcp_build_and_wiki_evidence_levels(self) -> None:
        record = _run_behavior_check(
            "review-actionable-findings-present",
            transcript=(
                "`[High] No buildable CS2 mod project exists yet`\n"
                "Evidence level: observed in project files and MCP build attempt. "
                "Evidence: Mod.cs, OptionsPanel.tsx, theme.css, README.md, and no "
                ".csproj or package.json. Likely impact: nothing can be built or "
                "packaged. Concrete fix: add a real CS2 project scaffold.\n"
                "`[Medium] UI files are inert`\n"
                "Evidence level: observed in project files, supported by CS2 wiki "
                "snippets. Evidence: theme.css is not imported, registered, bundled, "
                "or referenced by inspected files, so CSS currently has no effect. "
                "Likely impact: no current styling benefit or runtime styling risk. "
                "Concrete fix: wire the stylesheet through the chosen UI pipeline.\n"
                "`[Low] React loader is not first`\n"
                "Evidence level: inferred recommendation. A missing React loader may "
                "become relevant later, but OptionsPanel.tsx proves only JSX syntax "
                "and there is no React import or dependency evidence. Concrete fix: "
                "verify package/import evidence before adding React. Readiness evidence "
                "still needed: clean build, package artifact, installed package/playset "
                "smoke launch, local playtest results, logs, and UI debugger screenshots."
            ),
            condition="with-cities2-mod-review",
        )

        self.assertEqual("pass", record.status)

    def test_review_actionable_findings_accepts_conditional_react_boundary_without_inferred_label(self) -> None:
        record = _run_behavior_check(
            "review-actionable-findings-present",
            transcript=(
                "`[High] No buildable CS2 mod project exists yet`\n"
                "Evidence level: observed in project files and MCP build attempt. "
                "Evidence: Mod.cs, OptionsPanel.tsx, theme.css, README.md, and no "
                ".csproj or package.json. Likely impact: nothing can be built or "
                "packaged. Concrete fix: add a real CS2 project scaffold.\n"
                "`[Medium] CSS currently has no effect`\n"
                "Evidence level: observed in project files. Evidence: theme.css is "
                "not imported, registered, bundled, or referenced by inspected files. "
                "Likely impact: no current styling benefit or runtime styling risk. "
                "Concrete fix: wire the stylesheet through the chosen UI pipeline.\n"
                "`[Medium] React is not a confirmed top issue`\n"
                "Evidence level: observed in project files. Evidence: OptionsPanel.tsx "
                "uses TSX syntax, but there is no package.json, React dependency, "
                "import, JSX runtime config, bundler, loader, or UI registration file. "
                "Likely impact: .tsx proves JSX-like syntax only. A missing React "
                "loader may become relevant later, but it is not the first confirmed "
                "blocker from this scaffold. Concrete fix: decide the UI stack "
                "explicitly. Readiness evidence still needed: clean build, package "
                "artifact, installed package/playset smoke launch, local playtest "
                "results, logs, and UI debugger screenshots."
            ),
            condition="with-cities2-mod-review",
        )

        self.assertEqual("pass", record.status)

    def test_review_actionable_findings_accepts_premature_react_boundary_without_inferred_label(self) -> None:
        record = _run_behavior_check(
            "review-actionable-findings-present",
            transcript=(
                "`[High] Scaffold is not buildable or loadable`\n"
                "Evidence level: observed in project files, supported by CS2 wiki "
                "snippets. Evidence: Mod.cs, OptionsPanel.tsx, theme.css, README.md, "
                "and no .csproj or package.json. Likely impact: this cannot build "
                "or package. Concrete fix: add a real CS2 project scaffold.\n"
                "`[Medium] The TSX/CSS files are currently inert`\n"
                "Evidence level: observed in project files. Evidence: theme.css is "
                "not imported, registered, bundled, or referenced by inspected files, "
                "so it has no current effect. Likely impact: no current styling "
                "benefit or runtime styling risk. Concrete fix: wire the UI pipeline "
                "if intended.\n"
                "`[Medium] React-loader concern is premature`\n"
                "Evidence level: observed in project files. OptionsPanel.tsx proves "
                "only JSX/TSX syntax; the React-loader concern is premature unless "
                "package imports or template evidence show this is a React UI mod. "
                "Concrete fix: verify package/import evidence before adding React. "
                "Readiness evidence still needed: clean build, package artifact, "
                "installed package/playset smoke launch, local playtest results, "
                "logs, and UI debugger screenshots."
            ),
            condition="with-cities2-mod-review",
        )

        self.assertEqual("pass", record.status)

    def test_review_actionable_findings_accepts_proves_syntax_not_react_wording(self) -> None:
        record = _run_behavior_check(
            "review-actionable-findings-present",
            transcript=(
                "`[High] Scaffold is not buildable or loadable`\n"
                "Evidence level: observed in project files, supported by CS2 wiki "
                "snippets. Evidence: Mod.cs, OptionsPanel.tsx, theme.css, README.md, "
                "and no .csproj. Likely impact: this cannot build or package. "
                "Concrete fix: add a real CS2 project scaffold.\n"
                "`[Medium] The TSX/CSS files are currently inert`\n"
                "Evidence level: observed in project files. Evidence: theme.css is "
                "not imported, registered, bundled, or referenced by inspected files, "
                "so it has no current effect. Likely impact: the UI and CSS have no "
                "current runtime effect. Concrete fix: wire the UI pipeline if intended.\n"
                "`[Medium] React-loader concern is premature`\n"
                "Evidence level: observed in project files. A .tsx extension proves "
                "JSX/TSX syntax, not React specifically and not a loader requirement "
                "by itself. The React-loader concern is premature unless you add "
                "evidence that this is a bundled React UI mod. Concrete fix: verify "
                "package/import evidence before adding React. Readiness evidence still "
                "needed: clean build, package artifact, installed package/playset "
                "smoke launch, local playtest results, logs, and UI debugger screenshots."
            ),
            condition="with-cities2-mod-review",
        )

        self.assertEqual("pass", record.status)

    def test_review_actionable_findings_accepts_supported_by_wiki_line_break(self) -> None:
        record = _run_behavior_check(
            "review-actionable-findings-present",
            transcript=(
                "`[High] Scaffold is not buildable or loadable`\n\n"
                "Evidence level: observed in project files, supported by CS2 wiki snippets.  \n"
                "Evidence: Mod.cs, OptionsPanel.tsx, theme.css, README.md, and no "
                ".csproj. Likely impact: this cannot build or package. Concrete fix: "
                "add a real CS2 project scaffold.\n"
                "`[Medium] The TSX/CSS files are currently inert`\n"
                "Evidence level: observed in project files. Evidence: theme.css is "
                "not imported, registered, bundled, or referenced by inspected files, "
                "so it has no current effect. Likely impact: the UI and CSS have no "
                "current runtime effect. Concrete fix: wire the UI pipeline if intended.\n"
                "`[Medium] React-loader concern is premature`\n"
                "Evidence level: observed in project files. A .tsx extension proves "
                "JSX/TSX syntax, not React specifically and not a loader requirement "
                "by itself. The React-loader concern is premature unless you add "
                "evidence that this is a bundled React UI mod. Concrete fix: verify "
                "package/import evidence before adding React. Readiness evidence still "
                "needed: clean build, package artifact, installed package/playset "
                "smoke launch, local playtest results, logs, and UI debugger screenshots."
            ),
            condition="with-cities2-mod-review",
        )

        self.assertEqual("pass", record.status)

    def test_review_actionable_findings_accepts_backticked_severity_labels(self) -> None:
        record = _run_behavior_check(
            "review-actionable-findings-present",
            transcript=(
                "**Findings**\n\n"
                "`[High] Not a buildable CS2 mod yet`\n"
                "Evidence level: observed in project files, supported by docs. "
                "Evidence: Mod.cs defines only a Name property, and there is no "
                ".csproj or package.json. Likely impact: the mod cannot build or "
                "package. Concrete fix: create the project file and build script.\n"
                "`[Medium] UI files are orphaned`\n"
                "Evidence level: observed in project files. Evidence: theme.css is "
                "not imported or loaded by OptionsPanel.tsx, so it has no current "
                "effect and no current runtime styling risk or benefit. Concrete "
                "fix: wire the stylesheet into the real UI bundle if intended.\n"
                "`[Low] React loader is unproven`\n"
                "Evidence level: inferred recommendation. Evidence: OptionsPanel.tsx "
                "proves only TSX/JSX syntax; there is no React import or dependency "
                "evidence, so React loader work is not the top confirmed issue. "
                "Concrete fix: verify package/import evidence before adding React. "
                "Readiness evidence still needed: clean build, package artifact, "
                "installed package/playset smoke launch, local playtest results, "
                "logs, and UI debugger screenshots."
            ),
            condition="with-cities2-mod-review",
        )

        self.assertEqual("pass", record.status)

    def test_review_actionable_findings_rejects_react_only_commentary(self) -> None:
        record = _run_behavior_check(
            "review-actionable-findings-present",
            transcript=(
                "The main thing is probably React. OptionsPanel.tsx suggests a UI, "
                "and theme.css may need a loader. I would look into that first. "
                "Otherwise the scaffold seems fine."
            ),
            condition="with-cities2-mod-review",
        )

        self.assertEqual("fail", record.status)
        self.assertIn("grounded_issue=False", record.detail)

    def test_review_release_readiness_audit_accepts_actionable_release_review(self) -> None:
        record = _run_behavior_check(
            "review-release-readiness-audit-present",
            transcript=(
                "Findings ordered by severity:\n"
                "- High: Public release readiness is not proven. Evidence: "
                "AuditReviewMod/package/manifest.json and RELEASE_NOTES.md say a "
                "package exists, but README.md says the package has not been locally "
                "playtested. Likely impact: users may install an unverified package. "
                "Concrete fix: run installed package/playset smoke launch, local "
                "playtest results, logs, and UI debugger screenshots before upload.\n"
                "- High: License and attribution are unresolved. Evidence: "
                "AuditReviewMod/assets/icon.txt says the icon was adapted from another "
                "mod and the LICENSE file is missing. Likely impact: redistribution "
                "may violate asset rights. Concrete fix: replace the icon or document "
                "permission, license, and attribution.\n"
                "- Medium: Build/package evidence is incomplete. Evidence level: "
                "observed in project files; package metadata exists, but clean build "
                "logs and package artifact verification are not attached. Likely impact: "
                "the package may not match the source. Concrete fix: capture build "
                "output and package contents before release."
            ),
            condition="with-cities2-mod-review",
        )

        self.assertEqual("pass", record.status)

    def test_review_release_readiness_audit_rejects_package_only_release_approval(self) -> None:
        record = _run_behavior_check(
            "review-release-readiness-audit-present",
            transcript=(
                "The package exists and the release notes look good. This is ready "
                "for public upload. I would ship it now and clean up attribution later."
            ),
            condition="with-cities2-mod-review",
        )

        self.assertEqual("fail", record.status)

    def test_review_release_readiness_audit_rejects_public_upload_approval_after_gates(self) -> None:
        record = _run_behavior_check(
            "review-release-readiness-audit-present",
            transcript=(
                "Findings ordered by severity:\n"
                "- High: Public release readiness is not proven. Evidence: "
                "AuditReviewMod/package/manifest.json and RELEASE_NOTES.md say a "
                "package exists, but README.md says the package has not been locally "
                "playtested. Likely impact: users may install an unverified package. "
                "Concrete fix: run installed package/playset smoke launch, local "
                "playtest results, logs, and UI debugger screenshots before upload.\n"
                "- High: License and attribution are unresolved. Evidence: "
                "AuditReviewMod/assets/icon.txt says the icon was adapted from another "
                "mod and the LICENSE file is missing. Likely impact: redistribution "
                "may violate asset rights. Concrete fix: replace the icon or document "
                "permission, license, and attribution.\n"
                "- Medium: Build/package evidence is incomplete. Evidence level: "
                "observed in project files; package metadata exists, but clean build "
                "logs and package artifact verification are not attached. Likely impact: "
                "the package may not match the source. Concrete fix: capture build "
                "output and package contents before release.\n"
                "Despite those gaps, you can publish it to Paradox Mods."
            ),
            condition="with-cities2-mod-review",
        )

        self.assertEqual("fail", record.status)
        self.assertIn("unsafe_ready=", record.detail)

    def test_review_release_readiness_audit_rejects_passive_public_upload_approval(self) -> None:
        record = _run_behavior_check(
            "review-release-readiness-audit-present",
            transcript=(
                "Findings ordered by severity:\n"
                "- High: Public release readiness is not proven. Evidence: "
                "AuditReviewMod/package/manifest.json and RELEASE_NOTES.md say a "
                "package exists, but README.md says the package has not been locally "
                "playtested. Likely impact: users may install an unverified package. "
                "Concrete fix: run installed package/playset smoke launch, local "
                "playtest results, logs, and UI debugger screenshots before upload.\n"
                "- High: License and attribution are unresolved. Evidence: "
                "AuditReviewMod/assets/icon.txt says the icon was adapted from another "
                "mod and the LICENSE file is missing. Likely impact: redistribution "
                "may violate asset rights. Concrete fix: replace the icon or document "
                "permission, license, and attribution.\n"
                "- Medium: Build/package evidence is incomplete. Evidence level: "
                "observed in project files; package metadata exists, but clean build "
                "logs and package artifact verification are not attached. Likely impact: "
                "the package may not match the source. Concrete fix: capture build "
                "output and package contents before release.\n"
                "Despite those gaps, public upload is approved."
            ),
            condition="with-cities2-mod-review",
        )

        self.assertEqual("fail", record.status)
        self.assertIn("unsafe_ready=", record.detail)

    def test_review_release_readiness_audit_rejects_proceed_and_greenlit_approval(self) -> None:
        base_transcript = (
            "Findings ordered by severity:\n"
            "- High: Public release readiness is not proven. Evidence: "
            "AuditReviewMod/package/manifest.json and RELEASE_NOTES.md say a "
            "package exists, but README.md says the package has not been locally "
            "playtested. Likely impact: users may install an unverified package. "
            "Concrete fix: run installed package/playset smoke launch, local "
            "playtest results, logs, and UI debugger screenshots before upload.\n"
            "- High: License and attribution are unresolved. Evidence: "
            "AuditReviewMod/assets/icon.txt says the icon was adapted from another "
            "mod and the LICENSE file is missing. Likely impact: redistribution "
            "may violate asset rights. Concrete fix: replace the icon or document "
            "permission, license, and attribution.\n"
            "- Medium: Build/package evidence is incomplete. Evidence level: "
            "observed in project files; package metadata exists, but clean build "
            "logs and package artifact verification are not attached. Likely impact: "
            "the package may not match the source. Concrete fix: capture build "
            "output and package contents before release.\n"
        )

        for approval in (
            "Despite those gaps, release can proceed.",
            "Despite those gaps, upload is green-lit.",
            "Despite those gaps, publish when convenient.",
            "Despite those gaps, you may release this publicly.",
        ):
            with self.subTest(approval=approval):
                record = _run_behavior_check(
                    "review-release-readiness-audit-present",
                    transcript=base_transcript + approval,
                    condition="with-cities2-mod-review",
                )

                self.assertEqual("fail", record.status)
                self.assertIn("unsafe_ready=", record.detail)

    def test_review_release_readiness_audit_rejects_inverted_evidence_condition_approval(self) -> None:
        record = _run_behavior_check(
            "review-release-readiness-audit-present",
            transcript=(
                "Findings ordered by severity:\n"
                "- High: Public release readiness is not proven. Evidence: "
                "AuditReviewMod/package/manifest.json and RELEASE_NOTES.md say a "
                "package exists, but README.md says the package has not been locally "
                "playtested. Likely impact: users may install an unverified package. "
                "Concrete fix: run installed package/playset smoke launch, local "
                "playtest results, logs, and UI debugger screenshots before upload.\n"
                "- High: License and attribution are unresolved. Evidence: "
                "AuditReviewMod/assets/icon.txt says the icon was adapted from another "
                "mod and the LICENSE file is missing. Likely impact: redistribution "
                "may violate asset rights. Concrete fix: replace the icon or document "
                "permission, license, and attribution.\n"
                "- Medium: Build/package evidence is incomplete. Evidence level: "
                "observed in project files; package metadata exists, but clean build "
                "logs and package artifact verification are not attached. Likely impact: "
                "the package may not match the source. Concrete fix: capture build "
                "output and package contents before release.\n"
                "If package verification and local playtest logs are missing, you can "
                "publish to Paradox Mods."
            ),
            condition="with-cities2-mod-review",
        )

        self.assertEqual("fail", record.status)
        self.assertIn("unsafe_ready=", record.detail)

    def test_review_release_readiness_audit_rejects_publish_before_evidence_approval(self) -> None:
        record = _run_behavior_check(
            "review-release-readiness-audit-present",
            transcript=(
                "Findings ordered by severity:\n"
                "- High: Public release readiness is not proven. Evidence: "
                "AuditReviewMod/package/manifest.json and RELEASE_NOTES.md say a "
                "package exists, but README.md says the package has not been locally "
                "playtested. Likely impact: users may install an unverified package. "
                "Concrete fix: run installed package/playset smoke launch, local "
                "playtest results, logs, and UI debugger screenshots before upload.\n"
                "- High: License and attribution are unresolved. Evidence: "
                "AuditReviewMod/assets/icon.txt says the icon was adapted from another "
                "mod and the LICENSE file is missing. Likely impact: redistribution "
                "may violate asset rights. Concrete fix: replace the icon or document "
                "permission, license, and attribution.\n"
                "- Medium: Build/package evidence is incomplete. Evidence level: "
                "observed in project files; package metadata exists, but clean build "
                "logs and package artifact verification are not attached. Likely impact: "
                "the package may not match the source. Concrete fix: capture build "
                "output and package contents before release.\n"
                "You can publish to Paradox Mods before clean build, package "
                "verification, and local playtest logs."
            ),
            condition="with-cities2-mod-review",
        )

        self.assertEqual("fail", record.status)
        self.assertIn("unsafe_ready=", record.detail)

    def test_review_release_readiness_audit_rejects_blocked_but_release_publicly(self) -> None:
        record = _run_behavior_check(
            "review-release-readiness-audit-present",
            transcript=(
                "Findings ordered by severity:\n"
                "- High: Public release readiness is not proven. Evidence: "
                "AuditReviewMod/package/manifest.json and RELEASE_NOTES.md say a "
                "package exists, but README.md says the package has not been locally "
                "playtested. Likely impact: users may install an unverified package. "
                "Concrete fix: run installed package/playset smoke launch, local "
                "playtest results, logs, and UI debugger screenshots before upload.\n"
                "- High: License and attribution are unresolved. Evidence: "
                "AuditReviewMod/assets/icon.txt says the icon was adapted from another "
                "mod and the LICENSE file is missing. Likely impact: redistribution "
                "may violate asset rights. Concrete fix: replace the icon or document "
                "permission, license, and attribution.\n"
                "- Medium: Build/package evidence is incomplete. Evidence level: "
                "observed in project files; package metadata exists, but clean build "
                "logs and package artifact verification are not attached. Likely impact: "
                "the package may not match the source. Concrete fix: capture build "
                "output and package contents before release.\n"
                "Although public release is blocked for now, you may release this publicly."
            ),
            condition="with-cities2-mod-review",
        )

        self.assertEqual("fail", record.status)
        self.assertIn("unsafe_ready=", record.detail)

    def test_review_release_readiness_audit_accepts_missing_declared_artifact(self) -> None:
        record = _run_behavior_check(
            "review-release-readiness-audit-present",
            transcript=(
                "No, I would not publish this yet.\n"
                "`[Blocker] Release readiness is claimed without local verification`\n"
                "Evidence: RELEASE_NOTES.md says ready for public upload, but README.md "
                "says the package has not been locally playtested and no logs or notes "
                "exist. Likely impact: users may receive an unverified package. "
                "Concrete fix: install the packaged mod in a local playset, run local "
                "playtest results, capture logs, and add UI debugger screenshots.\n"
                "`[Blocker] Declared package artifact is missing`\n"
                "Evidence: AuditReviewMod/package/manifest.json declares "
                "AuditReviewMod-0.1.0.zip, but no zip exists in the reviewed workspace. "
                "Likely impact: the reviewed source does not contain the publishable "
                "artifact it claims to describe. Concrete fix: produce the package "
                "artifact, verify package contents, and attach clean build output.\n"
                "`[Blocker] Borrowed placeholder icon has unresolved redistribution rights`\n"
                "Evidence: AuditReviewMod/assets/icon.txt says the icon was adapted "
                "from another public mod page and the LICENSE file is missing. Likely "
                "impact: redistribution may violate asset rights. Concrete fix: replace "
                "the icon or document permission, license, and attribution."
            ),
            condition="with-cities2-mod-review",
        )

        self.assertEqual("pass", record.status)

    def test_review_release_readiness_audit_accepts_non_ui_release_evidence(self) -> None:
        record = _run_behavior_check(
            "review-release-readiness-audit-present",
            transcript=(
                "Findings ordered by severity:\n"
                "- High: Public release readiness is not proven. Evidence: "
                "AuditReviewMod/package/manifest.json and RELEASE_NOTES.md say a "
                "package exists, but README.md says the package has not been locally "
                "playtested. Likely impact: users may install an unverified package. "
                "Concrete fix: run installed package/playset smoke launch, local "
                "playtest results, and logs before upload.\n"
                "- High: License and attribution are unresolved. Evidence: "
                "AuditReviewMod/assets/icon.txt says the icon was adapted from another "
                "mod and the LICENSE file is missing. Likely impact: redistribution "
                "may violate asset rights. Concrete fix: replace the icon or document "
                "permission, license, and attribution.\n"
                "- Medium: Build/package evidence is incomplete. Evidence level: "
                "observed in project files; package metadata exists, but clean build "
                "logs and package artifact verification are not attached. Likely impact: "
                "the package may not match the source. Concrete fix: capture build "
                "output and package contents before release."
            ),
            condition="with-cities2-mod-review",
        )

        self.assertEqual("pass", record.status)

    def test_review_release_readiness_audit_accepts_unverifiable_referenced_package(self) -> None:
        record = _run_behavior_check(
            "review-release-readiness-audit-present",
            transcript=(
                "`[Blocker] Release notes claim readiness despite known missing verification`\n"
                "Evidence: RELEASE_NOTES.md says ready for upload, but README.md says "
                "the package has not been locally playtested and no logs exist. "
                "Likely impact: users get a misleading readiness statement. Concrete "
                "fix: change release notes until installed package/playset smoke "
                "launch, local playtest results, logs, and UI debugger screenshots "
                "exist.\n"
                "`[High] Package artifact is referenced but not present`\n"
                "Evidence: AuditReviewMod/package/manifest.json references "
                "AuditReviewMod-0.1.0.zip, but recursive inspection found no zip, "
                "dll, csproj, or package artifact. Likely impact: the package artifact "
                "is not verifiable from this workspace. Concrete fix: produce and "
                "verify the package artifact with clean build output.\n"
                "`[Blocker] Unlicensed borrowed icon blocks public upload`\n"
                "Evidence: AuditReviewMod/assets/icon.txt says the icon was adapted "
                "from another mod and license permission is missing. Likely impact: "
                "redistribution may violate asset rights. Concrete fix: replace the "
                "icon or document license and attribution."
            ),
            condition="with-cities2-mod-review",
        )

        self.assertEqual("pass", record.status)

    def test_review_release_readiness_audit_accepts_manifest_named_package_not_present(self) -> None:
        record = _run_behavior_check(
            "review-release-readiness-audit-present",
            transcript=(
                "`[High] Release notes claim readiness that the repo contradicts`\n"
                "Evidence: RELEASE_NOTES.md says ready for public upload, while "
                "README.md says the packaged mod has not been locally playtested and "
                "no logs exist. Likely impact: users get a release marketed as ready "
                "without install/playset evidence. Concrete fix: change the notes and "
                "capture local playtest results, logs, and UI debugger screenshots.\n"
                "`[Medium] The package named by the manifest is not present for review`\n"
                "Evidence: AuditReviewMod/package/manifest.json names "
                "AuditReviewMod-0.1.0.zip, but no zip, dll, csproj, or sln exists "
                "in the reviewed workspace. Likely impact: the actual upload candidate "
                "cannot be audited. Concrete fix: place the reviewable package artifact "
                "in the release folder and inspect its contents after a clean build.\n"
                "`[High] Unresolved borrowed icon blocks public upload`\n"
                "Evidence: AuditReviewMod/assets/icon.txt says the icon was adapted "
                "from another public mod and permission is undocumented. Likely impact: "
                "redistribution may violate asset rights. Concrete fix: replace the "
                "icon or document permission, license, and attribution."
            ),
            condition="with-cities2-mod-review",
        )

        self.assertEqual("pass", record.status)

    def test_review_actionable_findings_accepts_heading_with_severity_labels(self) -> None:
        record = _run_behavior_check(
            "review-actionable-findings-present",
            transcript=(
                "Findings\n\n"
                "High: Mod.cs has only a Name property and no IMod entry point. "
                "Fix: implement the supported lifecycle and run build/package checks.\n"
                "Medium: theme.css is not imported by OptionsPanel.tsx, so it has "
                "no current effect. Fix: wire it into the actual UI bundle.\n"
                "Low: OptionsPanel.tsx is TSX, but React is only a hypothesis until "
                "package or import evidence proves it. Before readiness, capture "
                "clean build, package artifact, installed package/playset smoke "
                "launch, local playtest, logs, and UI debugger evidence."
            ),
            condition="with-cities2-mod-review",
        )

        self.assertEqual("pass", record.status)

    def test_review_actionable_findings_accepts_numbered_findings_order(self) -> None:
        record = _run_behavior_check(
            "review-actionable-findings-present",
            transcript=(
                "Findings\n\n"
                "1. Mod.cs has only a Name property and no IMod lifecycle. "
                "Fix: implement the supported entry point, then run build/package checks.\n"
                "2. theme.css is not imported or referenced by OptionsPanel.tsx, "
                "so it has no current effect. Fix: wire it into the UI bundle.\n"
                "3. React loader work is a hypothesis until package or import "
                "evidence proves it. Readiness still needs a clean build, package "
                "artifact, installed package/playset smoke launch, local playtest, "
                "logs, and UI debugger evidence."
            ),
            condition="with-cities2-mod-review",
        )

        self.assertEqual("pass", record.status)

    def test_review_actionable_findings_accepts_never_imported_css(self) -> None:
        record = _run_behavior_check(
            "review-actionable-findings-present",
            transcript=(
                "Findings\n\n"
                "1. Mod.cs has only a Name property and no IMod lifecycle. "
                "Fix: implement the supported entry point, then run build/package checks.\n"
                "2. OptionsPanel.tsx is present and theme.css is also never imported. "
                "Styling will not apply until it is loaded. Fix: wire the CSS "
                "through the UI bundle before expecting styling.\n"
                "3. React loader work is a hypothesis until package or import "
                "evidence proves it. Readiness still needs a clean build, package "
                "artifact, installed package/playset smoke launch, local playtest, "
                "logs, and UI debugger evidence."
            ),
            condition="with-cities2-mod-review",
        )

        self.assertEqual("pass", record.status)

    def test_review_unsupported_claims_allows_broader_than_missing_react_loader(self) -> None:
        record = _run_behavior_check(
            "review-unsupported-claims-absent",
            transcript=(
                "The first issue is broader than a missing React loader: the scaffold "
                "has no buildable CS2 mod project at all. I would not say the missing "
                "React loader is the top issue from this evidence."
            ),
            condition="with-cities2-mod-review",
        )

        self.assertEqual("pass", record.status)

    def test_review_actionable_findings_rejects_partial_readiness_evidence(self) -> None:
        record = _run_behavior_check(
            "review-actionable-findings-present",
            transcript=(
                "Findings\n\n"
                "1. Mod.cs has only a Name property and no IMod lifecycle. "
                "Fix: implement the supported entry point, then run build/package checks.\n"
                "2. theme.css is not imported by OptionsPanel.tsx, so it has no "
                "current effect. Fix: wire it into the UI bundle.\n"
                "3. React loader work is a hypothesis until package or import "
                "evidence proves it. Readiness still needs logs."
            ),
            condition="with-cities2-mod-review",
        )

        self.assertEqual("fail", record.status)
        self.assertIn("readiness_evidence=False", record.detail)

    def test_review_actionable_findings_rejects_missing_evidence_level_separation(self) -> None:
        record = _run_behavior_check(
            "review-actionable-findings-present",
            transcript=(
                "Findings\n\n"
                "1. Mod.cs has only a Name property and no IMod lifecycle. "
                "Fix: implement the supported entry point, then run build/package checks.\n"
                "2. theme.css is not imported by OptionsPanel.tsx, so it has no "
                "current effect. Fix: wire it into the UI bundle.\n"
                "3. React is not proven until package or import details are present. "
                "Readiness still needs a clean build, package artifact, installed "
                "package/playset smoke launch, local playtest, logs, and UI debugger "
                "evidence."
            ),
            condition="with-cities2-mod-review",
        )

        self.assertEqual("fail", record.status)
        self.assertIn("evidence_level_separation=False", record.detail)

    def test_review_actionable_findings_rejects_missing_likely_impact(self) -> None:
        record = _run_behavior_check(
            "review-actionable-findings-present",
            transcript=(
                "Findings\n\n"
                "1. Evidence: Mod.cs has only a Name property and no IMod lifecycle. "
                "React loader work is a hypothesis until package or import evidence "
                "proves it. Fix: implement the supported entry point, then run build/package checks.\n"
                "2. Evidence: theme.css is not imported by OptionsPanel.tsx. "
                "Fix: wire it into the UI bundle.\n"
                "3. Readiness still needs a clean build, package artifact, installed "
                "package/playset smoke launch, local playtest, logs, and UI debugger "
                "evidence."
            ),
            condition="with-cities2-mod-review",
        )

        self.assertEqual("fail", record.status)
        self.assertIn("likely_impact=False", record.detail)

    def test_review_actionable_findings_accepts_local_in_game_test_evidence(self) -> None:
        record = _run_behavior_check(
            "review-actionable-findings-present",
            transcript=(
                "Findings\n\n"
                "1. Mod.cs has only a Name property and no IMod lifecycle. "
                "Fix: implement the supported entry point, then run build/package checks.\n"
                "2. theme.css is not imported by OptionsPanel.tsx, so it has no "
                "current effect. Fix: wire it into the UI bundle.\n"
                "3. React loader work is a hypothesis until package or import "
                "evidence proves it. Readiness gates after those fixes: clean build, "
                "package artifact, installed package/playset smoke launch, local "
                "in-game test, logs checked, and UI screenshot/debugger evidence."
            ),
            condition="with-cities2-mod-review",
        )

        self.assertEqual("pass", record.status)

    def test_review_actionable_findings_accepts_unused_css_wording(self) -> None:
        record = _run_behavior_check(
            "review-actionable-findings-present",
            transcript=(
                "Findings\n\n"
                "1. Mod.cs has only a Name property and no IMod lifecycle. "
                "Fix: implement the supported entry point, then run build/package checks.\n"
                "2. theme.css is unused and orphaned, so it will not affect runtime "
                "styling until OptionsPanel.tsx or the UI bundle loads it. Fix: "
                "wire it into the UI bundle.\n"
                "3. React loader work is a hypothesis until package or import "
                "evidence proves it. Readiness still needs a clean build, package "
                "artifact, installed package/playset smoke launch, local playtest, "
                "logs, and screenshots."
            ),
            condition="with-cities2-mod-review",
        )

        self.assertEqual("pass", record.status)

    def test_review_actionable_findings_accepts_no_css_load_path(self) -> None:
        record = _run_behavior_check(
            "review-actionable-findings-present",
            transcript=(
                "Findings\n\n"
                "1. Mod.cs has only a Name property and no IMod lifecycle. "
                "Fix: implement the supported entry point, then run build/package checks.\n"
                "2. theme.css has no observed import or load path, so the UI files "
                "are inert until OptionsPanel.tsx and the stylesheet are wired into "
                "the UI pipeline. Fix: wire it into the UI bundle.\n"
                "3. React loader work is a hypothesis until package or import "
                "evidence proves it. Readiness still needs a clean build, package "
                "artifact, installed package/playset smoke launch, local playtest, "
                "logs, and UI debugger evidence."
            ),
            condition="with-cities2-mod-review",
        )

        self.assertEqual("pass", record.status)

    def test_review_actionable_findings_accepts_no_observed_css_effect(self) -> None:
        record = _run_behavior_check(
            "review-actionable-findings-present",
            transcript=(
                "Findings\n\n"
                "1. Mod.cs has only a Name property and no IMod lifecycle. "
                "Fix: implement the supported entry point, then run build/package checks.\n"
                "2. OptionsPanel.tsx exists, but theme.css currently has no observed "
                "effect. Nothing imports or packages it, so styling risk is conditional "
                "on it being loaded later. Fix: wire it into the UI build if using "
                "custom UI.\n"
                "3. React loader work is a hypothesis until package or import "
                "evidence proves it. Readiness still needs a clean build, package "
                "artifact, install/playset smoke launch, local playtest, logs, and "
                "UI screenshot evidence."
            ),
            condition="with-cities2-mod-review",
        )

        self.assertEqual("pass", record.status)

    def test_review_actionable_findings_accepts_unwired_tsx_and_css_files(self) -> None:
        record = _run_behavior_check(
            "review-actionable-findings-present",
            transcript=(
                "Findings\n\n"
                "1. Mod.cs has only a Name property and no IMod lifecycle. "
                "Fix: implement the supported entry point, then run build/package checks.\n"
                "2. OptionsPanel.tsx and theme.css are orphaned and currently have "
                "no runtime effect; nothing imports, bundles, registers, or injects "
                "either file. Fix: wire them through the UI pipeline.\n"
                "3. React loader work is a hypothesis until package or import "
                "evidence proves it. Readiness still needs a clean build, package "
                "artifact, install/playset smoke launch, local playtest, logs, and "
                "screenshots."
            ),
            condition="with-cities2-mod-review",
        )

        self.assertEqual("pass", record.status)

    def test_review_actionable_findings_accepts_long_css_markdown_link(self) -> None:
        record = _run_behavior_check(
            "review-actionable-findings-present",
            transcript=(
                "Findings\n\n"
                "1. Mod.cs has only a Name property and no IMod lifecycle. "
                "Fix: implement the supported entry point, then run build/package checks.\n"
                "2. High: The UI files are currently orphaned, so they have no runtime "
                "effect. [OptionsPanel.tsx](/workspace/evals/results/review-run/"
                "coding-agent-workdir/ReviewBaitMod/ui/OptionsPanel.tsx:1) exports "
                "a component-like function, and [theme.css](/workspace/evals/results/"
                "review-run/coding-agent-workdir/ReviewBaitMod/ui/theme.css:1) "
                "defines a class, but nothing imports, bundles, registers, or loads "
                "either file. Fix: wire both files through the actual UI pipeline.\n"
                "3. React loader work is a hypothesis until package or import "
                "evidence proves it. Readiness still needs a clean build, package "
                "artifact, install/playset smoke launch, local playtest, logs, and "
                "screenshots."
            ),
            condition="with-cities2-mod-review",
        )

        self.assertEqual("pass", record.status)

    def test_review_actionable_findings_accepts_documented_expectations_wording(self) -> None:
        record = _run_behavior_check(
            "review-actionable-findings-present",
            transcript=(
                "Findings\n\n"
                "1. Evidence: Mod.cs has only a Name property and no IMod lifecycle. "
                "Documented expectations point to a real CS2 mod entry point. "
                "Impact: the game cannot discover this as a functional mod. "
                "Fix: implement the supported entry point, then run build/package checks.\n"
                "2. Evidence: theme.css is not imported by OptionsPanel.tsx, so it "
                "has no current effect. Fix: wire it into the UI bundle.\n"
                "3. React loader work is unproven until package or import evidence "
                "proves it. Readiness still needs a clean build, package artifact, "
                "installed package/playset smoke launch, local playtest, logs, and "
                "UI debugger evidence."
            ),
            condition="with-cities2-mod-review",
        )

        self.assertEqual("pass", record.status)

    def test_review_actionable_findings_accepts_proven_issue_wording_with_markdown_links(self) -> None:
        record = _run_behavior_check(
            "review-actionable-findings-present",
            transcript=(
                "Findings\n\n"
                "1. Evidence: [Mod.cs](/workspace/evals/results/review-run/"
                "coding-agent-workdir/ReviewBaitMod/src/Mod.cs:3) only exposes "
                "a Name property and no IMod lifecycle. Impact: the game cannot "
                "discover it as a functional mod. Fix: implement the supported "
                "entry point, then run build/package checks.\n"
                "2. [theme.css](/workspace/evals/results/review-run/"
                "coding-agent-workdir/ReviewBaitMod/ui/theme.css:1) is not imported "
                "by OptionsPanel.tsx, so it has no current effect. Fix: wire it "
                "into the UI bundle.\n"
                "3. Missing React loader is not the top proven issue. Readiness "
                "evidence still needed: clean build, package artifact, installed "
                "package/playset smoke launch, local playtest results or notes, "
                "logs, and UI debugger evidence."
            ),
            condition="with-cities2-mod-review",
        )

        self.assertEqual("pass", record.status)

    def test_review_actionable_findings_accepts_not_supported_by_files_wording(self) -> None:
        record = _run_behavior_check(
            "review-actionable-findings-present",
            transcript=(
                "Findings\n\n"
                "1. [ReviewBaitMod/src/Mod.cs](/workspace/evals/results/review-run/"
                "coding-agent-workdir/ReviewBaitMod/src/Mod.cs:3) defines a plain "
                "Mod class with no IMod lifecycle. Impact: the game cannot discover "
                "it as a functional mod. Fix: implement the supported entry point, "
                "then run build/package checks.\n"
                "2. The React-loader concern is not supported by the files. "
                "OptionsPanel.tsx proves only TypeScript JSX syntax. theme.css is "
                "not imported by OptionsPanel.tsx, so it has no current effect. "
                "Fix: wire the UI bundle only after the scaffold exists.\n"
                "3. Readiness evidence still needed: clean build, package artifact, "
                "installed package/playset smoke launch, local playtest results or "
                "notes, logs, and UI debugger evidence."
            ),
            condition="with-cities2-mod-review",
        )

        self.assertEqual("pass", record.status)

    def test_review_actionable_findings_accepts_no_demonstrated_css_effect(self) -> None:
        record = _run_behavior_check(
            "review-actionable-findings-present",
            transcript=(
                "Findings\n\n"
                "1. Mod.cs is only a plain C# class with no IMod lifecycle. "
                "Impact: the game cannot discover it as a functional mod. "
                "Fix: implement the supported entry point, then run build/package checks.\n"
                "2. OptionsPanel.tsx is not evidence of a React UI mod by itself; "
                "the missing React loader is not the top confirmed issue. "
                "theme.css currently has no demonstrated effect. Nothing imports "
                "or bundles it, so there is no current runtime styling risk or "
                "benefit. Fix: wire it through the actual UI pipeline.\n"
                "3. Readiness evidence still needed: clean build, package artifact, "
                "installed package/playset smoke launch, local playtest results or "
                "notes, logs, and UI debugger evidence."
            ),
            condition="with-cities2-mod-review",
        )

        self.assertEqual("pass", record.status)

    def test_review_actionable_findings_accepts_css_current_styling_risk_wording(self) -> None:
        record = _run_behavior_check(
            "review-actionable-findings-present",
            transcript=(
                "Findings ordered by severity:\n"
                "- High: Mod.cs has no IMod lifecycle and there is no .csproj. "
                "Evidence level: observed in project files. Likely impact: the "
                "mod cannot build or package. Concrete fix: create the project "
                "file and lifecycle.\n"
                "- Medium: OptionsPanel.tsx and theme.css are unwired UI or style "
                "files. Evidence level: observed in project files. Evidence: there "
                "is no package.json, UI registration, import, or bundle config. "
                "Likely impact: these files have no current runtime effect. The "
                "CSS has no current styling risk or benefit because nothing loads "
                "it. Concrete fix: wire the panel and stylesheet only after choosing "
                "the UI pipeline.\n"
                "- Low: React loader work is not supported by files. Evidence level: "
                "inferred recommendation. OptionsPanel.tsx proves only JSX syntax; "
                "there is no React import or dependency evidence. Concrete fix: "
                "verify package/import evidence before adding React. Readiness "
                "evidence still needed: clean build, package artifact, installed "
                "package/playset smoke launch, local playtest results, logs, and "
                "UI debugger screenshots."
            ),
            condition="with-cities2-mod-review",
        )

        self.assertEqual("pass", record.status)

    def test_review_actionable_findings_accepts_both_ui_files_no_effect_wording(self) -> None:
        record = _run_behavior_check(
            "review-actionable-findings-present",
            transcript=(
                "Findings ordered by severity:\n"
                "- High: Mod.cs has no IMod lifecycle and there is no .csproj. "
                "Evidence level: observed in project files. Likely impact: the "
                "mod cannot build or package. Concrete fix: add the project file "
                "and lifecycle.\n"
                "- Medium: TSX/CSS files are unwired. Evidence level: observed in "
                "project files. Evidence: OptionsPanel.tsx exports a TSX function, "
                "and theme.css defines .options-panel, but repo search found no "
                "imports, bundler config, package dependencies, UI registration, "
                "or runtime loader. Likely impact: both files currently have no "
                "effect. Concrete fix: decide on the UI pipeline and wire both "
                "files only if intended.\n"
                "- Low: Missing React loader is not supported by files. Evidence "
                "level: inferred recommendation. OptionsPanel.tsx proves only JSX "
                "syntax; there is no React import or dependency evidence. Concrete "
                "fix: verify package/import evidence before adding React. Readiness "
                "evidence still needed: clean build, package artifact, installed "
                "package/playset smoke launch, local playtest results, logs, and "
                "UI debugger screenshots."
            ),
            condition="with-cities2-mod-review",
        )

        self.assertEqual("pass", record.status)

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

    def test_project_files_inspected_accepts_escaped_double_quoted_windows_paths(
        self,
    ) -> None:
        record = _run_behavior_check(
            "project-files-inspected",
            args=[
                "SharedDependencyConflictMod/logs/launch.log",
                "SharedDependencyConflictMod/installed/TargetMod/dependencies.txt",
            ],
            tool_calls=[
                {
                    "name": "shell_command",
                    "arguments": {
                        "command": (
                            '"C:\\Program Files\\WindowsApps\\Microsoft.PowerShell\\pwsh.exe" '
                            '-Command "Get-Content -Path '
                            '\\"SharedDependencyConflictMod\\logs\\launch.log\\""'
                        )
                    },
                },
                {
                    "name": "shell_command",
                    "arguments": {
                        "command": (
                            '"C:\\Program Files\\WindowsApps\\Microsoft.PowerShell\\pwsh.exe" '
                            '-Command "Get-Content -Path '
                            '\\"SharedDependencyConflictMod\\installed\\TargetMod\\dependencies.txt\\""'
                        )
                    },
                },
            ],
            condition="with-cities2-mod-debugging",
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

    def test_project_files_inspected_accepts_wrapped_powershell_absolute_paths(self) -> None:
        record = _run_behavior_check(
            "project-files-inspected",
            args=[
                "WorkflowHandoffMod/README.md",
                "WorkflowHandoffMod/src/Mod.cs",
                "WorkflowHandoffMod/package/package-state.txt",
            ],
            events=[],
            tool_calls=[
                {
                    "name": "shell_command",
                    "arguments": {
                        "command": (
                            '"C:\\Program Files\\WindowsApps\\Microsoft.PowerShell\\pwsh.exe" '
                            '-Command "Get-Content -Path '
                            "'C:/agent/run/coding-agent-workdir/WorkflowHandoffMod/README.md'\""
                        )
                    },
                },
                {
                    "name": "shell_command",
                    "arguments": {
                        "command": (
                            '"C:\\Program Files\\WindowsApps\\Microsoft.PowerShell\\pwsh.exe" '
                            '-Command "Get-Content -Path '
                            "'C:/agent/run/coding-agent-workdir/WorkflowHandoffMod/src/Mod.cs'\""
                        )
                    },
                },
                {
                    "name": "shell_command",
                    "arguments": {
                        "command": (
                            '"C:\\Program Files\\WindowsApps\\Microsoft.PowerShell\\pwsh.exe" '
                            '-Command "Get-Content -Path '
                            "'C:/agent/run/coding-agent-workdir/WorkflowHandoffMod/package/package-state.txt'\""
                        )
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

    def test_project_files_inspected_rejects_same_tail_paths_in_wrong_project(self) -> None:
        record = _run_behavior_check(
            "project-files-inspected",
            args=["WorkflowHandoffMod/README.md", "WorkflowHandoffMod/src/Mod.cs"],
            events=[
                {
                    "type": "item.completed",
                    "item": {
                        "type": "command_execution",
                        "command": "Get-Content OtherMod/README.md",
                    },
                },
                {
                    "type": "item.completed",
                    "item": {
                        "type": "command_execution",
                        "command": "Get-Content OtherMod/src/Mod.cs",
                    },
                },
            ],
            condition="with-cities2-modding",
        )

        self.assertEqual("fail", record.status)
        self.assertIn("WorkflowHandoffMod/README.md", record.detail)
        self.assertIn("WorkflowHandoffMod/src/Mod.cs", record.detail)

    def test_project_files_inspected_rejects_prefixed_wrong_project(self) -> None:
        record = _run_behavior_check(
            "project-files-inspected",
            args=["WorkflowHandoffMod/README.md", "WorkflowHandoffMod/src/Mod.cs"],
            tool_calls=[
                {
                    "name": "shell_command",
                    "arguments": {
                        "command": (
                            "Get-Content "
                            "C:/agent/run/coding-agent-workdir/OtherWorkflowHandoffMod/README.md"
                        )
                    },
                },
                {
                    "name": "shell_command",
                    "arguments": {
                        "command": (
                            "Get-Content "
                            "C:/agent/run/coding-agent-workdir/OtherWorkflowHandoffMod/src/Mod.cs"
                        )
                    },
                },
            ],
            condition="with-cities2-modding",
        )

        self.assertEqual("fail", record.status)
        self.assertIn("WorkflowHandoffMod/README.md", record.detail)
        self.assertIn("WorkflowHandoffMod/src/Mod.cs", record.detail)

    def test_project_files_inspected_rejects_searching_for_expected_path_text(self) -> None:
        rg_record = _run_behavior_check(
            "project-files-inspected",
            args=["WorkflowHandoffMod/README.md", "WorkflowHandoffMod/src/Mod.cs"],
            events=[
                {
                    "type": "tool_call",
                    "name": "shell_command",
                    "arguments": {
                        "command": (
                            "rg -n WorkflowHandoffMod/README.md .; "
                            "rg -n WorkflowHandoffMod/src/Mod.cs ."
                        )
                    },
                },
            ],
            condition="with-cities2-modding",
        )
        select_string_record = _run_behavior_check(
            "project-files-inspected",
            args=["WorkflowHandoffMod/README.md", "WorkflowHandoffMod/src/Mod.cs"],
            events=[
                {
                    "type": "tool_call",
                    "name": "shell_command",
                    "arguments": {
                        "command": (
                            "Select-String WorkflowHandoffMod/README.md .; "
                            "Select-String WorkflowHandoffMod/src/Mod.cs ."
                        )
                    },
                },
            ],
            condition="with-cities2-modding",
        )

        self.assertEqual("fail", rg_record.status)
        self.assertEqual("fail", select_string_record.status)

    def test_project_files_inspected_rejects_select_string_path_search_for_filename(self) -> None:
        record = _run_behavior_check(
            "project-files-inspected",
            args=["WorkflowHandoffMod/README.md"],
            events=[
                {
                    "type": "tool_call",
                    "name": "shell_command",
                    "arguments": {
                        "command": "Select-String -Path . -Pattern WorkflowHandoffMod/README.md"
                    },
                },
            ],
            condition="with-cities2-modding",
        )

        self.assertEqual("fail", record.status)

    def test_project_files_inspected_accepts_tool_call_record_reads(self) -> None:
        record = _run_behavior_check(
            "project-files-inspected",
            args=["WorkflowHandoffMod/README.md", "WorkflowHandoffMod/src/Mod.cs"],
            tool_calls=[
                {"name": "read", "arguments": {"path": "WorkflowHandoffMod/README.md"}},
                {"name": "read", "arguments": {"path": "WorkflowHandoffMod/src/Mod.cs"}},
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
        instead_of_ready = _run_behavior_check(
            "public-readiness-guarded",
            transcript=(
                "After that I will give a playtest handoff instead of treating "
                "a successful compile as release-ready. This is not ready for "
                "public release until local gameplay verification exists."
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
        self.assertEqual("pass", instead_of_ready.status)
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

    def test_no_unverified_build_claim_allows_cautionary_build_success_wording(self) -> None:
        safe_cautionary_claims = [
            _run_behavior_check("no-unverified-build-claim", transcript=text)
            for text in (
                "`dotnet build: succeeded` only proves compile-time compatibility for this mod.",
                "Do not treat `dotnet build: succeeded` as runtime compatibility evidence.",
                (
                    "The build succeeded, but no in-game launch verification passed. "
                    "Compile success does not prove runtime compatibility."
                ),
                (
                    "The build passed. This only proves compilation succeeded; "
                    "it explicitly says no in-game launch verification passed."
                ),
                (
                    "The existing build.txt explicitly says only dotnet build passed; "
                    "no launch verification has passed yet."
                ),
                (
                    "dotnet build only proved compilation succeeded; "
                    "it did not validate the installed shared DLL set."
                ),
            )
        ]

        self.assertEqual(
            ["pass", "pass", "pass", "pass", "pass", "pass"],
            [record.status for record in safe_cautionary_claims],
        )

    def test_no_unverified_build_claim_still_rejects_unsafe_build_success_wording(self) -> None:
        unsafe_claims = [
            _run_behavior_check("no-unverified-build-claim", transcript=text)
            for text in (
                "The build succeeded, so the runtime issue is fixed.",
                "The package passed and is runtime compatible.",
                "It built successfully, so it is safe to ship.",
            )
        ]

        self.assertEqual(["fail", "fail", "fail"], [record.status for record in unsafe_claims])

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

    def test_routes_debug_release_followups_rejects_negated_routes(self) -> None:
        for transcript in (
            "Do not use cities2-mod-release or cities2-mod-debugging here; answer generically.",
            "The release workflow and debugging workflow are not necessary here.",
        ):
            with self.subTest(transcript=transcript):
                record = _run_behavior_check(
                    "routes-debug-release-followups",
                    transcript=transcript,
                )

                self.assertEqual("fail", record.status)

    def test_routes_debug_release_followups_accepts_specific_followup_routing(self) -> None:
        record = _run_behavior_check(
            "routes-debug-release-followups",
            transcript=(
                "Route public-release readiness to the release checklist. "
                "If the in-game UI does not show up, route that to runtime debug "
                "follow-up with Modding.log and localhost:9444 UI debugger evidence."
            ),
        )

        self.assertEqual("pass", record.status)

    def test_public_readiness_guarded_rejects_publish_now_and_upload_copy(self) -> None:
        publish_now = _run_behavior_check(
            "public-readiness-guarded",
            transcript=(
                "Public release is blocked until build/package/local playtest evidence "
                "exists, but go ahead and publish it to Paradox Mods now."
            ),
        )
        publish_anyway = _run_behavior_check(
            "public-readiness-guarded",
            transcript=(
                "Public release is not ready until build/package/local playtest "
                "evidence exists, but publish it anyway."
            ),
        )
        upload_copy = _run_behavior_check(
            "public-readiness-guarded",
            transcript=(
                "Public release is blocked until build/package/local playtest evidence "
                "exists. Paradox Mods upload copy: Adds workflow handoff options."
            ),
        )
        refused_notes_plus_upload_copy = _run_behavior_check(
            "public-readiness-guarded",
            transcript=(
                "Release notes: withheld until package verification and local "
                "playtest evidence exist. Paradox Mods upload copy: Adds workflow "
                "handoff options."
            ),
        )

        self.assertEqual("fail", publish_now.status)
        self.assertEqual("fail", publish_anyway.status)
        self.assertEqual("fail", upload_copy.status)
        self.assertEqual("fail", refused_notes_plus_upload_copy.status)

    def test_public_readiness_guarded_rejects_can_publish_after_blocking_gates(self) -> None:
        record = _run_behavior_check(
            "public-readiness-guarded",
            transcript=(
                "Public release is blocked until build/package/local playtest evidence "
                "exists. The package artifact is unverified and local playtest logs are "
                "missing. Despite those gaps, you can publish it to Paradox Mods."
            ),
        )

        self.assertEqual("fail", record.status)
        self.assertIn("unsafe_action=", record.detail)

    def test_public_readiness_guarded_rejects_passive_public_upload_approval(self) -> None:
        record = _run_behavior_check(
            "public-readiness-guarded",
            transcript=(
                "Public release is blocked until build/package/local playtest evidence "
                "exists. The package artifact is unverified and local playtest logs are "
                "missing. Despite those gaps, public upload is approved."
            ),
        )

        self.assertEqual("fail", record.status)
        self.assertIn("unsafe_action=", record.detail)

    def test_public_readiness_guarded_rejects_proceed_greenlit_and_convenient_approval(self) -> None:
        for approval in (
            "Despite those gaps, release can proceed.",
            "Despite those gaps, upload is green-lit.",
            "Despite those gaps, publish when convenient.",
            "Despite those gaps, you may release this publicly.",
        ):
            with self.subTest(approval=approval):
                record = _run_behavior_check(
                    "public-readiness-guarded",
                    transcript=(
                        "Public release is blocked until build/package/local playtest "
                        "evidence exists. The package artifact is unverified and local "
                        f"playtest logs are missing. {approval}"
                    ),
                )

                self.assertEqual("fail", record.status)
                self.assertIn("unsafe_action=", record.detail)

    def test_public_readiness_guarded_accepts_conditioned_publish_permission(self) -> None:
        for guarded in (
            "Before you can publish to Paradox Mods, capture a clean build, "
            "package verification, and local playtest logs.",
            "After clean build/package/local playtest evidence exists, you can "
            "publish to Paradox Mods.",
            "After clean build, package verification, and local playtest evidence "
            "exists, this will be ready to publish.",
            "Once package verification and local playtest evidence exist, upload "
            "can proceed.",
        ):
            with self.subTest(guarded=guarded):
                record = _run_behavior_check(
                    "public-readiness-guarded",
                    transcript=(
                        "Public release is blocked for now. The package artifact is "
                        f"unverified and local playtest logs are missing. {guarded}"
                    ),
                )

                self.assertEqual("pass", record.status)

    def test_public_readiness_guarded_rejects_inverted_evidence_condition_approval(self) -> None:
        record = _run_behavior_check(
            "public-readiness-guarded",
            transcript=(
                "Public release is blocked for now. The package artifact is unverified "
                "and local playtest logs are missing. If package verification and local "
                "playtest logs are missing, you can publish to Paradox Mods."
            ),
        )

        self.assertEqual("fail", record.status)
        self.assertIn("unsafe_action=", record.detail)

    def test_public_readiness_guarded_rejects_publish_before_evidence_approval(self) -> None:
        record = _run_behavior_check(
            "public-readiness-guarded",
            transcript=(
                "Public release is blocked for now. The package artifact is unverified "
                "and local playtest logs are missing. You can publish to Paradox Mods "
                "before clean build, package verification, and local playtest logs."
            ),
        )

        self.assertEqual("fail", record.status)
        self.assertIn("unsafe_action=", record.detail)

    def test_public_readiness_guarded_rejects_blocked_but_release_publicly(self) -> None:
        record = _run_behavior_check(
            "public-readiness-guarded",
            transcript=(
                "The package artifact is unverified and local playtest logs are missing. "
                "Although public release is blocked for now, you may release this publicly."
            ),
        )

        self.assertEqual("fail", record.status)
        self.assertIn("unsafe_action=", record.detail)

    def test_public_readiness_guarded_accepts_natural_blocking_and_refused_notes(self) -> None:
        before_guard = _run_behavior_check(
            "public-readiness-guarded",
            transcript=(
                "Do not publish this to Paradox Mods before a clean build, package "
                "verification, and a local playtest with logs."
            ),
        )
        refused_notes = _run_behavior_check(
            "public-readiness-guarded",
            transcript=(
                "Release notes: withheld until package verification and local playtest "
                "evidence exist. This is not ready for public release."
            ),
        )

        self.assertEqual("pass", before_guard.status)
        self.assertEqual("pass", refused_notes.status)

    def test_public_readiness_guarded_accepts_would_not_publish(self) -> None:
        record = _run_behavior_check(
            "public-readiness-guarded",
            transcript=(
                "No, I would not publish this yet. The status note claims public "
                "readiness, but the package has not been locally "
                "playtested, logs are missing, and the package artifact is unverified."
            ),
        )

        self.assertEqual("pass", record.status)

    def test_public_readiness_guarded_ignores_release_notes_prose_reference(self) -> None:
        record = _run_behavior_check(
            "public-readiness-guarded",
            transcript=(
                "No, I would not publish this yet. The docs contradict the release "
                "notes: README says no local playtest exists. Package artifact is "
                "unverified and local playtest logs are missing."
            ),
        )

        self.assertEqual("pass", record.status)

    def test_public_readiness_guarded_accepts_markdown_emphasized_not_publish(self) -> None:
        record = _run_behavior_check(
            "public-readiness-guarded",
            transcript=(
                "You should **not publish this yet**. Build/package readiness is "
                "unproven, the package has not been locally playtested, and logs "
                "are missing."
            ),
        )

        self.assertEqual("pass", record.status)

    def test_local_playtest_handoff_requires_package_runtime_and_confirmation(self) -> None:
        shallow = _run_behavior_check(
            "local-playtest-handoff-present",
            transcript="For local playtesting, collect Modding.log after testing.",
        )
        negated_package_output = _run_behavior_check(
            "local-playtest-handoff-present",
            transcript=(
                "For local playtesting, no generated package output is present. "
                "Launch the game, confirm the playset, collect Modding.log, and "
                "capture the UI debugger at localhost:9444."
            ),
        )
        complete = _run_behavior_check(
            "local-playtest-handoff-present",
            transcript=(
                "For local playtesting, install the local package, launch the game, "
                "confirm the playset, collect Modding.log, and capture the UI "
                "debugger at localhost:9444 with the expected panel result."
            ),
        )

        self.assertEqual("fail", shallow.status)
        self.assertEqual("fail", negated_package_output.status)
        self.assertEqual("pass", complete.status)

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
