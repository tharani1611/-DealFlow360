import React from 'react';

interface NeoGlassInputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
}

export const NeoGlassInput: React.FC<NeoGlassInputProps> = ({
  label,
  error,
  className = '',
  ...props
}) => {
  return (
    <div className="flex flex-col gap-1.5 w-full">
      {label && <label className="text-xs font-semibold text-slate-300 uppercase tracking-wide">{label}</label>}
      <input className={`neo-glass-input ${className}`} {...props} />
      {error && <span className="text-xs text-rose-400 font-mono mt-0.5">{error}</span>}
    </div>
  );
};
