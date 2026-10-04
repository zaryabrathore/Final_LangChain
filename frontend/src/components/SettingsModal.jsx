import React, { useState, useEffect } from 'react';
import { X, Key, Database, Mail, CheckCircle2, AlertCircle } from 'lucide-react';
import { GithubIcon as Github } from './Icons';

export default function SettingsModal({ isOpen, onClose, apiHost }) {
  const [geminiKey, setGeminiKey] = useState('');
  const [qdrantHost, setQdrantHost] = useState('');
  const [qdrantApiKey, setQdrantApiKey] = useState('');
  const [qdrantCollection, setQdrantCollection] = useState('pdf_rag_collection');
  const [githubToken, setGithubToken] = useState('');
  const [googleEmail, setGoogleEmail] = useState('');

  const [saving, setSaving] = useState(false);
  const [saveStatus, setSaveStatus] = useState(null);

  useEffect(() => {
    if (isOpen) {
      fetch(`${apiHost}/api/settings`)
        .then((res) => res.json())
        .then((data) => {
          setQdrantHost(data.qdrant_host || '');
          setQdrantCollection(data.qdrant_collection || 'pdf_rag_collection');
          setGoogleEmail(data.google_user_email || '');
        })
        .catch(console.error);
    }
  }, [isOpen, apiHost]);

  if (!isOpen) return null;

  const handleSave = async (e) => {
    e.preventDefault();
    setSaving(true);
    setSaveStatus(null);

    const payload = {};
    if (geminiKey) payload.gemini_api_key = geminiKey;
    if (qdrantHost) payload.qdrant_host = qdrantHost;
    if (qdrantApiKey) payload.qdrant_api_key = qdrantApiKey;
    if (qdrantCollection) payload.qdrant_collection = qdrantCollection;
    if (githubToken) payload.github_token = githubToken;
    if (googleEmail) payload.google_user_email = googleEmail;

    try {
      const res = await fetch(`${apiHost}/api/settings`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      if (res.ok) {
        setSaveStatus({ type: 'success', message: 'Settings successfully updated on backend server!' });
        setTimeout(() => setSaveStatus(null), 3000);
      } else {
        setSaveStatus({ type: 'error', message: 'Failed to update settings.' });
      }
    } catch (err) {
      setSaveStatus({ type: 'error', message: err.message });
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-md flex items-center justify-center p-4">
      <div className="glass-panel w-full max-w-xl p-6 relative space-y-5 animate-in fade-in zoom-in duration-200">
        <button
          onClick={onClose}
          className="absolute right-4 top-4 text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800 transition-colors"
        >
          <X className="w-5 h-5" />
        </button>

        <div className="flex items-center gap-3 border-b border-slate-800 pb-3">
          <div className="p-2 rounded-xl bg-indigo-500/10 text-indigo-400">
            <Key className="w-5 h-5" />
          </div>
          <div>
            <h3 className="font-bold text-base text-white">System API & Vector Store Settings</h3>
            <p className="text-xs text-slate-400">Configure LLM, Hosted Qdrant, GitHub, & Google Workspace credentials</p>
          </div>
        </div>

        <form onSubmit={handleSave} className="space-y-4">
          {/* Gemini Key */}
          <div>
            <label className="text-xs font-medium text-slate-300 flex items-center gap-1.5 mb-1">
              <Key className="w-3.5 h-3.5 text-cyan-400" />
              Google Gemini API Key
            </label>
            <input
              type="password"
              placeholder="AIzaSy..."
              value={geminiKey}
              onChange={(e) => setGeminiKey(e.target.value)}
              className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-white placeholder-slate-600 focus:outline-none focus:border-cyan-500"
            />
          </div>

          {/* Qdrant Cloud Host & Key */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs font-medium text-slate-300 flex items-center gap-1.5 mb-1">
                <Database className="w-3.5 h-3.5 text-cyan-400" />
                Hosted Qdrant Host URL
              </label>
              <input
                type="text"
                placeholder="https://xyz.cloud.qdrant.io:6333"
                value={qdrantHost}
                onChange={(e) => setQdrantHost(e.target.value)}
                className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-white placeholder-slate-600"
              />
            </div>
            <div>
              <label className="text-xs font-medium text-slate-300 flex items-center gap-1.5 mb-1">
                <Database className="w-3.5 h-3.5 text-cyan-400" />
                Qdrant Cloud API Key
              </label>
              <input
                type="password"
                placeholder="qdrant_api_key"
                value={qdrantApiKey}
                onChange={(e) => setQdrantApiKey(e.target.value)}
                className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-white placeholder-slate-600"
              />
            </div>
          </div>

          {/* GitHub Token & Google Email */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs font-medium text-slate-300 flex items-center gap-1.5 mb-1">
                <Github className="w-3.5 h-3.5 text-violet-400" />
                GitHub Personal Token
              </label>
              <input
                type="password"
                placeholder="ghp_xxx..."
                value={githubToken}
                onChange={(e) => setGithubToken(e.target.value)}
                className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-white placeholder-slate-600"
              />
            </div>
            <div>
              <label className="text-xs font-medium text-slate-300 flex items-center gap-1.5 mb-1">
                <Mail className="w-3.5 h-3.5 text-emerald-400" />
                Google Account Email
              </label>
              <input
                type="email"
                placeholder="user@example.com"
                value={googleEmail}
                onChange={(e) => setGoogleEmail(e.target.value)}
                className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-white"
              />
            </div>
          </div>

          {saveStatus && (
            <div className={`p-3 rounded-xl text-xs flex items-center gap-2 ${
              saveStatus.type === 'success'
                ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
            }`}>
              {saveStatus.type === 'success' ? <CheckCircle2 className="w-4 h-4" /> : <AlertCircle className="w-4 h-4" />}
              {saveStatus.message}
            </div>
          )}

          <div className="flex justify-end gap-2 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={saving}
              className="px-5 py-2 rounded-xl bg-gradient-to-r from-cyan-500 to-indigo-600 hover:from-cyan-400 hover:to-indigo-500 text-white text-xs font-medium shadow-md shadow-indigo-500/20"
            >
              {saving ? 'Saving...' : 'Save Settings'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
