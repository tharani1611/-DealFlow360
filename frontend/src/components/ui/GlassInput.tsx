import React from 'react';

export interface GlassInputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  helperText?: string;
}

export const GlassInput: React.FC<GlassInputProps> = ({
  label,
  error,
  helperText,
  className = '',
  id,
  ...props
}) => {
  const inputId = id || (label ? label.toLowerCase().replace(/\s+/g, '-') : undefined);

  return (
    <div className="flex flex-col gap-1.5 w-full">
      {label && (
        <label htmlFor={inputId} className="text-xs font-bold text-slate-300 uppercase tracking-wider">
          {label}
        </label>
      )}
      <input
        id={inputId}
        className={`w-full px-3 py-2 bg-slate-950/80 border rounded-lg text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all font-mono text-xs ${
          error ? 'border-rose-500/80 focus:ring-rose-500' : 'border-slate-700/80'
        } ${className}`}
        {...props}
      />
      {error && <span className="text-[11px] font-semibold text-rose-400">{error}</span>}
      {helperText && !error && <span className="text-[11px] text-slate-400">{helperText}</span>}
    </div>
  );
};
