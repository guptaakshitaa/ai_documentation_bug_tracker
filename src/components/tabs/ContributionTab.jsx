import { useEffect, useState } from "react";
import { api } from "../../api/client";
import { Spinner, ErrorBanner, SourceTag } from "../Primitives";

function CopyButton({ text }) {
  const [copied, setCopied] = useState(false);
  return (
    <button
      onClick={() => {
        navigator.clipboard.writeText(text);
        setCopied(true);
        setTimeout(() => setCopied(false), 1500);
      }}
      className="font-mono text-[11px] border border-line px-2 py-1 hover:border-ink"
    >
      {copied ? "Copied" : "Copy"}
    </button>
  );
}

export function ContributionTab({ repoUrl, issueNumber }) {
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    api
      .generateContribution(repoUrl, issueNumber)
      .then((data) => !cancelled && setResult(data))
      .catch((err) => !cancelled && setError(err.message))
      .finally(() => !cancelled && setLoading(false));
    return () => {
      cancelled = true;
    };
  }, [repoUrl, issueNumber]);

  if (loading) return <Spinner label="Drafting contribution" />;
  if (error) return <ErrorBanner message={error} />;
  if (!result) return null;

  return (
    <div className="space-y-6 max-w-2xl">
      <div>
        <div className="flex items-center justify-between mb-1">
          <h3 className="text-xs font-medium text-slate uppercase tracking-wide">PR title</h3>
          <CopyButton text={result.pr_title} />
        </div>
        <p className="text-sm font-medium">{result.pr_title}</p>
      </div>

      <div>
        <div className="flex items-center justify-between mb-1">
          <h3 className="text-xs font-medium text-slate uppercase tracking-wide">PR description</h3>
          <CopyButton text={result.pr_description} />
        </div>
        <pre className="text-sm whitespace-pre-wrap border border-line p-3 bg-line/10">{result.pr_description}</pre>
      </div>

      <div>
        <div className="flex items-center justify-between mb-1">
          <h3 className="text-xs font-medium text-slate uppercase tracking-wide">Commit message</h3>
          <CopyButton text={result.commit_message} />
        </div>
        <p className="text-sm font-mono border border-line p-3 bg-line/10">{result.commit_message}</p>
      </div>

      <div>
        <h3 className="text-xs font-medium text-slate uppercase tracking-wide mb-2">Testing checklist</h3>
        <ul className="space-y-1.5">
          {result.testing_checklist.map((item, i) => (
            <li key={i} className="text-sm flex gap-2 items-start">
              <input type="checkbox" className="mt-1" />
              <span>{item}</span>
            </li>
          ))}
        </ul>
      </div>

      <SourceTag source={result.source} />
    </div>
  );
}
