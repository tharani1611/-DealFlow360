import React from 'react';

type BadgeVariant = 'draft' | 'pending' | 'approved' | 'rejected' | 'negotiation' | 'confirmed' | 'healthy' | 'at_risk' | 'critical';

interface StateBadgeProps {
  state: string;
  variant?: BadgeVariant;
}

export const StateBadge: React.FC<StateBadgeProps> = ({ state, variant }) => {
  const getVariantStyles = (v?: string) => {
    const key = (v || state).toLowerCase();
    if (key.includes('draft')) return 'bg-slate-800 text-slate-300 border-slate-600';
    if (key.includes('pending')) return 'bg-amber-950/80 text-amber-300 border-amber-500/50';
    if (key.includes('approved') || key.includes('healthy') || key.includes('confirmed')) return 'bg-emerald-950/80 text-emerald-300 border-emerald-500/50';
    if (key.includes('reject') || key.includes('critical')) return 'bg-rose-950/80 text-rose-300 border-rose-500/50';
    if (key.includes('negotiat') || key.includes('at_risk')) return 'bg-sky-950/80 text-sky-300 border-sky-500/50';
    return 'bg-slate-800 text-slate-300 border-slate-600';
  };

  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-md text-xs font-bold uppercase tracking-wider border shadow-sm ${getVariantStyles(variant)}`}>
      {state}
    </span>
  );
};
