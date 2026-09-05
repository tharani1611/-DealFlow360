import React from 'react';
import { Activity, AlertTriangle, HelpCircle, CheckCircle, ArrowRight } from 'lucide-react';
import { DealHealthResponse, DealHealthSnapshot } from '../../types';
import { GlassCard } from '../ui/GlassCard';
import { StatusBadge } from '../ui/StatusBadge';

interface DealHealthCardProps {
  health?: DealHealthResponse | null;
  snapshot?: DealHealthSnapshot | null;
  isLoading?: boolean;
  onEvaluate?: () => void;
}

export const DealHealthCard: React.FC<DealHealthCardProps> = ({ health, snapshot, isLoading, onEvaluate }) => {
  if (isLoading) {
    return (
      <GlassCard className="p-5 animate-pulse">
        <div className="h-6 w-32 bg-white/10 rounded mb-4"></div>
        <div className="h-16 w-full bg-white/5 rounded mb-4"></div>
        <div className="h-10 w-full bg-white/5 rounded"></div>
      </GlassCard>
    );
  }

  const score = snapshot?.health_score ?? health?.health_score ?? 0;
  const statusStr = (snapshot?.health_status ?? health?.health_status ?? 'HEALTHY').toUpperCase();

  const getScoreColor = (scoreVal: number) => {
    if (scoreVal >= 80) return 'text-emerald-400 border-emerald-500/40 bg-emerald-500/10 shadow-emerald-500/20';
    if (scoreVal >= 60) return 'text-cyan-400 border-cyan-500/40 bg-cyan-500/10 shadow-cyan-500/20';
    if (scoreVal >= 40) return 'text-amber-400 border-amber-500/40 bg-amber-500/10 shadow-amber-500/20';
    return 'text-rose-400 border-rose-500/40 bg-rose-500/10 shadow-rose-500/20';
  };

  const scoreClass = getScoreColor(score);

  return (
    <GlassCard className="p-5 relative overflow-hidden border border-white/15">
      <div className="absolute -top-12 -right-12 w-32 h-32 bg-indigo-500/10 blur-2xl rounded-full pointer-events-none" />

      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Activity className="w-5 h-5 text-indigo-400" />
          <h3 className="text-sm font-semibold uppercase tracking-wider text-slate-200">
            Phase 53 — Deal Health Telemetry
          </h3>
        </div>
        <div className="flex items-center gap-2">
          <StatusBadge
            status={statusStr}
            variant={
              statusStr === 'HEALTHY' ? 'success' :
              statusStr === 'ATTENTION' ? 'info' :
              statusStr === 'STALLED' ? 'warning' : 'danger'
            }
          />
          {onEvaluate && (
            <button
              onClick={onEvaluate}
              className="text-xs px-2.5 py-1 rounded-md bg-indigo-600/30 hover:bg-indigo-600/50 border border-indigo-500/30 text-indigo-200 font-medium transition"
            >
              Re-evaluate
            </button>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 items-center mb-5">
        <div className={`p-4 rounded-xl border-2 text-center backdrop-blur-md shadow-lg ${scoreClass}`}>
          <div className="text-3xl font-extrabold font-mono tracking-tight">
            {score}
            <span className="text-sm text-slate-400 font-normal ml-0.5">/100</span>
          </div>
          <div className="text-[11px] font-bold uppercase tracking-wider mt-1 opacity-90">
            {statusStr}
          </div>
        </div>

        <div className="sm:col-span-2 space-y-2 text-xs text-slate-300">
          {health?.metrics && (
            <>
              <div className="flex justify-between items-center py-1 border-b border-white/5">
                <span className="text-slate-400">Win Probability</span>
                <span className="font-mono font-semibold text-slate-200">{health.metrics.probability}%</span>
              </div>
              <div className="flex justify-between items-center py-1 border-b border-white/5">
                <span className="text-slate-400">Overdue Tasks</span>
                <span className={`font-mono font-semibold ${health.metrics.overdue_activity_count > 0 ? 'text-rose-400' : 'text-emerald-400'}`}>
                  {health.metrics.overdue_activity_count}
                </span>
              </div>
            </>
          )}
          {snapshot?.evaluated_at && (
            <div className="flex justify-between items-center py-1 border-b border-white/5">
              <span className="text-slate-400">Last Evaluated</span>
              <span className="font-mono text-slate-300">
                {new Date(snapshot.evaluated_at).toLocaleString()}
              </span>
            </div>
          )}
        </div>
      </div>

      {snapshot?.positive_drivers && snapshot.positive_drivers.length > 0 && (
        <div className="mb-4">
          <div className="text-xs font-bold uppercase tracking-wider text-emerald-400 mb-2 flex items-center gap-1.5">
            <CheckCircle className="w-3.5 h-3.5" />
            Positive Health Drivers ({snapshot.positive_drivers.length})
          </div>
          <div className="space-y-1.5">
            {snapshot.positive_drivers.map((drv, idx) => (
              <div key={idx} className="p-2 rounded bg-emerald-500/10 border border-emerald-500/20 text-xs text-emerald-200 flex items-start gap-2">
                <span className="font-bold">•</span>
                <span>{drv}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {snapshot?.negative_drivers && snapshot.negative_drivers.length > 0 && (
        <div className="mb-4">
          <div className="text-xs font-bold uppercase tracking-wider text-rose-400 mb-2 flex items-center gap-1.5">
            <AlertTriangle className="w-3.5 h-3.5" />
            Negative Health Drivers ({snapshot.negative_drivers.length})
          </div>
          <div className="space-y-1.5">
            {snapshot.negative_drivers.map((drv, idx) => (
              <div key={idx} className="p-2 rounded bg-rose-500/10 border border-rose-500/20 text-xs text-rose-200 flex items-start gap-2">
                <span className="font-bold">•</span>
                <span>{drv}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {snapshot?.recommended_actions && snapshot.recommended_actions.length > 0 && (
        <div className="mt-4 pt-3 border-t border-white/10 text-xs">
          <div className="flex items-center gap-1.5 text-indigo-300 font-semibold mb-2">
            <ArrowRight className="w-3.5 h-3.5 text-indigo-400" />
            <span>Deterministic Recommended Actions</span>
          </div>
          <div className="space-y-1.5">
            {snapshot.recommended_actions.map((act, idx) => (
              <div key={idx} className="p-2 rounded bg-indigo-500/10 border border-indigo-500/20 text-xs text-indigo-200">
                {act}
              </div>
            ))}
          </div>
        </div>
      )}

      {health?.ai_explanation && !snapshot && (
        <div className="mt-4 pt-3 border-t border-white/10 text-xs">
          <div className="flex items-center gap-1.5 text-indigo-300 font-semibold mb-1">
            <HelpCircle className="w-3.5 h-3.5" />
            <span>Why this score?</span>
          </div>
          <p className="text-slate-300 text-[11px] italic leading-relaxed bg-white/5 p-2.5 rounded-lg border border-white/10">
            "{health.ai_explanation}"
          </p>
        </div>
      )}
    </GlassCard>
  );
};

