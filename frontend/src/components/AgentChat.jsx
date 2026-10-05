import React, { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, Sparkles, Terminal, Database, Calendar, ArrowRight, Activity } from 'lucide-react';
import { GithubIcon as Github } from './Icons';

export default function AgentChat({ apiHost }) {
  const [messages, setMessages] = useState([
    {
      sender: 'assistant',
      text: 'Hello! I am your Supervisor LangGraph Agent. I orchestrate 3 powerful sub-agents:\n\n1. **Sub-Agent 01**: PDF RAG with hosted Qdrant Vector Store\n2. **Sub-Agent 02**: GitHub MCP Agent (Repos, commits, issues, code)\n3. **Sub-Agent 03**: Google Workspace MCP Agent (Calendar meetings, Gmail draft/send, auto-schedule & notify)\n\nHow can I help you today?',
      activeAgent: 'supervisor',
      executionLogs: []
    }
  ]);

  const [input, setInput] = useState('');
  const [targetAgent, setTargetAgent] = useState('auto'); // 'auto', 'rag', 'github', 'google_workspace'
  const [loading, setLoading] = useState(false);
  const [currentExecutionLogs, setCurrentExecutionLogs] = useState([]);
  const [activeNode, setActiveNode] = useState(null);

  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userQuery = input.trim();
    setInput('');

    const newMessages = [...messages, { sender: 'user', text: userQuery }];
    setMessages(newMessages);

    setLoading(true);
    setActiveNode('supervisor_router');
    setCurrentExecutionLogs([
      { node: 'supervisor_router', status: 'running', details: 'Analyzing intent...' }
    ]);

    try {
      const targetParam = targetAgent === 'auto' ? null : targetAgent;
      const res = await fetch(`${apiHost}/api/agent/query`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_query: userQuery,
          target_sub_agent: targetParam
        }),
      });

      const data = await res.json();

      setActiveNode(null);
      setCurrentExecutionLogs(data.execution_logs || []);

      setMessages((prev) => [
        ...prev,
        {
          sender: 'assistant',
          text: data.agent_response,
          activeAgent: data.active_agent,
          executionLogs: data.execution_logs || [],
          ragContext: data.rag_context,
          githubResult: data.github_result,
          googleResult: data.google_result
        }
      ]);
    } catch (err) {
      console.error(err);
      setMessages((prev) => [
        ...prev,
        {
          sender: 'assistant',
          text: 'Error connecting to LangGraph Backend server. Please check settings or backend status.',
          activeAgent: 'error',
          executionLogs: []
        }
      ]);
    } finally {
      setLoading(false);
      setActiveNode(null);
    }
  };

  const getAgentBadge = (agentName) => {
    switch (agentName) {
      case 'rag_sub_agent':
        return <span className="flex items-center gap-1 text-[10px] px-2 py-0.5 rounded-full bg-cyan-500/10 text-cyan-400 border border-cyan-500/20"><Database className="w-3 h-3" /> Sub-Agent 01: Hosted Qdrant RAG</span>;
      case 'github_mcp_sub_agent':
        return <span className="flex items-center gap-1 text-[10px] px-2 py-0.5 rounded-full bg-violet-500/10 text-violet-400 border border-violet-500/20"><Github className="w-3 h-3" /> Sub-Agent 02: GitHub MCP</span>;
      case 'google_workspace_sub_agent':
        return <span className="flex items-center gap-1 text-[10px] px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"><Calendar className="w-3 h-3" /> Sub-Agent 03: Google Workspace</span>;
      default:
        return <span className="flex items-center gap-1 text-[10px] px-2 py-0.5 rounded-full bg-indigo-500/10 text-indigo-400 border border-indigo-500/20"><Bot className="w-3 h-3" /> Supervisor Orchestrator</span>;
    }
  };

  const renderFormattedMessage = (text) => {
    if (!text) return <p className="text-slate-400 italic">No response content received from agent.</p>;

    const lines = text.split('\n');
    return lines.map((line, lIdx) => {
      let content = line;
      const isBullet = line.trim().startsWith('- ') || line.trim().startsWith('* ');
      if (isBullet) {
        content = line.trim().substring(2);
      }

      const parts = content.split(/(\*\*.*?\*\*|`.*?`)/g);

      const formattedParts = parts.map((part, pIdx) => {
        if (part.startsWith('**') && part.endsWith('**')) {
          return <strong key={pIdx} className="font-semibold text-cyan-300">{part.slice(2, -2)}</strong>;
        }
        if (part.startsWith('`') && part.endsWith('`')) {
          return <code key={pIdx} className="bg-slate-800 text-amber-300 px-1.5 py-0.5 rounded font-mono text-[11px]">{part.slice(1, -1)}</code>;
        }
        return part;
      });

      if (isBullet) {
        return (
          <div key={lIdx} className="flex items-start gap-2 my-1 pl-2">
            <span className="text-cyan-400 font-bold">•</span>
            <div className="flex-1">{formattedParts}</div>
          </div>
        );
      }

      return (
        <div key={lIdx} className={line.trim() === '' ? 'h-2' : 'my-0.5'}>
          {formattedParts}
        </div>
      );
    });
  };

  return (
    <div className="space-y-4">

      {/* Main Chat Container */}
      <div className="glass-panel flex flex-col h-[580px] overflow-hidden">
        {/* Messages Scroll Area */}
        <div className="flex-1 p-5 overflow-y-auto space-y-4">
          {messages.map((msg, index) => (
            <div
              key={index}
              className={`flex gap-3 ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              {msg.sender === 'assistant' && (
                <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-cyan-500 to-indigo-600 flex items-center justify-center text-white shrink-0 mt-1 shadow-md shadow-indigo-500/20">
                  <Bot className="w-4 h-4" />
                </div>
              )}

              <div className={`max-w-[85%] space-y-2 ${
                msg.sender === 'user'
                  ? 'bg-indigo-600 text-white rounded-2xl rounded-tr-none px-4 py-3 shadow-md'
                  : 'bg-slate-900/90 border border-slate-800 text-slate-100 rounded-2xl rounded-tl-none p-4 shadow-sm'
              }`}>
                {msg.sender === 'assistant' && (
                  <div className="flex items-center justify-between border-b border-slate-800 pb-2 mb-2">
                    {getAgentBadge(msg.activeAgent)}
                  </div>
                )}

                <div className="text-xs leading-relaxed">
                  {renderFormattedMessage(msg.text)}
                </div>

                {/* Execution Logs Dropdown / Trace */}
                {msg.executionLogs && msg.executionLogs.length > 0 && (
                  <div className="mt-3 pt-2 border-t border-slate-800/80">
                    <details className="text-[10px] text-slate-400 font-mono">
                      <summary className="cursor-pointer hover:text-slate-200 transition-colors">
                        View LangGraph Execution Trace ({msg.executionLogs.length} steps)
                      </summary>
                      <div className="mt-2 space-y-1 pl-2 border-l border-indigo-500/30">
                        {msg.executionLogs.map((log, lIdx) => (
                          <div key={lIdx} className="flex items-center gap-1.5 text-slate-300">
                            <span className="text-cyan-400">[{log.node}]</span>
                            <span>{log.details || log.status}</span>
                          </div>
                        ))}
                      </div>
                    </details>
                  </div>
                )}
              </div>

              {msg.sender === 'user' && (
                <div className="w-8 h-8 rounded-xl bg-slate-800 border border-slate-700 flex items-center justify-center text-slate-300 shrink-0 mt-1">
                  <User className="w-4 h-4" />
                </div>
              )}
            </div>
          ))}

          {loading && (
            <div className="flex gap-3 justify-start">
              <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-cyan-500 to-indigo-600 flex items-center justify-center text-white shrink-0 animate-pulse">
                <Bot className="w-4 h-4" />
              </div>
              <div className="bg-slate-900 border border-slate-800 rounded-2xl rounded-tl-none p-4 text-xs text-slate-300 flex items-center gap-2">
                <Activity className="w-4 h-4 text-cyan-400 animate-spin" />
                <span>LangGraph Supervisor routing query to sub-agents...</span>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input Controls */}
        <div className="p-3 border-t border-slate-800 bg-slate-950/60 flex flex-col gap-2">
          {/* Target Router Selector */}
          <div className="flex items-center gap-2 text-[11px]">
            <span className="text-slate-400 font-medium">Route Target:</span>
            <div className="flex items-center gap-1 bg-slate-900 p-1 rounded-lg border border-slate-800 flex-wrap">
              {[
                { id: 'auto', label: 'Auto (Supervisor Router)' },
                { id: 'supervisor', label: 'Supervisor Chat' },
                { id: 'rag', label: 'PDF RAG (Sub 01)' },
                { id: 'github', label: 'GitHub MCP (Sub 02)' },
                { id: 'google_workspace', label: 'Google Workspace (Sub 03)' },
              ].map((opt) => (
                <button
                  key={opt.id}
                  onClick={() => setTargetAgent(opt.id)}
                  className={`px-2.5 py-1 rounded-md text-[10px] font-mono transition-all ${
                    targetAgent === opt.id
                      ? 'bg-indigo-600 text-white shadow'
                      : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  {opt.label}
                </button>
              ))}
            </div>
          </div>

          <form onSubmit={handleSubmit} className="flex gap-2">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask anything (PDF document question, GitHub code/repo, Google Calendar meeting, or Gmail draft/send)..."
              className="flex-1 px-4 py-3 rounded-xl bg-slate-900 border border-slate-800 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500"
            />
            <button
              type="submit"
              disabled={loading || !input.trim()}
              className="px-6 py-3 rounded-xl bg-gradient-to-r from-cyan-500 via-indigo-600 to-violet-600 hover:from-cyan-400 hover:to-violet-500 text-white font-medium text-xs transition-all shadow-lg shadow-indigo-600/25 disabled:opacity-50 flex items-center gap-1.5"
            >
              <span>Send</span>
              <Send className="w-3.5 h-3.5" />
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
