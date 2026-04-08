// src/app/pages/HistoryPage.tsx
//
// Shows a table of every past analysis that was saved to Supabase.
// This page fetches data directly from the database when it loads.

import { useEffect, useState } from 'react';
import { Shield, ArrowLeft, Clock, AlertTriangle, CheckCircle, XCircle, Video, Link as LinkIcon } from 'lucide-react';
import { supabase } from '../../lib/supabaseClient';

// ── Type that matches exactly one row from our analysis_logs table ──────────
interface LogRow {
  id: number;
  created_at: string;       // ISO timestamp, e.g. "2025-04-08T10:30:00Z"
  analysis_type: string;    // 'video' or 'url'
  content_type: string;     // 'investment', 'job', etc.
  risk_level: string;       // 'low', 'medium', 'high'
  risk_score: number;       // 0–100
}

// ── Props: we only need a callback to go back to the main page ──────────────
interface Props {
  onBack: () => void;
}

export default function HistoryPage({ onBack }: Props) {
  // logs — the array of rows fetched from Supabase
  const [logs, setLogs] = useState<LogRow[]>([]);

  // loading — true while the database request is in-flight
  const [loading, setLoading] = useState(true);

  // error — a message to show if the fetch fails
  const [error, setError] = useState<string | null>(null);

  // ── Fetch history when this page first loads ────────────────────────────
  // useEffect with an empty [] runs ONCE, right after the component mounts.
  // This is the standard React pattern for "do something when the page opens".
  useEffect(() => {
    async function fetchHistory() {
      try {
        const { data, error } = await supabase
          .from('analysis_logs')          // which table to read from
          .select('id, created_at, analysis_type, content_type, risk_level, risk_score')
          .order('created_at', { ascending: false })  // newest first
          .limit(100);                    // don't load thousands of rows

        if (error) throw error;

        // data is either an array of rows, or null if the table is empty.
        setLogs(data ?? []);
      } catch (err: any) {
        console.error('Failed to fetch history:', err);
        setError('Could not load history. Check that Supabase is configured correctly.');
      } finally {
        // Always turn off the loading spinner, success or failure.
        setLoading(false);
      }
    }

    fetchHistory();
  }, []); // The [] means: run this effect only once on mount, not on every re-render.

  // ── Helper: compute summary counts from the logs array ─────────────────
  // .filter() returns a new array with only the rows that match the condition.
  const total  = logs.length;
  const high   = logs.filter(l => l.risk_level === 'high').length;
  const medium = logs.filter(l => l.risk_level === 'medium').length;
  const low    = logs.filter(l => l.risk_level === 'low').length;

  // ── Helper: format "2025-04-08T10:30:00Z" → "08 Apr 2025, 10:30" ───────
  function formatDate(iso: string) {
    return new Date(iso).toLocaleString('en-MY', {
      day: '2-digit', month: 'short', year: 'numeric',
      hour: '2-digit', minute: '2-digit',
    });
  }

  // ── Helper: turn risk level string into a coloured badge ─────────────────
  function RiskBadge({ level }: { level: string }) {
    // Map each risk level to a Tailwind colour class
    const styles: Record<string, string> = {
      high:   'bg-red-500/20 text-red-400 border border-red-500/40',
      medium: 'bg-yellow-500/20 text-yellow-400 border border-yellow-500/40',
      low:    'bg-green-500/20 text-green-400 border border-green-500/40',
    };
    const icons: Record<string, JSX.Element> = {
      high:   <XCircle     className="w-3 h-3" />,
      medium: <AlertTriangle className="w-3 h-3" />,
      low:    <CheckCircle className="w-3 h-3" />,
    };
    return (
      <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium capitalize ${styles[level] ?? styles.medium}`}>
        {icons[level]}
        {level}
      </span>
    );
  }

  // ── Helper: icon for video vs url ─────────────────────────────────────────
  function TypeIcon({ type }: { type: string }) {
    return type === 'video'
      ? <Video   className="w-4 h-4 text-purple-400" />
      : <LinkIcon className="w-4 h-4 text-blue-400" />;
  }

  // ── Helper: capitalise the content type label ────────────────────────────
  function formatContentType(ct: string) {
    const labels: Record<string, string> = {
      investment: 'Investment',
      job:        'Job Offer',
      health:     'Health',
      news:       'News',
      general:    'General',
    };
    return labels[ct] ?? ct;
  }

  // ─── JSX ──────────────────────────────────────────────────────────────────
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900 p-6">
      <div className="max-w-6xl mx-auto">

        {/* ── Header ──────────────────────────────────────────────────────── */}
        <div className="flex items-center gap-4 mb-8 pt-8">
          {/* Back button — calls onBack() which switches the view in App.tsx */}
          <button
            onClick={onBack}
            className="flex items-center gap-2 text-blue-400 hover:text-white transition-colors text-sm"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to Analysis
          </button>

          <div className="flex items-center gap-3">
            <div className="p-2 bg-blue-500/20 rounded-xl">
              <Shield className="w-6 h-6 text-blue-400" />
            </div>
            <div>
              <h1 className="text-2xl text-white">Analysis History</h1>
              <p className="text-blue-400 text-sm">All past scam detection reports</p>
            </div>
          </div>
        </div>

        {/* ── Loading state ─────────────────────────────────────────────── */}
        {loading && (
          <div className="text-center py-20 text-blue-300">
            <Clock className="w-8 h-8 mx-auto mb-3 animate-spin" />
            <p>Loading history...</p>
          </div>
        )}

        {/* ── Error state ───────────────────────────────────────────────── */}
        {!loading && error && (
          <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-6 text-red-400 text-center">
            <AlertTriangle className="w-8 h-8 mx-auto mb-2" />
            <p>{error}</p>
            <p className="text-sm mt-2 text-red-300">
              Make sure VITE_SUPABASE_URL and VITE_SUPABASE_KEY are set in your frontend .env file.
            </p>
          </div>
        )}

        {/* ── Main content (only shown when loaded successfully) ────────── */}
        {!loading && !error && (
          <>
            {/* ── Summary cards row ─────────────────────────────────────── */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-6">
              {[
                { label: 'Total Scans',  value: total,  color: 'text-blue-400',   bg: 'bg-blue-500/10 border-blue-500/30' },
                { label: 'High Risk',    value: high,   color: 'text-red-400',    bg: 'bg-red-500/10 border-red-500/30' },
                { label: 'Medium Risk',  value: medium, color: 'text-yellow-400', bg: 'bg-yellow-500/10 border-yellow-500/30' },
                { label: 'Low Risk',     value: low,    color: 'text-green-400',  bg: 'bg-green-500/10 border-green-500/30' },
              ].map(card => (
                <div key={card.label} className={`rounded-xl border p-4 ${card.bg}`}>
                  <p className={`text-3xl font-bold ${card.color}`}>{card.value}</p>
                  <p className="text-gray-400 text-sm mt-1">{card.label}</p>
                </div>
              ))}
            </div>

            {/* ── Empty state ───────────────────────────────────────────── */}
            {logs.length === 0 && (
              <div className="text-center py-20 text-gray-400">
                <Shield className="w-12 h-12 mx-auto mb-4 opacity-30" />
                <p className="text-lg">No analyses yet.</p>
                <p className="text-sm mt-1">Run your first analysis and it will appear here.</p>
              </div>
            )}

            {/* ── History table ─────────────────────────────────────────── */}
            {logs.length > 0 && (
              <div className="bg-white/5 border border-white/10 rounded-2xl overflow-hidden">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-white/10 text-gray-400 text-xs uppercase tracking-wider">
                      <th className="text-left px-6 py-4">Date & Time</th>
                      <th className="text-left px-6 py-4">Type</th>
                      <th className="text-left px-6 py-4">Category</th>
                      <th className="text-left px-6 py-4">Risk Level</th>
                      <th className="text-right px-6 py-4">AI Score</th>
                    </tr>
                  </thead>
                  <tbody>
                    {/* .map() loops over every row and renders a <tr> for it */}
                    {logs.map((log, index) => (
                      <tr
                        key={log.id}
                        // Alternate row background for readability
                        className={`border-b border-white/5 hover:bg-white/5 transition-colors ${
                          index % 2 === 0 ? '' : 'bg-white/[0.02]'
                        }`}
                      >
                        {/* Date/time column */}
                        <td className="px-6 py-4 text-gray-300 whitespace-nowrap">
                          <div className="flex items-center gap-2">
                            <Clock className="w-3 h-3 text-gray-500" />
                            {formatDate(log.created_at)}
                          </div>
                        </td>

                        {/* Analysis type column (video or url icon) */}
                        <td className="px-6 py-4">
                          <div className="flex items-center gap-2 text-gray-300 capitalize">
                            <TypeIcon type={log.analysis_type} />
                            {log.analysis_type}
                          </div>
                        </td>

                        {/* Content category column */}
                        <td className="px-6 py-4 text-gray-300">
                          {formatContentType(log.content_type)}
                        </td>

                        {/* Risk level badge column */}
                        <td className="px-6 py-4">
                          <RiskBadge level={log.risk_level} />
                        </td>

                        {/* AI score column — coloured number */}
                        <td className="px-6 py-4 text-right">
                          <span className={`font-bold text-base ${
                            log.risk_score >= 65 ? 'text-red-400'
                            : log.risk_score >= 35 ? 'text-yellow-400'
                            : 'text-green-400'
                          }`}>
                            {log.risk_score}
                            <span className="text-gray-500 text-xs font-normal">/100</span>
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </>
        )}

      </div>
    </div>
  );
}
