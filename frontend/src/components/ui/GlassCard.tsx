import React from 'react';

interface GlassCardProps {
  title?: React.ReactNode;
  subtitle?: string;
  action?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
  hoverEffect?: boolean;
}

export const GlassCard: React.FC<GlassCardProps> = ({
  title,
  subtitle,
  action,
  children,
  className = '',
  hoverEffect = true,
}) => {
  return (
    <div
      className={`bg-slate-900/70 backdrop-blur-glass border border-slate-700/60 rounded-xl p-5 shadow-neo transition-all duration-200 ${
        hoverEffect ? 'hover:border-indigo-500/40 hover:shadow-neo-lg' : ''
      } ${className}`}
    >
      {(title || action) && (
        <div className="flex items-center justify-between gap-3 mb-4 pb-3 border-b border-slate-800">
          <div>
            {typeof title === 'string' ? (
              <h3 className="font-extrabold text-slate-100 tracking-tight text-base">{title}</h3>
            ) : (
              title
            )}
            {subtitle && <p className="text-xs text-slate-400 mt-0.5">{subtitle}</p>}
          </div>
          {action && <div>{action}</div>}
        </div>
      )}
      <div>{children}</div>
    </div>
  );
};
