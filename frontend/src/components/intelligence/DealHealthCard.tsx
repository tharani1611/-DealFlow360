import React from 'react';
import { Activity, AlertTriangle, ShieldAlert, HelpCircle } from 'lucide-react';
import { DealHealthResponse } from '../../types';
import { GlassCard } from '../ui/GlassCard';
import { StatusBadge } from '../ui/StatusBadge';

interface DealHealthCardProps {
  health: DealHealthResponse;
  isLoading?: boolean;
}

export const DealHealthCard: React.FC<DealHealthCardProps> = ({ health, isLoading }) => {
  if (isLoading) {
    return (
      <GlassCard className="p-5 animate-pulse">
        <div className="h-6 w-32 bg-white/10 rounded mb-4"></div>
        <div className="h-16 w-full bg-white/5 rounded mb-4"></div>
        <div className="h-10 w-full bg-white/5 rounded"></div>
      </GlassCard>
    );
  }

  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-emerald-400 border-emerald-500/40 bg-emerald-500/10 shadow-emerald-500/20';
    if (score >= 60) return 'text-cyan-400 border-cyan-500/40 bg-cyan-500/10 shadow-cyan-500/20';
    if (score >= 40) return 'text-amber-400 border-amber-500/40 bg-amber-500/10 shadow-amber-500/20';
    return 'text-rose-400 border-rose-500/40 bg-rose-500/10 shadow-rose-500/20';
  };

  const scoreClass = getScoreColor(health.health_score);

  return (
    <GlassCard className="p-5 relative overflow-hidden border border-white/15">
      {/* Background Subtle Ambient Glow */}
      <div className="absolute -top-12 -right-12 w-32 h-32 bg-indigo-500/10 blur-2xl rounded-full pointer-events-none" />

      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Activity className="w-5 h-5 text-indigo-400" />
          <h3 className="text-sm font-semibold uppercase tracking-wider text-slate-200">
            Deal Health Telemetry
          </h3>
        </div>
        <StatusBadge
          status={health.health_status}
          variant={
            health.health_status === 'healthy' ? 'success' :
            health.health_status === 'stable' ? 'info' :
            health.health_status === 'at_risk' ? 'warning' : 'danger'
          }
        />
      </div>

      {/* Main Score Display */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 items-center mb-5">
        <div className={`p-4 rounded-xl border-2 text-center backdrop-blur-md shadow-lg ${scoreClass}`}>
          <div className="text-3xl font-extrabold font-mono tracking-tight">
            {health.health_score}
            <span className="text-sm text-slate-400 font-normal ml-0.5">/100</span>
          </div>
          <div className="text-[11px] font-bold uppercase tracking-wider mt-1 opacity-90">
            {health.health_status.replace('_', ' ')}
          </div>
        </div>

        <div className="sm:col-span-2 space-y-2 text-xs text-slate-300">
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
          <div className="flex justify-between items-center py-1">
            <span className="text-slate-400">Expected Close</span>
            <span className="font-mono font-semibold text-slate-200">
              {health.metrics.days_until_expected_close !== null && health.metrics.days_until_expected_close !== undefined
                ? `${health.metrics.days_until_expected_close} days`
                : 'Not set'}
            </span>
          </div>
        </div>
      </div>

      {/* Risk Factors Section */}
      {health.risk_factors.length > 0 && (
        <div className="mb-4">
          <div className="text-xs font-bold uppercase tracking-wider text-slate-300 mb-2 flex items-center gap-1.5">
            <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
            Detected Risk Factors ({health.risk_factors.length})
          </div>
          <div className="space-y-2">
            {health.risk_factors.map((rf, idx) => (
              <div
                key={idx}
                className="p-3 rounded-lg bg-black/20 border border-white/10 text-xs backdrop-blur-sm"
              >
                <div className="flex items-center justify-between font-semibold text-slate-200 mb-1">
                  <span className="flex items-center gap-1.5 text-rose-300">
                    <ShieldAlert className="w-3.5 h-3.5" />
                    {rf.title}
                  </span>
                  <span className="text-[10px] px-1.5 py-0.5 rounded uppercase font-mono bg-rose-500/20 text-rose-300 border border-rose-500/30">
                    {rf.severity}
                  </span>
                </div>
                <p className="text-slate-300 text-[11px] mb-1.5">{rf.description}</p>
                <p className="text-indigo-300 text-[11px] font-medium bg-indigo-500/10 p-1.5 rounded border border-indigo-500/20">
                  <span className="font-bold">Recommendation: </span>{rf.recommendation}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* AI Explanation / Why Section */}
      {health.ai_explanation && (
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
