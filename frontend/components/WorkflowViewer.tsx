'use client';

import { useState, useEffect } from 'react';

interface AgentInfo {
  name: string;
  description: string;
  order: number;
}

interface WorkflowInfo {
  agents: AgentInfo[];
  description: string;
}

export default function WorkflowViewer() {
  const [isExpanded, setIsExpanded] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [workflowInfo, setWorkflowInfo] = useState<WorkflowInfo | null>(null);

  // Fetch workflow info when component mounts
  useEffect(() => {
    const fetchWorkflowInfo = async () => {
      try {
        const response = await fetch('http://localhost:8002/api/workflow/info');
        if (!response.ok) {
          throw new Error('Failed to fetch workflow info');
        }
        const data = await response.json();
        setWorkflowInfo(data);
      } catch (err) {
        console.error('Error fetching workflow info:', err);
      }
    };

    fetchWorkflowInfo();
  }, []);

  const handleToggle = () => {
    setIsExpanded(!isExpanded);
    if (!isExpanded) {
      setIsLoading(true);
      setError(null);
    }
  };

  const handleImageLoad = () => {
    setIsLoading(false);
  };

  const handleImageError = () => {
    setIsLoading(false);
    setError('ワークフローの読み込みに失敗しました');
  };

  // Agent icon mapping
  const getAgentIcon = (name: string) => {
    const icons: { [key: string]: string } = {
      'Router': '🔀',
      'Researcher': '🔍',
      'Analyzer': '📊',
      'Composer': '✍️'
    };
    return icons[name] || '⚙️';
  };

  return (
    <div className="border-2 border-blue-200 rounded-2xl overflow-hidden shadow-xl bg-white">
      {/* Header */}
      <button
        onClick={handleToggle}
        className="w-full p-6 bg-gradient-to-r from-blue-900 to-blue-800 hover:from-blue-800 hover:to-blue-700 text-left flex items-center justify-between transition-all"
      >
        <div>
          <h2 className="text-2xl font-bold text-white">
            ワークフロー設計
          </h2>
          <p className="text-sm text-blue-100 mt-2 font-medium">
            LangGraphによるマルチエージェントワークフローの可視化
          </p>
        </div>
        <svg
          className={`w-7 h-7 text-blue-100 transform transition-transform ${
            isExpanded ? 'rotate-180' : ''
          }`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M19 9l-7 7-7-7"
          />
        </svg>
      </button>

      {/* Content */}
      {isExpanded && (
        <div className="p-8 bg-gradient-to-br from-blue-50/50 to-white">
          {isLoading && (
            <div className="flex justify-center items-center h-64">
              <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-blue-900"></div>
            </div>
          )}

          {error && (
            <div className="flex justify-center items-center h-64">
              <div className="text-red-500 text-center">
                <svg
                  className="w-16 h-16 mx-auto mb-4"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
                <p className="font-semibold">{error}</p>
              </div>
            </div>
          )}

          <div className={isLoading || error ? 'hidden' : 'flex justify-center mb-6'}>
            <img
              src={`http://localhost:8002/api/workflow/graph?t=${Date.now()}`}
              alt="LangGraph Workflow Visualization"
              className="max-w-full h-auto border-2 border-blue-200 rounded-2xl shadow-lg"
              onLoad={handleImageLoad}
              onError={handleImageError}
            />
          </div>

          {workflowInfo && (
            <div className="mt-6 p-6 bg-gradient-to-br from-blue-100 to-blue-50 rounded-2xl border-2 border-blue-200 shadow-md">
              <h3 className="font-bold text-xl text-blue-900 mb-3">
                エージェント構成
              </h3>
              <p className="text-sm text-blue-800 mb-5 leading-relaxed">
                {workflowInfo.description}
              </p>
              <ul className="space-y-3">
                {workflowInfo.agents.map((agent) => (
                  <li
                    key={agent.name}
                    className="flex items-start p-4 bg-white rounded-xl border border-blue-200 shadow-sm hover:shadow-md transition-all"
                  >
                    <span className="text-2xl mr-3 mt-0.5">
                      {getAgentIcon(agent.name)}
                    </span>
                    <div>
                      <span className="font-bold text-blue-900 text-base">
                        {agent.order}. {agent.name}
                      </span>
                      <p className="text-sm text-gray-700 mt-1">
                        {agent.description}
                      </p>
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
