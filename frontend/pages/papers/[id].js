import { useRouter } from "next/router";
import { useEffect, useState } from "react";
import Link from "next/link";
import Card from "../../components/ui/Card";

export default function PaperDetail() {
  const router = useRouter();
  const { id } = router.query;
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (!id) return;
    setLoading(true);
    fetch(`/api/papers/${id}`)
      .then((r) => (r.ok ? r.json() : null))
      .then(setData)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [id]);

  async function toggleSaved() {
    if (!data?.paper) return;
    const newVal = !data.paper.saved;
    setSaving(true);
    try {
      const res = await fetch(`/api/papers/${id}/save`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ saved: newVal }),
      });
      if (res.ok) {
        setData(prev => prev ? { ...prev, paper: { ...prev.paper, saved: newVal } } : prev);
      }
    } catch {}
    setSaving(false);
  }

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-16 text-center">
        <svg className="animate-spin w-8 h-8 mx-auto text-primary-600" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
        </svg>
      </div>
    );
  }

  if (!data || !data.paper) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-16 text-center">
        <p className="text-gray-500">Paper not found.</p>
        <Link href="/knowledge" className="btn-primary mt-4 inline-block">Back to Knowledge Base</Link>
      </div>
    );
  }

  const { paper, similar_papers: similar } = data;

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <Link href="/knowledge" className="text-sm text-primary-600 hover:text-primary-700 mb-4 inline-block">
        &larr; Back to Knowledge Base
      </Link>

      <Card className="mb-6">
        <div className="flex items-start gap-3 mb-4">
          <span className={`text-xs font-medium px-2 py-0.5 rounded mt-0.5 ${
            paper.source_type === "web"
              ? "bg-blue-100 text-blue-700"
              : "bg-green-100 text-green-700"
          }`}>
            {paper.source_type === "web" ? "WEB" : "SAMPLE"}
          </span>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-bold text-gray-900">{paper.title}</h1>
              <button
                onClick={toggleSaved}
                disabled={saving}
                className={`shrink-0 p-2 rounded transition-colors ${
                  paper.saved
                    ? 'text-yellow-500 hover:text-yellow-600'
                    : 'text-gray-300 hover:text-yellow-400'
                } disabled:opacity-50`}
              >
                <svg className="w-5 h-5" fill={paper.saved ? "currentColor" : "none"} viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z" />
                </svg>
              </button>
            </div>
            <p className="text-sm text-gray-500 mt-2">
              {paper.authors || "Unknown authors"} &mdash; {paper.source || "Unknown source"} ({paper.year})
            </p>
          </div>
        </div>

        {paper.abstract && (
          <div className="mb-6">
            <h2 className="text-sm font-semibold text-gray-700 uppercase tracking-wider mb-2">Abstract</h2>
            <p className="text-gray-700 leading-relaxed">{paper.abstract}</p>
          </div>
        )}

        {paper.content && paper.content !== paper.abstract && (
          <div className="mb-6">
            <h2 className="text-sm font-semibold text-gray-700 uppercase tracking-wider mb-2">Full Content</h2>
            <p className="text-gray-700 leading-relaxed whitespace-pre-wrap text-sm">{paper.content}</p>
          </div>
        )}

        <div className="flex flex-wrap items-center gap-4 text-xs text-gray-500">
          {paper.keywords && paper.keywords.length > 0 && (
            <div className="flex flex-wrap gap-1.5 items-center">
              <span className="font-medium text-gray-600">Keywords:</span>
              {paper.keywords.map((kw, i) => (
                <span key={i} className="px-2 py-0.5 bg-gray-100 text-gray-600 rounded">{kw}</span>
              ))}
            </div>
          )}
          {paper.url && (
            <a
              href={paper.url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1 text-primary-600 hover:text-primary-700 font-medium"
            >
              <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
              </svg>
              View Original
            </a>
          )}
        </div>
      </Card>

      {similar && similar.length > 0 && (
        <Card title="Similar Papers" subtitle="Recommended based on TF-IDF text similarity">
          <div className="space-y-3">
            {similar.map((p) => (
              <Link key={p.id} href={`/papers/${p.id}`} className="block">
                <div className="p-3 rounded-lg border border-gray-100 hover:border-primary-200 hover:bg-primary-50/30 transition-colors">
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-0.5">
                        <span className={`text-xs font-medium px-1.5 py-0.5 rounded ${
                          p.source_type === "web" ? "bg-blue-100 text-blue-700" : "bg-green-100 text-green-700"
                        }`}>
                          {p.source_type === "web" ? "WEB" : "SAMPLE"}
                        </span>
                        <span className="text-xs text-gray-400">{p.source} ({p.year})</span>
                      </div>
                      <h4 className="font-medium text-gray-900 truncate">{p.title}</h4>
                      {p.authors && (
                        <p className="text-xs text-gray-500 mt-0.5">{p.authors}</p>
                      )}
                      {p.abstract && (
                        <p className="text-xs text-gray-500 mt-1.5 line-clamp-2">{p.abstract}</p>
                      )}
                    </div>
                    {p.similarity_score != null && (
                      <span className="shrink-0 text-xs font-medium text-primary-600 bg-primary-50 px-2 py-1 rounded">
                        {Math.round(p.similarity_score * 100)}%
                      </span>
                    )}
                  </div>
                </div>
              </Link>
            ))}
          </div>
        </Card>
      )}
    </div>
  );
}
