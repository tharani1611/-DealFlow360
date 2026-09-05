import React from 'react';

interface MarginTelemetryBarProps {
  totalRevenue: number;
  totalCost: number;
}

export const MarginTelemetryBar: React.FC<MarginTelemetryBarProps> = ({ totalRevenue, totalCost }) => {
  const marginAmount = totalRevenue - totalCost;
  const marginPct = totalRevenue > 0 ? (marginAmount / totalRevenue) * 100 : 0;
  const costPct = totalRevenue > 0 ? (totalCost / totalRevenue) * 100 : 0;

  return (
    <div className="neo-glass-panel flex flex-col gap-2">
      <div className="flex justify-between items-center text-xs uppercase font-bold tracking-wider text-slate-300">
        <span>Margin Telemetry</span>
        <span className="font-mono text-emerald-400 font-bold">${marginAmount.toLocaleString('en-US', { minimumFractionDigits: 2 })} ({marginPct.toFixed(1)}%)</span>
      </div>
      <div className="w-full bg-slate-900 h-4 rounded-full overflow-hidden border border-glass-border flex">
        <div
          className="bg-slate-600 h-full transition-all duration-300"
          style={{ width: `${Math.min(100, Math.max(0, costPct))}%` }}
          title={`Base Cost: $${totalCost}`}
        />
        <div
          className="bg-emerald-500 h-full transition-all duration-300"
          style={{ width: `${Math.min(100, Math.max(0, marginPct))}%` }}
          title={`Gross Margin: $${marginAmount}`}
        />
      </div>
      <div className="flex justify-between text-[11px] font-mono text-slate-400">
        <span>Base Cost: ${totalCost.toLocaleString('en-US', { minimumFractionDigits: 2 })}</span>
        <span>Revenue: ${totalRevenue.toLocaleString('en-US', { minimumFractionDigits: 2 })}</span>
      </div>
    </div>
  );
};
