"""
Bug Resolution Assistant (module E in the design doc).

Stack-trace / error extraction from issue text is real regex-based parsing.
Root-cause reasoning and fix suggestions use the LLM when configured,
otherwise fall back to a generic mock so the endpoint is fully testable
before an OPENAI_API_KEY is available.
"""
import re

from app.config import get_settings
from app.schemas.assistant import BugResolutionResult

# Matches common stack-trace-ish lines: "File ... line N", "at Foo.bar (...)",
# Python tracebacks, and generic "Error: ..." / "Exception: ..." lines.
STACK_LINE_PATTERNS = [
    re.compile(r"^\s*File \".*\", line \d+.*$", re.MULTILINE),
    re.compile(r"^\s*at [\w.$<>]+\s*\(.*\)\s*$", re.MULTILINE),          # JS-style "at Foo (file:line)"
    re.compile(r"^\s*\w*Error:.*$", re.MULTILINE),
    re.compile(r"^\s*\w*Exception:.*$", re.MULTILINE),
    re.compile(r"^\s*Traceback \(most recent call last\):\s*$", re.MULTILINE),
]


def extract_stack_frames(body: str) -> list[str]:
    """Real, deterministic extraction — no LLM involved."""
    frames: list[str] = []
    for pattern in STACK_LINE_PATTERNS:
        frames.extend(m.strip() for m in pattern.findall(body))
    # de-duplicate while preserving order
    seen = set()
    unique_frames = []
    for f in frames:
        if f not in seen:
            seen.add(f)
            unique_frames.append(f)
    return unique_frames[:15]  # cap to keep responses readable


def _mock_bug_analysis(title: str, body: str, frames: list[str]) -> tuple[list[str], list[str], list[str]]:
    root_causes = [
        "[MOCK] Null/undefined value reaching a code path that assumes it is set" if not frames else
        f"[MOCK] Likely originates near: {frames[0]}",
        "[MOCK] Possible edge case not covered by existing validation",
    ]
    fix_steps = [
        "[MOCK] Reproduce using the steps/environment described in the issue",
        "[MOCK] Add a guard clause or input validation at the failure point",
        "[MOCK] Re-run the original repro steps to confirm the fix",
    ]
    test_cases = [
        f"[MOCK] Regression test: reproduce '{title[:60]}' and assert no exception is raised",
        "[MOCK] Edge case test: empty/null input to the affected function",
    ]
    return root_causes, fix_steps, test_cases


async def resolve_bug(issue_number: int, title: str, body: str | None) -> BugResolutionResult:
    settings = get_settings()
    body = body or ""
    frames = extract_stack_frames(body)

    if not settings.llm_configured:
        root_causes, fix_steps, test_cases = _mock_bug_analysis(title, body, frames)
        return BugResolutionResult(
            issue_number=issue_number,
            extracted_stack_frames=frames,
            likely_root_causes=root_causes,
            recommended_fix_steps=fix_steps,
            suggested_test_cases=test_cases,
            source="mock",
        )

    from app.services.ai_service import _call_llm, _safe_json

    frames_desc = "\n".join(frames) or "No explicit stack trace found in the issue body."
    prompt = (
        "A contributor is looking at this GitHub bug report and needs help. "
        "Respond ONLY as JSON with keys: likely_root_causes (array of strings), "
        "recommended_fix_steps (array of strings), suggested_test_cases (array of strings).\n\n"
        f"Title: {title}\nBody: {body[:2000]}\nExtracted stack trace lines:\n{frames_desc}"
    )
    try:
        raw = await _call_llm(prompt)
        parsed = _safe_json(raw, fallback={
            "likely_root_causes": [], "recommended_fix_steps": [], "suggested_test_cases": [],
        })
        return BugResolutionResult(
            issue_number=issue_number,
            extracted_stack_frames=frames,
            likely_root_causes=parsed.get("likely_root_causes", []),
            recommended_fix_steps=parsed.get("recommended_fix_steps", []),
            suggested_test_cases=parsed.get("suggested_test_cases", []),
            source="llm",
        )
    except Exception:
        root_causes, fix_steps, test_cases = _mock_bug_analysis(title, body, frames)
        return BugResolutionResult(
            issue_number=issue_number,
            extracted_stack_frames=frames,
            likely_root_causes=root_causes,
            recommended_fix_steps=fix_steps,
            suggested_test_cases=test_cases,
            source="mock",
        )
