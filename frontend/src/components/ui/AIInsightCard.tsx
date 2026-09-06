import React from 'react';
import { Sparkles, ArrowRight } from 'lucide-react';
import { StatusBadge } from './StatusBadge';
import { BrutalButton } from './BrutalButton';

export interface AIInsightCardProps {
  title: string;
  provider?: string;
  model?: string;
  children: React.ReactNode;
  className?: string;
  riskLevel?: 'low' | 'medium' | 'high';
}

export const AIInsightCard: React.FC<AIInsightCardProps> = ({
  title,
  provider = 'AI Intelligence',
  model,
  children,
  className = '',
  riskLevel,
}) => {
  return (
    <div
      className={`bg-slate-900/90 backdrop-blur-glass border-2 border-indigo-500/40 rounded-2xl p-6 shadow-glass-glow relative overflow-hidden ${className}`}
    >
      {/* Glow Ambient Decoration */}
      <div className="absolute -top-12 -right-12 w-32 h-32 bg-indigo-600/20 rounded-full blur-2xl pointer-events-none" />

      {/* Header */}
      <div className="flex items-center justify-between gap-3 mb-4 pb-3 border-b border-indigo-500/20">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-indigo-600/30 border border-indigo-400/40 flex items-center justify-center text-indigo-300">
            <Sparkles className="w-4 h-4 animate-pulse" />
          </div>
          <div>
            <h3 className="font-black text-slate-100 tracking-tight text-base">{title}</h3>
            <span className="text-[10px] font-mono text-indigo-400 font-bold uppercase tracking-widest">
              {provider} {model ? `(${model})` : ''}
            </span>
          </div>
        </div>

        {riskLevel && <StatusBadge status={`Risk: ₹${riskLevel}`} variant={riskLevel === 'high' ? 'danger' : riskLevel === 'medium' ? 'warning' : 'success'} />}
      </div>

      <div>{children}</div>
    </div>
  );
};

export interface AIRecommendationProps {
  title: string;
  reason: string;
  actionType: string;
  priority: string;
  onExecute?: () => void;
  isLoading?: boolean;
}

export const AIRecommendation: React.FC<AIRecommendationProps> = ({
  title,
  reason,
  actionType,
  priority,
  onExecute,
  isLoading = false,
}) => {
  return (
    <div className="bg-slate-950/80 border border-indigo-500/40 rounded-xl p-5 shadow-neo">
      <div className="flex items-center justify-between gap-2 mb-2">
        <span className="text-[10px] font-mono font-black uppercase tracking-widest text-indigo-400">
          NEXT BEST ACTION • {actionType}
        </span>
        <StatusBadge status={priority} />
      </div>

      <h4 className="font-extrabold text-slate-100 text-base mb-1">{title}</h4>
      <p className="text-xs text-slate-300 leading-relaxed mb-4">{reason}</p>

      {onExecute && (
        <BrutalButton
          variant="primary"
          size="sm"
          icon={ArrowRight}
          onClick={onExecute}
          isLoading={isLoading}
        >
          Create Recommended Activity
        </BrutalButton>
      )}
    </div>
  );
};
