import { Search, GitCommit, AlertCircle, FileCode, Terminal, ExternalLink } from 'lucide-react';
import { GithubIcon as Github } from './Icons';

export default function GithubPanel({ apiHost }) {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [githubResult, setGithubResult] = useState(null);
  const [mcpTools, setMcpTools] = useState([]);

  useEffect(() => {
    fetch(`${apiHost}/api/mcp/github/tools`)
      .then((res) => res.json())
      .then((data) => setMcpTools(data.tools || []))
      .catch(console.error);
  }, [apiHost]);

  const handleQuery = async (e, customQuery = null) => {
    if (e) e.preventDefault();
    const q = customQuery || query;
    if (!q.trim()) return;

    setLoading(true);
    try {
      const res = await fetch(`${apiHost}/api/agent/query`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_query: q, target_sub_agent: 'github' }),
      });
      const data = await res.json();
      setGithubResult(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const sampleQueries = [
    'Search repositories for langgraph',
    'List recent commits for langchain-ai/langgraph',
    'Show open issues for langchain-ai/langgraph',
    'Read file README.md from langchain-ai/langgraph',
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <Github className="w-5 h-5 text-violet-400" />
            Sub-Agent 02: GitHub MCP Sub-Agent
          </h2>
          <p className="text-xs text-slate-400">
            Model Context Protocol (MCP) sub-agent for querying GitHub repositories, commit logs, open issues, and codebase files.
          </p>
        </div>
      </div>

      {/* Quick Actions & Search */}
      <div className="glass-panel p-5 space-y-4">
        <form onSubmit={handleQuery} className="flex gap-2">
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Ask any GitHub question (e.g., search repos, commits, issues, file contents)..."
              className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-slate-950/80 border border-slate-800 text-slate-100 placeholder-slate-500 text-xs focus:outline-none focus:border-violet-500"
            />
          </div>
          <button
            type="submit"
            disabled={loading || !query.trim()}
            className="px-5 py-2.5 rounded-xl bg-violet-600 hover:bg-violet-500 text-white font-medium text-xs transition-all shadow-md shadow-violet-600/20 disabled:opacity-50 flex items-center gap-1.5"
          >
            <Terminal className="w-4 h-4" />
            {loading ? 'Executing MCP...' : 'Query GitHub MCP'}
          </button>
        </form>

        <div className="flex flex-wrap items-center gap-2 pt-1">
          <span className="text-[11px] font-medium text-slate-400">Sample Prompts:</span>
          {sampleQueries.map((prompt, idx) => (
            <button
              key={idx}
              onClick={() => {
                setQuery(prompt);
                handleQuery(null, prompt);
              }}
              className="px-2.5 py-1 rounded-lg bg-slate-900 hover:bg-slate-800 border border-slate-800 text-[11px] text-slate-300 transition-colors"
            >
              {prompt}
            </button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Results Panel */}
        <div className="lg:col-span-2 space-y-4">
          {githubResult ? (
            <div className="glass-panel p-5 space-y-4">
              <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                <span className="text-xs font-mono text-violet-400 flex items-center gap-1.5">
                  <Terminal className="w-3.5 h-3.5" />
                  Active Node: GitHub MCP Sub-Agent
                </span>
                <span className="text-[10px] px-2 py-0.5 rounded bg-violet-500/10 text-violet-300 font-mono">
                  MCP Protocol Compliant
                </span>
              </div>

              <div className="p-4 rounded-xl bg-slate-950/90 border border-slate-800 text-xs text-slate-200 leading-relaxed whitespace-pre-line">
                {githubResult.agent_response}
              </div>

              {githubResult.github_result && (
                <div className="space-y-2">
                  <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                    Raw MCP Output Payload
                  </h4>
                  <pre className="p-3 rounded-xl bg-slate-950 border border-slate-800 text-[11px] text-emerald-400 font-mono overflow-x-auto max-h-60">
                    {JSON.stringify(githubResult.github_result, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          ) : (
            <div className="glass-panel p-10 flex flex-col items-center justify-center text-center text-slate-500">
              <Github className="w-12 h-12 text-slate-700 mb-3" />
              <p className="text-xs">Select a sample prompt or enter a GitHub query above to invoke the GitHub MCP Sub-Agent.</p>
            </div>
          )}
        </div>

        {/* MCP Available Tools Schema Inspector */}
        <div className="glass-panel p-5 space-y-3">
          <h3 className="text-xs font-semibold text-slate-300 uppercase tracking-wider flex items-center gap-2 border-b border-slate-800 pb-2">
            <FileCode className="w-4 h-4 text-violet-400" />
            GitHub MCP Tool Registry ({mcpTools.length})
          </h3>
          <div className="space-y-2 max-h-[450px] overflow-y-auto pr-1">
            {mcpTools.map((tool, idx) => (
              <div key={idx} className="p-3 rounded-xl bg-slate-950/60 border border-slate-800/80 space-y-1">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-mono text-violet-300 font-semibold">{tool.name}</span>
                  <span className="text-[9px] px-1.5 py-0.2 rounded bg-slate-800 text-slate-400">mcp/tool</span>
                </div>
                <p className="text-[11px] text-slate-400">{tool.description}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
