import Navbar from "./Navbar";

export default function Layout({ children }) {
  return (
    <div className="min-h-screen flex flex-col">
      <Navbar />
      <main className="flex-1">{children}</main>
      <footer className="bg-white border-t border-gray-200 py-8 mt-16">
        <div className="max-w-7xl mx-auto px-4 text-center text-sm text-gray-500">
          <p className="font-medium text-gray-700">AutoResearch</p>
          <p className="mt-1">AI-Powered Research Intelligence Platform</p>
          <p className="mt-2">&copy; {new Date().getFullYear()} AutoResearch. Built with FastAPI, PySpark &amp; Next.js</p>
        </div>
      </footer>
    </div>
  );
}
