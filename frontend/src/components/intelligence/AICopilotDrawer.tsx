import React, { useState } from 'react';
import { GlassDrawer } from '../ui/GlassDrawer';
import { GlassCard } from '../ui/GlassCard';
import { GlassInput } from '../ui/GlassInput';
import { AIInsightCard } from '../ui/AIInsightCard';
import { copilotApi } from '../../services/copilotApi';
import { CopilotResponse } from '../../types';
import { useToast } from '../../context/ToastContext';
import { Sparkles, Send, Zap, Bot } from 'lucide-react';

interface AICopilotDrawerProps {
  isOpen: boolean;
  onClose: () => void;
}

export const AICopilotDrawer: React.FC<AICopilotDrawerProps> = ({ isOpen, onClose }) => {
  const { showToast } = useToast();
  const [question, setQuestion] = useState('');
  const [response, setResponse] = useState<CopilotResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleAsk = async (queryToRun?: string) => {
    const targetQuery = queryToRun || question;
    if (!targetQuery.trim()) return;

    setIsLoading(true);
    try {
      const res = await copilotApi.chat({ message: targetQuery.trim() });
      setResponse(res);
      showToast('AI Copilot query executed.', 'success');
    } catch (err: any) {
      showToast(err.message || 'AI Copilot request failed.', 'error');
    } finally {
      setIsLoading(false);
    }
  };

  const presetQueries = [
    'Which deals need immediate attention?',
    'Summarize open sales pipeline & revenue forecast',
    'Show deals with high discount or margin risk',
    'Which quotations are waiting for approval?',
  ];

  return (
    <GlassDrawer isOpen={isOpen} onClose={onClose} title="AI Sales Copilot & Intelligence">
      <div className="space-y-4 text-slate-100">
        <div className="p-3 rounded-xl bg-purple-950/60 border border-purple-500/40 text-xs text-purple-200 flex items-center gap-2">
          <Sparkles className="w-4 h-4 text-purple-400 shrink-0 animate-pulse" />
          <span>Natural language AI queries across tenant deals, pipeline & governance.</span>
        </div>

        {/* Input Bar */}
        <div className="space-y-2">
          <div className="relative">
            <GlassInput
              placeholder="Ask AI Copilot anything (e.g. pipeline risks, top deals)..."
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleAsk()}
            />
            <button
              onClick={() => handleAsk()}
              disabled={isLoading || !question.trim()}
              className="absolute right-2 top-2 p-2 bg-purple-600 hover:bg-purple-500 disabled:opacity-50 text-white rounded-lg transition"
            >
              <Send className="w-4 h-4" />
            </button>
          </div>

          {/* Quick Presets */}
          <div className="flex flex-wrap gap-1.5 pt-1">
            {presetQueries.map((query, idx) => (
              <button
                key={idx}
                onClick={() => {
                  setQuestion(query);
                  handleAsk(query);
                }}
                className="px-2.5 py-1 rounded-lg bg-slate-900 border border-slate-800 hover:border-purple-500/50 text-[11px] text-slate-300 hover:text-purple-200 transition"
              >
                ⚡ {query}
              </button>
            ))}
          </div>
        </div>

        {/* Response Panel */}
        {isLoading && (
          <GlassCard className="p-4 text-center space-y-2">
            <Bot className="w-8 h-8 text-purple-400 mx-auto animate-bounce" />
            <p className="text-xs font-mono text-purple-300">Synthesizing CRM & Pipeline Telemetry...</p>
          </GlassCard>
        )}

        {response && !isLoading && (
          <div className="space-y-4 pt-2">
            <AIInsightCard
              title="AI Copilot Analysis"
              provider="AI Intelligence"
              model={response.intent}
            >
              <p className="text-xs text-slate-200 leading-relaxed font-sans">{response.answer}</p>

              {response.recommendations && response.recommendations.length > 0 && (
                <div className="mt-3 pt-3 border-t border-purple-500/30 space-y-1.5">
                  <span className="text-[10px] font-mono uppercase font-bold text-purple-300">Recommended Next Steps:</span>
                  {response.recommendations.map((act: string, i: number) => (
                    <div key={i} className="text-xs text-slate-300 flex items-start gap-1.5">
                      <Zap className="w-3.5 h-3.5 text-amber-400 shrink-0 mt-0.5" />
                      <span>{act}</span>
                    </div>
                  ))}
                </div>
              )}
            </AIInsightCard>
          </div>
        )}
      </div>
    </GlassDrawer>
  );
};
