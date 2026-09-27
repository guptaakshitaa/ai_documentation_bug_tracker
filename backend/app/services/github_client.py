"""
Thin wrapper around the GitHub REST API (v3).

Works without a token for public repositories (60 requests/hour limit,
shared across your IP). Set GITHUB_TOKEN in the environment to raise that
to 5000/hour and access private repos you have permission for.
"""
import re
import httpx
from fastapi import HTTPException

from app.config import get_settings

REPO_URL_PATTERN = re.compile(
    r"github\.com[/:]([\w.-]+)/([\w.-]+?)(?:\.git)?/?$"
)


def parse_repo_url(repo_url: str) -> tuple[str, str]:
    """Extract (owner, repo) from a GitHub URL like
    https://github.com/freeCodeCamp/freeCodeCamp or a bare 'owner/repo'."""
    repo_url = repo_url.strip()
    if "/" in repo_url and "github.com" not in repo_url and not repo_url.startswith("http"):
        # bare "owner/repo" form
        parts = repo_url.split("/")
        if len(parts) == 2:
            return parts[0], parts[1]

    match = REPO_URL_PATTERN.search(repo_url)
    if not match:
        raise HTTPException(status_code=400, detail=f"Could not parse a GitHub owner/repo from: {repo_url}")
    return match.group(1), match.group(2)


class GitHubClient:
    def __init__(self):
        settings = get_settings()
        self.base_url = settings.github_api_base
        self.headers = {"Accept": "application/vnd.github+json"}
        if settings.github_token:
            self.headers["Authorization"] = f"Bearer {settings.github_token}"

    async def _get(self, path: str, params: dict | None = None) -> httpx.Response:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(f"{self.base_url}{path}", headers=self.headers, params=params)
        if resp.status_code == 403 and "rate limit" in resp.text.lower():
            raise HTTPException(
                status_code=429,
                detail="GitHub API rate limit exceeded. Set GITHUB_TOKEN in your environment for a higher limit.",
            )
        if resp.status_code == 404:
            raise HTTPException(status_code=404, detail="Repository not found (check the URL / it may be private).")
        if resp.status_code >= 400:
            raise HTTPException(status_code=resp.status_code, detail=f"GitHub API error: {resp.text[:200]}")
        return resp

    async def get_repo_metadata(self, owner: str, repo: str) -> dict:
        resp = await self._get(f"/repos/{owner}/{repo}")
        return resp.json()

    async def get_issues(self, owner: str, repo: str, state: str = "open", per_page: int = 20, page: int = 1) -> list[dict]:
        """Note: GitHub's issues endpoint also returns pull requests; callers
        should filter using the 'pull_request' key if they want issues only."""
        resp = await self._get(
            f"/repos/{owner}/{repo}/issues",
            params={"state": state, "per_page": per_page, "page": page, "sort": "updated", "direction": "desc"},
        )
        return resp.json()

    async def get_issue(self, owner: str, repo: str, issue_number: int) -> dict:
        resp = await self._get(f"/repos/{owner}/{repo}/issues/{issue_number}")
        return resp.json()
