import React from 'react';

export interface GlassTextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string;
  error?: string;
  helperText?: string;
}

export const GlassTextarea: React.FC<GlassTextareaProps> = ({
  label,
  error,
  helperText,
  className = '',
  id,
  rows = 3,
  ...props
}) => {
  const textareaId = id || (label ? label.toLowerCase().replace(/\s+/g, '-') : undefined);

  return (
    <div className="flex flex-col gap-1.5 w-full">
      {label && (
        <label htmlFor={textareaId} className="text-xs font-bold text-slate-300 uppercase tracking-wider">
          {label}
        </label>
      )}
      <textarea
        id={textareaId}
        rows={rows}
        className={`w-full px-3 py-2 bg-slate-950/80 border rounded-lg text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all text-xs font-sans ${
          error ? 'border-rose-500/80 focus:ring-rose-500' : 'border-slate-700/80'
        } ${className}`}
        {...props}
      />
      {error && <span className="text-[11px] font-semibold text-rose-400">{error}</span>}
      {helperText && !error && <span className="text-[11px] text-slate-400">{helperText}</span>}
    </div>
  );
};
