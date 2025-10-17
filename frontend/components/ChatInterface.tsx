'use client';

import { useState, useEffect, useRef } from 'react';

interface AgentStep {
  agent: string;
  action: string;
  result?: string;
  elapsed_time?: number;  // Agent execution time in seconds
  input?: string;  // Agent input data
  output?: string;  // Agent output data
}

interface Message {
  role: 'user' | 'assistant';
  content: string;
  agentSteps?: Array<AgentStep>;
  elapsedTime?: number;  // Total processing time in seconds
}

export default function ChatInterface() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [elapsedTime, setElapsedTime] = useState(0);
  const timerRef = useRef<NodeJS.Timeout | null>(null);
  const [conversationHistory, setConversationHistory] = useState<
    Array<{ role: string; content: string }>
  >([]);
  const [expandedSteps, setExpandedSteps] = useState<{ [key: string]: boolean }>({});

  const toggleStepExpansion = (messageIndex: number, stepIndex: number) => {
    const key = `${messageIndex}-${stepIndex}`;
    setExpandedSteps(prev => ({ ...prev, [key]: !prev[key] }));
  };

  // Timer effect - updates every 0.1 seconds
  useEffect(() => {
    if (isLoading) {
      setElapsedTime(0);
      timerRef.current = setInterval(() => {
        setElapsedTime((prev) => Math.round((prev + 0.1) * 10) / 10);
      }, 100);
    } else {
      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }
    }

    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    };
  }, [isLoading]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage: Message = { role: 'user', content: input };
    const currentInput = input;
    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const response = await fetch('http://localhost:8002/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: currentInput,
          conversation_history: conversationHistory,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to fetch');
      }

      const data = await response.json();
      const assistantMessage: Message = {
        role: 'assistant',
        content: data.response,
        agentSteps: data.steps,
        elapsedTime: data.elapsed_time,
      };
      setMessages((prev) => [...prev, assistantMessage]);

      // Update conversation history
      setConversationHistory((prev) => [
        ...prev,
        { role: 'user', content: currentInput },
        { role: 'assistant', content: data.response },
      ]);
    } catch (error) {
      console.error('Error:', error);
      const errorMessage: Message = {
        role: 'assistant',
        content: 'エラーが発生しました。もう一度お試しください。',
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-[600px] bg-white border-2 border-blue-200 rounded-2xl overflow-hidden shadow-xl">
      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-6 space-y-4 bg-gradient-to-b from-white to-blue-50/30">
        {messages.map((message, index) => (
          <div
            key={index}
            className={`flex ${
              message.role === 'user' ? 'justify-end' : 'justify-start'
            }`}
          >
            <div
              className={`max-w-[80%] rounded-2xl p-4 shadow-md transition-all hover:shadow-lg ${
                message.role === 'user'
                  ? 'bg-gradient-to-br from-blue-900 to-blue-800 text-white'
                  : 'bg-white text-gray-800 border-2 border-blue-100'
              }`}
            >
              <p className="whitespace-pre-wrap leading-relaxed">{message.content}</p>
              {message.agentSteps && message.agentSteps.length > 0 && (
                <div className={`mt-3 pt-3 ${
                  message.role === 'user' ? 'border-t border-blue-700' : 'border-t border-blue-200'
                }`}>
                  <p className={`text-xs font-semibold mb-2 ${
                    message.role === 'user' ? 'text-blue-200' : 'text-blue-800'
                  }`}>
                    Agent Steps:
                  </p>
                  {message.agentSteps.map((step, idx) => {
                    const stepKey = `${index}-${idx}`;
                    const isExpanded = expandedSteps[stepKey];
                    const hasDetails = step.input || step.output;

                    return (
                      <div key={idx} className="mb-2">
                        <div className={`flex items-center justify-between text-xs ${
                          message.role === 'user' ? 'text-blue-100' : 'text-gray-700'
                        }`}>
                          <div className="flex-1">
                            <span className="font-semibold">{step.agent}:</span>{' '}
                            {step.action}
                            {step.elapsed_time !== undefined && (
                              <span className={`ml-2 ${
                                message.role === 'user' ? 'text-blue-200' : 'text-blue-600'
                              }`}>
                                ({step.elapsed_time.toFixed(1)}s)
                              </span>
                            )}
                          </div>
                          {hasDetails && (
                            <button
                              onClick={() => toggleStepExpansion(index, idx)}
                              className={`ml-2 p-1 rounded hover:bg-opacity-20 hover:bg-gray-500 transition-colors ${
                                message.role === 'user' ? 'text-blue-200' : 'text-blue-600'
                              }`}
                            >
                              {isExpanded ? '▼' : '▶'}
                            </button>
                          )}
                        </div>
                        {isExpanded && hasDetails && (
                          <div className={`mt-2 p-3 rounded text-xs ${
                            message.role === 'user'
                              ? 'bg-blue-800 bg-opacity-30 text-blue-50'
                              : 'bg-gray-50 text-gray-600'
                          }`}>
                            {step.input && (
                              <div className="mb-3">
                                <div className="font-semibold mb-1 flex items-center gap-2">
                                  <span>Input:</span>
                                  <span className={`text-xs font-normal ${
                                    message.role === 'user' ? 'text-blue-200' : 'text-gray-500'
                                  }`}>
                                    ({step.input.length}文字)
                                  </span>
                                </div>
                                <div className="whitespace-pre-wrap font-mono text-xs">
                                  {step.input}
                                </div>
                              </div>
                            )}
                            {step.output && (
                              <div>
                                <div className="font-semibold mb-1 flex items-center gap-2">
                                  <span>Output:</span>
                                  <span className={`text-xs font-normal ${
                                    message.role === 'user' ? 'text-blue-200' : 'text-gray-500'
                                  }`}>
                                    ({step.output.length}文字)
                                  </span>
                                </div>
                                <div className="whitespace-pre-wrap font-mono text-xs">
                                  {step.output}
                                </div>
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              )}
              {message.elapsedTime !== undefined && (
                <div className={`mt-3 pt-3 ${
                  message.role === 'user' ? 'border-t border-blue-700' : 'border-t border-blue-200'
                }`}>
                  <p className={`text-xs font-medium ${
                    message.role === 'user' ? 'text-blue-200' : 'text-blue-600'
                  }`}>
                    処理時間: {message.elapsedTime.toFixed(1)}秒
                  </p>
                </div>
              )}
            </div>
          </div>
        ))}
        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-white text-gray-800 border-2 border-blue-200 rounded-2xl p-4 shadow-md">
              <p className="animate-pulse font-medium text-blue-900">考え中...</p>
              <p className="text-xs text-blue-600 mt-2 font-medium">
                経過時間: {elapsedTime.toFixed(1)}秒
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Input Area */}
      <form onSubmit={handleSubmit} className="border-t-2 border-blue-200 p-5 bg-white">
        <div className="flex gap-3">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="メッセージを入力..."
            className="flex-1 p-3 border-2 border-blue-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-900 transition-all placeholder:text-gray-400"
            disabled={isLoading}
          />
          <button
            type="submit"
            disabled={isLoading}
            className="px-8 py-3 bg-gradient-to-r from-blue-900 to-blue-800 text-white font-semibold rounded-xl hover:from-blue-800 hover:to-blue-700 disabled:from-gray-400 disabled:to-gray-400 disabled:cursor-not-allowed transition-all shadow-md hover:shadow-lg transform hover:-translate-y-0.5"
          >
            送信
          </button>
        </div>
      </form>
    </div>
  );
}
