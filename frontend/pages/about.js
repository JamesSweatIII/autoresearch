import Card from "../components/ui/Card";

const FAQ = [
  {
    q: "What is AutoResearch?",
    a: "AutoResearch is an AI-powered research intelligence platform that gathers academic papers from 4 sources (Semantic Scholar, OpenAlex, arXiv, CrossRef), ranks them by semantic relevance, analyzes sentiment, and trains a PyTorch relevance model via an autonomous AI agent loop.",
  },
  {
    q: "How does article ranking work?",
    a: "Articles are ranked by semantic similarity using SentenceTransformer (all-MiniLM-L6-v2). The query and each article's title+abstract are encoded into embeddings, and cosine similarity produces a relevance score with an explanation.",
  },
  {
    q: "What is the autoresearch loop?",
    a: "An AI coding agent (OpenCode) iterates on a PyTorch training script — editing config, training, evaluating held-out accuracy, and keeping/discarding changes via git. The model is only exposed to users once accuracy reaches ≥85% (best achieved: 91.9%).",
  },
  {
    q: "What data source does the sample use?",
    a: "The included sample dataset contains 50 influential AI/ML research papers from top venues including NeurIPS, ICML, CVPR, Nature, and ACL. Papers span topics from deep learning and reinforcement learning to NLP, computer vision, and AI ethics.",
  },
  {
    q: "How are articles gathered?",
    a: "The system queries 4 academic APIs in parallel (Semantic Scholar, OpenAlex, arXiv, CrossRef), deduplicates by DOI and normalized title, then ranks by semantic similarity. No API keys are required.",
  },
  {
    q: "What is the sentiment analysis approach?",
    a: "Sentiment is classified using a lexicon-based approach (Bing Liu opinion lexicon + TextBlob). Document text is scanned for positive and negative keyword lists. If positive terms outnumber negative ones, the document is classified as 'positive'; the reverse yields 'negative'; otherwise it is 'neutral'.",
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
          <p className="text-2xl font-bold text-gray-900">4</p>
          <p className="text-sm text-gray-500">Search Sources</p>
        </Card>
        <Card className="text-center">
          <div className="text-3xl mb-2">⚡</div>
          <p className="text-2xl font-bold text-gray-900">≥85%</p>
          <p className="text-sm text-gray-500">Accuracy Gate</p>
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
              <tr className="border-b border-gray-100"><td className="py-2 px-2 font-mono text-xs text-primary-600">GET</td><td className="py-2 px-2">/api/stats</td><td className="py-2 px-2 text-gray-600">Dataset statistics</td></tr>
              <tr className="border-b border-gray-100"><td className="py-2 px-2 font-mono text-xs text-primary-600">GET</td><td className="py-2 px-2">/api/sources</td><td className="py-2 px-2 text-gray-600">List publication venues</td></tr>
              <tr className="border-b border-gray-100"><td className="py-2 px-2 font-mono text-xs text-primary-600">GET</td><td className="py-2 px-2">/api/papers</td><td className="py-2 px-2 text-gray-600">List/filter papers</td></tr>
              <tr className="border-b border-gray-100"><td className="py-2 px-2 font-mono text-xs text-primary-600">GET</td><td className="py-2 px-2">/api/papers/{'{id}'}</td><td className="py-2 px-2 text-gray-600">Paper detail + similar</td></tr>
              <tr className="border-b border-gray-100"><td className="py-2 px-2 font-mono text-xs text-primary-600">POST</td><td className="py-2 px-2">/api/articles/search</td><td className="py-2 px-2 text-gray-600">Multi-source article search</td></tr>
              <tr className="border-b border-gray-100"><td className="py-2 px-2 font-mono text-xs text-primary-600">POST</td><td className="py-2 px-2">/api/articles/save</td><td className="py-2 px-2 text-gray-600">Save article to database</td></tr>
              <tr className="border-b border-gray-100"><td className="py-2 px-2 font-mono text-xs text-primary-600">POST</td><td className="py-2 px-2">/api/pooler/pool</td><td className="py-2 px-2 text-gray-600">Background article gathering</td></tr>
              <tr className="border-b border-gray-100"><td className="py-2 px-2 font-mono text-xs text-primary-600">GET</td><td className="py-2 px-2">/api/autoresearch/status</td><td className="py-2 px-2 text-gray-600">Model readiness gate</td></tr>
              <tr className="border-b border-gray-100"><td className="py-2 px-2 font-mono text-xs text-primary-600">POST</td><td className="py-2 px-2">/api/autoresearch/predict</td><td className="py-2 px-2 text-gray-600">Score relevance (query, doc)</td></tr>
              <tr className="border-b border-gray-100"><td className="py-2 px-2 font-mono text-xs text-primary-600">POST</td><td className="py-2 px-2">/api/autoresearch/train</td><td className="py-2 px-2 text-gray-600">Train model on gathered papers</td></tr>
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
{`autoresearch/
├── backend/
│   ├── main.py              # FastAPI app entry point
│   ├── routes/              # API route handlers
│   │   ├── article_routes.py
│   │   ├── autoresearch_routes.py
│   │   ├── pooler_routes.py
│   │   └── legacy_routes.py
│   ├── services/            # Article retrieval, ranking, pooling
│   │   ├── article_retrieval.py
│   │   ├── article_pooler.py
│   │   └── local_llm.py
│   └── database/
│       └── setup.py         # SQLAlchemy models
├── frontend/
│   ├── pages/               # Next.js routes
│   │   ├── index.js         # Landing page
│   │   ├── dashboard.js     # Search + pooler
│   │   ├── interact.js      # Gated model interaction
│   │   ├── knowledge.js     # Knowledge base
│   │   ├── pipeline.js      # Architecture
│   │   ├── results/[id].js  # Research results
│   │   ├── papers/[id].js   # Paper detail
│   │   └── about.js         # Documentation
│   ├── components/          # React components
│   │   ├── ui/              # Base UI (Card)
│   │   ├── charts/          # Recharts visualizations
│   │   ├── dashboard/       # Dashboard widgets
│   │   └── layout/          # Navbar, Layout
│   └── styles/
├── autoresearch/            # Autonomous model optimization
│   ├── train_relevance.py
│   ├── model.py / features.py / infer.py
│   ├── build_dataset.py / plot.py
│   └── AGENT_INSTRUCTIONS.md
├── data/
│   ├── autoresearch.db      # SQLite database
│   └── sample_documents.json.bak
├── DEMO.md / FINAL_REPORT.md / PLAN.md / SLIDES.md
└── README.md`}
        </pre>
      </Card>
    </div>
  );
}
