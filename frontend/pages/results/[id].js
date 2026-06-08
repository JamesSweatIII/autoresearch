import { useRouter } from "next/router";
import { useEffect, useState } from "react";
import Link from "next/link";
import Card from "../../components/ui/Card";
import MetricCard from "../../components/dashboard/MetricCard";
import KeywordChart from "../../components/charts/KeywordChart";
import SourceChart from "../../components/charts/SourceChart";
import SentimentChart from "../../components/charts/SentimentChart";

export default function Results() {
  const router = useRouter();
  const { id } = router.query;
  const [job, setJob] = useState(null);
  const [docs, setDocs] = useState([]);
  const [allDocs, setAllDocs] = useState([]);
  const [sentimentFilter, setSentimentFilter] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!id) return;
    let cancelled = false;

    const fetchAll = async () => {
      try {
        const [jobRes, docsRes] = await Promise.all([
          fetch(`/api/research/${id}`),
          fetch(`/api/research/${id}/documents`),
        ]);
        if (cancelled) return;
        if (jobRes.ok) setJob(await jobRes.json());
        if (docsRes.ok) {
          const d = await docsRes.json();
          setAllDocs(d);
          setDocs(d);
        }
      } catch { /* ignore */ }
      if (!cancelled) setLoading(false);
    };
    fetchAll();
    return () => { cancelled = true; };
  }, [id]);

  useEffect(() => {
    if (!sentimentFilter) {
      setDocs(allDocs);
    } else {
      setDocs(allDocs.filter((d) => d.sentiment === sentimentFilter));
    }
  }, [sentimentFilter, allDocs]);

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-16 text-center">
        <svg className="animate-spin w-8 h-8 mx-auto text-primary-600" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
        </svg>
        <p className="mt-3 text-gray-500">Loading results...</p>
      </div>
    );
  }

  if (!job) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-16 text-center">
        <p className="text-gray-500">Job not found.</p>
        <Link href="/dashboard" className="btn-primary mt-4 inline-block">Back to Dashboard</Link>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <div className="flex items-center justify-between mb-8">
        <div>
          <Link href="/dashboard" className="text-sm text-primary-600 hover:text-primary-700 mb-1 inline-block">
            &larr; Back to Dashboard
          </Link>
          <h1 className="text-3xl font-bold text-gray-900">{job.topic}</h1>
          <p className="text-gray-500 mt-1">
            {job.documents_count} documents analyzed in {job.processing_time}s
          </p>
        </div>
        <span className={`status-badge capitalize ${
          job.status === "completed" ? "bg-green-100 text-green-800" : "bg-gray-100 text-gray-800"
        }`}>
          {job.status}
        </span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <MetricCard
          label="Documents Analyzed"
          value={job.documents_count}
          color="primary"
          icon={<svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>}
        />
        <MetricCard
          label="Avg Relevance"
          value={job.avg_relevance?.toFixed(3) || "—"}
          color="blue"
          icon={<svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" /></svg>}
        />
        <MetricCard
          label="Top Source"
          value={job.top_source || "—"}
          color="purple"
          icon={<svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" /></svg>}
        />
        <MetricCard
          label="Processing Time"
          value={`${job.processing_time}s`}
          color="orange"
          icon={<svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>}
        />
      </div>

      {job.summary && (
        <Card title="Executive Summary" className="mb-8">
          <p className="text-gray-700 leading-relaxed">{job.summary}</p>
        </Card>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        <Card title="Top Keywords" subtitle="Most frequent terms across documents">
          <KeywordChart data={job.keyword_frequency || {}} />
        </Card>
        <Card title="Source Distribution" subtitle="Documents by venue">
          <SourceChart data={job.topic_distribution || {}} />
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        {(job.themes && job.themes.length > 0) && (
          <Card title="Identified Themes">
            <div className="flex flex-wrap gap-2">
              {job.themes.map((theme, i) => (
                <span key={i} className="px-3 py-1.5 bg-primary-50 text-primary-700 rounded-full text-sm font-medium">
                  {theme}
                </span>
              ))}
            </div>
          </Card>
        )}
        {(job.research_gaps && job.research_gaps.length > 0) && (
          <Card title="Research Gaps">
            <ul className="space-y-2">
              {job.research_gaps.map((gap, i) => (
                <li key={i} className="flex items-start gap-2 text-sm text-gray-700">
                  <span className="text-primary-500 mt-0.5">&#9632;</span>
                  {gap}
                </li>
              ))}
            </ul>
          </Card>
        )}
      </div>

      <Card title="Sentiment Analysis" className="mb-8">
        <SentimentChart data={docs} />
      </Card>

      {job.source_rankings && job.source_rankings.length > 0 && (
        <Card title="Source Rankings" subtitle="Venues ranked by average document relevance" className="mb-8">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="text-left py-3 px-2 font-medium text-gray-500">Source</th>
                  <th className="text-right py-3 px-2 font-medium text-gray-500">Documents</th>
                  <th className="text-right py-3 px-2 font-medium text-gray-500">Avg Relevance</th>
                  <th className="text-left py-3 px-2 font-medium text-gray-500">Sample Titles</th>
                </tr>
              </thead>
              <tbody>
                {job.source_rankings.map((src, i) => (
                  <tr key={i} className="border-b border-gray-100 hover:bg-gray-50">
                    <td className="py-3 px-2 font-medium text-gray-900">{src.source}</td>
                    <td className="py-3 px-2 text-right text-gray-600">{src.documents}</td>
                    <td className="py-3 px-2 text-right text-gray-600">{src.avg_relevance}</td>
                    <td className="py-3 px-2 text-gray-500 text-xs truncate max-w-xs">
                      {src.sample_titles?.join(", ") || "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      <Card title="Documents" subtitle={`${docs.length} documents ranked by relevance`}>
        <div className="flex flex-wrap gap-2 mb-4 pb-4 border-b border-gray-100">
          {["", "positive", "neutral", "negative"].map((s) => {
            const count = s ? allDocs.filter((d) => d.sentiment === s).length : allDocs.length;
            return (
              <button
                key={s}
                onClick={() => setSentimentFilter(s)}
                className={`px-3 py-1 text-xs font-medium rounded-lg border transition-colors capitalize ${
                  sentimentFilter === s
                    ? s === "positive" ? "bg-green-600 text-white border-green-600"
                      : s === "negative" ? "bg-red-600 text-white border-red-600"
                      : s === "neutral" ? "bg-gray-600 text-white border-gray-600"
                      : "bg-primary-600 text-white border-primary-600"
                    : "bg-white text-gray-600 border-gray-200 hover:border-primary-300"
                }`}
              >
                {s || "All"} ({count})
              </button>
            );
          })}
        </div>
        {docs.length === 0 ? (
          <p className="text-gray-400 text-center py-8">No documents available</p>
        ) : (
          <div className="space-y-4">
            {docs.map((doc) => (
              <div key={doc.id} className="p-4 rounded-lg border border-gray-100 hover:border-primary-200 hover:bg-primary-50/30 transition-colors">
                <div className="flex items-start justify-between gap-4">
                    <div className="flex-1 min-w-0">
                      <Link href={doc.paper_id ? `/papers/${doc.paper_id}` : "#"} className="hover:text-primary-600 transition-colors">
                        <h4 className="font-medium text-gray-900 truncate">{doc.title}</h4>
                      </Link>
                    <p className="text-xs text-gray-500 mt-1">
                      {doc.authors} &mdash; {doc.source} ({doc.year})
                    </p>
                    <p className="text-sm text-gray-600 mt-2 line-clamp-2">{doc.abstract}</p>
                    {doc.keywords && doc.keywords.length > 0 && (
                      <div className="flex flex-wrap gap-1.5 mt-2">
                        {doc.keywords.map((kw, i) => (
                          <span key={i} className="px-2 py-0.5 bg-gray-100 text-gray-600 rounded text-xs">
                            {kw}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                  <div className="flex flex-col items-end gap-1 shrink-0">
                    <span className={`text-xs font-medium px-2 py-0.5 rounded ${
                      doc.sentiment === "positive" ? "bg-green-100 text-green-700"
                      : doc.sentiment === "negative" ? "bg-red-100 text-red-700"
                      : "bg-gray-100 text-gray-600"
                    }`}>
                      {doc.sentiment}
                    </span>
                    <span className="text-xs text-gray-400">
                      Score: {doc.relevance_score?.toFixed(3)}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  );
}
