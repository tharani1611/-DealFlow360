import React, { createContext, useContext, useState, useCallback } from 'react';
import { AlertCircle, CheckCircle, Info, AlertTriangle, Sparkles, X } from 'lucide-react';

export type ToastType = 'success' | 'error' | 'warning' | 'info' | 'ai';

export interface ToastMessage {
  id: string;
  type: ToastType;
  title?: string;
  message: string;
}

interface ToastContextType {
  showToast: (message: string, type?: ToastType, title?: string) => void;
}

const ToastContext = createContext<ToastContextType | undefined>(undefined);

export const ToastProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [toasts, setToasts] = useState<ToastMessage[]>([]);

  const showToast = useCallback((message: string, type: ToastType = 'info', title?: string) => {
    const id = Math.random().toString(36).substring(2, 9);
    const newToast: ToastMessage = { id, type, message, title };
    setToasts((prev) => [...prev, newToast]);

    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 4500);
  }, []);

  const removeToast = (id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  };

  return (
    <ToastContext.Provider value={{ showToast }}>
      {children}
      {/* Toast Render Container */}
      <div className="fixed bottom-5 right-5 z-50 flex flex-col gap-2 max-w-sm w-full pointer-events-none px-4">
        {toasts.map((toast) => (
          <div
            key={toast.id}
            className={`pointer-events-auto flex items-start gap-3 p-4 rounded-xl backdrop-blur-glass-lg border shadow-neo text-sm transition-all duration-300 animate-slide-in ${
              toast.type === 'success'
                ? 'bg-slate-900/95 border-emerald-500/50 text-emerald-300 shadow-neo-emerald'
                : toast.type === 'error'
                ? 'bg-slate-900/95 border-rose-500/50 text-rose-300 shadow-neo-rose'
                : toast.type === 'warning'
                ? 'bg-slate-900/95 border-amber-500/50 text-amber-300 shadow-neo-sm'
                : toast.type === 'ai'
                ? 'bg-slate-900/95 border-indigo-500/60 text-indigo-300 shadow-ai-glow'
                : 'bg-slate-900/95 border-sky-500/50 text-sky-300 shadow-neo-sm'
            }`}
          >
            {toast.type === 'success' && <CheckCircle className="w-5 h-5 text-emerald-400 shrink-0 mt-0.5" />}
            {toast.type === 'error' && <AlertCircle className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" />}
            {toast.type === 'warning' && <AlertTriangle className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />}
            {toast.type === 'ai' && <Sparkles className="w-5 h-5 text-indigo-400 shrink-0 mt-0.5 animate-pulse" />}
            {toast.type === 'info' && <Info className="w-5 h-5 text-sky-400 shrink-0 mt-0.5" />}

            <div className="flex-1">
              {toast.title && <div className="font-extrabold text-slate-100 mb-0.5">{toast.title}</div>}
              <div className="text-slate-200 text-xs leading-relaxed font-sans">{toast.message}</div>
            </div>

            <button
              onClick={() => removeToast(toast.id)}
              className="text-slate-400 hover:text-slate-100 p-1 rounded-md transition"
              aria-label="Dismiss toast notification"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
};

export const useToast = (): ToastContextType => {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error('useToast must be used within a ToastProvider');
  }
  return context;
};
