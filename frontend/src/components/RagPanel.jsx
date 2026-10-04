import React, { useState, useEffect } from 'react';
import { Upload, FileText, Search, Database, CheckCircle, AlertCircle, Sparkles, Layers } from 'lucide-react';

export default function RagPanel({ apiHost }) {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState(null);
  const [documents, setDocuments] = useState([]);
  const [query, setQuery] = useState('');
  const [searching, setSearching] = useState(false);
  const [ragResult, setRagResult] = useState(null);

  const fetchDocuments = async () => {
    try {
      const res = await fetch(`${apiHost}/api/rag/documents`);
      const data = await res.json();
      setDocuments(data.documents || []);
    } catch (err) {
      console.error('Failed to fetch documents:', err);
    }
  };

  useEffect(() => {
    fetchDocuments();
  }, [apiHost]);

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!file) return;

    setUploading(true);
    setUploadStatus(null);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await fetch(`${apiHost}/api/rag/upload`, {
        method: 'POST',
        body: formData,
      });
      const data = await res.json();
      if (res.ok) {
        setUploadStatus({ type: 'success', message: data.message });
        setFile(null);
        fetchDocuments();
      } else {
        setUploadStatus({ type: 'error', message: data.detail || 'Upload failed' });
      }
    } catch (err) {
      setUploadStatus({ type: 'error', message: err.message });
    } finally {
      setUploading(false);
    }
  };

  const handleQuery = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;

    setSearching(true);
    try {
      const res = await fetch(`${apiHost}/api/agent/query`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_query: query, target_sub_agent: 'rag' }),
      });
      const data = await res.json();
      setRagResult(data);
    } catch (err) {
      console.error(err);
    } finally {
      setSearching(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <Database className="w-5 h-5 text-cyan-400" />
            Sub-Agent 01: Complete PDF RAG & Hosted Qdrant
          </h2>
          <p className="text-xs text-slate-400">
            Upload any PDF to process chunks, embed vectors, and execute similarity search via hosted Qdrant vector database.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Upload Card */}
        <div className="glass-panel p-5 space-y-4">
          <h3 className="text-sm font-semibold text-slate-200 flex items-center gap-2 border-b border-slate-800 pb-2">
            <Upload className="w-4 h-4 text-indigo-400" />
            Upload PDF Document
          </h3>

          <form onSubmit={handleUpload} className="space-y-4">
            <label className="border-2 border-dashed border-slate-800 hover:border-cyan-500/50 rounded-xl p-6 flex flex-col items-center justify-center cursor-pointer transition-colors bg-slate-950/40">
              <FileText className="w-8 h-8 text-cyan-400 mb-2 opacity-80" />
              <span className="text-xs font-medium text-slate-300">
                {file ? file.name : 'Select or Drop PDF File'}
              </span>
              <span className="text-[10px] text-slate-500 mt-1">Supports PDF format up to 25MB</span>
              <input
                type="file"
                accept=".pdf"
                className="hidden"
                onChange={(e) => setFile(e.target.files[0])}
              />
            </label>

            {uploadStatus && (
              <div className={`p-3 rounded-lg text-xs flex items-center gap-2 ${
                uploadStatus.type === 'success'
                  ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                  : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
              }`}>
                {uploadStatus.type === 'success' ? <CheckCircle className="w-4 h-4" /> : <AlertCircle className="w-4 h-4" />}
                {uploadStatus.message}
              </div>
            )}

            <button
              type="submit"
              disabled={!file || uploading}
              className="w-full py-2.5 rounded-xl bg-gradient-to-r from-cyan-500 to-indigo-600 hover:from-cyan-400 hover:to-indigo-500 text-white font-medium text-xs transition-all shadow-lg shadow-cyan-500/20 disabled:opacity-50"
            >
              {uploading ? 'Processing & Vectorizing PDF...' : 'Upload & Index in Qdrant'}
            </button>
          </form>

          {/* Indexed Document List */}
          <div className="mt-4 pt-4 border-t border-slate-800 space-y-2">
            <h4 className="text-xs font-semibold text-slate-400 flex items-center gap-1.5">
              <Layers className="w-3.5 h-3.5 text-indigo-400" />
              Indexed Documents ({documents.length})
            </h4>
            {documents.length === 0 ? (
              <p className="text-xs text-slate-500 italic">No PDF files uploaded yet.</p>
            ) : (
              <div className="space-y-1.5 max-h-40 overflow-y-auto pr-1">
                {documents.map((doc, idx) => (
                  <div key={idx} className="p-2 rounded-lg bg-slate-900/80 border border-slate-800 flex items-center justify-between text-xs">
                    <span className="text-slate-300 truncate max-w-[150px]">{doc.filename}</span>
                    <span className="text-[10px] px-2 py-0.5 rounded bg-indigo-500/10 text-indigo-400 font-mono">
                      {doc.total_chunks} chunks
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Query & Results Column */}
        <div className="lg:col-span-2 space-y-4">
          <div className="glass-panel p-5 space-y-4">
            <form onSubmit={handleQuery} className="flex gap-2">
              <div className="relative flex-1">
                <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
                <input
                  type="text"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="Ask any question about your uploaded PDF..."
                  className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-slate-950/80 border border-slate-800 text-slate-100 placeholder-slate-500 text-xs focus:outline-none focus:border-cyan-500"
                />
              </div>
              <button
                type="submit"
                disabled={searching || !query.trim()}
                className="px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-medium text-xs transition-all shadow-md shadow-indigo-600/20 disabled:opacity-50 flex items-center gap-1.5"
              >
                <Sparkles className="w-4 h-4" />
                {searching ? 'Querying RAG...' : 'Query Sub-Agent 01'}
              </button>
            </form>

            {/* Response Section */}
            {ragResult && (
              <div className="mt-4 space-y-4">
                <div className="p-4 rounded-xl bg-slate-950/80 border border-cyan-500/30 space-y-2">
                  <div className="flex items-center justify-between text-xs text-cyan-400 font-mono">
                    <span>Active Node: RAG Sub-Agent</span>
                    <span>Qdrant Vector Database</span>
                  </div>
                  <div className="text-xs text-slate-200 leading-relaxed whitespace-pre-line">
                    {ragResult.agent_response}
                  </div>
                </div>

                {/* Retrieved Context Chunks */}
                {ragResult.rag_context && ragResult.rag_context.length > 0 && (
                  <div className="space-y-2">
                    <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                      Retrieved Vector Chunks ({ragResult.rag_context.length})
                    </h4>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                      {ragResult.rag_context.map((chunk, idx) => (
                        <div key={idx} className="p-3 rounded-lg bg-slate-900/60 border border-slate-800 space-y-1">
                          <div className="flex items-center justify-between text-[11px] text-slate-400 font-mono">
                            <span className="text-cyan-300">{chunk.filename} (Page {chunk.page})</span>
                            <span className="text-emerald-400">Score: {chunk.score?.toFixed(3)}</span>
                          </div>
                          <p className="text-[11px] text-slate-300 line-clamp-3">
                            "{chunk.text}"
                          </p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
