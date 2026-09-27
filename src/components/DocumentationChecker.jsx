import { useState } from "react";
import { api } from "../api/client";
import { Spinner, ErrorBanner, SourceTag } from "./Primitives";

const FINDING_COLOR = {
  broken_link: "border-brick",
  missing_alt_text: "border-brick",
  todo_marker: "border-amber",
  double_space: "border-slate",
  long_line: "border-slate",
};

export function DocumentationChecker() {
  const [content, setContent] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  async function handleCheck() {
    if (!content.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const data = await api.checkMarkdown(content);
      setResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="h-full flex flex-col">
      <div className="border-b border-line px-6 py-4">
        <h2 className="text-lg font-medium">Documentation checker</h2>
        <p className="text-sm text-slate mt-0.5">
          Paste Markdown to check for broken links, missing alt text, and formatting issues.
        </p>
      </div>

      <div className="flex-1 overflow-y-auto px-6 py-6 grid grid-cols-2 gap-6">
        <div className="flex flex-col">
          <label htmlFor="md-input" className="text-xs font-medium text-slate uppercase tracking-wide mb-2">
            Original
          </label>
          <textarea
            id="md-input"
            value={content}
            onChange={(e) => setContent(e.target.value)}
            placeholder={"# Getting started\n\nClone the repo and run `npm install`..."}
            className="flex-1 font-mono text-sm border border-line p-3 resize-none focus:border-ink"
          />
          <button
            onClick={handleCheck}
            disabled={loading || !content.trim()}
            className="mt-3 bg-ink text-paper text-sm font-medium px-4 py-2 self-start disabled:opacity-40"
          >
            {loading ? "Checking…" : "Check documentation"}
          </button>
        </div>

        <div className="flex flex-col overflow-y-auto">
          {loading && <Spinner label="Checking documentation" />}
          {error && <ErrorBanner message={error} />}
          {!loading && !error && !result && (
            <p className="text-sm text-slate">Results will appear here.</p>
          )}
          {result && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <p className="text-sm">
                  {result.issue_count === 0 ? "No issues found" : `${result.issue_count} issue(s) found`}
                </p>
                <SourceTag source={result.source} />
              </div>

              {result.findings.length > 0 && (
                <ul className="space-y-1.5">
                  {result.findings.map((f, i) => (
                    <li
                      key={i}
                      className={`text-sm border-l-2 pl-3 ${FINDING_COLOR[f.type] || "border-line"}`}
                    >
                      <span className="font-mono text-xs text-slate">Line {f.line_number}</span> — {f.detail}
                    </li>
                  ))}
                </ul>
              )}

              <div>
                <h3 className="text-xs font-medium text-slate uppercase tracking-wide mb-2">Improved version</h3>
                <pre className="font-mono text-xs whitespace-pre-wrap border border-line p-3 bg-line/10">
                  {result.improved_content}
                </pre>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
