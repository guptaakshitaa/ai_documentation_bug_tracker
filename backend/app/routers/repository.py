from fastapi import APIRouter, Query, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.repository import (
    RepoRequest, RepoMetadata, IssueListResponse, IssueSummary, IssueLabel,
    ClassificationResult, IssueAnalysis,
)
from app.schemas.assistant import (
    BugResolutionResult, ContributionArtifacts, AnalysisHistoryItem, RepositoryHistoryItem,
)
from app.services.github_client import GitHubClient, parse_repo_url
from app.services.ai_service import classify_issue, analyze_issue
from app.services.bug_assistant import resolve_bug
from app.services.pr_generator import generate_contribution_artifacts
from app.db.database import get_db_session
from app.db import crud

router = APIRouter(prefix="/api/repository", tags=["repository"])


async def _get_or_fetch_repo_and_issue(db: AsyncSession, client: GitHubClient, owner: str, repo: str, issue_number: int):
    """Fetches repo + issue from GitHub, then upserts both into the DB cache.
    Returns (repo_row, issue_row, raw_issue_json)."""
    repo_data = await client.get_repo_metadata(owner, repo)
    repo_row = await crud.upsert_repository(
        db, owner=owner, name=repo_data["name"], full_name=repo_data["full_name"],
        description=repo_data.get("description"), stars=repo_data.get("stargazers_count", 0),
        forks=repo_data.get("forks_count", 0), open_issues_count=repo_data.get("open_issues_count", 0),
        default_branch=repo_data.get("default_branch", "main"), language=repo_data.get("language"),
        html_url=repo_data.get("html_url", f"https://github.com/{owner}/{repo}"),
    )
    issue_data = await client.get_issue(owner, repo, issue_number)
    issue_row = await crud.upsert_issue(
        db, repository_id=repo_row.id, number=issue_number, title=issue_data["title"],
        body=issue_data.get("body"), state=issue_data.get("state", "open"),
        comments=issue_data.get("comments", 0), html_url=issue_data.get("html_url", ""),
    )
    return repo_row, issue_row, issue_data


@router.post("/metadata", response_model=RepoMetadata)
async def get_repo_metadata(payload: RepoRequest, db: AsyncSession = Depends(get_db_session)):
    owner, repo = parse_repo_url(payload.repo_url)
    client = GitHubClient()
    data = await client.get_repo_metadata(owner, repo)

    await crud.upsert_repository(
        db, owner=owner, name=data["name"], full_name=data["full_name"],
        description=data.get("description"), stars=data.get("stargazers_count", 0),
        forks=data.get("forks_count", 0), open_issues_count=data.get("open_issues_count", 0),
        default_branch=data.get("default_branch", "main"), language=data.get("language"),
        html_url=data.get("html_url", payload.repo_url),
    )

    return RepoMetadata(
        owner=owner,
        name=data["name"],
        full_name=data["full_name"],
        description=data.get("description"),
        stars=data.get("stargazers_count", 0),
        forks=data.get("forks_count", 0),
        open_issues_count=data.get("open_issues_count", 0),
        default_branch=data.get("default_branch", "main"),
        language=data.get("language"),
        html_url=data.get("html_url", payload.repo_url),
    )


@router.post("/issues", response_model=IssueListResponse)
async def list_issues(
    payload: RepoRequest,
    per_page: int = Query(20, ge=1, le=100),
    page: int = Query(1, ge=1),
    include_pull_requests: bool = Query(False),
):
    owner, repo = parse_repo_url(payload.repo_url)
    client = GitHubClient()
    raw_issues = await client.get_issues(owner, repo, per_page=per_page, page=page)
    metadata = await client.get_repo_metadata(owner, repo)

    issues = []
    for item in raw_issues:
        is_pr = "pull_request" in item
        if is_pr and not include_pull_requests:
            continue
        body = item.get("body") or ""
        issues.append(IssueSummary(
            number=item["number"],
            title=item["title"],
            body_excerpt=(body[:200] + "...") if len(body) > 200 else body,
            state=item["state"],
            labels=[IssueLabel(name=l["name"], color=l.get("color")) for l in item.get("labels", [])],
            comments=item.get("comments", 0),
            created_at=item["created_at"],
            updated_at=item["updated_at"],
            html_url=item["html_url"],
            is_pull_request=is_pr,
        ))

    return IssueListResponse(
        repo=f"{owner}/{repo}",
        total_open_issues=metadata.get("open_issues_count", 0),
        fetched_count=len(issues),
        issues=issues,
    )


@router.post("/issues/{issue_number}/classify", response_model=ClassificationResult)
async def classify_repo_issue(
    issue_number: int, payload: RepoRequest, refresh: bool = Query(False),
    db: AsyncSession = Depends(get_db_session),
):
    owner, repo = parse_repo_url(payload.repo_url)
    client = GitHubClient()
    repo_row, issue_row, issue_data = await _get_or_fetch_repo_and_issue(db, client, owner, repo, issue_number)

    if not refresh:
        cached = await crud.get_latest_analysis(db, issue_id=issue_row.id, analysis_type="classification")
        if cached:
            return ClassificationResult(**cached.payload)

    result = await classify_issue(issue_number, issue_data["title"], issue_data.get("body"))
    await crud.save_analysis_record(db, issue_id=issue_row.id, analysis_type="classification",
                                     source=result.source, payload=result.model_dump())
    return result


@router.post("/issues/{issue_number}/analyze", response_model=IssueAnalysis)
async def analyze_repo_issue(
    issue_number: int, payload: RepoRequest, refresh: bool = Query(False),
    db: AsyncSession = Depends(get_db_session),
):
    owner, repo = parse_repo_url(payload.repo_url)
    client = GitHubClient()
    repo_row, issue_row, issue_data = await _get_or_fetch_repo_and_issue(db, client, owner, repo, issue_number)

    if not refresh:
        cached = await crud.get_latest_analysis(db, issue_id=issue_row.id, analysis_type="analysis")
        if cached:
            return IssueAnalysis(**cached.payload)

    result = await analyze_issue(issue_number, issue_data["title"], issue_data.get("body"))
    await crud.save_analysis_record(db, issue_id=issue_row.id, analysis_type="analysis",
                                     source=result.source, payload=result.model_dump())
    return result


@router.post("/issues/{issue_number}/resolve-bug", response_model=BugResolutionResult)
async def resolve_repo_bug(
    issue_number: int, payload: RepoRequest, refresh: bool = Query(False),
    db: AsyncSession = Depends(get_db_session),
):
    """Extracts stack traces and suggests root causes / fix steps / test cases."""
    owner, repo = parse_repo_url(payload.repo_url)
    client = GitHubClient()
    repo_row, issue_row, issue_data = await _get_or_fetch_repo_and_issue(db, client, owner, repo, issue_number)

    if not refresh:
        cached = await crud.get_latest_analysis(db, issue_id=issue_row.id, analysis_type="bug_resolution")
        if cached:
            return BugResolutionResult(**cached.payload)

    result = await resolve_bug(issue_number, issue_data["title"], issue_data.get("body"))
    await crud.save_analysis_record(db, issue_id=issue_row.id, analysis_type="bug_resolution",
                                     source=result.source, payload=result.model_dump())
    return result


@router.post("/issues/{issue_number}/generate-contribution", response_model=ContributionArtifacts)
async def generate_repo_contribution(
    issue_number: int, payload: RepoRequest, refresh: bool = Query(False),
    db: AsyncSession = Depends(get_db_session),
):
    """Drafts a PR title/description, commit message, and testing checklist for the issue."""
    owner, repo = parse_repo_url(payload.repo_url)
    client = GitHubClient()
    repo_row, issue_row, issue_data = await _get_or_fetch_repo_and_issue(db, client, owner, repo, issue_number)

    if not refresh:
        cached = await crud.get_latest_analysis(db, issue_id=issue_row.id, analysis_type="contribution")
        if cached:
            return ContributionArtifacts(**cached.payload)

    result = await generate_contribution_artifacts(issue_number, issue_data["title"])
    await crud.save_analysis_record(db, issue_id=issue_row.id, analysis_type="contribution",
                                     source=result.source, payload=result.model_dump())
    return result


@router.post("/issues/{issue_number}/history", response_model=list[AnalysisHistoryItem])
async def get_issue_analysis_history(
    issue_number: int, payload: RepoRequest, db: AsyncSession = Depends(get_db_session),
):
    """Every AI result ever generated for this issue, newest first."""
    owner, repo = parse_repo_url(payload.repo_url)
    client = GitHubClient()
    repo_row, issue_row, _ = await _get_or_fetch_repo_and_issue(db, client, owner, repo, issue_number)
    records = await crud.get_issue_history(db, issue_id=issue_row.id)
    return [
        AnalysisHistoryItem(analysis_type=r.analysis_type, source=r.source, created_at=r.created_at, payload=r.payload)
        for r in records
    ]


@router.get("/history", response_model=list[RepositoryHistoryItem])
async def get_repository_history(db: AsyncSession = Depends(get_db_session)):
    """All repositories previously looked up, most recently fetched first."""
    repos = await crud.list_repositories(db)
    return [
        RepositoryHistoryItem(
            full_name=r.full_name, description=r.description, stars=r.stars,
            open_issues_count=r.open_issues_count, last_fetched_at=r.last_fetched_at,
        )
        for r in repos
    ]
