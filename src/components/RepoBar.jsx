import { useState } from "react";

export function RepoBar({ onLoad, loading, repoMeta, error }) {
  const [value, setValue] = useState("https://github.com/freeCodeCamp/freeCodeCamp");

  function handleSubmit(e) {
    e.preventDefault();
    if (value.trim()) onLoad(value.trim());
  }

  return (
    <div className="border-b border-line px-6 py-4">
      <form onSubmit={handleSubmit} className="flex items-center gap-3">
        <label htmlFor="repo-url" className="sr-only">
          GitHub repository URL
        </label>
        <input
          id="repo-url"
          value={value}
          onChange={(e) => setValue(e.target.value)}
          placeholder="https://github.com/owner/repo"
          className="flex-1 font-mono text-sm bg-transparent border border-line px-3 py-2 focus:border-ink"
        />
        <button
          type="submit"
          disabled={loading}
          className="bg-ink text-paper text-sm font-medium px-4 py-2 disabled:opacity-40"
        >
          {loading ? "Loading…" : "Load repository"}
        </button>
      </form>

      {error && <p className="text-sm text-brick mt-2">{error}</p>}

      {repoMeta && !error && (
        <div className="flex items-center gap-4 mt-3 text-sm text-slate">
          <span className="font-medium text-ink">{repoMeta.full_name}</span>
          {repoMeta.language && <span>{repoMeta.language}</span>}
          <span>★ {repoMeta.stars.toLocaleString()}</span>
          <span>{repoMeta.open_issues_count} open issues</span>
        </div>
      )}
    </div>
  );
}
