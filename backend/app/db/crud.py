"""
CRUD helpers. Kept as plain functions (rather than a repository-pattern
class hierarchy) since the query set is small and this stays easy to read
for a course project.
"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Repository, Issue, AnalysisRecord, DocumentationCheck


async def upsert_repository(db: AsyncSession, *, owner: str, name: str, full_name: str,
                             description: str | None, stars: int, forks: int,
                             open_issues_count: int, default_branch: str,
                             language: str | None, html_url: str) -> Repository:
    result = await db.execute(select(Repository).where(Repository.full_name == full_name))
    repo = result.scalar_one_or_none()
    if repo is None:
        repo = Repository(owner=owner, name=name, full_name=full_name)
        db.add(repo)

    repo.description = description
    repo.stars = stars
    repo.forks = forks
    repo.open_issues_count = open_issues_count
    repo.default_branch = default_branch
    repo.language = language
    repo.html_url = html_url

    await db.commit()
    await db.refresh(repo)
    return repo


async def upsert_issue(db: AsyncSession, *, repository_id: int, number: int, title: str,
                        body: str | None, state: str, comments: int, html_url: str) -> Issue:
    result = await db.execute(
        select(Issue).where(Issue.repository_id == repository_id, Issue.number == number)
    )
    issue = result.scalar_one_or_none()
    if issue is None:
        issue = Issue(repository_id=repository_id, number=number)
        db.add(issue)

    issue.title = title
    issue.body = body
    issue.state = state
    issue.comments = comments
    issue.html_url = html_url

    await db.commit()
    await db.refresh(issue)
    return issue


async def save_analysis_record(db: AsyncSession, *, issue_id: int, analysis_type: str,
                                source: str, payload: dict) -> AnalysisRecord:
    record = AnalysisRecord(issue_id=issue_id, analysis_type=analysis_type, source=source, payload=payload)
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return record


async def get_latest_analysis(db: AsyncSession, *, issue_id: int, analysis_type: str) -> AnalysisRecord | None:
    result = await db.execute(
        select(AnalysisRecord)
        .where(AnalysisRecord.issue_id == issue_id, AnalysisRecord.analysis_type == analysis_type)
        .order_by(AnalysisRecord.created_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def get_issue_history(db: AsyncSession, *, issue_id: int) -> list[AnalysisRecord]:
    result = await db.execute(
        select(AnalysisRecord)
        .where(AnalysisRecord.issue_id == issue_id)
        .order_by(AnalysisRecord.created_at.desc())
    )
    return list(result.scalars().all())


async def save_documentation_check(db: AsyncSession, *, content: str, issue_count: int,
                                    source: str, payload: dict) -> DocumentationCheck:
    record = DocumentationCheck(
        content_excerpt=content[:300], issue_count=issue_count, source=source, payload=payload
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return record


async def list_repositories(db: AsyncSession) -> list[Repository]:
    result = await db.execute(select(Repository).order_by(Repository.last_fetched_at.desc()))
    return list(result.scalars().all())
