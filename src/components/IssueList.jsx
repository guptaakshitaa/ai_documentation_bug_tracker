import { EmptyState, Spinner } from "./Primitives";

export function IssueList({ issues, loading, selectedNumber, onSelect, classifications }) {
  if (loading) return <Spinner label="Fetching issues" />;

  if (!issues || issues.length === 0) {
    return (
      <EmptyState
        title="No issues loaded"
        detail="Enter a GitHub repository URL above and select Load repository."
      />
    );
  }

  return (
    <ul className="divide-y divide-line overflow-y-auto">
      {issues.map((issue) => {
        const isSelected = issue.number === selectedNumber;
        const classification = classifications[issue.number];
        const borderColor = classification
          ? {
              Bug: "border-l-brick",
              Documentation: "border-l-moss",
              Enhancement: "border-l-amber",
              Question: "border-l-slate",
              "Good First Issue": "border-l-moss",
            }[classification.predicted_category] || "border-l-line"
          : "border-l-transparent";

        return (
          <li key={issue.number}>
            <button
              onClick={() => onSelect(issue.number)}
              className={`w-full text-left px-4 py-3 border-l-4 ${borderColor} ${
                isSelected ? "bg-line/40" : "hover:bg-line/20"
              }`}
            >
              <div className="flex items-baseline gap-2">
                <span className="font-mono text-xs text-slate">#{issue.number}</span>
                {classification && (
                  <span className="font-mono text-[11px] text-slate">{classification.predicted_category}</span>
                )}
              </div>
              <p className="text-sm text-ink mt-0.5 line-clamp-2">{issue.title}</p>
            </button>
          </li>
        );
      })}
    </ul>
  );
}
