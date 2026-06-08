import { useState, useEffect } from "react";
import Link from "next/link";
import Card from "../components/ui/Card";

export default function KnowledgeBase() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [sourceType, setSourceType] = useState("");
  const [page, setPage] = useState(1);
  const [stats, setStats] = useState(null);
  const limit = 20;

  useEffect(() => {
    fetch("/api/stats")
      .then((r) => r.json())
      .then(setStats)
      .catch(() => {});
  }, []);

  useEffect(() => {
    setLoading(true);
    setPage(1);
  }, [search, sourceType]);

  useEffect(() => {
    setLoading(true);
    const params = new URLSearchParams();
    if (search) params.set("search", search);
    if (sourceType) params.set("source_type", sourceType);
    params.set("limit", String(limit));
    params.set("offset", String((page - 1) * limit));

    fetch(`/api/papers?${params}`)
      .then((r) => r.json())
      .then(setData)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [search, sourceType, page]);

  const totalPages = data ? Math.ceil(data.total / limit) : 1;

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Knowledge Base</h1>
        <p className="text-gray-500 mt-1">
          All papers discovered across research jobs — sample data and web results combined
        </p>
      </div>

      {stats && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-8">
          <Card className="text-center py-4">
            <p className="text-2xl font-bold text-gray-900">{stats.total_papers}</p>
            <p className="text-xs text-gray-500">Total Papers</p>
          </Card>
          <Card className="text-center py-4">
            <p className="text-2xl font-bold text-green-600">{stats.sample_papers}</p>
            <p className="text-xs text-gray-500">Sample Papers</p>
          </Card>
          <Card className="text-center py-4">
            <p className="text-2xl font-bold text-blue-600">{stats.web_papers}</p>
            <p className="text-xs text-gray-500">Web Discovered</p>
          </Card>
          <Card className="text-center py-4">
            <p className="text-2xl font-bold text-gray-900">{stats.total_jobs}</p>
            <p className="text-xs text-gray-500">Research Jobs</p>
          </Card>
        </div>
      )}

      <Card className="mb-6">
        <div className="flex flex-col sm:flex-row gap-3">
          <div className="flex-1">
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search titles, authors, abstracts..."
              className="input-field"
            />
          </div>
          <select
            value={sourceType}
            onChange={(e) => setSourceType(e.target.value)}
            className="input-field sm:w-48"
          >
            <option value="">All sources</option>
            <option value="sample">Sample data</option>
            <option value="web">Web discovered</option>
          </select>
        </div>
      </Card>

      {loading ? (
        <div className="text-center py-12">
          <svg className="animate-spin w-6 h-6 mx-auto text-primary-600" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
        </div>
      ) : data && data.papers ? (
        <>
          <div className="flex items-center justify-between mb-4">
            <p className="text-sm text-gray-500">{data.total} papers found</p>
            {totalPages > 1 && (
              <div className="flex items-center gap-2 text-sm">
                <button
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page <= 1}
                  className="px-3 py-1 rounded border border-gray-200 disabled:opacity-30 hover:border-primary-300 transition-colors"
                >
                  Prev
                </button>
                <span className="text-gray-600">
                  Page {page} of {totalPages}
                </span>
                <button
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  disabled={page >= totalPages}
                  className="px-3 py-1 rounded border border-gray-200 disabled:opacity-30 hover:border-primary-300 transition-colors"
                >
                  Next
                </button>
              </div>
            )}
          </div>
          <div className="space-y-3">
            {data.papers.map((p) => (
              <div key={p.id} className="card hover:shadow-md transition-shadow">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className={`text-xs font-medium px-2 py-0.5 rounded ${
                        p.source_type === "web"
                          ? "bg-blue-100 text-blue-700"
                          : "bg-green-100 text-green-700"
                      }`}>
                        {p.source_type === "web" ? "WEB" : "SAMPLE"}
                      </span>
                      <span className="text-xs text-gray-400">{p.source}</span>
                      <span className="text-xs text-gray-400">({p.year})</span>
                    </div>
                    <h3 className="font-semibold text-gray-900 truncate">{p.title}</h3>
                    {p.authors && (
                      <p className="text-xs text-gray-500 mt-0.5">{p.authors}</p>
                    )}
                    {p.abstract && (
                      <p className="text-sm text-gray-600 mt-2 line-clamp-2">{p.abstract}</p>
                    )}
                    {p.keywords && p.keywords.length > 0 && (
                      <div className="flex flex-wrap gap-1.5 mt-2">
                        {p.keywords.slice(0, 6).map((kw, i) => (
                          <span key={i} className="px-2 py-0.5 bg-gray-100 text-gray-600 rounded text-xs">
                            {kw}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                  <div className="flex flex-col items-center gap-1 shrink-0">
                    <Link
                      href={`/papers/${p.id}`}
                      className="text-xs font-medium text-primary-600 hover:text-primary-700 px-2 py-1 rounded hover:bg-primary-50 transition-colors"
                    >
                      View
                    </Link>
                    {p.url && (
                      <a
                        href={p.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="p-1 text-gray-400 hover:text-primary-600 transition-colors"
                      >
                        <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                        </svg>
                      </a>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </>
      ) : (
        <Card>
          <p className="text-center text-gray-400 py-8">No papers found.</p>
        </Card>
      )}
    </div>
  );
}
