import { useState } from "react";
import { EmptyState } from "./Primitives";
import { ClassificationTab } from "./tabs/ClassificationTab";
import { AnalysisTab } from "./tabs/AnalysisTab";
import { BugResolutionTab } from "./tabs/BugResolutionTab";
import { ContributionTab } from "./tabs/ContributionTab";

const TABS = [
  { id: "classify", label: "Classification" },
  { id: "analyze", label: "AI analysis" },
  { id: "bug", label: "Bug resolution" },
  { id: "contribute", label: "Contribution" },
];

export function IssueDetail({ repoUrl, issue, onClassification }) {
  const [activeTab, setActiveTab] = useState("classify");

  if (!issue) {
    return (
      <EmptyState
        title="Select an issue"
        detail="Pick an issue from the list to see AI classification, analysis, bug-resolution suggestions, and contribution-ready content."
      />
    );
  }

  return (
    <div key={issue.number} className="detail-enter h-full flex flex-col">
      <div className="border-b border-line px-6 py-4">
        <p className="font-mono text-xs text-slate">#{issue.number}</p>
        <h2 className="text-lg font-medium mt-0.5">{issue.title}</h2>
        <a
          href={issue.html_url}
          target="_blank"
          rel="noreferrer"
          className="text-xs text-slate underline underline-offset-2"
        >
          View on GitHub
        </a>
      </div>

      <div className="border-b border-line px-6 flex gap-6">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`text-sm py-3 border-b-2 -mb-px ${
              activeTab === tab.id ? "border-ink text-ink" : "border-transparent text-slate hover:text-ink"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      <div className="flex-1 overflow-y-auto px-6 py-6">
        {activeTab === "classify" && (
          <ClassificationTab repoUrl={repoUrl} issueNumber={issue.number} onResult={onClassification} />
        )}
        {activeTab === "analyze" && <AnalysisTab repoUrl={repoUrl} issueNumber={issue.number} />}
        {activeTab === "bug" && <BugResolutionTab repoUrl={repoUrl} issueNumber={issue.number} />}
        {activeTab === "contribute" && <ContributionTab repoUrl={repoUrl} issueNumber={issue.number} />}
      </div>
    </div>
  );
}
