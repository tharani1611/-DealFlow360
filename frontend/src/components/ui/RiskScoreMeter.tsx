import React from 'react';

interface RiskScoreMeterProps {
  score: number; // 0 to 100
  label?: string;
}

export const RiskScoreMeter: React.FC<RiskScoreMeterProps> = ({ score, label = "Blended Risk Score" }) => {
  const getRiskColor = (s: number) => {
    if (s < 30) return 'text-emerald-400 bg-emerald-500';
    if (s < 70) return 'text-amber-400 bg-amber-500';
    return 'text-rose-400 bg-rose-500';
  };

  const getRiskLabel = (s: number) => {
    if (s < 30) return 'Low Risk (Auto-Approved)';
    if (s < 70) return 'Medium Risk (Manager Approval)';
    return 'High Risk (Finance Dual Approval)';
  };

  return (
    <div className="neo-glass-panel flex flex-col gap-2">
      <div className="flex justify-between items-center text-xs font-semibold uppercase tracking-wider text-slate-300">
        <span>{label}</span>
        <span className={`font-mono text-base font-bold ${getRiskColor(score).split(' ')[0]}`}>{score} / 100</span>
      </div>
      <div className="w-full bg-slate-900 h-3 rounded-full overflow-hidden border border-glass-border p-0.5">
        <div
          className={`h-full rounded-full transition-all duration-500 ${getRiskColor(score).split(' ')[1]}`}
          style={{ width: `${Math.min(100, Math.max(0, score))}%` }}
        />
      </div>
      <span className="text-[11px] font-mono text-slate-400 text-right">{getRiskLabel(score)}</span>
    </div>
  );
};
