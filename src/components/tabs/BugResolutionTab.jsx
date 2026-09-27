import { useEffect, useState } from "react";
import { api } from "../../api/client";
import { Spinner, ErrorBanner, SourceTag } from "../Primitives";

export function BugResolutionTab({ repoUrl, issueNumber }) {
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    api
      .resolveBug(repoUrl, issueNumber)
      .then((data) => !cancelled && setResult(data))
      .catch((err) => !cancelled && setError(err.message))
      .finally(() => !cancelled && setLoading(false));
    return () => {
      cancelled = true;
    };
  }, [repoUrl, issueNumber]);

  if (loading) return <Spinner label="Analyzing bug" />;
  if (error) return <ErrorBanner message={error} />;
  if (!result) return null;

  return (
    <div className="space-y-6 max-w-2xl">
      {result.extracted_stack_frames.length > 0 && (
        <div>
          <h3 className="text-xs font-medium text-slate uppercase tracking-wide mb-2">Extracted stack trace</h3>
          <pre className="font-mono text-xs bg-ink text-paper p-3 overflow-x-auto whitespace-pre-wrap">
            {result.extracted_stack_frames.join("\n")}
          </pre>
        </div>
      )}
      <div>
        <h3 className="text-xs font-medium text-slate uppercase tracking-wide mb-2">Likely root causes</h3>
        <ul className="space-y-1.5">
          {result.likely_root_causes.map((cause, i) => (
            <li key={i} className="text-sm border-l-2 border-brick pl-3">
              {cause}
            </li>
          ))}
        </ul>
      </div>
      <div>
        <h3 className="text-xs font-medium text-slate uppercase tracking-wide mb-2">Recommended fix steps</h3>
        <ol className="space-y-1.5">
          {result.recommended_fix_steps.map((step, i) => (
            <li key={i} className="text-sm flex gap-2">
              <span className="font-mono text-slate">{i + 1}.</span>
              <span>{step}</span>
            </li>
          ))}
        </ol>
      </div>
      <div>
        <h3 className="text-xs font-medium text-slate uppercase tracking-wide mb-2">Suggested test cases</h3>
        <ul className="space-y-1.5">
          {result.suggested_test_cases.map((test, i) => (
            <li key={i} className="text-sm font-mono border-l-2 border-moss pl-3">
              {test}
            </li>
          ))}
        </ul>
      </div>
      <SourceTag source={result.source} />
    </div>
  );
}
