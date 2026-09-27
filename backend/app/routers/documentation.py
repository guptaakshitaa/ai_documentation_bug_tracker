from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.assistant import MarkdownCheckRequest, DocumentationCheckResult
from app.services.doc_assistant import check_and_improve_markdown
from app.db.database import get_db_session
from app.db import crud

router = APIRouter(prefix="/api/documentation", tags=["documentation"])


@router.post("/check", response_model=DocumentationCheckResult)
async def check_markdown(payload: MarkdownCheckRequest, db: AsyncSession = Depends(get_db_session)):
    """Lints raw Markdown content and returns an improved version.
    Accepts pasted README/doc content directly — doesn't require a GitHub issue.
    Every check is saved to history for later review."""
    result = await check_and_improve_markdown(payload.content)
    await crud.save_documentation_check(
        db, content=payload.content, issue_count=result.issue_count,
        source=result.source, payload=result.model_dump(),
    )
    return result
