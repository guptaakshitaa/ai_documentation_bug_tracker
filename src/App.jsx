import { useState } from "react";
import { api } from "./api/client";
import { RepoBar } from "./components/RepoBar";
import { IssueList } from "./components/IssueList";
import { IssueDetail } from "./components/IssueDetail";
import { DocumentationChecker } from "./components/DocumentationChecker";

export default function App() {
  const [repoUrl, setRepoUrl] = useState(null);
  const [repoMeta, setRepoMeta] = useState(null);
  const [issues, setIssues] = useState([]);
  const [selectedNumber, setSelectedNumber] = useState(null);
  const [classifications, setClassifications] = useState({});
  const [loadingRepo, setLoadingRepo] = useState(false);
  const [repoError, setRepoError] = useState(null);
  const [view, setView] = useState("issues"); // "issues" | "docs"

  async function handleLoadRepo(url) {
    setLoadingRepo(true);
    setRepoError(null);
    setIssues([]);
    setSelectedNumber(null);
    setClassifications({});
    try {
      const [meta, issueList] = await Promise.all([api.getRepoMetadata(url), api.listIssues(url)]);
      setRepoMeta(meta);
      setIssues(issueList.issues);
      setRepoUrl(url);
    } catch (err) {
      setRepoError(err.message);
      setRepoMeta(null);
    } finally {
      setLoadingRepo(false);
    }
  }

  const selectedIssue = issues.find((i) => i.number === selectedNumber) || null;

  return (
    <div className="h-screen flex flex-col">
      <header className="border-b border-line px-6 py-3 flex items-center justify-between">
        <div>
          <h1 className="font-medium">Contribution Assistant</h1>
          <p className="text-xs text-slate">AI documentation & bug resolution for open-source repositories</p>
        </div>
        <nav className="flex gap-1 font-mono text-xs">
          <button
            onClick={() => setView("issues")}
            className={`px-3 py-1.5 border ${view === "issues" ? "border-ink" : "border-line text-slate"}`}
          >
            Issues
          </button>
          <button
            onClick={() => setView("docs")}
            className={`px-3 py-1.5 border ${view === "docs" ? "border-ink" : "border-line text-slate"}`}
          >
            Docs checker
          </button>
        </nav>
      </header>

      {view === "issues" ? (
        <>
          <RepoBar onLoad={handleLoadRepo} loading={loadingRepo} repoMeta={repoMeta} error={repoError} />
          <div className="flex-1 grid grid-cols-[320px_1fr] overflow-hidden">
            <div className="border-r border-line overflow-y-auto">
              <IssueList
                issues={issues}
                loading={loadingRepo}
                selectedNumber={selectedNumber}
                onSelect={setSelectedNumber}
                classifications={classifications}
              />
            </div>
            <div className="overflow-hidden">
              <IssueDetail
                repoUrl={repoUrl}
                issue={selectedIssue}
                onClassification={(result) =>
                  setClassifications((prev) => ({ ...prev, [result.issue_number]: result }))
                }
              />
            </div>
          </div>
        </>
      ) : (
        <div className="flex-1 overflow-hidden">
          <DocumentationChecker />
        </div>
      )}
    </div>
  );
}
