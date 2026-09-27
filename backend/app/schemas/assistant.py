from pydantic import BaseModel
from datetime import datetime


class MarkdownCheckRequest(BaseModel):
    content: str


class MarkdownIssue(BaseModel):
    type: str          # "broken_link" | "missing_alt_text" | "long_line" | "todo_marker" | "double_space"
    line_number: int
    detail: str


class DocumentationCheckResult(BaseModel):
    issue_count: int
    findings: list[MarkdownIssue]
    improved_content: str
    source: str  # "llm" or "mock"


class BugResolutionRequest(BaseModel):
    repo_url: str


class BugResolutionResult(BaseModel):
    issue_number: int
    extracted_stack_frames: list[str]
    likely_root_causes: list[str]
    recommended_fix_steps: list[str]
    suggested_test_cases: list[str]
    source: str  # "llm" or "mock"


class AnalysisHistoryItem(BaseModel):
    analysis_type: str
    source: str
    created_at: datetime
    payload: dict


class RepositoryHistoryItem(BaseModel):
    full_name: str
    description: str | None = None
    stars: int
    open_issues_count: int
    last_fetched_at: datetime


class ContributionArtifacts(BaseModel):
    issue_number: int
    pr_title: str
    pr_description: str
    commit_message: str
    testing_checklist: list[str]
    source: str
