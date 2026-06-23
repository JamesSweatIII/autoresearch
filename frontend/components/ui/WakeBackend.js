import { useState, useEffect, useRef } from "react";

const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL || "https://autoresearch-api.onrender.com";

let awake = false;

export default function WakeBackend({ children }) {
  const [waking, setWaking] = useState(!awake);
  const mounted = useRef(true);

  useEffect(() => {
    if (awake) return;

    let stopped = false;
    let attempts = 0;

    const ping = async () => {
      while (!stopped && !awake) {
        attempts++;
        try {
          const res = await fetch(`${BACKEND_URL}/health`, { mode: "cors" });
          if (res.ok) {
            awake = true;
            if (mounted.current) setWaking(false);
            return;
          }
        } catch {}
        await new Promise((r) => setTimeout(r, 2500));
      }
    };

    ping();

    return () => {
      stopped = true;
    };
  }, []);

  useEffect(() => {
    return () => {
      mounted.current = false;
    };
  }, []);

  if (!waking) return children;

  return (
    <div className="fixed inset-0 z-50 flex flex-col items-center justify-center bg-gradient-to-br from-primary-900 via-primary-800 to-indigo-900">
      <div className="w-16 h-16 bg-white/10 backdrop-blur-sm rounded-2xl flex items-center justify-center mb-6">
        <svg className="w-8 h-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
        </svg>
      </div>
      <h1 className="text-2xl font-bold text-white mb-2">AutoResearch</h1>
      <p className="text-primary-200 text-sm mb-8">Waking up the research engine...</p>
      <div className="flex gap-1.5">
        <span className="w-2.5 h-2.5 bg-white rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
        <span className="w-2.5 h-2.5 bg-white rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
        <span className="w-2.5 h-2.5 bg-white rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
      </div>
    </div>
  );
}
