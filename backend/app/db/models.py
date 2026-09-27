"""
ORM models for module G (Database Management).

- Repository: cached metadata for a GitHub repo the user has looked up.
- Issue: cached issue data, scoped to a repository.
- AnalysisRecord: every AI result ever generated for an issue (classification,
  analysis, doc check, bug resolution, contribution artifacts), so repeated
  requests can be served from history instead of re-calling GitHub/LLM, and
  so a full audit trail exists per the "analysis history" requirement in the
  design doc.
"""
from datetime import datetime, timezone

from sqlalchemy import String, Integer, Text, ForeignKey, DateTime, UniqueConstraint, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Repository(Base):
    __tablename__ = "repositories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    owner: Mapped[str] = mapped_column(String(255), index=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    full_name: Mapped[str] = mapped_column(String(511), unique=True, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    stars: Mapped[int] = mapped_column(Integer, default=0)
    forks: Mapped[int] = mapped_column(Integer, default=0)
    open_issues_count: Mapped[int] = mapped_column(Integer, default=0)
    default_branch: Mapped[str] = mapped_column(String(255), default="main")
    language: Mapped[str | None] = mapped_column(String(100), nullable=True)
    html_url: Mapped[str] = mapped_column(String(1023))
    last_fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    issues: Mapped[list["Issue"]] = relationship(back_populates="repository", cascade="all, delete-orphan")


class Issue(Base):
    __tablename__ = "issues"
    __table_args__ = (UniqueConstraint("repository_id", "number", name="uq_repo_issue_number"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    repository_id: Mapped[int] = mapped_column(ForeignKey("repositories.id"), index=True)
    number: Mapped[int] = mapped_column(Integer, index=True)
    title: Mapped[str] = mapped_column(Text)
    body: Mapped[str | None] = mapped_column(Text, nullable=True)
    state: Mapped[str] = mapped_column(String(50), default="open")
    comments: Mapped[int] = mapped_column(Integer, default=0)
    html_url: Mapped[str] = mapped_column(String(1023))
    last_fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    repository: Mapped["Repository"] = relationship(back_populates="issues")
    analysis_records: Mapped[list["AnalysisRecord"]] = relationship(back_populates="issue", cascade="all, delete-orphan")


class AnalysisRecord(Base):
    """One row per AI result ever generated for an issue. `analysis_type` is
    one of: classification | analysis | bug_resolution | contribution.
    `payload` stores the full JSON response so history can be replayed
    without recomputation."""
    __tablename__ = "analysis_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    issue_id: Mapped[int] = mapped_column(ForeignKey("issues.id"), index=True)
    analysis_type: Mapped[str] = mapped_column(String(50), index=True)
    source: Mapped[str] = mapped_column(String(20))  # "llm" or "mock"
    payload: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, index=True)

    issue: Mapped["Issue"] = relationship(back_populates="analysis_records")


class DocumentationCheck(Base):
    """Standalone doc checks aren't tied to a GitHub issue (raw pasted
    Markdown), so they get their own lightweight history table."""
    __tablename__ = "documentation_checks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    content_excerpt: Mapped[str] = mapped_column(Text)  # first ~300 chars, for display in history lists
    issue_count: Mapped[int] = mapped_column(Integer)
    source: Mapped[str] = mapped_column(String(20))
    payload: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, index=True)
