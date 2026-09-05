import React from 'react';

interface NeoGlassButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'default' | 'primary' | 'success' | 'danger' | 'warning';
  size?: 'sm' | 'md' | 'lg';
  children: React.ReactNode;
}

export const NeoGlassButton: React.FC<NeoGlassButtonProps> = ({
  variant = 'default',
  size = 'md',
  children,
  className = '',
  ...props
}) => {
  const variantClasses = {
    default: 'neo-glass-button',
    primary: 'neo-glass-button-primary',
    success: 'px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white font-bold rounded-lg shadow-neo border border-emerald-400/30 flex items-center justify-center gap-2',
    danger: 'px-4 py-2 bg-rose-600 hover:bg-rose-500 text-white font-bold rounded-lg shadow-neo border border-rose-400/30 flex items-center justify-center gap-2',
    warning: 'px-4 py-2 bg-amber-600 hover:bg-amber-500 text-white font-bold rounded-lg shadow-neo border border-amber-400/30 flex items-center justify-center gap-2',
  };

  const sizeClasses = {
    sm: 'text-xs px-3 py-1.5',
    md: 'text-sm px-4 py-2',
    lg: 'text-base px-6 py-3',
  };

  return (
    <button
      className={`${variantClasses[variant]} ${sizeClasses[size]} ${className}`}
      {...props}
    >
      {children}
    </button>
  );
};
