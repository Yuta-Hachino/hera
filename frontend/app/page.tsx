import ChatInterface from "../components/ChatInterface";
import WorkflowViewer from "../components/WorkflowViewer";

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center">
      {/* Header Section */}
      <header className="w-full bg-gradient-to-r from-blue-900 via-blue-800 to-blue-900 text-white py-6 px-4 shadow-lg animate-slide-down">
        <div className="max-w-4xl mx-auto flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold bg-gradient-to-r from-white to-blue-100 bg-clip-text text-transparent">
              AI HACKATHON
            </h1>
            <p className="text-sm text-blue-200 mt-1">
              Multi-Agent Intelligent System
            </p>
          </div>
          <div className="text-xs text-blue-300">
            LangGraph × Perplexity API × GPT-4.1-mini
          </div>
        </div>
      </header>

      <div className="w-full max-w-4xl p-4 flex flex-col gap-8">
        {/* Chat Interface */}
        <div className="animate-slide-up">
          <ChatInterface />
        </div>

        {/* Workflow Viewer */}
        <div className="animate-fade-in" style={{ animationDelay: "0.2s" }}>
          <WorkflowViewer />
        </div>
      </div>
    </main>
  );
}
