import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { copilotApi } from '../services/copilotApi';
import { CopilotResponse } from '../types';
import { GlassCard } from '../components/ui/GlassCard';
import { BrutalButton } from '../components/ui/BrutalButton';
import { AIInsightCard } from '../components/ui/AIInsightCard';
import { StatusBadge } from '../components/ui/StatusBadge';
import { useToast } from '../context/ToastContext';
import {
  Sparkles,
  ShieldCheck,
  Database,
  Lock,
  ExternalLink,
  FileCheck,
  Zap,
} from 'lucide-react';

export const AIPage: React.FC = () => {
  const navigate = useNavigate();
  const { showToast } = useToast();

  const [question, setQuestion] = useState('Which deals need immediate follow-up attention?');
  const [response, setResponse] = useState<CopilotResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleAsk = async (queryToRun?: string) => {
    const targetQuery = queryToRun || question;
    if (!targetQuery.trim()) return;

    setIsLoading(true);
    try {
      const res = await copilotApi.chat({ message: targetQuery.trim() });
      setResponse(res);
      showToast('AI Sales Copilot analysis completed.', 'success');
    } catch (err: any) {
      showToast(err.message || 'Failed to communicate with AI Copilot service.', 'error');
    } finally {
      setIsLoading(false);
    }
  };

  const presetQueries = [
    { label: 'Deals Needing Attention', query: 'Which deals need immediate attention?' },
    { label: 'Pipeline Summary', query: 'Summarize my open sales pipeline and revenue forecast.' },
    { label: 'Commercial Risks', query: 'Show all deals with high discount risk or low margin.' },
    { label: 'Pending Approvals', query: 'Which quotations are currently waiting for commercial approval?' },
    { label: 'Cooling Customers', query: 'Which customer accounts are going cold or inactive?' },
    { label: 'Product Upsells', query: 'Which products should we recommend for cross-selling?' },
  ];

  return (
    <div className="space-y-8 max-w-4xl mx-auto">
      {/* Page Header */}
      <div>
        <div className="flex items-center gap-2 text-indigo-400 font-mono text-xs font-bold uppercase tracking-widest">
          <Sparkles className="w-4 h-4 animate-pulse" />
          <span>Phase 26–30 — AI Sales Intelligence Copilot</span>
        </div>
        <h1 className="text-3xl font-black text-slate-100 tracking-tight mt-1">Ask DealFlow360</h1>
        <p className="text-xs text-slate-400 font-mono mt-1">
          Intent-routed sales intelligence, grounded commercial facts, and explainable recommendations
        </p>
      </div>

      {/* Query Bar */}
      <GlassCard className="border-2 border-indigo-500/40 p-6 shadow-glass-glow">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleAsk();
          }}
          className="space-y-4"
        >
          <div className="relative">
            <textarea
              rows={3}
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="Ask DealFlow360 anything about deals, pipeline, pricing, discounts, margins, or approvals..."
              className="w-full px-4 py-3 bg-slate-950/90 border border-slate-700/80 rounded-xl text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 text-sm font-mono"
            />
          </div>

          <div className="flex flex-wrap items-center justify-between gap-3">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-[10px] font-mono font-bold text-slate-400 uppercase">Shortcuts:</span>
              {presetQueries.map((pq, idx) => (
                <button
                  key={idx}
                  type="button"
                  onClick={() => {
                    setQuestion(pq.query);
                    handleAsk(pq.query);
                  }}
                  className="px-2.5 py-1 rounded-lg bg-slate-800/80 hover:bg-indigo-950 text-slate-300 hover:text-indigo-300 text-[11px] font-mono border border-slate-700/60 transition"
                >
                  {pq.label}
                </button>
              ))}
            </div>

            <BrutalButton type="submit" variant="ai" isLoading={isLoading}>
              ✦ Run AI Copilot Query
            </BrutalButton>
          </div>
        </form>
      </GlassCard>

      {/* Response Panel */}
      {response && (
        <AIInsightCard
          title={`Sales Intelligence Analysis — Intent: ${response.intent}`}
          provider={response.metadata.provider}
          model={response.metadata.model}
        >
          <div className="space-y-6">
            {/* Intent Badge */}
            <div className="flex items-center gap-2">
              <span className="text-[10px] font-mono font-bold text-slate-400 uppercase">Detected Intent:</span>
              <StatusBadge status={response.intent.toLowerCase()} size="sm" />
            </div>

            {/* Main AI Response Body */}
            <div className="p-4 bg-slate-950/80 rounded-xl border border-indigo-500/30 text-slate-200 text-sm leading-relaxed font-mono whitespace-pre-wrap">
              {response.answer}
            </div>

            {/* Evidence Telemetry Section */}
            {response.evidence.length > 0 && (
              <div className="space-y-2 pt-2 border-t border-slate-800">
                <div className="flex items-center gap-2 text-xs font-mono font-bold text-indigo-400 uppercase tracking-wider">
                  <FileCheck className="w-3.5 h-3.5" />
                  <span>Grounded Evidence Telemetry ({response.evidence.length})</span>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                  {response.evidence.map((ev, i) => (
                    <div key={i} className="p-2.5 rounded-lg bg-slate-900/80 border border-slate-800 text-xs font-mono flex items-start justify-between gap-2">
                      <div>
                        <span className="font-bold text-slate-200 block">{ev.label}</span>
                        {ev.detail && <span className="text-[10px] text-slate-400 block">{ev.detail}</span>}
                      </div>
                      <span className="px-2 py-0.5 rounded bg-indigo-500/20 text-indigo-300 font-bold text-[11px] shrink-0 border border-indigo-500/30">
                        {ev.value}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Actionable Recommendations Section */}
            {response.recommendations.length > 0 && (
              <div className="space-y-2 pt-2 border-t border-slate-800">
                <div className="flex items-center gap-2 text-xs font-mono font-bold text-amber-400 uppercase tracking-wider">
                  <Zap className="w-3.5 h-3.5" />
                  <span>Recommended Sales Actions</span>
                </div>
                <ul className="space-y-1.5 font-mono text-xs text-slate-300">
                  {response.recommendations.map((rec, i) => (
                    <li key={i} className="flex items-start gap-2 p-2 rounded bg-amber-500/10 border border-amber-500/20">
                      <span className="text-amber-400 font-bold">•</span>
                      <span>{rec}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Referenced Entities Navigation */}
            {response.referenced_deal_ids.length > 0 && (
              <div className="pt-2 border-t border-slate-800">
                <span className="text-[10px] font-mono font-bold text-indigo-400 uppercase tracking-widest block mb-2">
                  Referenced Opportunities:
                </span>
                <div className="flex items-center gap-2 flex-wrap">
                  {response.referenced_deal_ids.map((dealId) => (
                    <BrutalButton
                      key={dealId}
                      size="sm"
                      variant="ghost"
                      icon={ExternalLink}
                      onClick={() => navigate(`/deals/${dealId}`)}
                    >
                      Deal {dealId.substring(0, 8)}...
                    </BrutalButton>
                  ))}
                </div>
              </div>
            )}

            <div className="flex items-center justify-between text-[11px] font-mono text-slate-400 pt-2 border-t border-slate-800">
              <span>Grounding: Tenant Isolated Factual Context</span>
              <span>Timestamp: {new Date(response.metadata.generated_at).toLocaleTimeString()}</span>
            </div>
          </div>
        </AIInsightCard>
      )}

      {/* Architecture & Security Principles Banner */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-4 border-t border-slate-800 text-xs font-mono text-slate-400">
        <div className="p-4 bg-slate-900/60 border border-slate-800 rounded-xl flex items-start gap-3">
          <ShieldCheck className="w-5 h-5 text-emerald-400 shrink-0 mt-0.5" />
          <div>
            <span className="font-bold text-slate-200 block mb-0.5">Prompt Injection Defense</span>
            <span>Context boundary tags isolate untrusted business data from AI instructions.</span>
          </div>
        </div>

        <div className="p-4 bg-slate-900/60 border border-slate-800 rounded-xl flex items-start gap-3">
          <Database className="w-5 h-5 text-sky-400 shrink-0 mt-0.5" />
          <div>
            <span className="font-bold text-slate-200 block mb-0.5">Deterministic Business Rules</span>
            <span>Pricing, Margins & Approvals remain calculated by authoritative backend engines.</span>
          </div>
        </div>

        <div className="p-4 bg-slate-900/60 border border-slate-800 rounded-xl flex items-start gap-3">
          <Lock className="w-5 h-5 text-indigo-400 shrink-0 mt-0.5" />
          <div>
            <span className="font-bold text-slate-200 block mb-0.5">Read-Only Safety</span>
            <span>Copilot responses are advisory; 0 database mutations occur.</span>
          </div>
        </div>
      </div>
    </div>
  );
};
