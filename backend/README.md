# AI Documentation & Bug Resolution Assistant — Backend

FastAPI backend implementing **Repository Integration** and the skeleton of
**Issue Classification** / **AI-Based Issue Analysis** from the design doc.

## What's real vs. mocked right now

| Piece | Status |
|---|---|
| GitHub repo metadata fetch | **Real** — calls `api.github.com`, no token required for public repos |
| GitHub issue list / single issue fetch | **Real** |
| Issue classification (Bug/Docs/Enhancement/...) | **Mock** (keyword heuristic) — becomes real once `OPENAI_API_KEY` is set |
| Issue analysis (summary, steps) | **Mock** — same, switches to real LLM automatically |
| Documentation Assistant — markdown linting (broken links, missing alt text, TODOs, formatting) | **Real** — regex-based, no LLM needed |
| Documentation Assistant — rewritten/improved text | **Mock** cleanup pass until `OPENAI_API_KEY` is set |
| Bug Resolution Assistant — stack trace extraction | **Real** — regex-based |
| Bug Resolution Assistant — root cause / fix steps / test cases | **Mock** until LLM key is set |
| Contribution Generator (PR title/description, commit message, checklist) | **Mock** until LLM key is set |
| Database layer (SQLite, caching + history) | **Real** — SQLAlchemy async, tested |
| React frontend | Not yet built — next milestone |

Every mocked response has `"source": "mock"` in the JSON so the frontend can
show a placeholder badge; real responses have `"source": "llm"`.

## Setup

```bash
cd backend
python -m venv venv && source venv/bin/activate   # or venv\Scripts\activate on Windows
pip install -r requirements.txt
cp .env.example .env   # optional — fill in GITHUB_TOKEN / OPENAI_API_KEY later
uvicorn app.main:app --reload
```

Then open **http://localhost:8000/docs** for interactive Swagger UI.

## Endpoints so far

- `GET /` — health + config status
- `POST /api/repository/metadata` — `{"repo_url": "https://github.com/freeCodeCamp/freeCodeCamp"}`
- `POST /api/repository/issues` — same body, query params `per_page`, `page`, `include_pull_requests`
- `POST /api/repository/issues/{issue_number}/classify`
- `POST /api/repository/issues/{issue_number}/analyze`
- `POST /api/repository/issues/{issue_number}/resolve-bug` — stack trace + root cause + fix steps + test cases
- `POST /api/repository/issues/{issue_number}/generate-contribution` — PR title/description, commit message, checklist
- `POST /api/documentation/check` — `{"content": "...markdown..."}`, lints and returns an improved version (works standalone, no GitHub call needed)
- `POST /api/repository/issues/{issue_number}/history` — every AI result ever generated for that issue, newest first
- `GET /api/repository/history` — every repository ever looked up, most recently fetched first

## Database & caching

Every repo/issue lookup is upserted into SQLite (`assistant.db`, created automatically on
first run), and every classification / analysis / bug-resolution / contribution-generation
result is saved to `analysis_records`. By default, repeat calls to the same
`classify` / `analyze` / `resolve-bug` / `generate-contribution` endpoint for the same
issue are served from that cache instead of re-hitting GitHub/the LLM. Pass
`?refresh=true` on any of those endpoints to force recomputation.

Swap `DATABASE_URL` in `.env` to a Postgres URL (e.g.
`postgresql+asyncpg://user:pass@host/db`) for production — no code changes needed.

### Example

```bash
curl -X POST http://localhost:8000/api/repository/issues \
  -H "Content-Type: application/json" \
  -d '{"repo_url": "https://github.com/freeCodeCamp/freeCodeCamp"}'
```

## Notes

- Unauthenticated GitHub requests are capped at **60/hour per IP**. Add a
  `GITHUB_TOKEN` (a classic PAT with no scopes is enough for public repos)
  to raise this to 5000/hour.
- Without `OPENAI_API_KEY`, classification/analysis use a keyword-based mock
  so you can build and demo the frontend before spending on LLM calls.

## Next steps (matches the project timeline)

1. ~~Documentation Assistant (Markdown lint + LLM rewrite)~~ — done
2. ~~Bug Resolution Assistant (root-cause + fix suggestions)~~ — done
3. ~~PR/Commit message generator~~ — done
4. ~~Database layer (SQLite/Postgres) to cache analysis results~~ — done
5. React frontend dashboard
