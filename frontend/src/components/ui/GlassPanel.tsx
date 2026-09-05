import React from 'react';

interface GlassPanelProps {
  children: React.ReactNode;
  className?: string;
  padding?: 'none' | 'sm' | 'md' | 'lg';
}

export const GlassPanel: React.FC<GlassPanelProps> = ({
  children,
  className = '',
  padding = 'md',
}) => {
  const paddingClasses = {
    none: 'p-0',
    sm: 'p-3',
    md: 'p-5',
    lg: 'p-8',
  };

  return (
    <div
      className={`bg-slate-900/60 backdrop-blur-glass border border-slate-700/50 rounded-xl shadow-glass-glow ${paddingClasses[padding]} ${className}`}
    >
      {children}
    </div>
  );
};
