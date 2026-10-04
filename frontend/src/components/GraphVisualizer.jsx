import { Network, Database, Calendar, CheckCircle2, ArrowRight } from 'lucide-react';
import { GithubIcon as Github } from './Icons';

export default function GraphVisualizer({ activeNode, executionLogs }) {
  const nodes = [
    { id: 'supervisor_router', label: 'Supervisor Router', icon: Network, type: 'router', color: 'indigo' },
    { id: 'rag_sub_agent', label: 'RAG PDF Vector DB', icon: Database, type: 'subagent', color: 'cyan' },
    { id: 'github_mcp_sub_agent', label: 'GitHub MCP Agent', icon: Github, type: 'subagent', color: 'violet' },
    { id: 'google_workspace_sub_agent', label: 'Google Workspace MCP', icon: Calendar, type: 'subagent', color: 'emerald' },
    { id: 'supervisor_synthesis', label: 'Synthesis Node', icon: CheckCircle2, type: 'synthesis', color: 'amber' },
  ];

  const isNodeActive = (nodeId) => activeNode === nodeId;
  const isNodeExecuted = (nodeId) => executionLogs?.some(log => log.node === nodeId || log.target_sub_agent === nodeId.replace('_sub_agent', ''));

  return (
    <div className="glass-panel p-4 mb-6">
      <div className="flex items-center justify-between mb-3 border-b border-slate-800 pb-2">
        <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400 flex items-center gap-2">
          <Network className="w-4 h-4 text-cyan-400" />
          LangGraph Live State Graph Visualizer
        </h3>
        <span className="text-[11px] font-mono text-slate-500">
          StateGraph Router Dynamic Execution
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-5 gap-3 items-center">
        {nodes.map((node, index) => {
          const Icon = node.icon;
          const active = isNodeActive(node.id);
          const executed = isNodeExecuted(node.id);

          return (
            <div key={node.id} className="relative flex flex-col items-center">
              <div
                className={`w-full p-3 rounded-xl border flex flex-col items-center gap-2 transition-all duration-300 ${
                  active
                    ? 'bg-indigo-500/20 border-cyan-400 shadow-lg shadow-cyan-500/25 scale-105'
                    : executed
                    ? 'bg-slate-900/90 border-slate-700 text-slate-300'
                    : 'bg-slate-950/60 border-slate-800/80 opacity-50'
                }`}
              >
                <div className={`p-2 rounded-lg ${
                  active ? 'bg-cyan-500 text-slate-950' : executed ? 'bg-indigo-950 text-indigo-400' : 'bg-slate-800 text-slate-500'
                }`}>
                  <Icon className="w-4 h-4" />
                </div>

                <span className="text-xs font-medium text-center line-clamp-1">
                  {node.label}
                </span>

                {active && (
                  <span className="text-[10px] px-2 py-0.5 rounded-full bg-cyan-400/20 text-cyan-300 font-mono animate-pulse">
                    Executing...
                  </span>
                )}
                {!active && executed && (
                  <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 font-mono">
                    Completed
                  </span>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
