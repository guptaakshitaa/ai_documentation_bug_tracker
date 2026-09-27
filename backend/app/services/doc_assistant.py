"""
Documentation Assistant (module D in the design doc).

The *linting* (finding broken links, missing alt text, TODO markers, etc.)
is real, regex-based analysis — no LLM needed for that part. Only the final
"improved_content" rewrite depends on the LLM, and falls back to a mock
(lightly cleaned-up text) when no OPENAI_API_KEY is set.
"""
import re

from app.config import get_settings
from app.schemas.assistant import MarkdownIssue, DocumentationCheckResult

MD_LINK_PATTERN = re.compile(r"\[([^\]]*)\]\(([^)]*)\)")
MD_IMAGE_PATTERN = re.compile(r"!\[([^\]]*)\]\(([^)]*)\)")
TODO_PATTERN = re.compile(r"\b(TODO|FIXME|XXX)\b", re.IGNORECASE)
MAX_LINE_LENGTH = 120


def lint_markdown(content: str) -> list[MarkdownIssue]:
    """Real, deterministic checks — no LLM involved."""
    findings: list[MarkdownIssue] = []
    lines = content.splitlines()

    for i, line in enumerate(lines, start=1):
        # Broken / empty links: [text]() or [text](  )
        for match in MD_LINK_PATTERN.finditer(line):
            link_text, url = match.group(1), match.group(2).strip()
            if not url:
                findings.append(MarkdownIssue(type="broken_link", line_number=i,
                                               detail=f"Link '{link_text}' has an empty URL"))
            elif url.startswith("http") and " " in url:
                findings.append(MarkdownIssue(type="broken_link", line_number=i,
                                               detail=f"URL contains unencoded spaces: {url}"))

        # Images missing alt text
        for match in MD_IMAGE_PATTERN.finditer(line):
            alt_text = match.group(1).strip()
            if not alt_text:
                findings.append(MarkdownIssue(type="missing_alt_text", line_number=i,
                                               detail="Image is missing descriptive alt text"))

        # TODO / FIXME markers left in docs
        if TODO_PATTERN.search(line):
            findings.append(MarkdownIssue(type="todo_marker", line_number=i,
                                           detail="Unresolved TODO/FIXME marker left in documentation"))

        # Double spaces (common copy-paste artifact)
        if "  " in line.strip():
            findings.append(MarkdownIssue(type="double_space", line_number=i,
                                           detail="Double space found (formatting artifact)"))

        # Overly long lines hurt readability in rendered diffs
        if len(line) > MAX_LINE_LENGTH:
            findings.append(MarkdownIssue(type="long_line", line_number=i,
                                           detail=f"Line exceeds {MAX_LINE_LENGTH} characters ({len(line)})"))

    return findings


def _mock_rewrite(content: str, findings: list[MarkdownIssue]) -> str:
    """Deterministic placeholder cleanup: collapses double spaces and flags
    TODOs, without invoking any LLM. Clearly marked as a mock pass."""
    cleaned = re.sub(r" {2,}", " ", content)
    cleaned = TODO_PATTERN.sub(lambda m: f"{m.group(0)} [MOCK: needs resolution before merge]", cleaned)
    banner = "<!-- [MOCK] Auto-cleanup only (double spaces collapsed, TODOs flagged). Set OPENAI_API_KEY for full LLM rewrite. -->\n"
    return banner + cleaned


async def check_and_improve_markdown(content: str) -> DocumentationCheckResult:
    settings = get_settings()
    findings = lint_markdown(content)

    if not settings.llm_configured:
        improved = _mock_rewrite(content, findings)
        return DocumentationCheckResult(
            issue_count=len(findings),
            findings=findings,
            improved_content=improved,
            source="mock",
        )

    from app.services.ai_service import _call_llm  # reuse shared LLM caller

    findings_desc = "\n".join(f"- Line {f.line_number}: {f.type} — {f.detail}" for f in findings) or "None detected by linter."
    prompt = (
        "Rewrite the following Markdown documentation to fix grammar, improve readability, "
        "and address the listed issues, while strictly preserving its original meaning, "
        "structure, and any code blocks. Return ONLY the corrected Markdown, no commentary.\n\n"
        f"Known issues found by linter:\n{findings_desc}\n\n"
        f"Original content:\n{content}"
    )
    improved = await _call_llm(prompt)
    return DocumentationCheckResult(
        issue_count=len(findings),
        findings=findings,
        improved_content=improved.strip(),
        source="llm",
    )
