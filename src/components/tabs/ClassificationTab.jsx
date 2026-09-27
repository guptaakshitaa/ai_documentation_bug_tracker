import { useEffect, useState } from "react";
import { api } from "../../api/client";
import { Spinner, ErrorBanner, SourceTag } from "../Primitives";
import { categoryClass } from "../categoryColors";

export function ClassificationTab({ repoUrl, issueNumber, onResult }) {
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    api
      .classifyIssue(repoUrl, issueNumber)
      .then((data) => {
        if (cancelled) return;
        setResult(data);
        onResult?.(data);
      })
      .catch((err) => !cancelled && setError(err.message))
      .finally(() => !cancelled && setLoading(false));
    return () => {
      cancelled = true;
    };
  }, [repoUrl, issueNumber]);

  if (loading) return <Spinner label="Classifying issue" />;
  if (error) return <ErrorBanner message={error} />;
  if (!result) return null;

  return (
    <div className="space-y-4">
      <div className={`border-l-2 pl-4 ${categoryClass(result.predicted_category)}`}>
        <p className="text-lg font-medium">{result.predicted_category}</p>
        <p className="text-sm text-slate mt-1">
          Confidence {(result.confidence * 100).toFixed(0)}% · Difficulty {result.difficulty}
        </p>
      </div>
      <SourceTag source={result.source} />
    </div>
  );
}
