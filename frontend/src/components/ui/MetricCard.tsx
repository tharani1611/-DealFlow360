import React from 'react';
import { LucideIcon } from 'lucide-react';

interface MetricCardProps {
  label: string;
  value: string | number;
  subtitle?: string;
  trend?: {
    value: string;
    isPositive?: boolean;
  };
  icon?: LucideIcon;
  variant?: 'primary' | 'accent' | 'warning' | 'danger' | 'success';
}

export const MetricCard: React.FC<MetricCardProps> = ({
  label,
  value,
  subtitle,
  trend,
  icon: Icon,
  variant = 'primary',
}) => {
  const accentColors = {
    primary: 'border-l-4 border-l-indigo-500 text-indigo-400',
    accent: 'border-l-4 border-l-sky-500 text-sky-400',
    warning: 'border-l-4 border-l-amber-500 text-amber-400',
    danger: 'border-l-4 border-l-rose-500 text-rose-400',
    success: 'border-l-4 border-l-emerald-500 text-emerald-400',
  };

  return (
    <div className={`bg-slate-900/80 backdrop-blur-glass border border-slate-700/60 rounded-xl p-5 shadow-neo transition-all hover:shadow-neo-lg hover:border-slate-600 ${accentColors[variant]}`}>
      <div className="flex items-center justify-between gap-3 mb-2">
        <span className="text-xs font-bold uppercase tracking-wider text-slate-400">{label}</span>
        {Icon && <Icon className="w-5 h-5 opacity-80" />}
      </div>

      <div className="flex items-baseline justify-between gap-2">
        <span className="text-2xl sm:text-3xl font-black text-slate-100 tracking-tight font-mono">
          {value}
        </span>
        {trend && (
          <span
            className={`text-xs font-mono font-bold px-1.5 py-0.5 rounded ${
              trend.isPositive !== false ? 'bg-emerald-950/80 text-emerald-400' : 'bg-rose-950/80 text-rose-400'
            }`}
          >
            {trend.value}
          </span>
        )}
      </div>

      {subtitle && <p className="text-xs text-slate-400 mt-2 font-mono">{subtitle}</p>}
    </div>
  );
};
