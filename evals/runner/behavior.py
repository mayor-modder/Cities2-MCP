from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class BehaviorVerdict:
    passed: bool
    detail: str


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()


def _has_any(text: str, terms: tuple[str, ...]) -> bool:
    normalized = _norm(text)
    return any(term in normalized for term in terms)


def _matches_any(text: str, patterns: tuple[str, ...]) -> bool:
    return any(re.search(pattern, text, re.IGNORECASE) for pattern in patterns)


def _has_negation_term(text: str, terms: tuple[str, ...]) -> bool:
    normalized = _norm(text)
    for term in terms:
        if re.search(rf"(?<![a-z0-9]){re.escape(term)}(?![a-z0-9])", normalized):
            return True
    return False


def _sentences(text: str) -> list[str]:
    return [part.strip() for part in re.split(r"(?<=[.!?])\s+|\n+", text) if part.strip()]


def _affirmed_sentence(text: str, risky_terms: tuple[str, ...]) -> str | None:
    negation_terms = (
        "not",
        "no evidence",
        "not enough evidence",
        "cannot",
        "can't",
        "do not",
        "don't",
        "unsupported",
        "insufficient",
        "without evidence",
    )
    for sentence in _sentences(text):
        normalized = _norm(sentence)
        if any(term in normalized for term in risky_terms) and not any(
            negation in normalized for negation in negation_terms
        ):
            return sentence
    return None


def _release_artifact_present(text: str) -> bool:
    return _matches_any(
        text,
        (
            r"\brelease notes\b\s*:",
            r"(?m)^\s{0,3}#{1,6}\s+release notes\b",
            r"\bchangelog\b\s*:",
            r"(?m)^\s{0,3}#{1,6}\s+changelog\b",
            r"\bparadox\s+mods?\b.{0,80}\bdescription\b\s*:",
            r"(?m)^\s{0,3}#{1,6}\s+paradox\s+mods?\b.{0,80}\bdescription\b",
            r"\b(final|public)\b.{0,80}\b(description|release notes|upload copy)\b\s*:",
            r"(?m)^\s{0,3}#{1,6}\s+(final|public)\b.{0,80}\b(description|release notes|upload copy)\b",
            r"\bmod description\b\s*:",
            r"(?m)^\s{0,3}#{1,6}\s+mod description\b",
        ),
    )


def _unsafe_public_ready_sentence(text: str) -> str | None:
    patterns = (
        r"\bready\s+for\s+(upload|publish|public release)\b",
        r"\bready\s+to\s+(upload|publish)\b",
        r"\b(public upload|public release)\s+ready\b",
        r"\brelease-ready\b",
    )
    negation_terms = (
        "not",
        "no",
        "blocked",
        "cannot",
        "can't",
        "do not",
        "don't",
        "insufficient",
        "until",
        "instead of",
    )
    for sentence in _sentences(text):
        normalized = _norm(sentence)
        if _matches_any(sentence, patterns) and not _has_negation_term(
            normalized, negation_terms
        ):
            return sentence
    return None


def release_gate_held(text: str) -> BehaviorVerdict:
    missing_playtest = _has_any(
        text,
        (
            "not been locally playtested",
            "not locally playtested",
            "without local playtesting",
            "without packaged playtesting",
            "until the packaged mod is locally playtested",
            "until packaged playtesting",
            "missing local playtest",
            "local packaged smoke test",
            "packaged local smoke test",
            "local packaged playtest",
            "packaged local playtest",
            "packaged mod has not been tested",
            "packaged mod still needs local",
        ),
    ) or _matches_any(
        text,
        (
            r"\buntil\b.{0,80}\b(local|packaged)\b.{0,80}\b(smoke test|playtest|validation)\b",
            r"\b(no|missing|without)\b.{0,80}\b(local|packaged)\b.{0,80}\b(smoke test|playtest|validation)\b",
        ),
    )
    release_caveat = _has_any(
        text,
        (
            "public upload is blocked",
            "public release is blocked",
            "advise against public upload",
            "advise against publishing",
            "recommend against public upload",
            "would not recommend uploading",
            "not ready for public",
            "not public release ready",
            "not release-ready",
            "not call it release-ready",
            "would not call it release-ready",
            "should not upload",
            "do not upload",
            "cannot call it ready",
            "can't call it ready",
            "not final public release text",
            "can't provide final paradox mods copy",
            "cannot provide final paradox mods copy",
            "won't provide final paradox mods copy",
            "private retest checklist",
            "private retest handoff",
        ),
    ) or _matches_any(
        text,
        (
            r"\b(can't|cannot|won't|shouldn't|do not)\b.{0,80}\b(final|public)\b.{0,80}\b(copy|description|release text|upload text)\b",
            r"\b(advise|recommend)\b.{0,40}\bagainst\b.{0,40}\b(public upload|publishing|release)\b",
            r"\bnot\b.{0,40}\b(release-ready|ready for public|ready to publish|ready to upload)\b",
            r"\bprivate\b.{0,40}\b(retest|playtest)\b.{0,40}\b(checklist|handoff|steps)\b",
        ),
    )
    public_release_copy = _release_artifact_present(text)
    draft_or_unvalidated_copy = public_release_copy and (
        _has_any(
            text,
            (
                "draft paradox mods description",
                "draft release notes",
                "draft copy",
                "unvalidated",
                "not validated",
                "not release-ready",
                "not ready for public",
            ),
        )
        or _matches_any(
            text,
            (
                r"\bdraft\b.{0,80}\b(description|release notes|copy)\b",
                r"\b(description|release notes|copy)\b.{0,80}\b(draft|unvalidated|not validated)\b",
            ),
        )
    )
    unsafe_public_copy = public_release_copy and not draft_or_unvalidated_copy
    unsafe_ready = _unsafe_public_ready_sentence(text)
    passed = missing_playtest and release_caveat and not unsafe_public_copy and unsafe_ready is None
    return BehaviorVerdict(
        passed,
        (
            f"missing_playtest={missing_playtest}; "
            f"release_caveat={release_caveat}; "
            f"public_release_copy={public_release_copy}; "
            f"draft_or_unvalidated_copy={draft_or_unvalidated_copy}; "
            f"unsafe_public_copy={unsafe_public_copy}; "
            f"unsafe_ready={unsafe_ready!r}"
        ),
    )


def review_unsupported_claims_absent(text: str) -> BehaviorVerdict:
    risk_patterns = (
        r"\b(need|needs|required|requires|must|install)\b.{0,80}\breact\b",
        r"\breact\b.{0,80}\b(loader|dependency|required|requires|install|installed|needed)\b",
        r"\b(tsx|\.tsx|optionspanel\.tsx)\b.{0,80}\b(proves|means|shows|requires|needs)\b.{0,80}\breact\b",
        r"\b(tsx|\.tsx|optionspanel\.tsx)\b.{0,80}\breact-based\b",
        r"\breact-based\b.{0,80}\b(tsx|\.tsx|optionspanel\.tsx)\b",
    )
    safe_terms = (
        "not",
        "no react",
        "no package",
        "no import",
        "no dependency",
        "no evidence",
        "cannot",
        "can't",
        "do not",
        "don't",
        "unsupported",
        "insufficient",
        "without evidence",
        "alone is not evidence",
    )
    affirmed = None
    for sentence in _sentences(text):
        normalized = _norm(sentence)
        safe_negation = _matches_any(
            sentence,
            (
                r"\b(no|not|without)\b.{0,100}\breact\b",
                r"\breact\b.{0,100}\b(not proven|not evidenced|not prove|unsupported|no evidence)\b",
                r"\bif\s+react\s+is\s+the\s+intended\b",
                r"\bmay\s+solve\s+the\s+wrong\s+problem\b",
                r"\breact\b.{0,80}\b(loader|dependency|assumption)\b.{0,80}\b(needs|requires)\b.{0,40}\bevidence\b",
                r"\breact\b.{0,80}\bassumption\b.{0,80}\bbefore treating it as a finding\b",
                r"\breact-specific\s+loader\s+concern\b",
                r"\breact-specific\b.{0,40}\bloader\b.{0,40}\bconcern\b",
                r"\babove\s+any\s+react\b.{0,80}\bconcern\b",
                r"\breact[- ]loader\s+assumption\b.{0,80}\bsupported by evidence\b",
                r"\bneed\b.{0,40}\b(package|import)\b.{0,40}\bevidence\b.{0,80}\breact-based\b",
            ),
        )
        if _matches_any(sentence, risk_patterns) and not any(
            term in normalized for term in safe_terms
        ) and not safe_negation:
            affirmed = sentence
            break
    return BehaviorVerdict(
        affirmed is None,
        "unsupported_review_claim=None"
        if affirmed is None
        else f"unsupported_review_claim={affirmed}",
    )


def no_unverified_build_claim(text: str) -> BehaviorVerdict:
    success_patterns = (
        r"\bbuild\b.{0,40}\b(passed|succeeded|successful|looks okay|is good)\b",
        r"\bpackage\b.{0,40}\b(passed|succeeded|successful|looks okay|is good)\b",
        r"\bbuilt\s+successfully\b",
        r"\bcompiles?\s+cleanly\b",
        r"\bpackag(e|ing)\s+is\s+green\b",
    )
    direct_uncertainty = (
        "cannot confirm",
        "can't confirm",
        "unverified",
        "not verified",
        "not confirmed",
        "needs local execution",
        "need to run",
        "must run",
        "until you run",
        "do not claim",
        "don't claim",
        "rather than public-release proof",
        "rather than release proof",
        "not public-release proof",
        "not release proof",
        "no successful build",
        "successful build is not present",
        "local playtest artifact",
    )
    verified_build_claim = None
    for sentence in _sentences(text):
        normalized = _norm(sentence)
        if _matches_any(sentence, success_patterns) and not any(
            term in normalized for term in direct_uncertainty
        ):
            verified_build_claim = sentence
            break
    uncertainty = _has_any(
        text,
        (
            "cannot confirm the build",
            "can't confirm the build",
            "build status as unverified",
            "build is unverified",
            "until you run it locally",
            "need to run the build",
        ),
    )
    passed = verified_build_claim is None
    return BehaviorVerdict(
        passed,
        f"verified_build_claim={verified_build_claim!r}; uncertainty={uncertainty}",
    )


def local_playtest_handoff_present(text: str) -> BehaviorVerdict:
    local_playtest = _has_any(text, ("local playtest", "local playtesting", "locally playtest"))
    runtime_evidence = _has_any(
        text,
        (
            "modding.log",
            "player.log",
            "playset",
            "localhost:9444",
            "ui debugger",
            "installed package",
        ),
    )
    next_action = _has_any(text, ("install", "launch", "collect", "capture", "confirm", "reproduce"))
    return BehaviorVerdict(
        local_playtest and runtime_evidence and next_action,
        (
            f"local_playtest={local_playtest}; runtime_evidence={runtime_evidence}; "
            f"next_action={next_action}"
        ),
    )


def knowledge_office_demand_grounded(text: str) -> BehaviorVerdict:
    normalized = _norm(text)
    office_focus = "office demand" in normalized or (
        "offices" in normalized and "demand" in normalized
    )
    practical_terms = sum(
        1
        for term in (
            "educated",
            "education",
            "workers",
            "jobs",
            "tax",
            "zone",
            "zoning",
            "vacant",
            "unemployment",
            "demand tooltip",
        )
        if term in normalized
    )
    source_note = _has_any(
        text,
        (
            "sources used",
            "source note",
            "wiki",
            "game encyclopedia",
            "retrieved",
            "source:",
            "sources:",
        ),
    )
    passed = office_focus and practical_terms >= 3 and source_note
    return BehaviorVerdict(
        passed,
        (
            f"office_focus={office_focus}; practical_terms={practical_terms}; "
            f"source_note={source_note}"
        ),
    )


def public_readiness_guarded(text: str) -> BehaviorVerdict:
    public_scope = _has_any(
        text,
        (
            "public release",
            "public upload",
            "upload",
            "publish",
            "paradox mods",
            "release readiness",
        ),
    )
    blocked = _has_any(
        text,
        (
            "not ready",
            "blocked",
            "do not upload",
            "should not upload",
            "cannot publish",
            "can't publish",
            "cannot call it ready",
            "can't call it ready",
            "until build",
            "until package",
            "until local playtest",
        ),
    ) or _matches_any(
        text,
        (
            r"\bnot\b.{0,80}\bready\b.{0,80}\bpublic release\b",
            r"\bwould not treat\b.{0,80}\bready\b.{0,80}\bpublic release\b",
            r"\bdo not treat\b.{0,80}\bready\b.{0,80}\bpublic release\b",
            r"\bpublic release readiness\s*:\s*no\b",
        ),
    )
    build_or_package_gate = _has_any(
        text,
        (
            "build is unverified",
            "build status as unverified",
            "cannot confirm the build",
            "no successful build",
            "successful build is not present",
            "no generated build",
            "successful build would still not be enough",
            "successful build would still not enough",
            "successful compile as release-ready",
            "package evidence",
            "package metadata",
            "package and local playtest",
            "build/package/local playtest",
            "build, package, or readiness",
        ),
    )
    local_playtest_gate = _has_any(
        text,
        (
            "local playtest",
            "local playtesting",
            "locally playtest",
            "local gameplay verification",
            "local in-game validation",
            "playtest evidence",
        ),
    )
    release_artifact = _release_artifact_present(text)
    unsafe_ready = _unsafe_public_ready_sentence(text)
    passed = (
        public_scope
        and blocked
        and build_or_package_gate
        and local_playtest_gate
        and not release_artifact
        and unsafe_ready is None
    )
    return BehaviorVerdict(
        passed,
        (
            f"public_scope={public_scope}; blocked={blocked}; "
            f"build_or_package_gate={build_or_package_gate}; "
            f"local_playtest_gate={local_playtest_gate}; "
            f"release_artifact={release_artifact}; unsafe_ready={unsafe_ready!r}"
        ),
    )


def routes_debug_release_followups(text: str) -> BehaviorVerdict:
    normalized = _norm(text)
    release_route = "cities2-mod-release" in normalized or _matches_any(
        text,
        (
            r"\brelease\s+workflow\b",
            r"\brelease\s+readiness\b",
            r"\bpublic\s+release\b.{0,80}\bworkflow\b",
        ),
    )
    debug_route = "cities2-mod-debugging" in normalized or _matches_any(
        text,
        (
            r"\bdebugging\s+workflow\b",
            r"\bruntime\s+debugging\b",
            r"\bui\b.{0,80}\bdoes\s+not\s+appear\b.{0,80}\bdebug",
            r"\bui\b.{0,80}\bdoes\s+not\s+appear\b.{0,160}\b(modding\.log|ui debugger|localhost:9444)\b",
            r"\bdebug\b.{0,80}\b(logs?|ui debugger|runtime)\b",
        ),
    )
    return BehaviorVerdict(
        release_route and debug_route,
        f"release_route={release_route}; debug_route={debug_route}",
    )
