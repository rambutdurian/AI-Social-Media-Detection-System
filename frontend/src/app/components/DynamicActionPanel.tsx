// DynamicActionPanel.tsx
// Renders the LLM-generated scenario analysis (A, B, or C) from the backend.
//
// Scenario A — Investment scam: shows verdict, riskSummary, officialSources links
// Scenario B — General AI content: shows verdict, riskSummary
// Scenario C — Identity/impersonation: shows identityTrustScore, identityEvidence
// All scenarios: shows whatToDo (DON'T / DO / Verify Through) and explainableFindings

import {
  Shield, XCircle, CheckCircle, BadgeCheck, Ban, ArrowRight,
  Eye, AlertTriangle, ExternalLink, UserX, TrendingUp,
} from 'lucide-react';

interface WhatToDo {
  dontDo: string[];
  shouldDo: string[];
  verifyThrough: string[];
}

interface OfficialSource {
  name: string;
  url: string;
}

interface DynamicActionPanelProps {
  scenario?: 'A' | 'B' | 'C';
  verdict?: string;
  riskSummary?: string;
  whatToDo?: WhatToDo;
  officialSources?: OfficialSource[];
  identityTrustScore?: number;
  identityEvidence?: string[];
  explainableFindings?: string[];
}

// ── Colour helpers ────────────────────────────────────────────────────────────
// Each scenario gets a distinct accent colour so judges instantly see which
// route the LLM took.
const SCENARIO_STYLE: Record<string, { label: string; headerBg: string; accent: string }> = {
  A: {
    label:    'Investment Scam Detected',
    headerBg: 'from-red-700 via-orange-700 to-red-700',
    accent:   'text-orange-300',
  },
  B: {
    label:    'AI-Generated Content',
    headerBg: 'from-blue-700 via-indigo-700 to-blue-700',
    accent:   'text-blue-300',
  },
  C: {
    label:    'Identity Impersonation Alert',
    headerBg: 'from-purple-700 via-fuchsia-700 to-purple-700',
    accent:   'text-fuchsia-300',
  },
};

// ── Trust score ring colour ───────────────────────────────────────────────────
// Used in Scenario C to show how trustworthy the identity is (lower = more suspicious)
function getTrustRingColor(score: number) {
  if (score > 70) return 'text-green-400 border-green-400';
  if (score > 40) return 'text-yellow-400 border-yellow-400';
  return 'text-red-400 border-red-400';
}

export function DynamicActionPanel({
  scenario = 'B',
  verdict,
  riskSummary,
  whatToDo,
  officialSources = [],
  identityTrustScore,
  identityEvidence = [],
  explainableFindings = [],
}: DynamicActionPanelProps) {

  const style = SCENARIO_STYLE[scenario] ?? SCENARIO_STYLE['B'];

  return (
    <div className="space-y-6 animate-in fade-in duration-500">

      {/* ── Verdict banner ──────────────────────────────────────────────────── */}
      <div className={`bg-gradient-to-r ${style.headerBg} rounded-2xl shadow-2xl p-6 text-white`}>
        <div className="flex items-center gap-3 mb-3">
          <Shield className="w-7 h-7" />
          <span className="text-sm font-semibold uppercase tracking-widest opacity-80">
            {style.label}
          </span>
        </div>
        {verdict && (
          <p className="text-xl font-bold leading-snug mb-2">{verdict}</p>
        )}
        {riskSummary && (
          <p className="text-sm opacity-90 leading-relaxed">{riskSummary}</p>
        )}
      </div>

      {/* ── Scenario C: Identity Trust Score ────────────────────────────────── */}
      {/* Only shown when a known public figure may have been impersonated.      */}
      {/* A low identity trust score (< 40) means the face is likely NOT real.  */}
      {scenario === 'C' && identityTrustScore !== undefined && (
        <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-6 border border-fuchsia-500/30">
          <div className="flex items-center gap-3 mb-4">
            <UserX className="w-6 h-6 text-fuchsia-400" />
            <h3 className="text-white font-semibold">Identity Trust Analysis</h3>
          </div>
          <div className="flex items-center gap-6">
            {/* Circular badge showing the trust score */}
            <div
              className={`w-20 h-20 rounded-full border-4 flex flex-col items-center justify-center shrink-0 ${getTrustRingColor(identityTrustScore)}`}
            >
              <span className="text-2xl font-bold">{identityTrustScore}</span>
              <span className="text-xs opacity-70">/100</span>
            </div>
            <div className="flex-1">
              <p className="text-sm text-slate-300 mb-1">
                Identity Trust Score — lower means the identity is more likely fabricated.
              </p>
              {/* List of visual evidence that triggered the impersonation alert */}
              {identityEvidence.length > 0 && (
                <ul className="space-y-1 mt-2">
                  {identityEvidence.map((ev, i) => (
                    <li key={i} className="text-xs text-slate-300 flex gap-2">
                      <AlertTriangle className="w-3.5 h-3.5 text-fuchsia-400 mt-0.5 shrink-0" />
                      {ev}
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </div>
        </div>
      )}

      {/* ── What Should I Do? panel ──────────────────────────────────────────── */}
      {whatToDo && (
        <div className={`bg-gradient-to-r ${style.headerBg} rounded-2xl shadow-2xl p-8 text-white`}>
          <h2 className="mb-6 flex items-center gap-3 text-2xl">
            <Shield className="w-8 h-8" />
            What Should I Do?
          </h2>

          <div className="grid md:grid-cols-3 gap-6">
            {/* DON'T DO */}
            <div className="bg-white/10 backdrop-blur rounded-xl p-6">
              <div className="flex items-center gap-2 mb-4">
                <XCircle className="w-6 h-6" />
                <h3 className="text-lg font-semibold">DON'T</h3>
              </div>
              <ul className="space-y-2">
                {(whatToDo.dontDo ?? []).map((item, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm">
                    <Ban className="w-4 h-4 shrink-0 mt-0.5" />
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            </div>

            {/* SHOULD DO */}
            <div className="bg-white/10 backdrop-blur rounded-xl p-6">
              <div className="flex items-center gap-2 mb-4">
                <CheckCircle className="w-6 h-6" />
                <h3 className="text-lg font-semibold">DO</h3>
              </div>
              <ul className="space-y-2">
                {(whatToDo.shouldDo ?? []).map((item, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm">
                    <ArrowRight className="w-4 h-4 shrink-0 mt-0.5" />
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            </div>

            {/* VERIFY THROUGH */}
            <div className="bg-white/10 backdrop-blur rounded-xl p-6">
              <div className="flex items-center gap-2 mb-4">
                <BadgeCheck className="w-6 h-6" />
                <h3 className="text-lg font-semibold">Verify Through</h3>
              </div>
              <ul className="space-y-2">
                {(whatToDo.verifyThrough ?? []).map((item, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm">
                    <Shield className="w-4 h-4 shrink-0 mt-0.5" />
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}

      {/* ── Scenario A: Official Sources ─────────────────────────────────────── */}
      {/* Clickable links to SC Malaysia and BNM — shown only for investment scam */}
      {scenario === 'A' && officialSources.length > 0 && (
        <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-6 border border-orange-500/30">
          <div className="flex items-center gap-3 mb-4">
            <TrendingUp className="w-6 h-6 text-orange-400" />
            <h3 className="text-white font-semibold">Official Malaysian Sources</h3>
          </div>
          <ul className="space-y-3">
            {officialSources.map((src, i) => (
              <li key={i}>
                {/* rel="noopener noreferrer" prevents the new tab from accessing
                    window.opener — a basic security best practice for external links */}
                <a
                  href={src.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-3 p-3 bg-white/5 rounded-lg border border-white/10 hover:bg-orange-500/10 hover:border-orange-400/30 transition-all group"
                >
                  <ExternalLink className="w-4 h-4 text-orange-400 shrink-0" />
                  <span className="text-sm text-slate-200 group-hover:text-white">{src.name}</span>
                </a>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* ── Explainable Findings ─────────────────────────────────────────────── */}
      {explainableFindings.length > 0 && (
        <div className="bg-white/10 backdrop-blur-lg rounded-2xl shadow-2xl p-8 border border-white/20">
          <h2 className="mb-6 flex items-center gap-2 text-white text-2xl">
            <Eye className="w-7 h-7 text-blue-400" />
            Why This Looks Suspicious
          </h2>
          <p className="text-gray-300 mb-4">Here's what our AI detected in plain language:</p>
          <ul className="space-y-3">
            {explainableFindings.map((item, i) => (
              <li
                key={i}
                className="flex items-start gap-3 p-4 bg-white/5 rounded-lg border border-white/10 hover:bg-white/10 hover:border-blue-400/30 hover:translate-x-2 transition-all duration-300 animate-in fade-in slide-in-from-left"
                style={{ animationDelay: `${i * 100}ms` }}
              >
                <span className="w-7 h-7 bg-blue-500/20 text-blue-400 rounded-full flex items-center justify-center shrink-0 mt-0.5 text-sm font-semibold">
                  {i + 1}
                </span>
                <span className="text-gray-200">{item}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
