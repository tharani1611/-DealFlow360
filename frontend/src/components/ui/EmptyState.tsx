import React from 'react';
import { LucideIcon, FolderOpen, AlertTriangle, Loader2 } from 'lucide-react';
import { BrutalButton } from './BrutalButton';

export interface EmptyStateProps {
  title: string;
  description: string;
  actionLabel?: string;
  onAction?: () => void;
  icon?: LucideIcon;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  title,
  description,
  actionLabel,
  onAction,
  icon: Icon = FolderOpen,
}) => {
  return (
    <div className="bg-slate-900/60 backdrop-blur-glass border border-slate-800 rounded-2xl p-12 text-center flex flex-col items-center justify-center max-w-md mx-auto my-8">
      <div className="w-14 h-14 rounded-2xl bg-slate-800/80 border border-slate-700/60 flex items-center justify-center text-slate-400 mb-4 shadow-neo-sm">
        <Icon className="w-7 h-7" />
      </div>
      <h3 className="text-lg font-black text-slate-100 mb-1">{title}</h3>
      <p className="text-xs text-slate-400 max-w-sm mb-6 leading-relaxed">{description}</p>
      {actionLabel && onAction && (
        <BrutalButton variant="primary" onClick={onAction}>
          {actionLabel}
        </BrutalButton>
      )}
    </div>
  );
};

export const LoadingState: React.FC<{ message?: string }> = ({ message = 'Loading CRM telemetry...' }) => {
  return (
    <div className="flex flex-col items-center justify-center p-16 text-center">
      <Loader2 className="w-8 h-8 text-indigo-500 animate-spin mb-3" />
      <span className="text-xs font-mono font-bold text-slate-400 uppercase tracking-widest">{message}</span>
    </div>
  );
};

export interface ErrorStateProps {
  title?: string;
  message: string;
  onRetry?: () => void;
}

export const ErrorState: React.FC<ErrorStateProps> = ({
  title = 'Telemetry Error',
  message,
  onRetry,
}) => {
  return (
    <div className="bg-rose-950/40 border border-rose-500/40 rounded-2xl p-8 text-center flex flex-col items-center justify-center max-w-md mx-auto my-8 shadow-neo">
      <div className="w-12 h-12 rounded-xl bg-rose-900/80 border border-rose-500/50 flex items-center justify-center text-rose-300 mb-3">
        <AlertTriangle className="w-6 h-6" />
      </div>
      <h3 className="text-base font-black text-rose-200 mb-1">{title}</h3>
      <p className="text-xs text-rose-300/80 mb-5 max-w-xs">{message}</p>
      {onRetry && (
        <BrutalButton variant="danger" size="sm" onClick={onRetry}>
          Retry Operations
        </BrutalButton>
      )}
    </div>
  );
};
