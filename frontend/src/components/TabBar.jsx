import React from 'react';
import { Bot, FileText, Calendar } from 'lucide-react';
import { GithubIcon as Github } from './Icons';

export default function TabBar({ activeTab, setActiveTab }) {
  const tabs = [
    { id: 'chat', label: 'Supervisor Chat', icon: Bot, badge: 'Main Agent', color: 'indigo' },
    { id: 'rag', label: 'PDF RAG Sub-Agent', icon: FileText, badge: 'Sub 01', color: 'cyan' },
    { id: 'github', label: 'GitHub MCP Sub-Agent', icon: Github, badge: 'Sub 02', color: 'violet' },
    { id: 'workspace', label: 'Google Workspace Sub-Agent', icon: Calendar, badge: 'Sub 03', color: 'emerald' },
  ];

  return (
    <div className="glass-panel p-2 mb-6">
      <nav className="grid grid-cols-2 md:grid-cols-4 gap-2">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center justify-between px-4 py-3 rounded-xl text-xs font-semibold transition-all duration-300 ${
                isActive
                  ? 'bg-gradient-to-r from-indigo-600 via-indigo-500 to-violet-600 text-white shadow-lg shadow-indigo-500/25 border border-indigo-400/30 scale-[1.01]'
                  : 'bg-slate-900/60 hover:bg-slate-800/80 text-slate-400 hover:text-slate-200 border border-slate-800/80'
              }`}
            >
              <div className="flex items-center gap-2.5">
                <Icon className={`w-4 h-4 ${isActive ? 'text-cyan-300' : 'text-slate-400'}`} />
                <span className="tracking-wide">{tab.label}</span>
              </div>
              <span className={`text-[10px] px-2 py-0.5 rounded-full font-mono font-medium ${
                isActive ? 'bg-white/20 text-white' : 'bg-slate-800 text-slate-400 border border-slate-700/60'
              }`}>
                {tab.badge}
              </span>
            </button>
          );
        })}
      </nav>
    </div>
  );
}
