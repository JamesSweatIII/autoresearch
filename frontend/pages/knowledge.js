import { useState, useEffect } from "react";
import Link from "next/link";
import Card from "../components/ui/Card";

const colorPalette = [
  { bg: "bg-red-100", text: "text-red-700" },
  { bg: "bg-blue-100", text: "text-blue-700" },
  { bg: "bg-green-100", text: "text-green-700" },
  { bg: "bg-purple-100", text: "text-purple-700" },
  { bg: "bg-orange-100", text: "text-orange-700" },
  { bg: "bg-teal-100", text: "text-teal-700" },
  { bg: "bg-pink-100", text: "text-pink-700" },
  { bg: "bg-indigo-100", text: "text-indigo-700" },
  { bg: "bg-cyan-100", text: "text-cyan-700" },
  { bg: "bg-amber-100", text: "text-amber-700" },
  { bg: "bg-lime-100", text: "text-lime-700" },
  { bg: "bg-rose-100", text: "text-rose-700" },
];

function getSourceColor(source) {
  let hash = 0;
  for (let i = 0; i < source.length; i++) {
    hash = source.charCodeAt(i) + ((hash << 5) - hash);
  }
  return colorPalette[Math.abs(hash) % colorPalette.length];
}

function PaperCard({ p, showSave, onToggleSave, saving, onAddToGroup, groups, children }) {
  const [showGroupPicker, setShowGroupPicker] = useState(false);
  const [groupSearch, setGroupSearch] = useState("");
  const [newGroupName, setNewGroupName] = useState("");
  const [creating, setCreating] = useState(false);

  const paperGroupIds = new Set();
  if (p?.id) {
    groups.forEach(g => {
      if (g.paper_ids?.includes?.(p.id)) paperGroupIds.add(g.id);
    });
  }
  const filteredGroups = groups.filter(g =>
    !paperGroupIds.has(g.id) && g.name.toLowerCase().includes(groupSearch.toLowerCase())
  );

  async function handleCreateAndAdd() {
    if (!newGroupName.trim()) return;
    setCreating(true);
    try {
      const res = await fetch("/api/groups", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: newGroupName.trim() }),
      });
      if (res.ok) {
        const g = await res.json();
        await fetch(`/api/groups/${g.id}/papers`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ paper_id: p.id }),
        });
        if (onAddToGroup) onAddToGroup(g.id, p.id);
        setNewGroupName("");
        setGroupSearch("");
        setShowGroupPicker(false);
      }
    } catch {}
    setCreating(false);
  }

  return (
    <div className="card hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between gap-4">
        <Link href={`/papers/${p.id}`} className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className={`text-xs font-medium px-2 py-0.5 rounded ${getSourceColor(p.source || p.source_type).bg} ${getSourceColor(p.source || p.source_type).text}`}>
              {p.source || p.source_type}
            </span>
            <span className="text-xs text-gray-400">{p.year}</span>
          </div>
          <h3 className="font-semibold text-gray-900 truncate">{p.title}</h3>
          {p.authors && <p className="text-xs text-gray-500 mt-0.5">{p.authors}</p>}
          {p.abstract && <p className="text-sm text-gray-600 mt-2 line-clamp-2">{p.abstract}</p>}
          {p.keywords && p.keywords.length > 0 && (
            <div className="flex flex-wrap gap-1.5 mt-2">
              {p.keywords.slice(0, 6).map((kw, i) => (
                <span key={i} className="px-2 py-0.5 bg-gray-100 text-gray-600 rounded text-xs">{kw}</span>
              ))}
            </div>
          )}
        </Link>
        <div className="flex flex-col items-center gap-1 shrink-0 pt-1">
          <div className="relative">
            {showSave ? (
              <button
                onClick={(e) => { e.stopPropagation(); setShowGroupPicker(prev => !prev); }}
                disabled={saving[p.id]}
                className={`p-1.5 rounded transition-colors disabled:opacity-50 ${
                  p.saved ? 'text-yellow-500 hover:text-yellow-600' : 'text-gray-300 hover:text-yellow-400'
                }`}
              >
                <svg className="w-4 h-4" fill={p.saved ? "currentColor" : "none"} viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z" />
                </svg>
              </button>
            ) : (
              <button
                onClick={(e) => { e.stopPropagation(); onToggleSave(p); }}
                disabled={saving[p.id]}
                className={`p-1.5 rounded transition-colors disabled:opacity-50 ${
                  p.saved ? 'text-yellow-500 hover:text-yellow-600' : 'text-gray-300 hover:text-yellow-400'
                }`}
              >
                <svg className="w-4 h-4" fill={p.saved ? "currentColor" : "none"} viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z" />
                </svg>
              </button>
            )}
            {showGroupPicker && (
              <div className="absolute right-0 top-full mt-1 w-64 bg-white border border-gray-200 rounded-lg shadow-lg z-20 p-2" onClick={e => e.stopPropagation()}>
                <p className="text-xs font-medium text-gray-600 mb-1.5 px-1">Add to group</p>
                <input
                  type="text"
                  value={groupSearch}
                  onChange={e => { setGroupSearch(e.target.value); setNewGroupName(e.target.value); }}
                  placeholder="Search groups or create new..."
                  className="w-full text-xs px-2 py-1.5 border border-gray-200 rounded mb-1.5"
                  autoFocus
                />
                <div className="max-h-40 overflow-y-auto space-y-0.5">
                  {filteredGroups.length > 0 ? filteredGroups.map(g => {
                    return (
                      <button
                        key={g.id}
                        onClick={async () => {
                          await fetch(`/api/groups/${g.id}/papers`, {
                            method: "POST",
                            headers: { "Content-Type": "application/json" },
                            body: JSON.stringify({ paper_id: p.id }),
                          });
                          if (onAddToGroup) onAddToGroup(g.id, p.id);
                          setGroupSearch("");
                          setShowGroupPicker(false);
                        }}
                        className="w-full text-left text-xs px-2 py-1.5 rounded hover:bg-gray-100 flex items-center gap-2 text-gray-700"
                      >
                        <svg className="w-3 h-3 shrink-0 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                          <path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4" />
                        </svg>
                        {g.name}
                      </button>
                    );
                  }) : (
                    <p className="text-xs text-gray-400 px-2 py-2 text-center">No groups match &quot;{groupSearch}&quot;</p>
                  )}
                </div>
                {groupSearch && !filteredGroups.some(g => g.name.toLowerCase() === groupSearch.toLowerCase()) && (
                  <div className="border-t border-gray-100 mt-1.5 pt-1.5">
                    <button
                      onClick={handleCreateAndAdd}
                      disabled={creating || !newGroupName.trim()}
                      className="w-full text-xs px-2 py-1.5 bg-primary-600 text-white rounded hover:bg-primary-700 disabled:opacity-50 flex items-center justify-center gap-1.5"
                    >
                      <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4" />
                      </svg>
                      {creating ? "Creating..." : `Create "${newGroupName}" & add`}
                    </button>
                  </div>
                )}
              </div>
            )}
          </div>
          {p.url && (
            <a
              href={p.url}
              target="_blank"
              rel="noopener noreferrer"
              onClick={(e) => e.stopPropagation()}
              className="p-1 text-gray-400 hover:text-primary-600 transition-colors"
            >
              <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
              </svg>
            </a>
          )}
        </div>
      </div>
      {children}
    </div>
  );
}

export default function KnowledgeBase() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const SOURCE_OPTIONS = [
    { id: "semantic_scholar", label: "Semantic Scholar" },
    { id: "openalex", label: "OpenAlex" },
    { id: "arxiv", label: "arXiv" },
    { id: "crossref", label: "CrossRef" },
  ];
  const [search, setSearch] = useState("");
  const [sourceFilter, setSourceFilter] = useState([]);
  const [savedOnly, setSavedOnly] = useState(false);
  const [page, setPage] = useState(1);
  const [stats, setStats] = useState(null);
  const [saving, setSaving] = useState({});
  const [groups, setGroups] = useState([]);
  const [expandedGroup, setExpandedGroup] = useState(null);
  const [groupPapers, setGroupPapers] = useState({});
  const [loadingGroup, setLoadingGroup] = useState({});
  const [newGroupName, setNewGroupName] = useState("");
  const [creatingGroup, setCreatingGroup] = useState(false);
  const limit = 20;

  useEffect(() => {
    fetch("/api/stats")
      .then((r) => r.json())
      .then(setStats)
      .catch(() => {});
  }, []);

  useEffect(() => {
    if (savedOnly) {
      fetch("/api/groups")
        .then(r => r.json())
        .then(d => setGroups(d.groups || []))
        .catch(() => {});
    }
  }, [savedOnly]);

  useEffect(() => {
    setLoading(true);
    setPage(1);
  }, [search, sourceFilter, savedOnly]);

  useEffect(() => {
    if (savedOnly) return;
    setLoading(true);
    const params = new URLSearchParams();
    if (search) params.set("search", search);
    if (sourceFilter.length > 0) params.set("source", sourceFilter.join(","));
    params.set("limit", String(limit));
    params.set("offset", String((page - 1) * limit));
    fetch(`/api/papers?${params}`)
      .then((r) => r.json())
      .then(setData)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [search, sourceFilter, savedOnly, page]);

  const totalPages = data ? Math.ceil(data.total / limit) : 1;

  async function toggleSaved(p) {
    const newVal = !p.saved;
    setSaving(prev => ({ ...prev, [p.id]: true }));
    try {
      const res = await fetch(`/api/papers/${p.id}/save`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ saved: newVal }),
      });
      if (res.ok) {
        setData(prev => prev ? {
          ...prev,
          papers: prev.papers.map(pp => pp.id === p.id ? { ...pp, saved: newVal } : pp)
        } : prev);
      }
    } catch {}
    setSaving(prev => ({ ...prev, [p.id]: false }));
  }

  async function handleAddToGroup(groupId, paperId) {
    setGroups(prev => prev.map(g => {
      if (g.id !== groupId) return g;
      const ids = g.paper_ids || [];
      if (ids.includes(paperId)) return { ...g, paper_ids: ids.filter(id => id !== paperId), paper_count: g.paper_count - 1 };
      return { ...g, paper_ids: [...ids, paperId], paper_count: g.paper_count + 1 };
    }));
    if (expandedGroup === groupId && groupPapers[groupId]) {
      const inGroup = groupPapers[groupId].some(p => p.id === paperId);
      if (inGroup) {
        setGroupPapers(prev => ({ ...prev, [groupId]: prev[groupId].filter(p => p.id !== paperId) }));
      } else {
        const paper = data?.papers?.find(p => p.id === paperId);
        if (paper) {
          setGroupPapers(prev => ({ ...prev, [groupId]: [paper, ...prev[groupId]] }));
        }
      }
    }
  }

  function toggleGroup(groupId) {
    if (expandedGroup === groupId) {
      setExpandedGroup(null);
      return;
    }
    setExpandedGroup(groupId);
    if (!groupPapers[groupId]) {
      setLoadingGroup(prev => ({ ...prev, [groupId]: true }));
      fetch(`/api/groups/${groupId}`)
        .then(r => r.json())
        .then(d => setGroupPapers(prev => ({ ...prev, [groupId]: d.papers || [] })))
        .catch(() => {})
        .finally(() => setLoadingGroup(prev => ({ ...prev, [groupId]: false })));
    }
  }

  async function createGroup() {
    if (!newGroupName.trim()) return;
    setCreatingGroup(true);
    try {
      const res = await fetch("/api/groups", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: newGroupName.trim() }),
      });
      if (res.ok) {
        const g = await res.json();
        setGroups(prev => [{ ...g, paper_count: 0, paper_ids: [] }, ...prev]);
        setNewGroupName("");
      }
    } catch {}
    setCreatingGroup(false);
  }

  async function removeFromGroup(groupId, paperId) {
    try {
      await fetch(`/api/groups/${groupId}/papers/${paperId}`, { method: "DELETE" });
      setGroupPapers(prev => ({ ...prev, [groupId]: prev[groupId].filter(p => p.id !== paperId) }));
      setGroups(prev => prev.map(g => g.id === groupId ? { ...g, paper_count: g.paper_count - 1 } : g));
    } catch {}
  }

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Knowledge Base</h1>
        <p className="text-gray-500 mt-1">Browse and search research papers</p>
      </div>

      {stats && (
        <div className="mb-8">
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <Card className="sm:col-span-3 text-center py-6">
              <p className="text-5xl font-bold text-gray-900">{stats.total_papers}</p>
              <p className="text-sm text-gray-500 mt-1">Total Papers</p>
            </Card>
            <Card className="text-center py-4 flex flex-col justify-center">
              <p className="text-xl font-bold text-gray-400">{stats.total_jobs}</p>
              <p className="text-xs text-gray-400">Research Jobs</p>
            </Card>
          </div>
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
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-xs text-gray-500 font-medium">Sources:</span>
            {SOURCE_OPTIONS.map((s) => {
              const selected = sourceFilter.includes(s.id);
              const c = getSourceColor(s.id);
              return (
                <button
                  key={s.id}
                  onClick={() => {
                    setSourceFilter(prev =>
                      prev.includes(s.id) ? prev.filter(x => x !== s.id) : [...prev, s.id]
                    );
                  }}
                  className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium transition-all cursor-pointer ${
                    selected
                      ? `${c.bg} ${c.text} ring-2 ring-offset-1 ring-current`
                      : 'bg-gray-100 text-gray-500 hover:bg-gray-200'
                  }`}
                >
                  {s.label}
                </button>
              );
            })}
            <span className="w-px h-5 bg-gray-200 mx-1" />
            <button
              onClick={() => setSavedOnly(prev => !prev)}
              className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium transition-all cursor-pointer ${
                savedOnly
                  ? 'bg-yellow-100 text-yellow-700 ring-2 ring-offset-1 ring-yellow-400'
                  : 'bg-gray-100 text-gray-500 hover:bg-gray-200'
              }`}
            >
              <svg className="w-3.5 h-3.5" fill={savedOnly ? "currentColor" : "none"} viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z" />
              </svg>
              Saved
            </button>
          </div>
        </div>
      </Card>

      {savedOnly ? (
        <div>
          <div className="flex items-center gap-3 mb-4">
            <input
              type="text"
              value={newGroupName}
              onChange={e => setNewGroupName(e.target.value)}
              placeholder="New research group name..."
              className="input-field flex-1 max-w-xs"
            />
            <button
              onClick={createGroup}
              disabled={creatingGroup || !newGroupName.trim()}
              className="btn-primary text-sm disabled:opacity-50"
            >
              {creatingGroup ? "Creating..." : "Create Group"}
            </button>
          </div>
          {groups.length === 0 ? (
            <Card>
              <p className="text-center text-gray-400 py-8">No research groups yet. Create one above.</p>
            </Card>
          ) : (
            <div className="space-y-4">
              {groups.map(g => (
                <Card key={g.id}>
                  <button
                    onClick={() => toggleGroup(g.id)}
                    className="w-full text-left"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <h3 className="font-semibold text-gray-900">{g.name}</h3>
                          <span className="text-xs text-gray-400 bg-gray-100 px-2 py-0.5 rounded-full">{g.paper_count} papers</span>
                        </div>
                        {g.description && <p className="text-xs text-gray-500 mt-0.5">{g.description}</p>}
                      </div>
                      <svg className={`w-4 h-4 text-gray-400 transition-transform ${expandedGroup === g.id ? 'rotate-180' : ''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                      </svg>
                    </div>
                  </button>
                  {expandedGroup === g.id && (
                    <div className="mt-4 border-t border-gray-100 pt-4 space-y-3">
                      {loadingGroup[g.id] ? (
                        <div className="text-center py-4">
                          <svg className="animate-spin w-5 h-5 mx-auto text-primary-600" viewBox="0 0 24 24">
                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                          </svg>
                        </div>
                      ) : groupPapers[g.id]?.length > 0 ? (
                        groupPapers[g.id].map(p => (
                          <div key={p.id} className="flex items-start justify-between gap-3 p-3 rounded-lg border border-gray-100 hover:border-primary-100">
                            <Link href={`/papers/${p.id}`} className="flex-1 min-w-0">
                              <div className="flex items-center gap-2 mb-0.5">
                                <span className={`text-xs font-medium px-1.5 py-0.5 rounded ${getSourceColor(p.source || p.source_type).bg} ${getSourceColor(p.source || p.source_type).text}`}>
                                  {p.source || p.source_type}
                                </span>
                                <span className="text-xs text-gray-400">{p.year}</span>
                              </div>
                              <h4 className="font-medium text-gray-900 truncate">{p.title}</h4>
                              {p.authors && <p className="text-xs text-gray-500">{p.authors}</p>}
                            </Link>
                            <button
                              onClick={() => removeFromGroup(g.id, p.id)}
                              className="shrink-0 p-1 text-gray-300 hover:text-red-500 transition-colors"
                            >
                              <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                                <path strokeLinecap="round" strokeLinejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                              </svg>
                            </button>
                          </div>
                        ))
                      ) : (
                        <p className="text-center text-gray-400 py-4 text-sm">No papers in this group.</p>
                      )}
                    </div>
                  )}
                </Card>
              ))}
            </div>
          )}
        </div>
      ) : loading ? (
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
                <span className="text-gray-600">Page {page} of {totalPages}</span>
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
              <PaperCard
                key={p.id}
                p={p}
                showSave={true}
                onToggleSave={toggleSaved}
                saving={saving}
                onAddToGroup={handleAddToGroup}
                groups={groups}
              />
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
