from datetime import datetime
from pydantic import BaseModel, Field


class RepoRequest(BaseModel):
    repo_url: str = Field(..., examples=["https://github.com/freeCodeCamp/freeCodeCamp"])


class RepoMetadata(BaseModel):
    owner: str
    name: str
    full_name: str
    description: str | None = None
    stars: int
    forks: int
    open_issues_count: int
    default_branch: str
    language: str | None = None
    html_url: str


class IssueLabel(BaseModel):
    name: str
    color: str | None = None


class IssueSummary(BaseModel):
    number: int
    title: str
    body_excerpt: str | None = None
    state: str
    labels: list[IssueLabel] = []
    comments: int
    created_at: datetime
    updated_at: datetime
    html_url: str
    is_pull_request: bool = False


class IssueListResponse(BaseModel):
    repo: str
    total_open_issues: int
    fetched_count: int
    issues: list[IssueSummary]


class ClassificationResult(BaseModel):
    issue_number: int
    predicted_category: str  # Bug | Documentation | Enhancement | Question | Good First Issue
    confidence: float
    difficulty: str  # Easy | Medium | Hard
    source: str  # "llm" or "mock"


class IssueAnalysis(BaseModel):
    issue_number: int
    summary: str
    simplified_explanation: str
    difficulty: str
    recommended_steps: list[str]
    source: str  # "llm" or "mock"
