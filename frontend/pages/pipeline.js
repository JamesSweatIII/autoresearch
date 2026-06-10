import Card from "../components/ui/Card";

const PIPELINE_STAGES = [
  {
    name: "Data Ingestion",
    icon: "📥",
    description: "Research documents are loaded from sample_documents.json.bak, a curated collection of 50 influential AI/ML papers. The ingestion module reads and validates document structure before passing to the processing stage.",
    tech: "JSON, Python, FastAPI",
    color: "bg-blue-50 border-blue-200",
    iconBg: "bg-blue-100 text-blue-700",
  },
  {
    name: "Document Filtering",
    icon: "🔍",
    description: "Documents are filtered by relevance to the user's query topic. A scoring algorithm counts term frequency overlap between query terms and document text. Documents scoring zero are excluded.",
    tech: "Python, scikit-learn, TF-IDF scoring",
    color: "bg-indigo-50 border-indigo-200",
    iconBg: "bg-indigo-100 text-indigo-700",
  },
  {
    name: "PySpark Processing",
    icon: "⚡",
    description: "If PySpark is available, documents are loaded into a Spark DataFrame for distributed processing. This enables scaling to millions of documents across a cluster. A local fallback is used when Spark is unavailable.",
    tech: "PySpark, DataFrame API, UDFs",
    color: "bg-orange-50 border-orange-200",
    iconBg: "bg-orange-100 text-orange-700",
  },
  {
    name: "NLP Analysis",
    icon: "🧠",
    description: "Natural language processing extracts keywords, classifies sentiment (positive/neutral/negative), and computes relevance scores. The keyword extractor filters stop words and counts term frequency.",
    tech: "NLTK, regex, custom NLP pipeline",
    color: "bg-purple-50 border-purple-200",
    iconBg: "bg-purple-100 text-purple-700",
  },
  {
    name: "Theme Detection",
    icon: "🎯",
    description: "Topic modeling detects thematic clusters from extracted keywords. The system categorizes documents into pre-defined themes (Deep Learning, NLP, Computer Vision, etc.) based on keyword overlap.",
    tech: "Keyword clustering, heuristic matching",
    color: "bg-pink-50 border-pink-200",
    iconBg: "bg-pink-100 text-pink-700",
  },
  {
    name: "Summarization & Reporting",
    icon: "📊",
    description: "An executive summary is generated including document count, date range, key themes, and average relevance. Research gaps are identified from a curated list. Results are stored in SQLite and returned via API.",
    tech: "SQLAlchemy, SQLite, FastAPI",
    color: "bg-green-50 border-green-200",
    iconBg: "bg-green-100 text-green-700",
  },
];

const TECH_STACK = [
  { name: "FastAPI", desc: "High-performance Python API framework", category: "Backend" },
  { name: "PySpark", desc: "Distributed data processing engine", category: "Big Data" },
  { name: "SQLite / SQLAlchemy", desc: "Relational database with ORM", category: "Database" },
  { name: "Next.js 14", desc: "React framework with SSR and API routes", category: "Frontend" },
  { name: "Tailwind CSS", desc: "Utility-first CSS framework", category: "Frontend" },
  { name: "Recharts", desc: "Composable charting library for React", category: "Frontend" },
  { name: "NLTK", desc: "Natural Language Toolkit for Python", category: "NLP" },
  { name: "Threading", desc: "Async job processing via Python threads", category: "Infrastructure" },
];

export default function Pipeline() {
  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <div className="mb-10">
        <h1 className="text-3xl font-bold text-gray-900">Pipeline Architecture</h1>
        <p className="text-gray-500 mt-2 max-w-2xl">
          AutoResearch processes research documents through a six-stage pipeline that
          combines big data processing with NLP analysis.
        </p>
      </div>

      <div className="relative mb-16">
        <div className="hidden lg:block absolute left-1/2 top-0 bottom-0 w-0.5 bg-gray-200 -translate-x-1/2" />

        <div className="space-y-8 lg:space-y-12">
          {PIPELINE_STAGES.map((stage, i) => (
            <div key={stage.name} className={`relative flex flex-col lg:flex-row items-center gap-6 lg:gap-8 ${
              i % 2 === 0 ? "lg:flex-row" : "lg:flex-row-reverse"
            }`}>
              <div className={`flex-1 ${i % 2 === 0 ? "lg:text-right" : ""}`}>
                <div className={`p-6 rounded-xl border ${stage.color}`}>
                  <div className={`inline-flex items-center justify-center w-10 h-10 rounded-lg ${stage.iconBg} text-lg mb-3`}>
                    {stage.icon}
                  </div>
                  <span className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Stage {i + 1}</span>
                  <h3 className="text-lg font-bold text-gray-900 mt-1">{stage.name}</h3>
                  <p className="text-sm text-gray-600 mt-2 leading-relaxed">{stage.description}</p>
                  <div className="mt-3 flex flex-wrap gap-1.5">
                    {stage.tech.split(", ").map((t) => (
                      <span key={t} className="px-2 py-0.5 bg-white rounded text-xs font-medium text-gray-500 border border-gray-200">
                        {t}
                      </span>
                    ))}
                  </div>
                </div>
              </div>

              <div className="hidden lg:flex items-center justify-center w-12 h-12 rounded-full bg-primary-600 text-white font-bold text-sm z-10 shadow-lg shrink-0">
                {i + 1}
              </div>

              <div className="flex-1 hidden lg:block" />
            </div>
          ))}
        </div>
      </div>

      <h2 className="text-2xl font-bold text-gray-900 mb-6">Technology Stack</h2>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-10">
        {TECH_STACK.map((tech) => (
          <Card key={tech.name}>
            <p className="text-xs font-semibold text-primary-600 uppercase tracking-wider">{tech.category}</p>
            <h3 className="text-lg font-bold text-gray-900 mt-1">{tech.name}</h3>
            <p className="text-sm text-gray-500 mt-1">{tech.desc}</p>
          </Card>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card title="Data Flow" className="lg:col-span-2">
          <div className="text-sm text-gray-600 leading-relaxed space-y-3">
            <p><strong className="text-gray-900">1.</strong> User submits a research topic via the Dashboard form.</p>
            <p><strong className="text-gray-900">2.</strong> FastAPI creates a <code>ResearchJob</code> in SQLite and spawns a background thread.</p>
            <p><strong className="text-gray-900">3.</strong> The pipeline reads 50 sample documents from <code>sample_documents.json.bak</code>.</p>
            <p><strong className="text-gray-900">4.</strong> Documents are filtered by relevance to the topic using keyword overlap scoring.</p>
            <p><strong className="text-gray-900">5.</strong> If PySpark is installed, documents are loaded into a Spark DataFrame for distributed processing. Otherwise, a local Python fallback is used.</p>
            <p><strong className="text-gray-900">6.</strong> NLP extracts keywords, computes TF-based frequency, classifies sentiment, and computes relevance scores.</p>
            <p><strong className="text-gray-900">7.</strong> Theme detection clusters keywords into topic categories. Research gaps are identified.</p>
            <p><strong className="text-gray-900">8.</strong> An executive summary is generated. All results are stored in SQLite.</p>
            <p><strong className="text-gray-900">9.</strong> The frontend polls the API until the job completes, then displays results.</p>
          </div>
        </Card>
        <Card title="Scalability Notes" className="lg:col-span-1">
          <ul className="space-y-3 text-sm text-gray-600">
            <li className="flex items-start gap-2">
              <span className="text-primary-500 mt-0.5">&#9632;</span>
              <span><strong className="text-gray-900">PySpark integration</strong> enables processing of millions of documents across a cluster.</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-primary-500 mt-0.5">&#9632;</span>
              <span><strong className="text-gray-900">SQLite</strong> is suitable for single-server deployments. Swap to PostgreSQL for production.</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-primary-500 mt-0.5">&#9632;</span>
              <span><strong className="text-gray-900">Background threading</strong> keeps the API responsive during long-running analysis jobs.</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-primary-500 mt-0.5">&#9632;</span>
              <span><strong className="text-gray-900">Recharts</strong> renders charts client-side, reducing server load.</span>
            </li>
          </ul>
        </Card>
      </div>
    </div>
  );
}
