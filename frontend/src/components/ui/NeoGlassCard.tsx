import React from 'react';

interface NeoGlassCardProps extends React.HTMLAttributes<HTMLDivElement> {
  title?: string;
  subtitle?: string;
  headerAction?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
}

export const NeoGlassCard: React.FC<NeoGlassCardProps> = ({
  title,
  subtitle,
  headerAction,
  children,
  className = '',
  ...props
}) => {
  return (
    <div className={`neo-glass-card p-6 ${className}`} {...props}>
      {(title || headerAction) && (
        <div className="flex items-center justify-between mb-4 pb-3 border-b border-glass-border">
          <div>
            {title && <h3 className="text-lg font-bold text-slate-100 tracking-tight">{title}</h3>}
            {subtitle && <p className="text-xs text-slate-400 mt-0.5">{subtitle}</p>}
          </div>
          {headerAction && <div>{headerAction}</div>}
        </div>
      )}
      <div>{children}</div>
    </div>
  );
};
