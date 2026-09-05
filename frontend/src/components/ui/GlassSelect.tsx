import React from 'react';

export interface GlassSelectOption {
  value: string;
  label: string;
}

export interface GlassSelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> {
  label?: string;
  options: GlassSelectOption[];
  error?: string;
  helperText?: string;
}

export const GlassSelect: React.FC<GlassSelectProps> = ({
  label,
  options,
  error,
  helperText,
  className = '',
  id,
  ...props
}) => {
  const selectId = id || (label ? label.toLowerCase().replace(/\s+/g, '-') : undefined);

  return (
    <div className="flex flex-col gap-1.5 w-full">
      {label && (
        <label htmlFor={selectId} className="text-xs font-bold text-slate-300 uppercase tracking-wider">
          {label}
        </label>
      )}
      <select
        id={selectId}
        className={`w-full px-3 py-2 bg-slate-950/80 border rounded-lg text-slate-100 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all font-mono text-xs ${
          error ? 'border-rose-500/80 focus:ring-rose-500' : 'border-slate-700/80'
        } ${className}`}
        {...props}
      >
        {options.map((opt) => (
          <option key={opt.value} value={opt.value} className="bg-slate-900 text-slate-100">
            {opt.label}
          </option>
        ))}
      </select>
      {error && <span className="text-[11px] font-semibold text-rose-400">{error}</span>}
      {helperText && !error && <span className="text-[11px] text-slate-400">{helperText}</span>}
    </div>
  );
};
