import { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import Card from "../components/ui/Card";
import MetricCard from "../components/dashboard/MetricCard";
import KeywordChart from "../components/charts/KeywordChart";
import SourceChart from "../components/charts/SourceChart";

const STATUS_COLORS = {
  pending: "bg-yellow-400", ingesting: "bg-blue-400",
  processing: "bg-indigo-400", analyzing: "bg-purple-400",
  summarizing: "bg-pink-400", completed: "bg-green-400",
  failed: "bg-red-400",
};

export default function Dashboard() {
  const [topic, setTopic] = useState("");
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [activeJob, setActiveJob] = useState(null);
  const [backends, setBackends] = useState({ active: "all", backends: [] });
  const [sentimentFilter, setSentimentFilter] = useState("");
  const [sortBy, setSortBy] = useState("date");
  const [modelTrained, setModelTrained] = useState(false);
  const [modelPapers, setModelPapers] = useState(0);
  const [modelLoading, setModelLoading] = useState(true);
  const [modelTraining, setModelTraining] = useState(false);
  const [modelResult, setModelResult] = useState("");
  const [featureImportance, setFeatureImportance] = useState(null);
  const [testQuery, setTestQuery] = useState("");
  const [testResult, setTestResult] = useState(null);

  const fetchModelStatus = async () => {
    try {
      const res = await fetch("/api/model/status");
      if (res.ok) {
        const data = await res.json();
        setModelTrained(data.trained);
        setModelPapers(data.papers_count);
      }
    } catch {}
    setModelLoading(false);
  };

  useEffect(() => {
    fetch("/api/search/backends")
      .then((r) => r.json())
      .then(setBackends)
      .catch(() => {});
    fetchModelStatus();
  }, []);

  const switchBackend = async (id) => {
    try {
      const res = await fetch(`/api/search/backends/${id}`, { method: "POST" });
      if (res.ok) setBackends(await res.json());
    } catch {}
  };

  const fetchJobs = useCallback(async () => {
    try {
      const params = new URLSearchParams();
      if (sentimentFilter) params.set("sentiment", sentimentFilter);
      if (sortBy) params.set("sort_by", sortBy);
      const res = await fetch(`/api/research/?${params}`);
      if (res.ok) setJobs(await res.json());
    } catch {}
  }, [sentimentFilter, sortBy]);

  useEffect(() => { fetchJobs(); }, [fetchJobs]);

  useEffect(() => {
    if (!activeJob) return;
    const interval = setInterval(async () => {
      try {
        const res = await fetch(`/api/research/${activeJob.id}`);
        if (res.ok) {
          const data = await res.json();
          setActiveJob(data);
          if (data.status === "completed" || data.status === "failed") {
            clearInterval(interval);
            fetchJobs();
            setActiveJob(null);
            setLoading(false);
          }
        }
      } catch { /* ignore */ }
    }, 1500);
    return () => clearInterval(interval);
  }, [activeJob?.id, fetchJobs]);

  const startResearch = async (e) => {
    e.preventDefault();
    if (!topic.trim() || loading) return;
    setLoading(true);
    setError("");
    try {
      const res = await fetch("/api/research/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ topic }),
      });
      if (!res.ok) {
        const text = await res.text();
        throw new Error(text || "Failed to start research");
      }
      const job = await res.json();
      setActiveJob(job);
      setTopic("");
    } catch (err) {
      setError(err.message);
      setLoading(false);
    }
  };

  const getStatusDot = (status) =>
    `w-2 h-2 rounded-full ${STATUS_COLORS[status] || "bg-gray-400"}`;

  const deleteJob = async (e, jobId) => {
    e.preventDefault();
    if (!confirm("Delete this research job?")) return;
    try {
      await fetch(`/api/research/${jobId}`, { method: "DELETE" });
      fetchJobs();
    } catch {}
  };

  const retryJob = async (e, jobId) => {
    e.preventDefault();
    try {
      const res = await fetch(`/api/research/${jobId}/retry`, { method: "POST" });
      if (res.ok) {
        const job = await res.json();
        setActiveJob(job);
      }
    } catch {}
  };

  const trainModel = async () => {
    setModelTraining(true);
    setModelResult("");
    try {
      const res = await fetch("/api/model/train", { method: "POST" });
      if (res.ok) {
        const data = await res.json();
        setModelResult(data.message || "Training complete");
        setModelTrained(true);
        setModelPapers(data.papers);
        setFeatureImportance(data.feature_importance);
      } else {
        const err = await res.text();
        setModelResult("Error: " + err);
      }
    } catch (err) {
      setModelResult("Error: " + err.message);
    }
    setModelTraining(false);
  };

  const explainPrediction = async () => {
    if (!testQuery.trim()) return;
    try {
      const res = await fetch("/api/model/explain", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: testQuery, title: testQuery, abstract: "" }),
      });
      if (res.ok) setTestResult(await res.json());
    } catch {}
  };

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Research Dashboard</h1>
        <p className="text-gray-500 mt-1">Submit research topics and explore AI-powered analysis</p>
      </div>

      <Card className="mb-8">
        <form onSubmit={startResearch} className="flex flex-col sm:flex-row gap-4">
          <div className="flex-1">
            <input
              type="text"
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              placeholder="e.g., reinforcement learning, computer vision, NLP..."
              className="input-field"
              disabled={loading}
            />
          </div>
          <button type="submit" className="btn-primary flex items-center gap-2 justify-center" disabled={loading}>
            {loading ? (
              <>
                <svg className="animate-spin w-4 h-4" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                Analyzing...
              </>
            ) : (
              <>
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
                Start Research
              </>
            )}
          </button>
        </form>
        {error && <p className="mt-3 text-sm text-red-600">{error}</p>}
      </Card>

      <Card className="mb-6">
        <div className="flex flex-col sm:flex-row items-start sm:items-center gap-3">
          <div className="flex items-center gap-2 text-sm text-gray-600 shrink-0">
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9" />
            </svg>
            Search Engine:
          </div>
          <div className="flex flex-wrap gap-2">
            {backends.backends.map((b) => (
              <button
                key={b.id}
                onClick={() => switchBackend(b.id)}
                disabled={loading}
                className={`px-3 py-1.5 text-xs font-medium rounded-lg border transition-colors ${
                  b.active
                    ? "bg-primary-600 text-white border-primary-600"
                    : "bg-white text-gray-600 border-gray-200 hover:border-primary-300 hover:text-primary-600"
                }`}
              >
                {b.name}
              </button>
            ))}
          </div>
          {backends.backends.length > 0 && (
            <p className="text-xs text-gray-400 sm:ml-auto">
              {backends.backends.find((b) => b.active)?.description || ""}
            </p>
          )}
        </div>
      </Card>

      <Card className="mb-6">
        <div className="flex flex-col sm:flex-row items-start sm:items-center gap-3">
          <div className="flex items-center gap-2 text-sm text-gray-600 shrink-0">
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            Sentiment:
          </div>
          <div className="flex flex-wrap gap-2">
            {["", "positive", "neutral", "negative"].map((s) => (
              <button
                key={s}
                onClick={() => setSentimentFilter(s)}
                className={`px-3 py-1.5 text-xs font-medium rounded-lg border transition-colors capitalize ${
                  sentimentFilter === s
                    ? s === "positive" ? "bg-green-600 text-white border-green-600"
                      : s === "negative" ? "bg-red-600 text-white border-red-600"
                      : s === "neutral" ? "bg-gray-600 text-white border-gray-600"
                      : "bg-primary-600 text-white border-primary-600"
                    : "bg-white text-gray-600 border-gray-200 hover:border-primary-300"
                }`}
              >
                {s || "All"}
              </button>
            ))}
          </div>
        </div>
      </Card>

      <Card className="mb-6">
        <div className="flex flex-col sm:flex-row items-start sm:items-center gap-3">
          <div className="flex items-center gap-2 text-sm text-gray-600 shrink-0">
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 4h13M3 8h9m-9 4h6m4 0l4-4m0 0l4 4m-4-4v12" />
            </svg>
            Sort:
          </div>
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
            className="input-field text-xs sm:w-36"
          >
            <option value="date">Newest</option>
            <option value="relevance">Avg Relevance</option>
            <option value="docs">Doc Count</option>
          </select>
        </div>
      </Card>

      {activeJob && activeJob.status !== "completed" && activeJob.status !== "failed" && (
        <Card className="mb-8">
          <div className="flex items-center gap-4">
            <svg className="animate-spin w-6 h-6 text-primary-600" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
            <div>
              <p className="font-medium text-gray-900">
                Researching: <span className="text-primary-600">{activeJob.topic}</span>
              </p>
              <p className="text-sm text-gray-500 mt-0.5">
                Status: <span className="font-medium">{activeJob.status}</span>
              </p>
            </div>
          </div>
          <div className="mt-4 w-full bg-gray-200 rounded-full h-2">
            <div
              className="bg-primary-600 h-2 rounded-full transition-all duration-500"
              style={{
                width: activeJob.status === "ingesting" ? "25%"
                     : activeJob.status === "processing" ? "50%"
                     : activeJob.status === "analyzing" ? "75%"
                     : activeJob.status === "summarizing" ? "90%"
                     : "0%",
              }}
            />
          </div>
        </Card>
      )}

      {activeJob && activeJob.status === "completed" && (
        <Card className="mb-8 border-green-200 bg-green-50">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-green-100 rounded-full flex items-center justify-center">
                <svg className="w-5 h-5 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              </div>
              <div>
                <p className="font-semibold text-gray-900">Research Complete</p>
                <p className="text-sm text-gray-500">
                  {activeJob.topic} &mdash; {activeJob.documents_count} documents in {activeJob.processing_time}s
                </p>
              </div>
            </div>
            <Link href={`/results/${activeJob.id}`} className="btn-primary text-sm">
              View Results
            </Link>
          </div>
        </Card>
      )}

      <div className="mb-6">
        <h2 className="text-xl font-semibold text-gray-900">Recent Research Jobs</h2>
      </div>

      {jobs.length === 0 ? (
        <Card>
          <div className="text-center py-12 text-gray-400">
            <svg className="w-12 h-12 mx-auto mb-3 opacity-50" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
            </svg>
            <p>No research jobs yet. Start by entering a topic above!</p>
          </div>
        </Card>
      ) : (
        <div className="space-y-3">
          {jobs.map((job) => (
            <div key={job.id} className="card hover:shadow-md transition-shadow">
              <div className="flex items-center justify-between">
                <Link href={`/results/${job.id}`} className="flex-1 min-w-0">
                  <div className="flex items-center gap-3">
                    <span className={getStatusDot(job.status)} />
                    <div>
                      <p className="font-medium text-gray-900">{job.topic}</p>
                      <p className="text-xs text-gray-400">
                        {job.created_at ? new Date(job.created_at).toLocaleString() : ""}
                        {job.documents_count > 0 && ` \u2022 ${job.documents_count} docs`}
                        {job.avg_relevance > 0 && ` \u2022 ${job.avg_relevance.toFixed(2)} rel`}
                        {job.processing_time > 0 && ` \u2022 ${job.processing_time}s`}
                      </p>
                      {job.sentiment_distribution && (
                        <div className="flex gap-2 mt-1.5">
                          {["positive", "neutral", "negative"].map((s) => {
                            const count = job.sentiment_distribution[s] || 0;
                            if (!count) return null;
                            return (
                              <span key={s} className={`text-xs font-medium px-1.5 py-0.5 rounded ${
                                s === "positive" ? "bg-green-100 text-green-700"
                                : s === "negative" ? "bg-red-100 text-red-700"
                                : "bg-gray-100 text-gray-600"
                              }`}>
                                {count} {s}
                              </span>
                            );
                          })}
                        </div>
                      )}
                    </div>
                  </div>
                </Link>
                <div className="flex items-center gap-2 shrink-0 ml-4">
                  <span className="status-badge capitalize bg-gray-100 text-gray-700 text-xs">
                    {job.status}
                  </span>
                  {(job.status === "completed" || job.status === "failed") && (
                    <button
                      onClick={(e) => retryJob(e, job.id)}
                      className="p-1.5 text-gray-400 hover:text-primary-600 transition-colors"
                      title="Retry"
                    >
                      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                      </svg>
                    </button>
                  )}
                  <button
                    onClick={(e) => deleteJob(e, job.id)}
                    className="p-1.5 text-gray-400 hover:text-red-600 transition-colors"
                    title="Delete"
                  >
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* ── Model Management ── */}
      <Card title="Relevance Model" subtitle="Trainable ML model for document relevance scoring" className="mb-8">
        {modelLoading ? (
          <p className="text-sm text-gray-400">Loading model status...</p>
        ) : (
          <>
            <div className="flex items-center justify-between mb-4">
              <div>
                <span className={`inline-block w-2 h-2 rounded-full mr-2 ${modelTrained ? "bg-green-400" : "bg-gray-300"}`} />
                <span className="text-sm font-medium text-gray-700">{modelTrained ? "Trained" : "Not trained"}</span>
                {modelTrained && (
                  <span className="text-xs text-gray-400 ml-3">on {modelPapers} papers</span>
                )}
              </div>
              <button
                onClick={trainModel}
                disabled={modelTraining}
                className={`px-4 py-1.5 text-sm font-medium rounded-lg transition-colors ${
                  modelTraining
                    ? "bg-gray-200 text-gray-400 cursor-not-allowed"
                    : "bg-indigo-600 text-white hover:bg-indigo-700"
                }`}
              >
                {modelTraining ? "Training..." : "Train Model"}
              </button>
            </div>

            {modelResult && (
              <div className="mb-4 p-3 bg-green-50 border border-green-200 rounded-lg text-sm text-green-700">
                {modelResult}
              </div>
            )}

            {featureImportance && Object.keys(featureImportance).length > 0 && (
              <div className="mb-4">
                <h4 className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-2">Feature Importance</h4>
                <div className="space-y-1">
                  {Object.entries(featureImportance)
                    .sort((a, b) => b[1] - a[1])
                    .slice(0, 6)
                    .map(([name, imp]) => (
                      <div key={name} className="flex items-center gap-2">
                        <span className="text-xs text-gray-600 w-32 truncate">{name}</span>
                        <div className="flex-1 bg-gray-100 rounded-full h-2">
                          <div className="bg-indigo-400 h-2 rounded-full" style={{ width: `${imp * 100}%` }} />
                        </div>
                        <span className="text-xs text-gray-400 w-12 text-right">{(imp * 100).toFixed(0)}%</span>
                      </div>
                    ))}
                </div>
              </div>
            )}

            {modelTrained && (
              <div className="border-t border-gray-100 pt-4">
                <h4 className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-2">Test Query</h4>
                <div className="flex gap-2 mb-2">
                  <input
                    type="text"
                    value={testQuery}
                    onChange={(e) => setTestQuery(e.target.value)}
                    placeholder="Enter a query..."
                    className="flex-1 border border-gray-300 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
                  />
                  <button
                    onClick={explainPrediction}
                    disabled={!testQuery.trim()}
                    className="px-4 py-1.5 text-sm font-medium bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors disabled:opacity-50"
                  >
                    Explain
                  </button>
                </div>
                {testResult && (
                  <div className="p-3 bg-gray-50 rounded-lg border border-gray-200 text-sm">
                    <p className="font-medium text-gray-900 mb-1">Score: <span className="text-indigo-600">{testResult.score}</span></p>
                    <div className="space-y-0.5">
                      {Object.entries(testResult.contributions || {}).map(([name, val]) => (
                        <p key={name} className="text-xs text-gray-500">{name}: {val}</p>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </>
        )}
      </Card>
    </div>
  );
}
