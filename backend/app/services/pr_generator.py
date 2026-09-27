"""
Contribution Generator (module F). Takes an issue plus whatever the
Documentation or Bug Resolution assistants produced, and drafts
contribution-ready artifacts: PR title, PR description, commit message,
and a testing checklist.
"""
from app.config import get_settings
from app.schemas.assistant import ContributionArtifacts


def _mock_contribution(issue_number: int, title: str) -> ContributionArtifacts:
    short_title = title.strip().rstrip(".")
    return ContributionArtifacts(
        issue_number=issue_number,
        pr_title=f"[MOCK] Fix: {short_title}",
        pr_description=(
            f"[MOCK] This PR addresses issue #{issue_number}: \"{short_title}\".\n\n"
            "## Changes\n- [MOCK] Describe the code change here\n\n"
            "## Related Issue\nCloses #" + str(issue_number)
        ),
        commit_message=f"fix: {short_title.lower()} (#{issue_number})",
        testing_checklist=[
            "[MOCK] Existing tests pass",
            "[MOCK] Added a regression test for this issue",
            "[MOCK] Manually verified the fix resolves the reported behavior",
        ],
        source="mock",
    )


async def generate_contribution_artifacts(
    issue_number: int, title: str, analysis_context: str | None = None
) -> ContributionArtifacts:
    settings = get_settings()

    if not settings.llm_configured:
        return _mock_contribution(issue_number, title)

    from app.services.ai_service import _call_llm, _safe_json

    context = analysis_context or "No additional analysis context provided."
    prompt = (
        "Draft open-source contribution artifacts for closing this GitHub issue. "
        "Respond ONLY as JSON with keys: pr_title, pr_description (Markdown, include 'Closes #N'), "
        "commit_message (conventional-commits style), testing_checklist (array of strings).\n\n"
        f"Issue #{issue_number}: {title}\nContext:\n{context}"
    )
    raw = await _call_llm(prompt)
    parsed = _safe_json(raw, fallback={
        "pr_title": title, "pr_description": "", "commit_message": title, "testing_checklist": [],
    })
    return ContributionArtifacts(
        issue_number=issue_number,
        pr_title=parsed.get("pr_title", title),
        pr_description=parsed.get("pr_description", ""),
        commit_message=parsed.get("commit_message", title),
        testing_checklist=parsed.get("testing_checklist", []),
        source="llm",
    )
