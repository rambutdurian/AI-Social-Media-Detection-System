import React, { useEffect, useState } from 'react'
import { supabase } from '../lib/supabase'

interface HistoryRecord {
  id: string
  created_at: string
  file_name: string | null
  source_url: string | null
  risk_score: number
  risk_level: string
  risk_label: string
  confidence: number
  analysis_time: number
}

interface FullRecord {
  id: string
  risk_score: number
  trust_score: number
  confidence: number
  risk_level: string
  risk_label: string
  explainable_findings: string[]
  signal_breakdown: Record<string, unknown>
  what_to_do: Record<string, string[]>
  analysis_time: number
  frames_analyzed: number
  file_name: string | null
}

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000'

export default function HistoryPage() {
  const [history, setHistory] = useState<HistoryRecord[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedRecord, setSelectedRecord] = useState<FullRecord | null>(null)
  const [modalLoading, setModalLoading] = useState(false)
  const [downloadingId, setDownloadingId] = useState<string | null>(null)

  useEffect(() => { fetchHistory() }, [])

  const fetchHistory = async () => {
    setLoading(true)
    setError(null)
    try {
      const { data, error } = await supabase
        .from('analyses')
        .select('id, created_at, file_name, source_url, risk_score, risk_level, risk_label, confidence, analysis_time')
        .order('created_at', { ascending: false })
        .limit(50)
      if (error) throw error
      setHistory(data || [])
    } catch {
      setError('Could not load history. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const handleView = async (id: string) => {
    setModalLoading(true)
    try {
      const { data, error } = await supabase
        .from('analyses')
        .select('*')
        .eq('id', id)
        .single()
      if (error) throw error
      setSelectedRecord(data)
    } catch {
      alert('Could not load this analysis.')
    } finally {
      setModalLoading(false)
    }
  }

  const handleDownload = async (id: string) => {
    setDownloadingId(id)
    try {
      const res = await fetch(`${API_URL}/report/${id}`)
      if (!res.ok) throw new Error('Download failed')
      const blob = await res.blob()
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `frauda-report-${id.slice(0, 8)}.pdf`
      a.click()
      URL.revokeObjectURL(url)
    } catch {
      alert('Could not download report. Please try again.')
    } finally {
      setDownloadingId(null)
    }
  }

  const riskBadge = (level: string) => {
    if (level === 'high') return 'bg-red-100 text-red-700 border border-red-200'
    if (level === 'moderate') return 'bg-yellow-100 text-yellow-700 border border-yellow-200'
    return 'bg-green-100 text-green-700 border border-green-200'
  }

  const fmtDate = (iso: string) =>
    new Date(iso).toLocaleDateString('en-MY', {
      day: 'numeric', month: 'short', year: 'numeric',
      hour: '2-digit', minute: '2-digit',
    })

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-6xl mx-auto">

        {/* Header */}
        <div className="mb-6 flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Analysis History</h1>
            <p className="text-sm text-gray-500 mt-1">
              Past video analyses — view or download reports without re-analyzing
            </p>
          </div>
          <button onClick={fetchHistory} className="text-sm text-blue-600 hover:underline">
            Refresh
          </button>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4">
            {error}
          </div>
        )}

        {loading ? (
          <div className="text-center py-20 text-gray-400">Loading history...</div>
        ) : history.length === 0 ? (
          <div className="text-center py-20 text-gray-400">
            No analyses yet. Upload a video to get started.
          </div>
        ) : (
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  {['Date', 'Source', 'Risk Level', 'Score', 'Confidence', 'Actions'].map(h => (
                    <th key={h} className="px-4 py-3 text-left font-semibold text-gray-600">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {history.map((rec, i) => (
                  <tr key={rec.id} className={i % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                    <td className="px-4 py-3 text-gray-600 whitespace-nowrap">{fmtDate(rec.created_at)}</td>
                    <td className="px-4 py-3 text-gray-800 max-w-xs truncate">
                      {rec.file_name || rec.source_url || 'Unknown'}
                    </td>
                    <td className="px-4 py-3">
                      <span className={`px-2 py-1 rounded-full text-xs font-semibold ${riskBadge(rec.risk_level)}`}>
                        {rec.risk_label}
                      </span>
                    </td>
                    <td className="px-4 py-3 font-mono font-semibold text-gray-800">{rec.risk_score}/100</td>
                    <td className="px-4 py-3 text-gray-600">{rec.confidence}%</td>
                    <td className="px-4 py-3">
                      <div className="flex gap-2">
                        <button
                          onClick={() => handleView(rec.id)}
                          className="px-3 py-1 bg-blue-600 text-white text-xs rounded hover:bg-blue-700 transition"
                        >
                          View
                        </button>
                        <button
                          onClick={() => handleDownload(rec.id)}
                          disabled={downloadingId === rec.id}
                          className="px-3 py-1 bg-gray-100 text-gray-700 text-xs rounded hover:bg-gray-200 transition disabled:opacity-50"
                        >
                          {downloadingId === rec.id ? '...' : 'PDF'}
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* View Modal */}
      {(selectedRecord || modalLoading) && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            {modalLoading ? (
              <div className="p-10 text-center text-gray-400">Loading analysis...</div>
            ) : selectedRecord && (
              <div className="p-6">
                <div className="flex justify-between items-center mb-4">
                  <h2 className="text-xl font-bold text-gray-900">Analysis Result</h2>
                  <button onClick={() => setSelectedRecord(null)} className="text-gray-400 hover:text-gray-600 text-xl">✕</button>
                </div>

                <div className="grid grid-cols-3 gap-4 mb-6">
                  <div className="bg-gray-50 rounded-lg p-4 text-center">
                    <div className="text-3xl font-bold text-blue-600">{selectedRecord.trust_score}</div>
                    <div className="text-xs text-gray-500 mt-1">Trust Score</div>
                  </div>
                  <div className="bg-gray-50 rounded-lg p-4 text-center">
                    <div className="text-3xl font-bold text-gray-800">{selectedRecord.risk_score}</div>
                    <div className="text-xs text-gray-500 mt-1">AI Risk Score</div>
                  </div>
                  <div className="bg-gray-50 rounded-lg p-4 text-center">
                    <span className={`text-sm font-bold px-3 py-1 rounded-full ${riskBadge(selectedRecord.risk_level)}`}>
                      {selectedRecord.risk_label}
                    </span>
                    <div className="text-xs text-gray-500 mt-2">Risk Level</div>
                  </div>
                </div>

                {selectedRecord.explainable_findings?.length > 0 && (
                  <div className="mb-4">
                    <h3 className="font-semibold text-gray-800 mb-2">Forensic Findings</h3>
                    <ul className="space-y-1">
                      {selectedRecord.explainable_findings.map((f, i) => (
                        <li key={i} className="text-sm text-gray-600 flex gap-2">
                          <span className="text-red-500">⚠</span>{f}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                <div className="flex justify-end gap-3 mt-6 pt-4 border-t">
                  <button
                    onClick={() => handleDownload(selectedRecord.id)}
                    className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700 transition"
                  >
                    Download PDF Report
                  </button>
                  <button
                    onClick={() => setSelectedRecord(null)}
                    className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg text-sm hover:bg-gray-200 transition"
                  >
                    Close
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
