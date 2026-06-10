import { useState, useEffect } from "react";
import Card from "../components/ui/Card";

export default function Dashboard() {
  const SOURCE_OPTIONS = [
    { id: "semantic_scholar", label: "Semantic Scholar" },
    { id: "openalex", label: "OpenAlex" },
    { id: "arxiv", label: "arXiv" },
    { id: "crossref", label: "CrossRef" },
    { id: "local", label: "Local Database" },
  ];
  const [arTopic, setArTopic] = useState("");
  const [arSources, setArSources] = useState(SOURCE_OPTIONS.filter(s => s.id !== "local").map(s => s.id));
  const [arLoading, setArLoading] = useState(false);
  const [arError, setArError] = useState("");
  const [arResults, setArResults] = useState([]);
  const [arExpanded, setArExpanded] = useState({});
  const [arSaving, setArSaving] = useState({});

  const [poolRunning, setPoolRunning] = useState(false);
  const [poolResult, setPoolResult] = useState(null);
  const [poolProgress, setPoolProgress] = useState(0);
  const [poolTotal, setPoolTotal] = useState(0);
  const [poolCurrent, setPoolCurrent] = useState("");
  const [poolContext, setPoolContext] = useState("");
  const [groups, setGroups] = useState([]);
  const [deletingGroup, setDeletingGroup] = useState(null);

  const fetchGroups = async () => {
    try {
      const res = await fetch("/api/groups");
      if (res.ok) {
        const d = await res.json();
        setGroups(d.groups || []);
      }
    } catch {}
  };

  useEffect(() => { fetchGroups(); }, []);

  const deleteGroup = async (id) => {
    if (!confirm("Delete this research group and its papers?")) return;
    setDeletingGroup(id);
    try {
      await fetch(`/api/groups/${id}`, { method: "DELETE" });
      setGroups(prev => prev.filter(g => g.id !== id));
    } catch {}
    setDeletingGroup(null);
  };

  const searchArticles = async (e) => {
    e.preventDefault();
    if (!arTopic.trim()) return;
    setArLoading(true); setArError(""); setArResults([]); setArExpanded({});
    try {
      const body = { topic: arTopic, sources: arSources };
      const res = await fetch("/api/articles/search", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      if (res.ok) {
        const data = await res.json();
        setArResults(data.articles || []);
      } else {
        setArError((await res.text()) || "Search failed");
      }
    } catch (err) {
      setArError(err.message);
    }
    setArLoading(false);
  };

  const saveArticle = async (article) => {
    setArSaving(prev => ({ ...prev, [article.id]: true }));
    try {
      const res = await fetch("/api/articles/save", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          title: article.title,
          authors: article.authors || [],
          year: article.year,
          abstract: article.abstract,
          source: article.source,
          url: article.url,
          doi: article.doi,
        }),
      });
      if (res.ok) {
        const data = await res.json();
        alert(`Saved! Paper ID: ${data.id}`);
      } else {
        const err = await res.text();
        alert("Failed: " + err);
      }
    } catch (err) {
      alert("Error: " + err.message);
    }
    setArSaving(prev => ({ ...prev, [article.id]: false }));
  };

  const runPooler = async () => {
    setPoolRunning(true);
    setPoolResult(null);
    setPoolProgress(0);
    setPoolTotal(0);
    setPoolCurrent("");
    try {
      const res = await fetch("/api/pooler/pool", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ topic_fraction: 0.5, context: poolContext }),
      });
      if (!res.ok) {
        alert("Pooler error: " + (await res.text()));
        setPoolRunning(false);
      }
    } catch (err) {
      alert("Error: " + err.message);
      setPoolRunning(false);
    }
  };

  const pollPooler = async () => {
    if (!poolRunning) return;
    try {
      const res = await fetch("/api/pooler/status");
      if (res.ok) {
        const d = await res.json();
        setPoolProgress(d.progress);
        setPoolTotal(d.total_topics);
        setPoolCurrent(d.current_topic);
        if (d.status === "complete" && d.result) {
          setPoolResult(d.result);
          setPoolRunning(false);
        } else if (d.status === "error") {
          alert("Pooler error: " + (d.error || "Unknown error"));
          setPoolRunning(false);
        }
      }
    } catch {}
  };

  useEffect(() => {
    if (!poolRunning) return;
    const interval = setInterval(pollPooler, 2000);
    return () => clearInterval(interval);
  }, [poolRunning]);

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">AutoResearch</h1>
        <p className="text-gray-500 mt-1">Search articles and build your research dataset</p>
      </div>

      <Card title="Article Retrieval" subtitle="Search a source by topic — results ranked by semantic similarity" className="mb-8">
        <form onSubmit={searchArticles}>
          <div className="flex gap-2 mb-2">
            <input
              type="text"
              value={arTopic}
              onChange={(e) => setArTopic(e.target.value)}
              placeholder="e.g., reinforcement learning for robotics"
              className="flex-1 input-field"
              disabled={arLoading}
            />
            <button type="submit" disabled={arLoading || !arTopic.trim()} className="btn-primary flex items-center gap-2">
              {arLoading ? (
                <><svg className="animate-spin w-4 h-4" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" /><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" /></svg>Searching...</>
              ) : "Search"}
            </button>
          </div>

          <div className="flex flex-wrap items-center gap-3 mb-2">
            <span className="text-xs text-gray-500 font-medium">Sources:</span>
            {SOURCE_OPTIONS.map(s => (
              <label key={s.id} className="flex items-center gap-1.5 cursor-pointer select-none">
                <input
                  type="checkbox"
                  checked={arSources.includes(s.id)}
                  onChange={(e) => {
                    if (e.target.checked) {
                      setArSources(prev => [...prev, s.id]);
                    } else {
                      setArSources(prev => prev.filter(id => id !== s.id));
                    }
                  }}
                  className="w-3.5 h-3.5 rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                />
                <span className="text-xs text-gray-600">{s.label}</span>
              </label>
            ))}
          </div>
        </form>

        {arError && <p className="text-sm text-red-600 mb-3">{arError}</p>}

        {arLoading && (
          <div className="flex items-center gap-2 text-sm text-gray-500 mb-3">
            <svg className="animate-spin w-4 h-4" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" /><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" /></svg>
            Searching {arSources.length} source{arSources.length !== 1 ? "s" : ""}: {arSources.map(id => SOURCE_OPTIONS.find(s => s.id === id)?.label).join(", ")}...
          </div>
        )}

        {arResults.length > 0 && (
          <div>
            <p className="text-xs text-gray-400 mb-3">{arResults.length} results found — showing top 20 by relevance</p>
            <div className="max-h-96 overflow-y-auto overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-200">
                    <th className="text-left py-2 pr-2 font-medium text-gray-500 text-xs uppercase tracking-wider w-8">#</th>
                    <th className="text-left py-2 px-2 font-medium text-gray-500 text-xs uppercase tracking-wider">Title / Authors</th>
                    <th className="text-left py-2 px-2 font-medium text-gray-500 text-xs uppercase tracking-wider w-20">Source</th>
                    <th className="text-center py-2 px-2 font-medium text-gray-500 text-xs uppercase tracking-wider w-16">Score</th>
                    <th className="text-center py-2 pl-2 font-medium text-gray-500 text-xs uppercase tracking-wider w-16">Save</th>
                  </tr>
                </thead>
                <tbody>
                  {arResults.slice(0, 20).map((a, i) => {
                    const isExpanded = arExpanded[a.id];
                    const isSaving = arSaving[a.id];
                    const hasLongAbstract = a.abstract && a.abstract.length > 200;
                    return (
                      <tr key={a.id || i} className="border-b border-gray-100 hover:bg-gray-50 transition-colors">
                        <td className="py-3 pr-2 align-top text-xs text-gray-400">{i + 1}</td>
                        <td className="py-3 px-2">
                          <div>
                            <button onClick={() => toggleExpand(a.id, arExpanded, setArExpanded)} className="text-sm font-medium text-primary-700 hover:text-primary-800 text-left">
                              {a.title}
                            </button>
                            <p className="text-xs text-gray-400 mt-0.5">
                              {a.authors?.slice(0, 3).join(", ")}{a.authors?.length > 3 ? " et al." : ""}
                              {a.year && ` · ${a.year}`}
                              {a.citationCount != null && ` · ${a.citationCount} cites`}
                            </p>
                            {isExpanded && a.abstract && (
                              <p className="text-xs text-gray-500 mt-1">{a.abstract}</p>
                            )}
                            {!isExpanded && hasLongAbstract && (
                              <button onClick={() => toggleExpand(a.id, arExpanded, setArExpanded)} className="text-xs text-primary-500 hover:text-primary-700 mt-0.5">
                                Show abstract
                              </button>
                            )}
                          </div>
                        </td>
                        <td className="py-3 px-2 align-top">
                          <span className="inline-block text-xs px-1.5 py-0.5 rounded bg-gray-100 text-gray-600 capitalize whitespace-nowrap">{a.source?.replace("_", " ")}</span>
                        </td>
                        <td className="py-3 px-2 align-top text-center">
                          {a.relevanceScore != null && (
                            <span className={`text-xs font-semibold ${a.relevanceScore >= 0.7 ? 'text-green-600' : a.relevanceScore >= 0.4 ? 'text-yellow-600' : 'text-gray-400'}`}>
                              {a.relevanceScore.toFixed(2)}
                            </span>
                          )}
                        </td>
                        <td className="py-3 pl-2 align-top text-center">
                          <button onClick={() => saveArticle(a)} disabled={isSaving} className={`px-2 py-0.5 text-xs font-medium rounded transition-colors ${isSaving ? "bg-gray-200 text-gray-400 cursor-not-allowed" : "bg-white border border-gray-300 text-gray-600 hover:bg-gray-100"}`}>
                            {isSaving ? "..." : "+ Save"}
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </Card>

      <Card title="Article Pooler" subtitle="Automatically fetch articles from OpenAlex across 25 research topics to build your training dataset" className="mb-8">
        <div className="mb-3">
          <input
            type="text"
            value={poolContext}
            onChange={(e) => setPoolContext(e.target.value)}
            placeholder="Optional context to refine searches (e.g., 'chemistry' or 'biomedical')"
            className="input-field text-sm"
            disabled={poolRunning}
          />
        </div>
        <div className="flex items-center gap-3 mb-3">
          <button
            onClick={runPooler}
            disabled={poolRunning}
            className={`px-4 py-1.5 text-sm font-medium rounded-lg transition-colors ${poolRunning ? "bg-gray-200 text-gray-400 cursor-not-allowed" : "bg-green-600 text-white hover:bg-green-700"}`}
          >
            {poolRunning ? "Pooling..." : "Pool Articles"}
          </button>
          <span className="text-xs text-gray-400">Searches 25 broad topics, 50 results each, deduplicates against existing DB</span>
        </div>
        {poolRunning && poolTotal > 0 && (
          <div className="mb-3">
            <div className="flex items-center gap-2 text-sm text-gray-600 mb-1">
              <svg className="animate-spin w-4 h-4" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" /><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" /></svg>
              <span>Searching {poolProgress}/{poolTotal}: {poolCurrent}</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div className="bg-green-500 h-2 rounded-full transition-all duration-500" style={{ width: `${(poolProgress / poolTotal) * 100}%` }} />
            </div>
          </div>
        )}
        {poolResult && (
          <div className="p-3 bg-green-50 rounded-lg border border-green-200 text-sm">
            <p className="font-medium text-green-800">Pooled {poolResult.new_articles} new articles</p>
            <p className="text-xs text-green-600 mt-0.5">{poolResult.duplicates_skipped} duplicates skipped across {poolResult.topics_searched} topics</p>
          </div>
        )}
      </Card>

      <Card title="Research Groups" subtitle="Manage your saved paper groups" className="mb-8">
        {groups.length === 0 ? (
          <p className="text-sm text-gray-400">No research groups yet.</p>
        ) : (
          <div className="space-y-2">
            {groups.map(g => (
              <div key={g.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg border border-gray-100">
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-medium text-gray-900">{g.name}</p>
                  <p className="text-xs text-gray-400">{g.paper_count} papers</p>
                </div>
                <button
                  onClick={() => deleteGroup(g.id)}
                  disabled={deletingGroup === g.id}
                  className="ml-3 shrink-0 px-2.5 py-1 text-xs font-medium text-red-600 bg-white border border-red-200 rounded-lg hover:bg-red-50 disabled:opacity-50"
                >
                  {deletingGroup === g.id ? "..." : "Delete"}
                </button>
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  );
}

function toggleExpand(id, arExpanded, setArExpanded) {
  setArExpanded(prev => ({ ...prev, [id]: !prev[id] }));
}
