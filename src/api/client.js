const BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

async function request(path, options = {}) {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail || detail;
    } catch {
      // response body wasn't JSON; keep statusText
    }
    throw new Error(detail);
  }
  return res.json();
}

export const api = {
  getRepoMetadata: (repoUrl) =>
    request("/api/repository/metadata", { method: "POST", body: JSON.stringify({ repo_url: repoUrl }) }),

  listIssues: (repoUrl, { perPage = 20, page = 1 } = {}) =>
    request(`/api/repository/issues?per_page=${perPage}&page=${page}`, {
      method: "POST",
      body: JSON.stringify({ repo_url: repoUrl }),
    }),

  classifyIssue: (repoUrl, issueNumber, { refresh = false } = {}) =>
    request(`/api/repository/issues/${issueNumber}/classify?refresh=${refresh}`, {
      method: "POST",
      body: JSON.stringify({ repo_url: repoUrl }),
    }),

  analyzeIssue: (repoUrl, issueNumber, { refresh = false } = {}) =>
    request(`/api/repository/issues/${issueNumber}/analyze?refresh=${refresh}`, {
      method: "POST",
      body: JSON.stringify({ repo_url: repoUrl }),
    }),

  resolveBug: (repoUrl, issueNumber, { refresh = false } = {}) =>
    request(`/api/repository/issues/${issueNumber}/resolve-bug?refresh=${refresh}`, {
      method: "POST",
      body: JSON.stringify({ repo_url: repoUrl }),
    }),

  generateContribution: (repoUrl, issueNumber, { refresh = false } = {}) =>
    request(`/api/repository/issues/${issueNumber}/generate-contribution?refresh=${refresh}`, {
      method: "POST",
      body: JSON.stringify({ repo_url: repoUrl }),
    }),

  getIssueHistory: (repoUrl, issueNumber) =>
    request(`/api/repository/issues/${issueNumber}/history`, {
      method: "POST",
      body: JSON.stringify({ repo_url: repoUrl }),
    }),

  getRepoHistory: () => request("/api/repository/history"),

  checkMarkdown: (content) =>
    request("/api/documentation/check", { method: "POST", body: JSON.stringify({ content }) }),
};
