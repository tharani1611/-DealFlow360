import React, { useEffect } from 'react';
import { X } from 'lucide-react';
import { IconButton } from './IconButton';

interface GlassModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  subtitle?: string;
  children: React.ReactNode;
  maxWidth?: 'sm' | 'md' | 'lg' | 'xl' | '2xl';
}

export const GlassModal: React.FC<GlassModalProps> = ({
  isOpen,
  onClose,
  title,
  subtitle,
  children,
  maxWidth = 'lg',
}) => {
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    if (isOpen) {
      document.body.style.overflow = 'hidden';
      window.addEventListener('keydown', handleKeyDown);
    }
    return () => {
      document.body.style.overflow = 'unset';
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const maxWidthClasses = {
    sm: 'max-w-sm',
    md: 'max-w-md',
    lg: 'max-w-lg',
    xl: 'max-w-xl',
    '2xl': 'max-w-2xl',
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 overflow-y-auto">
      {/* Backdrop Overlay */}
      <div
        className="fixed inset-0 bg-slate-950/80 backdrop-blur-md transition-opacity"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Modal Dialog Box */}
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="modal-title"
        className={`relative w-full ${maxWidthClasses[maxWidth]} bg-slate-900 border border-slate-700/80 rounded-2xl p-6 shadow-2xl shadow-black z-10 my-8 transform transition-all animate-in fade-in zoom-in-95 border-t-2 border-t-indigo-500/50`}
      >
        {/* Header */}
        <div className="flex items-start justify-between gap-4 pb-4 border-b border-slate-800 mb-5">
          <div>
            <h2 id="modal-title" className="text-xl font-black text-slate-100 tracking-tight">
              {title}
            </h2>
            {subtitle && <p className="text-xs text-slate-400 mt-1 font-mono">{subtitle}</p>}
          </div>
          <IconButton icon={X} onClick={onClose} variant="ghost" size="sm" ariaLabel="Close dialog" />
        </div>

        {/* Content Body */}
        <div>{children}</div>
      </div>
    </div>
  );
};
