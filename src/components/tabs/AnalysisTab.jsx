import { useEffect, useState } from "react";
import { api } from "../../api/client";
import { Spinner, ErrorBanner, SourceTag } from "../Primitives";

export function AnalysisTab({ repoUrl, issueNumber }) {
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    api
      .analyzeIssue(repoUrl, issueNumber)
      .then((data) => !cancelled && setResult(data))
      .catch((err) => !cancelled && setError(err.message))
      .finally(() => !cancelled && setLoading(false));
    return () => {
      cancelled = true;
    };
  }, [repoUrl, issueNumber]);

  if (loading) return <Spinner label="Analyzing issue" />;
  if (error) return <ErrorBanner message={error} />;
  if (!result) return null;

  return (
    <div className="space-y-6 max-w-2xl">
      <div>
        <h3 className="text-xs font-medium text-slate uppercase tracking-wide mb-1">Summary</h3>
        <p className="text-sm">{result.summary}</p>
      </div>
      <div>
        <h3 className="text-xs font-medium text-slate uppercase tracking-wide mb-1">In plain language</h3>
        <p className="text-sm">{result.simplified_explanation}</p>
      </div>
      <div>
        <h3 className="text-xs font-medium text-slate uppercase tracking-wide mb-2">Recommended steps</h3>
        <ol className="space-y-1.5">
          {result.recommended_steps.map((step, i) => (
            <li key={i} className="text-sm flex gap-2">
              <span className="font-mono text-slate">{i + 1}.</span>
              <span>{step}</span>
            </li>
          ))}
        </ol>
      </div>
      <SourceTag source={result.source} />
    </div>
  );
}
