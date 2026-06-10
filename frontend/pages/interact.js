import { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import Card from "../components/ui/Card";

const GATE = 0.85;

export default function Interact() {
  const [status, setStatus] = useState(null);
  const [loadingStatus, setLoadingStatus] = useState(true);

  const [query, setQuery] = useState("");
  const [title, setTitle] = useState("");
  const [abstract, setAbstract] = useState("");
  const [result, setResult] = useState(null);
  const [predicting, setPredicting] = useState(false);
  const [error, setError] = useState("");

  const fetchStatus = useCallback(async () => {
    try {
      const res = await fetch("/api/autoresearch/status");
      if (res.ok) setStatus(await res.json());
    } catch {
      setStatus({ available: false, ready: false, error: "backend unreachable" });
    }
    setLoadingStatus(false);
  }, []);

  useEffect(() => {
    fetchStatus();
  }, [fetchStatus]);

  // While the model isn't ready yet, poll so the gate flips live as the
  // autoresearch agent drives accuracy past the threshold.
  useEffect(() => {
    if (status && status.ready) return;
    const id = setInterval(fetchStatus, 4000);
    return () => clearInterval(id);
  }, [status, fetchStatus]);

  const ready = !!(status && status.ready);
  const available = !!(status && status.available !== false);
  const acc = status && status.best_accuracy != null ? status.best_accuracy : null;
  const pct = acc != null ? Math.min(100, Math.round((acc / GATE) * 100)) : 0;
  const trainState = (status && status.training) || { status: "idle" };
  const isTraining = trainState.status === "training";

  const train = async () => {
    setError("");
    try {
      const res = await fetch("/api/autoresearch/train", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({}), // no job_id => train on the most recently gathered papers
      });
      const data = await res.json();
      if (!data.ok) throw new Error(data.error || "could not start training");
      fetchStatus(); // polling effect will track training -> ready/below_gate
    } catch (err) {
      setError(err.message || "training failed to start");
    }
  };

  const predict = async (e) => {
    e.preventDefault();
    if (!query.trim() || predicting) return;
    setPredicting(true);
    setError("");
    setResult(null);
    try {
      const res = await fetch("/api/autoresearch/predict", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query, title, abstract }),
      });
      const data = await res.json();
      if (data.error) throw new Error(data.error);
      setResult(data);
    } catch (err) {
      setError(err.message || "Prediction failed");
    }
    setPredicting(false);
  };

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Interact with the Model</h1>
        <p className="text-gray-500 mt-1">
          Query the relevance model trained by the autoresearch loop. Interaction
          unlocks only once held-out accuracy reaches the {Math.round(GATE * 100)}% gate.
        </p>
      </div>

      {/* ── Gate / status ── */}
      <Card className="mb-8">
        {loadingStatus ? (
          <p className="text-sm text-gray-400">Checking model status…</p>
        ) : !available ? (
          <div className="text-sm text-amber-700 bg-amber-50 border border-amber-200 rounded-lg p-3">
            Autoresearch model unavailable on the backend
            {status && status.error ? `: ${status.error}` : ""}. Train it first:
            <code className="block mt-1 text-xs">python autoresearch/build_dataset.py &amp;&amp; python autoresearch/train_relevance.py</code>
          </div>
        ) : (
          <div>
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <span className={`w-2.5 h-2.5 rounded-full ${
                  ready ? "bg-green-500" : isTraining ? "bg-yellow-400 animate-pulse" : "bg-gray-400"
                }`} />
                <span className="font-semibold text-gray-900">
                  {ready ? "Model ready"
                    : isTraining ? "Training on gathered papers…"
                    : trainState.status === "below_gate" ? "Below the 85% gate — not unlocked"
                    : acc != null ? "Not unlocked" : "No model trained yet"}
                </span>
              </div>
              <span className="text-sm text-gray-500">
                accuracy:{" "}
                <span className="font-semibold text-gray-900">
                  {acc != null ? `${(acc * 100).toFixed(1)}%` : "—"}
                </span>
                <span className="text-gray-400"> / gate {Math.round(GATE * 100)}%</span>
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2.5">
              <div
                className={`h-2.5 rounded-full transition-all duration-700 ${ready ? "bg-green-500" : "bg-yellow-400"}`}
                style={{ width: `${pct}%` }}
              />
            </div>

            <div className="mt-4 flex items-center gap-3">
              <button
                onClick={train}
                disabled={isTraining}
                className={`px-4 py-2 text-sm font-medium rounded-lg transition-colors ${
                  isTraining ? "bg-gray-200 text-gray-400 cursor-not-allowed"
                             : "bg-indigo-600 text-white hover:bg-indigo-700"
                }`}
              >
                {isTraining ? "Training…" : "Train relevance model on gathered papers"}
              </button>
              <span className="text-xs text-gray-400">
                Trains on the papers your latest search gathered (run a search on the{" "}
                <Link href="/dashboard" className="text-primary-600 hover:underline">dashboard</Link> first).
              </span>
            </div>

            {!ready && (
              <p className="text-xs text-gray-400 mt-3">
                Interaction unlocks automatically when held-out accuracy ≥ {Math.round(GATE * 100)}%.
                A single-topic search is harder to discriminate and may land below the gate (that's the
                gate doing its job); a diverse corpus clears it.
                {trainState.message ? ` — ${trainState.message}` : ""}
              </p>
            )}

            {error && (
              <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg">
                <p className="text-sm text-red-700">{error}</p>
                {error.includes("search for articles") && (
                  <a href="/dashboard" className="mt-1.5 inline-block text-sm font-medium text-primary-600 hover:text-primary-700 underline">
                    Go to Dashboard →
                  </a>
                )}
              </div>
            )}
          </div>
        )}
      </Card>

      {/* ── Interaction form (gated) ── */}
      <Card title="Relevance Query" subtitle="Score how relevant a document is to your topic — including text the model never saw in training.">
        <form onSubmit={predict} className="space-y-3">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Research topic / query (e.g., graph neural networks for chemistry)"
            className="input-field"
            disabled={!ready}
          />
          <input
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Document title"
            className="input-field"
            disabled={!ready}
          />
          <textarea
            value={abstract}
            onChange={(e) => setAbstract(e.target.value)}
            placeholder="Document abstract (optional)"
            rows={4}
            className="input-field"
            disabled={!ready}
          />
          <button type="submit" className="btn-primary" disabled={!ready || predicting}>
            {predicting ? "Scoring…" : ready ? "Score relevance" : `Locked until ${Math.round(GATE * 100)}% accuracy`}
          </button>
        </form>

          {result && (
          <div className="mt-5 p-4 rounded-lg border border-gray-200 bg-gray-50">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-500">Relevance score</span>
              <span className="text-2xl font-bold text-gray-900">{(result.score * 100).toFixed(1)}%</span>
            </div>
            <div className="mt-2 w-full bg-gray-200 rounded-full h-2">
              <div
                className={`h-2 rounded-full ${result.relevant ? "bg-green-500" : "bg-gray-400"}`}
                style={{ width: `${Math.round(result.score * 100)}%` }}
              />
            </div>
            <span
              className={`inline-block mt-3 px-2.5 py-1 rounded-full text-xs font-medium ${
                result.relevant ? "bg-green-100 text-green-700" : "bg-gray-200 text-gray-600"
              }`}
            >
              {result.relevant ? "Relevant" : "Not relevant"}
            </span>
          </div>
        )}
      </Card>
    </div>
  );
}
