import React, { useEffect } from 'react';
import { X } from 'lucide-react';
import { IconButton } from './IconButton';

interface GlassDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  title: React.ReactNode;
  children: React.ReactNode;
  side?: 'left' | 'right';
}

export const GlassDrawer: React.FC<GlassDrawerProps> = ({
  isOpen,
  onClose,
  title,
  children,
  side = 'right',
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

  const sideClasses = side === 'left' ? 'left-0 border-r' : 'right-0 border-l';

  return (
    <div className="fixed inset-0 z-50 overflow-hidden">
      <div
        className="fixed inset-0 bg-slate-950/80 backdrop-blur-md transition-opacity"
        onClick={onClose}
        aria-hidden="true"
      />
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="drawer-title"
        className={`fixed inset-y-0 ${sideClasses} max-w-full w-80 sm:w-96 bg-slate-900 border-slate-700/80 p-6 shadow-2xl flex flex-col justify-between z-10`}
      >
        <div>
          <div className="flex items-center justify-between pb-4 border-b border-slate-800 mb-6">
            <h2 id="drawer-title" className="text-lg font-black text-slate-100">{title}</h2>
            <IconButton icon={X} onClick={onClose} variant="ghost" size="sm" ariaLabel="Close drawer" />
          </div>
          <div>{children}</div>
        </div>
      </div>
    </div>
  );
};
