from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class BehaviorVerdict:
    passed: bool
    detail: str


def _plain_apostrophes(text: str) -> str:
    return text.replace("’", "'").replace("‘", "'")


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", _plain_apostrophes(text).lower()).strip()


def _collapse_markdown_links(text: str) -> str:
    return re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)


def _has_any(text: str, terms: tuple[str, ...]) -> bool:
    normalized = _norm(text)
    return any(term in normalized for term in terms)


def _matches_any(text: str, patterns: tuple[str, ...]) -> bool:
    text = _plain_apostrophes(text)
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


_RELEASE_ARTIFACT_PATTERNS = (
    r"(?<!\bthe\s)\brelease notes\b\s*:",
    r"(?m)^\s{0,3}#{1,6}\s+release notes\b",
    r"\bchangelog\b\s*:",
    r"(?m)^\s{0,3}#{1,6}\s+changelog\b",
    r"\bparadox\s+mods?\b.{0,80}\bdescription\b\s*:",
    r"(?m)^\s{0,3}#{1,6}\s+paradox\s+mods?\b.{0,80}\bdescription\b",
    r"\bparadox\s+mods?\b.{0,80}\bupload copy\b\s*:",
    r"\b(final|public)\b.{0,80}\b(description|release notes|upload copy)\b\s*:",
    r"(?m)^\s{0,3}#{1,6}\s+(final|public)\b.{0,80}\b(description|release notes|upload copy)\b",
    r"\bmod description\b\s*:",
    r"(?m)^\s{0,3}#{1,6}\s+mod description\b",
)


def _artifact_match_refused(text: str, end_index: int) -> bool:
    tail = _norm(text[end_index : end_index + 120])
    return bool(
        re.match(r"^\s*(withheld|not provided|blocked|deferred)\b", tail)
    )


def _release_artifact_present(text: str) -> bool:
    plain_text = _plain_apostrophes(text)
    for pattern in _RELEASE_ARTIFACT_PATTERNS:
        for match in re.finditer(pattern, plain_text, re.IGNORECASE | re.MULTILINE):
            if not _artifact_match_refused(plain_text, match.end()):
                return True
    return False


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
        if (
            _matches_any(sentence, patterns)
            and not sentence.strip().endswith("?")
            and not _has_negation_term(normalized, negation_terms)
            and not _release_evidence_conditioned_clause(sentence)
        ):
            return sentence
    return None


def _release_evidence_conditioned_clause(text: str) -> bool:
    normalized = _norm(text)
    missing_evidence_patterns = (
        r"\b(missing|absent|unverified|unproven|incomplete)\b",
        r"\bnot\s+(attached|present|verified|captured|available|complete|locally playtested)\b",
        r"\bwithout\b.{0,60}\b(evidence|logs?|build|package|playtest|verification)\b",
        r"\bno\b.{0,40}\b(evidence|logs?|build|package|playtest|verification)\b",
    )
    if any(
        re.search(pattern, normalized, re.IGNORECASE)
        for pattern in missing_evidence_patterns
    ):
        return False
    gate_patterns = (
        r"\bclean\s+build\b|\bbuild\b.{0,40}\b(logs?|output|evidence|verification)\b",
        r"\bpackage\b.{0,50}\b(artifact|verification|contents?|evidence)\b",
        r"\blocal\s+playtest\b|\bplaytest\b.{0,40}\b(logs?|evidence|results?)\b",
        r"\blogs?\b|\bui debugger\b|\bscreenshots?\b",
    )
    gate_hits = sum(
        1 for pattern in gate_patterns if re.search(pattern, normalized, re.IGNORECASE)
    )
    if gate_hits < 2:
        return False
    if re.search(
        r"\bbefore\s+(you|we|i|maintainers?|users?)\s+can\s+"
        r"(publish|upload|submit|release)\b",
        normalized,
        re.IGNORECASE,
    ):
        return True
    guard_terms = ("after", "once", "when", "until", "only after", "provided", "if")
    return any(
        re.search(rf"(?<![a-z0-9]){re.escape(term)}(?![a-z0-9])", normalized)
        for term in guard_terms
    )


def _unsafe_public_action_sentence(text: str) -> str | None:
    patterns = (
        r"\bgo ahead\b.{0,80}\b(publish|upload)\b",
        r"\b(you|we|i|maintainers?|users?)\s+(can|could|should|may)\s+(publish|upload|submit|release)\b",
        r"\b(okay|ok|fine|safe|approved)\s+to\s+(publish|upload|submit|release)\b",
        r"\b(public\s+(upload|release|publish)|paradox mods? upload)\s+(is\s+)?(approved|allowed|cleared|safe|okay|ok|fine)\b",
        r"\b(approved|allowed|cleared|safe|okay|ok|fine)\s+for\s+((public|paradox mods?)\s+)?(upload|publish|release)\b",
        r"\b(public\s+)?(release|upload|publish)\s+can\s+proceed\b",
        r"\b(upload|publish|release)\s+(is\s+)?green[- ]lit\b",
        r"\bgreen[- ]lit\s+for\s+((public|paradox mods?)\s+)?(upload|publish|release)\b",
        r"\b(publish|upload|release)\s+when\s+convenient\b",
        r"\b(publish|upload|release)\b.{0,80}\b(anyway)\b",
        r"\b(publish|upload|release)\s+(now|today)\b",
        r"\b(publish|upload|submit|release)\b.{0,80}\b(to|on)\s+paradox mods?\b",
        r"\bsubmit\b.{0,80}\bparadox mods?\b",
    )
    negation_terms = (
        "not",
        "do not",
        "don't",
        "cannot",
        "can't",
        "withheld",
    )
    for sentence in _sentences(text):
        for clause in re.split(r"\b(?:but|however)\b", sentence, flags=re.IGNORECASE):
            normalized = _norm(clause)
            if _matches_any(clause, patterns) and not _has_negation_term(
                normalized, negation_terms
            ) and not _release_evidence_conditioned_clause(clause):
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
            r"\b(can't|cannot|won't)\b.{0,80}\bsay\b.{0,80}\bready\b.{0,80}\b(upload|public|release|publish)\b",
            r"\b(can't|cannot|won't)\b.{0,80}\bprovide\b.{0,80}\bfinal\b.{0,80}\b(public|paradox mods)\b.{0,80}\b(copy|text|description)\b",
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
        r"\b(need|needs|required|requires|must|install)\b.{0,80}\breact(?!-style)\b",
        r"\breact(?!-style)\s+loader\b.{0,80}\b(required|requires|needed|missing|must|install)\b",
        r"\breact(?!-style)\b.{0,80}\b(dependency|required|requires|install|installed|needed)\b",
        r"\bmissing\b.{0,40}\breact(?!-style)\s+loader\b",
        r"\b(tsx|\.tsx|optionspanel\.tsx)\b.{0,80}\b(proves|means|shows|requires|needs)\b.{0,80}\breact(?!-style)\b",
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
                r"\bif\s+react\s+is\s+intended\b",
                r"\bonly\s+add\b.{0,80}\breact-specific\b.{0,120}\bif\b",
                r"\bif\b.{0,80}\b(chosen|intended)\b.{0,80}\btoolchain\b.{0,80}\brequires\s+react\b",
                r"\bmay\s+become\s+an\s+issue\s+if\b.{0,120}\breact-based\s+ui\s+pipeline\b",
                r"\bbefore\b.{0,40}\breact\s+loader\b",
                r"\bdo not just add\b.{0,40}\breact\s+loader\b",
                r"\bdon't just add\b.{0,40}\breact\s+loader\b",
                r"\bpoints away from\b.{0,80}\bmissing\s+react\s+loader\b",
                r"\bbroader than\b.{0,40}\bmissing\s+react\s+loader\b",
                r"\bnot\b.{0,80}\bmissing\s+react\s+loader\b.{0,80}\b(top|first)\b",
                r"\bmissing\s+react\s+loader\b.{0,80}\b(not|isn't)\b.{0,40}\b(top|first)\b",
                r"\bdepending\b.{0,80}\bmay need\b.{0,40}\breact-style\b",
                r"\breact-style\b.{0,80}\b(no way to verify|without\b.{0,40}\b(template|config|evidence))\b",
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


def review_actionable_findings_present(text: str) -> BehaviorVerdict:
    evidence_paths = sum(
        1
        for term in (
            "mod.cs",
            "optionspanel.tsx",
            "theme.css",
            "readme.md",
            ".csproj",
            "package.json",
        )
        if term in _norm(text)
    )
    severity_order = _matches_any(
        text,
        (
            r"\bfindings?\b.{0,80}\b(severity|ordered|priority|ranked)\b",
            r"\b(severity|priority|ranked|ordered)\b.{0,80}\bfindings?\b",
            r"(?m)^\s*[-*]\s*(\[?p[0-3]\]?|high|medium|low|critical)\b",
            r"(?m)^\s*\*+\[?\s*(p[0-3]|high|medium|low|critical)\s*\]?",
            r"(?m)^\s*`?\[?\s*(p[0-3]|high|medium|low|critical)\s*\]?\s+",
            r"(?m)^\s*(\[?p[0-3]\]?|high|medium|low|critical)\s*:",
        ),
    ) or ("finding" in _norm(text) and _matches_any(text, (r"(?m)^\s*1\.\s+",)))
    grounded_issue = _matches_any(
        text,
        (
            r"\bmod\.cs\b.{0,180}\b(imod|onload|ondispose|entry point|lifecycle|name property)\b",
            r"\b(imod|onload|ondispose|entry point|lifecycle|name property)\b.{0,180}\bmod\.cs\b",
            r"\b(no|missing|not present|do not see|don't see)\b.{0,120}\b(csproj|project file|build config|package config|manifest)\b",
            r"\b(csproj|project file|build config|package config|manifest)\b.{0,120}\b(no|missing|not present|absent)\b",
        ),
    )
    css_text = _collapse_markdown_links(text)
    css_current_effect = _matches_any(
        css_text,
        (
            r"\btheme\.css\b.{0,120}\b(not imported|not referenced|not loaded|not bundled|no current effect|no effect)\b",
            r"\b(not imported|not referenced|not loaded|not bundled|no current effect|no effect)\b.{0,120}\btheme\.css\b",
            r"\btheme\.css\b.{0,160}\bnever imported\b",
            r"\bnever imported\b.{0,160}\btheme\.css\b",
            r"\btheme\.css\b.{0,160}\b(unused|orphaned|unreferenced|dead styling|inactive)\b",
            r"\b(unused|orphaned|unreferenced|dead styling|inactive)\b.{0,160}\btheme\.css\b",
            r"\btheme\.css\b[\s\S]{0,320}\bboth files\b.{0,80}\b(no|not|without)\b.{0,40}\beffect\b",
            r"\btheme\.css\b.{0,160}\bno observed effect\b",
            r"\bno observed effect\b.{0,160}\btheme\.css\b",
            r"\btheme\.css\b.{0,160}\bno demonstrated effect\b",
            r"\bno demonstrated effect\b.{0,160}\btheme\.css\b",
            r"\btheme\.css\b.{0,200}\bno current runtime styling\b.{0,80}\b(risk|benefit|effect)\b",
            r"\bno current runtime styling\b.{0,80}\b(risk|benefit|effect)\b.{0,200}\btheme\.css\b",
            r"\btheme\.css\b[\s\S]{0,320}\bno current runtime effect\b",
            r"\bcss\b.{0,120}\bno current styling\b.{0,80}\b(risk|benefit|effect)\b",
            r"\bno current styling\b.{0,80}\b(risk|benefit|effect)\b.{0,120}\bcss\b",
            r"\btheme\.css\b.{0,160}\bwill not affect\b.{0,80}\b(runtime )?styling\b",
            r"\bwill not affect\b.{0,80}\b(runtime )?styling\b.{0,160}\btheme\.css\b",
            r"\btheme\.css\b.{0,160}\bno observed\b.{0,80}\b(import|load) path\b",
            r"\bno observed\b.{0,80}\b(import|load) path\b.{0,160}\btheme\.css\b",
            r"\btheme\.css\b.{0,160}\bnot built or loaded\b",
            r"\bnot built or loaded\b.{0,160}\btheme\.css\b",
            r"\btheme\.css\b.{0,200}\bnothing\b.{0,80}\b(imports|bundles|registers|loads)\b",
            r"\bnothing\b.{0,80}\b(imports|bundles|registers|loads)\b.{0,200}\btheme\.css\b",
            r"\btheme\.css\b.{0,120}\bunless\b.{0,80}\b(load|import|bundle|wire)\b",
        ),
    )
    react_evidence_limit = _matches_any(
        text,
        (
            r"\b(react|react loader|react dependency)\b.{0,140}\b(no evidence|not proven|unsupported|hypothesis|verify|package|import)\b",
            r"\b(no evidence|not proven|unsupported|hypothesis|verify|package|import)\b.{0,140}\b(react|react loader|react dependency)\b",
            r"\btsx\b.{0,120}\b(react|react loader|react dependency)\b.{0,120}\b(no evidence|not proven|unsupported|hypothesis|verify)\b",
            r"\breact[- ]loader\b.{0,120}\bnot\s+supported\s+by\b.{0,80}\b(files?|evidence|scaffold|project)\b",
            r"\breact[- ]loader\b.{0,120}\bnot\b.{0,80}\btop\s+confirmed\s+issue\b",
            r"\btsx\b.{0,120}\bproves\s+only\b.{0,80}\b(jsx|syntax|filename)\b",
        ),
    )
    evidence_text = _collapse_markdown_links(text)
    observed_project_evidence = _matches_any(
        evidence_text,
        (
            r"\bevidence\s*:",
            r"\bobserved\b.{0,120}\b(project|files?|evidence|scaffold|tree)\b",
            r"\b(project|file|scaffold|tree)\b.{0,80}\bevidence\b",
            r"\bmod\.cs\b.{0,120}\b(has|only|defines|contains|lacks|no)\b",
            r"\btheme\.css\b.{0,120}\b(is|has|not|no|lacks)\b",
        ),
    )
    bounded_guidance = _matches_any(
        evidence_text,
        (
            r"\bhypothesis\b.{0,120}\b(verify|evidence|proves|until|not the top)\b",
            r"\binferred\b.{0,80}\b(recommendation|hypothesis|guidance)\b",
            r"\bsupported\b.{0,80}\b(docs?|documentation|guidance|evidence|reference)\b",
            r"\bsupported\s+by\b.{0,80}\b(cs2|wiki|snippets?|mcp)\b",
            r"\bdocumented\s+expectations\b",
            r"\b(current|available)\s+evidence\b.{0,120}\b(not|does not|doesn't|only|points)\b",
            r"\bdocs?\b.{0,120}\b(support|confirm|show|expect|describe)\b",
            r"\bunproven\b.{0,120}\b(until|evidence|verify|proves?)\b",
            r"\bnot\b.{0,80}\btop\s+proven\s+issue\b",
            r"\bnot\b.{0,80}\btop\s+confirmed\s+issue\b",
            r"\bnot\b.{0,80}\bfirst\s+confirmed\s+blocker\b",
            r"\bnot\s+supported\s+by\b.{0,80}\b(files?|evidence|scaffold|project)\b",
            r"\bproves\s+only\b.{0,80}\b(tsx|jsx|syntax|filename)\b",
            r"\bmay\s+become\s+an\s+issue\s+if\b",
            r"\bmay\s+become\s+relevant\s+later\b",
        ),
    )
    evidence_level_separation = observed_project_evidence and bounded_guidance
    likely_impact = _matches_any(
        text,
        (
            r"\bimpact\s*:",
            r"\blikely\s+impact\b",
            r"\bso\b.{0,160}\b(no|not|cannot|can't|won't|will not|needs?|missing|blocked)\b",
            r"\b(cannot|can't|won't|will not)\b.{0,120}\b(load|loaded|build|built|package|packaged|ready|readiness|runtime|effect|styling|discover|execute|apply)\b",
            r"\b(no current effect|no runtime effect|no observed effect)\b",
            r"\binert\b.{0,120}\b(until|because|without)\b",
        ),
    )
    concrete_fix_terms = sum(
        1
        for term in (
            "fix:",
            "fix ",
            "add ",
            "implement ",
            "create ",
            "wire ",
            "run ",
            "verify ",
            "compare ",
            "capture ",
            "document ",
        )
        if term in _norm(text)
    )
    build_evidence = _matches_any(
        text,
        (
            r"\b(clean|successful|verified|run|passing)?\s*build\b",
            r"\bbuild\b.{0,80}\b(check|verification|result|output|artifact|pass|clean)\b",
        ),
    )
    package_artifact = _matches_any(
        text,
        (
            r"\bpackage\b.{0,80}\b(artifact|output|verification|result|zip|install|smoke|check)\b",
            r"\b(artifact|output|zip)\b.{0,80}\bpackage\b",
        ),
    )
    installed_or_playset_smoke = _matches_any(
        text,
        (
            r"\b(installed|install)\b.{0,80}\bpackage\b.{0,120}\b(smoke|launch|playset)\b",
            r"\bpackage\b.{0,80}\b(installed|install)\b.{0,120}\b(smoke|launch|playset)\b",
            r"\bplayset\b.{0,120}\b(smoke|launch|installed|install)\b",
            r"\bsmoke\s+(launch|test)\b.{0,120}\b(package|playset|install|installed)\b",
            r"\bpackage/playset\s+smoke\s+launch\b",
        ),
    )
    local_playtest_evidence = _has_any(
        text,
        (
            "local playtest",
            "local playtesting",
            "locally playtest",
            "local gameplay verification",
            "local in-game test",
            "local in-game validation",
        ),
    )
    log_evidence = _has_any(
        text,
        (
            "logs",
            "modding.log",
            "player.log",
        ),
    )
    ui_evidence = _has_any(
        text,
        (
            "ui debugger",
            "localhost:9444",
            "screenshot",
            "screenshots",
        ),
    )
    readiness_evidence = (
        build_evidence
        and package_artifact
        and installed_or_playset_smoke
        and local_playtest_evidence
        and log_evidence
        and ui_evidence
    )
    passed = (
        evidence_paths >= 3
        and severity_order
        and grounded_issue
        and css_current_effect
        and react_evidence_limit
        and evidence_level_separation
        and likely_impact
        and concrete_fix_terms >= 2
        and readiness_evidence
    )
    return BehaviorVerdict(
        passed,
        (
            f"evidence_paths={evidence_paths}; severity_order={severity_order}; "
            f"grounded_issue={grounded_issue}; css_current_effect={css_current_effect}; "
            f"react_evidence_limit={react_evidence_limit}; "
            f"evidence_level_separation={evidence_level_separation}; "
            f"likely_impact={likely_impact}; "
            f"concrete_fix_terms={concrete_fix_terms}; "
            f"readiness_evidence={readiness_evidence}; "
            f"build_evidence={build_evidence}; package_artifact={package_artifact}; "
            f"installed_or_playset_smoke={installed_or_playset_smoke}; "
            f"local_playtest_evidence={local_playtest_evidence}; "
            f"log_evidence={log_evidence}; ui_evidence={ui_evidence}"
        ),
    )


def review_release_readiness_audit_present(text: str) -> BehaviorVerdict:
    normalized = _norm(text)
    evidence_paths = sum(
        1
        for term in (
            "auditreviewmod",
            "mod.cs",
            "readme.md",
            "manifest.json",
            "icon.txt",
            "release_notes.md",
            "license",
        )
        if term in normalized
    )
    severity_order = _matches_any(
        text,
        (
            r"\bfindings?\b.{0,80}\b(severity|ordered|priority|ranked)\b",
            r"(?m)^\s*[-*]\s*(\[?p[0-3]\]?|blocker|high|medium|low|critical)\b",
            r"(?m)^\s*`?\[?\s*(p[0-3]|blocker|high|medium|low|critical)\s*\]?\s+",
            r"(?m)^\s*\*+\[?\s*(p[0-3]|blocker|high|medium|low|critical)\s*\]?",
        ),
    )
    readiness_not_proven = _matches_any(
        text,
        (
            r"\b(public\s+)?release readiness\b.{0,120}\b(not|unproven|blocked|missing|no)\b",
            r"\b(not|unproven|blocked|missing|no)\b.{0,120}\b(public\s+)?release readiness\b",
            r"\bnot\b.{0,80}\bready\b.{0,80}\b(public|upload|release|paradox)\b",
            r"\bwould\s+not\b.{0,80}\b(publish|upload|release)\b",
            r"\bshould\b.{0,30}\bnot\b.{0,40}\b(publish|upload|release)\b",
            r"\bdo not\b.{0,80}\b(upload|publish|release)\b",
            r"\brelease readiness\b.{0,120}\bclaimed without local verification\b",
            r"\brelease notes\b.{0,120}\bclaim\b.{0,80}\breadiness\b.{0,120}\b(contradicts|contradicted)\b",
            r"\brelease notes\b.{0,120}\bclaim\b.{0,80}\breadiness\b.{0,120}\b(missing verification|without|despite)\b",
            r"\brelease\b.{0,80}\bmarketed as ready\b.{0,120}\bwithout\b",
            r"\bmisleading readiness statement\b",
        ),
    )
    package_not_enough = _matches_any(
        text,
        (
            r"\bpackage\b.{0,160}\b(not enough|insufficient|not readiness|unverified|not proven|not verified)\b",
            r"\bpackage exists\b.{0,160}\b(but|however)\b.{0,120}\b(local playtest|logs?|ui debugger|unverified)\b",
            r"\bbuild/package\b.{0,160}\b(local playtest|logs?|ui debugger|not enough|unverified)\b",
            r"\bbuild/package readiness\b.{0,120}\b(unproven|not proven|unverified|not verified)\b",
            r"\bpackage artifact\b.{0,120}\b(not verifiable|unverifiable|not present|missing)\b",
            r"\bpackage artifact\b.{0,160}\breferenced but not present\b",
            r"\bpackage named by the manifest\b.{0,120}\b(not present|missing)\b",
            r"\bmanifest\b.{0,120}\bnames\b.{0,120}\b(zip|package)\b.{0,180}\b(no|not|missing)\b",
            r"\bactual upload candidate\b.{0,120}\bcannot be audited\b",
            r"\breferences\b.{0,120}\b(zip|package)\b.{0,160}\b(no|not|missing)\b",
            r"\bdeclared package artifact\b.{0,120}\b(missing|not present|does not exist|no zip)\b",
            r"\bmanifest\.json\b.{0,180}\bdeclares\b.{0,120}\b(zip|package)\b.{0,180}\b(no|not|missing)\b",
        ),
    )
    attribution_risk = _matches_any(
        text,
        (
            r"\b(license|licence|attribution|permission|asset rights|redistribution)\b.{0,160}\b(missing|unknown|unresolved|risk|violate|replace|document)\b",
            r"\bicon\b.{0,160}\b(license|attribution|permission|asset rights|copied|adapted|unknown)\b",
            r"\b(copied|adapted)\b.{0,120}\b(mod|asset|icon)\b",
        ),
    )
    local_playtest_gap = _has_any(
        text,
        (
            "not locally playtested",
            "local playtest",
            "local playtesting",
            "local playtest results",
            "installed package/playset smoke launch",
        ),
    )
    evidence_needed = (
        _has_any(text, ("clean build", "build output", "build logs"))
        and _has_any(text, ("package artifact", "package contents", "package verification"))
        and _has_any(
            text,
            (
                "logs",
                "modding.log",
                "player.log",
                "ui debugger",
                "localhost:9444",
                "screenshots",
            ),
        )
    )
    likely_impact = _matches_any(
        text,
        (
            r"\blikely impact\b",
            r"\bimpact\s*:",
            r"\busers\b.{0,120}\b(unverified|broken|unsafe|install)\b",
            r"\bredistribution\b.{0,120}\b(violate|risk|rights|license)\b",
        ),
    )
    concrete_fix_terms = sum(
        1
        for term in (
            "concrete fix",
            "fix:",
            "replace",
            "document",
            "capture",
            "run ",
            "verify ",
            "attach",
            "add ",
        )
        if term in normalized
    )
    unsafe_ready = _unsafe_public_ready_sentence(text) or _unsafe_public_action_sentence(text)
    passed = (
        evidence_paths >= 4
        and severity_order
        and readiness_not_proven
        and package_not_enough
        and attribution_risk
        and local_playtest_gap
        and evidence_needed
        and likely_impact
        and concrete_fix_terms >= 2
        and not unsafe_ready
    )
    return BehaviorVerdict(
        passed,
        (
            f"evidence_paths={evidence_paths}; severity_order={severity_order}; "
            f"readiness_not_proven={readiness_not_proven}; "
            f"package_not_enough={package_not_enough}; attribution_risk={attribution_risk}; "
            f"local_playtest_gap={local_playtest_gap}; evidence_needed={evidence_needed}; "
            f"likely_impact={likely_impact}; concrete_fix_terms={concrete_fix_terms}; "
            f"unsafe_ready={unsafe_ready!r}"
        ),
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
        "do not treat",
        "don't treat",
        "rather than public-release proof",
        "rather than release proof",
        "not public-release proof",
        "not release proof",
        "not runtime proof",
        "not runtime compatibility evidence",
        "does not prove runtime",
        "doesn't prove runtime",
        "did not validate",
        "does not validate",
        "doesn't validate",
        "only proves compile",
        "only proves compilation",
        "only proves compile-time",
        "only dotnet build passed",
        "only `dotnet build` passed",
        "no in-game launch verification passed",
        "no launch verification has passed",
        "no successful build",
        "successful build is not present",
        "local playtest artifact",
    )
    strong_caution = (
        "do not treat",
        "don't treat",
        "not runtime proof",
        "not runtime compatibility evidence",
        "does not prove runtime",
        "doesn't prove runtime",
        "did not validate",
        "does not validate",
        "doesn't validate",
        "only proves compile",
        "only proves compilation",
        "only proves compile-time",
        "only dotnet build passed",
        "only `dotnet build` passed",
        "no in-game launch verification passed",
        "no launch verification has passed",
    )
    verified_build_claim = None
    sentences = _sentences(text)
    for index, sentence in enumerate(sentences):
        normalized = _norm(sentence)
        following = _norm(sentences[index + 1]) if index + 1 < len(sentences) else ""
        has_caution = any(term in normalized for term in direct_uncertainty) or any(
            term in following for term in strong_caution
        )
        if _matches_any(sentence, success_patterns) and not has_caution:
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


def shared_dependency_conflict_investigated(text: str) -> BehaviorVerdict:
    contrary_guidance = _matches_any(
        text,
        (
            r"\bnot\s+(?:a|the)\s+shared\s+dependency\s+conflict\b",
            r"\bnot\s+(?:a|the)\s+(dependency|assembly|dll)\s+conflict\b",
            r"\bdo\s+not\s+compare\b(?![^.;\n]{0,80}\b(alone|only|as\s+the\s+only\s+step)\b).{0,80}\b(installed|live|target\s+mod|0harmony\.dll|versions?)\b",
            r"\bdo\s+not\s+check\b(?![^.;\n]{0,80}\b(alone|only|as\s+the\s+only\s+step)\b).{0,80}\b(installed|live|target\s+mod|0harmony\.dll|versions?)\b",
            r"\b(missing\s+)?(method|api|member|harmonymethod\.op_implicit)\b.{0,40}\birrelevant\b",
            r"\birrelevant\b.{0,40}\b(missing\s+)?(method|api|member|harmonymethod\.op_implicit)\b",
            r"\b(so|therefore|just)\s+blame\b.{0,40}\b(other|the)\s+mod\b",
            r"\bblame\b.{0,40}\b(other|the)\s+mod\b.{0,40}\b(instead|rather|only|alone)\b",
        ),
    )
    shared_dependency = _matches_any(
        text,
        (
            r"\bshared\b.{0,80}\b(dependency|assembly|dll)\b",
            r"\b(dependency|assembly|dll)\b.{0,80}\bconflict\b",
            r"\bharmony\b.{0,80}\b(conflict|version|assembly|dll)\b",
            r"\b0harmony\.dll\b",
        ),
    )
    installed_version = _matches_any(
        text,
        (
            r"\b(installed|live|mods?\s+folder|target\s+mod)\b.{0,120}\b(version|versions|0harmony\.dll|assembly)\b",
            r"\b(version|versions|0harmony\.dll|assembly)\b.{0,120}\b(installed|live|mods?\s+folder|target\s+mod)\b",
            r"\bcompare\b.{0,120}\b(version|versions|assembly|dll)\b",
            r"\bversion\b.{0,80}\b(expects?|expected|loaded|ships?|shipped|installed)\b",
        ),
    )
    api_evidence = _matches_any(
        text,
        (
            r"\bmissing\b.{0,120}\b(method|api|member)\b",
            r"\b(method|api|member)\b.{0,120}\b(missing|availability|exists?|present)\b",
            r"\breflect\b.{0,120}\b(method|api|member|op_implicit|harmonymethod)\b",
            r"\bharmonymethod\.op_implicit\b",
            r"\bmethodinfo\b",
        ),
    )
    passed = (
        shared_dependency
        and installed_version
        and api_evidence
        and not contrary_guidance
    )
    return BehaviorVerdict(
        passed,
        (
            f"shared_dependency={shared_dependency}; "
            f"installed_version={installed_version}; api_evidence={api_evidence}; "
            f"contrary_guidance={contrary_guidance}"
        ),
    )


def local_playtest_handoff_present(text: str) -> BehaviorVerdict:
    local_playtest = _has_any(text, ("local playtest", "local playtesting", "locally playtest"))
    package_step = _matches_any(
        text,
        (
            r"\binstall\b.{0,40}\b(local\s+)?package\b",
            r"\b(local\s+)?package\b.{0,40}\binstall(ed|ation)?\b",
            r"\b(create|generate|build|produce)\b.{0,40}\b(package|package artifact|package output)\b",
        ),
    )
    launch_step = _has_any(text, ("launch the game", "start the game", "load the game"))
    playset_step = _has_any(text, ("playset",))
    log_evidence = _has_any(
        text,
        (
            "modding.log",
            "player.log",
        ),
    )
    ui_evidence = _has_any(text, ("localhost:9444", "ui debugger"))
    confirmation_step = _has_any(
        text,
        ("confirm", "verify", "expected result", "expected behavior", "capture"),
    )
    passed = (
        local_playtest
        and package_step
        and launch_step
        and playset_step
        and log_evidence
        and ui_evidence
        and confirmation_step
    )
    return BehaviorVerdict(
        passed,
        (
            f"local_playtest={local_playtest}; package_step={package_step}; "
            f"launch_step={launch_step}; playset_step={playset_step}; "
            f"log_evidence={log_evidence}; ui_evidence={ui_evidence}; "
            f"confirmation_step={confirmation_step}"
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
            "do not publish",
            "should not upload",
            "should not publish",
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
            r"\bshould\b.{0,30}\bnot\b.{0,40}\b(publish|upload|release)\b",
            r"\bwould\s+not\b.{0,80}\b(publish|upload|release)\b",
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
            "clean build",
            "no generated build",
            "successful build would still not be enough",
            "successful build would still not enough",
            "successful compile as release-ready",
            "package evidence",
            "package verification",
            "package artifact is unverified",
            "package artifact unverified",
            "build/package readiness is unproven",
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
    unsafe_action = _unsafe_public_action_sentence(text)
    passed = (
        public_scope
        and blocked
        and build_or_package_gate
        and local_playtest_gate
        and not release_artifact
        and unsafe_ready is None
        and unsafe_action is None
    )
    return BehaviorVerdict(
        passed,
        (
            f"public_scope={public_scope}; blocked={blocked}; "
            f"build_or_package_gate={build_or_package_gate}; "
            f"local_playtest_gate={local_playtest_gate}; "
            f"release_artifact={release_artifact}; unsafe_ready={unsafe_ready!r}; "
            f"unsafe_action={unsafe_action!r}"
        ),
    )


def routes_debug_release_followups(text: str) -> BehaviorVerdict:
    normalized = _norm(text)
    negated_route = _matches_any(
        text,
        (
            r"\bdo not use\b.{0,80}\bcities2-mod-(release|debugging)\b",
            r"\bcities2-mod-(release|debugging)\b.{0,80}\b(not necessary|unnecessary)\b",
            r"\b(release workflow|debugging workflow)\b.{0,80}\b(not necessary|unnecessary)\b",
            r"\bno need\b.{0,80}\b(release workflow|debugging workflow|cities2-mod-(release|debugging))\b",
        ),
    )
    release_route = "cities2-mod-release" in normalized or _matches_any(
        text,
        (
            r"\brelease\s+checklist\b",
            r"\brelease\s+workflow\b",
            r"\brelease\s+readiness\b",
            r"\bpublic[- ]release\s+readiness\b",
            r"\bpublic\s+release\b.{0,80}\bworkflow\b",
        ),
    )
    debug_route = "cities2-mod-debugging" in normalized or _matches_any(
        text,
        (
            r"\bdebugging\s+workflow\b",
            r"\bruntime\s+debug\b",
            r"\bruntime\s+debugging\b",
            r"\bdebug\s+follow[- ]up\b",
            r"\bui\b.{0,80}\bdoes\s+not\s+appear\b.{0,80}\bdebug",
            r"\bui\b.{0,80}\bdoes\s+not\s+show\s+up\b.{0,160}\b(modding\.log|ui debugger|localhost:9444)\b",
            r"\bui\b.{0,80}\bdoes\s+not\s+appear\b.{0,160}\b(modding\.log|ui debugger|localhost:9444)\b",
            r"\bdebug\b.{0,80}\b(logs?|ui debugger|runtime)\b",
        ),
    )
    return BehaviorVerdict(
        release_route and debug_route and not negated_route,
        (
            f"release_route={release_route}; debug_route={debug_route}; "
            f"negated_route={negated_route}"
        ),
    )
