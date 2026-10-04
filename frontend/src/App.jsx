import React, { useState, useEffect } from 'react';
import Navbar from './components/Navbar';
import AgentChat from './components/AgentChat';
import RagPanel from './components/RagPanel';
import GithubPanel from './components/GithubPanel';
import WorkspacePanel from './components/WorkspacePanel';
import SettingsModal from './components/SettingsModal';

const API_HOST = 'http://localhost:8000';

export default function App() {
  const [activeTab, setActiveTab] = useState('chat');
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [systemHealth, setSystemHealth] = useState(null);

  useEffect(() => {
    fetch(`${API_HOST}/api/health`)
      .then((res) => res.json())
      .then(setSystemHealth)
      .catch(console.error);
  }, []);

  return (
    <div className="min-h-screen bg-[#0a0d14] text-slate-100 flex flex-col font-sans">
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        onOpenSettings={() => setIsSettingsOpen(true)}
        systemHealth={systemHealth}
      />

      <main className="flex-1 max-w-7xl w-full mx-auto p-4 md:p-6">
        {activeTab === 'chat' && <AgentChat apiHost={API_HOST} />}
        {activeTab === 'rag' && <RagPanel apiHost={API_HOST} />}
        {activeTab === 'github' && <GithubPanel apiHost={API_HOST} />}
        {activeTab === 'workspace' && <WorkspacePanel apiHost={API_HOST} />}
      </main>

      <SettingsModal
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
        apiHost={API_HOST}
      />

      <footer className="border-t border-slate-900 bg-slate-950/60 py-3 text-center text-xs text-slate-500">
        LangGraph Multi-Agent Orchestrator • Hosted Qdrant RAG • GitHub MCP • Google Workspace MCP
      </footer>
    </div>
  );
}
