"""
AI service layer for issue classification and analysis.

If OPENAI_API_KEY is configured, calls the LLM directly. Otherwise falls back
to a heuristic MOCK so the rest of the app (routes, frontend, tests) can be
built and demoed before real API keys are wired in. Every mock response is
tagged source="mock" so callers/UI can show a "placeholder" badge.
"""
import json
import re

from app.config import get_settings
from app.schemas.repository import ClassificationResult, IssueAnalysis

CATEGORY_KEYWORDS = {
    "Bug": ["bug", "error", "crash", "fail", "broken", "exception", "traceback", "doesn't work", "not working"],
    "Documentation": ["docs", "documentation", "readme", "typo", "grammar", "broken link", "wording", "clarify"],
    "Enhancement": ["feature", "enhancement", "improve", "add support", "request"],
    "Question": ["how do i", "question", "help", "why does", "?"],
}


def _mock_classify(title: str, body: str) -> tuple[str, float, str]:
    text = f"{title} {body}".lower()
    scores = {cat: sum(1 for kw in kws if kw in text) for cat, kws in CATEGORY_KEYWORDS.items()}
    best_category = max(scores, key=scores.get)
    if scores[best_category] == 0:
        best_category = "Good First Issue" if len(text) < 200 else "Enhancement"
    confidence = min(0.5 + 0.1 * scores.get(best_category, 0), 0.95)
    difficulty = "Easy" if len(text) < 300 else ("Medium" if len(text) < 800 else "Hard")
    return best_category, round(confidence, 2), difficulty


async def classify_issue(issue_number: int, title: str, body: str | None) -> ClassificationResult:
    settings = get_settings()
    body = body or ""

    if not settings.llm_configured:
        category, confidence, difficulty = _mock_classify(title, body)
        return ClassificationResult(
            issue_number=issue_number,
            predicted_category=category,
            confidence=confidence,
            difficulty=difficulty,
            source="mock",
        )

    # --- Real LLM path (used once OPENAI_API_KEY is set) ---
    prompt = (
        "Classify this GitHub issue into exactly one category: "
        "Bug, Documentation, Enhancement, Question, or Good First Issue. "
        "Also estimate difficulty (Easy, Medium, Hard). "
        f"Respond ONLY as JSON: {{\"category\": str, \"confidence\": float, \"difficulty\": str}}.\n\n"
        f"Title: {title}\nBody: {body[:1500]}"
    )
    raw = await _call_llm(prompt)
    parsed = _safe_json(raw, fallback={"category": "Enhancement", "confidence": 0.5, "difficulty": "Medium"})
    return ClassificationResult(
        issue_number=issue_number,
        predicted_category=parsed.get("category", "Enhancement"),
        confidence=float(parsed.get("confidence", 0.5)),
        difficulty=parsed.get("difficulty", "Medium"),
        source="llm",
    )


async def analyze_issue(issue_number: int, title: str, body: str | None) -> IssueAnalysis:
    settings = get_settings()
    body = body or ""

    if not settings.llm_configured:
        return IssueAnalysis(
            issue_number=issue_number,
            summary=f"[MOCK] This issue is about: {title[:120]}",
            simplified_explanation=(
                "[MOCK] This is a placeholder explanation. Once OPENAI_API_KEY is set, "
                "this will contain a plain-language breakdown of the issue for newcomers."
            ),
            difficulty=_mock_classify(title, body)[2],
            recommended_steps=[
                "[MOCK] Reproduce the issue locally",
                "[MOCK] Identify the relevant source file(s)",
                "[MOCK] Implement and test a fix",
            ],
            source="mock",
        )

    # --- Real LLM path ---
    prompt = (
        "You are helping a new open-source contributor understand a GitHub issue. "
        "Respond ONLY as JSON with keys: summary (1-2 sentences), "
        "simplified_explanation (plain language, 2-4 sentences), difficulty (Easy/Medium/Hard), "
        "recommended_steps (array of 3-5 short actionable strings).\n\n"
        f"Title: {title}\nBody: {body[:2000]}"
    )
    raw = await _call_llm(prompt)
    parsed = _safe_json(raw, fallback={
        "summary": title,
        "simplified_explanation": "Could not parse LLM response.",
        "difficulty": "Medium",
        "recommended_steps": [],
    })
    return IssueAnalysis(
        issue_number=issue_number,
        summary=parsed.get("summary", title),
        simplified_explanation=parsed.get("simplified_explanation", ""),
        difficulty=parsed.get("difficulty", "Medium"),
        recommended_steps=parsed.get("recommended_steps", []),
        source="llm",
    )


async def _call_llm(prompt: str) -> str:
    """Calls an OpenAI-compatible chat completions endpoint."""
    import httpx

    settings = get_settings()
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {settings.openai_api_key}"},
            json={
                "model": settings.openai_model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.3,
            },
        )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]


def _safe_json(raw: str, fallback: dict) -> dict:
    try:
        cleaned = re.sub(r"^```json|```$", "", raw.strip(), flags=re.MULTILINE).strip()
        return json.loads(cleaned)
    except (json.JSONDecodeError, TypeError):
        return fallback
