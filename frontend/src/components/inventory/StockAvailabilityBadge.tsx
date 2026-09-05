import React from 'react';
import { CheckCircle2, AlertTriangle, XCircle, Package } from 'lucide-react';

export interface StockAvailabilityBadgeProps {
  status: 'AVAILABLE' | 'PARTIALLY_AVAILABLE' | 'OUT_OF_STOCK' | string;
  totalAvailable?: number;
  totalRequested?: number;
  totalShortfall?: number;
  size?: 'sm' | 'md';
}

export const StockAvailabilityBadge: React.FC<StockAvailabilityBadgeProps> = ({
  status,
  totalAvailable,
  totalRequested,
  totalShortfall,
  size = 'md',
}) => {
  const s = status.toUpperCase();

  let colorClass = 'bg-slate-800 text-slate-300 border-slate-700';
  let Icon = Package;

  if (s === 'AVAILABLE') {
    colorClass = 'bg-emerald-950/60 text-emerald-300 border-emerald-500/40 shadow-[0_0_10px_rgba(16,185,129,0.15)]';
    Icon = CheckCircle2;
  } else if (s === 'PARTIALLY_AVAILABLE') {
    colorClass = 'bg-amber-950/60 text-amber-300 border-amber-500/40 shadow-[0_0_10px_rgba(245,158,11,0.15)]';
    Icon = AlertTriangle;
  } else if (s === 'OUT_OF_STOCK') {
    colorClass = 'bg-rose-950/60 text-rose-300 border-rose-500/40 shadow-[0_0_10px_rgba(239,68,68,0.15)]';
    Icon = XCircle;
  }

  const isSmall = size === 'sm';

  return (
    <div className={`inline-flex items-center gap-1.5 font-mono border rounded-md ${colorClass} ${isSmall ? 'px-2 py-0.5 text-[10px]' : 'px-2.5 py-1 text-xs font-bold'}`}>
      <Icon className={isSmall ? 'w-3 h-3' : 'w-4 h-4'} />
      <span className="uppercase tracking-wider">{s.replace(/_/g, ' ')}</span>
      {totalRequested !== undefined && totalAvailable !== undefined && (
        <span className="opacity-80 text-[10px]">
          ({totalAvailable}/{totalRequested})
        </span>
      )}
      {totalShortfall !== undefined && totalShortfall > 0 && (
        <span className="bg-rose-900/80 text-rose-200 px-1 rounded text-[9px] font-mono">
          -{totalShortfall} short
        </span>
      )}
    </div>
  );
};
