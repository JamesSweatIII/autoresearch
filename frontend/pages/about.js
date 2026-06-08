import Card from "../components/ui/Card";

const FAQ = [
  {
    q: "What is AutoResearch?",
    a: "AutoResearch is an AI-powered research intelligence platform that automatically ingests, analyzes, and summarizes research documents. It combines PySpark for distributed data processing with NLP techniques for keyword extraction, sentiment analysis, theme detection, and summarization.",
  },
  {
    q: "How does document filtering work?",
    a: "Documents are scored by calculating term frequency overlap between the user's query and each document's title, abstract, and keywords. Documents with zero overlap are excluded. The remainder are sorted by relevance score.",
  },
  {
    q: "Does it require PySpark?",
    a: "No. AutoResearch detects PySpark at runtime. If PySpark is installed, documents are loaded into Spark DataFrames for distributed processing. If not, a local Python fallback processes documents in memory. This makes the platform accessible for development and small-scale analysis without a Spark cluster.",
  },
  {
    q: "What data source does the sample use?",
    a: "The included sample dataset contains 50 influential AI/ML research papers from top venues including NeurIPS, ICML, CVPR, Nature, and ACL. Papers span topics from deep learning and reinforcement learning to NLP, computer vision, and AI ethics.",
  },
  {
    q: "Can I add my own documents?",
    a: "Yes. The sample_documents.json file can be extended with additional documents following the same schema. Future versions will support PDF ingestion, API-based retrieval, and database connectors.",
  },
  {
    q: "How are keywords extracted?",
    a: "Keywords are extracted using term frequency analysis with stop-word filtering. The system tokenizes document text, removes common English stop words, counts remaining terms, and returns the top N most frequent terms. This is a TF-based approach that runs both as a PySpark UDF and as a local Python function.",
  },
  {
    q: "What is the sentiment analysis approach?",
    a: "Sentiment is classified using a lexicon-based approach. Document text is scanned for positive and negative keyword lists. If positive terms outnumber negative ones, the document is classified as 'positive'; the reverse yields 'negative'; otherwise it is 'neutral'.",
  },
];

export default function About() {
  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <div className="mb-10">
        <h1 className="text-3xl font-bold text-gray-900">About AutoResearch</h1>
        <p className="text-gray-500 mt-2">
          AI-Powered Research Intelligence Platform &mdash; architecture, usage, and FAQ
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-10">
        <Card className="text-center">
          <div className="text-3xl mb-2">📚</div>
          <p className="text-2xl font-bold text-gray-900">50</p>
          <p className="text-sm text-gray-500">Sample Documents</p>
        </Card>
        <Card className="text-center">
          <div className="text-3xl mb-2">🔧</div>
          <p className="text-2xl font-bold text-gray-900">6</p>
          <p className="text-sm text-gray-500">Pipeline Stages</p>
        </Card>
        <Card className="text-center">
          <div className="text-3xl mb-2">⚡</div>
          <p className="text-2xl font-bold text-gray-900">2</p>
          <p className="text-sm text-gray-500">Processing Modes</p>
        </Card>
      </div>

      <Card title="Quick Start" className="mb-8">
        <div className="prose prose-sm max-w-none text-gray-600">
          <div className="space-y-2">
            <p><strong className="text-gray-900">1. Install backend dependencies:</strong></p>
            <pre className="bg-gray-50 p-3 rounded-lg text-xs overflow-x-auto">pip install -r backend/requirements.txt</pre>
            <p><strong className="text-gray-900">2. Start the API server:</strong></p>
            <pre className="bg-gray-50 p-3 rounded-lg text-xs overflow-x-auto">cd backend && python main.py</pre>
            <p><strong className="text-gray-900">3. Install frontend dependencies:</strong></p>
            <pre className="bg-gray-50 p-3 rounded-lg text-xs overflow-x-auto">cd frontend && npm install</pre>
            <p><strong className="text-gray-900">4. Start the frontend dev server:</strong></p>
            <pre className="bg-gray-50 p-3 rounded-lg text-xs overflow-x-auto">cd frontend && npm run dev</pre>
            <p><strong className="text-gray-900">5. Open your browser:</strong></p>
            <pre className="bg-gray-50 p-3 rounded-lg text-xs overflow-x-auto">http://localhost:3000</pre>
          </div>
        </div>
      </Card>

      <Card title="API Endpoints" className="mb-8">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-200">
                <th className="text-left py-2 px-2 font-medium text-gray-500">Method</th>
                <th className="text-left py-2 px-2 font-medium text-gray-500">Path</th>
                <th className="text-left py-2 px-2 font-medium text-gray-500">Description</th>
              </tr>
            </thead>
            <tbody>
              <tr className="border-b border-gray-100"><td className="py-2 px-2 font-mono text-xs text-primary-600">GET</td><td className="py-2 px-2">/api/health</td><td className="py-2 px-2 text-gray-600">Health check</td></tr>
              <tr className="border-b border-gray-100"><td className="py-2 px-2 font-mono text-xs text-primary-600">GET</td><td className="py-2 px-2">/api/stats</td><td className="py-2 px-2 text-gray-600">Global dataset statistics</td></tr>
              <tr className="border-b border-gray-100"><td className="py-2 px-2 font-mono text-xs text-primary-600">GET</td><td className="py-2 px-2">/api/sources</td><td className="py-2 px-2 text-gray-600">List data sources</td></tr>
              <tr className="border-b border-gray-100"><td className="py-2 px-2 font-mono text-xs text-primary-600">POST</td><td className="py-2 px-2">/api/research/</td><td className="py-2 px-2 text-gray-600">Create research job</td></tr>
              <tr className="border-b border-gray-100"><td className="py-2 px-2 font-mono text-xs text-primary-600">GET</td><td className="py-2 px-2">/api/research/</td><td className="py-2 px-2 text-gray-600">List recent jobs</td></tr>
              <tr className="border-b border-gray-100"><td className="py-2 px-2 font-mono text-xs text-primary-600">GET</td><td className="py-2 px-2">/api/research/{'{id}'}</td><td className="py-2 px-2 text-gray-600">Get job results</td></tr>
              <tr className="border-b border-gray-100"><td className="py-2 px-2 font-mono text-xs text-primary-600">GET</td><td className="py-2 px-2">/api/research/{'{id}'}/documents</td><td className="py-2 px-2 text-gray-600">Get documents</td></tr>
            </tbody>
          </table>
        </div>
      </Card>

      <Card title="Frequently Asked Questions" className="mb-8">
        <div className="space-y-6">
          {FAQ.map((item) => (
            <div key={item.q}>
              <h3 className="font-semibold text-gray-900">{item.q}</h3>
              <p className="text-sm text-gray-600 mt-1 leading-relaxed">{item.a}</p>
            </div>
          ))}
        </div>
      </Card>

      <Card title="Project Structure" className="mb-8">
        <pre className="text-xs text-gray-600 leading-relaxed overflow-x-auto">
{`autoreaserch/
├── backend/
│   ├── main.py              # FastAPI app entry point
│   ├── routes/              # API route handlers
│   │   ├── research_routes.py
│   │   └── analytics_routes.py
│   ├── services/            # Business logic (NLP, filtering, scoring)
│   │   └── research_service.py
│   ├── models/              # Pydantic schemas
│   │   └── schemas.py
│   ├── database/            # SQLAlchemy models & DB setup
│   │   └── setup.py
│   └── pipeline/            # PySpark & local processing
│       └── processing.py
├── frontend/
│   ├── pages/               # Next.js routes
│   │   ├── index.js         # Landing page
│   │   ├── dashboard.js     # Research dashboard
│   │   ├── results/[id].js  # Detailed results
│   │   ├── pipeline.js      # Architecture page
│   │   └── about.js         # Documentation
│   ├── components/          # React components
│   │   ├── ui/              # Base UI components
│   │   ├── charts/          # Chart components (Recharts)
│   │   ├── dashboard/       # Dashboard-specific widgets
│   │   └── layout/          # Navbar, Layout
│   └── styles/              # Tailwind CSS globals
├── data/
│   └── sample_documents.json # 50 AI/ML research papers
└── README.md`}
        </pre>
      </Card>
    </div>
  );
}
