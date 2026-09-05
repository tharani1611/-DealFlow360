import React from 'react';
import { LucideIcon } from 'lucide-react';

interface IconButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  icon: LucideIcon;
  variant?: 'primary' | 'secondary' | 'danger' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
  ariaLabel: string;
}

export const IconButton: React.FC<IconButtonProps> = ({
  icon: Icon,
  variant = 'secondary',
  size = 'md',
  ariaLabel,
  disabled,
  className = '',
  ...props
}) => {
  const baseClasses =
    'rounded-lg flex items-center justify-center transition-all duration-150 active:translate-x-[1px] active:translate-y-[1px] disabled:opacity-50 disabled:cursor-not-allowed';

  const variantClasses = {
    primary: 'bg-indigo-600 hover:bg-indigo-500 text-white border border-indigo-400/40 shadow-neo-sm',
    secondary: 'bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-slate-100 border border-slate-700 shadow-neo-sm',
    danger: 'bg-rose-600/20 hover:bg-rose-600 text-rose-300 hover:text-white border border-rose-500/30',
    ghost: 'bg-transparent hover:bg-slate-800 text-slate-400 hover:text-slate-100 border-none',
  };

  const sizeClasses = {
    sm: 'p-1.5 text-xs',
    md: 'p-2 text-sm',
    lg: 'p-3 text-base',
  };

  return (
    <button
      type="button"
      aria-label={ariaLabel}
      title={ariaLabel}
      disabled={disabled}
      className={`${baseClasses} ${variantClasses[variant]} ${sizeClasses[size]} ${className}`}
      {...props}
    >
      <Icon className="w-4 h-4" />
    </button>
  );
};
