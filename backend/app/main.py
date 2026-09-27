from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.db.database import init_db
from app.routers import repository, documentation

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    description=(
        "Backend for the AI Documentation & Bug Resolution Assistant. "
        "Integrates the GitHub REST API with LLM-based issue classification, "
        "analysis, documentation improvement, and PR/commit generation."
    ),
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(repository.router)
app.include_router(documentation.router)


@app.on_event("startup")
async def on_startup():
    await init_db()


@app.get("/")
async def root():
    return {
        "app": settings.app_name,
        "status": "running",
        "github_configured": settings.github_configured,
        "llm_configured": settings.llm_configured,
        "docs": "/docs",
    }


@app.get("/health")
async def health():
    return {"status": "ok"}
