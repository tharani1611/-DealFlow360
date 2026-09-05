import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { aiApi } from '../services/aiApi';
import { AssistantResponse } from '../types';
import { GlassCard } from '../components/ui/GlassCard';
import { BrutalButton } from '../components/ui/BrutalButton';
import { AIInsightCard } from '../components/ui/AIInsightCard';
import { useToast } from '../context/ToastContext';
import { Sparkles, ShieldCheck, Database, Lock, ExternalLink } from 'lucide-react';

export const AIPage: React.FC = () => {
  const navigate = useNavigate();
  const { showToast } = useToast();

  const [question, setQuestion] = useState('Which deals need immediate follow-up attention?');
  const [response, setResponse] = useState<AssistantResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleAsk = async (queryToRun?: string) => {
    const targetQuery = queryToRun || question;
    if (!targetQuery.trim()) return;

    setIsLoading(true);
    try {
      const res = await aiApi.askAssistant(targetQuery.trim());
      setResponse(res);
      showToast('AI Assistant query processed.', 'success');
    } catch (err: any) {
      showToast(err.message || 'Failed to communicate with AI Intelligence service.', 'error');
    } finally {
      setIsLoading(false);
    }
  };

  const presetQueries = [
    'Explain our revenue forecast',
    'Which deals put our forecast at risk?',
    'Which deals are at risk?',
    'Which customers are going cold?',
    'What needs attention today?',
    'What is my weighted pipeline?',
    'What products should we consider offering this customer?',
    'Which deals need immediate follow-up attention?',
  ];

  return (
    <div className="space-y-8 max-w-4xl mx-auto">
      {/* Page Header */}
      <div>
        <div className="flex items-center gap-2 text-indigo-400 font-mono text-xs font-bold uppercase tracking-widest">
          <Sparkles className="w-4 h-4 animate-pulse" />
          <span>AI Intelligence Command</span>
        </div>
        <h1 className="text-3xl font-black text-slate-100 tracking-tight mt-1">Ask DealFlow360</h1>
        <p className="text-xs text-slate-400 font-mono mt-1">
          Query tenant CRM context, deal risk signals, and relationship telemetry in natural language
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
              placeholder="Ask DealFlow360 a question about your deals, customers, or tasks..."
              className="w-full px-4 py-3 bg-slate-950/90 border border-slate-700/80 rounded-xl text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 text-sm font-mono"
            />
          </div>

          <div className="flex flex-wrap items-center justify-between gap-3">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-[10px] font-mono font-bold text-slate-400 uppercase">Presets:</span>
              {presetQueries.map((pq, idx) => (
                <button
                  key={idx}
                  type="button"
                  onClick={() => {
                    setQuestion(pq);
                    handleAsk(pq);
                  }}
                  className="px-2.5 py-1 rounded-lg bg-slate-800/80 hover:bg-indigo-950 text-slate-300 hover:text-indigo-300 text-[11px] font-mono border border-slate-700/60 transition"
                >
                  {pq.substring(0, 30)}...
                </button>
              ))}
            </div>

            <BrutalButton type="submit" variant="ai" isLoading={isLoading}>
              ✦ Ask AI Assistant
            </BrutalButton>
          </div>
        </form>
      </GlassCard>

      {/* Response Panel */}
      {response && (
        <AIInsightCard
          title="AI Assistant Analysis"
          provider={response.metadata.provider}
          model={response.metadata.model}
        >
          <div className="space-y-4">
            <div className="p-4 bg-slate-950/80 rounded-xl border border-indigo-500/30 text-slate-200 text-sm leading-relaxed font-mono">
              {response.answer}
            </div>

            <div className="flex items-center justify-between text-xs font-mono text-slate-400 pt-2 border-t border-slate-800">
              <span>Context Analyzed: {response.context_used_count} CRM Records</span>
              <span>Generated: {new Date(response.metadata.generated_at).toLocaleTimeString()}</span>
            </div>

            {response.referenced_deal_ids.length > 0 && (
              <div className="pt-2">
                <span className="text-[10px] font-mono font-bold text-indigo-400 uppercase tracking-widest block mb-2">
                  Referenced Pipeline Opportunities:
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
          </div>
        </AIInsightCard>
      )}

      {/* Security Principles Banner */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-4 border-t border-slate-800 text-xs font-mono text-slate-400">
        <div className="p-4 bg-slate-900/60 border border-slate-800 rounded-xl flex items-start gap-3">
          <ShieldCheck className="w-5 h-5 text-emerald-400 shrink-0 mt-0.5" />
          <div>
            <span className="font-bold text-slate-200 block mb-0.5">Prompt Injection Defense</span>
            <span>Context is strictly isolated inside boundary tags.</span>
          </div>
        </div>

        <div className="p-4 bg-slate-900/60 border border-slate-800 rounded-xl flex items-start gap-3">
          <Database className="w-5 h-5 text-sky-400 shrink-0 mt-0.5" />
          <div>
            <span className="font-bold text-slate-200 block mb-0.5">Strict Tenant Isolation</span>
            <span>Only data belonging to your organization is accessible.</span>
          </div>
        </div>

        <div className="p-4 bg-slate-900/60 border border-slate-800 rounded-xl flex items-start gap-3">
          <Lock className="w-5 h-5 text-indigo-400 shrink-0 mt-0.5" />
          <div>
            <span className="font-bold text-slate-200 block mb-0.5">Read-Only Guarantee</span>
            <span>AI outputs are purely advisory; 0 database mutations occur.</span>
          </div>
        </div>
      </div>
    </div>
  );
};
