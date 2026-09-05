import React from 'react';
import { LucideIcon, Loader2, Sparkles } from 'lucide-react';

export interface BrutalButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  children: React.ReactNode;
  variant?: 'primary' | 'secondary' | 'danger' | 'ghost' | 'success' | 'ai';
  size?: 'sm' | 'md' | 'lg';
  icon?: LucideIcon;
  isLoading?: boolean;
  fullWidth?: boolean;
}

export const BrutalButton: React.FC<BrutalButtonProps> = ({
  children,
  variant = 'primary',
  size = 'md',
  icon: Icon,
  isLoading = false,
  fullWidth = false,
  disabled,
  className = '',
  ...props
}) => {
  const baseClasses =
    'font-bold rounded-lg transition-all duration-150 flex items-center justify-center gap-2 select-none border active:translate-x-[1px] active:translate-y-[1px] disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none focus:ring-2 focus:outline-none';

  const variantClasses = {
    primary:
      'bg-indigo-600 hover:bg-indigo-500 text-white border-indigo-400/40 shadow-neo hover:shadow-neo-lg focus:ring-indigo-400',
    secondary:
      'bg-slate-800 hover:bg-slate-700 text-slate-100 border-slate-600/60 shadow-neo-sm hover:shadow-neo focus:ring-slate-400',
    danger:
      'bg-rose-600 hover:bg-rose-500 text-white border-rose-400/40 shadow-neo hover:shadow-neo-rose focus:ring-rose-400',
    success:
      'bg-emerald-600 hover:bg-emerald-500 text-white border-emerald-400/40 shadow-neo hover:shadow-neo-emerald focus:ring-emerald-400',
    ai:
      'bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white border-indigo-300/40 shadow-neo-indigo hover:shadow-ai-glow focus:ring-purple-400',
    ghost:
      'bg-transparent hover:bg-slate-800/60 text-slate-300 border-transparent shadow-none hover:text-slate-100 focus:ring-slate-500',
  };

  const sizeClasses = {
    sm: 'px-3 py-1.5 text-xs font-bold',
    md: 'px-4 py-2 text-xs font-bold',
    lg: 'px-5 py-2.5 text-sm font-extrabold',
  };

  // If variant is AI and no custom icon provided, default to Sparkles
  const DisplayIcon = Icon || (variant === 'ai' ? Sparkles : undefined);

  return (
    <button
      disabled={disabled || isLoading}
      className={`${baseClasses} ${variantClasses[variant]} ${sizeClasses[size]} ${
        fullWidth ? 'w-full' : ''
      } ${className}`}
      {...props}
    >
      {isLoading ? (
        <Loader2 className="w-4 h-4 animate-spin shrink-0" />
      ) : DisplayIcon ? (
        <DisplayIcon className={`w-4 h-4 shrink-0 ${variant === 'ai' ? 'animate-pulse' : ''}`} />
      ) : null}
      <span>{children}</span>
    </button>
  );
};
