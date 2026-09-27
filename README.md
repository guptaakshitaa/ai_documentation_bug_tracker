# AI Documentation & Bug Resolution Assistant — Frontend

React + Tailwind dashboard (module H) for the backend built earlier. Lets you:

- Enter a GitHub repo URL and browse its open issues
- Classify each issue (Bug / Documentation / Enhancement / Question / Good First Issue)
- Get an AI summary, plain-language explanation, and recommended steps
- For bugs: see extracted stack frames, likely root causes, fix steps, test cases
- Generate PR title/description, commit message, and a testing checklist — with one-click copy
- Paste raw Markdown into a standalone documentation checker (no GitHub issue needed)

## Setup

```bash
cd frontend
npm install
cp .env.example .env   # point at your backend if it's not on localhost:8000
npm run dev
```

Open **http://localhost:5173**. Make sure the backend (`../backend`) is running on
port 8000 first — the app calls it directly, there's no proxy.

## Design notes

Every classified issue gets a colored left border in the issue list (green =
Documentation, brick red = Bug, amber = Enhancement, slate = Question/neutral) —
the same visual language as a diff gutter, so category is legible without
reading a badge. Every AI-generated result carries a small `mock` / `llm` tag
so you always know whether you're looking at a placeholder or a real model
response — this flips automatically once the backend has `OPENAI_API_KEY` set.

## Structure

```
src/
  api/client.js           — one function per backend endpoint
  components/
    RepoBar.jsx            — repo URL input + metadata summary
    IssueList.jsx          — left-rail issue list
    IssueDetail.jsx         — tab container for a selected issue
    DocumentationChecker.jsx — standalone markdown checker (no issue needed)
    tabs/
      ClassificationTab.jsx
      AnalysisTab.jsx
      BugResolutionTab.jsx
      ContributionTab.jsx
  App.jsx                  — layout + state
```

## Not yet built

- Persisted view of analysis history (backend already stores it at
  `/api/repository/issues/{n}/history` and `/api/repository/history` — just
  needs a UI panel)
- Auth / private repo support
- Pagination controls for repos with >20 open issues
