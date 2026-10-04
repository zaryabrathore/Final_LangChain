import React, { useState, useEffect } from 'react';
import { Calendar, Mail, Clock, PlusCircle, Send, FileEdit, CheckCircle2, Video, Sparkles } from 'lucide-react';

export default function WorkspacePanel({ apiHost }) {
  const [activeSubTab, setActiveSubTab] = useState('calendar'); // 'calendar' | 'email' | 'schedule_notify'
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [mcpTools, setMcpTools] = useState([]);

  // Form states
  const [meetingSummary, setMeetingSummary] = useState('LangGraph & MCP Architecture Sync');
  const [meetingTime, setMeetingTime] = useState('2026-10-04T14:00:00Z');
  const [meetingDuration, setMeetingDuration] = useState(45);

  const [emailTo, setEmailTo] = useState('colleague@example.com');
  const [emailSubject, setEmailSubject] = useState('LangGraph MCP Integration Update');
  const [emailBody, setEmailBody] = useState('Hi,\n\nThe Google Calendar and Gmail MCP sub-agents are ready for testing.');

  const [scheduleEmail, setScheduleEmail] = useState('lead@example.com');
  const [scheduleSummary, setScheduleSummary] = useState('Sprint Planning & Demo');
  const [scheduleTime, setScheduleTime] = useState('2026-10-05T10:00:00Z');
  const [scheduleNote, setScheduleNote] = useState('Please bring your system architecture notes.');

  useEffect(() => {
    fetch(`${apiHost}/api/mcp/google/tools`)
      .then((res) => res.json())
      .then((data) => setMcpTools(data.tools || []))
      .catch(console.error);
  }, [apiHost]);

  const runMcpTool = async (toolName, args) => {
    setLoading(true);
    try {
      const res = await fetch(`${apiHost}/api/mcp/google/execute`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ tool_name: toolName, arguments: args }),
      });
      const data = await res.json();
      setResult(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleReadMeetings = () => {
    runMcpTool('calendar_read_meetings', { days_ahead: 7 });
  };

  const handleCreateMeeting = (e) => {
    e.preventDefault();
    runMcpTool('calendar_create_meeting', {
      summary: meetingSummary,
      start_time: meetingTime,
      duration_minutes: Number(meetingDuration),
      attendees: [emailTo]
    });
  };

  const handleDraftEmail = (e) => {
    e.preventDefault();
    runMcpTool('email_write_draft', {
      to_email: emailTo,
      subject: emailSubject,
      body: emailBody
    });
  };

  const handleSendEmail = (e) => {
    e.preventDefault();
    runMcpTool('email_send_now', {
      to_email: emailTo,
      subject: emailSubject,
      body: emailBody
    });
  };

  const handleScheduleAndNotify = (e) => {
    e.preventDefault();
    runMcpTool('schedule_meeting_and_notify', {
      recipient_email: scheduleEmail,
      meeting_summary: scheduleSummary,
      meeting_time: scheduleTime,
      email_note: scheduleNote
    });
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <Calendar className="w-5 h-5 text-emerald-400" />
            Sub-Agent 03: Google Workspace (Calendar & Gmail) MCP Sub-Agent
          </h2>
          <p className="text-xs text-slate-400">
            Read/Create Google Calendar meetings and draft/send emails or schedule meetings with automatic email notifications.
          </p>
        </div>
      </div>

      {/* Sub tabs */}
      <div className="flex items-center gap-2 bg-slate-900/80 p-1.5 rounded-xl border border-slate-800 w-fit">
        <button
          onClick={() => setActiveSubTab('calendar')}
          className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
            activeSubTab === 'calendar' ? 'bg-emerald-600 text-white shadow' : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          <Calendar className="w-3.5 h-3.5" />
          Google Calendar
        </button>
        <button
          onClick={() => setActiveSubTab('email')}
          className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
            activeSubTab === 'email' ? 'bg-emerald-600 text-white shadow' : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          <Mail className="w-3.5 h-3.5" />
          Gmail Draft & Send
        </button>
        <button
          onClick={() => setActiveSubTab('schedule_notify')}
          className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
            activeSubTab === 'schedule_notify' ? 'bg-emerald-600 text-white shadow' : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          <Sparkles className="w-3.5 h-3.5 text-amber-300" />
          Schedule Meeting & Auto Email
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Form Input Column */}
        <div className="lg:col-span-2 space-y-4">
          {activeSubTab === 'calendar' && (
            <div className="glass-panel p-5 space-y-4">
              <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                <h3 className="text-xs font-semibold text-slate-200 flex items-center gap-2">
                  <Calendar className="w-4 h-4 text-emerald-400" />
                  Google Calendar Actions
                </h3>
                <button
                  onClick={handleReadMeetings}
                  disabled={loading}
                  className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium transition-colors"
                >
                  Read Upcoming Meetings
                </button>
              </div>

              <form onSubmit={handleCreateMeeting} className="space-y-3">
                <div>
                  <label className="text-[11px] font-medium text-slate-400 block mb-1">Meeting Title / Summary</label>
                  <input
                    type="text"
                    value={meetingSummary}
                    onChange={(e) => setMeetingSummary(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-white"
                    required
                  />
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="text-[11px] font-medium text-slate-400 block mb-1">Start Time (ISO Timestamp)</label>
                    <input
                      type="text"
                      value={meetingTime}
                      onChange={(e) => setMeetingTime(e.target.value)}
                      className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs font-mono text-white"
                      required
                    />
                  </div>
                  <div>
                    <label className="text-[11px] font-medium text-slate-400 block mb-1">Duration (Minutes)</label>
                    <input
                      type="number"
                      value={meetingDuration}
                      onChange={(e) => setMeetingDuration(e.target.value)}
                      className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-white"
                    />
                  </div>
                </div>
                <button
                  type="submit"
                  disabled={loading}
                  className="w-full py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-medium text-xs transition-all shadow-md shadow-emerald-600/20"
                >
                  {loading ? 'Creating Meeting...' : 'Create Meeting on Google Calendar'}
                </button>
              </form>
            </div>
          )}

          {activeSubTab === 'email' && (
            <div className="glass-panel p-5 space-y-4">
              <h3 className="text-xs font-semibold text-slate-200 flex items-center gap-2 border-b border-slate-800 pb-2">
                <Mail className="w-4 h-4 text-emerald-400" />
                Gmail Draft & Automated Email Actions
              </h3>
              <form className="space-y-3">
                <div>
                  <label className="text-[11px] font-medium text-slate-400 block mb-1">Recipient Email Address</label>
                  <input
                    type="email"
                    value={emailTo}
                    onChange={(e) => setEmailTo(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-white"
                    required
                  />
                </div>
                <div>
                  <label className="text-[11px] font-medium text-slate-400 block mb-1">Subject Line</label>
                  <input
                    type="text"
                    value={emailSubject}
                    onChange={(e) => setEmailSubject(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-white"
                    required
                  />
                </div>
                <div>
                  <label className="text-[11px] font-medium text-slate-400 block mb-1">Email Content Body</label>
                  <textarea
                    rows={4}
                    value={emailBody}
                    onChange={(e) => setEmailBody(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-white"
                  />
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <button
                    type="button"
                    onClick={handleDraftEmail}
                    disabled={loading}
                    className="py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-200 font-medium text-xs transition-colors flex items-center justify-center gap-1.5"
                  >
                    <FileEdit className="w-3.5 h-3.5 text-amber-400" />
                    Save Draft Email
                  </button>
                  <button
                    type="button"
                    onClick={handleSendEmail}
                    disabled={loading}
                    className="py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-medium text-xs transition-colors shadow-md shadow-emerald-600/20 flex items-center justify-center gap-1.5"
                  >
                    <Send className="w-3.5 h-3.5" />
                    Send Email Now
                  </button>
                </div>
              </form>
            </div>
          )}

          {activeSubTab === 'schedule_notify' && (
            <div className="glass-panel p-5 space-y-4">
              <h3 className="text-xs font-semibold text-amber-300 flex items-center gap-2 border-b border-slate-800 pb-2">
                <Sparkles className="w-4 h-4 text-amber-400" />
                Schedule Calendar Meeting & Automatically Send Email Invitation
              </h3>
              <form onSubmit={handleScheduleAndNotify} className="space-y-3">
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="text-[11px] font-medium text-slate-400 block mb-1">Recipient Email</label>
                    <input
                      type="email"
                      value={scheduleEmail}
                      onChange={(e) => setScheduleEmail(e.target.value)}
                      className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-white"
                      required
                    />
                  </div>
                  <div>
                    <label className="text-[11px] font-medium text-slate-400 block mb-1">Meeting Summary</label>
                    <input
                      type="text"
                      value={scheduleSummary}
                      onChange={(e) => setScheduleSummary(e.target.value)}
                      className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-white"
                      required
                    />
                  </div>
                </div>
                <div>
                  <label className="text-[11px] font-medium text-slate-400 block mb-1">Schedule Time (ISO Format)</label>
                  <input
                    type="text"
                    value={scheduleTime}
                    onChange={(e) => setScheduleTime(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs font-mono text-white"
                    required
                  />
                </div>
                <div>
                  <label className="text-[11px] font-medium text-slate-400 block mb-1">Additional Email Note</label>
                  <input
                    type="text"
                    value={scheduleNote}
                    onChange={(e) => setScheduleNote(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-white"
                  />
                </div>
                <button
                  type="submit"
                  disabled={loading}
                  className="w-full py-2.5 rounded-xl bg-gradient-to-r from-emerald-600 via-teal-600 to-cyan-600 hover:from-emerald-500 hover:to-cyan-500 text-white font-medium text-xs transition-all shadow-lg shadow-emerald-600/20"
                >
                  {loading ? 'Processing Schedule & Auto Email...' : 'Schedule Meeting & Send Email Invitation'}
                </button>
              </form>
            </div>
          )}

          {/* Execution Result Box */}
          {result && (
            <div className="glass-panel p-5 space-y-3">
              <h4 className="text-xs font-semibold text-emerald-400 uppercase tracking-wider flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4" />
                Google Workspace MCP Execution Result ({result.tool_name})
              </h4>
              <pre className="p-3 rounded-xl bg-slate-950 border border-slate-800 text-[11px] text-emerald-300 font-mono overflow-x-auto max-h-60">
                {JSON.stringify(result.result, null, 2)}
              </pre>
            </div>
          )}
        </div>

        {/* MCP Tools Column */}
        <div className="glass-panel p-5 space-y-3">
          <h3 className="text-xs font-semibold text-slate-300 uppercase tracking-wider flex items-center gap-2 border-b border-slate-800 pb-2">
            <Calendar className="w-4 h-4 text-emerald-400" />
            Workspace MCP Tool Schemas ({mcpTools.length})
          </h3>
          <div className="space-y-2 max-h-[450px] overflow-y-auto pr-1">
            {mcpTools.map((tool, idx) => (
              <div key={idx} className="p-3 rounded-xl bg-slate-950/60 border border-slate-800/80 space-y-1">
                <span className="text-xs font-mono text-emerald-400 font-semibold block">{tool.name}</span>
                <p className="text-[11px] text-slate-400">{tool.description}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
