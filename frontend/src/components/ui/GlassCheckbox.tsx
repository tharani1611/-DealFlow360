import React from 'react';

export interface GlassCheckboxProps extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'type'> {
  label: string;
}

export const GlassCheckbox: React.FC<GlassCheckboxProps> = ({
  label,
  className = '',
  id,
  ...props
}) => {
  const checkboxId = id || label.toLowerCase().replace(/\s+/g, '-');

  return (
    <div className="flex items-center gap-2.5 cursor-pointer select-none">
      <input
        type="checkbox"
        id={checkboxId}
        className={`w-4 h-4 rounded bg-slate-950 border border-slate-700 text-indigo-600 focus:ring-indigo-500 focus:ring-offset-slate-900 focus:ring-1 transition cursor-pointer ${className}`}
        {...props}
      />
      <label htmlFor={checkboxId} className="text-xs font-semibold text-slate-300 cursor-pointer">
        {label}
      </label>
    </div>
  );
};
