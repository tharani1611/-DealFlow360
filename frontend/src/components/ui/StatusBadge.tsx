import React from 'react';

export interface StatusBadgeProps {
  status: string;
  variant?: 'default' | 'success' | 'warning' | 'danger' | 'info' | 'purple';
  size?: 'sm' | 'md';
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({
  status,
  variant,
  size = 'md',
}) => {
  // Infer variant if not provided
  const s = status.toLowerCase();
  let resolvedVariant = variant;
  if (!resolvedVariant) {
    if (['active', 'accepted', 'won', 'completed', 'good', 'low', 'converted'].includes(s)) resolvedVariant = 'success';
    else if (['sent', 'qualified', 'proposal', 'negotiation', 'pending', 'neutral', 'medium', 'expired'].includes(s)) resolvedVariant = 'warning';
    else if (['rejected', 'cancelled', 'lost', 'inactive', 'at_risk', 'high', 'urgent'].includes(s)) resolvedVariant = 'danger';
    else if (['new', 'draft', 'open'].includes(s)) resolvedVariant = 'info';
    else if (['priced'].includes(s)) resolvedVariant = 'purple';
    else resolvedVariant = 'default';
  }

  const variantStyles = {
    default: 'bg-slate-800/80 text-slate-300 border-slate-700',
    success: 'bg-emerald-950/60 text-emerald-300 border-emerald-500/40 shadow-[0_0_10px_rgba(16,185,129,0.15)]',
    warning: 'bg-amber-950/60 text-amber-300 border-amber-500/40 shadow-[0_0_10px_rgba(245,158,11,0.15)]',
    danger: 'bg-rose-950/60 text-rose-300 border-rose-500/40 shadow-[0_0_10px_rgba(239,68,68,0.15)]',
    info: 'bg-sky-950/60 text-sky-300 border-sky-500/40 shadow-[0_0_10px_rgba(56,189,248,0.15)]',
    purple: 'bg-indigo-950/60 text-indigo-300 border-indigo-500/40 shadow-[0_0_10px_rgba(99,102,241,0.15)]',
  };

  const sizeStyles = {
    sm: 'px-2 py-0.5 text-[10px] uppercase tracking-wider',
    md: 'px-2.5 py-1 text-xs font-bold uppercase tracking-wider',
  };

  return (
    <span
      className={`inline-flex items-center gap-1.5 font-mono border rounded-md ${variantStyles[resolvedVariant]} ${sizeStyles[size]}`}
    >
      <span className="w-1.5 h-1.5 rounded-full bg-current" />
      <span>{status.replace(/_/g, ' ')}</span>
    </span>
  );
};

export const PriorityBadge: React.FC<{ priority: string }> = ({ priority }) => {
  const p = priority.toLowerCase();
  let colorClass = 'text-slate-400 border-slate-700 bg-slate-900';
  if (p === 'low') colorClass = 'text-sky-400 border-sky-500/30 bg-sky-950/40';
  if (p === 'medium') colorClass = 'text-amber-400 border-amber-500/30 bg-amber-950/40';
  if (p === 'high') colorClass = 'text-orange-400 border-orange-500/30 bg-orange-950/40';
  if (p === 'urgent') colorClass = 'text-rose-400 border-rose-500/30 bg-rose-950/40 animate-pulse';

  return (
    <span className={`inline-flex items-center px-2 py-0.5 text-[10px] font-bold font-mono uppercase tracking-wider border rounded ${colorClass}`}>
      {priority}
    </span>
  );
};
